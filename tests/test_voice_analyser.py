"""Tests for ``voice/analyser.py`` (pure computation helpers only)."""

from __future__ import annotations

import numpy as np
import pytest

from voice.analyser import (
    VoiceSnapshot,
    _bytes_to_float32,
    _compute_hnr,
    _find_formants,
    _find_fundamental,
    _rms_db,
    _spectral_envelope,
    analyse_frame,
)


SR = 44_100


def _tone(freq: float, amplitude: float = 0.5, n: int = 4096,
          sr: int = SR) -> np.ndarray:
    t = np.arange(n) / sr
    return (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float32)


class TestVoiceSnapshot:
    def test_defaults(self):
        s = VoiceSnapshot()
        assert s.timestamp == 0.0
        assert s.fundamental_frequency_hz == 0.0
        assert s.formants == []
        assert s.spectral_envelope.size == 0
        assert s.hnr_db == 0.0
        assert s.energy_db == -100.0


class TestBytesToFloat32:
    def test_round_trip(self):
        arr = np.array([0, 32767, -32768], dtype=np.int16)
        out = _bytes_to_float32(arr.tobytes())
        assert out.dtype == np.float32
        assert out[0] == 0.0
        assert abs(out[1] - 32767 / 32768.0) < 1e-6
        assert out[2] == -1.0


class TestRmsDb:
    def test_silence_floor(self):
        assert _rms_db(np.zeros(1024, dtype=np.float32)) == -100.0

    def test_unit_amplitude_is_zero_dbfs(self):
        x = np.ones(1024, dtype=np.float32)
        assert abs(_rms_db(x) - 0.0) < 1e-3

    def test_half_amplitude_is_approx_minus_6(self):
        x = np.ones(1024, dtype=np.float32) * 0.5
        assert abs(_rms_db(x) - (-6.02)) < 0.1


class TestSpectralEnvelope:
    def test_shape(self):
        mag = np.ones(128, dtype=np.float32)
        env = _spectral_envelope(mag, smooth_width=5)
        assert env.shape == mag.shape
        assert env.dtype == np.float32

    def test_db_floor_for_zero(self):
        mag = np.zeros(32, dtype=np.float32)
        env = _spectral_envelope(mag, smooth_width=3)
        # 20 log10(1e-10) = -200 dB.
        assert np.all(env < -150.0)


class TestFindFundamental:
    def test_detects_200_hz(self):
        n = 4096
        tone = _tone(200.0, n=n)
        spectrum = np.abs(np.fft.rfft(tone))
        freqs = np.fft.rfftfreq(n, d=1 / SR).astype(np.float32)
        f0 = _find_fundamental(spectrum, freqs)
        assert abs(f0 - 200.0) < 15.0

    def test_returns_zero_for_silence(self):
        freqs = np.fft.rfftfreq(1024, d=1 / SR).astype(np.float32)
        spectrum = np.zeros_like(freqs)
        assert _find_fundamental(spectrum, freqs) == 0.0

    def test_no_mask_bins(self):
        # Very small frame so no bins exist below the high cutoff.
        freqs = np.array([10.0], dtype=np.float32)
        spectrum = np.array([1.0], dtype=np.float32)
        assert _find_fundamental(spectrum, freqs, low_hz=1000, high_hz=2000) == 0.0


class TestFindFormants:
    def test_no_valid_bins(self):
        env = np.array([0.0], dtype=np.float32)
        freqs = np.array([50.0], dtype=np.float32)
        assert _find_formants(env, freqs, n_formants=3, min_freq=10_000.0) == []

    def test_detects_multiple_peaks(self):
        # Build a synthetic envelope with clear peaks at bins 50, 100, 150.
        n = 257
        env = np.full(n, -50.0, dtype=np.float32)
        freqs = np.linspace(0, 8000, n, dtype=np.float32)
        for i in (50, 100, 150):
            env[i - 2:i + 3] = -10.0
        formants = _find_formants(env, freqs, n_formants=3, min_freq=200.0)
        assert len(formants) == 3
        # Peaks should be sorted ascending by frequency.
        assert formants == sorted(formants)


class TestComputeHnr:
    def test_silent_returns_zero(self):
        assert _compute_hnr(np.zeros(1024, dtype=np.float32), SR) == 0.0

    def test_periodic_signal_positive_hnr(self):
        # Pure tone → strong autocorrelation peak → positive HNR.
        hnr = _compute_hnr(_tone(200.0, n=4096), SR)
        assert hnr > 0.0

    def test_invalid_lag_range_returns_zero(self):
        # Use an impossibly short sample array.
        samples = np.array([0.3, -0.3], dtype=np.float32)
        assert _compute_hnr(samples, SR) == 0.0


class TestAnalyseFrame:
    def test_returns_populated_snapshot(self):
        tone = _tone(200.0, amplitude=0.5, n=4096)
        snap = analyse_frame(tone, sample_rate=SR, n_formants=3)
        assert isinstance(snap, VoiceSnapshot)
        assert snap.spectral_envelope.size > 0
        assert snap.fundamental_frequency_hz > 0
        assert snap.energy_db > -50.0
        assert snap.timestamp > 0.0

    def test_silence_low_energy(self):
        snap = analyse_frame(np.zeros(4096, dtype=np.float32), sample_rate=SR)
        assert snap.energy_db == -100.0
        assert snap.fundamental_frequency_hz == 0.0

    def test_dtype_coercion(self):
        tone = _tone(150.0, n=2048).astype(np.float64)
        snap = analyse_frame(tone, sample_rate=SR)
        # Envelope is float32 per implementation.
        assert snap.spectral_envelope.dtype == np.float32
