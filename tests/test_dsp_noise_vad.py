"""Tests for ``dsp/noise.py`` – the VoiceActivityDetector class."""

from __future__ import annotations

import numpy as np
import pytest

from dsp.noise import VoiceActivityDetector

SR = 16_000


def _make_vad(**kwargs) -> VoiceActivityDetector:
    defaults = dict(sample_rate=SR, threshold_db=9.0, adapt_seconds=1.0)
    defaults.update(kwargs)
    return VoiceActivityDetector(**defaults)


class TestConstruction:
    def test_defaults(self):
        vad = _make_vad()
        assert vad.sample_rate == SR
        assert vad.threshold_db == 9.0
        assert vad.adapt_seconds == 1.0

    def test_invalid_sample_rate_raises(self):
        with pytest.raises(ValueError, match="sample_rate"):
            VoiceActivityDetector(sample_rate=0)

    def test_invalid_adapt_seconds_raises(self):
        with pytest.raises(ValueError, match="adapt_seconds"):
            VoiceActivityDetector(sample_rate=SR, adapt_seconds=0.0)

    def test_max_zcr_none_disables_zcr_test(self):
        vad = VoiceActivityDetector(sample_rate=SR, max_zcr=None)
        assert vad.max_zcr is None


class TestIsSpeech:
    def test_empty_array_returns_false(self):
        vad = _make_vad()
        assert vad.is_speech(np.array([], dtype=np.float32)) is False

    def test_silence_returns_false(self):
        vad = _make_vad()
        assert not vad.is_speech(np.zeros(256, dtype=np.float32))

    def test_loud_tone_returns_true(self):
        vad = _make_vad(threshold_db=6.0)
        t = np.arange(512) / SR
        tone = (0.5 * np.sin(2 * np.pi * 200.0 * t)).astype(np.float32)
        assert vad.is_speech(tone)

    def test_noise_floor_adapts_on_non_speech_frames(self):
        vad = _make_vad(adapt_seconds=0.01)
        noise = np.random.default_rng(0).standard_normal(256).astype(np.float32) * 0.001
        initial_floor = vad.noise_floor_db
        vad.is_speech(noise)
        # Noise floor should have adapted upward toward the noise level.
        assert vad.noise_floor_db != initial_floor

    def test_speech_frame_does_not_update_noise_floor(self):
        vad = _make_vad(threshold_db=0.0, adapt_seconds=0.1)
        loud = np.ones(256, dtype=np.float32) * 0.9
        floor_before = vad._noise_rms
        vad.is_speech(loud)
        # If flagged as speech, noise floor is NOT updated.
        assert vad._noise_rms == floor_before

    def test_wideband_noise_rejected_by_zcr(self):
        """White noise has high zero-crossing rate → rejected even if energy is high."""
        vad = _make_vad(threshold_db=0.0, max_zcr=0.1)
        rng = np.random.default_rng(42)
        white = rng.standard_normal(1024).astype(np.float32) * 0.5
        # Speech-like energy but very high ZCR → should be rejected.
        result = vad.is_speech(white)
        assert not result

    def test_zcr_disabled_allows_wideband(self):
        """With max_zcr=None, white noise passes the ZCR test."""
        vad = _make_vad(threshold_db=0.0, max_zcr=None)
        rng = np.random.default_rng(42)
        white = rng.standard_normal(1024).astype(np.float32) * 0.5
        # Energy is well above threshold=0 so should be classified as speech.
        result = vad.is_speech(white)
        assert result


class TestNoiseFloorDb:
    def test_initial_value_is_very_negative(self):
        vad = _make_vad()
        assert vad.noise_floor_db < -100.0

    def test_increases_after_noise_frame(self):
        vad = _make_vad(adapt_seconds=0.001)
        noise = np.random.default_rng(1).standard_normal(256).astype(np.float32) * 0.01
        before = vad.noise_floor_db
        vad.is_speech(noise)
        assert vad.noise_floor_db > before


class TestReset:
    def test_reset_restores_initial_noise_floor(self):
        vad = _make_vad(adapt_seconds=0.001)
        noise = np.random.default_rng(2).standard_normal(256).astype(np.float32) * 0.1
        for _ in range(10):
            vad.is_speech(noise)
        vad.reset()
        assert vad._noise_rms == pytest.approx(1e-6)
        assert vad.noise_floor_db < -100.0
