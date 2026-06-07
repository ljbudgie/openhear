"""Tests for ``stream/tempo_channel.py`` — performer's live-BPM beat channel."""

from __future__ import annotations

import pytest

from stream.haptic_packet import PACKET_LENGTH
from stream.haptic_primitive import SILENCE_PACKET, HapticPrimitive, PrimitiveEvent
from stream.tempo_channel import (
    DEFAULT_INTENSITY,
    DEFAULT_SHARPNESS,
    MAX_BPM,
    MIN_BPM,
    TempoChannel,
    WindowedBeats,
    bpm_to_pulse_rate_hz,
    pulse_rate_hz_to_bpm,
)

# ── Conversion helpers ────────────────────────────────────────────────────────


def test_bpm_to_pulse_rate_hz_round_trip():
    for bpm in (30.0, 60.0, 120.0, 144.0, 300.0):
        assert pulse_rate_hz_to_bpm(bpm_to_pulse_rate_hz(bpm)) == pytest.approx(bpm)


def test_bpm_to_pulse_rate_hz_known_values():
    assert bpm_to_pulse_rate_hz(120.0) == pytest.approx(2.0)
    assert bpm_to_pulse_rate_hz(60.0) == pytest.approx(1.0)


def test_bpm_to_pulse_rate_hz_rejects_below_min():
    with pytest.raises(ValueError, match="bpm"):
        bpm_to_pulse_rate_hz(MIN_BPM - 0.01)


def test_bpm_to_pulse_rate_hz_rejects_above_max():
    with pytest.raises(ValueError, match="bpm"):
        bpm_to_pulse_rate_hz(MAX_BPM + 0.01)


def test_pulse_rate_hz_to_bpm_rejects_out_of_range():
    with pytest.raises(ValueError, match="pulse_rate_hz"):
        pulse_rate_hz_to_bpm(0.0)
    with pytest.raises(ValueError, match="pulse_rate_hz"):
        pulse_rate_hz_to_bpm(100.0)


# ── Construction & validation ─────────────────────────────────────────────────


def test_default_channel_constructs():
    ch = TempoChannel()
    assert ch.bpm is None
    assert ch.beats_per_bar is None


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"intensity": -1}, "intensity"),
        ({"intensity": 256}, "intensity"),
        ({"sharpness": -0.1}, "sharpness"),
        ({"sharpness": 1.1}, "sharpness"),
        ({"spatial_balance": -1.1}, "spatial_balance"),
        ({"spatial_balance": 1.1}, "spatial_balance"),
        ({"smoothing": -0.1}, "smoothing"),
        ({"smoothing": 1.0}, "smoothing"),
        ({"beats_per_bar": 0}, "beats_per_bar"),
        ({"accent_intensity": 300}, "accent_intensity"),
    ],
)
def test_invalid_construction_raises(kwargs, match):
    with pytest.raises(ValueError, match=match):
        TempoChannel(**kwargs)


# ── update() ──────────────────────────────────────────────────────────────────


def test_update_rejects_out_of_range_bpm():
    ch = TempoChannel()
    with pytest.raises(ValueError, match="bpm"):
        ch.update(MIN_BPM - 1.0)
    with pytest.raises(ValueError, match="bpm"):
        ch.update(MAX_BPM + 1.0)


def test_update_sets_bpm_and_returns_primitive():
    ch = TempoChannel()
    prim = ch.update(120.0)
    assert isinstance(prim, HapticPrimitive)
    assert ch.bpm == 120.0
    assert prim.pulse_rate_hz == pytest.approx(2.0)
    assert prim.intensity == DEFAULT_INTENSITY
    assert prim.sharpness == DEFAULT_SHARPNESS
    assert prim.spatial_balance == 0.0


def test_update_smoothing_averages_live_tempo():
    ch = TempoChannel(smoothing=0.5)
    ch.update(120.0)
    # Second reading is averaged 50/50 with the previous smoothed value.
    ch.update(140.0)
    assert ch.bpm == pytest.approx(130.0)


def test_to_primitive_without_update_raises():
    ch = TempoChannel()
    with pytest.raises(RuntimeError, match="BPM"):
        ch.to_primitive()


# ── events_for_window basics ──────────────────────────────────────────────────


def test_events_for_window_requires_bpm():
    ch = TempoChannel()
    with pytest.raises(RuntimeError, match="BPM"):
        ch.events_for_window(1.0)


def test_events_for_window_returns_windowed_beats():
    ch = TempoChannel()
    ch.update(120.0)
    result = ch.events_for_window(1.0)
    assert isinstance(result, WindowedBeats)


def test_events_for_window_non_positive_returns_empty():
    ch = TempoChannel()
    ch.update(120.0)
    assert ch.events_for_window(0.0).events == []
    assert ch.events_for_window(-1.0).events == []


def test_events_for_window_emits_on_off_pairs():
    ch = TempoChannel()
    ch.update(120.0)  # period = 500 ms
    result = ch.events_for_window(1.0)
    # 2 beats in 1.0 s → 4 events.
    assert len(result.events) == 4
    kinds = [e.kind for e in result.events]
    assert kinds == ["on", "off", "on", "off"]


def test_events_for_window_first_beat_at_t_zero():
    ch = TempoChannel()
    ch.update(120.0)
    result = ch.events_for_window(0.5)
    assert result.events[0].at_ms == 0.0
    assert result.events[0].kind == "on"


def test_events_for_window_beat_period_matches_bpm():
    ch = TempoChannel()
    ch.update(120.0)  # 500 ms period
    result = ch.events_for_window(2.0)
    onsets = [e.at_ms for e in result.events if e.kind == "on"]
    assert onsets == pytest.approx([0.0, 500.0, 1000.0, 1500.0])


def test_events_for_window_off_packet_is_silence():
    ch = TempoChannel()
    ch.update(120.0)
    result = ch.events_for_window(1.0)
    offs = [e for e in result.events if e.kind == "off"]
    for off in offs:
        assert off.packet == SILENCE_PACKET


def test_events_for_window_off_clamped_to_window_end():
    ch = TempoChannel(sharpness=0.0)  # 50% duty → on_ms = 250 at 120 BPM
    ch.update(120.0)
    # Window 600 ms: beats at 0 and 500.  Second beat's off would be 750
    # but is clamped to 600.
    result = ch.events_for_window(0.6)
    last = result.events[-1]
    assert last.kind == "off"
    assert last.at_ms == 600.0


def test_events_packets_are_three_bytes():
    ch = TempoChannel()
    ch.update(120.0)
    for e in ch.events_for_window(1.0).events:
        assert isinstance(e.packet, bytes)
        assert len(e.packet) == PACKET_LENGTH


# ── Phase continuity across windows ───────────────────────────────────────────


def test_phase_continuity_back_to_back_windows():
    ch = TempoChannel()
    ch.update(120.0)  # 500 ms period
    # Three back-to-back 600 ms windows == 1800 ms total.
    # Expected beat absolute times: 0, 500, 1000, 1500.
    onsets_absolute: list[float] = []
    window_start = 0.0
    for _ in range(3):
        result = ch.events_for_window(0.6)
        for e in result.events:
            if e.kind == "on":
                onsets_absolute.append(window_start + e.at_ms)
        window_start += 600.0
    assert onsets_absolute == pytest.approx([0.0, 500.0, 1000.0, 1500.0])


def test_tempo_change_between_windows_preserves_phase():
    ch = TempoChannel()
    # Start at 60 BPM (period = 1000 ms): first beat at 0, next at 1000.
    ch.update(60.0)
    first = ch.events_for_window(0.6)  # only the t=0 beat fires
    assert [e.at_ms for e in first.events if e.kind == "on"] == [0.0]
    # Now double the tempo: period = 500 ms.  600 ms have elapsed since the
    # last beat, which is already past one new period (500), so the next
    # beat should fire immediately at t=0 of the second window.
    ch.update(120.0)
    second = ch.events_for_window(1.0)
    onsets = [e.at_ms for e in second.events if e.kind == "on"]
    assert onsets[0] == 0.0
    # Then beats spaced by the new 500 ms period.
    assert onsets == pytest.approx([0.0, 500.0])


def test_window_with_no_beat_advances_phase():
    ch = TempoChannel()
    ch.update(30.0)  # 2000 ms period (MIN_BPM)
    # First call fires t=0 immediately; phase after = 500 ms.
    ch.events_for_window(0.5)
    # Next 1 s window: nothing fires (next beat is still 1500 ms away).
    second = ch.events_for_window(1.0)
    assert second.events == []
    # After 1500 ms accumulated, next beat should arrive 500 ms into a
    # 1 s window (period − accumulated = 2000 − 1500 = 500).
    third = ch.events_for_window(1.0)
    onsets = [e.at_ms for e in third.events if e.kind == "on"]
    assert onsets == [500.0]


def test_reset_clears_state():
    ch = TempoChannel()
    ch.update(120.0)
    ch.events_for_window(0.6)
    ch.reset()
    assert ch.bpm is None
    with pytest.raises(RuntimeError):
        ch.events_for_window(1.0)


# ── Accent / bar tracking ─────────────────────────────────────────────────────


def test_no_accent_when_beats_per_bar_unset():
    ch = TempoChannel(intensity=120)
    ch.update(120.0)
    result = ch.events_for_window(2.0)
    assert result.bar_starts_ms == []
    # All on-packets carry the offbeat intensity.
    on_packets = [e.packet for e in result.events if e.kind == "on"]
    expected = HapticPrimitive(
        pulse_rate_hz=2.0,
        intensity=120,
        spatial_balance=0.0,
        sharpness=DEFAULT_SHARPNESS,
    ).to_packet()
    assert all(p == expected for p in on_packets)


def test_downbeat_accent_uses_accent_intensity():
    ch = TempoChannel(intensity=100, accent_intensity=200, beats_per_bar=4)
    ch.update(120.0)  # 500 ms period
    result = ch.events_for_window(2.0)  # 4 beats == 1 bar
    on_events = [e for e in result.events if e.kind == "on"]
    assert len(on_events) == 4
    downbeat_pkt = HapticPrimitive(
        pulse_rate_hz=2.0,
        intensity=200,
        spatial_balance=0.0,
        sharpness=DEFAULT_SHARPNESS,
    ).to_packet()
    offbeat_pkt = HapticPrimitive(
        pulse_rate_hz=2.0,
        intensity=100,
        spatial_balance=0.0,
        sharpness=DEFAULT_SHARPNESS,
    ).to_packet()
    assert on_events[0].packet == downbeat_pkt
    assert all(e.packet == offbeat_pkt for e in on_events[1:])
    assert result.bar_starts_ms == [0.0]


def test_accent_default_is_intensity_plus_fifty_capped():
    ch = TempoChannel(intensity=220, beats_per_bar=2)
    # 220 + 50 == 270 capped to 255.
    ch.update(120.0)
    result = ch.events_for_window(1.0)
    on_events = [e for e in result.events if e.kind == "on"]
    capped = HapticPrimitive(
        pulse_rate_hz=2.0,
        intensity=255,
        spatial_balance=0.0,
        sharpness=DEFAULT_SHARPNESS,
    ).to_packet()
    assert on_events[0].packet == capped


def test_bar_position_persists_across_windows():
    ch = TempoChannel(intensity=100, accent_intensity=200, beats_per_bar=4)
    ch.update(120.0)  # 500 ms period
    # First window: beats 0, 1 of bar (t=0 and t=500).
    first = ch.events_for_window(1.0)
    assert first.bar_starts_ms == [0.0]
    # Second window: beats 2, 3 of bar (t=0 and t=500 relative).  No downbeat.
    second = ch.events_for_window(1.0)
    assert second.bar_starts_ms == []
    # Third window: beat 0 of next bar fires at t=0.
    third = ch.events_for_window(1.0)
    assert third.bar_starts_ms == [0.0]


# ── PrimitiveEvent contract sanity ────────────────────────────────────────────


def test_events_are_primitive_events():
    ch = TempoChannel()
    ch.update(120.0)
    for e in ch.events_for_window(1.0).events:
        assert isinstance(e, PrimitiveEvent)
