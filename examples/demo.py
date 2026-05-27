"""
demo.py – offline OpenHear DSP demo.

Reads a WAV file, runs it through the OpenHear DSP chain (noise
reduction, WDRC, voice clarity) and writes the processed audio to a
new WAV file.  This is the easiest way to evaluate a tuning change
without setting up real-time audio routing.

Usage::

    python examples/demo.py --input speech.wav --output processed.wav
    python examples/demo.py -i speech.wav -o processed.wav --bypass

Loads its tunable parameters from ``~/.openhear/config.yaml`` (or the
file passed via ``--config``); the live ``dsp.config`` constants are
used as a sane fallback when no user config is available.
"""

from __future__ import annotations

import argparse
import logging
import sys
import wave
from pathlib import Path

import numpy as np

from dsp import config
from dsp.compression import WDRCompressor
from dsp.noise import SpectralSubtractor
from dsp.user_config import load_config
from dsp.voice_clarity import VoiceClarityEnhancer

logger = logging.getLogger(__name__)


def _read_wav(path: Path) -> tuple[np.ndarray, int]:
    """Read a 16-bit mono WAV and return (samples, sample_rate)."""
    with wave.open(str(path), "rb") as wf:
        if wf.getsampwidth() != 2:
            raise ValueError("Only 16-bit PCM WAV files are supported.")
        sr = wf.getframerate()
        n = wf.getnframes()
        raw = wf.readframes(n)
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if wf.getnchannels() > 1:
        # Down-mix to mono.
        audio = audio.reshape(-1, wf.getnchannels()).mean(axis=1)
    return audio, sr


def _write_wav(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    """Write a float32 mono signal to a 16-bit PCM WAV."""
    clipped = np.clip(samples, -1.0, 1.0)
    int16 = (clipped * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int16.tobytes())


def process_signal(
    samples: np.ndarray,
    sample_rate: int,
    block_size: int,
    bypass: bool,
    user_config,
) -> np.ndarray:
    """Run *samples* through the DSP chain block-by-block.

    Args:
        samples: Mono float32 input signal.
        sample_rate: Sample rate in Hz.
        block_size: Number of samples per processing block.
        bypass: If ``True``, return the input unchanged (useful for A/B).
        user_config: Loaded :class:`dsp.user_config.Config`.

    Returns:
        Processed mono float32 signal of the same length.
    """
    if bypass:
        return samples.copy()

    chain = []
    if config.NOISE_REDUCTION_ENABLED:
        chain.append(SpectralSubtractor(
            frame_length=block_size,
            noise_floor_multiplier=config.NOISE_FLOOR_MULTIPLIER,
            spectral_floor=config.SPECTRAL_FLOOR,
            noise_estimation_frames=config.NOISE_ESTIMATION_FRAMES,
        ))
    chain.append(WDRCompressor(
        sample_rate=sample_rate,
        ratio=user_config.compression.ratio,
        knee_dbfs=user_config.compression.knee_db,
        attack_s=user_config.compression.attack_ms / 1000.0,
        release_s=user_config.compression.release_ms / 1000.0,
    ))
    chain.append(VoiceClarityEnhancer(
        frame_length=block_size,
        sample_rate=sample_rate,
        low_hz=user_config.voice.boost_hz[0],
        high_hz=user_config.voice.boost_hz[1],
        gain=10.0 ** (user_config.voice.boost_db / 20.0),
    ))

    out = np.zeros_like(samples)
    pos = 0
    n = samples.shape[0]
    while pos < n:
        end = min(pos + block_size, n)
        block = samples[pos:end]
        if block.shape[0] < block_size:
            # Pad final partial block.
            pad = np.zeros(block_size - block.shape[0], dtype=np.float32)
            block = np.concatenate([block, pad])
        for stage in chain:
            block = stage.process(block)
        out[pos:end] = block[: end - pos]
        pos = end
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--input", "-i", required=True, type=Path)
    parser.add_argument("--output", "-o", required=True, type=Path)
    parser.add_argument(
        "--config", "-c", type=Path, default=None,
        help="Path to a user config YAML file.  Defaults to "
             "~/.openhear/config.yaml.",
    )
    parser.add_argument(
        "--block-size", type=int, default=256,
        help="Block size in samples (default: 256).",
    )
    parser.add_argument(
        "--bypass", action="store_true",
        help="Skip DSP processing — copy input to output.  Useful for A/B.",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        cfg = load_config(args.config)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 2

    samples, sample_rate = _read_wav(args.input)
    logger.info(
        "Loaded %s: %d samples @ %d Hz (%.2f s)",
        args.input, samples.shape[0], sample_rate,
        samples.shape[0] / sample_rate,
    )
    processed = process_signal(
        samples=samples,
        sample_rate=sample_rate,
        block_size=args.block_size,
        bypass=args.bypass,
        user_config=cfg,
    )
    _write_wav(args.output, processed, sample_rate)
    logger.info("Wrote processed audio to %s", args.output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
