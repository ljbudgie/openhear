"""
profile_delta.py – bounded, composable DSP parameter deltas.

A :class:`ProfileDelta` is a small, additive bias applied on top of a base
DSP configuration (typically derived from an audiogram prescription).  It
is shared by two roadmap features:

* **S1 — Per-contact DSP profile bank** (``dsp/contact_profiles.py``):
  a delta describes how a chosen contact's voice should be processed
  relative to the user's generic profile.
* **S3 — Fatigue-aware DSP** (``dsp/fatigue.py``): a delta describes how
  the pipeline should soften compression and ease off noise reduction
  when the user's recovery is low.

Every delta is **bounded**, **deterministic**, and **explainable**:

* All numeric fields are clipped to safe limits on construction
  (:data:`MAX_COMPRESSION_RATIO_DELTA`, :data:`MAX_COMPRESSION_KNEE_DELTA_DB`,
  :data:`MAX_VOICE_GAIN_DELTA`, :data:`MAX_NR_AGGRESSIVENESS_DELTA`).
* Composition via :meth:`ProfileDelta.combine` sums fields and clips again
  so cumulative bias from multiple sources (e.g. contact + fatigue) can
  never exceed the same safe envelope.
* A short ``reason`` string travels with the delta and surfaces in
  pipeline explanations, so the user can always answer "why did the DSP
  change?".

Sovereignty & safety notes:
    * No I/O is performed in this module; all state is in-memory.
    * Limits are kept conservative on purpose — a delta is a nudge, not a
      replacement for the base prescription.
    * The dataclass is frozen so deltas are safe to share between threads
      and cannot be mutated after they are explained to the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

#: Maximum absolute change to the WDRC compression ratio (linear).
#: A delta of ±0.5 corresponds to roughly "one half-step" of compressor
#: aggressiveness — enough to soften or sharpen perceived loudness without
#: leaving the safe envelope.
MAX_COMPRESSION_RATIO_DELTA: float = 0.5

#: Maximum absolute change to the WDRC knee point (dB).
#: ±6 dB shifts the knee about one perceptual "step" softer or louder.
MAX_COMPRESSION_KNEE_DELTA_DB: float = 6.0

#: Maximum absolute change to the speech-band voice-clarity gain
#: (linear multiplier).  ±0.4 is roughly ±3 dB at the band centre.
MAX_VOICE_GAIN_DELTA: float = 0.4

#: Maximum absolute change to noise-reduction aggressiveness (unitless,
#: scales the over-subtraction multiplier).  ±0.3 keeps the spectral
#: subtractor inside its musical-noise-free range.
MAX_NR_AGGRESSIVENESS_DELTA: float = 0.3


def _clip(value: float, limit: float) -> float:
    """Symmetrically clip ``value`` to the closed interval ``[-limit, limit]``.

    Args:
        value: The value to clip.
        limit: Positive symmetric limit.

    Returns:
        ``value`` clipped to ``[-limit, limit]``.
    """
    if limit < 0:
        raise ValueError(f"limit must be non-negative, got {limit}")
    if value > limit:
        return limit
    if value < -limit:
        return -limit
    return float(value)


@dataclass(frozen=True)
class ProfileDelta:
    """A bounded, additive bias on top of a base DSP profile.

    All fields default to ``0.0`` (i.e. "no change"), and all are clipped
    to the module-level ``MAX_*`` constants on construction.

    Attributes:
        compression_ratio_delta: Added to the compressor ratio.  Negative
            values soften compression (closer to linear); positive values
            make it more aggressive.  Clipped to
            ``±MAX_COMPRESSION_RATIO_DELTA``.
        compression_knee_delta_db: Added to the compressor knee (dBFS).
            Negative values lower the knee (compression engages earlier);
            positive values raise it.  Clipped to
            ``±MAX_COMPRESSION_KNEE_DELTA_DB``.
        voice_gain_delta: Added to the voice-clarity gain (linear).
            Clipped to ``±MAX_VOICE_GAIN_DELTA``.
        nr_aggressiveness_delta: Added to the noise-reduction
            over-subtraction multiplier (``alpha``).  Negative values
            make NR gentler; positive values make it more aggressive.
            Clipped to ``±MAX_NR_AGGRESSIVENESS_DELTA``.
        sources: Tuple of short tags (e.g. ``"contact:partner"``,
            ``"fatigue:yellow"``) describing where this delta came from.
            Used by the explainer to show the user every contributor.
        reason: One-line human-readable explanation.  Empty for the
            identity delta.
    """

    compression_ratio_delta: float = 0.0
    compression_knee_delta_db: float = 0.0
    voice_gain_delta: float = 0.0
    nr_aggressiveness_delta: float = 0.0
    sources: tuple[str, ...] = field(default_factory=tuple)
    reason: str = ""

    def __post_init__(self) -> None:  # noqa: D401 — frozen dataclass hook
        # ``frozen=True`` forbids attribute assignment, so go via
        # ``object.__setattr__`` to apply clipping.
        object.__setattr__(
            self,
            "compression_ratio_delta",
            _clip(self.compression_ratio_delta, MAX_COMPRESSION_RATIO_DELTA),
        )
        object.__setattr__(
            self,
            "compression_knee_delta_db",
            _clip(self.compression_knee_delta_db, MAX_COMPRESSION_KNEE_DELTA_DB),
        )
        object.__setattr__(
            self,
            "voice_gain_delta",
            _clip(self.voice_gain_delta, MAX_VOICE_GAIN_DELTA),
        )
        object.__setattr__(
            self,
            "nr_aggressiveness_delta",
            _clip(self.nr_aggressiveness_delta, MAX_NR_AGGRESSIVENESS_DELTA),
        )
        # Normalise ``sources`` to a tuple of strings.
        object.__setattr__(self, "sources", tuple(str(s) for s in self.sources))

    # ── Combination ──────────────────────────────────────────────────────

    def combine(self, other: "ProfileDelta") -> "ProfileDelta":
        """Return the sum of two deltas, re-clipped to the safe envelope.

        Sources are concatenated and reasons joined with ``" + "``.

        Args:
            other: The delta to add to ``self``.

        Returns:
            A new :class:`ProfileDelta`.
        """
        new_reason = " + ".join(r for r in (self.reason, other.reason) if r)
        return ProfileDelta(
            compression_ratio_delta=self.compression_ratio_delta + other.compression_ratio_delta,
            compression_knee_delta_db=self.compression_knee_delta_db
            + other.compression_knee_delta_db,
            voice_gain_delta=self.voice_gain_delta + other.voice_gain_delta,
            nr_aggressiveness_delta=self.nr_aggressiveness_delta + other.nr_aggressiveness_delta,
            sources=self.sources + other.sources,
            reason=new_reason,
        )

    @classmethod
    def compose(cls, deltas: Iterable["ProfileDelta"]) -> "ProfileDelta":
        """Combine an iterable of deltas in order.

        Empty iterables return the identity (no-change) delta.
        """
        result = cls()
        for delta in deltas:
            result = result.combine(delta)
        return result

    # ── Application ──────────────────────────────────────────────────────

    def apply_to_compression(self, *, ratio: float, knee_dbfs: float) -> tuple[float, float]:
        """Return ``(ratio, knee_dbfs)`` with this delta applied.

        The ratio is floored at ``1.0`` (linear); the knee is left at
        whatever the calling pipeline decided after the addition.  No
        further clipping is performed here — call sites that need
        additional limits should apply them themselves.
        """
        new_ratio = max(1.0, ratio + self.compression_ratio_delta)
        new_knee = knee_dbfs + self.compression_knee_delta_db
        return new_ratio, new_knee

    def apply_to_voice_gain(self, gain: float) -> float:
        """Return the voice-clarity gain with this delta applied.

        The result is floored at ``0.0`` (no negative gain).
        """
        return max(0.0, gain + self.voice_gain_delta)

    def apply_to_nr_alpha(self, alpha: float) -> float:
        """Return the noise-reduction over-subtraction multiplier.

        The result is floored at ``1.0`` (no under-subtraction below the
        estimated noise floor), consistent with the contract documented
        in :class:`dsp.noise_reduction.SpectralSubtractor`.
        """
        return max(1.0, alpha + self.nr_aggressiveness_delta)

    # ── Convenience ──────────────────────────────────────────────────────

    def is_identity(self) -> bool:
        """``True`` if this delta makes no change to any DSP parameter."""
        return (
            self.compression_ratio_delta == 0.0
            and self.compression_knee_delta_db == 0.0
            and self.voice_gain_delta == 0.0
            and self.nr_aggressiveness_delta == 0.0
        )

    def with_source(self, source: str) -> "ProfileDelta":
        """Return a copy with ``source`` appended to :attr:`sources`."""
        return replace(self, sources=self.sources + (str(source),))

    def explain(self) -> str:
        """One-line explanation suitable for logs and the explain CLI."""
        if self.is_identity():
            return "no DSP delta applied"
        bits: list[str] = []
        if self.compression_ratio_delta:
            bits.append(f"comp ratio {self.compression_ratio_delta:+.2f}")
        if self.compression_knee_delta_db:
            bits.append(f"comp knee {self.compression_knee_delta_db:+.1f} dB")
        if self.voice_gain_delta:
            bits.append(f"voice gain {self.voice_gain_delta:+.2f}")
        if self.nr_aggressiveness_delta:
            bits.append(f"NR alpha {self.nr_aggressiveness_delta:+.2f}")
        sources = ",".join(self.sources) if self.sources else "unspecified"
        reason = f" ({self.reason})" if self.reason else ""
        return f"DSP delta [{sources}]: " + ", ".join(bits) + reason
