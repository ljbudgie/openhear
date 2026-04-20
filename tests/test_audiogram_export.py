"""Tests for ``audiogram/export.py``."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from audiogram.export import to_csv, to_dsp_config, to_markdown


class TestToCsv:
    def test_writes_expected_rows(self, audiogram_path, tmp_path: Path):
        out = tmp_path / "out.csv"
        to_csv(audiogram_path, str(out))

        rows = list(csv.reader(out.open()))
        assert rows[0] == ["ear", "freq_hz", "db_hl"]

        # Should contain one row per (ear, frequency).
        body = rows[1:]
        ears = {r[0] for r in body}
        assert ears == {"right", "left"}
        # 6 frequencies × 2 ears = 12 rows
        assert len(body) == 12

    def test_csv_values_are_integers(self, audiogram_path, tmp_path: Path):
        out = tmp_path / "out.csv"
        to_csv(audiogram_path, str(out))
        rows = list(csv.reader(out.open()))[1:]
        for _, freq, db in rows:
            int(freq)
            int(db)


class TestToMarkdown:
    def test_contains_headers_and_tables(self, audiogram_path):
        md = to_markdown(audiogram_path)
        assert "# Audiogram — Test Subject" in md
        assert "## Right Ear (O)" in md
        assert "## Left Ear (X)" in md
        assert "**PTA:**" in md
        assert "| Frequency (Hz) | Threshold (dB HL) | Severity |" in md

    def test_includes_notes_when_present(self, audiogram_path):
        md = to_markdown(audiogram_path)
        assert "Synthetic audiogram" in md

    def test_handles_missing_notes(self, tmp_path: Path, sample_audiogram_dict):
        import json
        sample_audiogram_dict.pop("notes", None)
        p = tmp_path / "a.json"
        p.write_text(json.dumps(sample_audiogram_dict), encoding="utf-8")
        md = to_markdown(str(p))
        assert "Notes" not in md

    def test_handles_pta_insufficient(self, tmp_path: Path, sample_audiogram_dict):
        import json
        # Remove 4000 Hz from right ear so PTA cannot be computed.
        sample_audiogram_dict["right_ear"]["thresholds"] = [
            t for t in sample_audiogram_dict["right_ear"]["thresholds"]
            if t["freq_hz"] != 4000
        ]
        p = tmp_path / "a.json"
        p.write_text(json.dumps(sample_audiogram_dict), encoding="utf-8")
        md = to_markdown(str(p))
        assert "insufficient frequencies" in md


class TestToDspConfig:
    def test_returns_expected_keys(self, audiogram_path):
        cfg = to_dsp_config(audiogram_path, "right")
        for key in (
            "gain_profile",
            "compression_bands",
            "compression_knee_dbfs",
            "noise_floor_multiplier",
            "voice_clarity_gain",
            "voice_clarity_low_hz",
            "voice_clarity_high_hz",
            "pta",
            "severity",
        ):
            assert key in cfg

    def test_gain_profile_matches_loader(self, audiogram_path):
        from audiogram.loader import get_gain_profile, load_audiogram

        ag = load_audiogram(audiogram_path)
        cfg = to_dsp_config(audiogram_path, "right")
        assert cfg["gain_profile"] == get_gain_profile(ag, "right")

    def test_compression_bands_match_gain_count(self, audiogram_path):
        cfg = to_dsp_config(audiogram_path, "right")
        assert len(cfg["compression_bands"]) == len(cfg["gain_profile"])

    @pytest.mark.parametrize(
        "gain_db,expected_ratio",
        [(0, 1.2), (10, 1.2), (20, 1.5), (35, 2.0), (50, 2.5), (65, 3.0), (80, 3.5)],
    )
    def test_compression_ratio_mapping(
        self, tmp_path: Path, sample_audiogram_dict, gain_db, expected_ratio
    ):
        import json

        # Set every right-ear threshold to gain_db + 20 so get_gain_profile
        # returns gain_db at every frequency.
        for t in sample_audiogram_dict["right_ear"]["thresholds"]:
            t["db_hl"] = gain_db + 20
        p = tmp_path / "a.json"
        p.write_text(json.dumps(sample_audiogram_dict), encoding="utf-8")

        cfg = to_dsp_config(str(p), "right")
        assert all(r == expected_ratio for _, r in cfg["compression_bands"])

    @pytest.mark.parametrize(
        "pta_db,expected_knee",
        [(30, -35.0), (50, -40.0), (65, -45.0), (85, -50.0)],
    )
    def test_knee_point_mapping(
        self, tmp_path: Path, sample_audiogram_dict, pta_db, expected_knee
    ):
        import json

        # Give every PTA frequency a threshold of pta_db.
        for t in sample_audiogram_dict["right_ear"]["thresholds"]:
            t["db_hl"] = pta_db
        p = tmp_path / "a.json"
        p.write_text(json.dumps(sample_audiogram_dict), encoding="utf-8")

        cfg = to_dsp_config(str(p), "right")
        assert cfg["compression_knee_dbfs"] == expected_knee

    @pytest.mark.parametrize(
        "pta_db,expected_mult,expected_voice_gain",
        [(30, 1.1, 1.4), (50, 1.2, 1.6), (65, 1.3, 1.8), (85, 1.4, 2.0)],
    )
    def test_noise_and_voice_mapping(
        self, tmp_path: Path, sample_audiogram_dict, pta_db,
        expected_mult, expected_voice_gain,
    ):
        import json

        for t in sample_audiogram_dict["right_ear"]["thresholds"]:
            t["db_hl"] = pta_db
        p = tmp_path / "a.json"
        p.write_text(json.dumps(sample_audiogram_dict), encoding="utf-8")

        cfg = to_dsp_config(str(p), "right")
        assert cfg["noise_floor_multiplier"] == expected_mult
        assert cfg["voice_clarity_gain"] == expected_voice_gain

    def test_voice_clarity_band_constant(self, audiogram_path):
        cfg = to_dsp_config(audiogram_path, "right")
        assert cfg["voice_clarity_low_hz"] == 1000.0
        assert cfg["voice_clarity_high_hz"] == 4000.0
