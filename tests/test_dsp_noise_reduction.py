"""Tests for ``dsp/noise_reduction.py``."""

from __future__ import annotations

import numpy as np

from dsp.noise_reduction import SpectralSubtractor


def _make() -> SpectralSubtractor:
    return SpectralSubtractor(
        frame_length=256,
        noise_floor_multiplier=1.2,
        spectral_floor=0.1,
        noise_estimation_frames=4,
    )


class TestNoiseEstimation:
    def test_not_profiled_initially(self):
        s = _make()
        assert s.is_noise_profiled is False

    def test_profile_after_enough_frames(self):
        s = _make()
        noise = np.random.default_rng(0).standard_normal(256).astype(np.float32) * 0.01
        for _ in range(4):
            s.process(noise)
        assert s.is_noise_profiled is True

    def test_warmup_returns_input_unchanged(self):
        s = _make()
        frame = np.random.default_rng(1).standard_normal(256).astype(np.float32) * 0.01
        out = s.process(frame)
        np.testing.assert_array_equal(out, frame)

    def test_reset_clears_profile(self):
        s = _make()
        for _ in range(4):
            s.process(np.zeros(256, dtype=np.float32) + 0.01)
        assert s.is_noise_profiled
        s.reset()
        assert not s.is_noise_profiled


class TestSubtraction:
    def test_output_shape_and_dtype(self):
        s = _make()
        frame = np.random.default_rng(2).standard_normal(256).astype(np.float32) * 0.01
        for _ in range(4):
            s.process(frame)
        out = s.process(frame)
        assert out.shape == (256,)
        assert out.dtype == np.float32

    def test_reduces_stationary_noise(self):
        s = _make()
        rng = np.random.default_rng(42)
        noise = rng.standard_normal(256).astype(np.float32) * 0.05
        # Profile using noise-only frames.
        for _ in range(4):
            s.process(noise)
        out = s.process(noise)
        # Output energy of pure noise should be lower than input energy.
        assert np.sum(out ** 2) < np.sum(noise ** 2)

    def test_spectral_floor_prevents_total_silence(self):
        """Applying subtraction with an aggressive multiplier should not
        zero the signal out below the spectral floor."""
        s = SpectralSubtractor(
            frame_length=256, noise_floor_multiplier=100.0,
            spectral_floor=0.1, noise_estimation_frames=2,
        )
        rng = np.random.default_rng(3)
        noise = rng.standard_normal(256).astype(np.float32) * 0.05
        for _ in range(2):
            s.process(noise)
        out = s.process(noise)
        # Floor of 0.1 × original magnitude means ~1 % of energy preserved.
        assert np.sum(out ** 2) > 0.0

    def test_preserves_speech_above_noise(self):
        """A strong tone added on top of the profiled noise should still
        appear in the output."""
        s = _make()
        rng = np.random.default_rng(7)
        noise = rng.standard_normal(256).astype(np.float32) * 0.01
        for _ in range(4):
            s.process(noise)
        t = np.arange(256) / 16_000.0
        tone = (0.5 * np.sin(2 * np.pi * 1000.0 * t)).astype(np.float32)
        mixed = tone + noise
        out = s.process(mixed)
        # Output should still be dominated by a 1 kHz tone.
        spectrum = np.abs(np.fft.rfft(out))
        freqs = np.fft.rfftfreq(256, d=1 / 16_000.0)
        peak_freq = freqs[np.argmax(spectrum)]
        assert abs(peak_freq - 1000.0) < 100.0
