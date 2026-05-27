from hardware.wristband.firmware.haptic_mapper import HapticSkinMapper, ImuPose, WristbandLayout
from hardware.wristband.firmware.openhear_firmware_v1 import (
    HapticScheduler,
    NullHapticDriver,
    V1PacketCodec,
    process_packet,
)


def test_v1_mapper_renders_bark_frame_and_v0_packet():
    mapper = HapticSkinMapper(WristbandLayout(actuator_count=64), comfort_scale=0.5)
    events = mapper.render_bark_frame(
        [0.0, 0.2, 0.8, 0.1],
        {"thresholds": {"left": {"500": 45}, "right": {"500": 70}}},
        ImuPose(yaw_deg=45),
        azimuth_deg=90,
        elevation_deg=45,
        distance_m=2.0,
        pattern="directional_speech",
    )

    assert events
    assert all(0 <= event.actuator_index < 64 for event in events)
    assert all(20 <= event.drive_frequency_hz <= 600 for event in events)
    assert mapper.v0_compat_packet(events)[2] == 240


def test_v1_packet_codec_and_scheduler_support_legacy_packet():
    driver = NullHapticDriver()
    scheduler = HapticScheduler(driver, actuator_count=24)

    kind, data = V1PacketCodec.decode(bytes([ord("O"), 3, 180, 0, 64, 20]))
    assert kind == "events"
    assert data == [(3, 180, 64, 20)]

    process_packet(scheduler, bytes([ord("O"), 3, 180, 0, 64, 20]))
    process_packet(scheduler, bytes([ord("V"), 1, 80, 240]))

    assert driver.log[0] == (3, 180, 64, 20)
    assert driver.log[1][0] == 0
    assert driver.log[2][0] == 12
