"""
reference.py – reference artist frequency profile loader for OpenHear.

Loads a lossless audio file (WAV or FLAC), isolates vocal frequencies with
a bandpass filter, and computes an average spectral envelope across the
entire track.  The result is a ReferenceProfile that the comparison engine
uses as a training target.

This is not a voice cloner.  The reference is a mirror — it shows the user
what a particular vocal frequency distribution looks like so they can
develop their own voice toward the characteristics they want.  The user
owns the goal.

Implementation:
  - SciPy io.wavfile for WAV loading; soundfile (if available) for FLAC.
    Falls back to WAV-only if soundfile is not installed.
  - Butterworth bandpass filter (SciPy signal) to isolate 80–8 000 Hz.
  - Short-time FFT with overlapping windows for robust spectral averaging.
  - Formant extraction reuses the same peak-detection logic as analyser.py.

Tunable parameters (from voice/config.py):
  - REFERENCE_BANDPASS: frequency range for the vocal isolation filter.
  - FORMANT_PEAKS:      number of formant peaks to extract.
  - SAMPLE_RATE:        target sample rate (files are resampled if different).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import gcd
from pathlib import Path

import numpy as np
from scipy.io import wavfile as scipy_wav
from scipy.signal import butter, resample_poly, sosfilt

from voice import config
from voice.analyser import _find_formants, _spectral_envelope

# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class ReferenceProfile:
    """Average vocal frequency profile extracted from a reference recording.

    Attributes:
        artist_name:            Human-readable label for this profile.
        avg_formants:           Average formant frequencies [F1, F2, F3, ...]
                                across the track in Hz.
        spectral_envelope:      Average spectral envelope (dB) as a 1-D
                                numpy array — same bin count as the analyser
                                output so they can be compared directly.
        dominant_frequency_range:
                                Tuple (low_hz, high_hz) spanning the range
                                where the reference voice has the most energy.
    """
    artist_name: str = ""
    avg_formants: list[float] = field(default_factory=list)
    spectral_envelope: np.ndarray = field(
        default_factory=lambda: np.array([], dtype=np.float32)
    )
    dominant_frequency_range: tuple[float, float] = (0.0, 0.0)


# ── File I/O ─────────────────────────────────────────────────────────────────

def _load_audio(path: Path) -> tuple[int, np.ndarray]:
    """Load an audio file and return (sample_rate, mono_float32_samples).

    Supports WAV natively via SciPy.  FLAC support requires the
    ``soundfile`` package (``pip install soundfile``).

    Raises:
        ValueError: If the file format is not supported.
    """
    suffix = path.suffix.lower()

    if suffix == ".wav":
        sr, data = scipy_wav.read(str(path))
        # Convert to float32 normalised to [-1.0, 1.0].
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
        elif data.dtype != np.float32:
            data = data.astype(np.float32)

    elif suffix == ".flac":
        try:
            import soundfile as sf
        except ImportError:
            raise ImportError(
                "FLAC support requires the 'soundfile' package.  "
                "Install it with:  pip install soundfile"
            )
        data, sr = sf.read(str(path), dtype="float32")

    else:
        raise ValueError(
            f"Unsupported audio format '{suffix}'.  Use .wav or .flac."
        )

    # Mix to mono if stereo.
    if data.ndim == 2:
        data = data.mean(axis=1).astype(np.float32)

    return int(sr), data.astype(np.float32)


# ── Signal conditioning ──────────────────────────────────────────────────────

def _bandpass(samples: np.ndarray, sample_rate: int,
              low_hz: float, high_hz: float, order: int = 4) -> np.ndarray:
    """Apply a Butterworth bandpass filter to isolate vocal frequencies."""
    nyquist = sample_rate / 2.0
    low = max(low_hz / nyquist, 1e-5)
    high = min(high_hz / nyquist, 0.9999)
    sos = butter(order, [low, high], btype="band", output="sos")
    return sosfilt(sos, samples).astype(np.float32)


def _resample(samples: np.ndarray, orig_sr: int,
              target_sr: int) -> np.ndarray:
    """Resample *samples* from *orig_sr* to *target_sr* using polyphase
    resampling (integer ratio via GCD).
    """
    if orig_sr == target_sr:
        return samples
    divisor = gcd(orig_sr, target_sr)
    up = target_sr // divisor
    down = orig_sr // divisor
    return resample_poly(samples, up, down).astype(np.float32)


# ── Profile computation ─────────────────────────────────────────────────────

def _dominant_range(envelope_db: np.ndarray, freqs: np.ndarray,
                    threshold_db: float = 10.0) -> tuple[float, float]:
    """Find the frequency range where the envelope is within *threshold_db*
    of the peak level.  Returns (low_hz, high_hz).
    """
    peak = np.max(envelope_db)
    above = freqs[envelope_db >= (peak - threshold_db)]
    if len(above) == 0:
        return (0.0, 0.0)
    return (float(above[0]), float(above[-1]))


def load_reference(path: str | Path,
                   artist_name: str = "",
                   sample_rate: int = config.SAMPLE_RATE,
                   frame_size: int = config.FRAME_BUFFER,
                   bandpass: tuple[float, float] = config.REFERENCE_BANDPASS,
                   n_formants: int = config.FORMANT_PEAKS) -> ReferenceProfile:
    """Load a reference recording and compute its average vocal profile.

    Args:
        path:         Path to a .wav or .flac file.
        artist_name:  Human-readable label (defaults to the filename stem).
        sample_rate:  Target sample rate for analysis (file is resampled if
                      needed).
        frame_size:   FFT window size for short-time analysis.
        bandpass:     (low_hz, high_hz) for the vocal isolation filter.
        n_formants:   Number of formant peaks to extract.

    Returns:
        A populated ReferenceProfile dataclass.
    """
    path = Path(path)
    if not artist_name:
        artist_name = path.stem

    # Load and condition.
    orig_sr, samples = _load_audio(path)
    samples = _resample(samples, orig_sr, sample_rate)
    samples = _bandpass(samples, sample_rate, bandpass[0], bandpass[1])

    # Short-time FFT: split into overlapping frames, compute envelope for
    # each, then average.  50 % overlap for smooth coverage.
    hop = frame_size // 2
    n_bins = frame_size // 2 + 1
    window = np.hanning(frame_size).astype(np.float32)
    freqs = np.fft.rfftfreq(frame_size, d=1.0 / sample_rate).astype(np.float32)

    envelope_sum = np.zeros(n_bins, dtype=np.float64)
    formant_accumulator: list[list[float]] = []
    n_frames = 0

    for start in range(0, len(samples) - frame_size, hop):
        frame = samples[start:start + frame_size] * window
        spectrum = np.fft.rfft(frame)
        magnitude = np.abs(spectrum).astype(np.float32)

        env = _spectral_envelope(magnitude)
        envelope_sum += env.astype(np.float64)

        formants = _find_formants(env, freqs, n_formants)
        if formants:
            formant_accumulator.append(formants)
        n_frames += 1

    if n_frames == 0:
        return ReferenceProfile(artist_name=artist_name)

    avg_envelope = (envelope_sum / n_frames).astype(np.float32)

    # Average formants: take the per-frame formant lists that have the
    # expected number of entries and compute column-wise means.
    avg_formants: list[float] = []
    full_formant_frames = [f for f in formant_accumulator if len(f) == n_formants]
    if full_formant_frames:
        formant_array = np.array(full_formant_frames, dtype=np.float32)
        avg_formants = [float(v) for v in formant_array.mean(axis=0)]

    dominant = _dominant_range(avg_envelope, freqs)

    return ReferenceProfile(
        artist_name=artist_name,
        avg_formants=avg_formants,
        spectral_envelope=avg_envelope,
        dominant_frequency_range=dominant,
    )
