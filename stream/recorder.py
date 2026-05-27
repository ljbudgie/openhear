"""
recorder.py – capture raw and processed OpenHear audio to WAV files.

Useful for debugging the DSP chain: record the raw microphone feed
(``--raw``), the post-DSP feed (``--processed``), or both at once so
A/B comparison can be done in a DAW.

Tests cover the file-writing and concatenation helpers; the live
capture path is hardware-dependent and not exercised by unit tests.

CLI::

    python -m stream.recorder --raw raw.wav --duration 5
    python -m stream.recorder --raw raw.wav --processed proc.wav --duration 10
"""

from __future__ import annotations

import argparse
import logging
import sys
import wave
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


# ── Helpers (testable) ─────────────────────────────────────────────────────


def write_wav(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    """Write a mono float32 buffer to a 16-bit PCM WAV file.

    Args:
        path: Output WAV path.  Parent directories are created.
        samples: Mono float32 array in [-1, 1].
        sample_rate: Sample rate in Hz.

    Raises:
        ValueError: If the sample rate is non-positive or the buffer is
            empty.
    """
    if sample_rate <= 0:
        raise ValueError(f"sample_rate must be positive, got {sample_rate}.")
    arr = np.asarray(samples, dtype=np.float32)
    if arr.size == 0:
        raise ValueError("Refusing to write an empty WAV file.")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    int16 = (np.clip(arr, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int16.tobytes())


@dataclass
class Recorder:
    """In-memory capture buffer that writes a WAV when closed.

    Used by both unit tests and the live CLI.  Each call to
    :meth:`feed` appends a block of samples; :meth:`save` writes the
    accumulated buffer to disk.

    Attributes:
        path: Where the WAV will be written.
        sample_rate: Audio sample rate (Hz).
        max_samples: Optional cap.  Once reached, further blocks are
            silently dropped to bound memory usage during long captures.
    """

    path: Path
    sample_rate: int
    max_samples: int | None = None
    _chunks: list[np.ndarray] = field(default_factory=list, init=False)
    _total: int = field(default=0, init=False)

    def feed(self, block: np.ndarray) -> None:
        """Append *block* to the in-memory buffer.

        Excess samples beyond :attr:`max_samples` are clipped without
        raising so a recorder can run alongside a live pipeline of
        unknown duration.
        """
        arr = np.asarray(block, dtype=np.float32).ravel()
        if self.max_samples is not None and self._total + arr.size > self.max_samples:
            remaining = self.max_samples - self._total
            if remaining <= 0:
                return
            arr = arr[:remaining]
        self._chunks.append(arr)
        self._total += arr.size

    @property
    def length_samples(self) -> int:
        return self._total

    def save(self) -> Path:
        """Concatenate the captured chunks and write the WAV file.

        Returns the resolved output path.
        """
        if self._total == 0:
            raise RuntimeError("Recorder.save() called before any samples were fed.")
        signal = np.concatenate(self._chunks) if self._chunks else np.empty(0, dtype=np.float32)
        write_wav(self.path, signal, self.sample_rate)
        logger.info("Recorder wrote %d samples (%.2f s) to %s",
                    signal.size, signal.size / self.sample_rate, self.path)
        return Path(self.path)


# ── CLI ─────────────────────────────────────────────────────────────────────


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture raw and/or processed OpenHear audio to WAV.",
    )
    parser.add_argument("--raw", type=Path, default=None,
                        help="Output WAV path for the raw microphone feed.")
    parser.add_argument("--processed", type=Path, default=None,
                        help="Output WAV path for the post-DSP feed.")
    parser.add_argument("--duration", type=float, default=5.0,
                        help="Capture duration in seconds (default: 5).")
    parser.add_argument("--sample-rate", type=int, default=16_000,
                        help="Sample rate in Hz (default: 16000).")
    parser.add_argument("--block-size", type=int, default=256,
                        help="Capture block size in samples (default: 256).")
    parser.add_argument("--input-device", type=int, default=None,
                        help="PyAudio input device index.")
    return parser


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - hardware path
    """CLI entry: capture raw / processed audio for *duration* seconds."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    args = _build_arg_parser().parse_args(argv)

    if args.raw is None and args.processed is None:
        print("error: at least one of --raw or --processed is required.",
              file=sys.stderr)
        return 2

    try:
        import pyaudio
    except Exception as exc:
        logger.error("PyAudio not available: %s.  Plug in audio hardware "
                     "or install PyAudio to use the recorder.", exc)
        return 2

    sr = args.sample_rate
    n_total = int(sr * args.duration)
    raw_rec = Recorder(args.raw, sr, max_samples=n_total) if args.raw else None
    proc_rec = Recorder(args.processed, sr, max_samples=n_total) if args.processed else None

    pa = pyaudio.PyAudio()
    try:
        stream = pa.open(
            rate=sr, channels=1, format=pyaudio.paInt16, input=True,
            frames_per_buffer=args.block_size,
            input_device_index=args.input_device,
        )
        # Build the DSP chain (only loaded when --processed is requested).
        chain = []
        if proc_rec is not None:
            from dsp.pipeline import build_dsp_chain  # late import
            chain = build_dsp_chain()

        captured = 0
        while captured < n_total:
            n = min(args.block_size, n_total - captured)
            raw_bytes = stream.read(n, exception_on_overflow=False)
            block = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            if raw_rec is not None:
                raw_rec.feed(block)
            if proc_rec is not None:
                processed = block.copy()
                for stage in chain:
                    processed = stage.process(processed)
                proc_rec.feed(processed)
            captured += n
    finally:
        try:
            stream.stop_stream(); stream.close()
        except Exception:
            pass
        pa.terminate()

    if raw_rec is not None:
        raw_rec.save()
    if proc_rec is not None:
        proc_rec.save()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
