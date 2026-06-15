"""Tests for ``dsp/output_safety.py``."""

from __future__ import annotations

import numpy as np
import pytest

from dsp.output_safety import OutputSafetyLimiter

SR = 16_000


def _tone(freq: float, amplitude: float, n: int = 256, sr: int = SR) -> np.ndarray:
    t = np.arange(n) / sr
    return (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float32)


class TestConstruction:
    def test_default_ceiling_is_below_full_scale(self):
        limiter = OutputSafetyLimiter()
        # -1.0 dBFS → ~0.891 linear.
        assert 0.0 < limiter.ceiling_linear < 1.0
        assert limiter.ceiling_linear == pytest.approx(10.0 ** (-1.0 / 20.0))

    def test_positive_dbfs_rejected(self):
        with pytest.raises(ValueError, match="max_output_dbfs"):
            OutputSafetyLimiter(max_output_dbfs=3.0)

    def test_non_positive_sample_rate_rejected(self):
        with pytest.raises(ValueError, match="sample_rate"):
            OutputSafetyLimiter(sample_rate=0)

    def test_negative_times_rejected(self):
        with pytest.raises(ValueError, match="non-negative"):
            OutputSafetyLimiter(attack_s=-0.1)

    def test_lower_ceiling_is_quieter(self):
        loud = OutputSafetyLimiter(max_output_dbfs=-1.0)
        quiet = OutputSafetyLimiter(max_output_dbfs=-12.0)
        assert quiet.ceiling_linear < loud.ceiling_linear


class TestCeilingGuarantee:
    def test_loud_block_never_exceeds_ceiling(self):
        limiter = OutputSafetyLimiter(max_output_dbfs=-6.0)
        loud = _tone(1000.0, amplitude=0.99)
        out = limiter.process(loud)
        assert np.max(np.abs(out)) <= limiter.ceiling_linear + 1e-6

    def test_full_scale_transient_clamped_immediately(self):
        # A sudden full-scale spike must be clamped on the very first block,
        # even before the smoothed gain envelope settles, thanks to the hard
        # clip safety net.
        limiter = OutputSafetyLimiter(max_output_dbfs=-6.0)
        spike = np.ones(256, dtype=np.float32)
        out = limiter.process(spike)
        assert np.max(np.abs(out)) <= limiter.ceiling_linear + 1e-6

    def test_repeated_loud_blocks_stay_bounded(self):
        limiter = OutputSafetyLimiter(max_output_dbfs=-3.0)
        for _ in range(50):
            out = limiter.process(_tone(800.0, amplitude=0.95))
            assert np.max(np.abs(out)) <= limiter.ceiling_linear + 1e-6

    def test_negative_full_scale_clamped(self):
        limiter = OutputSafetyLimiter(max_output_dbfs=-6.0)
        spike = -np.ones(256, dtype=np.float32)
        out = limiter.process(spike)
        assert np.min(out) >= -limiter.ceiling_linear - 1e-6


class TestTransparency:
    def test_quiet_block_passes_through_unchanged(self):
        limiter = OutputSafetyLimiter(max_output_dbfs=-1.0)
        quiet = _tone(1000.0, amplitude=0.1)
        out = limiter.process(quiet)
        np.testing.assert_allclose(out, quiet, atol=1e-6)

    def test_gain_never_amplifies(self):
        limiter = OutputSafetyLimiter()
        # Drive it loud, then quiet; the smoothed gain must stay <= 1.0.
        limiter.process(_tone(1000.0, amplitude=0.99))
        for _ in range(10):
            limiter.process(_tone(1000.0, amplitude=0.05))
            assert limiter.current_gain <= 1.0

    def test_silence_returns_silence(self):
        limiter = OutputSafetyLimiter()
        out = limiter.process(np.zeros(256, dtype=np.float32))
        assert np.all(out == 0.0)


class TestStageContract:
    def test_output_shape_and_dtype_preserved(self):
        limiter = OutputSafetyLimiter()
        block = _tone(1000.0, amplitude=0.5)
        out = limiter.process(block)
        assert out.shape == block.shape
        assert out.dtype == np.float32

    def test_empty_block_handled(self):
        limiter = OutputSafetyLimiter()
        out = limiter.process(np.zeros(0, dtype=np.float32))
        assert out.shape == (0,)

    def test_reset_restores_unity_gain(self):
        limiter = OutputSafetyLimiter()
        limiter.process(_tone(1000.0, amplitude=0.99))
        limiter.reset()
        assert limiter.current_gain == 1.0


class TestActivityTelemetry:
    def test_fresh_limiter_has_empty_stats(self):
        limiter = OutputSafetyLimiter()
        stats = limiter.stats
        assert stats.blocks_processed == 0
        assert stats.blocks_limited == 0
        assert stats.max_gain_reduction_db == 0.0
        assert stats.limited_fraction == 0.0

    def test_quiet_audio_never_counts_as_limited(self):
        limiter = OutputSafetyLimiter(max_output_dbfs=-1.0)
        for _ in range(5):
            limiter.process(_tone(1000.0, amplitude=0.1))
        stats = limiter.stats
        assert stats.blocks_processed == 5
        assert stats.blocks_limited == 0
        assert stats.max_gain_reduction_db == 0.0

    def test_loud_audio_records_limiting(self):
        limiter = OutputSafetyLimiter(max_output_dbfs=-6.0)
        for _ in range(10):
            limiter.process(_tone(1000.0, amplitude=0.99))
        stats = limiter.stats
        assert stats.blocks_processed == 10
        assert stats.blocks_limited >= 1
        assert stats.max_gain_reduction_db > 0.0
        assert 0.0 < stats.limited_fraction <= 1.0

    def test_full_scale_spike_reports_expected_attenuation(self):
        # A full-scale spike against a -6 dBFS ceiling must be attenuated by
        # ~6 dB on the very first block (hard clip), so the deepest recorded
        # reduction should be at least ~6 dB.
        limiter = OutputSafetyLimiter(max_output_dbfs=-6.0)
        limiter.process(np.ones(256, dtype=np.float32))
        stats = limiter.stats
        assert stats.blocks_limited == 1
        assert stats.max_gain_reduction_db >= 5.9

    def test_empty_blocks_do_not_count(self):
        limiter = OutputSafetyLimiter()
        limiter.process(np.zeros(0, dtype=np.float32))
        assert limiter.stats.blocks_processed == 0

    def test_reset_clears_telemetry(self):
        limiter = OutputSafetyLimiter(max_output_dbfs=-6.0)
        limiter.process(_tone(1000.0, amplitude=0.99))
        assert limiter.stats.blocks_processed == 1
        limiter.reset()
        stats = limiter.stats
        assert stats.blocks_processed == 0
        assert stats.blocks_limited == 0
        assert stats.max_gain_reduction_db == 0.0

    def test_summary_when_never_engaged_mentions_no_engagement(self):
        limiter = OutputSafetyLimiter(max_output_dbfs=-1.0)
        limiter.process(_tone(1000.0, amplitude=0.1))
        summary = limiter.summary()
        assert "never engaged" in summary
        # The full message should also surface the block count and ceiling.
        assert "1 blocks" in summary
        assert "-1.0 dBFS" in summary

    def test_summary_when_engaged_reports_counts(self):
        limiter = OutputSafetyLimiter(max_output_dbfs=-6.0)
        for _ in range(3):
            limiter.process(_tone(1000.0, amplitude=0.99))
        summary = limiter.summary()
        assert "engaged" in summary
        assert "dB" in summary

    def test_summary_with_no_audio(self):
        limiter = OutputSafetyLimiter()
        assert "no audio" in limiter.summary()
