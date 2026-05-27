"""
feedback_canceller.py – LMS adaptive feedback cancellation for OpenHear.

# SAFETY DISCLAIMER
# This module is part of an open-source hearing aid research project.
# It is NOT certified as a medical device and must NOT be used as the
# sole mechanism for hearing protection or clinical hearing aid fitting.
# Misconfigured feedback cancellation can produce loud artefacts.
# Always test at safe volume levels.

Hearing aids that amplify sound and play it back through a speaker near
the microphone are susceptible to acoustic feedback (whistling).  The
LMS (Least Mean Squares) adaptive filter estimates the feedback path –
the transfer function from speaker output back to the microphone – and
subtracts the predicted feedback from the input signal in real time.

Algorithm outline:
  1. Maintain a finite-length adaptive filter W (the feedback-path model).
  2. For each sample, predict the feedback contribution as W · x_buf
     (the convolution of the filter with recent output samples).
  3. Subtract the prediction from the microphone input to obtain the
     error signal e, which is also the cleaned output.
  4. Update W using the LMS rule: W += 2 * mu * e * x_buf.
  5. If the filter energy diverges (exceeds a safety ceiling), fall back
     to phase inversion to suppress feedback until the filter is reset.

Tunable parameters (from dsp/config.py):
  - FEEDBACK_FILTER_LENGTH:    number of taps in the adaptive filter.
  - FEEDBACK_MU:               LMS step-size / learning rate.
  - ANTI_FEEDBACK_GAIN_DB:     extra loop-gain reduction near feedback.

References:
  - Haykin, S. (2002). Adaptive Filter Theory, 4th ed.  Prentice Hall.
  - Spriet, A. et al. (2008). Feedback control in hearing aids. Springer
    Handbook of Speech Processing.
"""

from __future__ import annotations

import numpy as np


class FeedbackCanceller:
    """Stateful LMS adaptive feedback canceller.

    Keeps the adaptive filter coefficients and a circular buffer of
    recent output samples across successive :meth:`process` calls so
    that adaptation is continuous at block boundaries.

    A phase-inversion fallback engages automatically when the filter
    energy exceeds a safety ceiling, preventing runaway oscillation
    until :meth:`reset` is called or the filter re-converges.

    Args:
        filter_length:      Number of taps in the adaptive FIR filter.
        mu:                 LMS step size (learning rate).  Smaller values
                            converge more slowly but are more stable.
        sample_rate:        Audio sample rate in Hz.
        anti_feedback_gain_db:
                            Additional gain reduction (dB) applied to the
                            output.  Reduces loop gain to prevent oscillation.
                            0 = no extra attenuation.
    """

    # Safety ceiling: if the L2 energy of the filter coefficients
    # exceeds filter_length * this value, we assume divergence.
    _ENERGY_CEILING_PER_TAP: float = 4.0

    def __init__(
        self,
        filter_length: int = 128,
        mu: float = 0.01,
        sample_rate: int = 16_000,
        anti_feedback_gain_db: float = -6.0,
    ) -> None:
        if filter_length < 1:
            raise ValueError(
                f"filter_length must be >= 1, got {filter_length}"
            )
        if mu <= 0.0:
            raise ValueError(f"mu must be > 0, got {mu}")

        self.filter_length = filter_length
        self.mu = mu
        self.sample_rate = sample_rate

        # Convert dB gain to linear multiplier.
        self._anti_fb_gain = 10.0 ** (anti_feedback_gain_db / 20.0)

        # Adaptive filter coefficients (feedback path model).
        self._weights = np.zeros(filter_length, dtype=np.float64)

        # Circular buffer of recent output samples used for prediction.
        self._x_buf = np.zeros(filter_length, dtype=np.float64)

        # Divergence flag.
        self._diverged: bool = False

    # ------------------------------------------------------------------
    # Public API

    @property
    def is_diverged(self) -> bool:
        """True when the adaptive filter has diverged."""
        return self._diverged

    def process(self, samples: np.ndarray) -> np.ndarray:
        """Cancel feedback from *samples* and return the cleaned signal.

        Args:
            samples: 1-D float32 array of normalised PCM samples [-1.0, 1.0].

        Returns:
            Cleaned float32 array of the same shape.
        """
        samples = samples.astype(np.float32, copy=False)
        output = np.empty_like(samples, dtype=np.float32)

        energy_ceiling = self.filter_length * self._ENERGY_CEILING_PER_TAP

        for i, mic_sample in enumerate(samples):
            mic = float(mic_sample)

            if self._diverged:
                # Phase-inversion fallback: simply invert the signal
                # to suppress the feedback loop until reset.
                error = -mic * self._anti_fb_gain
                output[i] = np.float32(error)
                # Attempt slow re-convergence by resetting weights.
                self._weights[:] = 0.0
                self._diverged = False
                continue

            # Predict feedback contribution from the adaptive filter.
            feedback_estimate = float(np.dot(self._weights, self._x_buf))

            # Error = microphone input minus estimated feedback.
            error = mic - feedback_estimate

            # LMS weight update: W += 2 * mu * e * x_buf
            norm = float(np.dot(self._x_buf, self._x_buf)) + 1e-10
            self._weights += (2.0 * self.mu * error / norm) * self._x_buf

            # Check for divergence (filter energy too high).
            filter_energy = float(np.dot(self._weights, self._weights))
            if filter_energy > energy_ceiling:
                self._diverged = True

            # Apply anti-feedback gain.
            out_sample = error * self._anti_fb_gain

            output[i] = np.float32(out_sample)

            # Shift the output buffer and insert the new output sample.
            self._x_buf = np.roll(self._x_buf, 1)
            self._x_buf[0] = out_sample

        return output

    def reset(self) -> None:
        """Reset the adaptive filter and all internal state."""
        self._weights[:] = 0.0
        self._x_buf[:] = 0.0
        self._diverged = False
