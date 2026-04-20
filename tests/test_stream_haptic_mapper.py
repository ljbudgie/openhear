"""Tests for ``stream/haptic_mapper.py``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from stream.haptic_mapper import (
    PATTERN_IDS,
    SOUND_CLASS_IDS,
    HapticMapper,
    SOUND_PROFILES,
    threshold_to_scale,
)


@pytest.fixture
def legacy_audiogram_path(tmp_path: Path) -> str:
    path = tmp_path / "legacy_audiogram.json"
    path.write_text(
        json.dumps(
            {
                "patient_id": "001",
                "audiogram": {
                    "right": {"250": 20, "500": 35, "1000": 45, "2000": 60, "4000": 75, "8000": 80},
                    "left": {"250": 15, "500": 30, "1000": 40, "2000": 55, "4000": 70, "8000": 75},
                },
            }
        ),
        encoding="utf-8",
    )
    return str(path)


class TestThresholdToScale:
    @pytest.mark.parametrize(
        ("threshold", "expected"),
        [(10, 0.25), (20, 0.5), (39.9, 0.5), (40, 0.75), (60, 0.75), (61, 1.0)],
    )
    def test_bucket_mapping(self, threshold, expected):
        assert threshold_to_scale(threshold) == expected


class TestHapticMapper:
    def test_stable_sound_and_pattern_ids(self):
        assert SOUND_CLASS_IDS == {
            "silence": 0,
            "voice": 1,
            "doorbell": 2,
            "alarm": 3,
            "dog": 4,
            "traffic": 5,
            "media": 6,
        }
        assert PATTERN_IDS == SOUND_CLASS_IDS

    def test_legacy_audiogram_is_supported(self, legacy_audiogram_path: str):
        mapper = HapticMapper(legacy_audiogram_path)
        sound_class_id, intensity, pattern_id = mapper.build_command("alarm")
        assert sound_class_id == SOUND_PROFILES["alarm"].sound_class_id
        assert pattern_id == SOUND_PROFILES["alarm"].pattern_id
        assert intensity == 255

    def test_interpolates_dominant_frequency(self, audiogram_path: str):
        mapper = HapticMapper(audiogram_path)
        assert mapper.get_threshold(3150, "right") == pytest.approx(55.75)

    def test_confidence_and_comfort_scale_affect_intensity(self, audiogram_path: str):
        mapper = HapticMapper(audiogram_path, comfort_scale=0.5)
        intensity = mapper.get_intensity("voice", confidence=0.5)
        assert intensity == 48

    def test_silence_maps_to_zero(self, audiogram_path: str):
        mapper = HapticMapper(audiogram_path)
        assert mapper.build_command("silence") == (0, 0, 0)

    def test_average_ear_strategy_is_supported(self, legacy_audiogram_path: str):
        mapper = HapticMapper(legacy_audiogram_path, ear_strategy="average")
        assert mapper.get_intensity("voice") == 191
