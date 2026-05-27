"""
noise.py – noise-handling DSP for OpenHear.

This is the canonical name (per the master execution prompt) for the
noise-reduction stage.  The original implementation lives in
:mod:`dsp.noise_reduction` and is re-exported here unchanged so older
imports keep working while new code targets the canonical name.

In addition to re-exporting :class:`SpectralSubtractor`, this module
adds a lightweight energy-based :class:`VoiceActivityDetector` (VAD)
useful for gating spectral-subtraction noise updates so the noise
profile only adapts on speech-free frames.
"""

from __future__ import annotations

import numpy as np

from dsp.noise_reduction import SpectralSubtractor

__all__ = ["SpectralSubtractor", "VoiceActivityDetector"]


class VoiceActivityDetector:
    """Simple energy-and-zero-crossing voice-activity detector.

    The detector compares short-time RMS energy against an adaptive
    noise floor.  Frames whose energy exceeds the floor by
    ``threshold_db`` are flagged as speech.  An optional zero-crossing
    rate test rejects frames that look like wide-band noise even when
    their energy is high.

    The detector is intentionally simple and dependency-free; for
    production use it can be replaced with a learned model like WebRTC
    VAD or Silero.

    Args:
        sample_rate: Audio sample rate in Hz.
        threshold_db: How many dB above the running noise floor a frame
            must be to count as speech.  Typical 6–15 dB.
        adapt_seconds: Time constant for adapting the noise floor when
            no speech is present.
        max_zcr: Maximum acceptable zero-crossing rate (per sample) for
            a frame to be considered speech.  ``None`` disables the test.
    """

    def __init__(
        self,
        sample_rate: int,
        threshold_db: float = 9.0,
        adapt_seconds: float = 1.0,
        max_zcr: float | None = 0.35,
    ) -> None:
        if sample_rate <= 0:
            raise ValueError(f"sample_rate must be positive, got {sample_rate}.")
        if adapt_seconds <= 0:
            raise ValueError(f"adapt_seconds must be positive, got {adapt_seconds}.")
        self.sample_rate = sample_rate
        self.threshold_db = threshold_db
        self.adapt_seconds = adapt_seconds
        self.max_zcr = max_zcr

        # Running noise-floor RMS, initialised to a small non-zero value
        # so the first frame doesn't trip a divide-by-zero.
        self._noise_rms: float = 1e-6

    @property
    def noise_floor_db(self) -> float:
        """Current adaptive noise floor in dBFS."""
        return 20.0 * np.log10(max(self._noise_rms, 1e-9))

    def is_speech(self, samples: np.ndarray) -> bool:
        """Classify *samples* as speech (``True``) or non-speech.

        Args:
            samples: 1-D float array of normalised PCM (one block).

        Returns:
            ``True`` if the block is judged to contain speech.
        """
        x = np.asarray(samples, dtype=np.float32)
        if x.size == 0:
            return False

        rms = float(np.sqrt(np.mean(x * x) + 1e-12))
        rms_db = 20.0 * np.log10(max(rms, 1e-9))
        threshold = self.noise_floor_db + self.threshold_db
        speech_like = rms_db > threshold

        if speech_like and self.max_zcr is not None:
            # Reject wideband noise via zero-crossing rate.
            zcr = float(np.mean(np.abs(np.diff(np.signbit(x)))))
            if zcr > self.max_zcr:
                speech_like = False

        # Update the noise floor only on non-speech frames, with a
        # one-pole IIR whose time constant is `adapt_seconds`.
        if not speech_like:
            block_seconds = x.size / self.sample_rate
            tau = max(block_seconds, 1e-6) / self.adapt_seconds
            tau = min(tau, 1.0)
            self._noise_rms = (1.0 - tau) * self._noise_rms + tau * rms

        return speech_like

    def reset(self) -> None:
        """Reset the noise-floor estimate."""
        self._noise_rms = 1e-6
