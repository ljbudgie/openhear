"""Clock-supplied playback, phase continuity, and exclusive alert arbitration."""

from copy import deepcopy
from dataclasses import replace

import pytest

from stream.haptic_playback import HapticPlayback
from stream.haptic_primitive import SILENCE_PACKET, HapticPrimitive, PrimitiveEvent


def primitive(rate=1.0, intensity=80, sharpness=0.0):
    return HapticPrimitive(rate, intensity, 0.0, sharpness)


def on(now, value):
    return [PrimitiveEvent(now, value.to_packet(), "on")]


def off(now):
    return [PrimitiveEvent(now, SILENCE_PACKET, "off")]


def test_fresh_start_and_half_open_pulse_boundaries():
    playback = HapticPlayback()
    value = primitive()
    assert playback.set_texture(value, now_ms=200) is None
    assert playback.poll(200) == on(200, value)
    assert playback.poll(699) == []
    assert playback.poll(700) == off(700)
    assert playback.poll(1199) == []
    assert playback.poll(1200) == on(1200, value)
    assert playback.poll(1200) == []


def test_frequent_texture_updates_do_not_restart_phase():
    playback = HapticPlayback()
    value = primitive()
    playback.set_texture(value, now_ms=0)
    assert playback.poll(0) == on(0, value)
    for now in range(100, 5001, 100):
        playback.set_texture(replace(value), now_ms=now)
        expected = on(now, value) if now % 1000 == 0 else off(now) if now % 500 == 0 else []
        assert playback.poll(now) == expected


def test_rate_change_integrates_previous_rate_before_preserving_phase():
    playback = HapticPlayback()
    slow = primitive()
    fast = replace(slow, pulse_rate_hz=2)
    playback.set_texture(slow, now_ms=0)
    assert playback.poll(0) == on(0, slow)
    playback.set_texture(fast, now_ms=250)
    assert playback.poll(250) == []
    assert playback.poll(374) == []
    assert playback.poll(375) == off(375)
    assert playback.poll(624) == []
    assert playback.poll(625) == on(625, fast)
    playback.set_texture(slow, now_ms=750)
    assert playback.poll(999) == []
    assert playback.poll(1000) == off(1000)


def test_sharpness_and_packet_updates_apply_at_existing_phase():
    playback = HapticPlayback()
    value = primitive()
    playback.set_texture(value, now_ms=0)
    playback.poll(0)
    sharp = replace(value, sharpness=1)
    playback.set_texture(sharp, now_ms=300)
    assert playback.poll(300) == off(300)
    changed = replace(value, intensity=100, spatial_balance=1)
    playback.set_texture(changed, now_ms=300)
    assert playback.poll(300) == on(300, changed)


def test_idle_and_zero_intensity_are_explicit_silence_without_energizing():
    playback = HapticPlayback()
    assert playback.poll(0) == off(0)
    playback.set_texture(primitive(intensity=0), now_ms=0)
    for now in (0, 100, 500, 1000, 1500):
        assert playback.poll(now) == []
    fresh = HapticPlayback()
    fresh.set_texture(primitive(intensity=0), now_ms=10)
    assert fresh.poll(10) == off(10)


def test_zero_intensity_retains_phase_and_none_clears_it():
    playback = HapticPlayback()
    value = primitive()
    playback.set_texture(value, now_ms=0)
    playback.poll(0)
    playback.set_texture(replace(value, intensity=0), now_ms=200)
    assert playback.poll(200) == off(200)
    playback.set_texture(value, now_ms=600)
    assert playback.poll(600) == []
    assert playback.poll(1000) == on(1000, value)
    playback.set_texture(None, now_ms=1100)
    assert playback.poll(1100) == off(1100)
    playback.set_texture(value, now_ms=1600)
    assert playback.poll(1600) == on(1600, value)


def test_texture_off_edges_cannot_interrupt_alert_and_latest_texture_resumes():
    playback = HapticPlayback()
    texture = primitive()
    alarm = primitive(intensity=220)
    playback.set_texture(texture, now_ms=0)
    playback.poll(0)
    playback.set_alert(alarm, now_ms=400, duration_ms=800)
    assert playback.poll(400) == on(400, alarm)
    assert playback.poll(500) == []  # Texture's off edge is suppressed.
    latest = replace(texture, intensity=120, spatial_balance=-1)
    playback.set_texture(latest, now_ms=600)
    assert playback.poll(600) == []
    assert playback.poll(900) == off(900)  # Only the alarm's own off edge.
    assert playback.poll(1000) == []  # Texture's on edge is also suppressed.
    assert playback.poll(1200) == on(1200, latest)


def test_rate_updates_during_alert_keep_advancing_hidden_texture():
    playback = HapticPlayback()
    value = primitive()
    playback.set_texture(value, now_ms=0)
    playback.set_alert(primitive(intensity=220), now_ms=0, duration_ms=625)
    playback.poll(0)
    faster = replace(value, pulse_rate_hz=2)
    playback.set_texture(faster, now_ms=250)
    playback.poll(375)
    assert playback.poll(625) == on(625, faster)
    assert playback.poll(875) == off(875)


def test_higher_priority_preempts_then_lower_resumes_at_current_phase():
    playback = HapticPlayback()
    low = primitive(intensity=100)
    high = primitive(intensity=220)
    playback.set_alert(low, now_ms=0, duration_ms=3000, priority=10)
    assert playback.poll(0) == on(0, low)
    playback.set_alert(high, now_ms=100, duration_ms=600, priority=100)
    assert playback.poll(100) == on(100, high)
    assert playback.poll(700) == off(700)  # Lower alert resumes in its off half.
    assert playback.poll(1000) == on(1000, low)
    assert playback.poll(3000) == off(3000)


def test_new_weaker_alert_does_not_interrupt_stronger_alert():
    playback = HapticPlayback()
    high = primitive(intensity=220)
    low = primitive(intensity=100)
    playback.set_alert(high, now_ms=0, duration_ms=200, priority=100)
    playback.poll(0)
    playback.set_alert(low, now_ms=50, duration_ms=1000, priority=1)
    assert playback.poll(50) == []
    assert playback.poll(200) == on(200, low)


def test_priority_not_amplitude_controls_winner_even_during_winners_off_half():
    playback = HapticPlayback()
    loud = primitive(intensity=255)
    quiet = primitive(intensity=1, sharpness=1)
    playback.set_alert(loud, now_ms=0, duration_ms=1000, priority=1.5)
    playback.set_alert(quiet, now_ms=0, duration_ms=200, priority=2.5)
    assert playback.poll(0) == on(0, quiet)
    assert playback.poll(100) == off(100)
    assert playback.poll(150) == []  # No loud lower-priority pulse fills the gap.
    assert playback.poll(200) == on(200, loud)


def test_fast_sharp_pulse_boundary_is_not_held_on():
    playback = HapticPlayback()
    value = primitive(rate=30, sharpness=1)
    period = 1000 / value.pulse_rate_hz
    playback.set_texture(value, now_ms=0)
    assert playback.poll(0) == on(0, value)
    assert playback.poll(period * value.duty_cycle) == off(period * value.duty_cycle)
    assert playback.poll(period) == on(period, value)


def test_equal_priority_replacement_restarts_phase_and_replaces_expiry():
    playback = HapticPlayback()
    first = primitive(intensity=100)
    second = primitive(intensity=220)
    playback.set_alert(first, now_ms=0, duration_ms=5000)
    playback.poll(0)
    assert playback.poll(600) == off(600)
    playback.set_alert(second, now_ms=600, duration_ms=200)
    assert playback.poll(600) == on(600, second)
    assert playback.poll(799) == []
    assert playback.poll(800) == off(800)
    assert playback.poll(1000) == []  # Replaced alert never returns.


def test_silent_high_priority_alert_suppresses_all_weaker_channels():
    playback = HapticPlayback()
    value = primitive()
    playback.set_texture(value, now_ms=0)
    playback.set_alert(primitive(intensity=200), now_ms=0, duration_ms=100, priority=1)
    playback.poll(0)
    playback.set_alert(primitive(intensity=0), now_ms=20, duration_ms=180, priority=2)
    assert playback.poll(20) == off(20)
    assert playback.poll(100) == []
    assert playback.poll(200) == on(200, value)


def test_alert_storage_is_bounded_and_retains_strongest_priorities():
    playback = HapticPlayback()
    for priority in range(1, 101):
        playback.set_alert(
            primitive(intensity=priority), now_ms=0, duration_ms=priority, priority=priority
        )
    assert len(playback._alerts) == playback.MAX_ALERTS
    assert playback.poll(0) == on(0, primitive(intensity=100))
    playback.set_alert(primitive(intensity=255), now_ms=0, duration_ms=1000, priority=1)
    assert playback.poll(0) == []
    assert len(playback._alerts) == playback.MAX_ALERTS
    assert playback.poll(100) == off(100)  # Discarded low priority did not queue.
    assert playback._alerts == {}


def test_late_poll_drops_old_edges_including_expired_alert():
    playback = HapticPlayback()
    value = primitive()
    playback.set_texture(value, now_ms=0)
    assert playback.poll(0) == on(0, value)
    playback.set_alert(primitive(intensity=220), now_ms=100, duration_ms=100)
    assert playback.poll(10_100) == []  # Same current packet, not missed pulses.
    assert playback.poll(10_600) == off(10_600)
    assert playback.poll(20_100) == on(20_100, value)


def test_huge_finite_clock_jump_does_not_overflow_phase():
    playback = HapticPlayback()
    value = primitive(rate=30)
    playback.set_texture(value, now_ms=0)
    playback.poll(0)
    events = playback.poll(1e308)
    assert len(events) <= 1
    assert all(event.at_ms == 1e308 for event in events)


def test_stop_always_silences_clears_state_and_allows_fresh_texture():
    playback = HapticPlayback()
    value = primitive()
    playback.set_texture(value, now_ms=0)
    playback.set_alert(primitive(intensity=220), now_ms=0, duration_ms=10000)
    playback.poll(0)
    assert playback.stop(200) == off(200)
    assert playback.poll(1000) == []
    assert playback.stop(1000) == off(1000)
    playback.set_texture(value, now_ms=1100)
    assert playback.poll(1100) == on(1100, value)
    with pytest.raises(ValueError, match="monotonic"):
        playback.stop(0)


@pytest.mark.parametrize("method", ["poll", "stop", "set_texture", "set_alert"])
@pytest.mark.parametrize("bad", [-1, 99, float("inf"), float("-inf"), float("nan")])
def test_invalid_times_rejected_before_any_mutation(method, bad):
    playback = HapticPlayback()
    value = primitive()
    playback.set_texture(value, now_ms=100)
    playback.set_alert(primitive(intensity=220), now_ms=100, duration_ms=100)
    playback.poll(100)
    before = deepcopy(playback.__dict__)
    with pytest.raises(ValueError):
        if method == "set_texture":
            playback.set_texture(None, now_ms=bad)
        elif method == "set_alert":
            playback.set_alert(value, now_ms=bad, duration_ms=100)
        else:
            getattr(playback, method)(bad)
    assert playback.__dict__ == before
    assert playback.poll(200) == on(200, value)


@pytest.mark.parametrize("field", ["duration_ms", "priority"])
@pytest.mark.parametrize("bad", [0, -1, float("nan"), float("inf"), float("-inf")])
def test_invalid_alert_parameters_do_not_advance_or_expire_existing_state(field, bad):
    playback = HapticPlayback()
    value = primitive()
    playback.set_texture(value, now_ms=0)
    playback.set_alert(primitive(intensity=220), now_ms=0, duration_ms=100)
    playback.poll(0)
    before = deepcopy(playback.__dict__)
    kwargs = {"duration_ms": 100, "priority": 100, field: bad}
    with pytest.raises(ValueError):
        playback.set_alert(value, now_ms=500, **kwargs)
    assert playback.__dict__ == before
    assert playback.poll(100) == on(100, value)


@pytest.mark.parametrize("bad", [None, "100", True, object()])
@pytest.mark.parametrize("field", ["now_ms", "duration_ms", "priority"])
def test_nonnumeric_arguments_rejected_without_mutation(field, bad):
    playback = HapticPlayback()
    before = deepcopy(playback.__dict__)
    kwargs = {"now_ms": 0, "duration_ms": 100, "priority": 100, field: bad}
    with pytest.raises(TypeError):
        playback.set_alert(primitive(), **kwargs)
    assert playback.__dict__ == before


def test_invalid_primitives_do_not_mutate_state():
    playback = HapticPlayback()
    playback.set_texture(primitive(), now_ms=0)
    before = deepcopy(playback.__dict__)
    with pytest.raises(TypeError):
        playback.set_texture(object(), now_ms=500)
    assert playback.__dict__ == before
    with pytest.raises(TypeError):
        playback.set_alert(None, now_ms=500, duration_ms=100)
    assert playback.__dict__ == before
