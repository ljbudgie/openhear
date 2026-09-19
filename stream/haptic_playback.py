"""Deterministic, phase-preserving arbitration of texture and alert primitives.

This renderer performs no I/O and never reads a wall clock. Supply milliseconds
from one monotonic clock to every call. Setters update state only; call ``poll``
immediately afterwards for prompt output, and send its returned packets in order.
All writes to the shared haptic channel must pass exclusively through this
renderer and one serialized transport writer: separate texture/off writers would
bypass alert priority. Use firmware that supports these packets and interruptible
playback. Host-side arbitration cannot guarantee physical alert preemption on
legacy firmware that blocks while playing a pattern.

Poll more frequently than the shortest on/off pulse (about 3.3 ms at the
primitive's fastest, sharpest setting). Late polls produce only the current
packet change, never a backlog of obsolete edges. This is not a real-time or
hardware-delivery guarantee. Firmware support, actuator response, transport
latency and perceptual thresholds require calibration on the actual hardware.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real

from stream.haptic_primitive import SILENCE_PACKET, HapticPrimitive, PrimitiveEvent


def _number(name: str, value: float, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    try:
        value = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        bound = "positive" if positive else "nonnegative"
        raise ValueError(f"{name} must be finite and {bound}")
    return value


def _phase(phase: float, elapsed_ms: float, primitive: HapticPrimitive) -> float:
    period_ms = 1000.0 / primitive.pulse_rate_hz
    # Reduce elapsed time first to avoid overflowing on a large clock jump.
    result = (phase + (elapsed_ms % period_ms) / period_ms) % 1.0
    # Repeated fractional updates can land just below an exact cycle boundary.
    return 0.0 if math.isclose(result, 1.0, rel_tol=0.0, abs_tol=1e-12) else result


def _packet(primitive: HapticPrimitive | None, phase: float) -> bytes:
    if primitive is None or primitive.intensity == 0:
        return SILENCE_PACKET
    if phase >= primitive.duty_cycle or math.isclose(
        phase, primitive.duty_cycle, rel_tol=0.0, abs_tol=1e-12
    ):
        return SILENCE_PACKET
    return primitive.to_packet()


@dataclass(frozen=True)
class _Alert:
    primitive: HapticPrimitive
    started_ms: float
    duration_ms: float


class HapticPlayback:
    """Render one texture beneath bounded, explicitly prioritised alerts.

    Texture updates retain fractional phase and integrate elapsed time at the
    *previous* rate. Alerts suppress the entire texture, including its off edges;
    the texture clock continues underneath them. Alert phases and lifetimes also
    continue while preempted, so expiry resumes the current state, not old edges.

    Higher positive numeric priorities win. A new alert replaces/restarts an
    existing alert at the same priority. At most ``MAX_ALERTS`` distinct priorities
    are retained; when full, only an alert stronger than the weakest is admitted,
    evicting that weakest alert. Evicted/replaced alerts never resume.

    Every call validates before mutating state. Times must be finite,
    nonnegative and nondecreasing across *all* calls, including after ``stop``.
    """

    MAX_ALERTS = 16

    def __init__(self) -> None:
        self._now_ms: float | None = None
        self._texture: HapticPrimitive | None = None
        self._texture_phase = 0.0
        self._alerts: dict[float, _Alert] = {}
        self._last_packet: bytes | None = None

    def _time(self, now_ms: float) -> float:
        now_ms = _number("now_ms", now_ms)
        if self._now_ms is not None and now_ms < self._now_ms:
            raise ValueError("now_ms must be monotonic (nondecreasing)")
        return now_ms

    def _advance(self, now_ms: float) -> None:
        if self._texture is not None and self._now_ms is not None:
            self._texture_phase = _phase(
                self._texture_phase, now_ms - self._now_ms, self._texture
            )
        self._alerts = {
            priority: alert
            for priority, alert in self._alerts.items()
            if now_ms - alert.started_ms < alert.duration_ms
        }
        self._now_ms = now_ms

    def set_texture(self, primitive: HapticPrimitive | None, *, now_ms: float) -> None:
        """Update texture without restarting phase; ``None`` clears/resets it.

        A newly installed texture starts on at phase zero. Intensity zero is
        true silence but retains phase. Output changes are emitted by ``poll``.
        """
        now_ms = self._time(now_ms)
        if primitive is not None and not isinstance(primitive, HapticPrimitive):
            raise TypeError("primitive must be a HapticPrimitive or None")
        self._advance(now_ms)
        if primitive is None or self._texture is None:
            self._texture_phase = 0.0
        self._texture = primitive

    def set_alert(
        self,
        primitive: HapticPrimitive,
        *,
        now_ms: float,
        duration_ms: float,
        priority: float = 100,
    ) -> None:
        """Install a phase-zero alert with positive finite duration and priority.

        Lifetime is ``[now_ms, now_ms + duration_ms)``. Even a silent alert
        suppresses texture and weaker alerts. Output is emitted only by ``poll``.
        """
        now_ms = self._time(now_ms)
        duration_ms = _number("duration_ms", duration_ms, positive=True)
        priority = _number("priority", priority, positive=True)
        if not isinstance(primitive, HapticPrimitive):
            raise TypeError("primitive must be a HapticPrimitive")
        self._advance(now_ms)
        if priority not in self._alerts and len(self._alerts) >= self.MAX_ALERTS:
            weakest = min(self._alerts)
            if priority < weakest:
                return
            del self._alerts[weakest]
        self._alerts[priority] = _Alert(primitive, now_ms, duration_ms)

    def poll(self, now_ms: float) -> list[PrimitiveEvent]:
        """Return zero or one currently needed packet change, timestamped now.

        The first poll establishes output, including explicit silence if idle.
        Missed pulses are intentionally dropped, not replayed.
        """
        now_ms = self._time(now_ms)
        self._advance(now_ms)
        if self._alerts:
            alert = self._alerts[max(self._alerts)]
            phase = _phase(0.0, now_ms - alert.started_ms, alert.primitive)
            packet = _packet(alert.primitive, phase)
        else:
            packet = _packet(self._texture, self._texture_phase)
        if packet == self._last_packet:
            return []
        self._last_packet = packet
        return [PrimitiveEvent(now_ms, packet, "off" if packet == SILENCE_PACKET else "on")]

    def stop(self, now_ms: float) -> list[PrimitiveEvent]:
        """Clear both channels and always return an explicit silence command."""
        now_ms = self._time(now_ms)
        self._now_ms = now_ms
        self._texture = None
        self._texture_phase = 0.0
        self._alerts.clear()
        self._last_packet = SILENCE_PACKET
        return [PrimitiveEvent(now_ms, SILENCE_PACKET, "off")]
