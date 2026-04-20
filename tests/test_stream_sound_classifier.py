"""Tests for ``stream/sound_classifier.py``."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from stream import sound_classifier
from stream.sound_classifier import (
    DEFAULT_MIN_CONFIDENCE,
    WINDOW_SECONDS,
    ClassifiedSound,
    YamnetClassifier,
    _load_labels,
    _load_tflite_interpreter,
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


def test_load_labels_supports_plain_text(tmp_path):
    labels_path = tmp_path / "labels.txt"
    labels_path.write_text("Speech\nDog\n", encoding="utf-8")
    assert _load_labels(str(labels_path)) == ["Speech", "Dog"]


def test_load_labels_supports_official_yamnet_csv():
    labels_path = (
        Path(__file__).resolve().parents[1] / "stream" / "data" / "yamnet_class_map.csv"
    )
    labels = _load_labels(str(labels_path))
    assert len(labels) == 521
    assert labels[0] == "Speech"
    assert labels[349] == "Doorbell"
    assert labels[-1] == "Field recording"


# ── Additional coverage ──────────────────────────────────────────────────────


def test_map_label_to_sound_key_returns_none_for_unknown():
    assert map_label_to_sound_key("Whatever weird sound") is None


def test_map_label_to_sound_key_recognises_silence():
    assert map_label_to_sound_key("Silence") == "silence"


def test_classify_scores_skips_unsupported_labels():
    """Unsupported labels with the highest score should be ignored entirely."""
    result = classify_scores({"Mystery noise": 0.99, "Speech": 0.5}, min_confidence=0.2)
    assert result.sound_key == "voice"
    assert result.source_label == "Speech"


def test_classify_scores_dominant_silence_below_threshold():
    """A purely-silence label should still resolve to the silence packet."""
    result = classify_scores({"Silence": 0.05}, min_confidence=DEFAULT_MIN_CONFIDENCE)
    assert result.sound_key == "silence"


def test_prepare_audio_window_downmixes_stereo():
    stereo = np.column_stack([
        np.ones(8000, dtype=np.float32),
        -np.ones(8000, dtype=np.float32),
    ])
    window = prepare_audio_window(stereo, 8_000)
    # The two channels cancel; the average is zero everywhere.
    assert np.allclose(window, 0.0)


def test_prepare_audio_window_truncates_when_input_too_long():
    samples = np.zeros(int(round(16_000 * (WINDOW_SECONDS + 0.5))), dtype=np.float32)
    window = prepare_audio_window(samples, 16_000)
    assert len(window) == int(round(16_000 * WINDOW_SECONDS))


# ── _load_labels edge cases ───────────────────────────────────────────────────


def test_load_labels_empty_file_returns_empty_list(tmp_path):
    labels_path = tmp_path / "empty.txt"
    labels_path.write_text("", encoding="utf-8")
    assert _load_labels(str(labels_path)) == []


def test_load_labels_falls_back_to_rightmost_column(tmp_path):
    """CSV without ``display_name`` header uses the rightmost populated column."""
    labels_path = tmp_path / "labels.csv"
    labels_path.write_text("1,fooLabel\n2,barLabel\n", encoding="utf-8")
    labels = _load_labels(str(labels_path))
    assert labels == ["fooLabel", "barLabel"]


def test_load_labels_skips_blank_rows(tmp_path):
    labels_path = tmp_path / "labels.txt"
    labels_path.write_text("Speech\n\n\nDog\n   \n", encoding="utf-8")
    assert _load_labels(str(labels_path)) == ["Speech", "Dog"]


# ── ClassifiedSound properties ────────────────────────────────────────────────


def test_classified_sound_exposes_profile_metadata():
    classified = ClassifiedSound("doorbell", 0.9, "Doorbell")
    assert classified.sound_class_id == 2
    assert classified.pattern_id == 2
    assert classified.dominant_frequency_hz == 2000


def test_classified_sound_silence_has_no_dominant_frequency():
    classified = ClassifiedSound("silence", 0.0, "silence")
    assert classified.dominant_frequency_hz is None


# ── YamnetClassifier with stub interpreter ────────────────────────────────────


class _StubInterpreter:
    """Bare-minimum tflite Interpreter stand-in."""

    def __init__(self, scores, *, input_shape=(1, 15_600)):
        self._scores = np.asarray(scores, dtype=np.float32)
        self._input_shape = input_shape
        self.allocate_called = False
        self.invoke_called = False
        self.last_input = None

    def allocate_tensors(self):
        self.allocate_called = True

    def get_input_details(self):
        return [{"index": 0, "shape": self._input_shape}]

    def get_output_details(self):
        return [{"index": 1}]

    def set_tensor(self, index, tensor):
        self.last_input = tensor

    def invoke(self):
        self.invoke_called = True

    def get_tensor(self, index):
        return self._scores


def test_yamnet_classifier_classify_window_returns_top_class(tmp_path):
    labels_path = tmp_path / "labels.txt"
    labels_path.write_text("Speech\nDog\nTraffic noise, roadway noise\n", encoding="utf-8")
    # Three frame scores → highest weight on traffic.
    interpreter = _StubInterpreter(
        scores=[[0.05, 0.2, 0.85], [0.01, 0.1, 0.9], [0.0, 0.05, 0.95]],
    )

    with patch.object(sound_classifier, "_load_tflite_interpreter", return_value=interpreter):
        classifier = YamnetClassifier("dummy.tflite", str(labels_path))

    samples = np.zeros(15_600, dtype=np.float32)
    result = classifier.classify_window(samples, 16_000)

    assert interpreter.allocate_called
    assert interpreter.invoke_called
    # The 2-D input shape causes the tensor to be batched.
    assert classifier._input_details[0]["shape"] == (1, 15_600)
    assert interpreter.last_input.shape == (1, 15_600)
    assert result.sound_key == "traffic"


def test_yamnet_classifier_classify_window_handles_1d_input_shape(tmp_path):
    labels_path = tmp_path / "labels.txt"
    labels_path.write_text("Speech\n", encoding="utf-8")
    interpreter = _StubInterpreter(scores=[0.95], input_shape=(15_600,))

    with patch.object(sound_classifier, "_load_tflite_interpreter", return_value=interpreter):
        classifier = YamnetClassifier("dummy.tflite", str(labels_path))

    classifier.classify_window(np.zeros(15_600, dtype=np.float32), 16_000)
    # 1-D input shape ⇒ no leading batch axis is added.
    assert interpreter.last_input.shape == (15_600,)


def test_load_tflite_interpreter_uses_tensorflow_when_no_tflite_runtime(monkeypatch):
    """When ``tflite_runtime`` is missing, fall back to ``tensorflow.lite``."""
    monkeypatch.setitem(sys.modules, "tflite_runtime", None)

    fake_tf = types.ModuleType("tensorflow")
    fake_lite = types.ModuleType("tensorflow.lite")

    captured = {}

    class _FakeInterpreter:
        def __init__(self, model_path):
            captured["model_path"] = model_path

    fake_lite.Interpreter = _FakeInterpreter
    fake_tf.lite = fake_lite
    monkeypatch.setitem(sys.modules, "tensorflow", fake_tf)
    monkeypatch.setitem(sys.modules, "tensorflow.lite", fake_lite)

    interp = _load_tflite_interpreter("/tmp/model.tflite")
    assert isinstance(interp, _FakeInterpreter)
    assert captured["model_path"] == "/tmp/model.tflite"

