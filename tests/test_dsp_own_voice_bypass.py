"""Tests for ``dsp/own_voice_bypass.py``."""

from __future__ import annotations

import numpy as np
import pytest

from dsp.own_voice_bypass import OwnVoiceBypass, _VoiceState


SR = 16_000


def _tone(freq: float, amplitude: float, n: int = 2048, sr: int = SR) -> np.ndarray:
    t = np.arange(n) / sr
    return (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float32)


class TestConstruction:
    def test_invalid_f0_range_raises(self):
        with pytest.raises(ValueError, match="f0_low_hz"):
            OwnVoiceBypass(f0_low_hz=300, f0_high_hz=80)

    def test_lag_bounds(self):
        b = OwnVoiceBypass(sample_rate=16_000, f0_low_hz=80.0, f0_high_hz=300.0)
        # lag_low = sr / f0_high = 16000/300 ≈ 53
        # lag_high = sr / f0_low  = 16000/80  = 200
        assert b._lag_low == 53
        assert b._lag_high == 200


class TestDetection:
    def test_silence_not_detected(self):
        b = OwnVoiceBypass(energy_threshold_dbfs=-20.0)
        silent = np.zeros(2048, dtype=np.float32)
        assert b._detect(silent) is False

    def test_low_energy_not_detected(self):
        b = OwnVoiceBypass(energy_threshold_dbfs=-20.0)
        tone = _tone(150.0, amplitude=0.001)  # Very quiet.
        assert b._detect(tone) is False

    def test_loud_voice_tone_detected(self):
        b = OwnVoiceBypass(energy_threshold_dbfs=-20.0)
        tone = _tone(150.0, amplitude=0.5)  # Loud tone in F0 range.
        assert b._detect(tone) is True

    def test_frame_too_short_for_f0_range(self):
        b = OwnVoiceBypass(sample_rate=16_000, f0_low_hz=80.0)
        # lag_high = 16000/80 = 200 ≥ frame length 100 → returns False.
        tone = _tone(150.0, amplitude=0.5, n=100)
        assert b._detect(tone) is False

    def test_noise_without_periodicity_not_detected(self):
        b = OwnVoiceBypass(energy_threshold_dbfs=-40.0)
        rng = np.random.default_rng(123)
        noise = (rng.standard_normal(2048).astype(np.float32) * 0.3)
        # White noise should not pass the periodicity check.
        assert b._detect(noise) is False


class TestStateMachine:
    def test_hysteresis_entry(self):
        b = OwnVoiceBypass(hysteresis_frames=3)
        assert b.is_own_voice is False
        for _ in range(2):
            b._update_state(True)
        assert b.is_own_voice is False
        b._update_state(True)
        assert b.is_own_voice is True

    def test_hysteresis_exit(self):
        b = OwnVoiceBypass(hysteresis_frames=2)
        for _ in range(2):
            b._update_state(True)
        assert b.is_own_voice is True
        for _ in range(2):
            b._update_state(False)
        assert b.is_own_voice is False

    def test_reset_clears_state(self):
        b = OwnVoiceBypass(hysteresis_frames=2)
        for _ in range(2):
            b._update_state(True)
        assert b.is_own_voice is True
        b.reset()
        assert b._state is _VoiceState.EXTERNAL
        assert b._consecutive_own == 0


class TestProcess:
    def test_external_audio_passed_through(self):
        b = OwnVoiceBypass(hysteresis_frames=2, bypass_gain=0.5)
        # A high-frequency tone (outside F0 band) with high energy should
        # not trigger own-voice detection.
        external = _tone(3000.0, amplitude=0.3)
        out = b.process(external)
        np.testing.assert_array_equal(out, external)

    def test_own_voice_attenuated(self):
        b = OwnVoiceBypass(
            hysteresis_frames=1, bypass_gain=0.5,
            energy_threshold_dbfs=-20.0,
        )
        voice_like = _tone(150.0, amplitude=0.5)
        out = b.process(voice_like)
        assert b.is_own_voice is True
        np.testing.assert_allclose(out, voice_like * 0.5, atol=1e-6)

    def test_accepts_non_float32_input(self):
        b = OwnVoiceBypass()
        x = np.zeros(2048, dtype=np.float64)
        assert b.process(x).dtype == np.float32
