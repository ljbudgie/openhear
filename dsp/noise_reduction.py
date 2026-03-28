"""
noise_reduction.py – spectral subtraction noise reducer for OpenHear.

Implements the classic Boll (1979) spectral subtraction algorithm:
  1. Estimate the noise spectrum from the first few frames (assumed to
     contain background noise only).
  2. Subtract the estimated noise magnitude spectrum from every subsequent
     frame's magnitude spectrum.
  3. Apply a spectral floor to prevent over-subtraction artefacts.
  4. Reconstruct the time-domain signal using the original phase.

Tunable parameters (from dsp/config.py):
  - NOISE_FLOOR_MULTIPLIER:    over-subtraction factor (alpha).
  - SPECTRAL_FLOOR:            minimum post-subtraction spectral fraction.
  - NOISE_ESTIMATION_FRAMES:   how many initial frames to use for noise profile.

References:
  - Boll, S.F. (1979). Suppression of acoustic noise in speech using spectral
    subtraction. IEEE Transactions on Acoustics, Speech, and Signal Processing.
"""

from __future__ import annotations

import numpy as np


class SpectralSubtractor:
    """Stateful spectral-subtraction noise reducer.

    Noise estimation runs automatically during the first
    *noise_estimation_frames* calls to :meth:`process`.  After that the
    noise profile is frozen and subtraction begins.

    Args:
        frame_length:            Number of samples per processing frame
                                 (should equal FRAMES_PER_BUFFER in config.py).
        noise_floor_multiplier:  Over-subtraction factor (alpha >= 1.0).
        spectral_floor:          Minimum retained fraction after subtraction.
        noise_estimation_frames: Number of frames used to build noise profile.
    """

    def __init__(
        self,
        frame_length: int,
        noise_floor_multiplier: float = 1.2,
        spectral_floor: float = 0.10,
        noise_estimation_frames: int = 8,
    ) -> None:
        self.frame_length = frame_length
        self.alpha = noise_floor_multiplier
        self.beta = spectral_floor
        self._estimation_frames_needed = noise_estimation_frames

        # Accumulated magnitude spectrum sum used during noise estimation.
        fft_bins = frame_length // 2 + 1
        self._noise_sum = np.zeros(fft_bins, dtype=np.float64)
        self._frames_collected: int = 0

        # Frozen noise magnitude spectrum (set once estimation is complete).
        self._noise_spectrum: np.ndarray | None = None

    # ------------------------------------------------------------------
    # Public API

    @property
    def is_noise_profiled(self) -> bool:
        """True once enough frames have been collected to begin subtraction."""
        return self._noise_spectrum is not None

    def process(self, samples: np.ndarray) -> np.ndarray:
        """Denoise *samples* and return a cleaned frame.

        During the noise estimation phase the input is returned unchanged
        (to avoid a silent gap at startup).  Once the noise profile is
        built every frame is subtracted.

        Args:
            samples: 1-D float32 array of normalised PCM samples.

        Returns:
            Denoised float32 array of the same length.
        """
        samples = samples.astype(np.float32, copy=False)

        # Step 1: FFT
        spectrum = np.fft.rfft(samples)
        magnitude = np.abs(spectrum)
        phase = np.angle(spectrum)

        # Step 2: noise estimation or subtraction.
        if not self.is_noise_profiled:
            self._noise_sum += magnitude.astype(np.float64)
            self._frames_collected += 1
            if self._frames_collected >= self._estimation_frames_needed:
                self._noise_spectrum = (
                    self._noise_sum / self._frames_collected
                ).astype(np.float32)
            # Return original samples during warm-up phase.
            return samples

        # Step 3: subtract noise magnitude (with over-subtraction factor).
        assert self._noise_spectrum is not None
        clean_magnitude = magnitude - self.alpha * self._noise_spectrum

        # Step 4: apply spectral floor — never subtract below beta * original.
        floor = self.beta * magnitude
        clean_magnitude = np.maximum(clean_magnitude, floor)

        # Step 5: reconstruct complex spectrum and convert back to time domain.
        clean_spectrum = clean_magnitude * np.exp(1j * phase)
        clean_samples = np.fft.irfft(clean_spectrum, n=self.frame_length)

        return clean_samples.astype(np.float32)

    def reset(self) -> None:
        """Reset noise profile and estimation state."""
        fft_bins = self.frame_length // 2 + 1
        self._noise_sum = np.zeros(fft_bins, dtype=np.float64)
        self._frames_collected = 0
        self._noise_spectrum = None
