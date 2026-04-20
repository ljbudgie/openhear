"""
latency.py – round-trip audio latency measurement for OpenHear.

Plays a short impulse on the configured output device and records the
input device simultaneously.  The detected delay between the played
and recorded impulse is the round-trip latency — the most useful
single number for tuning the OpenHear pipeline (target: ≤ 20 ms).

Usage::

    python -m stream.latency --target 20
    python -m stream.latency --output-device 3 --input-device 1

The measurement requires that the output and input devices form a
loop — physically (e.g. headphones near the microphone), via a
virtual audio cable, or via a hardware loopback.

Tests cover the math (:func:`detect_impulse_delay`, :func:`format_report`)
without exercising real audio I/O.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class LatencyReport:
    """A single round-trip latency measurement.

    Attributes:
        latency_ms: Measured one-way → round-trip latency in milliseconds.
        target_ms: User-supplied target.  Used to format the verdict.
        sample_rate: Capture sample rate (Hz).
        impulse_index: Sample index at which the played impulse was found
            in the recording, or ``-1`` if no impulse was detected.
    """

    latency_ms: float
    target_ms: float
    sample_rate: int
    impulse_index: int

    @property
    def within_target(self) -> bool:
        return self.impulse_index >= 0 and self.latency_ms <= self.target_ms

    @property
    def verdict(self) -> str:
        if self.impulse_index < 0:
            return "no impulse detected"
        if self.within_target:
            return "within target"
        return "above target"


def synthesise_impulse(
    duration_samples: int,
    impulse_at: int = 0,
    amplitude: float = 0.9,
) -> np.ndarray:
    """Build a simple click impulse to use as the test stimulus.

    Args:
        duration_samples: Total length of the buffer in samples.
        impulse_at: Sample index of the click.
        amplitude: Peak amplitude (linear, 0–1).

    Returns:
        Float32 1-D array of length *duration_samples*.
    """
    if duration_samples <= 0:
        raise ValueError("duration_samples must be positive.")
    if not (0 <= impulse_at < duration_samples):
        raise ValueError(
            f"impulse_at must be in [0, {duration_samples}), got {impulse_at}."
        )
    out = np.zeros(duration_samples, dtype=np.float32)
    out[impulse_at] = float(amplitude)
    return out


def detect_impulse_delay(
    recording: np.ndarray,
    *,
    threshold_db: float = -20.0,
) -> int:
    """Return the index of the first peak above *threshold_db* in *recording*.

    Uses the global peak as a reference (relative threshold), so the
    detection is robust across different microphones and gains.

    Args:
        recording: Mono 1-D float32 array.
        threshold_db: Detection threshold relative to the recording's
            peak amplitude (negative dB).

    Returns:
        Sample index of the detected impulse, or ``-1`` if no sample
        crosses the threshold.
    """
    x = np.abs(np.asarray(recording, dtype=np.float32))
    if x.size == 0:
        return -1
    peak = float(np.max(x))
    if peak <= 1e-9:
        return -1
    rel = x / peak
    threshold_linear = 10.0 ** (threshold_db / 20.0)
    above = np.where(rel >= threshold_linear)[0]
    if above.size == 0:
        return -1
    return int(above[0])


def measure_latency(
    recording: np.ndarray,
    sample_rate: int,
    *,
    target_ms: float = 20.0,
    threshold_db: float = -20.0,
) -> LatencyReport:
    """Build a :class:`LatencyReport` from *recording*.

    The recording must start at the moment the test impulse was emitted
    (i.e. impulse_at = 0 in :func:`synthesise_impulse`).  The first
    sample crossing *threshold_db* is taken as the impulse return.

    Args:
        recording: Captured float32 audio aligned to play-start.
        sample_rate: Capture sample rate in Hz.
        target_ms: Target latency for the verdict.
        threshold_db: Detection threshold (see :func:`detect_impulse_delay`).
    """
    if sample_rate <= 0:
        raise ValueError(f"sample_rate must be positive, got {sample_rate}.")
    idx = detect_impulse_delay(recording, threshold_db=threshold_db)
    latency_ms = (idx / sample_rate) * 1000.0 if idx >= 0 else float("nan")
    return LatencyReport(
        latency_ms=latency_ms,
        target_ms=target_ms,
        sample_rate=sample_rate,
        impulse_index=idx,
    )


def format_report(report: LatencyReport) -> str:
    """Render *report* as a single human-readable line."""
    if report.impulse_index < 0:
        return (
            "No impulse detected — check that the output device is "
            "looped back to the input device."
        )
    return (
        f"latency={report.latency_ms:6.2f} ms  "
        f"target={report.target_ms:.1f} ms  "
        f"verdict={report.verdict}"
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry: capture and report round-trip latency.

    The actual capture path uses PyAudio and is therefore not exercised
    by unit tests; the math helpers are tested instead.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(
        description="Measure round-trip audio latency.",
    )
    parser.add_argument("--target", type=float, default=20.0,
                        help="Target latency in ms (default: 20).")
    parser.add_argument("--sample-rate", type=int, default=16_000,
                        help="Sample rate in Hz (default: 16000).")
    parser.add_argument("--input-device", type=int, default=None)
    parser.add_argument("--output-device", type=int, default=None)
    parser.add_argument("--duration-ms", type=float, default=200.0,
                        help="Total capture window in ms (default: 200).")
    parser.add_argument("--threshold-db", type=float, default=-20.0)
    args = parser.parse_args(argv)

    duration_samples = int(args.sample_rate * args.duration_ms / 1000.0)

    try:  # pragma: no cover - hardware path, not exercised by unit tests
        import pyaudio
    except Exception as exc:
        logger.error("PyAudio not available: %s.  Plug in audio hardware "
                     "or install PyAudio to use --measure.", exc)
        return 2

    pa = pyaudio.PyAudio()
    try:
        in_stream = pa.open(
            rate=args.sample_rate, channels=1, format=pyaudio.paInt16,
            input=True, frames_per_buffer=duration_samples,
            input_device_index=args.input_device,
        )
        out_stream = pa.open(
            rate=args.sample_rate, channels=1, format=pyaudio.paInt16,
            output=True, frames_per_buffer=duration_samples,
            output_device_index=args.output_device,
        )
        impulse = synthesise_impulse(duration_samples, impulse_at=0)
        int16 = (np.clip(impulse, -1, 1) * 32767).astype(np.int16).tobytes()
        # Start recording first, then immediately play.
        out_stream.write(int16)
        raw = in_stream.read(duration_samples, exception_on_overflow=False)
        recording = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        report = measure_latency(
            recording, args.sample_rate,
            target_ms=args.target, threshold_db=args.threshold_db,
        )
        print(format_report(report))
        return 0 if report.within_target else 1
    finally:  # pragma: no cover
        try:
            in_stream.stop_stream(); in_stream.close()
            out_stream.stop_stream(); out_stream.close()
        except Exception:
            pass
        pa.terminate()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
