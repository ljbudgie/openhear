"""
entrainment.py – delivery-agnostic rhythmic entrainment scheduling.

A binaural beat is one way to present a rhythm to the brain; it needs two
audible, balanced ear-tones (see :mod:`therapy.binaural`).  But the *rhythm*
itself — "pulse at 10 Hz for 20 minutes" — does not care how it reaches you.
This module renders that rhythm as a precise schedule of **isochronic
pulses** that can drive the wristband, so an entrainment frequency can be
*felt* when it cannot be heard.

That matters for OpenHear's hardest case: profound loss, where no acoustic
carrier works at all.  A 10 Hz rhythm on the wrist needs no residual hearing.
The same protocol can therefore be delivered acoustically (binaural, via
hearing aids or earbuds) *or* haptically (this module) *or* both — the user
chooses the channel their body can receive.

The output is a timestamped list of 3-byte wristband packets built with the
shared :func:`stream.haptic_packet.encode_packet` codec, so the wire format
is identical to every other haptic path.  Pure timing maths, no I/O, fully
unit-testable.  OpenHear is not a medical device; see
:mod:`therapy.protocol` for evidence grading and contraindication gating.
"""

from __future__ import annotations

from dataclasses import dataclass

from stream.haptic_packet import encode_packet
from therapy.protocol import TherapeuticProtocol

#: Reserved wristband sound-class id for therapeutic entrainment pulses.
#: Distinct from the environmental-awareness classes (0–6) so the firmware
#: and app can route therapy separately and never confuse it with an alert.
THERAPY_SOUND_CLASS_ID: int = 200

#: Reserved pattern id meaning "sustain a steady pulse until the off event".
THERAPY_PATTERN_ID: int = 200

#: Default per-pulse intensity. Kept under the firmware intensity ceiling
#: (MAX_INTENSITY = 180) and gentle for long sessions.
DEFAULT_INTENSITY: int = 150


@dataclass(frozen=True)
class Pulse:
    """One on/off pulse of the entrainment rhythm.

    Attributes:
        onset_ms: Pulse start, milliseconds from session start.
        duration_ms: How long the pulse stays on, milliseconds.
    """

    onset_ms: float
    duration_ms: float

    @property
    def offset_ms(self) -> float:
        """When the pulse ends (onset + duration), milliseconds."""
        return self.onset_ms + self.duration_ms


@dataclass(frozen=True)
class EntrainmentEvent:
    """A single timestamped wristband packet in an entrainment schedule.

    Attributes:
        at_ms: When to send the packet, milliseconds from session start.
        packet: The 3-byte wristband payload.
        kind: ``"on"`` (drive) or ``"off"`` (stop).
    """

    at_ms: float
    packet: bytes
    kind: str


def pulse_schedule(
    beat_hz: float,
    duration_s: float,
    *,
    duty_cycle: float = 0.5,
) -> list[Pulse]:
    """Return the isochronic pulse train for *beat_hz* over *duration_s*.

    Args:
        beat_hz: Entrainment (pulse) frequency in Hz.
        duration_s: Session length in seconds.
        duty_cycle: Fraction of each period the pulse is on, in ``(0, 1)``.

    Returns:
        A list of :class:`Pulse`, one per complete period that fits in
        ``duration_s``.

    Raises:
        ValueError: On non-positive ``beat_hz``/``duration_s`` or a
            ``duty_cycle`` outside ``(0, 1)`` (an off phase must exist for a
            rhythm to be perceptible).
    """
    if beat_hz <= 0:
        raise ValueError("beat_hz must be positive.")
    if duration_s <= 0:
        raise ValueError("duration_s must be positive.")
    if not 0.0 < duty_cycle < 1.0:
        raise ValueError("duty_cycle must be in (0, 1) so each pulse has an off phase.")

    period_ms = 1000.0 / beat_hz
    on_ms = period_ms * duty_cycle
    count = int(duration_s * beat_hz)
    return [Pulse(onset_ms=k * period_ms, duration_ms=on_ms) for k in range(count)]


def haptic_events(
    beat_hz: float,
    duration_s: float,
    *,
    duty_cycle: float = 0.5,
    intensity: int = DEFAULT_INTENSITY,
    sound_class_id: int = THERAPY_SOUND_CLASS_ID,
    pattern_id: int = THERAPY_PATTERN_ID,
) -> list[EntrainmentEvent]:
    """Render an entrainment rhythm as timestamped wristband packets.

    Each pulse becomes an ``"on"`` event at its onset (intensity > 0) and an
    ``"off"`` event at its end (intensity 0, which the firmware treats as
    stop), so the wrist follows the beat exactly.

    Args:
        beat_hz: Entrainment frequency in Hz.
        duration_s: Session length in seconds.
        duty_cycle: On-fraction of each period, ``(0, 1)``.
        intensity: On-pulse intensity (0–255; kept gentle by default).
        sound_class_id: Wristband class id for the therapy channel.
        pattern_id: Wristband pattern id for the therapy channel.

    Returns:
        Events sorted by ``at_ms``: an on/off pair per pulse.
    """
    off_packet = encode_packet(sound_class_id, 0, pattern_id)
    on_packet = encode_packet(sound_class_id, intensity, pattern_id)

    events: list[EntrainmentEvent] = []
    for pulse in pulse_schedule(beat_hz, duration_s, duty_cycle=duty_cycle):
        events.append(EntrainmentEvent(pulse.onset_ms, on_packet, "on"))
        events.append(EntrainmentEvent(pulse.offset_ms, off_packet, "off"))
    events.sort(key=lambda e: (e.at_ms, e.kind == "on"))
    return events


def events_for_protocol(
    protocol: TherapeuticProtocol,
    *,
    duration_s: float | None = None,
    conditions: frozenset[str] | set[str] = frozenset(),
    intensity: int = DEFAULT_INTENSITY,
) -> list[EntrainmentEvent]:
    """Build a haptic entrainment schedule for a bundled protocol.

    Gates contraindications first (a seizure-disorder user gets a refusal,
    not a buzzing wrist), then renders the protocol's first frequency at its
    declared duty cycle for ``duration_s`` (default: the protocol's
    ``session_length_s``).

    Args:
        protocol: The therapeutic protocol to deliver.
        duration_s: Override session length in seconds.
        conditions: The user's declared health conditions, for gating.
        intensity: On-pulse intensity.

    Returns:
        The entrainment event schedule.

    Raises:
        ContraindicationError: If the user's conditions are contraindicated.
    """
    protocol.gate(conditions)
    seconds = duration_s if duration_s is not None else float(protocol.session_length_s)
    return haptic_events(
        protocol.frequencies[0],
        seconds,
        duty_cycle=protocol.duty_cycle if protocol.duty_cycle < 1.0 else 0.5,
        intensity=intensity,
    )
