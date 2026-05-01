"""OpenHear wristband v1 firmware reference for RP2040/ESP32-S3 MicroPython.

Code licence: MIT OR Apache-2.0.

Latency budget for simple Bark energy -> haptic onset:
- PDM DMA half-buffer: 0.50 ms
- fixed 24-band energy update: 0.80 ms
- audiogram lookup + haptic render: 0.20 ms
- driver bus update: 0.80-1.60 ms depending on channel count
- LRA onset: 2.00-4.00 ms off-the-shelf, piezo future path <0.50 ms
Full YAMNet-class classification is a parallel scene tag, not the first-edge
safety path. The custom RISC-V Hearing NPU is the future route for sub-5 ms full
source separation/classification at wearable power.
"""

from __future__ import annotations

DEVICE_NAME = "OpenHear-v1"
DEFAULT_ACTUATOR_COUNT = 24
FRAME_US = 500
MAX_INTENSITY = 180
THERMAL_DERATE_C = 38.0
THERMAL_SHUTOFF_C = 40.0
V0_COMPAT_PATTERN = 240


class HapticScheduler:
    """Jitter-bounded event scheduler for actuator driver backends."""

    def __init__(self, driver, actuator_count: int = DEFAULT_ACTUATOR_COUNT) -> None:
        self.driver = driver
        self.actuator_count = actuator_count
        self.intensity_cap = MAX_INTENSITY
        self.enabled = True

    def set_temperature(self, skin_temp_c: float) -> None:
        if skin_temp_c >= THERMAL_SHUTOFF_C:
            self.enabled = False
            self.driver.all_off()
        elif skin_temp_c >= THERMAL_DERATE_C:
            self.intensity_cap = MAX_INTENSITY // 2
        else:
            self.enabled = True
            self.intensity_cap = MAX_INTENSITY

    def submit_events(self, events) -> None:
        if not self.enabled:
            return
        for event in events:
            index = int(event[0]) % self.actuator_count
            frequency_hz = int(event[1])
            intensity = min(self.intensity_cap, max(0, int(event[2])))
            duration_ms = max(1, int(event[3]))
            self.driver.drive(index, frequency_hz, intensity, duration_ms)

    def submit_v0_packet(self, packet: bytes | bytearray | tuple[int, int, int]) -> None:
        if len(packet) < 3:
            return
        intensity, pattern_id = int(packet[1]), int(packet[2])
        if pattern_id == 0 or intensity == 0:
            self.driver.all_off()
        elif pattern_id == V0_COMPAT_PATTERN:
            self.driver.drive(0, 180, min(intensity, self.intensity_cap), 40)
            if self.actuator_count > 1:
                self.driver.drive(self.actuator_count // 2, 180, min(intensity, self.intensity_cap), 40)
        else:
            self._legacy_pattern(pattern_id, intensity)

    def _legacy_pattern(self, pattern_id: int, intensity: int) -> None:
        left = 0
        right = max(1, self.actuator_count // 2)
        capped = min(intensity, self.intensity_cap)
        if pattern_id in (1, 2, 6):
            self.driver.drive(left, 160, capped, 80)
            self.driver.drive(right, 160, capped, 80)
        elif pattern_id == 3:
            self.driver.drive(left, 220, capped, 35)
            self.driver.drive(right, 220, capped, 35)
        elif pattern_id == 4:
            self.driver.drive(right, 120, capped, 120)
        elif pattern_id == 5:
            self.driver.drive(left, 120, capped, 160)


class NullHapticDriver:
    """Safe backend used for desktop tests and unported boards."""

    def __init__(self) -> None:
        self.log: list[tuple[int, int, int, int]] = []

    def drive(self, actuator_index: int, frequency_hz: int, intensity: int, duration_ms: int) -> None:
        self.log.append((actuator_index, frequency_hz, intensity, duration_ms))

    def all_off(self) -> None:
        self.log.append((-1, 0, 0, 0))


class V1PacketCodec:
    """BLE 5.3 companion protocol codec."""

    @staticmethod
    def decode(payload: bytes | bytearray) -> tuple[str, object]:
        if not payload:
            return ("none", None)
        packet_type = chr(payload[0])
        if packet_type == "V" and len(payload) >= 4:
            return ("v0", payload[1:4])
        if packet_type == "C" and len(payload) >= 3:
            return ("config", {"actuator_count": payload[1], "intensity_cap": payload[2]})
        if packet_type == "O":
            events = []
            for offset in range(1, len(payload) - 4, 5):
                index = payload[offset]
                frequency = payload[offset + 1] | (payload[offset + 2] << 8)
                intensity = payload[offset + 3]
                duration = payload[offset + 4]
                events.append((index, frequency, intensity, duration))
            return ("events", events)
        return ("unknown", payload)


def process_packet(scheduler: HapticScheduler, payload: bytes | bytearray) -> None:
    packet_type, data = V1PacketCodec.decode(payload)
    if packet_type == "events":
        scheduler.submit_events(data)
    elif packet_type == "v0":
        scheduler.submit_v0_packet(data)
    elif packet_type == "config" and isinstance(data, dict):
        scheduler.actuator_count = int(data["actuator_count"])
        scheduler.intensity_cap = min(MAX_INTENSITY, int(data["intensity_cap"]))


def main() -> None:
    """Board entry point placeholder for RP2040 PIO/DMA or ESP32-S3 I2S/PDM ports."""
    driver = NullHapticDriver()
    scheduler = HapticScheduler(driver)
    _ = scheduler


if __name__ == "__main__":
    main()
