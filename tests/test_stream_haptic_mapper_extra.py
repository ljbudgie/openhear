"""Additional tests for ``stream/haptic_mapper.py`` – covering the private
helpers ``_combine_ears`` and ``_interpolate_threshold`` that the main test
file does not exercise."""

from __future__ import annotations

import pytest

from stream.haptic_mapper import (
    HapticMapper,
    _combine_ears,
    _interpolate_threshold,
    clamp_uint8,
)


class TestClampUint8:
    def test_clamps_below_zero(self):
        assert clamp_uint8(-10.0) == 0

    def test_clamps_above_255(self):
        assert clamp_uint8(300.0) == 255

    def test_rounds_correctly(self):
        assert clamp_uint8(127.5) == 128

    def test_zero(self):
        assert clamp_uint8(0.0) == 0

    def test_255(self):
        assert clamp_uint8(255.0) == 255


class TestCombineEars:
    def test_worst_returns_max(self):
        assert _combine_ears(30.0, 50.0, strategy="worst") == 50.0
        assert _combine_ears(70.0, 40.0, strategy="worst") == 70.0

    def test_average_returns_mean(self):
        result = _combine_ears(30.0, 50.0, strategy="average")
        assert result == pytest.approx(40.0)

    def test_better_returns_min(self):
        assert _combine_ears(30.0, 50.0, strategy="better") == 30.0
        assert _combine_ears(70.0, 40.0, strategy="better") == 40.0

    def test_case_insensitive_strategy(self):
        assert _combine_ears(30.0, 50.0, strategy="WORST") == 50.0
        assert _combine_ears(30.0, 50.0, strategy="Average") == pytest.approx(40.0)
        assert _combine_ears(30.0, 50.0, strategy="BETTER") == 30.0

    def test_strip_whitespace_strategy(self):
        assert _combine_ears(30.0, 50.0, strategy="  worst  ") == 50.0

    def test_invalid_strategy_raises(self):
        with pytest.raises(ValueError, match="ear_strategy"):
            _combine_ears(30.0, 50.0, strategy="median")


class TestInterpolateThreshold:
    _THRESHOLDS = [(250, 20), (500, 30), (1000, 40), (2000, 50), (4000, 60)]

    def test_exact_match_first_entry(self):
        result = _interpolate_threshold(self._THRESHOLDS, 250)
        assert result == pytest.approx(20.0)

    def test_exact_match_middle_entry(self):
        result = _interpolate_threshold(self._THRESHOLDS, 1000)
        assert result == pytest.approx(40.0)

    def test_below_range_clamps_to_first(self):
        result = _interpolate_threshold(self._THRESHOLDS, 100)
        assert result == pytest.approx(20.0)

    def test_above_range_clamps_to_last(self):
        result = _interpolate_threshold(self._THRESHOLDS, 8000)
        assert result == pytest.approx(60.0)

    def test_interpolates_midpoint(self):
        # Midpoint between 500 (30 dB) and 1000 (40 dB) → 750 Hz → 35 dB
        result = _interpolate_threshold(self._THRESHOLDS, 750)
        assert result == pytest.approx(35.0)

    def test_interpolates_at_quarter(self):
        # 25% between 1000 (40 dB) and 2000 (50 dB) → 1250 Hz → 42.5 dB
        result = _interpolate_threshold(self._THRESHOLDS, 1250)
        assert result == pytest.approx(42.5)

    def test_empty_threshold_list_raises(self):
        with pytest.raises(ValueError, match="empty"):
            _interpolate_threshold([], 1000)

    def test_duplicate_frequencies_returns_first(self):
        """When two entries share the same frequency, return the first value."""
        thresholds = [(500, 30), (500, 50), (1000, 40)]
        result = _interpolate_threshold(thresholds, 500)
        assert result == pytest.approx(30.0)


class TestHapticMapperGetSoundProfileError:
    def test_unknown_sound_key_raises(self, audiogram_path: str):
        mapper = HapticMapper(audiogram_path)
        with pytest.raises(KeyError, match="Unsupported sound class"):
            mapper.get_sound_profile("thunderstorm")

    def test_better_ear_strategy(self, audiogram_path: str):
        mapper = HapticMapper(audiogram_path, ear_strategy="better")
        intensity = mapper.get_intensity("voice")
        # "better" ear has lower threshold → lower intensity bucket
        assert 0 <= intensity <= 255

    def test_negative_confidence_clamped_to_zero(self, audiogram_path: str):
        mapper = HapticMapper(audiogram_path)
        assert mapper.get_intensity("voice", confidence=-1.0) == 0

    def test_zero_confidence_gives_zero(self, audiogram_path: str):
        mapper = HapticMapper(audiogram_path)
        assert mapper.get_intensity("voice", confidence=0.0) == 0
