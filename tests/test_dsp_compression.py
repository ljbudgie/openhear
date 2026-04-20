"""Tests for ``dsp/compression.py``."""

from __future__ import annotations

import numpy as np
import pytest

from dsp.compression import WDRCompressor


SR = 16_000


def _make_compressor(**kwargs) -> WDRCompressor:
    defaults = dict(
        sample_rate=SR,
        ratio=2.0,
        knee_dbfs=-40.0,
        attack_s=0.005,
        release_s=0.060,
    )
    defaults.update(kwargs)
    return WDRCompressor(**defaults)


class TestConstruction:
    def test_default_construction(self):
        c = _make_compressor()
        assert c.ratio == 2.0
        assert c.knee_dbfs == -40.0

    def test_invalid_ratio_raises(self):
        with pytest.raises(ValueError, match=">=\\s*1.0"):
            _make_compressor(ratio=0.5)


class TestProcess:
    def test_output_shape_matches_input(self):
        c = _make_compressor()
        x = np.zeros(256, dtype=np.float32)
        assert c.process(x).shape == x.shape

    def test_output_dtype_is_float32(self):
        c = _make_compressor()
        x = np.ones(128, dtype=np.float32) * 0.1
        assert c.process(x).dtype == np.float32

    def test_silence_in_silence_out(self):
        c = _make_compressor()
        x = np.zeros(128, dtype=np.float32)
        y = c.process(x)
        np.testing.assert_array_equal(y, 0.0)

    def test_below_knee_is_linear_gain(self):
        """Signals well below the knee point should pass through unchanged."""
        c = _make_compressor(knee_dbfs=-10.0)  # high knee, tiny input
        x = (0.01 * np.sin(np.linspace(0, 20 * np.pi, 512))).astype(np.float32)
        y = c.process(x)
        # Below knee → gain == 1 → output ≈ input.
        np.testing.assert_allclose(y, x, atol=1e-4)

    def test_above_knee_attenuates_loud_signal(self):
        """With ratio=4 and a low knee, loud sustained input should be attenuated."""
        c = _make_compressor(ratio=4.0, knee_dbfs=-40.0, attack_s=0.001)
        x = np.ones(2048, dtype=np.float32) * 0.8
        y = c.process(x)
        # After attack settles, output peak should be well below input peak.
        settled = np.abs(y[-256:])
        assert settled.max() < 0.8

    def test_accepts_non_float32_input(self):
        c = _make_compressor()
        x = np.zeros(64, dtype=np.float64)
        y = c.process(x)
        assert y.dtype == np.float32

    def test_state_persists_across_calls(self):
        """Envelope follower state survives between process() calls."""
        c = _make_compressor()
        loud = np.ones(512, dtype=np.float32) * 0.9
        c.process(loud)
        env_after_loud = c._envelope
        assert env_after_loud > 1e-5

    def test_reset_clears_state(self):
        c = _make_compressor()
        c.process(np.ones(256, dtype=np.float32) * 0.9)
        assert c._envelope > 1e-5
        c.reset()
        assert c._envelope == 1e-10

    def test_ratio_one_is_near_passthrough_above_knee(self):
        c = _make_compressor(ratio=1.0, knee_dbfs=-60.0)
        x = (0.5 * np.sin(np.linspace(0, 10 * np.pi, 512))).astype(np.float32)
        # Allow the envelope to settle.
        c.process(x)
        y = c.process(x)
        np.testing.assert_allclose(y, x, atol=5e-3)
