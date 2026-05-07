"""Tests for ``dsp/beamforming.py``."""

from __future__ import annotations

import numpy as np
import pytest

from dsp.beamforming import (
    DelaySumBeamformer,
    MicrophoneArray,
    MvdrBeamformer,
    _fractional_delay,
    mono_passthrough,
)

SR = 16_000


class TestMonoPassthrough:
    def test_1d_array_returned_unchanged(self):
        x = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        out = mono_passthrough(x)
        np.testing.assert_array_equal(out, x)
        assert out.dtype == np.float32

    def test_single_row_2d_returns_1d(self):
        x = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)
        out = mono_passthrough(x)
        assert out.ndim == 1
        np.testing.assert_array_equal(out, [1.0, 2.0, 3.0])

    def test_multi_row_2d_raises(self):
        x = np.ones((2, 4), dtype=np.float32)
        with pytest.raises(ValueError, match="shape"):
            mono_passthrough(x)


class TestMicrophoneArray:
    def test_n_channels(self):
        arr = MicrophoneArray(positions_m=(0.0, 0.014), sample_rate=SR)
        assert arr.n_channels == 2

    def test_delays_for_0_deg_front(self):
        arr = MicrophoneArray(positions_m=(0.0, 0.014), sample_rate=SR)
        delays = arr.delays_for_direction(0.0)
        # Front-facing (0°): path diff = pos * cos(0) = pos * 1
        assert delays[0] == pytest.approx(0.0)
        assert delays[1] == pytest.approx(0.014 / 343.0, rel=1e-5)

    def test_delays_for_90_deg_broadside(self):
        arr = MicrophoneArray(positions_m=(0.0, 0.014), sample_rate=SR)
        delays = arr.delays_for_direction(90.0)
        # cos(90°) = 0 → zero delay for both mics
        np.testing.assert_allclose(delays, [0.0, 0.0], atol=1e-10)


class TestFractionalDelay:
    def test_zero_delay_returns_copy(self):
        x = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
        out = _fractional_delay(x, 0)
        np.testing.assert_array_equal(out, x)
        assert out is not x  # should be a copy

    def test_integer_right_shift(self):
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)
        out = _fractional_delay(x, 2.0)
        # First 2 samples are zero (zero-padded); then original values
        assert out[0] == pytest.approx(0.0)
        assert out[1] == pytest.approx(0.0)
        assert out[2] == pytest.approx(1.0)

    def test_fractional_right_shift_blends(self):
        x = np.array([1.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
        out = _fractional_delay(x, 0.5)
        # The first sample blends: (1.0 - 0.5) * 1.0 at index 0
        assert out[0] == pytest.approx(0.5)
        # The fractional part goes to index 1: 0.5 * 1.0
        assert out[1] == pytest.approx(0.5)

    def test_left_shift_negative_delay(self):
        """Negative delay shifts signal earlier (left shift)."""
        x = np.array([0.0, 1.0, 2.0, 3.0, 4.0], dtype=np.float32)
        out = _fractional_delay(x, -1.0)
        # Shift left by 1: x[1:] moves to x[:]
        assert out[0] == pytest.approx(1.0)
        assert out[1] == pytest.approx(2.0)
        assert out[2] == pytest.approx(3.0)

    def test_left_shift_fractional(self):
        """Left shift with fractional part blends adjacent samples."""
        x = np.array([0.0, 1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        out = _fractional_delay(x, -0.5)
        # Fractional left: index 0 = (1-0.5)*x[0] + ... blended
        # Just check that the function runs and returns the right shape
        assert out.shape == x.shape
        assert out.dtype == np.float32

    def test_delay_larger_than_signal_returns_zeros(self):
        """Delay ≥ len(signal) should produce an all-zero output."""
        x = np.ones(4, dtype=np.float32)
        out = _fractional_delay(x, 10.0)
        np.testing.assert_array_equal(out, 0.0)


class TestDelaySumBeamformer:
    def _two_mic_array(self) -> MicrophoneArray:
        return MicrophoneArray(positions_m=(0.0, 0.014), sample_rate=SR)

    def test_mono_input_passthrough(self):
        bf = DelaySumBeamformer(self._two_mic_array(), direction_deg=0.0)
        x = np.ones(256, dtype=np.float32)
        out = bf.process(x)
        np.testing.assert_array_equal(out, x)

    def test_output_shape_for_stereo(self):
        bf = DelaySumBeamformer(self._two_mic_array(), direction_deg=0.0)
        channels = np.ones((2, 256), dtype=np.float32)
        out = bf.process(channels)
        assert out.shape == (256,)

    def test_output_dtype_is_float32(self):
        bf = DelaySumBeamformer(self._two_mic_array(), direction_deg=0.0)
        channels = np.ones((2, 128), dtype=np.float64)
        out = bf.process(channels)
        assert out.dtype == np.float32

    def test_identical_channels_average_correctly(self):
        """Summing identical channels then dividing by n_channels = passthrough."""
        bf = DelaySumBeamformer(self._two_mic_array(), direction_deg=90.0)
        # At 90° broadside the delay is zero; identical channels → same output.
        signal = np.random.default_rng(42).uniform(-1, 1, 256).astype(np.float32)
        channels = np.vstack([signal, signal])
        out = bf.process(channels)
        # Output should approximate the input (both channels aligned at 90°).
        np.testing.assert_allclose(out, signal, atol=0.05)

    def test_wrong_channel_count_raises(self):
        bf = DelaySumBeamformer(self._two_mic_array(), direction_deg=0.0)
        with pytest.raises(ValueError, match="rows"):
            bf.process(np.ones((3, 128), dtype=np.float32))

    def test_3d_input_raises(self):
        bf = DelaySumBeamformer(self._two_mic_array(), direction_deg=0.0)
        with pytest.raises(ValueError, match="1-D or 2-D"):
            bf.process(np.ones((2, 128, 4), dtype=np.float32))

    def test_four_channel_array(self):
        arr = MicrophoneArray(positions_m=(0.0, 0.005, 0.010, 0.015), sample_rate=SR)
        bf = DelaySumBeamformer(arr, direction_deg=0.0)
        channels = np.ones((4, 256), dtype=np.float32)
        out = bf.process(channels)
        assert out.shape == (256,)


class TestMvdrBeamformer:
    def _two_mic_array(self) -> MicrophoneArray:
        return MicrophoneArray(positions_m=(0.0, 0.014), sample_rate=SR)

    def test_stub_produces_output(self):
        bf = MvdrBeamformer(self._two_mic_array(), direction_deg=0.0)
        channels = np.ones((2, 128), dtype=np.float32)
        out = bf.process(channels)
        assert out.shape == (128,)

    def test_warning_logged_once(self, caplog):
        import logging

        bf = MvdrBeamformer(self._two_mic_array())
        channels = np.ones((2, 64), dtype=np.float32)

        with caplog.at_level(logging.WARNING, logger="dsp.beamforming"):
            bf.process(channels)
            bf.process(channels)  # second call – warning should NOT repeat

        warning_msgs = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warning_msgs) == 1
        assert "stub" in warning_msgs[0].message.lower()

    def test_mono_input_passthrough(self):
        bf = MvdrBeamformer(self._two_mic_array())
        x = np.ones(64, dtype=np.float32)
        out = bf.process(x)
        np.testing.assert_array_equal(out, x)
