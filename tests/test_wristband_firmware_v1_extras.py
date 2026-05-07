"""Additional tests for ``hardware/wristband/firmware``."""

from __future__ import annotations

import pytest

from hardware.wristband.firmware.haptic_mapper import (
    BARK_BAND_CENTRES_HZ,
    COMMON_PATTERNS,
    HapticSkinMapper,
    ImuPose,
    WristbandLayout,
    _threshold_for_band,
    _values_from_threshold_mapping,
)
from hardware.wristband.firmware.openhear_firmware_v1 import (
    DEFAULT_ACTUATOR_COUNT,
    MAX_INTENSITY,
    THERMAL_DERATE_C,
    THERMAL_SHUTOFF_C,
    V0_COMPAT_PATTERN,
    HapticScheduler,
    NullHapticDriver,
    V1PacketCodec,
    main,
    process_packet,
)

# ===========================================================================
# openhear_firmware_v1
# ===========================================================================


class TestHapticSchedulerThermal:
    def test_normal_temperature_uses_full_intensity_cap(self):
        sched = HapticScheduler(NullHapticDriver())
        sched.set_temperature(25.0)
        assert sched.enabled is True
        assert sched.intensity_cap == MAX_INTENSITY

    def test_derate_temperature_halves_cap(self):
        sched = HapticScheduler(NullHapticDriver())
        sched.set_temperature(THERMAL_DERATE_C)
        assert sched.enabled is True
        assert sched.intensity_cap == MAX_INTENSITY // 2

    def test_shutoff_temperature_disables_and_clears_driver(self):
        driver = NullHapticDriver()
        sched = HapticScheduler(driver)
        sched.set_temperature(THERMAL_SHUTOFF_C + 0.1)
        assert sched.enabled is False
        # Driver should have received an all_off command.
        assert driver.log[-1] == (-1, 0, 0, 0)

    def test_recovery_after_shutoff(self):
        sched = HapticScheduler(NullHapticDriver())
        sched.set_temperature(45.0)
        assert sched.enabled is False
        sched.set_temperature(20.0)
        assert sched.enabled is True
        assert sched.intensity_cap == MAX_INTENSITY


class TestHapticSchedulerSubmit:
    def test_submit_events_when_disabled_drops_packets(self):
        driver = NullHapticDriver()
        sched = HapticScheduler(driver)
        sched.enabled = False
        sched.submit_events([(0, 200, 100, 30)])
        # Nothing routed to the driver.
        assert driver.log == []

    def test_submit_events_caps_intensity_and_wraps_index(self):
        driver = NullHapticDriver()
        sched = HapticScheduler(driver, actuator_count=8)
        sched.intensity_cap = 100
        sched.submit_events([(15, 200, 250, 0), (3, 180, -10, 5)])
        # Index 15 % 8 = 7, intensity capped at 100, duration min 1.
        assert driver.log[0] == (7, 200, 100, 1)
        # Negative intensity clamped to 0.
        assert driver.log[1] == (3, 180, 0, 5)


class TestSubmitV0Packet:
    def test_short_packet_ignored(self):
        driver = NullHapticDriver()
        sched = HapticScheduler(driver, actuator_count=24)
        sched.submit_v0_packet(b"\x00\x00")
        assert driver.log == []

    def test_pattern_zero_calls_all_off(self):
        driver = NullHapticDriver()
        sched = HapticScheduler(driver, actuator_count=24)
        sched.submit_v0_packet(bytes((1, 100, 0)))
        assert driver.log == [(-1, 0, 0, 0)]

    def test_intensity_zero_calls_all_off(self):
        driver = NullHapticDriver()
        sched = HapticScheduler(driver, actuator_count=24)
        sched.submit_v0_packet(bytes((1, 0, 4)))
        assert driver.log == [(-1, 0, 0, 0)]

    def test_compat_pattern_drives_two_actuators_for_multi_actuator_band(self):
        driver = NullHapticDriver()
        sched = HapticScheduler(driver, actuator_count=24)
        sched.submit_v0_packet(bytes((1, 80, V0_COMPAT_PATTERN)))
        # Expect two drive() calls: index 0 and index 12.
        assert driver.log[0] == (0, 180, 80, 40)
        assert driver.log[1] == (12, 180, 80, 40)

    def test_compat_pattern_single_actuator(self):
        driver = NullHapticDriver()
        sched = HapticScheduler(driver, actuator_count=1)
        sched.submit_v0_packet(bytes((1, 80, V0_COMPAT_PATTERN)))
        # Only the single actuator drive() is emitted.
        assert driver.log == [(0, 180, 80, 40)]

    @pytest.mark.parametrize("pattern_id", [1, 2, 6])
    def test_legacy_voice_pattern(self, pattern_id):
        driver = NullHapticDriver()
        sched = HapticScheduler(driver, actuator_count=24)
        sched.submit_v0_packet(bytes((1, 100, pattern_id)))
        # 2 drives @ frequency 160.
        assert len(driver.log) == 2
        assert driver.log[0][1] == 160
        assert driver.log[1][1] == 160

    def test_legacy_alarm_pattern(self):
        driver = NullHapticDriver()
        sched = HapticScheduler(driver, actuator_count=24)
        sched.submit_v0_packet(bytes((1, 100, 3)))
        assert len(driver.log) == 2
        assert driver.log[0][1] == 220
        assert driver.log[1][1] == 220

    def test_legacy_dog_pattern_right_only(self):
        driver = NullHapticDriver()
        sched = HapticScheduler(driver, actuator_count=24)
        sched.submit_v0_packet(bytes((1, 100, 4)))
        # Only right (index 12) is driven.
        assert len(driver.log) == 1
        assert driver.log[0][0] == 12

    def test_legacy_traffic_pattern_left_only(self):
        driver = NullHapticDriver()
        sched = HapticScheduler(driver, actuator_count=24)
        sched.submit_v0_packet(bytes((1, 100, 5)))
        assert len(driver.log) == 1
        assert driver.log[0][0] == 0


class TestV1PacketCodec:
    def test_decode_empty(self):
        assert V1PacketCodec.decode(b"") == ("none", None)

    def test_decode_v0(self):
        kind, data = V1PacketCodec.decode(bytes((ord("V"), 1, 80, 240)))
        assert kind == "v0"
        assert bytes(data) == bytes((1, 80, 240))

    def test_decode_config(self):
        kind, data = V1PacketCodec.decode(bytes((ord("C"), 64, 200)))
        assert kind == "config"
        assert data == {"actuator_count": 64, "intensity_cap": 200}

    def test_decode_unknown(self):
        kind, _ = V1PacketCodec.decode(bytes((ord("Z"), 1, 2)))
        assert kind == "unknown"

    def test_decode_short_v0_falls_through(self):
        # Less than 4 bytes for "V" should not be parsed as v0.
        kind, _ = V1PacketCodec.decode(bytes((ord("V"), 1)))
        assert kind == "unknown"


class TestProcessPacket:
    def test_config_updates_scheduler(self):
        sched = HapticScheduler(NullHapticDriver(), actuator_count=24)
        process_packet(sched, bytes((ord("C"), 64, 250)))
        assert sched.actuator_count == 64
        # MAX_INTENSITY caps the requested cap.
        assert sched.intensity_cap == min(MAX_INTENSITY, 250)

    def test_v0_routed_to_submit_v0(self):
        driver = NullHapticDriver()
        sched = HapticScheduler(driver, actuator_count=24)
        process_packet(sched, bytes((ord("V"), 1, 80, V0_COMPAT_PATTERN)))
        # At least one drive call.
        assert any(entry[0] >= 0 for entry in driver.log)

    def test_unknown_packet_is_noop(self):
        driver = NullHapticDriver()
        sched = HapticScheduler(driver)
        process_packet(sched, bytes((ord("Z"), 1, 2)))
        assert driver.log == []


def test_main_runs_without_errors():
    # main() is a placeholder; just ensure it doesn't raise.
    main()


def test_default_actuator_count_constant():
    assert DEFAULT_ACTUATOR_COUNT in (24, 64, 128)


# ===========================================================================
# haptic_mapper extras
# ===========================================================================


class TestWristbandLayout:
    def test_invalid_actuator_count_raises(self):
        with pytest.raises(ValueError):
            WristbandLayout(actuator_count=17)

    @pytest.mark.parametrize("count,rings", [(24, 1), (64, 4), (128, 8)])
    def test_default_ring_counts(self, count, rings):
        layout = WristbandLayout(actuator_count=count)
        assert layout.rings == rings
        assert layout.columns == count // rings

    def test_explicit_ring_count(self):
        layout = WristbandLayout(actuator_count=64, ring_count=2)
        assert layout.rings == 2
        assert layout.columns == 32

    def test_index_wraps(self):
        layout = WristbandLayout(actuator_count=24)
        assert layout.index(0, 0) == 0
        # ring wraps
        assert layout.index(layout.rings, 0) == 0
        # column wraps
        assert layout.index(0, layout.columns) == 0


class TestHapticSkinMapperCues:
    def test_render_bark_frame_empty_returns_empty(self):
        mapper = HapticSkinMapper()
        assert mapper.render_bark_frame([]) == []

    def test_render_spatial_cue_emits_five_actuators(self):
        mapper = HapticSkinMapper(WristbandLayout(actuator_count=64))
        events = mapper.render_spatial_cue(
            azimuth_deg=90,
            elevation_deg=0,
            distance_m=1.5,
            imu_pose=ImuPose(yaw_deg=10),
        )
        assert len(events) == 5
        # Intensities decrease across the funnel.
        intensities = [e.intensity for e in events]
        assert intensities[0] >= intensities[-1]

    def test_render_spatial_cue_unknown_pattern_falls_back(self):
        mapper = HapticSkinMapper()
        events = mapper.render_spatial_cue(
            azimuth_deg=0,
            elevation_deg=0,
            distance_m=1.0,
            pattern="unknown_pattern",
        )
        # Falls back to directional_speech.
        assert events
        assert events[0].pattern_id == COMMON_PATTERNS["directional_speech"]

    def test_v0_compat_packet_for_empty_events_is_zero(self):
        mapper = HapticSkinMapper()
        assert mapper.v0_compat_packet([]) == (0, 0, 0)

    def test_distance_decay_clamped(self):
        mapper = HapticSkinMapper()
        # At very large distance the decay is floored at 0.08.
        assert mapper.distance_decay(1000.0) == pytest.approx(0.08)
        # Very near distance returns the full 1.0.
        assert mapper.distance_decay(0.0) == pytest.approx(1.0)

    def test_band_to_drive_frequency_within_bounds(self):
        mapper = HapticSkinMapper()
        for band in range(len(BARK_BAND_CENTRES_HZ)):
            f = mapper.band_to_drive_frequency(band)
            assert 20 <= f <= 600

    def test_elevation_to_ring_clamps_to_layout(self):
        mapper = HapticSkinMapper(WristbandLayout(actuator_count=64))
        assert mapper.elevation_to_ring(-180.0) == 0
        assert mapper.elevation_to_ring(180.0) == mapper.layout.rings - 1


class TestThresholdHelpers:
    def test_no_audiogram_returns_default(self):
        assert _threshold_for_band(0, None) == 40.0
        assert _threshold_for_band(0, {}) == 40.0

    def test_audiogram_returns_band_value(self):
        ag = {"thresholds": {"left": {"500": 50, "1000": 70, "2000": 90}}}
        # Sorted by frequency: [50, 70, 90]. Band 1 should pick 70.
        assert _threshold_for_band(1, ag) == 70.0

    def test_audiogram_with_lists(self):
        ag = {"thresholds": {"left": [10, 20, 30, 40]}}
        assert _threshold_for_band(2, ag) == 30.0

    def test_audiogram_overflow_falls_back_to_last(self):
        ag = {"thresholds": {"left": {"500": 25}}}
        # band index out of range => last value used.
        assert _threshold_for_band(99, ag) == 25.0

    def test_values_from_threshold_mapping_handles_non_numeric_key(self):
        # Non-numeric keys still produce values, ordered by insertion.
        values = _values_from_threshold_mapping({"500": 10, "1000": 20})
        assert values == [10.0, 20.0]


class TestHapticMapperWeighting:
    def test_weight_band_increases_with_threshold(self):
        mapper = HapticSkinMapper()
        light = mapper._weight_band(0, 1.0, {"thresholds": {"left": [10]}})
        heavy = mapper._weight_band(0, 1.0, {"thresholds": {"left": [95]}})
        assert heavy > light

    def test_intensity_byte_clamps_to_zero_for_negative(self):
        mapper = HapticSkinMapper(comfort_scale=1.0)
        assert mapper._intensity_byte(-5) == 0

    def test_intensity_byte_clamps_to_255_for_overflow(self):
        mapper = HapticSkinMapper(comfort_scale=1.0)
        assert mapper._intensity_byte(2.0) == 255
