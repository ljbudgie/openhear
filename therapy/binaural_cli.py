"""
binaural_cli.py – generate a binaural-beat WAV from the terminal.

Writes a 16-bit stereo WAV using only the standard library, so it needs no
audio dependencies.  With ``--audiogram`` it personalises the carrier and
per-ear levels to your own hearing (see
:func:`therapy.binaural.prescribe_binaural`).

Usage::

    python -m therapy.binaural_cli --beat 10 --carrier 300 --out beats.wav
    python -m therapy.binaural_cli --beat 10 --audiogram AG.json --out beats.wav
"""

from __future__ import annotations

import sys
import wave
from pathlib import Path

import click
import numpy as np

from audiogram.audiogram import Audiogram
from therapy.binaural import (
    DEFAULT_SAMPLE_RATE,
    generate_binaural,
    prescribe_binaural,
)


def _write_wav(path: Path, stereo: np.ndarray, sample_rate: int) -> None:
    """Write a ``(N, 2)`` float signal in [-1, 1] as a 16-bit stereo WAV."""
    clipped = np.clip(stereo, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())


@click.command()
@click.option("--beat", "beat_hz", type=float, required=True, help="Beat frequency (Hz).")
@click.option("--carrier", "carrier_hz", type=float, default=None, help="Carrier (Hz).")
@click.option(
    "--audiogram",
    "audiogram_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Personalise carrier and per-ear levels from this audiogram.",
)
@click.option("--duration", "duration_s", type=float, default=60.0, help="Length (s).")
@click.option("--amplitude", type=float, default=0.2, help="Base amplitude (0-1].")
@click.option("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE, help="Sample rate.")
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("beats.wav"))
def main(
    beat_hz: float,
    carrier_hz: float | None,
    audiogram_path: Path | None,
    duration_s: float,
    amplitude: float,
    sample_rate: int,
    out_path: Path,
) -> None:
    """Generate a binaural-beat WAV.

    OpenHear is not a medical device; this is sovereign tooling for
    evidence-led self-experimentation.
    """
    try:
        if audiogram_path is not None:
            audiogram = Audiogram.from_path(audiogram_path)
            rx = prescribe_binaural(
                audiogram, beat_hz, amplitude=amplitude, sample_rate=sample_rate
            )
            click.echo(rx.rationale)
            stereo = rx.render(duration_s)
        else:
            stereo = generate_binaural(
                carrier_hz if carrier_hz is not None else 300.0,
                beat_hz,
                duration_s,
                sample_rate=sample_rate,
                amplitude=amplitude,
            )
    except (ValueError, OSError) as exc:
        click.echo(f"Could not generate: {exc}", err=True)
        sys.exit(1)

    _write_wav(out_path, stereo, sample_rate)
    click.echo(f"Wrote {out_path} ({duration_s:.0f}s, beat {beat_hz:g} Hz).")


if __name__ == "__main__":  # pragma: no cover
    main()
