"""Tests for dsp/output_limiter.py."""

from __future__ import annotations

import numpy as np
import pytest

from dsp.output_limiter import PeakLimiter


SAMPLE_RATE = 16_000
FRAMES = 256


class TestPeakLimiterInit:
    def test_default_parameters(self):
        lim = PeakLimiter()
        assert lim is not None

    def test_custom_parameters(self):
        lim = PeakLimiter(ceiling_dbfs=-6.0, attack_s=0.002, release_s=0.200, sample_rate=SAMPLE_RATE)
        assert lim is not None

    def test_invalid_ceiling_positive(self):
        with pytest.raises(ValueError, match="ceiling_dbfs"):
            PeakLimiter(ceiling_dbfs=3.0)

    def test_invalid_attack_zero(self):
        with pytest.raises(ValueError, match="attack_s"):
            PeakLimiter(attack_s=0.0)

    def test_invalid_release_negative(self):
        with pytest.raises(ValueError, match="release_s"):
            PeakLimiter(release_s=-1.0)

    def test_ceiling_at_zero_dbfs_is_valid(self):
        # 0 dBFS ceiling (unity) should be accepted.
        lim = PeakLimiter(ceiling_dbfs=0.0)
        assert lim is not None


class TestPeakLimiterProcess:
    def test_returns_float32(self):
        lim = PeakLimiter()
        x = np.random.default_rng(0).uniform(-0.5, 0.5, FRAMES).astype(np.float32)
        y = lim.process(x)
        assert y.dtype == np.float32

    def test_output_shape_preserved(self):
        lim = PeakLimiter()
        x = np.zeros(FRAMES, dtype=np.float32)
        y = lim.process(x)
        assert y.shape == x.shape

    def test_silence_in_silence_out(self):
        lim = PeakLimiter()
        x = np.zeros(FRAMES, dtype=np.float32)
        y = lim.process(x)
        np.testing.assert_array_equal(y, 0.0)

    def test_below_ceiling_unity_gain(self):
        """Signals well below the ceiling should pass through without reduction."""
        ceiling_dbfs = -6.0
        ceiling_lin = 10 ** (ceiling_dbfs / 20.0)  # ≈ 0.501
        # Use a signal clearly below the ceiling (0.1 << 0.5).
        lim = PeakLimiter(ceiling_dbfs=ceiling_dbfs, sample_rate=SAMPLE_RATE)
        x = np.full(FRAMES, 0.1, dtype=np.float32)
        # Process several blocks so limiter gain has settled at 1.0.
        for _ in range(20):
            y = lim.process(x.copy())
        np.testing.assert_allclose(y, x, rtol=1e-3)

    def test_above_ceiling_is_limited(self):
        """Signal whose peak exceeds the ceiling must be reduced below it."""
        ceiling_dbfs = -6.0
        ceiling_lin = 10 ** (ceiling_dbfs / 20.0)
        lim = PeakLimiter(ceiling_dbfs=ceiling_dbfs, attack_s=0.0001, sample_rate=SAMPLE_RATE)
        # Use a block that's 6 dB above the ceiling.
        x = np.full(FRAMES, ceiling_lin * 2.0, dtype=np.float32)
        # Process many blocks so the gain envelope has fully converged.
        for _ in range(100):
            y = lim.process(x.copy())
        peak_out = float(np.max(np.abs(y)))
        assert peak_out <= ceiling_lin * 1.05  # within 5% of ceiling

    def test_no_amplification_below_ceiling(self):
        """The limiter must never increase gain above 1.0."""
        lim = PeakLimiter(ceiling_dbfs=-1.0, sample_rate=SAMPLE_RATE)
        rng = np.random.default_rng(99)
        x = rng.uniform(-0.3, 0.3, FRAMES).astype(np.float32)
        for _ in range(50):
            y = lim.process(x.copy())
        # Output must be ≤ input (no amplification).
        assert float(np.max(np.abs(y))) <= float(np.max(np.abs(x))) + 1e-6

    def test_output_never_exceeds_one(self):
        """With a −1 dBFS ceiling the output peak must be < 1.0 at steady state."""
        lim = PeakLimiter(ceiling_dbfs=-1.0, attack_s=0.0001, sample_rate=SAMPLE_RATE)
        # Feed a signal that would clip without limiting.
        x = np.full(FRAMES, 1.5, dtype=np.float32)
        for _ in range(200):
            y = lim.process(x.copy())
        assert float(np.max(np.abs(y))) < 1.0


class TestPeakLimiterReset:
    def test_reset_returns_gain_to_unity(self):
        """After reset the limiter should behave as freshly constructed."""
        lim = PeakLimiter(ceiling_dbfs=-6.0, attack_s=0.0001, sample_rate=SAMPLE_RATE)
        lim_fresh = PeakLimiter(ceiling_dbfs=-6.0, attack_s=0.0001, sample_rate=SAMPLE_RATE)
        ceiling_lin = 10 ** (-6.0 / 20.0)
        # Drive the limiter into gain reduction.
        for _ in range(50):
            lim.process(np.full(FRAMES, ceiling_lin * 4.0, dtype=np.float32))
        lim.reset()
        # After reset both should produce identical output from the same input.
        x = np.full(FRAMES, 0.1, dtype=np.float32)
        np.testing.assert_allclose(lim.process(x), lim_fresh.process(x), atol=1e-6)

    def test_reset_gain_state_is_unity(self):
        lim = PeakLimiter()
        lim.reset()
        assert lim._gain == 1.0
