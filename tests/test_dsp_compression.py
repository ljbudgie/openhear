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


class TestBlockBasedBehaviour:
    """Tests specific to the block-based (per-buffer) envelope implementation."""

    def test_output_shape_matches_input_various_sizes(self):
        """Output shape must equal input shape for several buffer sizes."""
        c = _make_compressor()
        for n in (64, 128, 256, 512, 1024):
            x = np.zeros(n, dtype=np.float32)
            assert c.process(x).shape == (n,), f"shape mismatch for n={n}"

    def test_gain_reduction_above_knee(self):
        """A single loud block above the knee must be attenuated."""
        c = _make_compressor(ratio=4.0, knee_dbfs=-30.0, attack_s=0.001)
        loud = np.ones(256, dtype=np.float32) * 0.8  # ~−1.9 dBFS, well above knee
        out = c.process(loud)
        # Whole block must be attenuated relative to input.
        assert float(np.max(np.abs(out))) < 0.8

    def test_passthrough_below_knee(self):
        """A block whose peak is well below the knee must pass through at unity gain."""
        # Knee at −10 dBFS; input at ~0.01 (≈ −40 dBFS), safely below knee.
        c = _make_compressor(knee_dbfs=-10.0)
        quiet = 0.01 * np.ones(256, dtype=np.float32)
        out = c.process(quiet)
        np.testing.assert_allclose(out, quiet, atol=1e-6)

    def test_state_continuity_across_blocks(self):
        """Envelope state must carry over so a loud first block raises the envelope
        for a subsequent quiet block (release behaviour)."""
        c = _make_compressor(ratio=4.0, knee_dbfs=-30.0, attack_s=0.001, release_s=1.0)
        loud = np.ones(256, dtype=np.float32) * 0.8
        c.process(loud)
        env_after_loud = c._envelope
        # Feed a quiet block — envelope should still be elevated (slow release).
        quiet = np.ones(256, dtype=np.float32) * 0.01
        c.process(quiet)
        # Envelope must have decayed but still be significantly above the quiet level.
        assert c._envelope > 0.01
        # And it must have started to decay from the loud level.
        assert c._envelope < env_after_loud
