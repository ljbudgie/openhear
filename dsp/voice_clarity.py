"""
voice_clarity.py – speech frequency emphasis for OpenHear.

Boosts the 1,000–4,000 Hz band which contains the majority of speech
intelligibility cues (consonant articulation, formant transitions).
Listeners with high-frequency sensorineural hearing loss particularly
benefit from this emphasis.

Implementation:
  - A brick-wall mask is applied in the frequency domain: bins within the
    speech band are multiplied by VOICE_CLARITY_GAIN; bins outside are
    left at unity.
  - Frequency-domain processing is used (rather than a time-domain FIR/IIR
    filter) because the pipeline already transforms frames to the frequency
    domain for noise reduction.  The bin mask is pre-computed in __init__.

Tunable parameters (from dsp/config.py):
  - VOICE_CLARITY_LOW_HZ:  lower edge of speech band (default 1,000 Hz).
  - VOICE_CLARITY_HIGH_HZ: upper edge of speech band (default 4,000 Hz).
  - VOICE_CLARITY_GAIN:    linear gain within the band (default 1.6 ≈ +4 dB).
"""

from __future__ import annotations

import numpy as np


class VoiceClarityEnhancer:
    """Frequency-domain speech band emphasis processor.

    Pre-computes a gain mask at construction time so that the per-frame
    cost is a single element-wise multiply on a numpy array.

    Args:
        frame_length: Number of samples per frame (must equal FRAMES_PER_BUFFER).
        sample_rate:  Audio sample rate in Hz.
        low_hz:       Lower bound of the emphasis band in Hz.
        high_hz:      Upper bound of the emphasis band in Hz.
        gain:         Linear gain to apply within the band.
    """

    def __init__(
        self,
        frame_length: int,
        sample_rate: int,
        low_hz: float = 1000.0,
        high_hz: float = 4000.0,
        gain: float = 1.6,
    ) -> None:
        if low_hz >= high_hz:
            raise ValueError(
                f"low_hz ({low_hz}) must be less than high_hz ({high_hz})"
            )
        if gain < 1.0:
            raise ValueError(f"gain ({gain}) should be >= 1.0 for emphasis")

        self.frame_length = frame_length
        self.sample_rate = sample_rate
        self.low_hz = low_hz
        self.high_hz = high_hz
        self.gain = gain

        # Pre-compute the frequency bin gain mask.
        self._mask = self._build_mask(frame_length, sample_rate, low_hz, high_hz, gain)

    # ------------------------------------------------------------------

    @staticmethod
    def _build_mask(
        frame_length: int,
        sample_rate: int,
        low_hz: float,
        high_hz: float,
        gain: float,
    ) -> np.ndarray:
        """Return a float32 gain mask for rfft output bins."""
        n_bins = frame_length // 2 + 1
        freqs = np.fft.rfftfreq(frame_length, d=1.0 / sample_rate)
        mask = np.ones(n_bins, dtype=np.float32)
        in_band = (freqs >= low_hz) & (freqs <= high_hz)
        mask[in_band] = gain
        return mask

    def process(self, samples: np.ndarray) -> np.ndarray:
        """Apply speech-band emphasis to *samples*.

        Args:
            samples: 1-D float32 array of normalised PCM samples.

        Returns:
            Emphasised float32 array of the same length.
        """
        samples = samples.astype(np.float32, copy=False)
        spectrum = np.fft.rfft(samples)
        spectrum *= self._mask
        output = np.fft.irfft(spectrum, n=self.frame_length)
        return output.astype(np.float32)
