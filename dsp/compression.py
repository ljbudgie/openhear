"""
compression.py – Wide Dynamic Range Compression (WDRC) for OpenHear.

Implements a single-band WDRC algorithm suitable for hearing aid DSP.
WDRC amplifies soft sounds more than loud sounds, compressing the wide
dynamic range of the acoustic world into the narrower dynamic range that
a hearing aid user can perceive comfortably.

Design choices:
  - Peak-following envelope detection with independent attack/release.
  - Knee point and ratio tunable via dsp/config.py.
  - Operates on a numpy float32 array (values in [-1.0, 1.0] representing
    normalised PCM samples) to avoid per-sample Python overhead.
  - No look-ahead; processing is causal to stay within the 20 ms budget.

References:
  - Kates, J.M. (2008). Digital Hearing Aids. Plural Publishing.
  - Moore, B.C.J. (2012). An Introduction to the Psychology of Hearing, 6th ed.
"""

from __future__ import annotations

import numpy as np


class WDRCompressor:
    """Stateful single-band WDRC processor.

    State (envelope follower level) is preserved across successive
    :meth:`process` calls so that the compressor behaves correctly at
    block boundaries.

    Args:
        sample_rate:      Audio sample rate in Hz.
        ratio:            Compression ratio (>= 1.0).  1.0 = linear.
        knee_dbfs:        Knee-point level in dBFS.  Signals above this
                          are compressed; signals below are passed through
                          with unity gain.
        attack_s:         Envelope attack time constant in seconds.
        release_s:        Envelope release time constant in seconds.
    """

    def __init__(
        self,
        sample_rate: int,
        ratio: float,
        knee_dbfs: float,
        attack_s: float,
        release_s: float,
    ) -> None:
        if ratio < 1.0:
            raise ValueError(f"Compression ratio must be >= 1.0, got {ratio}")
        self.ratio = ratio
        self.knee_dbfs = knee_dbfs

        # Pre-compute per-sample time constants from the block-level
        # attack/release times using a first-order IIR approximation.
        self._attack_coeff = np.exp(-1.0 / (sample_rate * attack_s))
        self._release_coeff = np.exp(-1.0 / (sample_rate * release_s))

        # Envelope follower state (linear magnitude, initialised to silence).
        self._envelope: float = 1e-10

    # ------------------------------------------------------------------

    def process(self, samples: np.ndarray) -> np.ndarray:
        """Apply WDRC to *samples* in-place and return the result.

        Args:
            samples: 1-D float32 array of normalised PCM samples [-1.0, 1.0].

        Returns:
            Compressed float32 array of the same shape.
        """
        samples = samples.astype(np.float32, copy=False)
        output = np.empty_like(samples)
        env = self._envelope

        knee_linear = 10.0 ** (self.knee_dbfs / 20.0)

        for i, x in enumerate(samples):
            # Envelope follower (peak detector).
            abs_x = abs(float(x))
            if abs_x > env:
                env = self._attack_coeff * env + (1.0 - self._attack_coeff) * abs_x
            else:
                env = self._release_coeff * env + (1.0 - self._release_coeff) * abs_x

            env = max(env, 1e-10)  # prevent log(0)

            # Apply gain above the knee.
            if env > knee_linear:
                # Desired output level = knee + (input_level - knee) / ratio
                input_db = 20.0 * np.log10(env)
                knee_db = self.knee_dbfs
                output_db = knee_db + (input_db - knee_db) / self.ratio
                gain = 10.0 ** ((output_db - input_db) / 20.0)
            else:
                gain = 1.0

            output[i] = np.float32(x * gain)

        self._envelope = env
        return output

    def reset(self) -> None:
        """Reset the compressor state (envelope follower)."""
        self._envelope = 1e-10
