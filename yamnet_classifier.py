"""
yamnet_classifier.py – user-facing live YAMNet wrapper for OpenHear v1.0.0.

This keeps the existing ``stream.sound_classifier`` implementation as the core
classifier and adds a small clinic-facing entry point for microphone checks.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from stream.sound_classifier import (
    TARGET_SAMPLE_RATE,
    WINDOW_SECONDS,
    ClassifiedSound,
    YamnetClassifier,
)


DEFAULT_LABELS_PATH = Path(__file__).resolve().parent / "stream" / "data" / "yamnet_class_map.csv"


def bundled_labels_path() -> str:
    """Return the bundled YAMNet label CSV used by the wristband prototype."""
    return str(DEFAULT_LABELS_PATH)


def _load_sounddevice():
    try:
        import sounddevice as sd
    except ImportError as exc:  # pragma: no cover - runtime-only path.
        raise RuntimeError(
            "Live microphone capture requires the 'sounddevice' package."
        ) from exc
    return sd


class LiveYamnetClassifier:
    """Clinic-side microphone wrapper around ``stream.sound_classifier.YamnetClassifier``."""

    def __init__(
        self,
        model_path: str,
        *,
        labels_path: str | None = None,
        sample_rate: int = TARGET_SAMPLE_RATE,
        window_seconds: float = WINDOW_SECONDS,
        classifier: YamnetClassifier | None = None,
        sounddevice_module=None,
    ) -> None:
        self.sample_rate = sample_rate
        self.window_seconds = window_seconds
        self.labels_path = labels_path or bundled_labels_path()
        self.classifier = classifier or YamnetClassifier(model_path, self.labels_path)
        self._sounddevice_module = sounddevice_module

    @property
    def frame_samples(self) -> int:
        return int(round(self.sample_rate * self.window_seconds))

    def classify_once(self, samples: np.ndarray, sample_rate: int | None = None) -> ClassifiedSound:
        """Classify one audio window using the existing YAMNet wrapper."""
        effective_sample_rate = sample_rate or self.sample_rate
        return self.classifier.classify_window(np.asarray(samples), effective_sample_rate)

    def iter_classifications(self, *, input_device: int | None = None):
        """Yield classifications from the default microphone until interrupted."""
        sd = self._sounddevice_module or _load_sounddevice()
        stream_kwargs = {
            "samplerate": self.sample_rate,
            "channels": 1,
            "dtype": "float32",
            "blocksize": self.frame_samples,
        }
        if input_device is not None:
            stream_kwargs["device"] = input_device

        with sd.InputStream(**stream_kwargs) as stream:
            while True:
                samples, _ = stream.read(self.frame_samples)
                yield self.classify_once(samples[:, 0], self.sample_rate)


def main() -> None:
    parser = argparse.ArgumentParser(description="Live YAMNet microphone monitor for OpenHear.")
    parser.add_argument("--model", required=True, help="Path to the local YAMNet .tflite model.")
    parser.add_argument(
        "--labels",
        default=bundled_labels_path(),
        help="Path to the YAMNet labels CSV/txt. Defaults to the bundled official CSV.",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=TARGET_SAMPLE_RATE,
        help="Microphone sample rate. Defaults to 16000 Hz.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Stop after this many classification windows.",
    )
    parser.add_argument(
        "--input-device",
        type=int,
        help="Optional sounddevice input device index.",
    )
    args = parser.parse_args()

    live_classifier = LiveYamnetClassifier(
        args.model,
        labels_path=args.labels,
        sample_rate=args.sample_rate,
    )

    for index, classified in enumerate(
        live_classifier.iter_classifications(input_device=args.input_device),
        start=1,
    ):
        print(
            f"{classified.sound_key:<8} "
            f"conf={classified.confidence:.2f} "
            f"label={classified.source_label}"
        )
        if args.limit is not None and index >= args.limit:
            break


if __name__ == "__main__":
    main()
