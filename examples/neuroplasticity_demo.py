"""
neuroplasticity_demo.py – local binaural entrainer demo.

Writes a deterministic, safety-limited stereo WAV file without microphone,
network, or cloud access.

Usage::

    python examples/neuroplasticity_demo.py --output binaural_demo.wav
"""

from __future__ import annotations

import argparse
import logging
import sys
import wave
from pathlib import Path

import numpy as np

from dsp.audiogram_profile import BandPrescription, Prescription
from dsp.stages.binaural_entrainer import BinauralEntrainer


def _example_prescription() -> Prescription:
    right = [
        BandPrescription(freq_hz=250, threshold_db_hl=20.0, gain_db=2.0, ratio=1.0, knee_dbfs=-30),
        BandPrescription(freq_hz=500, threshold_db_hl=25.0, gain_db=3.0, ratio=1.0, knee_dbfs=-30),
    ]
    left = [
        BandPrescription(freq_hz=250, threshold_db_hl=35.0, gain_db=6.0, ratio=1.5, knee_dbfs=-35),
        BandPrescription(freq_hz=500, threshold_db_hl=40.0, gain_db=8.0, ratio=1.5, knee_dbfs=-35),
    ]
    return Prescription(right=right, left=left)


def _write_stereo_wav(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    clipped = np.clip(samples, -0.7, 0.7)
    int16 = (clipped.reshape(-1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int16.tobytes())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a local binaural entrainer WAV demo.")
    parser.add_argument("--output", "-o", type=Path, default=Path("binaural_demo.wav"))
    parser.add_argument("--duration", type=float, default=10.0, help="Session duration in seconds.")
    parser.add_argument("--beat-hz", type=float, default=6.0)
    parser.add_argument("--carrier-hz", type=float, default=300.0)
    parser.add_argument("--mask-type", choices=["pink_noise", "ambient", "none"], default="pink_noise")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    sample_rate = 16_000
    block_size = 256
    stage = BinauralEntrainer(
        sample_rate=sample_rate,
        beat_hz=args.beat_hz,
        carrier_hz=args.carrier_hz,
        duration_s=args.duration,
        ramp_ms=1000.0,
        mask_type=args.mask_type,
        prescription=_example_prescription(),
    )

    blocks: list[np.ndarray] = []
    total = int(round(args.duration * sample_rate))
    rendered = 0
    while rendered < total:
        n = min(block_size, total - rendered)
        blocks.append(stage.process(np.zeros(n, dtype=np.float32)))
        rendered += n

    out = np.vstack(blocks)
    _write_stereo_wav(args.output, out, sample_rate)
    print(f"Wrote {args.output} ({args.duration:.1f}s, max amplitude {np.max(np.abs(out)):.3f})")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
