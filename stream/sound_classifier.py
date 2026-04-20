"""
sound_classifier.py – YAMNet-oriented sound mapping for the OpenHear wristband.

This module provides:

  - category definitions for the 7 OpenHear wristband sound classes,
  - a pure-Python score aggregation layer that maps YAMNet labels to those
    classes, and
  - an optional TensorFlow Lite wrapper for running a local YAMNet model if
    ``tflite_runtime`` or ``tensorflow`` is installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from stream.haptic_mapper import SOUND_PROFILES


WINDOW_SECONDS = 0.975
TARGET_SAMPLE_RATE = 16_000
DEFAULT_MIN_CONFIDENCE = 0.20

_LABEL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "voice": (
        "speech",
        "conversation",
        "narration",
        "male speaking",
        "female speaking",
        "child speech",
    ),
    "doorbell": ("doorbell", "ding-dong", "chime"),
    "alarm": ("alarm", "siren", "smoke detector", "fire alarm", "alarm clock", "buzzer"),
    "dog": ("dog", "bark", "bow-wow", "howl"),
    "traffic": (
        "traffic",
        "car",
        "truck",
        "bus",
        "motor vehicle",
        "motorcycle",
        "roadway noise",
        "vehicle horn",
        "engine",
    ),
    "media": ("music", "television", "radio", "podcast", "video game music"),
}


@dataclass(frozen=True)
class ClassifiedSound:
    """Result of mapping model scores into an OpenHear wristband category."""

    sound_key: str
    confidence: float
    source_label: str

    @property
    def sound_class_id(self) -> int:
        return SOUND_PROFILES[self.sound_key].sound_class_id

    @property
    def pattern_id(self) -> int:
        return SOUND_PROFILES[self.sound_key].pattern_id

    @property
    def dominant_frequency_hz(self) -> int | None:
        return SOUND_PROFILES[self.sound_key].dominant_frequency_hz


def prepare_audio_window(
    samples: np.ndarray,
    sample_rate: int,
    *,
    target_sample_rate: int = TARGET_SAMPLE_RATE,
    window_seconds: float = WINDOW_SECONDS,
) -> np.ndarray:
    """Resample and pad/truncate audio to the YAMNet window shape."""
    mono = np.asarray(samples, dtype=np.float32)
    if mono.ndim > 1:
        mono = mono.mean(axis=1)

    if sample_rate != target_sample_rate:
        original_times = np.linspace(0.0, len(mono) / sample_rate, num=len(mono), endpoint=False)
        target_length = max(1, int(round(len(mono) * target_sample_rate / sample_rate)))
        target_times = np.linspace(
            0.0, len(mono) / sample_rate, num=target_length, endpoint=False
        )
        mono = np.interp(target_times, original_times, mono).astype(np.float32)

    desired_length = int(round(target_sample_rate * window_seconds))
    if len(mono) < desired_length:
        mono = np.pad(mono, (0, desired_length - len(mono)))
    else:
        mono = mono[:desired_length]
    return mono.astype(np.float32, copy=False)


def map_label_to_sound_key(label: str) -> str | None:
    """Map one YAMNet label to an OpenHear sound class."""
    label_normalised = label.lower().strip()
    for sound_key, keywords in _LABEL_KEYWORDS.items():
        if any(keyword in label_normalised for keyword in keywords):
            return sound_key
    if "silence" in label_normalised:
        return "silence"
    return None


def classify_scores(
    scores_by_label: dict[str, float],
    *,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> ClassifiedSound:
    """Aggregate YAMNet-like label scores into one OpenHear category."""
    best_sound = "silence"
    best_score = 0.0
    best_label = "silence"

    for label, score in scores_by_label.items():
        sound_key = map_label_to_sound_key(label)
        if sound_key is None:
            continue
        if float(score) > best_score:
            best_sound = sound_key
            best_score = float(score)
            best_label = label

    if best_score < min_confidence or best_sound == "silence":
        return ClassifiedSound("silence", 0.0, "silence")
    return ClassifiedSound(best_sound, best_score, best_label)


class YamnetClassifier:
    """Optional TensorFlow Lite wrapper for running YAMNet locally."""

    def __init__(self, model_path: str, labels_path: str) -> None:
        self.model_path = str(model_path)
        self.labels = _load_labels(labels_path)
        self._interpreter = _load_tflite_interpreter(self.model_path)
        self._interpreter.allocate_tensors()
        self._input_details = self._interpreter.get_input_details()
        self._output_details = self._interpreter.get_output_details()

    def classify_window(self, samples: np.ndarray, sample_rate: int) -> ClassifiedSound:
        """Run YAMNet on *samples* and return one OpenHear sound class."""
        window = prepare_audio_window(samples, sample_rate)
        input_tensor = window
        input_shape = tuple(self._input_details[0]["shape"])
        if len(input_shape) == 2:
            input_tensor = window[np.newaxis, :]
        self._interpreter.set_tensor(self._input_details[0]["index"], input_tensor.astype(np.float32))
        self._interpreter.invoke()
        raw_scores = self._interpreter.get_tensor(self._output_details[0]["index"])
        scores = np.asarray(raw_scores, dtype=np.float32)
        if scores.ndim == 2:
            scores = scores.mean(axis=0)
        scores_by_label = {
            label: float(scores[idx])
            for idx, label in enumerate(self.labels[: len(scores)])
        }
        return classify_scores(scores_by_label)


def _load_labels(labels_path: str) -> list[str]:
    content = Path(labels_path).read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in content if line.strip()]


def _load_tflite_interpreter(model_path: str):
    try:
        from tflite_runtime.interpreter import Interpreter
    except ImportError:
        try:
            from tensorflow.lite import Interpreter
        except ImportError as exc:  # pragma: no cover - runtime-only path.
            raise RuntimeError(
                "YAMNet inference requires either 'tflite-runtime' or 'tensorflow'."
            ) from exc
    return Interpreter(model_path=model_path)
