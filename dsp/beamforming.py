"""
beamforming.py – multi-microphone beamforming for OpenHear.

Hearing aids increasingly carry two or more microphones per shell so the
pipeline can spatially focus on the talker in front while attenuating
noise from the sides and behind.  This module implements two open
techniques:

* **Delay-and-sum** (:class:`DelaySumBeamformer`): a fixed beamformer
  that aligns the wavefront from a target direction and sums the
  channels.  Cheap, robust, and the right default when the geometry is
  known.
* **MVDR** (:class:`MvdrBeamformer`, currently a documented stub):
  Minimum Variance Distortionless Response — adaptively shapes a null
  toward the loudest interferer.  The full implementation requires a
  noise covariance estimator and matrix inversion per block; this
  module exposes the API and falls back to delay-and-sum so the
  pipeline keeps working until the adaptive solver lands.

When a mono signal is passed in, the beamformers transparently behave
as a passthrough (:func:`mono_passthrough`), which is the right
behaviour for users with single-microphone setups.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: Speed of sound in air at 20 °C.
SPEED_OF_SOUND_M_S: float = 343.0


def mono_passthrough(samples: np.ndarray) -> np.ndarray:
    """Return ``samples`` unchanged when there is only one channel."""
    arr = np.asarray(samples, dtype=np.float32)
    if arr.ndim == 1:
        return arr
    if arr.ndim == 2 and arr.shape[0] == 1:
        return arr[0]
    raise ValueError(
        "mono_passthrough expects a 1-D or single-row 2-D array; got "
        f"shape {arr.shape}."
    )


@dataclass
class MicrophoneArray:
    """Geometry of a microphone array (linear, end-fire by convention).

    Attributes:
        positions_m: Mic positions along the array axis in metres.  The
            first mic is the reference (delay = 0).  For a typical
            front-back BTE pair this is e.g. ``(0.0, 0.014)``.
        sample_rate: Sample rate in Hz.
    """

    positions_m: tuple[float, ...]
    sample_rate: int

    @property
    def n_channels(self) -> int:
        return len(self.positions_m)

    def delays_for_direction(self, direction_deg: float) -> np.ndarray:
        """Return per-channel propagation delays (seconds) for *direction_deg*.

        Args:
            direction_deg: Angle of arrival in degrees, where 0° points
                along the array axis (front).
        """
        theta = np.deg2rad(direction_deg)
        # Distance the wavefront travels to each mic relative to the first.
        positions = np.asarray(self.positions_m, dtype=np.float64)
        path_diff = positions * np.cos(theta)
        return path_diff / SPEED_OF_SOUND_M_S


def _fractional_delay(samples: np.ndarray, delay_samples: float) -> np.ndarray:
    """Apply a fractional sample delay via linear interpolation.

    Positive *delay_samples* shifts the signal later in time.  Causal:
    the leading edge is zero-padded.
    """
    x = np.asarray(samples, dtype=np.float32)
    if delay_samples == 0:
        return x.copy()
    int_part = int(np.floor(delay_samples))
    frac = float(delay_samples - int_part)
    n = x.shape[0]
    out = np.zeros_like(x)
    if int_part >= 0:
        # Right shift.
        if int_part < n:
            shifted = x[: n - int_part]
            out[int_part:] = (1.0 - frac) * shifted
            if frac > 0 and (int_part + 1) < n:
                out[int_part + 1:] += frac * shifted[: n - int_part - 1]
    else:
        # Left shift (rare for beamforming but handle for completeness).
        shift = -int_part
        if shift < n:
            shifted = x[shift:]
            length = shifted.shape[0]
            out[:length] = (1.0 - frac) * shifted
            if frac > 0 and length > 1:
                out[: length - 1] += frac * shifted[1:]
    return out


class DelaySumBeamformer:
    """Fixed delay-and-sum beamformer for a known target direction.

    Args:
        array: Microphone-array geometry.
        direction_deg: Target direction in degrees (0 = forward).
    """

    def __init__(self, array: MicrophoneArray, direction_deg: float = 0.0) -> None:
        self.array = array
        self.direction_deg = direction_deg

    def process(self, channels: np.ndarray) -> np.ndarray:
        """Apply beamforming and return a 1-D mono signal.

        Args:
            channels: Either a 1-D mono array (returned as-is) or a 2-D
                array of shape ``(n_channels, n_samples)``.

        Returns:
            Mono float32 array of length ``n_samples``.
        """
        x = np.asarray(channels, dtype=np.float32)
        if x.ndim == 1:
            return mono_passthrough(x)
        if x.ndim != 2:
            raise ValueError(
                "channels must be 1-D or 2-D; got "
                f"{x.ndim}-D array of shape {x.shape}."
            )
        if x.shape[0] != self.array.n_channels:
            raise ValueError(
                f"channels has {x.shape[0]} rows but array has "
                f"{self.array.n_channels} mics."
            )

        delays_seconds = self.array.delays_for_direction(self.direction_deg)
        delays_samples = delays_seconds * self.array.sample_rate
        # Align: delay each channel by (max_delay − its own delay) so the
        # target wavefront lines up across channels.
        max_delay = float(np.max(delays_samples))
        out = np.zeros(x.shape[1], dtype=np.float32)
        for ch_index in range(self.array.n_channels):
            d = max_delay - float(delays_samples[ch_index])
            out += _fractional_delay(x[ch_index], d)
        out /= self.array.n_channels
        return out


class MvdrBeamformer:
    """Stub MVDR (Minimum Variance Distortionless Response) beamformer.

    The interface is shaped after a real MVDR implementation: the user
    supplies an array geometry, a steering direction, and (eventually)
    a noise covariance estimator.  Until the covariance estimation
    pipeline lands the :meth:`process` method falls back to
    :class:`DelaySumBeamformer` so the chain still produces correct
    audio, with a logged warning.

    Args:
        array: Microphone-array geometry.
        direction_deg: Target direction in degrees (0 = forward).
    """

    def __init__(self, array: MicrophoneArray, direction_deg: float = 0.0) -> None:
        import logging

        self._logger = logging.getLogger(__name__)
        self.array = array
        self.direction_deg = direction_deg
        self._fallback = DelaySumBeamformer(array, direction_deg)
        self._warned_once = False

    def process(self, channels: np.ndarray) -> np.ndarray:
        """Process channels via the (currently stubbed) MVDR algorithm.

        Args:
            channels: 1-D mono or 2-D ``(n_channels, n_samples)`` array.

        Returns:
            Mono float32 array, currently produced by delay-and-sum.
        """
        if not self._warned_once:
            self._logger.warning(
                "MvdrBeamformer is a stub and currently delegates to "
                "DelaySumBeamformer.  See module docstring for status."
            )
            self._warned_once = True
        return self._fallback.process(channels)
