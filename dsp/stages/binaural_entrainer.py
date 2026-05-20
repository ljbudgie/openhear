"""
binaural_entrainer.py – optional binaural beat generator for OpenHear.

This stage is deliberately output-only: it is intended to sit at the end of
the DSP chain, after hearing-path processing and limiting, so generated tones
are never fed back into compression, feedback cancellation, or voice stages.
"""

from __future__ import annotations

import logging

import numpy as np
from scipy.signal import lfilter

from dsp.audiogram_profile import Prescription
from dsp.stages.base import BaseStage

logger = logging.getLogger(__name__)

_WARNING_TEXT = "Experimental feature. Not a medical device. Consult a professional before use."
_MIN_BEAT_HZ = 4.0
_MAX_BEAT_HZ = 40.0
_MIN_CARRIER_HZ = 200.0
_MAX_CARRIER_HZ = 500.0
_MAX_AMPLITUDE = 0.7
# Conservative default: leaves headroom for audiogram compensation and any
# existing hearing-path signal before the final 0.7 hard limiter.
_BASE_TONE_AMPLITUDE = 0.12
# Mask is intentionally much quieter than the carrier so it softens the tone
# without dominating the entrainment signal.
_MASK_AMPLITUDE = 0.025
# Single-pole low-pass coefficient used to make deterministic white noise
# spectrally tilt toward pink-ish masking while staying cheap per block.
_PINK_FILTER_ALPHA = 0.98
# 120 dB HL maps to a 1.5x threshold weight; denominator is doubled to keep
# audiogram threshold influence conservative because gain_db is already applied.
_THRESHOLD_WEIGHT_DENOMINATOR = 240.0
_VALID_MASK_TYPES = {"pink_noise", "ambient", "none"}


class BinauralEntrainer(BaseStage):
    """Generate a safe, deterministic stereo binaural entrainment signal.

    Args:
        sample_rate: Audio sample rate in Hz.
        beat_hz: Left/right frequency offset in Hz. Enforced range: 4–40 Hz.
        carrier_hz: Centre carrier frequency in Hz. Enforced range: 200–500 Hz.
        duration_s: Optional session duration in seconds. ``None`` runs until
            the caller stops the pipeline.
        ramp_ms: Fade-in/fade-out ramp length in milliseconds.
        mask_type: ``"pink_noise"``, ``"ambient"``, or ``"none"``.
        prescription: Optional audiogram-derived per-ear gains/thresholds.
        own_voice_bypass: If true, generation is bypassed and input is returned
            unchanged except for stereo conversion and the hard limiter.
    """

    def __init__(
        self,
        *,
        sample_rate: int = 16_000,
        beat_hz: float = 6.0,
        carrier_hz: float = 300.0,
        duration_s: float | None = None,
        ramp_ms: float = 1000.0,
        mask_type: str = "pink_noise",
        prescription: Prescription | None = None,
        own_voice_bypass: bool = False,
    ) -> None:
        if sample_rate <= 0:
            raise ValueError(f"sample_rate must be positive, got {sample_rate}.")
        if not (_MIN_BEAT_HZ <= beat_hz <= _MAX_BEAT_HZ):
            raise ValueError(f"beat_hz must be 4–40 Hz, got {beat_hz}.")
        if not (_MIN_CARRIER_HZ <= carrier_hz <= _MAX_CARRIER_HZ):
            raise ValueError(f"carrier_hz must be 200–500 Hz, got {carrier_hz}.")
        if duration_s is not None and duration_s <= 0:
            raise ValueError(f"duration_s must be positive when set, got {duration_s}.")
        if ramp_ms < 0:
            raise ValueError(f"ramp_ms must be non-negative, got {ramp_ms}.")
        if mask_type not in _VALID_MASK_TYPES:
            raise ValueError(
                f"mask_type must be one of {sorted(_VALID_MASK_TYPES)}, got {mask_type!r}."
            )

        self.sample_rate = int(sample_rate)
        self.beat_hz = float(beat_hz)
        self.carrier_hz = float(carrier_hz)
        self.duration_s = None if duration_s is None else float(duration_s)
        self.ramp_ms = float(ramp_ms)
        self.mask_type = mask_type
        self.prescription = prescription
        self.own_voice_bypass = bool(own_voice_bypass)

        self.left_hz = self.carrier_hz - self.beat_hz / 2.0
        self.right_hz = self.carrier_hz + self.beat_hz / 2.0
        self._left_phase = 0.0
        self._right_phase = 0.0
        self._sample_index = 0
        self._warned = False
        self._rng = np.random.default_rng(0)
        self._pink_state = 0.0

        self._left_scale = self._ear_scale("left")
        self._right_scale = self._ear_scale("right")

    @property
    def max_amplitude(self) -> float:
        """Hard safety ceiling applied to the final stereo output."""
        return _MAX_AMPLITUDE

    def process(self, samples: np.ndarray) -> np.ndarray:
        """Mix binaural tones into a stereo block and hard-limit to ±0.7."""
        stereo = self._as_stereo(samples)
        if stereo.size == 0:
            return stereo.astype(np.float32)

        if self.own_voice_bypass or self._session_finished():
            return self._limit(stereo)

        self._warn_once()

        n = stereo.shape[0]
        envelope = self._ramp_envelope(n)
        tone = self._tone_block(n, envelope)
        mask = self._mask_block(stereo, n, envelope)
        mixed = stereo + tone + mask
        return self._limit(mixed)

    def reset(self) -> None:
        """Reset phase, time, warning, and deterministic mask state."""
        self._left_phase = 0.0
        self._right_phase = 0.0
        self._sample_index = 0
        self._warned = False
        self._rng = np.random.default_rng(0)
        self._pink_state = 0.0

    def _warn_once(self) -> None:
        if not self._warned:
            logger.warning(_WARNING_TEXT)
            self._warned = True

    def _session_finished(self) -> bool:
        if self.duration_s is None:
            return False
        return self._sample_index >= int(round(self.duration_s * self.sample_rate))

    def _tone_block(self, n: int, envelope: np.ndarray) -> np.ndarray:
        t = np.arange(n, dtype=np.float64) / self.sample_rate
        left = np.sin((2.0 * np.pi * self.left_hz * t) + self._left_phase)
        right = np.sin((2.0 * np.pi * self.right_hz * t) + self._right_phase)

        self._left_phase = (
            self._left_phase + 2.0 * np.pi * self.left_hz * n / self.sample_rate
        ) % (2.0 * np.pi)
        self._right_phase = (
            self._right_phase + 2.0 * np.pi * self.right_hz * n / self.sample_rate
        ) % (2.0 * np.pi)

        tone = np.column_stack(
            (
                left * _BASE_TONE_AMPLITUDE * self._left_scale,
                right * _BASE_TONE_AMPLITUDE * self._right_scale,
            )
        )
        return (tone * envelope[:, None]).astype(np.float32)

    def _mask_block(self, stereo: np.ndarray, n: int, envelope: np.ndarray) -> np.ndarray:
        if self.mask_type == "none":
            return np.zeros((n, 2), dtype=np.float32)
        if self.mask_type == "ambient":
            return (stereo * np.float32(0.05) * envelope[:, None]).astype(np.float32)

        white = self._rng.standard_normal(n)
        pink_mono, _ = lfilter(
            [1.0 - _PINK_FILTER_ALPHA],
            [1.0, -_PINK_FILTER_ALPHA],
            white,
            zi=[_PINK_FILTER_ALPHA * self._pink_state],
        )
        self._pink_state = float(pink_mono[-1])
        pink = np.column_stack((pink_mono, pink_mono))
        peak = float(np.max(np.abs(pink))) if pink.size else 0.0
        if peak > 0.0:
            pink = pink / peak
        return (pink * _MASK_AMPLITUDE * envelope[:, None]).astype(np.float32)

    def _ramp_envelope(self, n: int) -> np.ndarray:
        positions = self._sample_index + np.arange(n, dtype=np.float64)
        self._sample_index += n
        env = np.ones(n, dtype=np.float64)

        ramp_samples = int(round(self.ramp_ms * self.sample_rate / 1000.0))
        if ramp_samples > 0:
            env = np.minimum(env, np.clip(positions / ramp_samples, 0.0, 1.0))

        if self.duration_s is not None:
            duration_samples = int(round(self.duration_s * self.sample_rate))
            remaining = duration_samples - positions
            env = np.minimum(env, np.clip(remaining / max(ramp_samples, 1), 0.0, 1.0))
            env = np.where(positions < duration_samples, env, 0.0)

        return env.astype(np.float32)

    def _ear_scale(self, ear: str) -> float:
        if self.prescription is None:
            return 1.0

        bands = self.prescription.bands(ear)
        if not bands:
            return 1.0

        closest = min(bands, key=lambda band: abs(band.freq_hz - self.carrier_hz))
        gain_db = max(0.0, min(closest.gain_db, 35.0))
        threshold_db_hl = max(0.0, min(closest.threshold_db_hl, 120.0))
        threshold_weight = 1.0 + (threshold_db_hl / _THRESHOLD_WEIGHT_DENOMINATOR)
        scale = (10.0 ** (gain_db / 20.0)) * threshold_weight
        return float(min(scale, _MAX_AMPLITUDE / _BASE_TONE_AMPLITUDE))

    @staticmethod
    def _as_stereo(samples: np.ndarray) -> np.ndarray:
        arr = np.asarray(samples, dtype=np.float32)
        if arr.ndim == 1:
            return np.column_stack((arr, arr)).astype(np.float32)
        if arr.ndim == 2 and arr.shape[1] == 2:
            return arr.astype(np.float32, copy=False)
        raise ValueError(f"samples must be mono (n,) or stereo (n, 2), got shape {arr.shape}.")

    @staticmethod
    def _limit(samples: np.ndarray) -> np.ndarray:
        if samples.size == 0:
            return samples.astype(np.float32)
        peak = float(np.max(np.abs(samples)))
        if peak > _MAX_AMPLITUDE:
            samples = samples * (_MAX_AMPLITUDE / peak)
        return np.clip(samples, -_MAX_AMPLITUDE, _MAX_AMPLITUDE).astype(np.float32)
