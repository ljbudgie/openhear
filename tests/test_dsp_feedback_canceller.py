"""Tests for ``dsp/feedback_canceller.py``."""

from __future__ import annotations

import numpy as np
import pytest

from dsp.feedback_canceller import FeedbackCanceller


class TestConstruction:
    def test_defaults(self):
        fc = FeedbackCanceller()
        assert fc.filter_length == 128
        assert fc.mu == 0.01
        assert fc.is_diverged is False

    def test_invalid_filter_length(self):
        with pytest.raises(ValueError, match="filter_length"):
            FeedbackCanceller(filter_length=0)

    def test_invalid_mu(self):
        with pytest.raises(ValueError, match="mu"):
            FeedbackCanceller(mu=0.0)

    def test_anti_feedback_gain_db_applied(self):
        fc = FeedbackCanceller(anti_feedback_gain_db=-6.0)
        # 10 ** (-6/20) ≈ 0.501
        assert abs(fc._anti_fb_gain - 0.5011872) < 1e-5


class TestProcess:
    def test_output_shape_and_dtype(self):
        fc = FeedbackCanceller(filter_length=32)
        x = np.zeros(128, dtype=np.float32)
        out = fc.process(x)
        assert out.shape == (128,)
        assert out.dtype == np.float32

    def test_silence_in_silence_out(self):
        fc = FeedbackCanceller(filter_length=32, anti_feedback_gain_db=0.0)
        x = np.zeros(128, dtype=np.float32)
        out = fc.process(x)
        np.testing.assert_array_equal(out, 0.0)

    def test_applies_anti_feedback_gain(self):
        """The first sample has zero feedback prediction, so output equals
        input × anti-feedback gain."""
        fc = FeedbackCanceller(
            filter_length=8, mu=0.001, anti_feedback_gain_db=-6.0,
        )
        x = np.ones(1, dtype=np.float32)
        out = fc.process(x)
        np.testing.assert_allclose(out[0], 0.5011872, atol=1e-5)

    def test_reset_clears_state(self):
        fc = FeedbackCanceller(filter_length=8, mu=0.5)
        rng = np.random.default_rng(0)
        fc.process(rng.standard_normal(256).astype(np.float32) * 0.3)
        assert np.any(fc._weights != 0.0)
        fc.reset()
        assert np.all(fc._weights == 0.0)
        assert np.all(fc._x_buf == 0.0)
        assert fc.is_diverged is False

    def test_divergence_triggers_phase_inversion(self):
        """Force divergence by setting weights beyond the energy ceiling."""
        fc = FeedbackCanceller(filter_length=4, anti_feedback_gain_db=0.0)
        fc._diverged = True
        x = np.array([0.5, 0.3, -0.1, 0.2], dtype=np.float32)
        out = fc.process(x)
        # First sample inverted; subsequent samples process normally after reset.
        assert out[0] == -0.5
        # After first sample, the diverged flag is cleared.
        assert fc.is_diverged is False

    def test_accepts_non_float32_input(self):
        fc = FeedbackCanceller(filter_length=8)
        x = np.zeros(16, dtype=np.float64)
        out = fc.process(x)
        assert out.dtype == np.float32
