"""Tests for audiogram.communication_needs_summary (openhear-communication-needs-summary-v1)."""

from __future__ import annotations

import ast
import copy
import json
import socket
from datetime import datetime, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from audiogram import communication_needs_summary as cns
from audiogram.communication_needs_summary import (
    SCHEMA_ID,
    SECTIONS,
    build_json_text,
    build_markdown,
    build_summary,
    canonical_json,
    coarsen_date,
    confirm_consent,
    find_forbidden_keys,
    free_text_warning_box,
    is_forbidden_key,
    verify_integrity,
    write_summary,
)
from audiogram.communication_needs_summary_cli import main as cli_main

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_DIR = ROOT / "examples" / "communication_needs_summary"
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


def _pending(source=None, **kw) -> dict:
    kw.setdefault("include", SECTIONS)
    kw.setdefault("now", FIXED_NOW)
    return build_summary(source if source is not None else _self_report(), **kw)


def _build(source=None, *, with_integrity_hash=True, **kw) -> dict:
    """Pending document plus confirmed consent, as written after 'write'."""
    return confirm_consent(
        _pending(source, **kw), with_integrity_hash=with_integrity_hash, now=FIXED_NOW
    )


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
    schema = json.loads(cns.SCHEMA_PATH.read_text(encoding="utf-8"))

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
        assert len(item["provenance"]["recorded_on"]) == 7  # month by default


def test_reasonable_adjustment_flag_is_kept_and_rendered():
    doc = _build()
    flags = [a["is_reasonable_adjustment"] for a in doc["reasonable_adjustments"]]
    assert flags == [True, True, True, False]
    md = build_markdown(doc)
    assert "(reasonable adjustment)" in md
    assert "(preference)" in md


def test_reasonable_adjustment_flag_is_required():
    src = _self_report()
    del src["reasonable_adjustments"][0]["is_reasonable_adjustment"]
    with pytest.raises(ValueError, match="is_reasonable_adjustment is required"):
        _build(src)


@pytest.mark.parametrize("bad", ["yes", "true", 1, 0, None, []])
def test_reasonable_adjustment_flag_must_be_bool(bad):
    src = _self_report()
    src["reasonable_adjustments"][1]["is_reasonable_adjustment"] = bad
    with pytest.raises(ValueError, match="true or false"):
        _build(src)


def test_schema_requires_boolean_reasonable_adjustment_flag():
    schema = json.loads(cns.SCHEMA_PATH.read_text(encoding="utf-8"))
    item = schema["properties"]["reasonable_adjustments"]["items"]
    assert "is_reasonable_adjustment" in item["required"]
    assert item["properties"]["is_reasonable_adjustment"] == {"type": "boolean"}
    committed = json.loads(
        (EXAMPLE_DIR / "alex_example_communication_needs_summary.json").read_text("utf-8")
    )
    missing = copy.deepcopy(committed)
    del missing["reasonable_adjustments"][0]["is_reasonable_adjustment"]
    assert _mini_validate(missing, schema)
    wrong = copy.deepcopy(committed)
    wrong["reasonable_adjustments"][0]["is_reasonable_adjustment"] = "yes"
    assert _mini_validate(wrong, schema)


def test_example_input_states_flag_explicitly_for_every_adjustment():
    for item in _self_report()["reasonable_adjustments"]:
        assert isinstance(item["is_reasonable_adjustment"], bool)


def test_clinician_section_is_stubbed_off():
    doc = _build()
    assert doc["clinician_sourced"]["included"] is False


def test_clinician_sourced_provenance_is_rejected():
    src = _self_report()
    src["reasonable_adjustments"][0]["provenance"]["source_type"] = "clinician_sourced"
    with pytest.raises(ValueError, match="self_reported"):
        _build(src)


@pytest.mark.parametrize("bad", ["12/10/2026", "2026-13", "2026-02-30", "26"])
def test_bad_date_is_rejected(bad):
    src = _self_report()
    src["variation_over_time"][0]["recorded_on"] = bad
    with pytest.raises(ValueError, match="date"):
        _build(src)


def test_unknown_section_is_rejected():
    with pytest.raises(ValueError, match="Unknown section"):
        _build(include=["clinical_core"])


def test_display_name_is_opt_in():
    doc = build_summary(_self_report(), now=FIXED_NOW)
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
    assert cns.clinical_text_warnings(doc)
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


def test_write_refuses_pending_consent(tmp_path):
    with pytest.raises(PermissionError):
        write_summary(_pending(), tmp_path / "out")
    forged = _pending()
    forged["consent"]["given"] = True  # status still pending, no timestamp
    with pytest.raises(PermissionError):
        write_summary(forged, tmp_path / "out")
    assert list(tmp_path.iterdir()) == []


# ── Consent: pending in preview, given only after confirmation ───────────────


def test_preview_shows_consent_pending():
    pending = _pending()
    consent = pending["consent"]
    assert consent["status"] == "pending"
    assert consent["given"] is False
    assert consent["given_at"] is None
    assert consent["preview_confirmed"] is False
    assert "integrity" not in pending
    md = build_markdown(pending)
    assert "PENDING" in md
    assert "Status: given" not in md


def test_confirm_records_given_with_date_and_does_not_mutate_pending():
    pending = _pending()
    final = confirm_consent(pending, now=FIXED_NOW)
    assert pending["consent"]["status"] == "pending"
    assert final["consent"]["status"] == "given"
    assert final["consent"]["given"] is True
    assert final["consent"]["preview_confirmed"] is True
    assert final["consent"]["given_at"] == "2026-11"  # month precision, no time
    assert "Status: given (2026-11)" in build_markdown(final)
    assert verify_integrity(final)
    with pytest.raises(ValueError, match="pending"):
        confirm_consent(final)


def test_confirm_with_export_time_records_full_timestamp():
    final = _build(include_export_time=True)
    assert final["exported_at"] == "2026-11-24T20:00:00+00:00"
    assert final["consent"]["given_at"] == "2026-11-24T20:00:00+00:00"


def test_only_consent_and_hash_differ_between_preview_and_written():
    pending = _pending()
    final = confirm_consent(pending, now=FIXED_NOW)
    strip = lambda d: {k: v for k, v in d.items() if k not in ("consent", "integrity")}  # noqa: E731
    assert strip(pending) == strip(final)
    keep = ("statement", "destination", "upload_performed", "sections_included")
    for key in keep:
        assert pending["consent"][key] == final["consent"][key]


# ── Timestamps and date precision ────────────────────────────────────────────


def test_export_time_is_off_by_default():
    assert "exported_at" not in _pending()
    assert "exported_at" not in _build()
    assert "Exported" not in build_markdown(_build())


@pytest.mark.parametrize("precision, length", [("day", 10), ("month", 7), ("year", 4)])
def test_date_precision_applies_to_every_entry_date(precision, length):
    doc = _build(date_precision=precision)
    assert doc["date_precision"] == precision
    dates = [v["recorded_on"] for v in doc["variation_over_time"]]
    for section in (
        "reasonable_adjustments",
        "channels_that_do_not_work_for_me",
        "variation_over_time",
    ):
        for item in doc[section]:
            dates.append(item["provenance"]["recorded_on"])
            if "last_reviewed" in item["provenance"]:
                dates.append(item["provenance"]["last_reviewed"])
    dates.append(doc["functional_impact"]["provenance"]["recorded_on"])
    assert dates and all(len(d) == length for d in dates)


def test_default_date_precision_is_month():
    assert _build()["date_precision"] == "month"
    assert _build()["variation_over_time"][0]["recorded_on"] == "2026-10"


def test_coarsen_never_invents_precision():
    assert coarsen_date("2026", "day") == "2026"
    assert coarsen_date("2026-10", "day") == "2026-10"
    assert coarsen_date("2026-10-12", "year") == "2026"
    with pytest.raises(ValueError):
        coarsen_date("2026-10-12", "week")


def test_coarse_input_dates_are_accepted():
    src = _self_report()
    src["variation_over_time"][0]["recorded_on"] = "2026-10"
    src["functional_impact"]["provenance"]["recorded_on"] = "2026"
    doc = _build(src, date_precision="day")
    assert doc["variation_over_time"][0]["recorded_on"] == "2026-10"
    assert doc["functional_impact"]["provenance"]["recorded_on"] == "2026"


def test_unknown_precision_is_rejected():
    with pytest.raises(ValueError, match="precision"):
        _pending(date_precision="week")


# ── Free-text warning ────────────────────────────────────────────────────────


def test_free_text_warning_box_always_shown_and_lists_examples():
    box = free_text_warning_box(_pending())
    assert box.splitlines()[0].startswith("!!!")
    assert "never edits or removes anything you typed" in box
    for example in ("test results", "dB", "diagnoses", "NHS", "postcodes", "phone", "email"):
        assert example in box
    assert "Spotted in your text" not in box


@pytest.mark.parametrize(
    "text, label",
    [
        ("My NI number is JK 12 34 56 C.", "National Insurance number"),
        ("Reference AB123456D on the letter.", "National Insurance number"),
        ("NHS no. 943 476 5919", "NHS number"),
        ("NHS 9434765919", "NHS number"),
        ("Post goes to SW1A 1AA.", "UK postcode"),
        ("Write to me at m1 1ae please.", "UK postcode"),
        ("I live at 12 Example Road.", "street address"),
        ("Flat 3, 221B Baker Street", "street address"),
        ("Call 020 7946 0958 if needed", "phone number"),
        ("Mobile +44 7700 900123", "phone number"),
        ("My number is 07700900123.", "phone number"),
        ("Email alex.example@example.org", "email address"),
    ],
)
def test_free_text_scanner_flags_personal_details_without_editing(text, label):
    src = _self_report()
    src["functional_impact"]["in_my_own_words"] = text
    pending = _pending(src)
    warnings = cns.clinical_text_warnings(pending)
    assert any(label in w and "functional_impact.in_my_own_words" in w for w in warnings), warnings
    assert pending["functional_impact"]["in_my_own_words"] == text
    assert label in free_text_warning_box(pending)


def test_free_text_scanner_is_quiet_on_the_fictional_example():
    assert cns.clinical_text_warnings(_pending()) == []


def test_free_text_warning_box_lists_spotted_snippets_without_editing():
    src = _self_report()
    words = "My audiogram shows 70 dB HL at 4 kHz; diagnosis was given."
    src["functional_impact"]["in_my_own_words"] = words
    pending = _pending(src)
    box = free_text_warning_box(pending)
    assert "Spotted in your text" in box
    assert "functional_impact.in_my_own_words" in box
    assert pending["functional_impact"]["in_my_own_words"] == words


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
    for name in ("communication_needs_summary.py", "communication_needs_summary_cli.py"):
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
    assert "PENDING" in result.output
    assert "Consent was not given" in result.output
    assert "Nothing was written" in result.output
    assert list(tmp_path.iterdir()) == []


def test_cli_confirm_writes_exactly_the_preview(tmp_path, no_network):
    out = tmp_path / "summary"
    # display_name defaults to no; accept the rest, then type the confirm word.
    result = CliRunner().invoke(cli_main, _cli_args(out), input="\n\n\n\n\nwrite\n")
    assert result.exit_code == 0, result.output
    md = (tmp_path / "summary.md").read_text(encoding="utf-8")
    data = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    out_text = result.output
    # The warning box comes before the free-text preview.
    assert out_text.index("CHECK YOUR OWN WORDS") < out_text.index("PREVIEW: Markdown")
    # Preview said PENDING; the written file says given, and nothing else differs.
    assert "PENDING" in out_text
    assert data["consent"]["status"] == "given" and data["consent"]["given"] is True
    assert "Status: given" in md and "PENDING" not in md
    preview_doc = json.loads(
        out_text.split("──── PREVIEW: JSON (consent PENDING) ────\n\n", 1)[1].split(
            "\nIf you confirm", 1
        )[0]
    )
    assert preview_doc["consent"]["status"] == "pending"
    strip = lambda d: {k: v for k, v in d.items() if k not in ("consent", "integrity")}  # noqa: E731
    assert strip(preview_doc) == strip(data)
    assert "exported_at" not in data
    assert data["date_precision"] == "month"
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
    committed_json = (EXAMPLE_DIR / "alex_example_communication_needs_summary.json").read_text(
        encoding="utf-8"
    )
    committed_md = (EXAMPLE_DIR / "alex_example_communication_needs_summary.md").read_text(
        encoding="utf-8"
    )
    assert committed_json == build_json_text(doc)
    assert committed_md == build_markdown(doc)
    data = json.loads(committed_json)
    assert verify_integrity(data)
    assert find_forbidden_keys(data) == []
    assert data["display_name"] == "Alex Example"


def test_cli_opt_in_export_time_and_year_precision(tmp_path, no_network):
    out = tmp_path / "summary"
    args = _cli_args(out) + [
        "--include",
        "variation_over_time",
        "--include-export-time",
        "--date-precision",
        "year",
    ]
    result = CliRunner().invoke(cli_main, args, input="write\n")
    assert result.exit_code == 0, result.output
    data = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert "exported_at" in data
    assert "T" in data["consent"]["given_at"]
    assert all(len(v["recorded_on"]) == 4 for v in data["variation_over_time"])


def test_written_and_pending_documents_against_schema_without_dependencies():
    """Runs everywhere, including CI, using the small validator below."""
    schema = json.loads(cns.SCHEMA_PATH.read_text(encoding="utf-8"))
    committed = json.loads(
        (EXAMPLE_DIR / "alex_example_communication_needs_summary.json").read_text("utf-8")
    )
    for doc in (
        committed,
        _build(),
        _build(date_precision="day", include_export_time=True),
        _build(date_precision="year", with_integrity_hash=False),
    ):
        assert _mini_validate(doc, schema) == [], _mini_validate(doc, schema)
    # Pending (unconfirmed) documents are never valid as written files.
    assert _mini_validate(_pending(), schema)
    bad = copy.deepcopy(committed)
    bad["functional_impact"]["severity"] = "severe"
    assert _mini_validate(bad, schema)
    bad = copy.deepcopy(committed)
    bad["variation_over_time"][0]["recorded_on"] = "12/10/2026"
    assert _mini_validate(bad, schema)


def _mini_validate(inst, schema, root=None, path="$"):
    """Validate the JSON Schema subset used by communication_needs_summary.schema.json.

    Supports $ref (local), type, const, enum, required, properties,
    additionalProperties (false), items, pattern, minLength, minItems,
    uniqueItems and anyOf.  ``format`` is advisory and not checked.
    """
    import re as _re

    root = root or schema
    errs: list[str] = []
    if "$ref" in schema:
        node = root
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        return _mini_validate(inst, node, root, path)
    if "anyOf" in schema:
        if all(_mini_validate(inst, sub, root, path) for sub in schema["anyOf"]):
            errs.append(f"{path}: matches no anyOf branch")
    types = {
        "object": dict,
        "array": list,
        "string": str,
        "boolean": bool,
        "integer": int,
    }
    if "type" in schema and not isinstance(inst, types[schema["type"]]):
        return errs + [f"{path}: expected {schema['type']}"]
    if "const" in schema and (inst != schema["const"] or type(inst) is not type(schema["const"])):
        errs.append(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and inst not in schema["enum"]:
        errs.append(f"{path}: not in enum")
    if isinstance(inst, str):
        if len(inst) < schema.get("minLength", 0):
            errs.append(f"{path}: too short")
        if "pattern" in schema and not _re.search(schema["pattern"], inst):
            errs.append(f"{path}: does not match pattern")
    if isinstance(inst, dict):
        for key in schema.get("required", []):
            if key not in inst:
                errs.append(f"{path}: missing {key}")
        props = schema.get("properties", {})
        for key, value in inst.items():
            if key in props:
                errs += _mini_validate(value, props[key], root, f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}: unexpected key {key}")
    if isinstance(inst, list):
        if len(inst) < schema.get("minItems", 0):
            errs.append(f"{path}: too few items")
        if schema.get("uniqueItems") and len({json.dumps(i, sort_keys=True) for i in inst}) != len(
            inst
        ):
            errs.append(f"{path}: items not unique")
        if "items" in schema:
            for i, value in enumerate(inst):
                errs += _mini_validate(value, schema["items"], root, f"{path}[{i}]")
    return errs


def test_committed_example_matches_json_schema():
    # CI's workflow installs an explicit package list without jsonschema, and that
    # workflow file cannot be changed from this branch's push credentials.  The
    # dependency-free schema test above always runs; this one adds full
    # validation wherever jsonschema is installed (e.g. `make install-dev`).
    jsonschema = pytest.importorskip(
        "jsonschema",
        reason="jsonschema not installed (CI workflow does not install it); "
        "dependency-free schema test still runs",
    )
    schema = json.loads(cns.SCHEMA_PATH.read_text(encoding="utf-8"))
    data = json.loads(
        (EXAMPLE_DIR / "alex_example_communication_needs_summary.json").read_text("utf-8")
    )
    jsonschema.validate(data, schema)
    bad = copy.deepcopy(data)
    bad["functional_impact"]["severity"] = "severe"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
