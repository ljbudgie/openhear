"""
haptic_primitive.py – parametrised haptic primitives for OpenHear v2.

The v1 wristband knows seven hard-coded patterns (voice, doorbell, alarm,
dog, traffic, media, silence).  Those patterns collapse almost everything
that matters about a sound down to "a thing happened, here is its category."

This module introduces a richer vocabulary: four independent axes that can
be composed and continuously modulated to express *who, where, how urgent*
rather than just *what*.

    pulse_rate_hz   — slow throb (0.1 Hz) to rapid buzz (30 Hz)
    intensity       — drive strength, 0–255 (matches the existing packet byte)
    spatial_balance — −1.0 (left only) to +1.0 (right only), 0.0 = centre
    sharpness       — 0.0 (soft, long duty cycle) to 1.0 (sharp click)

Each primitive can be rendered as a timed event schedule (:meth:`to_events`)
for continuous-channel use (crowd arousal, beat tracking, sustained textures)
or collapsed to the closest 3-byte v1 packet (:meth:`to_packet`) for
backward-compatible one-shot firing.

Spatial balance encodes direction today via a simple left/centre/right
zone (routed to the appropriate actuator pattern in v1 firmware).  In a
multi-actuator v2 hardware revision the same axis carries angle-of-arrival
for the full directional use case described in the REGEN_VISION doc.

These primitives are the building blocks; callers assemble them from signals
produced by :mod:`stream.crowd_arousal` (sustained crowd-texture channel) or
the existing :mod:`therapy.entrainment` (isochronic therapeutic rhythm).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from stream.haptic_packet import encode_packet, validate_uint8

# ── Parameter bounds ──────────────────────────────────────────────────────────

#: Slowest meaningful pulse rate.  Below 0.1 Hz the human haptic system stops
#: perceiving it as a rhythm.
PULSE_RATE_MIN_HZ: float = 0.1

#: Fastest haptic pulse rate the wristband actuators can render cleanly.
#: At 30 Hz the mechanical lag of an LRA begins to smear individual pulses.
PULSE_RATE_MAX_HZ: float = 30.0

# ── Well-known v2 reserved sound-class IDs ────────────────────────────────────
#
# These IDs sit above the v1 range (0–6) so firmware can route them separately.
# Firmware that does not recognise them should treat them as a generic alert —
# that is a safe fallback and preserves haptic feedback even on old firmware.

#: sound_class_id for a primitive that drives the *left* actuator zone.
PRIMITIVE_CLASS_LEFT: int = 10

#: sound_class_id for a primitive that drives *both* actuators (centre).
PRIMITIVE_CLASS_CENTRE: int = 11

#: sound_class_id for a primitive that drives the *right* actuator zone.
PRIMITIVE_CLASS_RIGHT: int = 12

# ── Well-known v2 reserved pattern IDs ──────────────────────────────────────

#: Soft pattern — long duty cycle, gradual envelope.
PRIMITIVE_PATTERN_SOFT: int = 10

#: Medium pattern — balanced duty cycle.
PRIMITIVE_PATTERN_MEDIUM: int = 11

#: Sharp pattern — short duty cycle, click-like onset.
PRIMITIVE_PATTERN_SHARP: int = 12

# ── Silence packet ────────────────────────────────────────────────────────────

#: A packet that silences all motors.  Used as the "off" edge in event streams.
SILENCE_PACKET: bytes = encode_packet(0, 0, 0)


# ── Event type ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PrimitiveEvent:
    """One timed on/off edge in a rendered primitive event stream.

    Attributes:
        at_ms: When this edge fires, milliseconds from session start.
        packet: The 3-byte wristband packet to send at this moment.
        kind:   ``"on"`` when the actuator starts, ``"off"`` when it stops.
    """

    at_ms: float
    packet: bytes
    kind: Literal["on", "off"]


# ── Core type ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class HapticPrimitive:
    """A composable, continuously-modulatable haptic expression.

    Attributes:
        pulse_rate_hz:   Rhythm frequency, :data:`PULSE_RATE_MIN_HZ`–
                         :data:`PULSE_RATE_MAX_HZ` Hz.
        intensity:       Drive strength, 0–255.
        spatial_balance: −1.0 (left only) to +1.0 (right only), 0.0 = centre.
        sharpness:       0.0 (soft, gradual envelope) to 1.0 (sharp click).
    """

    pulse_rate_hz: float
    intensity: int
    spatial_balance: float
    sharpness: float

    def __post_init__(self) -> None:
        _validate_range("pulse_rate_hz", self.pulse_rate_hz, PULSE_RATE_MIN_HZ, PULSE_RATE_MAX_HZ)
        validate_uint8("intensity", self.intensity)
        _validate_range("spatial_balance", self.spatial_balance, -1.0, 1.0)
        _validate_range("sharpness", self.sharpness, 0.0, 1.0)

    # ── Derived properties ────────────────────────────────────────────────────

    @property
    def duty_cycle(self) -> float:
        """Pulse-on fraction.

        Sharpness 0.0 → 0.5 (half on, half off — symmetric square wave).
        Sharpness 1.0 → 0.1 (brief click, mostly off).
        """
        return 0.5 - 0.4 * self.sharpness

    @property
    def spatial_zone(self) -> Literal["left", "centre", "right"]:
        """Coarse spatial zone, used for v1 back-compat actuator routing.

        ``left``   — spatial_balance < −0.33
        ``centre`` — −0.33 ≤ spatial_balance ≤ +0.33
        ``right``  — spatial_balance > +0.33
        """
        if self.spatial_balance < -0.33:
            return "left"
        if self.spatial_balance > 0.33:
            return "right"
        return "centre"

    # ── Rendering ─────────────────────────────────────────────────────────────

    def to_packet(self) -> bytes:
        """Collapse this primitive to the closest 3-byte v1 wristband packet.

        The spatial zone selects the sound_class_id (v2 reserved range 10–12)
        and the sharpness selects the pattern_id so firmware can choose the
        waveform that best matches, even without continuous-channel support.
        """
        sound_class_id = _ZONE_CLASS[self.spatial_zone]
        pattern_id = _sharpness_pattern(self.sharpness)
        return encode_packet(sound_class_id, self.intensity, pattern_id)

    def to_events(self, duration_s: float) -> list[PrimitiveEvent]:
        """Render as a timed list of on/off wristband events.

        The resulting schedule drives the wristband at :attr:`pulse_rate_hz`
        for *duration_s* seconds, alternating on/off at :attr:`duty_cycle`.
        All on/off edges are pre-computed so a caller can feed them to a send
        loop without real-time arithmetic.

        Args:
            duration_s: Session length in seconds.  Zero or negative returns
                        an empty list.

        Returns:
            Chronologically ordered list of :class:`PrimitiveEvent`.
        """
        if duration_s <= 0:
            return []
        period_ms = 1000.0 / self.pulse_rate_hz
        on_ms = period_ms * self.duty_cycle
        pkt = self.to_packet()
        events: list[PrimitiveEvent] = []
        t = 0.0
        total_ms = duration_s * 1000.0
        while t < total_ms:
            events.append(PrimitiveEvent(at_ms=t, packet=pkt, kind="on"))
            off_t = min(t + on_ms, total_ms)
            events.append(PrimitiveEvent(at_ms=off_t, packet=SILENCE_PACKET, kind="off"))
            t += period_ms
        return events


# ── Factories: well-known starting points ─────────────────────────────────────


def calm() -> HapticPrimitive:
    """A quiet, slow, centred pulse — gentle ambient texture for a calm crowd."""
    return HapticPrimitive(
        pulse_rate_hz=1.0,
        intensity=60,
        spatial_balance=0.0,
        sharpness=0.1,
    )


def alert() -> HapticPrimitive:
    """A fast, strong, sharp centred burst — high-urgency foreground event."""
    return HapticPrimitive(
        pulse_rate_hz=8.0,
        intensity=200,
        spatial_balance=0.0,
        sharpness=0.9,
    )


def directional(bearing: float, *, intensity: int = 140, rate_hz: float = 3.0) -> HapticPrimitive:
    """Create a spatially-cued primitive for directional awareness.

    The *bearing* maps directly to :attr:`HapticPrimitive.spatial_balance`.
    On v1 hardware with two actuator zones (left/right) this drives the
    closer motor.  On a future multi-actuator band the same axis encodes a
    continuous angle of arrival.

    Args:
        bearing:   Angle of arrival, −1.0 (hard left) to +1.0 (hard right).
        intensity: Drive strength, 0–255.  Default 140 keeps headroom for
                   simultaneous alert signals.
        rate_hz:   Pulse rate, 0.1–30 Hz.  Default 3.0 Hz is noticeable but
                   not intrusive.

    Returns:
        A :class:`HapticPrimitive` whose :attr:`spatial_balance` = *bearing*.
    """
    _validate_range("bearing", bearing, -1.0, 1.0)
    return HapticPrimitive(
        pulse_rate_hz=rate_hz,
        intensity=intensity,
        spatial_balance=bearing,
        sharpness=0.5,
    )


# ── Private helpers ───────────────────────────────────────────────────────────

_ZONE_CLASS: dict[str, int] = {
    "left": PRIMITIVE_CLASS_LEFT,
    "centre": PRIMITIVE_CLASS_CENTRE,
    "right": PRIMITIVE_CLASS_RIGHT,
}


def _validate_range(name: str, value: float, lo: float, hi: float) -> None:
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be in [{lo}, {hi}], got {value!r}.")


def _sharpness_pattern(sharpness: float) -> int:
    """Map sharpness [0, 1] to the closest named pattern id."""
    if sharpness < 0.33:
        return PRIMITIVE_PATTERN_SOFT
    if sharpness < 0.67:
        return PRIMITIVE_PATTERN_MEDIUM
    return PRIMITIVE_PATTERN_SHARP
