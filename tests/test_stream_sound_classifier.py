"""Tests for ``stream/sound_classifier.py``."""

from __future__ import annotations

import numpy as np

from stream.sound_classifier import (
    ClassifiedSound,
    classify_scores,
    map_label_to_sound_key,
    prepare_audio_window,
)


def test_prepare_audio_window_resamples_and_pads():
    samples = np.linspace(-1.0, 1.0, num=8_000, dtype=np.float32)
    window = prepare_audio_window(samples, 8_000)
    assert window.dtype == np.float32
    assert len(window) == 15_600


def test_map_label_to_sound_key():
    assert map_label_to_sound_key("Smoke detector, smoke alarm") == "alarm"
    assert map_label_to_sound_key("Doorbell") == "doorbell"
    assert map_label_to_sound_key("Speech") == "voice"


def test_classify_scores_selects_best_supported_label():
    result = classify_scores(
        {
            "Speech": 0.41,
            "Dog": 0.32,
            "Traffic noise, roadway noise": 0.87,
        }
    )
    assert isinstance(result, ClassifiedSound)
    assert result.sound_key == "traffic"
    assert result.sound_class_id == 5
    assert result.pattern_id == 5


def test_classify_scores_falls_back_to_silence():
    result = classify_scores({"Unknown label": 0.99, "Music": 0.1}, min_confidence=0.2)
    assert result.sound_key == "silence"
    assert result.confidence == 0.0
