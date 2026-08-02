"""
adapt.py – apply an :class:`~accessibility.profiles.AccessProfile` to the
subsystems that already exist.

The profile is data; this module is the only place that turns it into
behaviour, so the adaptation rules are auditable in one file rather than
smeared across the DSP, haptic and voice layers.

Nothing here loosens an existing safety limit.  The two invariants that
matter:

* **An alarm always reaches the wrist.**  Comfort damping is bounded by
  :data:`SAFETY_INTENSITY_FLOOR` for safety-critical classes, so lowering
  ``haptic_intensity_scale`` can never mute a smoke alarm.
* **Adaptation only ever moves within the existing envelopes.**  The
  profile's fields are already clipped on construction; the derived
  values here are clipped again at the point of use.
"""

from __future__ import annotations

from dataclasses import dataclass

from accessibility.profiles import NEUTRAL, AccessProfile
from stream.haptic_policy import (
    SAFETY_PRIORITY,
    PolicyConfig,
    priority_of,
)

#: Lowest intensity byte a safety-critical alert may be damped to.  Chosen
#: to stay clearly above the perceptual floor of a wrist-worn LRA even
#: through a sleeve.  Comfort scaling stops here; it does not continue to
#: zero.
SAFETY_INTENSITY_FLOOR: int = 160

#: Confidence floor is a probability — the adapted value stays inside a
#: usable band no matter what deltas are combined.
_MIN_CONFIDENCE_BOUNDS: tuple[float, float] = (0.1, 0.95)


def policy_config_for(
    profile: AccessProfile | None = None,
    base: PolicyConfig | None = None,
) -> PolicyConfig:
    """Return a :class:`~stream.haptic_policy.PolicyConfig` adapted to *profile*.

    The confidence floor is raised (or lowered) by
    ``profile.min_confidence_delta`` and every refractory window — including
    the fallback — is multiplied by ``profile.haptic_refractory_scale``, so
    alerts are both rarer and better spaced for a user who needs longer to
    orient to each one.

    Args:
        profile: The access profile; ``None`` means
            :data:`~accessibility.profiles.NEUTRAL` (an exact copy of
            *base*).
        base: Configuration to adapt.  Defaults to the stock
            :class:`PolicyConfig`.

    Returns:
        A new :class:`PolicyConfig`; *base* is never mutated.
    """
    profile = profile or NEUTRAL
    base = base or PolicyConfig()

    low, high = _MIN_CONFIDENCE_BOUNDS
    min_confidence = max(low, min(high, base.min_confidence + profile.min_confidence_delta))
    scale = profile.haptic_refractory_scale

    return PolicyConfig(
        min_confidence=min_confidence,
        refractory_ms={key: value * scale for key, value in base.refractory_ms.items()},
        fallback_refractory_ms=base.fallback_refractory_ms * scale,
    )


def scale_intensity(
    intensity: int,
    profile: AccessProfile | None = None,
    *,
    sound_key: str | None = None,
) -> int:
    """Return *intensity* damped for *profile*, never muting safety alerts.

    Args:
        intensity: The audiogram-derived intensity byte (0–255), e.g. from
            :meth:`stream.haptic_mapper.HapticMapper.get_intensity`.
        profile: The access profile; ``None`` means no damping.
        sound_key: The class being driven.  When it is safety-critical
            (:data:`~stream.haptic_policy.SAFETY_PRIORITY`), the result is
            held at or above :data:`SAFETY_INTENSITY_FLOOR` — but only if
            the undamped value was already that high, so a genuinely quiet
            command is never *amplified*.

    Returns:
        The damped intensity byte, clamped to 0–255.
    """
    profile = profile or NEUTRAL
    original = max(0, min(255, int(intensity)))
    damped = int(round(original * profile.haptic_intensity_scale))

    if sound_key is not None and priority_of(sound_key) >= SAFETY_PRIORITY:
        damped = max(damped, min(original, SAFETY_INTENSITY_FLOOR))

    return max(0, min(255, damped))


def voice_match_tolerance_db(
    base_tolerance_db: float,
    profile: AccessProfile | None = None,
) -> float:
    """Return the voice-module match tolerance widened for *profile*.

    Dysarthric speech varies far more between repetitions of the same
    utterance than the default ±3 dB assumes, so scoring it against that
    window reports failure where there is none.
    """
    profile = profile or NEUTRAL
    return float(base_tolerance_db) * profile.voice_tolerance_scale


@dataclass
class InputGate:
    """Hold-to-confirm gate for controls operated with involuntary movement.

    Spasticity, dyskinesia and tremor all make a plain "button down =
    action" control unreliable: a limb brushes the wristband and the user
    has silently toggled a setting, or one intended press registers as
    three.  This gate requires a control to be held continuously for
    ``profile.input_hold_ms`` before it counts, then ignores everything
    for ``profile.input_lockout_ms``.

    Like :class:`~stream.haptic_policy.HapticPolicy` it is pure decision
    logic over a caller-supplied monotonic millisecond clock — no I/O, no
    wall-clock, fully deterministic under test.

    Usage::

        gate = InputGate(CEREBRAL_PALSY)
        gate.update(pressed=True, now_ms=t)   # -> False while held
        ...
        gate.update(pressed=True, now_ms=t + 400)  # -> True (accepted)
    """

    profile: AccessProfile = NEUTRAL
    _press_started_ms: float | None = None
    _accepted_ms: float | None = None
    _armed: bool = True

    def reset(self) -> None:
        """Forget all press history (e.g. when the device reconnects)."""
        self._press_started_ms = None
        self._accepted_ms = None
        self._armed = True

    def update(self, *, pressed: bool, now_ms: float) -> bool:
        """Feed one control sample; return ``True`` when an input is accepted.

        Args:
            pressed: Whether the control is physically active right now.
            now_ms: Monotonic timestamp in milliseconds.

        Returns:
            ``True`` exactly once per accepted input — on the sample where
            the hold requirement is first met — and ``False`` otherwise.
            A press is never accepted twice; the control must be released
            and held again.
        """
        if not pressed:
            self._press_started_ms = None
            self._armed = True
            return False

        if not self._armed:
            return False

        if self._accepted_ms is not None and (
            now_ms - self._accepted_ms < self.profile.input_lockout_ms
        ):
            return False

        if self._press_started_ms is None:
            self._press_started_ms = now_ms

        if now_ms - self._press_started_ms < self.profile.input_hold_ms:
            return False

        self._accepted_ms = now_ms
        self._press_started_ms = None
        self._armed = False
        return True


__all__ = [
    "InputGate",
    "SAFETY_INTENSITY_FLOOR",
    "policy_config_for",
    "scale_intensity",
    "voice_match_tolerance_db",
]
