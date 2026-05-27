"""Tests for ``hardware/tympan/audiogram_to_tympan.py``."""

from __future__ import annotations

from pathlib import Path

import pytest

from hardware.tympan.audiogram_to_tympan import (
    _TYMPAN_BAND_CENTRES,
    _compute_compression_ratios,
    _compute_gain_per_band,
    _compute_knee_per_band,
    _compute_mpo_per_band,
    _fill_template,
    _format_float_array,
    _interpolate_to_bands,
    generate_binaural_sketch,
    generate_tympan_sketch,
)


class TestInterpolateToBands:
    def test_interpolation_at_known_point(self):
        thresholds = [(500, 20), (1000, 40), (2000, 60)]
        result = _interpolate_to_bands(thresholds, [1000])
        assert result == [40.0]

    def test_linear_midpoint(self):
        thresholds = [(500, 20), (1000, 40)]
        result = _interpolate_to_bands(thresholds, [750])
        assert result == [30.0]

    def test_extrapolation_at_edges(self):
        thresholds = [(500, 20), (1000, 40)]
        result = _interpolate_to_bands(thresholds, [250, 2000])
        # np.interp clamps to the end values.
        assert result == [20.0, 40.0]


class TestComputeGainPerBand:
    def test_zero_below_normal(self):
        thresholds = [(500, 10), (1000, 15)]
        gains = _compute_gain_per_band(thresholds, [500, 1000])
        assert gains == [0.0, 0.0]

    def test_positive_above_normal(self):
        thresholds = [(500, 40), (1000, 50)]
        gains = _compute_gain_per_band(thresholds, [500, 1000])
        assert gains == [20.0, 30.0]


class TestComputeCompressionRatios:
    @pytest.mark.parametrize(
        "gain,expected",
        [(0, 1.2), (10, 1.2), (20, 1.5), (35, 2.0), (50, 2.5), (65, 3.0), (80, 3.5)],
    )
    def test_ratio_mapping(self, gain, expected):
        assert _compute_compression_ratios([gain]) == [expected]

    def test_multiple_bands(self):
        ratios = _compute_compression_ratios([5, 20, 45, 80])
        assert ratios == [1.2, 1.5, 2.5, 3.5]


class TestComputeMpoPerBand:
    def test_respects_minimum(self):
        mpo = _compute_mpo_per_band([(500, 5)], [500], safety_margin_db=50)
        # UCL estimate = 15 dB, minus 50 margin = -35; floored at 85.
        assert mpo[0] == 85.0

    def test_profound_loss_allows_higher_ucl(self):
        # Threshold 100 dB → UCL = threshold + 10 = 110, cap 120.
        mpo = _compute_mpo_per_band([(500, 100)], [500], safety_margin_db=5)
        # 110 - 5 = 105.
        assert mpo[0] == 105.0

    def test_normal_loss_capped_at_100_ucl(self):
        # Threshold 50 → UCL = 60 → mpo = 55 → floored at 85.
        mpo = _compute_mpo_per_band([(500, 50)], [500], safety_margin_db=5)
        assert mpo[0] == 85.0


class TestComputeKneePerBand:
    @pytest.mark.parametrize("pta,expected", [(30, 45.0), (50, 40.0), (65, 35.0), (85, 30.0)])
    def test_pta_mapping(self, pta, expected):
        knees = _compute_knee_per_band([10, 20, 30], pta)
        assert knees == [expected, expected, expected]

    def test_length_matches_input(self):
        knees = _compute_knee_per_band([0] * 8, 50)
        assert len(knees) == 8


class TestFormatFloatArray:
    def test_basic(self):
        assert _format_float_array([1.0, 2.5, 3.0]) == "{1.0, 2.5, 3.0}"

    def test_custom_decimals(self):
        assert _format_float_array([1.23456], decimals=3) == "{1.235}"


class TestFillTemplate:
    def test_replaces_placeholders(self):
        template = "Hello {{NAME}}!  You are {{ROLE}}."
        result = _fill_template(template, {"NAME": "Alice", "ROLE": "admin"})
        assert result == "Hello Alice!  You are admin."

    def test_missing_placeholder_preserved(self):
        result = _fill_template("{{A}} {{B}}", {"A": "x"})
        assert result == "x {{B}}"


class TestGenerateSketch:
    def test_generates_file_and_substitutes(self, burgess_audiogram_path, tmp_path: Path):
        output = tmp_path / "sketch.ino"
        sketch = generate_tympan_sketch(
            burgess_audiogram_path, str(output), ear="right",
        )
        assert output.exists()
        assert sketch == output.read_text(encoding="utf-8")
        # Template placeholders should have been replaced.
        assert "{{" not in sketch
        assert "}}" not in sketch

    def test_contains_expected_metadata(self, burgess_audiogram_path, tmp_path: Path):
        output = tmp_path / "sketch.ino"
        sketch = generate_tympan_sketch(
            burgess_audiogram_path, str(output), ear="right",
        )
        assert "Right ear" in sketch
        # The audiogram's subject name should appear as AUDIOGRAM_SOURCE.
        assert "Lewis Burgess" in sketch
        # 8-band default configuration.
        assert str(len(_TYMPAN_BAND_CENTRES)) in sketch

    def test_binaural_uses_worse_ear(self, burgess_audiogram_path, tmp_path: Path, capsys):
        output = tmp_path / "sketch_binaural.ino"
        generate_binaural_sketch(burgess_audiogram_path, str(output))
        captured = capsys.readouterr()
        # The Burgess audiogram has the left ear as worse (PTA 73.75 vs 72.5).
        assert "left ear" in captured.out

    def test_ear_left(self, burgess_audiogram_path, tmp_path: Path):
        output = tmp_path / "sketch_left.ino"
        sketch = generate_tympan_sketch(
            burgess_audiogram_path, str(output), ear="left",
        )
        assert "Left ear" in sketch
