"""Tests for audiogram.pip_safe_summary (openhear-pip-safe-summary-v1)."""

from __future__ import annotations

import ast
import copy
import json
import socket
from datetime import datetime, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from audiogram import pip_safe_summary as pss
from audiogram.pip_safe_summary import (
    SCHEMA_ID,
    SECTIONS,
    build_json_text,
    build_markdown,
    build_summary,
    canonical_json,
    find_forbidden_keys,
    is_forbidden_key,
    verify_integrity,
    write_summary,
)
from audiogram.pip_safe_summary_cli import main as cli_main

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_DIR = ROOT / "examples" / "pip_safe_summary"
SELF_REPORT = EXAMPLE_DIR / "alex_example_self_report.json"
FIXED_NOW = datetime(2026, 11, 24, 20, 0, tzinfo=timezone.utc)


def _prov(day: str = "2026-09-01") -> dict:
    return {"source_type": "self_reported", "recorded_on": day}


def _self_report() -> dict:
    return json.loads(SELF_REPORT.read_text(encoding="utf-8"))


def _poisoned_living_profile() -> dict:
    """A synthetic Living Hearing Profile / passport bundle full of forbidden data.

    Clinical data appears at the top level *and* is smuggled inside every
    communication-needs item.  None of it may reach the summary.
    """
    smuggle = {
        "thresholds": [{"freq_hz": 1000, "db_hl": 70}],
        "pta": 72.5,
        "pure_tone_average": 72.5,
        "severity": "severe",
        "severity_label": "severe",
        "diagnosis": "sensorineural hearing loss",
        "id": "adj-001",
        "uuid": "00000000-0000-4000-8000-000000000000",
        "nhs_number": "000 000 0000",
        "national_insurance_number": "QQ000000Q",
        "date_of_birth": "1900-01-01",
        "address": "1 Example Street",
        "dsp_gain_profile": {"1000": 25},
    }
    needs = _self_report()
    needs.update(copy.deepcopy(smuggle))
    for item in needs["reasonable_adjustments"]:
        item.update(copy.deepcopy(smuggle))
        item["provenance"].update({"clinician_id": "C-1", "linkingId": "L-1"})
    for item in needs["channels_that_do_not_work_for_me"]:
        item.update(copy.deepcopy(smuggle))
    needs["functional_impact"].update(copy.deepcopy(smuggle))
    for item in needs["variation_over_time"]:
        item.update(copy.deepcopy(smuggle))
    return {
        "schema": "openhear-living-profile-v1",
        "schema_version": 2,
        "subject": "Alex Example",
        "persistent_identifier": "P-123",
        "clinical_core": {
            "right_ear": {"thresholds": [{"freq_hz": 1000, "db_hl": 70}]},
            "left_ear": {"thresholds": [{"freq_hz": 1000, "db_hl": 65}]},
            "classification": {"pta_right": 72.5, "severity": "severe"},
        },
        "haptic_layer": {"sound_classes": []},
        "history": {"entries": [{"sha256": "0" * 64}]},
        "communication_needs": needs,
    }


def _build(source=None, **kw) -> dict:
    kw.setdefault("include", SECTIONS)
    kw.setdefault("consent_given", True)
    kw.setdefault("preview_confirmed", True)
    kw.setdefault("now", FIXED_NOW)
    return build_summary(source if source is not None else _self_report(), **kw)


# ── Forbidden keys ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "key",
    [
        "thresholds",
        "threshold_db",
        "pta",
        "PTA",
        "pta_right",
        "pure_tone_average",
        "severity",
        "severity_label",
        "diagnosis",
        "id",
        "uuid",
        "linkingId",
        "persistent_identifier",
        "cross_service_identifier",
        "nhs_number",
        "national_insurance_number",
        "nino",
        "date_of_birth",
        "dob",
        "address",
        "db_hl",
        "clinical_core",
        "subject",
    ],
)
def test_forbidden_key_detector_flags(key):
    assert is_forbidden_key(key)


@pytest.mark.parametrize(
    "key",
    [
        "schema",
        "schema_version",
        "in_my_own_words",
        "is_reasonable_adjustment",
        "provenance",
        "recorded_on",
        "display_name",
        "sections_included",
        "what_does_not_help",
        "channel",
    ],
)
def test_forbidden_key_detector_allows_summary_keys(key):
    assert not is_forbidden_key(key)


def test_no_forbidden_keys_from_plain_self_report():
    doc = _build()
    assert find_forbidden_keys(doc) == []


def test_no_forbidden_keys_even_when_source_profile_holds_them():
    source = _poisoned_living_profile()
    assert find_forbidden_keys(source)  # the fixture really is poisoned
    doc = _build(source)
    assert find_forbidden_keys(doc) == []
    text = build_json_text(doc) + build_markdown(doc)
    for leak in (
        "sensorineural",
        "72.5",
        "db_hl",
        "QQ000000Q",
        "000 000 0000",
        "1900-01-01",
        "Example Street",
        "adj-001",
        "P-123",
        "00000000-0000-4000",
    ):
        assert leak not in text, leak
    assert doc["reasonable_adjustments"] == _build()["reasonable_adjustments"]


def test_schema_file_cannot_express_forbidden_keys():
    schema = json.loads(pss.SCHEMA_PATH.read_text(encoding="utf-8"))

    def _prop_names(node):
        if isinstance(node, dict):
            for k, v in node.get("properties", {}).items():
                yield k
                yield from _prop_names(v)
            for k, v in node.items():
                if k != "properties":
                    yield from _prop_names(v)
        elif isinstance(node, list):
            for v in node:
                yield from _prop_names(v)

    names = set(_prop_names(schema))
    assert names, "schema has no properties"
    assert not [n for n in names if is_forbidden_key(n)]


# ── Content and provenance ───────────────────────────────────────────────────


def test_every_item_has_self_reported_provenance_and_date():
    doc = _build()
    items = (
        doc["reasonable_adjustments"]
        + doc["channels_that_do_not_work_for_me"]
        + doc["variation_over_time"]
        + [doc["functional_impact"]]
    )
    for item in items:
        assert item["provenance"]["source_type"] == "self_reported"
        assert len(item["provenance"]["recorded_on"]) == 10


def test_email_only_is_marked_as_reasonable_adjustment():
    doc = _build()
    email = doc["reasonable_adjustments"][0]
    assert email["category"] == "contact_channel"
    assert email["is_reasonable_adjustment"] is True
    assert "(reasonable adjustment)" in build_markdown(doc)


def test_clinician_section_is_stubbed_off():
    doc = _build()
    assert doc["clinician_sourced"]["included"] is False


def test_clinician_sourced_provenance_is_rejected():
    src = _self_report()
    src["reasonable_adjustments"][0]["provenance"]["source_type"] = "clinician_sourced"
    with pytest.raises(ValueError, match="self_reported"):
        _build(src)


def test_bad_date_is_rejected():
    src = _self_report()
    src["variation_over_time"][0]["recorded_on"] = "12/10/2026"
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        _build(src)


def test_unknown_section_is_rejected():
    with pytest.raises(ValueError, match="Unknown section"):
        _build(include=["clinical_core"])


def test_display_name_is_opt_in():
    doc = build_summary(_self_report(), consent_given=True, preview_confirmed=True, now=FIXED_NOW)
    assert "display_name" not in doc
    assert "display_name" in doc["consent"]["sections_not_included"]


def test_section_selection_is_respected():
    doc = _build(include=["functional_impact"])
    assert "reasonable_adjustments" not in doc
    assert doc["consent"]["sections_included"] == ["functional_impact"]


def test_clinical_text_warning_is_advisory_only():
    src = _self_report()
    src["functional_impact"]["in_my_own_words"] = "My PTA is 80 dB HL."
    doc = _build(src)
    assert pss.clinical_text_warnings(doc)
    assert doc["functional_impact"]["in_my_own_words"] == "My PTA is 80 dB HL."


# ── Integrity hash ───────────────────────────────────────────────────────────


def test_integrity_hash_round_trip_and_tamper_detection():
    doc = _build()
    assert verify_integrity(doc)
    tampered = copy.deepcopy(doc)
    tampered["functional_impact"]["in_my_own_words"] += " Edited."
    assert not verify_integrity(tampered)
    assert canonical_json(doc) == canonical_json({k: v for k, v in doc.items()})


def test_integrity_hash_is_optional():
    doc = _build(with_integrity_hash=False)
    assert "integrity" not in doc
    assert not verify_integrity(doc)


def test_hash_is_never_called_a_signature():
    doc = _build()
    assert "not a signature" in doc["integrity"]["label"]
    md = build_markdown(doc)
    assert "integrity hash" in md.lower()
    for line in md.splitlines():
        if "signature" in line.lower():
            assert "not a signature" in line.lower()


# ── Writing, consent and network ─────────────────────────────────────────────


def test_write_requires_consent_and_preview(tmp_path):
    doc = _build(consent_given=False)
    with pytest.raises(PermissionError):
        write_summary(doc, tmp_path / "out")
    doc = _build(preview_confirmed=False)
    with pytest.raises(PermissionError):
        write_summary(doc, tmp_path / "out")
    assert list(tmp_path.iterdir()) == []


def test_write_produces_exact_preview_and_refuses_overwrite(tmp_path):
    doc = _build()
    md_path, json_path = write_summary(doc, tmp_path / "out")
    assert md_path.read_text(encoding="utf-8") == build_markdown(doc)
    assert json_path.read_text(encoding="utf-8") == build_json_text(doc)
    assert verify_integrity(json.loads(json_path.read_text(encoding="utf-8")))
    with pytest.raises(FileExistsError):
        write_summary(doc, tmp_path / "out")


def test_write_refuses_document_with_forbidden_key(tmp_path):
    doc = _build()
    doc["severity"] = "severe"
    with pytest.raises(ValueError, match="Forbidden"):
        write_summary(doc, tmp_path / "out")
    assert list(tmp_path.iterdir()) == []


def test_module_imports_nothing_that_talks_to_the_network():
    banned = {"socket", "urllib", "http", "requests", "httpx", "aiohttp", "ftplib", "smtplib"}
    for name in ("pip_safe_summary.py", "pip_safe_summary_cli.py"):
        tree = ast.parse((ROOT / "audiogram" / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""]
            else:
                continue
            for mod in mods:
                assert mod.split(".")[0] not in banned, f"{name} imports {mod}"


@pytest.fixture
def no_network(monkeypatch):
    def _blocked(*a, **k):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)


def _cli_args(out: Path) -> list[str]:
    return [str(SELF_REPORT), "--out", str(out)]


def test_cli_cancel_writes_nothing(tmp_path, no_network):
    out = tmp_path / "summary"
    result = CliRunner().invoke(cli_main, _cli_args(out), input="y\ny\ny\ny\ny\nno\n")
    assert result.exit_code == 0, result.output
    assert "PREVIEW" in result.output
    assert "Nothing was written" in result.output
    assert list(tmp_path.iterdir()) == []


def test_cli_confirm_writes_exactly_the_preview(tmp_path, no_network):
    out = tmp_path / "summary"
    # display_name defaults to no; accept the rest, then type the confirm word.
    result = CliRunner().invoke(cli_main, _cli_args(out), input="\n\n\n\n\nwrite\n")
    assert result.exit_code == 0, result.output
    md = (tmp_path / "summary.md").read_text(encoding="utf-8")
    data = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert md in result.output
    assert build_json_text(data) in result.output
    assert "display_name" not in data
    assert data["schema"] == SCHEMA_ID
    assert find_forbidden_keys(data) == []
    assert verify_integrity(data)


def test_cli_with_poisoned_profile_source(tmp_path, no_network):
    src = tmp_path / "living_profile.json"
    src.write_text(json.dumps(_poisoned_living_profile()), encoding="utf-8")
    out = tmp_path / "summary"
    args = [str(src), "--out", str(out), "--include", "reasonable_adjustments", "--no-hash"]
    result = CliRunner().invoke(cli_main, args, input="write\n")
    assert result.exit_code == 0, result.output
    data = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert find_forbidden_keys(data) == []
    assert "integrity" not in data
    assert "sensorineural" not in (tmp_path / "summary.md").read_text(encoding="utf-8")


# ── Committed fictional example ──────────────────────────────────────────────


def test_committed_example_is_reproducible_and_clean():
    doc = _build()
    committed_json = (EXAMPLE_DIR / "alex_example_pip_safe_summary.json").read_text(
        encoding="utf-8"
    )
    committed_md = (EXAMPLE_DIR / "alex_example_pip_safe_summary.md").read_text(encoding="utf-8")
    assert committed_json == build_json_text(doc)
    assert committed_md == build_markdown(doc)
    data = json.loads(committed_json)
    assert verify_integrity(data)
    assert find_forbidden_keys(data) == []
    assert data["display_name"] == "Alex Example"


def test_committed_example_matches_json_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(pss.SCHEMA_PATH.read_text(encoding="utf-8"))
    data = json.loads((EXAMPLE_DIR / "alex_example_pip_safe_summary.json").read_text("utf-8"))
    jsonschema.validate(data, schema)
    bad = copy.deepcopy(data)
    bad["functional_impact"]["severity"] = "severe"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
