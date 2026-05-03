"""Tests for dsp/occlusion_reduction.py."""

from __future__ import annotations

import numpy as np
import pytest

from dsp.occlusion_reduction import OcclusionReducer


SAMPLE_RATE = 16_000
FRAMES = 256


class TestOcclusionReducerInit:
    def test_default_parameters(self):
        r = OcclusionReducer(sample_rate=SAMPLE_RATE)
        assert r is not None

    def test_custom_parameters(self):
        r = OcclusionReducer(sample_rate=SAMPLE_RATE, corner_hz=200.0, slope_db_oct=6.0)
        assert r is not None

    def test_invalid_corner_hz_zero(self):
        with pytest.raises(ValueError, match="corner_hz"):
            OcclusionReducer(sample_rate=SAMPLE_RATE, corner_hz=0.0)

    def test_invalid_corner_hz_above_nyquist(self):
        nyquist = SAMPLE_RATE / 2
        with pytest.raises(ValueError, match="corner_hz"):
            OcclusionReducer(sample_rate=SAMPLE_RATE, corner_hz=nyquist)

    def test_invalid_slope_zero(self):
        with pytest.raises(ValueError, match="slope_db_oct"):
            OcclusionReducer(sample_rate=SAMPLE_RATE, slope_db_oct=0.0)

    def test_invalid_slope_negative(self):
        with pytest.raises(ValueError, match="slope_db_oct"):
            OcclusionReducer(sample_rate=SAMPLE_RATE, slope_db_oct=-6.0)


class TestOcclusionReducerProcess:
    def test_returns_float32(self):
        r = OcclusionReducer(sample_rate=SAMPLE_RATE)
        x = np.random.default_rng(0).uniform(-0.5, 0.5, FRAMES).astype(np.float32)
        y = r.process(x)
        assert y.dtype == np.float32

    def test_output_shape_preserved(self):
        r = OcclusionReducer(sample_rate=SAMPLE_RATE)
        x = np.ones(FRAMES, dtype=np.float32) * 0.1
        y = r.process(x)
        assert y.shape == x.shape

    def test_silence_in_silence_out(self):
        r = OcclusionReducer(sample_rate=SAMPLE_RATE)
        x = np.zeros(FRAMES, dtype=np.float32)
        y = r.process(x)
        np.testing.assert_array_equal(y, 0.0)

    def test_high_frequency_passes_through(self):
        """A 2 kHz tone is well above the corner; it should be nearly unchanged."""
        r = OcclusionReducer(sample_rate=SAMPLE_RATE, corner_hz=300.0)
        t = np.arange(FRAMES * 10, dtype=np.float64) / SAMPLE_RATE
        # Generate 10 blocks' worth, process them all, measure the last block
        # so the filter has settled into steady state.
        signal = (0.5 * np.sin(2.0 * np.pi * 2000.0 * t)).astype(np.float32)
        for i in range(10):
            chunk = signal[i * FRAMES: (i + 1) * FRAMES]
            out = r.process(chunk)
        # The last block should be close to the original amplitude.
        rms_in = float(np.sqrt(np.mean(chunk**2)))
        rms_out = float(np.sqrt(np.mean(out**2)))
        assert abs(rms_in - rms_out) / rms_in < 0.05  # < 5% attenuation

    def test_low_frequency_attenuated(self):
        """A 50 Hz tone is well below the 300 Hz corner; it should be reduced."""
        r = OcclusionReducer(sample_rate=SAMPLE_RATE, corner_hz=300.0, slope_db_oct=12.0)
        # Generate many blocks so the filter reaches steady state.
        n_blocks = 40
        t = np.arange(FRAMES * n_blocks, dtype=np.float64) / SAMPLE_RATE
        signal = (0.5 * np.sin(2.0 * np.pi * 50.0 * t)).astype(np.float32)
        for i in range(n_blocks):
            chunk = signal[i * FRAMES: (i + 1) * FRAMES]
            out = r.process(chunk)
        rms_in = float(np.sqrt(np.mean(chunk**2)))
        rms_out = float(np.sqrt(np.mean(out**2)))
        # A 50 Hz tone is ~2.5 octaves below the 300 Hz corner; 12 dB/oct × 2.5 = ~30 dB
        # attenuation — expect at least 20 dB (linear factor 0.1).
        assert rms_out < rms_in * 0.1

    def test_state_preserved_across_blocks(self):
        """Processing two half-blocks should equal processing the full block."""
        r_full = OcclusionReducer(sample_rate=SAMPLE_RATE)
        r_split = OcclusionReducer(sample_rate=SAMPLE_RATE)
        rng = np.random.default_rng(42)
        x = rng.uniform(-0.5, 0.5, FRAMES).astype(np.float32)

        y_full = r_full.process(x)
        y_split = np.concatenate([
            r_split.process(x[:FRAMES // 2]),
            r_split.process(x[FRAMES // 2:]),
        ])
        np.testing.assert_allclose(y_full, y_split, atol=1e-6)


class TestOcclusionReducerReset:
    def test_reset_clears_state(self):
        """After reset the filter should behave as if freshly constructed."""
        r = OcclusionReducer(sample_rate=SAMPLE_RATE)
        r_fresh = OcclusionReducer(sample_rate=SAMPLE_RATE)
        rng = np.random.default_rng(7)
        # Run some signal through r to dirty its state.
        for _ in range(5):
            r.process(rng.uniform(-0.5, 0.5, FRAMES).astype(np.float32))
        r.reset()
        # Now both r (reset) and r_fresh should produce the same output.
        x = rng.uniform(-0.5, 0.5, FRAMES).astype(np.float32)
        np.testing.assert_allclose(r.process(x), r_fresh.process(x), atol=1e-6)

    def test_first_order_slope(self):
        """slope_db_oct=6 should produce a 1st-order filter without error."""
        r = OcclusionReducer(sample_rate=SAMPLE_RATE, corner_hz=300.0, slope_db_oct=6.0)
        x = np.ones(FRAMES, dtype=np.float32) * 0.1
        y = r.process(x)
        assert y.shape == x.shape
