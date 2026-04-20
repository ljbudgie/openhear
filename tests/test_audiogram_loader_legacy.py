"""Tests for the legacy v0.1.0 normalisation path in ``audiogram/loader.py``.

These tests cover error paths in ``_normalise_legacy_audiogram`` and
``_legacy_threshold_map_to_array``, plus the ``ValueError`` swallow logic
in ``compare_audiograms`` when one audiogram is missing PTA frequencies.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from audiogram.loader import compare_audiograms, load_audiogram


def _write(tmp_path: Path, name: str, payload: dict) -> str:
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


class TestLegacyNormalisationErrors:
    def test_missing_one_ear_in_legacy_audiogram(self, tmp_path: Path):
        """A legacy file missing an ear must produce a clear error."""
        legacy = {
            "patient_id": "001",
            "audiogram": {
                "right": {"500": 35, "1000": 45, "2000": 60, "4000": 75},
                # 'left' deliberately omitted.
            },
        }
        path = _write(tmp_path, "missing_left.json", legacy)
        with pytest.raises(ValueError, match="missing ear data for"):
            load_audiogram(path)

    def test_missing_both_ears_in_legacy_audiogram(self, tmp_path: Path):
        legacy = {"patient_id": "001", "audiogram": {}}
        path = _write(tmp_path, "no_ears.json", legacy)
        with pytest.raises(ValueError, match="missing ear data for.*left.*right"):
            load_audiogram(path)

    def test_legacy_threshold_map_must_be_non_empty(self, tmp_path: Path):
        legacy = {
            "patient_id": "001",
            "audiogram": {
                "right": {},
                "left": {"500": 35, "1000": 45, "2000": 60, "4000": 75},
            },
        }
        path = _write(tmp_path, "empty_right.json", legacy)
        with pytest.raises(ValueError, match="non-empty object"):
            load_audiogram(path)

    def test_legacy_threshold_values_must_be_integer_like(self, tmp_path: Path):
        legacy = {
            "patient_id": "001",
            "audiogram": {
                "right": {"500": "loud", "1000": 45, "2000": 60, "4000": 75},
                "left": {"500": 35, "1000": 45, "2000": 60, "4000": 75},
            },
        }
        path = _write(tmp_path, "bad_values.json", legacy)
        with pytest.raises(ValueError, match="integer-like"):
            load_audiogram(path)


class TestCompareAudiograms:
    def test_skips_pta_diff_when_one_audiogram_misses_pta_freqs(
        self, tmp_path: Path, sample_audiogram_dict: dict
    ):
        """If one audiogram has no PTA-eligible frequencies on an ear, the
        ``*_pta_diff`` value must be ``None`` instead of raising."""
        path_full = _write(tmp_path, "full.json", sample_audiogram_dict)

        # Build a second audiogram whose right ear contains *only* a
        # non-PTA frequency (250 Hz).  PTA frequencies are 500/1000/2000/4000,
        # so ``get_pta`` will raise ``ValueError`` for the right ear.
        sparse = json.loads(json.dumps(sample_audiogram_dict))
        sparse["right_ear"]["thresholds"] = [{"freq_hz": 250, "db_hl": 20}]
        path_sparse = _write(tmp_path, "sparse.json", sparse)

        result = compare_audiograms(path_full, path_sparse)
        # Right ear PTA cannot be computed for the sparse audiogram → None.
        assert result["right_pta_diff"] is None
        # Left ear is intact in both files → numeric diff.
        assert isinstance(result["left_pta_diff"], float)

    def test_skips_pta_diff_when_first_audiogram_misses_pta_freqs(
        self, tmp_path: Path, sample_audiogram_dict: dict
    ):
        """The same ValueError suppression must apply to the *first* audiogram."""
        path_full = _write(tmp_path, "full.json", sample_audiogram_dict)
        sparse = json.loads(json.dumps(sample_audiogram_dict))
        sparse["right_ear"]["thresholds"] = [{"freq_hz": 250, "db_hl": 20}]
        path_sparse = _write(tmp_path, "sparse.json", sparse)

        # Pass the sparse audiogram FIRST so ``pta_a`` raises and is swallowed.
        result = compare_audiograms(path_sparse, path_full)
        assert result["right_pta_diff"] is None
        assert isinstance(result["left_pta_diff"], float)
