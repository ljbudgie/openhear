"""Tests for ``audiogram/loader.py``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from audiogram.loader import (
    _resolve_ear_key,
    compare_audiograms,
    get_gain_profile,
    get_pta,
    get_severity,
    get_thresholds,
    load_audiogram,
)


class TestLoadAudiogram:
    def test_loads_valid_audiogram(self, audiogram_path):
        data = load_audiogram(audiogram_path)
        assert data["subject"] == "Test Subject"
        assert data["format_version"] == "openhear-audiogram-v1"

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_audiogram(str(tmp_path / "nope.json"))

    def test_missing_required_fields(self, tmp_path: Path):
        bad = {"subject": "x", "format_version": "openhear-audiogram-v1"}
        p = tmp_path / "bad.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        with pytest.raises(ValueError, match="missing required fields"):
            load_audiogram(str(p))

    def test_wrong_format_version(self, tmp_path: Path, sample_audiogram_dict: dict):
        sample_audiogram_dict["format_version"] = "other-v2"
        p = tmp_path / "wrong.json"
        p.write_text(json.dumps(sample_audiogram_dict), encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported format version"):
            load_audiogram(str(p))

    def test_loads_legacy_openhear_v010_format(self, tmp_path: Path):
        legacy = {
            "patient_id": "001",
            "audiogram": {
                "right": {"250": 20, "500": 35, "1000": 45, "2000": 60, "4000": 75, "8000": 80},
                "left": {"250": 25, "500": 40, "1000": 50, "2000": 65, "4000": 70, "8000": 75},
            },
        }
        p = tmp_path / "legacy.json"
        p.write_text(json.dumps(legacy), encoding="utf-8")

        data = load_audiogram(str(p))

        assert data["subject"] == "001"
        assert data["format_version"] == "openhear-audiogram-v1"
        assert data["right_ear"]["thresholds"][0] == {"freq_hz": 250, "db_hl": 20}

    def test_missing_thresholds_array(self, tmp_path: Path, sample_audiogram_dict: dict):
        del sample_audiogram_dict["right_ear"]["thresholds"]
        sample_audiogram_dict["right_ear"]["symbol"] = "O"
        p = tmp_path / "no_thresholds.json"
        p.write_text(json.dumps(sample_audiogram_dict), encoding="utf-8")
        with pytest.raises(ValueError, match="missing the 'thresholds' array"):
            load_audiogram(str(p))

    def test_missing_threshold_fields(self, tmp_path: Path, sample_audiogram_dict: dict):
        sample_audiogram_dict["left_ear"]["thresholds"] = [{"freq_hz": 500}]
        p = tmp_path / "bad_threshold.json"
        p.write_text(json.dumps(sample_audiogram_dict), encoding="utf-8")
        with pytest.raises(ValueError, match="freq_hz.*db_hl"):
            load_audiogram(str(p))


class TestGetThresholds:
    def test_returns_sorted_tuples(self, sample_audiogram_dict):
        thresh = get_thresholds(sample_audiogram_dict, "right")
        freqs = [f for f, _ in thresh]
        assert freqs == sorted(freqs)
        assert thresh[0] == (250, 20)

    def test_left_ear(self, sample_audiogram_dict):
        thresh = get_thresholds(sample_audiogram_dict, "left")
        assert (250, 25) in thresh
        assert (8000, 75) in thresh

    def test_invalid_ear(self, sample_audiogram_dict):
        with pytest.raises(ValueError, match="ear must be"):
            get_thresholds(sample_audiogram_dict, "middle")


class TestGetPta:
    def test_right_pta(self, sample_audiogram_dict):
        # 500, 1000, 2000, 4000 → 30, 40, 50, 60 → mean = 45
        assert get_pta(sample_audiogram_dict, "right") == 45.0

    def test_left_pta(self, sample_audiogram_dict):
        # 35, 45, 55, 65 → mean = 50
        assert get_pta(sample_audiogram_dict, "left") == 50.0

    def test_pta_insufficient_frequencies(self, sample_audiogram_dict):
        # Remove 4000 Hz from right ear.
        sample_audiogram_dict["right_ear"]["thresholds"] = [
            t for t in sample_audiogram_dict["right_ear"]["thresholds"]
            if t["freq_hz"] != 4000
        ]
        with pytest.raises(ValueError, match="missing thresholds"):
            get_pta(sample_audiogram_dict, "right")


class TestGetSeverity:
    @pytest.mark.parametrize(
        "db,expected",
        [
            (0, "normal"),
            (20, "normal"),
            (25, "normal"),
            (26, "mild"),
            (40, "mild"),
            (41, "moderate"),
            (55, "moderate"),
            (56, "moderately-severe"),
            (70, "moderately-severe"),
            (71, "severe"),
            (90, "severe"),
            (91, "profound"),
            (120, "profound"),
        ],
    )
    def test_classification_boundaries(self, db, expected):
        assert get_severity(db) == expected


class TestGetGainProfile:
    def test_gain_profile(self, sample_audiogram_dict):
        gains = get_gain_profile(sample_audiogram_dict, "right")
        d = dict(gains)
        # 20 dB HL → 0 gain (already at normal)
        assert d[250] == 0
        # 30 dB HL → 10 dB gain
        assert d[500] == 10
        assert d[8000] == 50

    def test_gain_never_negative(self, sample_audiogram_dict):
        sample_audiogram_dict["right_ear"]["thresholds"] = [
            {"freq_hz": 500, "db_hl": 5},
            {"freq_hz": 1000, "db_hl": 10},
            {"freq_hz": 2000, "db_hl": 20},
            {"freq_hz": 4000, "db_hl": 25},
        ]
        gains = get_gain_profile(sample_audiogram_dict, "right")
        assert all(g >= 0 for _, g in gains)


class TestCompareAudiograms:
    def test_identical_audiograms(self, audiogram_path):
        result = compare_audiograms(audiogram_path, audiogram_path)
        assert all(diff == 0 for _, diff in result["right"])
        assert all(diff == 0 for _, diff in result["left"])
        assert result["right_pta_diff"] == 0.0
        assert result["left_pta_diff"] == 0.0

    def test_worsened_audiogram(self, tmp_path: Path, sample_audiogram_dict: dict):
        a_path = tmp_path / "a.json"
        a_path.write_text(json.dumps(sample_audiogram_dict), encoding="utf-8")

        worse = json.loads(json.dumps(sample_audiogram_dict))
        for ear in ("right_ear", "left_ear"):
            for t in worse[ear]["thresholds"]:
                t["db_hl"] += 10
        b_path = tmp_path / "b.json"
        b_path.write_text(json.dumps(worse), encoding="utf-8")

        result = compare_audiograms(str(a_path), str(b_path))
        for _, diff in result["right"]:
            assert diff == 10
        assert result["right_pta_diff"] == 10.0
        assert result["left_pta_diff"] == 10.0

    def test_comparison_pta_handles_missing(
        self, tmp_path: Path, sample_audiogram_dict: dict
    ):
        # Remove 4000 Hz from one file → its PTA calc fails → diff is None.
        a_path = tmp_path / "a.json"
        a_path.write_text(json.dumps(sample_audiogram_dict), encoding="utf-8")
        incomplete = json.loads(json.dumps(sample_audiogram_dict))
        incomplete["right_ear"]["thresholds"] = [
            t for t in incomplete["right_ear"]["thresholds"]
            if t["freq_hz"] != 4000
        ]
        b_path = tmp_path / "b.json"
        b_path.write_text(json.dumps(incomplete), encoding="utf-8")

        result = compare_audiograms(str(a_path), str(b_path))
        assert result["right_pta_diff"] is None
        # Left side still computes because both files have full left data.
        assert result["left_pta_diff"] == 0.0


class TestResolveEarKey:
    @pytest.mark.parametrize(
        "ear,expected",
        [
            ("right", "right_ear"),
            ("left", "left_ear"),
            ("RIGHT", "right_ear"),
            ("  Left  ", "left_ear"),
        ],
    )
    def test_valid(self, ear, expected):
        assert _resolve_ear_key(ear) == expected

    def test_invalid(self):
        with pytest.raises(ValueError):
            _resolve_ear_key("both")


class TestBundledSample:
    """Sanity-check the bundled Burgess 2021 audiogram loads cleanly."""

    def test_loads(self, burgess_audiogram_path):
        data = load_audiogram(burgess_audiogram_path)
        assert data["subject"] == "Lewis Burgess"

    def test_pta_values(self, burgess_audiogram_path):
        data = load_audiogram(burgess_audiogram_path)
        # Right: 50 + 75 + 80 + 85 = 290 / 4 = 72.5
        assert get_pta(data, "right") == 72.5
        # Left:  55 + 75 + 80 + 85 = 295 / 4 = 73.75; Python's banker's
        # rounding in round(73.75, 1) yields 73.8.
        assert get_pta(data, "left") == 73.8

    def test_severity_matches_expected(self, burgess_audiogram_path):
        data = load_audiogram(burgess_audiogram_path)
        pta = get_pta(data, "right")
        assert get_severity(int(pta)) == "severe"
