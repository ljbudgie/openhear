"""
own_voice_bypass.py – own-voice detection and DSP bypass for OpenHear.

Hearing aid users frequently complain that their own voice sounds
unnatural ("hollow", "boomy", or "echoey") because the device processes
it through compression and noise reduction just like external sounds.
This module detects when the user is speaking and reduces DSP processing
intensity so that own-voice perception stays natural.

Detection strategy:
  1. **Energy gate** – own voice arrives via bone conduction and is
     typically louder (higher RMS) than most external sounds.
  2. **Fundamental frequency (F0)** – the autocorrelation of the frame
     is searched for a peak within the expected F0 range (80–300 Hz for
     human speech).  A clear peak combined with high energy strongly
     suggests own-voice activity.
  3. **Hysteresis state machine** – the detector transitions between
     EXTERNAL and OWN_VOICE states with separate entry/exit thresholds
     to avoid rapid toggling on borderline signals.

When own voice is detected, the module attenuates the DSP effect by
multiplying the processed signal with a configurable bypass gain (< 1.0
means less DSP effect, more natural own-voice sound).

Tunable parameters (from dsp/config.py):
  - OWN_VOICE_F0_LOW_HZ / OWN_VOICE_F0_HIGH_HZ:  F0 search range.
  - OWN_VOICE_ENERGY_THRESHOLD_DBFS:               energy gate level.
  - OWN_VOICE_BYPASS_GAIN:                         DSP reduction gain.
"""

from __future__ import annotations

import enum

import numpy as np


class _VoiceState(enum.Enum):
    """Internal states for the own-voice detector state machine."""

    EXTERNAL = 0
    OWN_VOICE = 1


class OwnVoiceBypass:
    """Own-voice detector with DSP bypass.

    Uses energy and fundamental-frequency cues to decide whether the
    current audio frame contains the user's own voice.  When own voice
    is detected, :meth:`process` attenuates the DSP effect by blending
    the dry (unprocessed) input toward unity gain, resulting in a more
    natural own-voice percept.

    Args:
        sample_rate:         Audio sample rate in Hz.
        f0_low_hz:           Lower bound of the F0 search range (Hz).
        f0_high_hz:          Upper bound of the F0 search range (Hz).
        energy_threshold_dbfs:
                             RMS energy threshold (dBFS).  Frames above
                             this level are candidates for own-voice.
        bypass_gain:         Gain multiplier applied to the processed
                             signal when own voice is detected.  1.0 = no
                             change; 0.5 = halve the DSP effect.
        hysteresis_frames:   Number of consecutive positive/negative
                             detections required before a state transition.
    """

    def __init__(
        self,
        sample_rate: int = 16_000,
        f0_low_hz: float = 80.0,
        f0_high_hz: float = 300.0,
        energy_threshold_dbfs: float = -20.0,
        bypass_gain: float = 0.5,
        hysteresis_frames: int = 3,
    ) -> None:
        if f0_low_hz >= f0_high_hz:
            raise ValueError(
                f"f0_low_hz ({f0_low_hz}) must be less than "
                f"f0_high_hz ({f0_high_hz})"
            )

        self.sample_rate = sample_rate
        self.f0_low_hz = f0_low_hz
        self.f0_high_hz = f0_high_hz
        self.energy_threshold_dbfs = energy_threshold_dbfs
        self.bypass_gain = bypass_gain
        self.hysteresis_frames = hysteresis_frames

        # Lag range for autocorrelation F0 search (in samples).
        self._lag_low = int(sample_rate / f0_high_hz)
        self._lag_high = int(sample_rate / f0_low_hz)

        # State machine.
        self._state = _VoiceState.EXTERNAL
        self._consecutive_own: int = 0
        self._consecutive_ext: int = 0

    # ------------------------------------------------------------------
    # Public API

    @property
    def is_own_voice(self) -> bool:
        """True when the detector believes the user is speaking."""
        return self._state is _VoiceState.OWN_VOICE

    def process(self, samples: np.ndarray) -> np.ndarray:
        """Detect own voice and attenuate DSP processing if present.

        When own voice is detected the output is scaled toward unity
        (less DSP effect) by *bypass_gain*.  When external sound is
        detected the signal is returned unchanged.

        Args:
            samples: 1-D float32 array of normalised PCM samples [-1.0, 1.0].

        Returns:
            float32 array of the same length, optionally attenuated.
        """
        samples = samples.astype(np.float32, copy=False)

        own_voice_detected = self._detect(samples)
        self._update_state(own_voice_detected)

        if self._state is _VoiceState.OWN_VOICE:
            return samples * np.float32(self.bypass_gain)

        return samples

    def reset(self) -> None:
        """Reset the detector state machine."""
        self._state = _VoiceState.EXTERNAL
        self._consecutive_own = 0
        self._consecutive_ext = 0

    # ------------------------------------------------------------------
    # Internal helpers

    def _detect(self, samples: np.ndarray) -> bool:
        """Return True if the frame looks like own voice."""
        # ── Energy gate ──────────────────────────────────────────────
        rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
        if rms < 1e-10:
            return False
        rms_dbfs = 20.0 * np.log10(rms)
        if rms_dbfs < self.energy_threshold_dbfs:
            return False

        # ── Autocorrelation-based F0 detection ───────────────────────
        frame = samples.astype(np.float64)
        frame = frame - np.mean(frame)  # remove DC
        n = len(frame)

        if self._lag_high >= n:
            # Frame too short for the requested F0 range.
            return False

        # Compute normalised autocorrelation in the lag range.
        autocorr = np.correlate(frame, frame, mode="full")
        autocorr = autocorr[n - 1:]  # keep only non-negative lags
        if autocorr[0] < 1e-10:
            return False
        autocorr = autocorr / autocorr[0]  # normalise

        lag_range = autocorr[self._lag_low: self._lag_high + 1]
        if len(lag_range) == 0:
            return False

        peak_value = float(np.max(lag_range))

        # A clear autocorrelation peak (> 0.3) indicates periodicity
        # consistent with voiced speech.
        return peak_value > 0.3

    def _update_state(self, detected: bool) -> None:
        """Update the hysteresis state machine."""
        if detected:
            self._consecutive_own += 1
            self._consecutive_ext = 0
        else:
            self._consecutive_ext += 1
            self._consecutive_own = 0

        if (
            self._state is _VoiceState.EXTERNAL
            and self._consecutive_own >= self.hysteresis_frames
        ):
            self._state = _VoiceState.OWN_VOICE
        elif (
            self._state is _VoiceState.OWN_VOICE
            and self._consecutive_ext >= self.hysteresis_frames
        ):
            self._state = _VoiceState.EXTERNAL
