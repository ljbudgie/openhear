"""Tests for ``yamnet_classifier.py``."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from stream.sound_classifier import ClassifiedSound
from yamnet_classifier import (
    LiveYamnetClassifier,
    _load_sounddevice,
    bundled_labels_path,
    main,
)


class _StubClassifier:
    def __init__(self, results=None):
        self.calls = []
        self._results = list(results or [])

    def classify_window(self, samples, sample_rate):
        self.calls.append((samples, sample_rate))
        if self._results:
            return self._results.pop(0)
        return ClassifiedSound("voice", 0.9, "Speech")


class _StreamExhausted(Exception):
    """Raised by the stub stream once its frame queue is empty."""


class _StubInputStream:
    """Minimal sounddevice.InputStream replacement.

    Each ``read`` call returns one of the canned audio frames.  Once the
    queue is exhausted the stream raises ``_StreamExhausted`` so the
    iteration callers can break out of their loop.  We avoid raising
    ``StopIteration`` directly because PEP 479 turns it into a
    ``RuntimeError`` when leaked from a generator.
    """

    def __init__(self, frames, capture_kwargs):
        self._frames = list(frames)
        self.capture_kwargs = capture_kwargs
        self.entered = False
        self.exited = False

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exc_type, exc, tb):
        self.exited = True
        return False

    def read(self, frame_samples):
        if not self._frames:
            raise _StreamExhausted("no more frames")
        frame = self._frames.pop(0)
        return frame.reshape(-1, 1), False


class _StubSounddevice:
    def __init__(self, frames):
        self._frames = list(frames)
        self.last_kwargs = None
        self.streams: list[_StubInputStream] = []

    def InputStream(self, **kwargs):  # noqa: N802 - mirror sounddevice API.
        self.last_kwargs = kwargs
        stream = _StubInputStream(self._frames, kwargs)
        self.streams.append(stream)
        return stream


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


# ── Additional coverage ──────────────────────────────────────────────────────


class TestLiveYamnetClassifier:
    def test_frame_samples_matches_sample_rate_and_window(self):
        stub = _StubClassifier()
        classifier = LiveYamnetClassifier(
            "unused.tflite", classifier=stub, sample_rate=8_000, window_seconds=1.0
        )
        assert classifier.frame_samples == 8_000

    def test_classify_once_uses_explicit_sample_rate_when_provided(self):
        stub = _StubClassifier()
        classifier = LiveYamnetClassifier("unused.tflite", classifier=stub)
        classifier.classify_once(np.zeros(10, dtype=np.float32), sample_rate=44_100)
        assert stub.calls[0][1] == 44_100

    def test_default_labels_path_falls_back_to_bundled(self):
        stub = _StubClassifier()
        classifier = LiveYamnetClassifier("unused.tflite", classifier=stub)
        assert classifier.labels_path == bundled_labels_path()

    def test_iter_classifications_yields_until_stream_exhausted(self):
        frame = np.zeros(int(round(16_000 * 0.975)), dtype=np.float32)
        sd = _StubSounddevice([frame, frame, frame])
        stub = _StubClassifier(
            results=[
                ClassifiedSound("voice", 0.9, "Speech"),
                ClassifiedSound("dog", 0.8, "Bark"),
                ClassifiedSound("alarm", 0.7, "Alarm"),
            ]
        )
        classifier = LiveYamnetClassifier(
            "unused.tflite", classifier=stub, sounddevice_module=sd
        )

        results = []
        with pytest.raises(_StreamExhausted):
            for classified in classifier.iter_classifications():
                results.append(classified)

        assert [r.sound_key for r in results] == ["voice", "dog", "alarm"]
        # The stream should have been opened with the configured frame size.
        assert sd.last_kwargs["blocksize"] == classifier.frame_samples
        assert sd.last_kwargs["samplerate"] == 16_000
        # Context manager protocol must be respected for resource cleanup.
        assert sd.streams[0].entered and sd.streams[0].exited
        # ``device`` should NOT be passed when input_device is None.
        assert "device" not in sd.last_kwargs

    def test_iter_classifications_forwards_input_device(self):
        frame = np.zeros(int(round(16_000 * 0.975)), dtype=np.float32)
        sd = _StubSounddevice([frame])
        stub = _StubClassifier(results=[ClassifiedSound("voice", 0.9, "Speech")])
        classifier = LiveYamnetClassifier(
            "unused.tflite", classifier=stub, sounddevice_module=sd
        )

        with pytest.raises(_StreamExhausted):
            for _ in classifier.iter_classifications(input_device=3):
                pass

        assert sd.last_kwargs["device"] == 3


def test_load_sounddevice_returns_module_when_available(monkeypatch):
    fake_module = types.ModuleType("sounddevice")
    monkeypatch.setitem(sys.modules, "sounddevice", fake_module)
    assert _load_sounddevice() is fake_module


# ── CLI entry point ──────────────────────────────────────────────────────────


def test_main_iterates_until_limit(monkeypatch, capsys):
    frame = np.zeros(int(round(16_000 * 0.975)), dtype=np.float32)
    sd = _StubSounddevice([frame, frame, frame, frame])
    stub = _StubClassifier(
        results=[
            ClassifiedSound("voice", 0.9, "Speech"),
            ClassifiedSound("dog", 0.8, "Bark"),
            ClassifiedSound("alarm", 0.7, "Alarm"),
            ClassifiedSound("voice", 0.6, "Conversation"),
        ]
    )

    def fake_init(self, model_path, *, labels_path=None, sample_rate=16_000,
                  window_seconds=0.975, classifier=None, sounddevice_module=None):
        self.sample_rate = sample_rate
        self.window_seconds = window_seconds
        self.labels_path = labels_path or bundled_labels_path()
        self.classifier = stub
        self._sounddevice_module = sd

    monkeypatch.setattr(LiveYamnetClassifier, "__init__", fake_init)
    monkeypatch.setattr(
        "sys.argv",
        [
            "yamnet_classifier",
            "--model", "unused.tflite",
            "--limit", "2",
        ],
    )
    main()

    output_lines = [
        line for line in capsys.readouterr().out.splitlines() if line.strip()
    ]
    # --limit 2 means exactly two classification lines should be printed.
    assert len(output_lines) == 2
    assert "voice" in output_lines[0]
    assert "dog" in output_lines[1]

