"""
output_limiter.py – final-stage peak limiter for the OpenHear DSP chain.

Sits at the end of the processing chain and ensures the output signal
never exceeds a configurable ceiling (default −1 dBFS).  This is a
software safety layer that complements the passive hardware MPO limiter
described in hardware/safety/mpo_calculator.py.

Design:
  - Block-level feedforward limiter: the peak of each input buffer is
    compared to the ceiling once per block, consistent with the
    block-based compressor elsewhere in the chain.
  - Gain changes are smoothed with independent attack and release
    envelopes so abrupt transients cause a gradual (inaudible) gain
    reduction rather than an instantaneous step.
  - Unity gain (no limiting) is the steady-state when all signals are
    below the ceiling; the limiter is transparent for quiet passages.
  - _float32_to_bytes in pipeline.py retains its np.clip() as an
    absolute last resort; the limiter prevents the signal from reaching
    that hard boundary during normal operation.

Configure in dsp/config.py:
    OUTPUT_LIMITER_ENABLED = True          # on by default
    OUTPUT_LIMITER_CEILING_DBFS = -1.0     # headroom below digital full-scale
    OUTPUT_LIMITER_ATTACK_S = 0.001        # 1 ms onset
    OUTPUT_LIMITER_RELEASE_S = 0.100       # 100 ms recovery
"""

from __future__ import annotations

import numpy as np


class PeakLimiter:
    """Stateful block-based peak limiter.

    Args:
        ceiling_dbfs: Output ceiling in dBFS (must be ≤ 0.0).
        attack_s:     Time constant for gain reduction onset (seconds).
        release_s:    Time constant for gain recovery (seconds).
        sample_rate:  Audio sample rate in Hz (used to compute IIR coefficients).
    """

    def __init__(
        self,
        ceiling_dbfs: float = -1.0,
        attack_s: float = 0.001,
        release_s: float = 0.100,
        sample_rate: int = 16_000,
    ) -> None:
        if ceiling_dbfs > 0.0:
            raise ValueError(f"ceiling_dbfs must be ≤ 0.0, got {ceiling_dbfs}.")
        if attack_s <= 0:
            raise ValueError(f"attack_s must be positive, got {attack_s}.")
        if release_s <= 0:
            raise ValueError(f"release_s must be positive, got {release_s}.")

        self._ceiling = 10.0 ** (ceiling_dbfs / 20.0)
        # Per-sample IIR time constants used for the block-level envelope.
        self._attack_coeff = float(np.exp(-1.0 / (sample_rate * attack_s)))
        self._release_coeff = float(np.exp(-1.0 / (sample_rate * release_s)))
        self._gain: float = 1.0  # current smoothed gain; 1.0 = no reduction

    def process(self, samples: np.ndarray) -> np.ndarray:
        """Apply peak limiting to *samples*.

        When the block peak is at or below the ceiling the output is
        unchanged (gain == 1.0 in steady state).  When it exceeds the
        ceiling, gain is smoothly reduced so the peak just reaches the
        ceiling, then recovers gradually once the signal falls back.

        Args:
            samples: 1-D float32 normalised PCM array [-1.0, 1.0].

        Returns:
            Peak-limited float32 array of the same shape.
        """
        samples = np.asarray(samples, dtype=np.float32)
        block_peak = float(np.max(np.abs(samples))) if samples.size else 0.0

        if block_peak > 0.0:
            # Target gain: reduce so that block_peak * gain == ceiling.
            # min(1.0, ...) ensures we never amplify below-ceiling signals.
            target_gain = min(1.0, self._ceiling / block_peak)
        else:
            target_gain = 1.0

        # Attack when gain must fall; release when gain is recovering.
        if target_gain < self._gain:
            self._gain = (
                self._attack_coeff * self._gain
                + (1.0 - self._attack_coeff) * target_gain
            )
        else:
            self._gain = (
                self._release_coeff * self._gain
                + (1.0 - self._release_coeff) * target_gain
            )

        return (samples * self._gain).astype(np.float32)

    def reset(self) -> None:
        """Reset limiter state; gain returns to unity (no reduction)."""
        self._gain = 1.0
