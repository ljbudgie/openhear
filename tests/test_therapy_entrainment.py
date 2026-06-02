"""Tests for therapy/entrainment.py — delivery-agnostic haptic entrainment."""

from __future__ import annotations

import pytest

from stream.haptic_packet import PACKET_LENGTH, decode_packet
from therapy.entrainment import (
    DEFAULT_INTENSITY,
    THERAPY_SOUND_CLASS_ID,
    EntrainmentEvent,
    events_for_protocol,
    haptic_events,
    pulse_schedule,
)
from therapy.protocol import BRAINWAVE_PROTOCOLS, ContraindicationError, get_protocol

# ── Pulse train timing ──────────────────────────────────────────────────────


def test_pulse_count_matches_frequency_and_duration():
    # 10 Hz for 2 s → 20 complete pulses.
    pulses = pulse_schedule(10.0, 2.0)
    assert len(pulses) == 20


def test_pulse_spacing_and_duty_cycle():
    pulses = pulse_schedule(10.0, 1.0, duty_cycle=0.4)
    period_ms = 100.0
    assert pulses[0].onset_ms == 0.0
    assert pulses[1].onset_ms == pytest.approx(period_ms)
    # 40% duty of a 100 ms period → 40 ms on.
    assert pulses[0].duration_ms == pytest.approx(40.0)
    assert pulses[0].offset_ms == pytest.approx(40.0)


def test_pulse_schedule_validation():
    with pytest.raises(ValueError):
        pulse_schedule(0.0, 1.0)
    with pytest.raises(ValueError):
        pulse_schedule(10.0, 0.0)
    for bad_duty in (0.0, 1.0, 1.5):
        with pytest.raises(ValueError):
            pulse_schedule(10.0, 1.0, duty_cycle=bad_duty)


# ── Haptic event rendering ──────────────────────────────────────────────────


def test_each_pulse_yields_on_then_off():
    events = haptic_events(5.0, 1.0)  # 5 pulses → 10 events
    assert len(events) == 10
    assert all(isinstance(e, EntrainmentEvent) for e in events)
    # Events are time-ordered.
    times = [e.at_ms for e in events]
    assert times == sorted(times)


def test_on_and_off_packets_are_valid_and_distinct():
    events = haptic_events(10.0, 0.5, intensity=120)
    ons = [e for e in events if e.kind == "on"]
    offs = [e for e in events if e.kind == "off"]
    assert ons and offs
    for e in events:
        assert len(e.packet) == PACKET_LENGTH
    on_decoded = decode_packet(ons[0].packet)
    off_decoded = decode_packet(offs[0].packet)
    assert on_decoded.sound_class_id == THERAPY_SOUND_CLASS_ID
    assert on_decoded.intensity == 120          # drive
    assert off_decoded.intensity == 0           # stop


def test_default_intensity_is_within_firmware_ceiling():
    # Firmware MAX_INTENSITY is 180; default must stay under it.
    assert 0 < DEFAULT_INTENSITY <= 180
    on = [e for e in haptic_events(8.0, 0.5) if e.kind == "on"][0]
    assert decode_packet(on.packet).intensity == DEFAULT_INTENSITY


def test_off_follows_on_within_one_period():
    events = haptic_events(10.0, 0.3, duty_cycle=0.5)
    first_on = next(e for e in events if e.kind == "on")
    first_off = next(e for e in events if e.kind == "off")
    # 50% of a 100 ms period → off 50 ms after on.
    assert first_off.at_ms - first_on.at_ms == pytest.approx(50.0)


# ── Protocol integration + safety gating ────────────────────────────────────


def test_events_for_protocol_renders_first_frequency():
    proto = get_protocol("alpha_relax")  # 10 Hz
    events = events_for_protocol(proto, duration_s=1.0)
    # 10 Hz over 1 s → 10 pulses → 20 events.
    assert len(events) == 20


def test_events_for_protocol_gates_contraindications():
    proto = get_protocol("gamma_40hz")
    with pytest.raises(ContraindicationError):
        events_for_protocol(proto, duration_s=1.0, conditions={"epilepsy"})


def test_every_preset_can_render_a_short_schedule():
    for proto in BRAINWAVE_PROTOCOLS.values():
        events = events_for_protocol(proto, duration_s=0.5)
        assert events  # non-empty, and no contraindication for an empty condition set
