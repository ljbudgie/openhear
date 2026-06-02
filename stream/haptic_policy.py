"""
haptic_policy.py – the decision layer between "a sound was classified" and
"buzz the wrist".

The classifier (:mod:`stream.sound_classifier`) turns audio into a single
:class:`~stream.sound_classifier.ClassifiedSound`, and the mapper
(:mod:`stream.haptic_mapper`) turns a sound class into wristband packet
fields.  Between them sits a judgement nothing in the repo made yet:

    *Should this detection reach the wrist at all — and if several compete,
    which one wins?*

Get that wrong and the wristband becomes noise: it fires on every uncertain
guess, machine-guns the same doorbell ten times a second, and lets ambient
media drown out a smoke alarm.  Alert fatigue is what makes people stop
wearing assistive haptics, so this layer is where the device earns trust.

The policy applies three rules, in order:

1. **Actionability** — silence (and any non-mapped class) never fires.
2. **Confidence gate** — a detection below the confidence floor is held
   back rather than risk a false buzz.
3. **Per-class refractory** — once a class fires, it stays quiet for a
   short window so a single event is one clear signal, not a burst.

Each class also carries a **priority** (a smoke alarm outranks the TV) so
the UI and firmware can format urgency and so callers can rank competing
detections.

The policy is pure decision logic over a monotonic millisecond clock
supplied by the caller — no audio, no I/O, no wall-clock — so every path
is deterministic and unit-testable.  Encoding the winning decision into
the wire packet is a separate, optional step (:func:`packet_for`) that
reuses the shared :mod:`stream.haptic_packet` codec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from stream.haptic_packet import encode_packet

if TYPE_CHECKING:  # avoid importing the numpy-backed classifier at runtime
    from stream.sound_classifier import ClassifiedSound

# ── Priority + timing defaults ──────────────────────────────────────────────
#
# Priority is a pure ranking: higher means more important to surface. Safety
# signals sit at the top, ambient media at the bottom. Silence is 0 (never
# actionable).
PRIORITY: dict[str, int] = {
    "silence": 0,
    "media": 20,
    "traffic": 30,
    "dog": 40,
    "voice": 60,
    "doorbell": 70,
    "alarm": 100,
}

#: Priority at/above which a sound is treated as safety-critical.
SAFETY_PRIORITY: int = 100

# How long (ms) a class stays quiet after firing. Urgent signals repeat
# sooner (a smoke alarm should keep reminding you); ambient ones back off so
# they never dominate the wrist.
_DEFAULT_REFRACTORY_MS: dict[str, float] = {
    "alarm": 800.0,
    "doorbell": 1200.0,
    "voice": 1000.0,
    "dog": 1500.0,
    "traffic": 2000.0,
    "media": 3000.0,
}

_FALLBACK_REFRACTORY_MS: float = 1500.0


def priority_of(sound_key: str) -> int:
    """Return the surfacing priority for *sound_key* (unknown → 0)."""
    return PRIORITY.get(sound_key, 0)


@dataclass(frozen=True)
class PolicyConfig:
    """Tunable thresholds for :class:`HapticPolicy`.

    Attributes:
        min_confidence: Detections below this confidence are suppressed.
        refractory_ms: Per-class quiet window after a fire.  Missing
            classes fall back to ``fallback_refractory_ms``.
        fallback_refractory_ms: Refractory used for classes not listed.
    """

    min_confidence: float = 0.6
    refractory_ms: dict[str, float] = field(
        default_factory=lambda: dict(_DEFAULT_REFRACTORY_MS)
    )
    fallback_refractory_ms: float = _FALLBACK_REFRACTORY_MS

    def refractory_for(self, sound_key: str) -> float:
        """Return the refractory window (ms) for *sound_key*."""
        return self.refractory_ms.get(sound_key, self.fallback_refractory_ms)


@dataclass(frozen=True)
class PolicyDecision:
    """The outcome of evaluating one classified sound.

    Attributes:
        sound_key: The class considered.
        should_fire: Whether the wrist should be driven.
        priority: Surfacing priority of the class.
        confidence: The detection confidence considered.
        reason: Machine-readable explanation — ``"fire"``,
            ``"not_actionable"``, ``"low_confidence"`` or ``"refractory"``.
    """

    sound_key: str
    should_fire: bool
    priority: int
    confidence: float
    reason: str

    @property
    def is_safety(self) -> bool:
        """Whether this is a safety-critical class (e.g. an alarm)."""
        return self.priority >= SAFETY_PRIORITY


class HapticPolicy:
    """Stateful decision layer turning a detection stream into wrist events.

    A single instance is fed successive detections via :meth:`decide`,
    each with a monotonic millisecond timestamp.  It remembers when each
    class last fired so it can enforce the refractory windows.
    """

    def __init__(self, config: PolicyConfig | None = None) -> None:
        self.config = config or PolicyConfig()
        self._last_fire_ms: dict[str, float] = {}

    def reset(self) -> None:
        """Forget all firing history (e.g. when the stream restarts)."""
        self._last_fire_ms.clear()

    def decide(self, classified: "ClassifiedSound", now_ms: float) -> PolicyDecision:
        """Decide whether *classified* should drive the wrist at *now_ms*.

        Args:
            classified: The latest classified sound (needs ``sound_key``
                and ``confidence`` attributes).
            now_ms: Monotonic timestamp in milliseconds.

        Returns:
            A :class:`PolicyDecision`.  When it fires, the firing time is
            recorded so the refractory window applies to later calls.
        """
        key = classified.sound_key
        confidence = float(classified.confidence)
        priority = priority_of(key)

        def decision(should_fire: bool, reason: str) -> PolicyDecision:
            return PolicyDecision(
                sound_key=key,
                should_fire=should_fire,
                priority=priority,
                confidence=confidence,
                reason=reason,
            )

        if priority <= 0:
            return decision(False, "not_actionable")

        if confidence < self.config.min_confidence:
            return decision(False, "low_confidence")

        last = self._last_fire_ms.get(key)
        if last is not None and now_ms - last < self.config.refractory_for(key):
            return decision(False, "refractory")

        self._last_fire_ms[key] = now_ms
        return decision(True, "fire")


# Signature of haptic_mapper.build_command / HapticMapper.build_command:
# (sound_key, *, confidence) -> (sound_class_id, intensity, pattern_id).
BuildCommand = Callable[..., "tuple[int, int, int]"]


def packet_for(decision: PolicyDecision, build_command: BuildCommand) -> bytes | None:
    """Encode the wristband packet for a *firing* decision, else ``None``.

    Bridges policy → mapper → wire codec: when ``decision.should_fire`` is
    true, ``build_command`` (e.g. :meth:`HapticMapper.build_command`)
    produces the ``(sound_class_id, intensity, pattern_id)`` triple and it
    is encoded with :func:`stream.haptic_packet.encode_packet`.

    Args:
        decision: The result of :meth:`HapticPolicy.decide`.
        build_command: Callable mapping ``(sound_key, confidence=…)`` to the
            three packet fields.

    Returns:
        The 3-byte packet, or ``None`` when the decision does not fire.
    """
    if not decision.should_fire:
        return None
    fields = build_command(decision.sound_key, confidence=decision.confidence)
    return encode_packet(*fields)
