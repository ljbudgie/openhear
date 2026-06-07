"""Tests for ``stream/haptic_primitive.py`` — parametrised haptic primitives."""

from __future__ import annotations

import pytest

from stream.haptic_packet import PACKET_LENGTH
from stream.haptic_primitive import (
    PRIMITIVE_CLASS_CENTRE,
    PRIMITIVE_CLASS_LEFT,
    PRIMITIVE_CLASS_RIGHT,
    PRIMITIVE_PATTERN_MEDIUM,
    PRIMITIVE_PATTERN_SHARP,
    PRIMITIVE_PATTERN_SOFT,
    PULSE_RATE_MAX_HZ,
    PULSE_RATE_MIN_HZ,
    SILENCE_PACKET,
    HapticPrimitive,
    PrimitiveEvent,
    alert,
    calm,
    directional,
)

# ── Construction & validation ─────────────────────────────────────────────────


def test_valid_primitive_constructs():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=128, spatial_balance=0.0, sharpness=0.5)
    assert p.pulse_rate_hz == 4.0
    assert p.intensity == 128
    assert p.spatial_balance == 0.0
    assert p.sharpness == 0.5


def test_pulse_rate_too_low_raises():
    with pytest.raises(ValueError, match="pulse_rate_hz"):
        HapticPrimitive(pulse_rate_hz=0.0, intensity=128, spatial_balance=0.0, sharpness=0.5)


def test_pulse_rate_too_high_raises():
    with pytest.raises(ValueError, match="pulse_rate_hz"):
        HapticPrimitive(
            pulse_rate_hz=PULSE_RATE_MAX_HZ + 0.1,
            intensity=128,
            spatial_balance=0.0,
            sharpness=0.5,
        )


def test_intensity_negative_raises():
    with pytest.raises(ValueError, match="intensity"):
        HapticPrimitive(pulse_rate_hz=1.0, intensity=-1, spatial_balance=0.0, sharpness=0.5)


def test_intensity_over_255_raises():
    with pytest.raises(ValueError, match="intensity"):
        HapticPrimitive(pulse_rate_hz=1.0, intensity=256, spatial_balance=0.0, sharpness=0.5)


def test_intensity_not_int_raises():
    with pytest.raises(TypeError, match="intensity"):
        HapticPrimitive(pulse_rate_hz=1.0, intensity=1.5, spatial_balance=0.0, sharpness=0.5)


def test_spatial_balance_too_low_raises():
    with pytest.raises(ValueError, match="spatial_balance"):
        HapticPrimitive(pulse_rate_hz=1.0, intensity=128, spatial_balance=-1.1, sharpness=0.5)


def test_spatial_balance_too_high_raises():
    with pytest.raises(ValueError, match="spatial_balance"):
        HapticPrimitive(pulse_rate_hz=1.0, intensity=128, spatial_balance=1.1, sharpness=0.5)


def test_sharpness_out_of_range_raises():
    with pytest.raises(ValueError, match="sharpness"):
        HapticPrimitive(
            pulse_rate_hz=1.0, intensity=128, spatial_balance=0.0, sharpness=1.1
        )


def test_boundary_values_are_valid():
    # All boundary values should construct without error
    HapticPrimitive(
        pulse_rate_hz=PULSE_RATE_MIN_HZ, intensity=0, spatial_balance=-1.0, sharpness=0.0
    )
    HapticPrimitive(
        pulse_rate_hz=PULSE_RATE_MAX_HZ, intensity=255, spatial_balance=1.0, sharpness=1.0
    )


# ── duty_cycle property ───────────────────────────────────────────────────────


def test_duty_cycle_at_zero_sharpness_is_half():
    p = HapticPrimitive(pulse_rate_hz=1.0, intensity=128, spatial_balance=0.0, sharpness=0.0)
    assert p.duty_cycle == pytest.approx(0.5)


def test_duty_cycle_at_full_sharpness_is_one_tenth():
    p = HapticPrimitive(pulse_rate_hz=1.0, intensity=128, spatial_balance=0.0, sharpness=1.0)
    assert p.duty_cycle == pytest.approx(0.1)


def test_duty_cycle_decreases_with_sharpness():
    lo = HapticPrimitive(pulse_rate_hz=1.0, intensity=128, spatial_balance=0.0, sharpness=0.2)
    hi = HapticPrimitive(pulse_rate_hz=1.0, intensity=128, spatial_balance=0.0, sharpness=0.8)
    assert lo.duty_cycle > hi.duty_cycle


# ── spatial_zone property ─────────────────────────────────────────────────────


def test_spatial_zone_left():
    p = HapticPrimitive(pulse_rate_hz=1.0, intensity=128, spatial_balance=-0.9, sharpness=0.5)
    assert p.spatial_zone == "left"


def test_spatial_zone_right():
    p = HapticPrimitive(pulse_rate_hz=1.0, intensity=128, spatial_balance=0.9, sharpness=0.5)
    assert p.spatial_zone == "right"


def test_spatial_zone_centre():
    p = HapticPrimitive(pulse_rate_hz=1.0, intensity=128, spatial_balance=0.0, sharpness=0.5)
    assert p.spatial_zone == "centre"


def test_spatial_zone_boundary_centre_range():
    # −0.33 and +0.33 are the centre-zone boundaries (exclusive)
    lo = HapticPrimitive(pulse_rate_hz=1.0, intensity=128, spatial_balance=-0.33, sharpness=0.5)
    hi = HapticPrimitive(pulse_rate_hz=1.0, intensity=128, spatial_balance=0.33, sharpness=0.5)
    assert lo.spatial_zone == "centre"
    assert hi.spatial_zone == "centre"


# ── to_packet ─────────────────────────────────────────────────────────────────


def test_to_packet_returns_three_bytes():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.0, sharpness=0.5)
    assert len(p.to_packet()) == PACKET_LENGTH


def test_to_packet_centre_uses_centre_class():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.0, sharpness=0.5)
    pkt = p.to_packet()
    assert pkt[0] == PRIMITIVE_CLASS_CENTRE


def test_to_packet_left_uses_left_class():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=-0.9, sharpness=0.5)
    pkt = p.to_packet()
    assert pkt[0] == PRIMITIVE_CLASS_LEFT


def test_to_packet_right_uses_right_class():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.9, sharpness=0.5)
    pkt = p.to_packet()
    assert pkt[0] == PRIMITIVE_CLASS_RIGHT


def test_to_packet_intensity_is_byte_1():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=77, spatial_balance=0.0, sharpness=0.5)
    assert p.to_packet()[1] == 77


def test_to_packet_soft_sharpness_selects_soft_pattern():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.0, sharpness=0.1)
    assert p.to_packet()[2] == PRIMITIVE_PATTERN_SOFT


def test_to_packet_medium_sharpness_selects_medium_pattern():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.0, sharpness=0.5)
    assert p.to_packet()[2] == PRIMITIVE_PATTERN_MEDIUM


def test_to_packet_high_sharpness_selects_sharp_pattern():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.0, sharpness=0.9)
    assert p.to_packet()[2] == PRIMITIVE_PATTERN_SHARP


# ── to_events ─────────────────────────────────────────────────────────────────


def test_to_events_zero_duration_is_empty():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.0, sharpness=0.5)
    assert p.to_events(0.0) == []


def test_to_events_negative_duration_is_empty():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.0, sharpness=0.5)
    assert p.to_events(-1.0) == []


def test_to_events_alternates_on_off():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.0, sharpness=0.5)
    events = p.to_events(1.0)
    assert len(events) > 0
    for i, ev in enumerate(events):
        expected_kind = "on" if i % 2 == 0 else "off"
        assert ev.kind == expected_kind, f"event {i} should be {expected_kind!r}"


def test_to_events_on_events_carry_primitive_packet():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.0, sharpness=0.5)
    pkt = p.to_packet()
    events = p.to_events(1.0)
    on_events = [e for e in events if e.kind == "on"]
    for ev in on_events:
        assert ev.packet == pkt


def test_to_events_off_events_carry_silence_packet():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.0, sharpness=0.5)
    events = p.to_events(1.0)
    off_events = [e for e in events if e.kind == "off"]
    for ev in off_events:
        assert ev.packet == SILENCE_PACKET


def test_to_events_sorted_by_at_ms():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.0, sharpness=0.5)
    events = p.to_events(2.0)
    times = [e.at_ms for e in events]
    assert times == sorted(times)


def test_to_events_first_event_at_zero():
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.0, sharpness=0.5)
    events = p.to_events(1.0)
    assert events[0].at_ms == pytest.approx(0.0)


def test_to_events_no_event_beyond_duration():
    duration_s = 1.0
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.0, sharpness=0.5)
    events = p.to_events(duration_s)
    assert all(e.at_ms <= duration_s * 1000.0 for e in events)


def test_to_events_count_matches_rate():
    # 4 Hz for 1 s → 4 pulses → 8 events (4 on + 4 off)
    p = HapticPrimitive(pulse_rate_hz=4.0, intensity=100, spatial_balance=0.0, sharpness=0.5)
    events = p.to_events(1.0)
    on_count = sum(1 for e in events if e.kind == "on")
    assert on_count == 4


def test_to_events_returns_primitive_event_instances():
    p = HapticPrimitive(pulse_rate_hz=2.0, intensity=100, spatial_balance=0.0, sharpness=0.5)
    events = p.to_events(1.0)
    assert all(isinstance(e, PrimitiveEvent) for e in events)


# ── Factories ─────────────────────────────────────────────────────────────────


def test_calm_constructs():
    p = calm()
    assert isinstance(p, HapticPrimitive)
    assert p.spatial_zone == "centre"
    assert p.pulse_rate_hz < 3.0  # should be slow


def test_alert_constructs():
    p = alert()
    assert isinstance(p, HapticPrimitive)
    assert p.pulse_rate_hz > 5.0  # should be fast
    assert p.intensity > 150  # should be strong


def test_alert_is_faster_and_stronger_than_calm():
    c = calm()
    a = alert()
    assert a.pulse_rate_hz > c.pulse_rate_hz
    assert a.intensity > c.intensity
    assert a.sharpness > c.sharpness


def test_directional_centre():
    p = directional(0.0)
    assert p.spatial_zone == "centre"
    assert p.spatial_balance == pytest.approx(0.0)


def test_directional_hard_left():
    p = directional(-1.0)
    assert p.spatial_zone == "left"


def test_directional_hard_right():
    p = directional(1.0)
    assert p.spatial_zone == "right"


def test_directional_custom_intensity():
    p = directional(0.5, intensity=200)
    assert p.intensity == 200


def test_directional_custom_rate():
    p = directional(0.5, rate_hz=10.0)
    assert p.pulse_rate_hz == pytest.approx(10.0)


def test_directional_out_of_range_bearing_raises():
    with pytest.raises(ValueError, match="bearing"):
        directional(1.5)


def test_directional_out_of_range_bearing_negative_raises():
    with pytest.raises(ValueError, match="bearing"):
        directional(-1.5)
