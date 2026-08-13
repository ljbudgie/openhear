"""
profiles.py – access profiles for users whose bodies, not just their ears,
shape how OpenHear should behave.

OpenHear's DSP and haptic layers are tuned from an *audiogram*: what the
user can hear.  That is only half the story for a large part of the
audience.  Cerebral palsy, for example, frequently co-occurs with hearing
loss, and the same person may also live with spasticity, dyskinesia,
tactile hypersensitivity, an exaggerated startle response and dysarthric
speech.  For them the wristband is worn on a limb with fluctuating tone,
the controls can be triggered by an involuntary movement, and a sudden
hard buzz is not merely unpleasant — it can provoke a spasm.

An :class:`AccessProfile` captures those *motor and sensory* access needs
as a handful of bounded numbers, so every subsystem can adapt from one
declared source of truth instead of scattering condition-specific special
cases through the codebase.

Design rules (deliberately the same ones the rest of OpenHear follows):

* **Bounded, always.**  Every field is clipped into a safe range on
  construction, so a hand-edited or malformed profile can never push the
  wristband harder, quieter, or slower than the envelope allows.
* **Never silences safety.**  Damping is capped so an alarm always stays
  perceptible; see :func:`accessibility.adapt.scale_intensity`.
* **A profile is a default, not a diagnosis.**  No two people with the
  same condition need the same settings.  Profiles are starting points
  the user overrides with :meth:`AccessProfile.replace`, and nothing here
  is stored, inferred, or transmitted — the user declares it or it does
  not exist.
* **Screening prompts, not assumptions.**  Conditions that *often*
  co-occur (e.g. epilepsy with cerebral palsy) are surfaced as prompts
  for the user to answer, never asserted on their behalf.  What the user
  answers is what reaches :meth:`therapy.protocol.TherapeuticProtocol.gate`.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

# ── Safe envelopes ──────────────────────────────────────────────────────────
#
# (minimum, maximum) for each tunable.  Values are clipped to these on
# construction; they are the only guarantor that a profile — however it was
# authored — stays inside the safe operating range.
HAPTIC_INTENSITY_SCALE_RANGE: tuple[float, float] = (0.35, 1.0)
HAPTIC_RAMP_MS_RANGE: tuple[float, float] = (0.0, 500.0)
HAPTIC_REFRACTORY_SCALE_RANGE: tuple[float, float] = (1.0, 4.0)
MIN_CONFIDENCE_DELTA_RANGE: tuple[float, float] = (-0.2, 0.2)
INPUT_HOLD_MS_RANGE: tuple[float, float] = (0.0, 2000.0)
INPUT_LOCKOUT_MS_RANGE: tuple[float, float] = (0.0, 5000.0)
VOICE_TOLERANCE_SCALE_RANGE: tuple[float, float] = (1.0, 3.0)


def _clip(value: float, bounds: tuple[float, float]) -> float:
    """Return *value* clipped into ``bounds``."""
    low, high = bounds
    return max(low, min(high, float(value)))


@dataclass(frozen=True)
class AccessProfile:
    """Motor and sensory access needs, expressed as bounded adjustments.

    Attributes:
        key: Stable identifier (e.g. ``"cerebral_palsy"``).
        label: Human-readable name shown in UIs.
        summary: One-line description of who the profile is for.
        haptic_intensity_scale: Multiplier applied to the wristband
            intensity byte.  Below 1.0 for users whose threshold for
            discomfort — or for triggering a spasm or a startle — is
            lower than the drive level an audiogram alone would pick.
        haptic_ramp_ms: Minimum onset ramp, in milliseconds, that the
            driver or firmware should use instead of a hard step.  A
            gradual rise is far less likely to provoke a startle response
            or an involuntary movement than an instant full-amplitude buzz.
        haptic_refractory_scale: Multiplier on the per-class refractory
            windows in :mod:`stream.haptic_policy`.  Above 1.0 spaces
            alerts out for users who need longer to orient to, and act
            on, each one.
        min_confidence_delta: Added to the policy confidence floor.
            Positive values trade a few missed detections for markedly
            fewer false buzzes — worth it when every buzz costs effort.
        input_hold_ms: How long a control must be held before it counts,
            so tremor, dyskinesia or an unintended brush does not toggle
            anything.
        input_lockout_ms: Quiet window after an accepted input during
            which repeats are ignored, so one intended press is not read
            as several.
        voice_tolerance_scale: Multiplier on the voice-module match
            tolerance (:data:`voice.config.MATCH_TOLERANCE_DB`).  Above
            1.0 for dysarthric speech, where the natural variability
            between repetitions of the same utterance is much wider than
            the default ±3 dB assumes.
        screening_prompts: Questions a UI should ask before running
            anything gated — never answers.  See the module docstring.
        notes: Free-text rationale, surfaced by CLIs and docs.
    """

    key: str
    label: str = ""
    summary: str = ""
    haptic_intensity_scale: float = 1.0
    haptic_ramp_ms: float = 0.0
    haptic_refractory_scale: float = 1.0
    min_confidence_delta: float = 0.0
    input_hold_ms: float = 0.0
    input_lockout_ms: float = 0.0
    voice_tolerance_scale: float = 1.0
    screening_prompts: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        key = str(self.key).strip().lower().replace(" ", "_").replace("-", "_")
        if not key:
            raise ValueError("An access profile needs a non-empty key.")
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "label", self.label or key.replace("_", " ").capitalize())

        for name, bounds in (
            ("haptic_intensity_scale", HAPTIC_INTENSITY_SCALE_RANGE),
            ("haptic_ramp_ms", HAPTIC_RAMP_MS_RANGE),
            ("haptic_refractory_scale", HAPTIC_REFRACTORY_SCALE_RANGE),
            ("min_confidence_delta", MIN_CONFIDENCE_DELTA_RANGE),
            ("input_hold_ms", INPUT_HOLD_MS_RANGE),
            ("input_lockout_ms", INPUT_LOCKOUT_MS_RANGE),
            ("voice_tolerance_scale", VOICE_TOLERANCE_SCALE_RANGE),
        ):
            object.__setattr__(self, name, _clip(getattr(self, name), bounds))

        object.__setattr__(self, "screening_prompts", tuple(self.screening_prompts))
        object.__setattr__(self, "notes", tuple(self.notes))

    def replace(self, **overrides: Any) -> "AccessProfile":
        """Return a copy with *overrides* applied and re-clipped.

        This is how a user personalises a bundled profile: the registry
        entry is a starting point, never a prescription.
        """
        return replace(self, **overrides)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict of this profile."""
        return {
            "key": self.key,
            "label": self.label,
            "summary": self.summary,
            "haptic_intensity_scale": self.haptic_intensity_scale,
            "haptic_ramp_ms": self.haptic_ramp_ms,
            "haptic_refractory_scale": self.haptic_refractory_scale,
            "min_confidence_delta": self.min_confidence_delta,
            "input_hold_ms": self.input_hold_ms,
            "input_lockout_ms": self.input_lockout_ms,
            "voice_tolerance_scale": self.voice_tolerance_scale,
            "screening_prompts": list(self.screening_prompts),
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AccessProfile":
        """Build a profile from *payload*, ignoring unknown keys.

        Unknown keys are dropped rather than raising, so a profile written
        by a newer OpenHear can still be read by an older one — with the
        fields it does not understand left at their defaults.

        Raises:
            ValueError: If *payload* has no ``key``.
        """
        if "key" not in payload:
            raise ValueError("An access profile payload needs a 'key'.")
        known = {name for name in cls.__dataclass_fields__ if name != "key"}
        kwargs = {name: value for name, value in payload.items() if name in known}
        for seq in ("screening_prompts", "notes"):
            if seq in kwargs:
                kwargs[seq] = tuple(kwargs[seq])
        return cls(key=payload["key"], **kwargs)


#: The identity profile — no adjustments.  Used when nothing is declared,
#: so callers can treat "no profile" and "a profile" uniformly.
NEUTRAL = AccessProfile(
    key="neutral",
    label="Neutral",
    summary="No motor or sensory adjustments declared.",
)


#: Cerebral palsy — the reason this module exists.
#:
#: Hearing loss is common in cerebral palsy, so a substantial share of
#: OpenHear's audience is navigating both at once, and an audiogram-only
#: fit serves them badly.  The defaults below are conservative starting
#: points, chosen from the access needs that most often collide with a
#: wrist-worn haptic system:
#:
#:   * spasticity / dyskinesia — an abrupt, hard buzz on a limb with
#:     fluctuating tone can provoke an involuntary movement, so intensity
#:     is damped and onset is ramped rather than stepped;
#:   * startle response — a raised confidence floor means far fewer
#:     false alerts;
#:   * orienting and acting take longer — refractory windows are spaced
#:     out so alerts do not stack up;
#:   * involuntary movement at the controls — a hold-to-confirm dwell and
#:     a repeat lockout stop a brush or a tremor from toggling settings;
#:   * dysarthria — the voice module's match tolerance is widened so
#:     ordinary variability is not scored as failure.
CEREBRAL_PALSY = AccessProfile(
    key="cerebral_palsy",
    label="Cerebral palsy",
    summary=(
        "Damped, ramped haptics, longer alert spacing, hold-to-confirm input "
        "and dysarthria-tolerant voice scoring."
    ),
    haptic_intensity_scale=0.7,
    haptic_ramp_ms=120.0,
    haptic_refractory_scale=1.6,
    min_confidence_delta=0.1,
    input_hold_ms=400.0,
    input_lockout_ms=800.0,
    voice_tolerance_scale=2.0,
    screening_prompts=(
        "Do you have epilepsy or any seizure disorder? Entrainment protocols "
        "in therapy/ are gated on your answer and will refuse to run.",
        "Which limb wears the wristband, and does its muscle tone vary through "
        "the day? Re-check comfort intensity when it does.",
        "Does vibration ever trigger discomfort, spasm or startle for you? "
        "Lower haptic_intensity_scale until it does not.",
    ),
    notes=(
        "A starting point, not a prescription — tune every value with the user.",
        "Damping never drops a safety-critical alert below the floor enforced in "
        "accessibility.adapt.scale_intensity; an alarm stays perceptible.",
        "Cerebral palsy does not imply epilepsy; it is screened for, never assumed.",
    ),
)


#: Autism — an opt-in sensory starting point, not a statement about any
#: individual autistic person.  Sensory preferences vary substantially, so
#: these settings privilege fewer, gentler, more predictable alerts and are
#: intended to be personalised or declined.
AUTISM = AccessProfile(
    key="autism",
    label="Autism",
    summary=(
        "Gentler, ramped haptics with fewer low-confidence alerts and "
        "hold-to-confirm input."
    ),
    haptic_intensity_scale=0.65,
    haptic_ramp_ms=180.0,
    haptic_refractory_scale=1.75,
    min_confidence_delta=0.1,
    input_hold_ms=250.0,
    input_lockout_ms=600.0,
    screening_prompts=(
        "Would gentler vibration, fewer alerts, or a slower onset make cues more "
        "comfortable? Adjust or disable any setting that does not.",
        "Are there sounds, vibration patterns, or contexts you prefer not to be "
        "alerted to? Configure those preferences explicitly.",
        "Do you have epilepsy or any seizure disorder? Entrainment protocols in "
        "therapy/ are gated on your answer and will refuse to run.",
    ),
    notes=(
        "Autism does not imply a particular sensory profile; this is an opt-in "
        "starting point, not a diagnostic or behavioural inference.",
        "Tune with the user and retain only settings they choose to declare.",
    ),
)


#: Sensory-processing differences — an opt-in alternative for people whose
#: haptic comfort needs do not map to a diagnosis, or who prefer this starting
#: point over another bundled profile.
SENSORY_PROCESSING = AccessProfile(
    key="sensory_processing",
    label="Sensory processing",
    summary=(
        "Gentler, ramped haptics with wider alert spacing and "
        "hold-to-confirm input."
    ),
    haptic_intensity_scale=0.6,
    haptic_ramp_ms=200.0,
    haptic_refractory_scale=1.8,
    min_confidence_delta=0.1,
    input_hold_ms=150.0,
    input_lockout_ms=500.0,
    screening_prompts=(
        "Would gentler vibration, fewer alerts, or a slower onset make cues more "
        "comfortable? Adjust or disable any setting that does not.",
        "Which alerts are useful enough to keep, and which should be quieter or "
        "less frequent?",
        "Do you have epilepsy or any seizure disorder? Entrainment protocols in "
        "therapy/ are gated on your answer and will refuse to run.",
    ),
    notes=(
        "Sensory-processing needs are user-declared and can change by context; "
        "this profile is not a diagnosis.",
        "Tune with the user and retain only settings they choose to declare.",
    ),
)


#: Bundled access profiles, keyed by :attr:`AccessProfile.key`.
ACCESS_PROFILES: dict[str, AccessProfile] = {
    profile.key: profile
    for profile in (NEUTRAL, CEREBRAL_PALSY, AUTISM, SENSORY_PROCESSING)
}


def get_access_profile(key: str | None) -> AccessProfile:
    """Return a bundled profile by *key* (``None`` → :data:`NEUTRAL`).

    Raises:
        KeyError: If *key* is not a bundled profile.
    """
    if key is None:
        return NEUTRAL
    normalised = str(key).strip().lower().replace(" ", "_").replace("-", "_")
    try:
        return ACCESS_PROFILES[normalised]
    except KeyError as exc:
        raise KeyError(
            f"Unknown access profile {key!r}. Available: {', '.join(sorted(ACCESS_PROFILES))}."
        ) from exc


__all__ = [
    "AccessProfile",
    "ACCESS_PROFILES",
    "AUTISM",
    "CEREBRAL_PALSY",
    "NEUTRAL",
    "SENSORY_PROCESSING",
    "get_access_profile",
]
