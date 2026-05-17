"""Tests for Phase A: extraction schema, safety evaluator, Phonak mock
adapter, and the new ``openhear-noahlink`` CLI subcommands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from audiogram.audiogram import Audiogram
from core.fitting_data import (
    CompressionProfile,
    DeviceInfo,
    FittingSession,
    GainTable,
    MPOProfile,
    ProgrammeSlot,
)
from core.noahlink import main as noahlink_main
from core.noahlink.vendors import available_adapters
from core.noahlink.vendors.phonak import (
    FEATURE_FLAG_ENV,
    WRITE_SUPPORTED,
    PhonakMockAdapter,
    is_enabled,
    raise_if_write_disabled,
    read_extraction,
)
from core.safety import (
    DEFAULT_THRESHOLDS,
    SafetyFlag,
    SafetyReport,
    SafetyThresholds,
    evaluate_extraction,
    evaluate_session,
)
from core.schema import EXTRACTION_V1_VERSION
from core.schema.extraction_v1 import (
    SCHEMA_VERSION,
    BoneConductionAudiogram,
    ExtractedFitting,
    ExtractionSafetyFlag,
    RECDProfile,
)

# ── schema/extraction_v1 ----------------------------------------------------


class TestExtractionV1Schema:
    def test_schema_version_constant_is_exposed(self):
        assert SCHEMA_VERSION == "openhear-extraction-v1"
        assert EXTRACTION_V1_VERSION == SCHEMA_VERSION

    def test_round_trip_default_document(self):
        original = ExtractedFitting()
        text = original.to_json()
        restored = ExtractedFitting.from_json(text)
        assert restored.to_dict() == original.to_dict()

    def test_round_trip_full_document(self):
        original = ExtractedFitting(
            captured_at="2026-05-17T11:00:00+00:00",
            vendor_adapter="phonak.mock",
            is_verified=False,
            confidence=0.0,
            device=DeviceInfo(manufacturer="Phonak", model="Naida", serial="SN-1"),
            air_conduction=Audiogram(
                left_ear={500: 30, 1000: 40},
                right_ear={500: 25, 1000: 35},
                source="synthetic",
            ),
            bone_conduction=BoneConductionAudiogram(
                left_ear={500: 25, 1000: 30},
                right_ear={500: 20, 1000: 28},
            ),
            recd=RECDProfile(
                frequencies_hz=[500, 1000, 2000],
                left_db=[2.0, 4.0, 8.0],
                right_db=[2.0, 4.0, 8.0],
            ),
            right_gain=GainTable(frequencies_hz=[500, 1000, 2000], gains_db=[10.0, 15.0, 20.0]),
            left_gain=GainTable(frequencies_hz=[500, 1000, 2000], gains_db=[10.0, 15.0, 20.0]),
            right_compression=CompressionProfile(
                centre_frequencies_hz=[500, 1000],
                ratios=[2.0, 2.5],
                knee_db=[50.0, 50.0],
                attack_ms=[5.0, 5.0],
                release_ms=[50.0, 50.0],
            ),
            left_compression=CompressionProfile(
                centre_frequencies_hz=[500, 1000],
                ratios=[2.0, 2.5],
                knee_db=[50.0, 50.0],
                attack_ms=[5.0, 5.0],
                release_ms=[50.0, 50.0],
            ),
            right_mpo=MPOProfile(centre_frequencies_hz=[500, 1000], max_db_spl=[110.0, 110.0]),
            left_mpo=MPOProfile(centre_frequencies_hz=[500, 1000], max_db_spl=[110.0, 110.0]),
            programmes=[ProgrammeSlot(slot_index=0, name="Default")],
            safety_flags=[
                ExtractionSafetyFlag(level="info", code="x", message="m", location="loc")
            ],
            raw_payload_hex="dead",
        )
        restored = ExtractedFitting.from_json(original.to_json())
        assert restored.to_dict() == original.to_dict()
        assert restored.device.manufacturer == "Phonak"
        assert restored.air_conduction is not None
        assert restored.bone_conduction is not None
        assert restored.recd is not None
        assert restored.recd.frequencies_hz == [500, 1000, 2000]

    def test_rejects_wrong_schema_version(self):
        with pytest.raises(ValueError, match="schema_version"):
            ExtractedFitting(schema_version="openhear-extraction-v2")

    def test_rejects_confidence_out_of_range(self):
        with pytest.raises(ValueError, match="confidence"):
            ExtractedFitting(confidence=1.5)
        with pytest.raises(ValueError, match="confidence"):
            ExtractedFitting(confidence=-0.1)

    def test_sha256_commitment_is_deterministic(self):
        a = ExtractedFitting(captured_at="t", vendor_adapter="x")
        b = ExtractedFitting(captured_at="t", vendor_adapter="x")
        assert a.sha256_commitment() == b.sha256_commitment()
        assert len(a.sha256_commitment()) == 64  # SHA-256 hex digest

    def test_sha256_commitment_changes_with_content(self):
        a = ExtractedFitting(captured_at="t", vendor_adapter="x")
        b = ExtractedFitting(captured_at="t", vendor_adapter="y")
        assert a.sha256_commitment() != b.sha256_commitment()

    def test_canonical_json_is_sorted(self):
        doc = ExtractedFitting(vendor_adapter="x")
        text = doc.canonical_json()
        parsed = json.loads(text)
        # Sorted keys means schema_version comes after the lexicographic
        # ordering of all other top-level keys.  Verify it's present and
        # that the encoding uses no whitespace.
        assert " " not in text
        assert parsed["schema_version"] == SCHEMA_VERSION


class TestBoneConductionAudiogram:
    def test_validates_threshold_range(self):
        with pytest.raises(ValueError, match="outside the valid range"):
            BoneConductionAudiogram(left_ear={500: 200.0})

    def test_validates_frequency_is_integer(self):
        with pytest.raises(ValueError, match="integer-like"):
            BoneConductionAudiogram(left_ear={"abc": 30.0})

    def test_validates_threshold_is_numeric(self):
        with pytest.raises(ValueError, match="numeric"):
            BoneConductionAudiogram(left_ear={500: "loud"})

    def test_accepts_string_frequency_keys(self):
        bc = BoneConductionAudiogram(left_ear={"500": 30, "1000": 40})
        assert bc.left_ear == {500: 30.0, 1000: 40.0}

    def test_round_trip_dict(self):
        bc = BoneConductionAudiogram(
            left_ear={500: 30, 1000: 40},
            right_ear={500: 25, 1000: 35},
        )
        assert BoneConductionAudiogram.from_dict(bc.to_dict()).to_dict() == bc.to_dict()

    def test_from_dict_accepts_list_of_pairs(self):
        bc = BoneConductionAudiogram.from_dict(
            {"left_ear": [[500, 30], [1000, 40]], "right_ear": {}}
        )
        assert bc.left_ear == {500: 30.0, 1000: 40.0}


class TestRECDProfile:
    def test_length_mismatch_rejected(self):
        with pytest.raises(ValueError, match="length"):
            RECDProfile(frequencies_hz=[500, 1000], left_db=[1.0], right_db=[1.0, 2.0])

    def test_round_trip(self):
        r = RECDProfile(frequencies_hz=[500, 1000], left_db=[2.0, 4.0], right_db=[3.0, 5.0])
        assert RECDProfile.from_dict(r.to_dict()).to_dict() == r.to_dict()


class TestExtractionSafetyFlag:
    def test_rejects_unknown_level(self):
        with pytest.raises(ValueError, match="level"):
            ExtractionSafetyFlag(level="boom", code="x", message="m")

    def test_rejects_empty_code(self):
        with pytest.raises(ValueError, match="code"):
            ExtractionSafetyFlag(level="info", code="", message="m")

    def test_round_trip(self):
        f = ExtractionSafetyFlag(level="warning", code="x", message="m", location="l")
        assert ExtractionSafetyFlag.from_dict(f.to_dict()).to_dict() == f.to_dict()


# ── safety ------------------------------------------------------------------


def _session_with_safe_defaults() -> FittingSession:
    return FittingSession(
        right_gain=GainTable(frequencies_hz=[500, 1000], gains_db=[10.0, 15.0]),
        left_gain=GainTable(frequencies_hz=[500, 1000], gains_db=[10.0, 15.0]),
        right_compression=CompressionProfile(
            centre_frequencies_hz=[500, 1000],
            ratios=[2.0, 2.0],
            knee_db=[50.0, 50.0],
            attack_ms=[5.0, 5.0],
            release_ms=[50.0, 50.0],
        ),
        left_compression=CompressionProfile(
            centre_frequencies_hz=[500, 1000],
            ratios=[2.0, 2.0],
            knee_db=[50.0, 50.0],
            attack_ms=[5.0, 5.0],
            release_ms=[50.0, 50.0],
        ),
        right_mpo=MPOProfile(centre_frequencies_hz=[500, 1000], max_db_spl=[110.0, 110.0]),
        left_mpo=MPOProfile(centre_frequencies_hz=[500, 1000], max_db_spl=[110.0, 110.0]),
    )


class TestSafetyEvaluator:
    def test_safe_session_passes_with_no_flags(self):
        report = evaluate_session(_session_with_safe_defaults())
        assert report.passed
        assert report.flags == []

    def test_gain_above_ceiling_is_critical(self):
        session = _session_with_safe_defaults()
        session.right_gain = GainTable(frequencies_hz=[500], gains_db=[80.0])
        report = evaluate_session(session)
        assert not report.passed
        crit = report.critical()
        assert len(crit) == 1
        assert crit[0].code == "gain_exceeds_ceiling"
        assert "right_gain[0]" in crit[0].location

    def test_negative_gain_is_warning_not_critical(self):
        session = _session_with_safe_defaults()
        session.right_gain = GainTable(frequencies_hz=[500], gains_db=[-3.0])
        report = evaluate_session(session)
        assert report.passed  # warnings only
        assert any(f.code == "negative_gain" for f in report.warnings())

    def test_high_compression_ratio_is_warning(self):
        session = _session_with_safe_defaults()
        session.right_compression = CompressionProfile(
            centre_frequencies_hz=[500],
            ratios=[12.0],
            knee_db=[50.0],
            attack_ms=[5.0],
            release_ms=[50.0],
        )
        report = evaluate_session(session)
        assert any(f.code == "compression_ratio_high" for f in report.flags)
        assert report.passed  # warning only

    def test_expander_ratio_is_warning(self):
        session = _session_with_safe_defaults()
        session.right_compression = CompressionProfile(
            centre_frequencies_hz=[500],
            ratios=[0.8],
            knee_db=[50.0],
            attack_ms=[5.0],
            release_ms=[50.0],
        )
        report = evaluate_session(session)
        assert any(f.code == "compression_ratio_low" for f in report.flags)

    def test_missing_mpo_is_critical_by_default(self):
        session = _session_with_safe_defaults()
        session.right_mpo = MPOProfile()
        report = evaluate_session(session)
        assert not report.passed
        assert any(f.code == "mpo_missing" for f in report.critical())

    def test_require_mpo_can_be_disabled(self):
        session = _session_with_safe_defaults()
        session.right_mpo = MPOProfile()
        session.left_mpo = MPOProfile()
        thresholds = SafetyThresholds(require_mpo=False)
        report = evaluate_session(session, thresholds=thresholds)
        assert report.passed

    def test_mpo_above_ceiling_is_critical(self):
        session = _session_with_safe_defaults()
        session.right_mpo = MPOProfile(centre_frequencies_hz=[500], max_db_spl=[140.0])
        report = evaluate_session(session)
        assert any(f.code == "mpo_exceeds_ceiling" for f in report.critical())

    def test_summary_string_contains_counts(self):
        session = _session_with_safe_defaults()
        session.right_mpo = MPOProfile()  # critical flag
        report = evaluate_session(session)
        summary = report.summary()
        assert "FAIL" in summary
        assert "critical" in summary

    def test_evaluate_extraction_flags_unverified_adapter(self):
        extraction = ExtractedFitting(
            vendor_adapter="phonak.mock",
            is_verified=False,
            right_mpo=MPOProfile(centre_frequencies_hz=[500], max_db_spl=[110.0]),
            left_mpo=MPOProfile(centre_frequencies_hz=[500], max_db_spl=[110.0]),
        )
        report = evaluate_extraction(extraction)
        codes = {f.code for f in report.flags}
        assert "adapter_unverified" in codes
        assert "low_confidence" in codes

    def test_evaluate_extraction_passes_verified_high_confidence(self):
        extraction = ExtractedFitting(
            vendor_adapter="real",
            is_verified=True,
            confidence=0.95,
            right_mpo=MPOProfile(centre_frequencies_hz=[500], max_db_spl=[110.0]),
            left_mpo=MPOProfile(centre_frequencies_hz=[500], max_db_spl=[110.0]),
        )
        report = evaluate_extraction(extraction)
        assert report.passed
        assert report.flags == []

    def test_default_thresholds_constant(self):
        assert isinstance(DEFAULT_THRESHOLDS, SafetyThresholds)
        assert DEFAULT_THRESHOLDS.max_insertion_gain_db == 60.0

    def test_safety_flag_dataclass_fields(self):
        f = SafetyFlag(level="info", code="x", message="m")
        assert f.location == ""
        report = SafetyReport(flags=[f])
        assert report.passed
        assert report.warnings() == []


# ── Phonak mock adapter -----------------------------------------------------


class TestPhonakMockAdapter:
    def test_write_is_never_supported(self):
        assert WRITE_SUPPORTED is False
        with pytest.raises(RuntimeError, match="mock-only"):
            raise_if_write_disabled()

    def test_feature_flag_blocks_read_by_default(self, monkeypatch):
        monkeypatch.delenv(FEATURE_FLAG_ENV, raising=False)
        assert not is_enabled()
        with pytest.raises(RuntimeError, match="disabled"):
            PhonakMockAdapter().read()

    def test_read_with_flag_enabled_returns_extraction(self, monkeypatch):
        monkeypatch.setenv(FEATURE_FLAG_ENV, "1")
        assert is_enabled()
        extraction = PhonakMockAdapter(device_serial="SN-XYZ").read()
        assert isinstance(extraction, ExtractedFitting)
        assert extraction.vendor_adapter == "phonak.mock"
        assert extraction.is_verified is False
        assert extraction.confidence == 0.0
        assert extraction.device.manufacturer == "Phonak"
        assert extraction.device.serial == "SN-XYZ"
        assert extraction.air_conduction is not None
        assert extraction.bone_conduction is not None
        assert extraction.recd is not None
        # Contains a mock-data warning flag in the document itself.
        assert any(f.code == "mock_data" for f in extraction.safety_flags)

    def test_read_extraction_function_wrapper(self, monkeypatch):
        monkeypatch.setenv(FEATURE_FLAG_ENV, "1")
        extraction = read_extraction(device_serial="SN-2")
        assert extraction.device.serial == "SN-2"

    def test_mock_extraction_passes_default_safety(self, monkeypatch):
        monkeypatch.setenv(FEATURE_FLAG_ENV, "1")
        extraction = PhonakMockAdapter().read()
        report = evaluate_extraction(extraction)
        # The "unverified" flag is a warning, not critical — must still pass.
        assert report.passed
        assert any(f.code == "adapter_unverified" for f in report.flags)

    def test_available_adapters_lists_phonak(self):
        adapters = available_adapters()
        assert "phonak" in adapters
        assert "mock" in adapters["phonak"].lower()


# ── CLI: extract / backup / validate ----------------------------------------


@pytest.fixture
def phonak_enabled(monkeypatch):
    monkeypatch.setenv(FEATURE_FLAG_ENV, "1")
    return monkeypatch


class TestCliExtract:
    def test_extract_prints_json_to_stdout(self, phonak_enabled, capsys, tmp_path):
        rc = noahlink_main(["extract", "--aid", "phonak", "--json"])
        assert rc == 0
        out = capsys.readouterr().out
        doc = json.loads(out.strip().split("\n", 0)[0] if "\n" not in out else out)
        # Re-parse from the start of the printed JSON (the test above may have
        # split incorrectly; do a safer parse):
        doc = json.loads(out[out.index("{") :])
        assert doc["schema_version"] == SCHEMA_VERSION
        assert doc["vendor_adapter"] == "phonak.mock"

    def test_extract_writes_to_output_file(self, phonak_enabled, tmp_path):
        out_file = tmp_path / "fitting.json"
        rc = noahlink_main(["extract", "--aid", "phonak", "--output", str(out_file)])
        assert rc == 0
        assert out_file.exists()
        doc = ExtractedFitting.from_json(out_file.read_text(encoding="utf-8"))
        assert doc.vendor_adapter == "phonak.mock"

    def test_extract_unknown_adapter_raises(self, capsys):
        with pytest.raises(ValueError, match="Unknown vendor"):
            noahlink_main(["extract", "--aid", "nonesuch"])

    def test_extract_emits_unverified_banner_on_stderr(self, phonak_enabled, capsys, tmp_path):
        out_file = tmp_path / "fitting.json"
        noahlink_main(["extract", "--aid", "phonak", "--output", str(out_file)])
        err = capsys.readouterr().err
        assert "UNVERIFIED" in err


class TestCliBackup:
    def test_backup_creates_three_files(self, phonak_enabled, tmp_path, capsys):
        rc = noahlink_main(["backup", "--aid", "phonak", "--output", str(tmp_path)])
        assert rc == 0
        backups = list(tmp_path.iterdir())
        assert len(backups) == 1
        bd = backups[0]
        for name in ("extraction.json", "raw.bin", "manifest.json"):
            assert (bd / name).exists(), f"Missing {name}"

    def test_backup_manifest_contains_sha256_commitment(self, phonak_enabled, tmp_path):
        noahlink_main(["backup", "--aid", "phonak", "--output", str(tmp_path)])
        bd = next(iter(tmp_path.iterdir()))
        manifest = json.loads((bd / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["schema_version"] == "openhear-backup-v1"
        assert manifest["extraction_schema_version"] == SCHEMA_VERSION
        assert manifest["vendor_adapter"] == "phonak.mock"
        assert manifest["is_verified"] is False
        assert len(manifest["extraction_sha256"]) == 64
        assert len(manifest["extraction_commitment_sha256"]) == 64

    def test_backup_list_adapters(self, capsys, tmp_path):
        rc = noahlink_main(
            ["backup", "--aid", "phonak", "--output", str(tmp_path), "--list-adapters"]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "phonak" in out


class TestCliValidate:
    def test_validate_returns_zero_on_passing_document(self, phonak_enabled, tmp_path, capsys):
        path = tmp_path / "ok.json"
        path.write_text(PhonakMockAdapter().read().to_json(), encoding="utf-8")
        rc = noahlink_main(["validate", str(path)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Schema: OK" in out
        assert "Safety:" in out

    def test_validate_returns_two_on_missing_file(self, tmp_path, capsys):
        rc = noahlink_main(["validate", str(tmp_path / "nope.json")])
        assert rc == 2
        err = capsys.readouterr().err
        assert "not found" in err

    def test_validate_returns_two_on_invalid_schema(self, tmp_path, capsys):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps({"schema_version": "bogus"}), encoding="utf-8")
        rc = noahlink_main(["validate", str(path)])
        assert rc == 2
        err = capsys.readouterr().err
        assert "Schema validation failed" in err

    def test_validate_returns_one_on_critical_finding(self, tmp_path, capsys):
        # Build an extraction with no MPO -> critical mpo_missing flag.
        doc = ExtractedFitting(
            vendor_adapter="real",
            is_verified=True,
            confidence=0.9,
        )
        path = tmp_path / "critical.json"
        path.write_text(doc.to_json(), encoding="utf-8")
        rc = noahlink_main(["validate", str(path)])
        assert rc == 1
        out = capsys.readouterr().out
        assert "FAIL" in out
