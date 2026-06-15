"""
output_safety.py – final output safety limiter for the OpenHear pipeline.

Over-amplification is the single most dangerous failure mode of any hearing
device: a runaway gain stage, an over-aggressive voice boost, or a typo in a
user-edited config can drive a level into the ear that is uncomfortable or
genuinely harmful.  OpenHear already ships a *hardware* maximum-power-output
(MPO) limiter for the sovereign device (a passive zener clamp, see
``hardware/safety/mpo_calculator.py``), but the software streaming path that
feeds a user's own aids had no equivalent ceiling.  This module is that
ceiling.

:class:`OutputSafetyLimiter` is designed to be the **last** stage in the DSP
chain.  Whatever the upstream stages do — compression, voice-clarity boost,
feedback cancellation, an audiogram prescription, or a hand-edited
``dsp/config.py`` — the limiter guarantees that no sample leaving the pipeline
exceeds the configured ceiling.  The guarantee is unconditional: a smooth
attack/release gain envelope keeps the limiting transparent during normal
speech, and a final hard clip enforces the ceiling exactly even while the
envelope is still settling.

Design notes:
  * The ceiling is expressed in **dBFS** (decibels relative to full scale),
    where 0 dBFS is the maximum representable level.  A ceiling of ``-1.0``
    dBFS leaves a little headroom below digital full scale; lower values
    (for example ``-6.0``) provide a deliberately conservative, quieter cap
    for users who want extra protection.
  * Gain reduction is smoothed with separate attack and release time
    constants so the limiter does not pump or click on transients.  The
    attack is fast (the ceiling must be respected promptly) and the release
    is slower (gain recovers gently once the signal drops).
  * The smoothed gain only ever *reduces* level (it never exceeds unity), so
    the limiter can make a signal quieter but never louder — it can only make
    things safer.

Tunable parameters (from ``dsp/config.py``):
  - OUTPUT_SAFETY_LIMITER_ENABLED:  master on/off switch (default on).
  - OUTPUT_SAFETY_MAX_DBFS:         output ceiling in dBFS.
  - OUTPUT_SAFETY_ATTACK_S:         attack time constant (gain reduction).
  - OUTPUT_SAFETY_RELEASE_S:        release time constant (gain recovery).

The limiter also keeps lightweight **activity telemetry** (:class:`LimiterStats`,
exposed via :attr:`OutputSafetyLimiter.stats` and :meth:`OutputSafetyLimiter.summary`):
how many blocks it processed, how many it actually attenuated, and the deepest
attenuation it applied. A safety net that is hit often is a useful signal that
the upstream chain is running too hot, so the pipeline logs a one-line summary
when it stops rather than letting the clamping happen silently.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LimiterStats:
    """Immutable snapshot of the limiter's activity since the last reset.

    The limiter is a safety net, and a net that is hit often is telling you
    something: the upstream chain (or a hand-edited gain) is running hot enough
    to need clamping. Surfacing these numbers keeps that action visible rather
    than silent, so a clinician or user can decide whether to bring the upstream
    level down instead of leaning on the ceiling.

    Attributes:
        blocks_processed: Total number of non-empty blocks seen.
        blocks_limited: Number of blocks whose output was actually attenuated
            (smoothed gain reduction and/or the hard-clip safety net).
        max_gain_reduction_db: Deepest attenuation applied to any single block,
            in dB (``0.0`` means the limiter never engaged). Always ``>= 0``.
    """

    blocks_processed: int
    blocks_limited: int
    max_gain_reduction_db: float

    @property
    def limited_fraction(self) -> float:
        """Fraction of processed blocks that were attenuated (0.0–1.0)."""
        if self.blocks_processed == 0:
            return 0.0
        return self.blocks_limited / self.blocks_processed


class OutputSafetyLimiter:
    """Hard output-level ceiling for the end of the DSP chain.

    The limiter measures the peak level of each block and, if it exceeds the
    configured ceiling, applies a gain reduction so the peak is brought back
    to the ceiling.  The gain is smoothed across blocks with attack/release
    time constants to avoid audible pumping, and a final hard clip guarantees
    the ceiling is never exceeded even mid-transient.

    Args:
        sample_rate: Audio sample rate in Hz (used to convert the attack and
            release times into per-block smoothing coefficients).
        max_output_dbfs: Output ceiling in dBFS.  Must be <= 0.0 (0 dBFS is
            digital full scale).  More negative values are quieter and safer.
        attack_s: Time constant for *reducing* gain when the signal exceeds
            the ceiling.  Shorter = the ceiling is enforced more promptly.
        release_s: Time constant for *recovering* gain once the signal drops
            below the ceiling.  Longer = gentler, less pumping.
    """

    def __init__(
        self,
        sample_rate: int = 16_000,
        max_output_dbfs: float = -1.0,
        attack_s: float = 0.001,
        release_s: float = 0.050,
    ) -> None:
        if sample_rate <= 0:
            raise ValueError(f"sample_rate must be positive, got {sample_rate}")
        if max_output_dbfs > 0.0:
            raise ValueError(
                f"max_output_dbfs must be <= 0.0 dBFS (full scale), " f"got {max_output_dbfs}"
            )
        if attack_s < 0.0 or release_s < 0.0:
            raise ValueError("attack_s and release_s must be non-negative")

        self.sample_rate = sample_rate
        self.max_output_dbfs = max_output_dbfs
        self.attack_s = attack_s
        self.release_s = release_s

        # Linear ceiling corresponding to the dBFS limit.
        self._ceiling_linear = float(10.0 ** (max_output_dbfs / 20.0))

        # Smoothed gain, starts at unity (no reduction).
        self._gain: float = 1.0

        # Activity telemetry (see :class:`LimiterStats`). These only ever
        # accumulate observations about the audio; they never alter it.
        self._blocks_processed: int = 0
        self._blocks_limited: int = 0
        self._max_gain_reduction_db: float = 0.0

    # ------------------------------------------------------------------
    # Public API

    @property
    def ceiling_linear(self) -> float:
        """The linear amplitude ceiling (absolute value samples are capped at)."""
        return self._ceiling_linear

    @property
    def current_gain(self) -> float:
        """The most recent smoothed gain (1.0 = no reduction, < 1.0 = limiting)."""
        return self._gain

    @property
    def stats(self) -> LimiterStats:
        """Snapshot of limiter activity since construction or the last reset."""
        return LimiterStats(
            blocks_processed=self._blocks_processed,
            blocks_limited=self._blocks_limited,
            max_gain_reduction_db=self._max_gain_reduction_db,
        )

    def summary(self) -> str:
        """Human-readable, one-line description of the limiter's activity.

        Intended for an end-of-session log line so the safety net's behaviour
        is visible rather than silent.
        """
        s = self.stats
        ceiling = self.max_output_dbfs
        if s.blocks_processed == 0:
            return f"Output-safety limiter saw no audio (ceiling {ceiling:.1f} dBFS)."
        if s.blocks_limited == 0:
            return (
                "Output-safety limiter never engaged: no block exceeded the "
                f"{ceiling:.1f} dBFS ceiling across {s.blocks_processed} blocks."
            )
        return (
            "Output-safety limiter engaged on "
            f"{s.blocks_limited}/{s.blocks_processed} blocks "
            f"({s.limited_fraction * 100.0:.1f}%); deepest attenuation "
            f"{s.max_gain_reduction_db:.1f} dB (ceiling {ceiling:.1f} dBFS)."
        )

    def process(self, samples: np.ndarray) -> np.ndarray:
        """Apply the output ceiling to a block of samples.

        Args:
            samples: 1-D float32 array of normalised PCM samples.

        Returns:
            float32 array of the same length whose absolute value never
            exceeds :attr:`ceiling_linear`.
        """
        samples = samples.astype(np.float32, copy=False)
        if samples.size == 0:
            return samples

        peak = float(np.max(np.abs(samples)))

        # Target gain needed to bring this block's peak down to the ceiling.
        # If the block is already under the ceiling, the target is unity.
        if peak > self._ceiling_linear:
            target_gain = self._ceiling_linear / peak
        else:
            target_gain = 1.0

        # Smooth the gain toward the target.  Use the fast attack coefficient
        # when reducing gain (target below current) and the slower release
        # coefficient when recovering (target above current).
        block_seconds = samples.size / self.sample_rate
        if target_gain < self._gain:
            alpha = self._smoothing_coefficient(self.attack_s, block_seconds)
        else:
            alpha = self._smoothing_coefficient(self.release_s, block_seconds)
        self._gain += alpha * (target_gain - self._gain)

        # The gain should only ever attenuate, never amplify.
        if self._gain > 1.0:
            self._gain = 1.0

        out = samples * np.float32(self._gain)

        # Hard guarantee: clamp to the ceiling regardless of the smoothed gain
        # state.  This makes the safety bound unconditional even while the
        # attack envelope is still catching up to a sudden transient.
        np.clip(out, -self._ceiling_linear, self._ceiling_linear, out=out)

        # Record activity telemetry from the *effective* attenuation (smoothed
        # gain and hard clip combined), so the readout reflects what actually
        # reached the output rather than just the envelope state.  This never
        # alters the audio; it only observes it.
        self._blocks_processed += 1
        if peak > 0.0:
            out_peak = float(np.max(np.abs(out)))
            if out_peak < peak:
                reduction_db = -20.0 * math.log10(out_peak / peak) if out_peak > 0.0 else math.inf
                self._blocks_limited += 1
                if reduction_db > self._max_gain_reduction_db:
                    self._max_gain_reduction_db = reduction_db

        return out

    def reset(self) -> None:
        """Reset the smoothed gain back to unity and clear activity telemetry."""
        self._gain = 1.0
        self._blocks_processed = 0
        self._blocks_limited = 0
        self._max_gain_reduction_db = 0.0

    # ------------------------------------------------------------------
    # Internal helpers

    @staticmethod
    def _smoothing_coefficient(time_constant_s: float, block_seconds: float) -> float:
        """One-pole smoothing coefficient for a given time constant.

        A ``time_constant_s`` of 0 yields an instantaneous coefficient (1.0),
        meaning the gain jumps straight to the target.  Larger time constants
        yield smaller coefficients and therefore gentler smoothing.
        """
        if time_constant_s <= 0.0:
            return 1.0
        return 1.0 - math.exp(-block_seconds / time_constant_s)
