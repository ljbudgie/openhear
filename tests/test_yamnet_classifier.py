"""Tests for ``yamnet_classifier.py``."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from stream.sound_classifier import ClassifiedSound
from yamnet_classifier import LiveYamnetClassifier, bundled_labels_path


class _StubClassifier:
    def __init__(self):
        self.calls = []

    def classify_window(self, samples, sample_rate):
        self.calls.append((samples, sample_rate))
        return ClassifiedSound("voice", 0.9, "Speech")


def test_bundled_labels_path_points_to_repo_csv():
    labels_path = Path(bundled_labels_path())
    assert labels_path.name == "yamnet_class_map.csv"
    assert labels_path.exists()


def test_live_classifier_delegates_to_existing_classifier():
    stub = _StubClassifier()
    classifier = LiveYamnetClassifier("unused.tflite", classifier=stub)
    samples = np.array([0.1, -0.1, 0.2], dtype=np.float32)
    result = classifier.classify_once(samples)
    assert result == ClassifiedSound("voice", 0.9, "Speech")
    assert stub.calls[0][1] == 16_000
