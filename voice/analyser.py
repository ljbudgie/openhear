"""
analyser.py – real-time vocal frequency analyser for OpenHear.

Captures microphone input, computes an FFT, and extracts the features that
matter for vocal development: fundamental frequency, formant positions,
spectral envelope shape, harmonic-to-noise ratio, and overall energy.

For someone with sensorineural hearing loss who has never monitored their
own voice through a clean signal, these numbers replace the feedback loop
that hearing listeners take for granted.  The brain can learn to control
what it can measure — this module provides the measurement.

Implementation:
  - PyAudio for real-time mic capture (callback-free blocking reads for
    simplicity and deterministic latency).
  - NumPy rfft for spectral decomposition.
  - SciPy signal.find_peaks on a smoothed spectral envelope for formant
    detection.
  - HNR computed as the ratio of periodic energy (harmonics) to aperiodic
    energy (noise floor between harmonics).

Tunable parameters (from voice/config.py):
  - SAMPLE_RATE:      capture rate in Hz (default 44 100).
  - FRAME_BUFFER:     samples per capture frame (default 1024).
  - MIC_DEVICE_INDEX: PyAudio device index (default None = system default).
  - FORMANT_PEAKS:    number of formant peaks to extract (default 3).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
from scipy.signal import find_peaks

from voice import config

# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class VoiceSnapshot:
    """A single frame of vocal analysis data.

    Every field is computed from one capture buffer — typically ~23 ms of
    audio at 44 100 Hz / 1024 frames.  Collect a stream of these to build
    a time-series of your vocal behaviour.

    Attributes:
        timestamp:              UTC epoch seconds when the frame was captured.
        fundamental_frequency_hz:
                                Estimated F0 (pitch) in Hz, or 0.0 if no
                                voiced signal was detected.
        formants:               List of formant frequencies [F1, F2, F3, ...]
                                in Hz, extracted from the spectral envelope.
        spectral_envelope:      Smoothed magnitude spectrum (dB) as a 1-D
                                numpy array.
        hnr_db:                 Harmonic-to-noise ratio in dB.  Higher values
                                mean a clearer, more periodic voice signal.
        energy_db:              RMS energy of the frame in dBFS.
    """
    timestamp: float = 0.0
    fundamental_frequency_hz: float = 0.0
    formants: list[float] = field(default_factory=list)
    spectral_envelope: np.ndarray = field(
        default_factory=lambda: np.array([], dtype=np.float32)
    )
    hnr_db: float = 0.0
    energy_db: float = -100.0


# ── Internal helpers ─────────────────────────────────────────────────────────

def _bytes_to_float32(raw: bytes) -> np.ndarray:
    """Convert raw int16 PCM bytes to normalised float32 [-1.0, 1.0]."""
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    samples /= 32768.0
    return samples


def _rms_db(samples: np.ndarray) -> float:
    """Return RMS energy in dBFS, floored at -100 dB."""
    rms = np.sqrt(np.mean(samples ** 2))
    if rms < 1e-10:
        return -100.0
    return float(20.0 * np.log10(rms))


def _spectral_envelope(magnitude: np.ndarray, smooth_width: int = 15) -> np.ndarray:
    """Smooth a magnitude spectrum into a spectral envelope using a moving
    average.  Returns values in dB (floored at -100 dB).
    """
    kernel = np.ones(smooth_width, dtype=np.float32) / smooth_width
    smoothed = np.convolve(magnitude, kernel, mode="same")
    # Convert to dB, guarding against log(0).
    smoothed = np.where(smoothed > 1e-10, smoothed, 1e-10)
    return (20.0 * np.log10(smoothed)).astype(np.float32)


def _find_fundamental(magnitude: np.ndarray, freqs: np.ndarray,
                      low_hz: float = 50.0, high_hz: float = 500.0) -> float:
    """Estimate the fundamental frequency (F0) as the strongest peak in the
    *low_hz*–*high_hz* range of the magnitude spectrum.

    Returns 0.0 if no clear peak is found.
    """
    mask = (freqs >= low_hz) & (freqs <= high_hz)
    if not np.any(mask):
        return 0.0
    masked_mag = magnitude.copy()
    masked_mag[~mask] = 0.0
    peak_bin = np.argmax(masked_mag)
    if masked_mag[peak_bin] < 1e-10:
        return 0.0
    return float(freqs[peak_bin])


def _find_formants(envelope_db: np.ndarray, freqs: np.ndarray,
                   n_formants: int, min_freq: float = 200.0) -> list[float]:
    """Extract formant frequencies from the spectral envelope.

    Uses SciPy peak detection on the dB envelope, filtered to frequencies
    above *min_freq* (below which F0 harmonics dominate), and returns the
    *n_formants* strongest peaks sorted by frequency.
    """
    # Only consider bins above min_freq.
    valid = freqs >= min_freq
    if not np.any(valid):
        return []

    # Find peaks in the envelope with a minimum prominence of 3 dB and
    # a minimum distance of ~100 Hz between peaks.
    freq_resolution = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
    min_distance = max(1, int(100.0 / freq_resolution))

    peak_indices, properties = find_peaks(
        envelope_db, prominence=3.0, distance=min_distance
    )

    # Filter to valid frequency range.
    peak_indices = peak_indices[valid[peak_indices]]
    if len(peak_indices) == 0:
        return []

    # Sort by prominence (strongest first), take top n_formants, then
    # re-sort by frequency for conventional F1 < F2 < F3 ordering.
    prominences = properties["prominences"]
    # Re-index prominences to match filtered peaks.
    orig_indices = np.where(np.isin(
        np.arange(len(envelope_db)),
        peak_indices
    ))[0]
    # Rebuild prominences for filtered set.
    all_peak_indices_list = list(find_peaks(envelope_db, prominence=3.0,
                                           distance=min_distance)[0])
    filtered_prominences = []
    for pi in peak_indices:
        if pi in all_peak_indices_list:
            idx = all_peak_indices_list.index(pi)
            filtered_prominences.append(prominences[idx])
        else:
            filtered_prominences.append(0.0)
    filtered_prominences = np.array(filtered_prominences)

    top_n = min(n_formants, len(peak_indices))
    top_indices = peak_indices[np.argsort(filtered_prominences)[-top_n:]]
    top_indices = np.sort(top_indices)

    return [float(freqs[i]) for i in top_indices]


def _compute_hnr(samples: np.ndarray, sample_rate: int) -> float:
    """Estimate Harmonic-to-Noise Ratio (HNR) using autocorrelation.

    HNR measures voice clarity: how much of the signal is periodic (voiced)
    versus aperiodic (breathy/noisy).  Higher values = cleaner voicing.

    Returns HNR in dB, or 0.0 if the signal is too quiet.
    """
    if np.max(np.abs(samples)) < 1e-6:
        return 0.0

    # Autocorrelation via FFT (fast).
    n = len(samples)
    fft = np.fft.rfft(samples, n=2 * n)
    acf = np.fft.irfft(fft * np.conj(fft))[:n]
    acf /= acf[0] if acf[0] > 0 else 1.0

    # Search for the autocorrelation peak in the voiced pitch range
    # (50 Hz – 500 Hz → lag range in samples).
    min_lag = max(1, sample_rate // 500)
    max_lag = min(n - 1, sample_rate // 50)

    if min_lag >= max_lag:
        return 0.0

    search_region = acf[min_lag:max_lag + 1]
    if len(search_region) == 0:
        return 0.0

    peak_val = float(np.max(search_region))

    if peak_val <= 0.0:
        return 0.0

    # HNR = 10 * log10(r / (1 - r)) where r is the peak autocorrelation.
    peak_val = min(peak_val, 0.9999)  # Clamp to avoid log(inf).
    hnr = 10.0 * np.log10(peak_val / (1.0 - peak_val))
    return float(hnr)


# ── Public API ───────────────────────────────────────────────────────────────

def analyse_frame(samples: np.ndarray,
                  sample_rate: int = config.SAMPLE_RATE,
                  n_formants: int = config.FORMANT_PEAKS) -> VoiceSnapshot:
    """Analyse a single audio frame and return a VoiceSnapshot.

    This is the pure-computation entry point — it does not touch the
    microphone.  Use it when you already have samples (e.g. from the DSP
    pipeline or a file) or when writing tests.

    Args:
        samples:     1-D float32 array of normalised PCM samples [-1.0, 1.0].
        sample_rate: Sample rate in Hz.
        n_formants:  Number of formant peaks to extract.

    Returns:
        A populated VoiceSnapshot dataclass.
    """
    samples = samples.astype(np.float32, copy=False)
    n = len(samples)

    # Magnitude spectrum (rfft gives positive frequencies only).
    window = np.hanning(n).astype(np.float32)
    windowed = samples * window
    spectrum = np.fft.rfft(windowed)
    magnitude = np.abs(spectrum).astype(np.float32)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate).astype(np.float32)

    # Spectral envelope (smoothed magnitude in dB).
    envelope_db = _spectral_envelope(magnitude)

    # Fundamental frequency.
    f0 = _find_fundamental(magnitude, freqs)

    # Formants.
    formants = _find_formants(envelope_db, freqs, n_formants)

    # HNR.
    hnr = _compute_hnr(samples, sample_rate)

    # Energy.
    energy = _rms_db(samples)

    return VoiceSnapshot(
        timestamp=time.time(),
        fundamental_frequency_hz=f0,
        formants=formants,
        spectral_envelope=envelope_db,
        hnr_db=hnr,
        energy_db=energy,
    )


def open_mic_stream(sample_rate: int = config.SAMPLE_RATE,
                    frame_buffer: int = config.FRAME_BUFFER,
                    device_index: int | None = config.MIC_DEVICE_INDEX):
    """Open a PyAudio microphone input stream.

    Returns a (pyaudio_instance, stream) tuple.  The caller is responsible
    for closing both when done::

        pa, stream = open_mic_stream()
        try:
            raw = stream.read(config.FRAME_BUFFER)
            ...
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

    Args:
        sample_rate:  Capture sample rate in Hz.
        frame_buffer: Frames per read buffer.
        device_index: PyAudio device index, or None for system default.

    Returns:
        Tuple of (pyaudio.PyAudio instance, pyaudio.Stream).
    """
    import pyaudio

    pa = pyaudio.PyAudio()
    kwargs: dict = dict(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        frames_per_buffer=frame_buffer,
    )
    if device_index is not None:
        kwargs["input_device_index"] = device_index

    stream = pa.open(**kwargs)
    return pa, stream


def capture_snapshot(stream,
                     sample_rate: int = config.SAMPLE_RATE,
                     frame_buffer: int = config.FRAME_BUFFER,
                     n_formants: int = config.FORMANT_PEAKS) -> VoiceSnapshot:
    """Read one frame from *stream* and return a VoiceSnapshot.

    Args:
        stream:       An open PyAudio input stream.
        sample_rate:  Sample rate the stream was opened with.
        frame_buffer: Number of frames to read.
        n_formants:   Number of formant peaks to extract.

    Returns:
        A populated VoiceSnapshot dataclass.
    """
    raw = stream.read(frame_buffer, exception_on_overflow=False)
    samples = _bytes_to_float32(raw)
    return analyse_frame(samples, sample_rate=sample_rate, n_formants=n_formants)
