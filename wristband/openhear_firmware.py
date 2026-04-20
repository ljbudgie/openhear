"""
Canonical OpenHear micro:bit v2 firmware entry point for the v1.0.0 wristband.

Expects 3-byte BLE UART packets:

    [sound_class_id, intensity_0_to_255, pattern_id]

Pins:
  - Left motor driver  -> P0
  - Right motor driver -> P1
"""

from microbit import display, pin0, pin1, sleep
import bluetooth
from bluetooth import UARTService


DEVICE_NAME = "OpenHear"
_ANALOG_MAX = 1023


def _scale_intensity(intensity_0_to_255):
    return int((max(0, min(255, intensity_0_to_255)) / 255) * _ANALOG_MAX)


def _motors(left, right, duration_ms):
    pin0.write_analog(_scale_intensity(left))
    pin1.write_analog(_scale_intensity(right))
    sleep(duration_ms)


def _off(duration_ms=0):
    pin0.write_analog(0)
    pin1.write_analog(0)
    if duration_ms:
        sleep(duration_ms)


def _pattern_silence(intensity):
    _off()


def _pattern_voice(intensity):
    for _ in range(3):
        _motors(intensity, intensity, 200)
        _off(100)


def _pattern_doorbell(intensity):
    for _ in range(2):
        _motors(intensity, intensity, 50)
        _off(50)


def _pattern_alarm(intensity):
    for step in range(8):
        if step % 2 == 0:
            _motors(intensity, 0, 30)
        else:
            _motors(0, intensity, 30)
        _off(30)


def _pattern_dog(intensity):
    _motors(0, intensity, 150)
    _off()


def _pattern_traffic(intensity):
    _motors(intensity, 0, 300)
    _off()


def _pattern_media(intensity):
    for _ in range(2):
        _motors(intensity, intensity, 500)
        _off(500)


PATTERNS = {
    0: _pattern_silence,
    1: _pattern_voice,
    2: _pattern_doorbell,
    3: _pattern_alarm,
    4: _pattern_dog,
    5: _pattern_traffic,
    6: _pattern_media,
}


def _advertise(uart):
    if hasattr(bluetooth, "set_advertisement"):
        try:
            bluetooth.set_advertisement(name=DEVICE_NAME, services=[uart])
            bluetooth.advertise(True)
            return
        except TypeError:
            pass

    if hasattr(uart, "start_advertising"):
        try:
            uart.start_advertising(advertise_name=DEVICE_NAME)
            return
        except TypeError:
            uart.start_advertising()
            return

    if hasattr(bluetooth, "advertise"):
        try:
            bluetooth.advertise(100000, uart)
        except TypeError:
            bluetooth.advertise(True)


def _read_packet(uart):
    if not uart.any():
        return None
    payload = uart.read(3)
    if not payload or len(payload) < 3:
        return None
    return payload[0], payload[1], payload[2]


def main():
    display.show("H")
    uart = UARTService()
    _advertise(uart)

    while True:
        packet = _read_packet(uart)
        if packet is None:
            _off()
            sleep(20)
            continue

        sound_class_id, intensity, pattern_id = packet
        handler = PATTERNS.get(pattern_id, _pattern_silence)
        handler(intensity)
        _off(20)


main()
