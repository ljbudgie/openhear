"""Tests for ``voice/reference.py``."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from scipy.io import wavfile as scipy_wav

from voice.reference import (
    ReferenceProfile,
    _bandpass,
    _dominant_range,
    _load_audio,
    _resample,
    load_reference,
)

SR = 44_100


class TestReferenceProfileDefaults:
    def test_defaults(self):
        p = ReferenceProfile()
        assert p.artist_name == ""
        assert p.avg_formants == []
        assert p.spectral_envelope.size == 0
        assert p.dominant_frequency_range == (0.0, 0.0)


class TestBandpass:
    def test_removes_out_of_band_tone(self):
        n = 4096
        t = np.arange(n) / SR
        inband = 0.5 * np.sin(2 * np.pi * 1000 * t)
        outband = 0.5 * np.sin(2 * np.pi * 30 * t)  # below 80 Hz.
        mixed = (inband + outband).astype(np.float32)
        filtered = _bandpass(mixed, SR, 80.0, 8000.0)
        # Out-of-band component should be significantly attenuated.
        spec = np.abs(np.fft.rfft(filtered))
        freqs = np.fft.rfftfreq(n, d=1 / SR)
        bin_30 = np.argmin(np.abs(freqs - 30))
        bin_1000 = np.argmin(np.abs(freqs - 1000))
        assert spec[bin_1000] > 10 * spec[bin_30]

    def test_output_dtype(self):
        x = np.zeros(512, dtype=np.float32)
        out = _bandpass(x, SR, 80.0, 8000.0)
        assert out.dtype == np.float32


class TestResample:
    def test_identity_when_rates_match(self):
        x = np.arange(100, dtype=np.float32)
        out = _resample(x, 16_000, 16_000)
        np.testing.assert_array_equal(out, x)

    def test_downsample_by_two(self):
        n = 4096
        x = np.sin(2 * np.pi * np.arange(n) / n * 10).astype(np.float32)
        out = _resample(x, 16_000, 8_000)
        # Length should be approximately half.
        assert abs(len(out) - n // 2) < 10


class TestDominantRange:
    def test_all_below_peak_minus_threshold(self):
        env = np.array([-50, -50, -50, -50], dtype=np.float32)
        freqs = np.array([100, 200, 300, 400], dtype=np.float32)
        lo, hi = _dominant_range(env, freqs, threshold_db=10.0)
        # Peak is -50; all bins are within 10 dB → full range.
        assert lo == 100.0
        assert hi == 400.0

    def test_narrow_range(self):
        env = np.array([-100, -100, -20, -100, -100], dtype=np.float32)
        freqs = np.array([100, 200, 300, 400, 500], dtype=np.float32)
        lo, hi = _dominant_range(env, freqs, threshold_db=5.0)
        # Only bin at 300 Hz is within 5 dB of the peak.
        assert lo == 300.0
        assert hi == 300.0

    def test_all_equal_envelope(self):
        env = np.full(4, -30.0, dtype=np.float32)
        freqs = np.array([100, 200, 300, 400], dtype=np.float32)
        lo, hi = _dominant_range(env, freqs)
        assert lo == 100.0
        assert hi == 400.0


class TestLoadAudio:
    def test_wav_round_trip(self, tmp_path: Path):
        n = 1024
        x = (0.5 * np.sin(2 * np.pi * 440 * np.arange(n) / SR)).astype(np.float32)
        pcm = (x * 32767).astype(np.int16)
        path = tmp_path / "tone.wav"
        scipy_wav.write(str(path), SR, pcm)
        sr, data = _load_audio(path)
        assert sr == SR
        assert data.dtype == np.float32
        assert len(data) == n

    def test_wav_stereo_downmix(self, tmp_path: Path):
        n = 512
        left = np.zeros(n, dtype=np.int16)
        right = (np.ones(n, dtype=np.int16) * 10_000)
        stereo = np.stack([left, right], axis=1)
        path = tmp_path / "stereo.wav"
        scipy_wav.write(str(path), SR, stereo)
        _, mono = _load_audio(path)
        assert mono.ndim == 1
        assert len(mono) == n

    def test_wav_int32_normalises(self, tmp_path: Path):
        path = tmp_path / "int32.wav"
        pcm = np.array([0, 2**30, -(2**30)], dtype=np.int32)
        scipy_wav.write(str(path), SR, pcm)
        _, data = _load_audio(path)
        assert data.dtype == np.float32
        # 2^30 / 2^31 = 0.5.
        assert abs(data[1] - 0.5) < 1e-6

    def test_unsupported_format(self, tmp_path: Path):
        path = tmp_path / "file.mp3"
        path.write_bytes(b"bogus")
        with pytest.raises(ValueError, match="Unsupported audio format"):
            _load_audio(path)


class TestLoadReference:
    def _write_tone(self, path: Path, freq: float = 300.0, n: int = 16_384) -> None:
        x = (0.5 * np.sin(2 * np.pi * freq * np.arange(n) / SR)).astype(np.float32)
        pcm = (x * 32767).astype(np.int16)
        scipy_wav.write(str(path), SR, pcm)

    def test_populates_profile(self, tmp_path: Path):
        p = tmp_path / "tone.wav"
        self._write_tone(p)
        prof = load_reference(p, artist_name="test_tone",
                              sample_rate=SR, frame_size=1024)
        assert prof.artist_name == "test_tone"
        assert prof.spectral_envelope.size > 0
        lo, hi = prof.dominant_frequency_range
        assert lo <= hi

    def test_default_artist_name_uses_stem(self, tmp_path: Path):
        p = tmp_path / "alice.wav"
        self._write_tone(p)
        prof = load_reference(p, sample_rate=SR, frame_size=1024)
        assert prof.artist_name == "alice"

    def test_empty_audio_returns_default_profile(self, tmp_path: Path):
        # File too short for any frame.
        p = tmp_path / "short.wav"
        pcm = np.zeros(10, dtype=np.int16)
        scipy_wav.write(str(p), SR, pcm)
        prof = load_reference(p, sample_rate=SR, frame_size=1024)
        assert prof.spectral_envelope.size == 0
        assert prof.avg_formants == []
