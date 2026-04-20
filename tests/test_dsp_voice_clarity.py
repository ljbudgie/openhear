"""Tests for ``dsp/voice_clarity.py``."""

from __future__ import annotations

import numpy as np
import pytest

from dsp.voice_clarity import VoiceClarityEnhancer


class TestConstruction:
    def test_defaults(self):
        v = VoiceClarityEnhancer(frame_length=512, sample_rate=16_000)
        assert v.low_hz == 1000.0
        assert v.high_hz == 4000.0
        assert v.gain == 1.6

    def test_invalid_band_raises(self):
        with pytest.raises(ValueError, match="must be less than"):
            VoiceClarityEnhancer(
                frame_length=256, sample_rate=16_000, low_hz=4000, high_hz=1000,
            )

    def test_invalid_gain_raises(self):
        with pytest.raises(ValueError, match="should be >= 1.0"):
            VoiceClarityEnhancer(
                frame_length=256, sample_rate=16_000, gain=0.5,
            )


class TestMask:
    def test_mask_within_band_is_gain(self):
        v = VoiceClarityEnhancer(
            frame_length=512, sample_rate=16_000,
            low_hz=1000.0, high_hz=4000.0, gain=2.0,
        )
        freqs = np.fft.rfftfreq(512, d=1.0 / 16_000)
        in_band = (freqs >= 1000.0) & (freqs <= 4000.0)
        np.testing.assert_allclose(v._mask[in_band], 2.0)

    def test_mask_outside_band_is_unity(self):
        v = VoiceClarityEnhancer(
            frame_length=512, sample_rate=16_000,
            low_hz=1000.0, high_hz=4000.0, gain=2.0,
        )
        freqs = np.fft.rfftfreq(512, d=1.0 / 16_000)
        out_band = (freqs < 1000.0) | (freqs > 4000.0)
        np.testing.assert_allclose(v._mask[out_band], 1.0)


class TestProcess:
    def test_output_shape(self):
        v = VoiceClarityEnhancer(frame_length=256, sample_rate=16_000)
        x = np.zeros(256, dtype=np.float32)
        assert v.process(x).shape == (256,)

    def test_output_dtype(self):
        v = VoiceClarityEnhancer(frame_length=256, sample_rate=16_000)
        x = np.zeros(256, dtype=np.float32)
        assert v.process(x).dtype == np.float32

    def test_low_frequency_tone_unchanged(self):
        """A 200 Hz tone (below the emphasis band) should be unchanged."""
        sr = 16_000
        n = 1024
        v = VoiceClarityEnhancer(
            frame_length=n, sample_rate=sr,
            low_hz=1000.0, high_hz=4000.0, gain=2.0,
        )
        t = np.arange(n) / sr
        tone = (0.3 * np.sin(2 * np.pi * 200.0 * t)).astype(np.float32)
        out = v.process(tone)
        # RMS should be essentially unchanged.
        assert abs(np.std(out) - np.std(tone)) / np.std(tone) < 0.05

    def test_inband_tone_is_boosted(self):
        sr = 16_000
        n = 1024
        gain = 2.0
        v = VoiceClarityEnhancer(
            frame_length=n, sample_rate=sr,
            low_hz=1000.0, high_hz=4000.0, gain=gain,
        )
        t = np.arange(n) / sr
        tone = (0.3 * np.sin(2 * np.pi * 2000.0 * t)).astype(np.float32)
        out = v.process(tone)
        # RMS should be roughly gain times the input.
        ratio = np.std(out) / np.std(tone)
        assert 1.6 < ratio < 2.2
