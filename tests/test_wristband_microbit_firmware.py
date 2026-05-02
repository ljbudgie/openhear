"""Tests for the MicroPython micro:bit wristband firmware modules.

The firmware modules ``wristband.openhear_firmware`` and
``hardware.wristband.firmware`` are written for the BBC micro:bit's
MicroPython runtime and import ``bluetooth`` / ``microbit``, which are
not available on standard CPython.  We install lightweight stubs so
these modules can be imported and their pure helpers exercised here.
"""

from __future__ import annotations

import importlib
import os as _os
import sys
import types
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# MicroPython stubs (installed once on import).
# ---------------------------------------------------------------------------


class _FakePin:
    def __init__(self):
        self.values: list[int] = []

    def write_analog(self, value: int) -> None:
        self.values.append(int(value))


class _FakeUART:
    def __init__(self):
        self.queued: list[bytes] = []
        self.advertised = False
        self.advertised_name: str | None = None

    def any(self) -> bool:
        return bool(self.queued)

    def read(self, n: int) -> bytes:
        if not self.queued:
            return b""
        payload = self.queued.pop(0)
        return payload[:n]

    # used by some firmware codepaths
    def start_advertising(self, advertise_name: str | None = None) -> None:
        self.advertised = True
        self.advertised_name = advertise_name


def _install_microbit_stubs() -> tuple[_FakePin, _FakePin]:
    pin0 = _FakePin()
    pin1 = _FakePin()

    # Provide deterministic sleep; tests don't actually wait.
    def _sleep(_ms: int) -> None:
        return None

    class _Display:
        def __init__(self):
            self.shown: list[Any] = []

        def show(self, value):
            self.shown.append(value)

    microbit = types.ModuleType("microbit")
    microbit.pin0 = pin0
    microbit.pin1 = pin1
    microbit.sleep = _sleep
    microbit.display = _Display()
    sys.modules["microbit"] = microbit

    bluetooth = types.ModuleType("bluetooth")

    class _UARTService(_FakeUART):
        pass

    def _set_advertisement(name=None, services=None):  # noqa: ARG001
        pass

    def _advertise(*_args, **_kwargs):
        pass

    bluetooth.UARTService = _UARTService
    bluetooth.set_advertisement = _set_advertisement
    bluetooth.advertise = _advertise
    sys.modules["bluetooth"] = bluetooth
    return pin0, pin1


_PIN0, _PIN1 = _install_microbit_stubs()


# The two firmware modules call ``main()`` at module load (because that is
# what the micro:bit's MicroPython runtime expects).  ``main()`` is an
# infinite ``while True`` loop, so we cannot simply ``import`` them in a
# unit test.  Instead, we load the source, strip the trailing top-level
# ``main()`` call, and exec the rest into a fresh module namespace.
def _load_firmware_module(module_name: str, source_path: str) -> types.ModuleType:
    with open(source_path, "r", encoding="utf-8") as fh:
        source = fh.read()
    # Remove the bare top-level ``main()`` invocation that runs the
    # blocking event loop on the device.
    sanitised_lines = [
        line for line in source.splitlines()
        if line.strip() != "main()"
    ]
    module = types.ModuleType(module_name)
    module.__file__ = source_path
    code = compile("\n".join(sanitised_lines), source_path, "exec")
    exec(code, module.__dict__)
    sys.modules[module_name] = module
    return module


_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
firmware_canonical = _load_firmware_module(
    "wristband.openhear_firmware",
    _os.path.join(_REPO_ROOT, "wristband", "openhear_firmware.py"),
)
firmware_legacy = _load_firmware_module(
    "hardware.wristband.firmware",
    _os.path.join(_REPO_ROOT, "hardware", "wristband", "firmware.py"),
)


# ---------------------------------------------------------------------------
# Shared parametrised tests for both firmware copies.
# ---------------------------------------------------------------------------


FIRMWARES = [firmware_canonical, firmware_legacy]


@pytest.mark.parametrize("firmware", FIRMWARES)
class TestScaleIntensity:
    def test_zero(self, firmware):
        assert firmware._scale_intensity(0) == 0

    def test_max(self, firmware):
        assert firmware._scale_intensity(255) == firmware._ANALOG_MAX

    def test_clamps_high(self, firmware):
        assert firmware._scale_intensity(999) == firmware._ANALOG_MAX

    def test_clamps_low(self, firmware):
        assert firmware._scale_intensity(-50) == 0

    def test_midpoint(self, firmware):
        # 128/255 ≈ 0.5019; * 1023 ≈ 513
        assert firmware._scale_intensity(128) == int((128 / 255) * firmware._ANALOG_MAX)


@pytest.mark.parametrize("firmware", FIRMWARES)
class TestPatterns:
    def test_pattern_silence_keeps_pins_off(self, firmware):
        _PIN0.values.clear(); _PIN1.values.clear()
        firmware._pattern_silence(200)
        # _off writes 0 to both
        assert _PIN0.values == [0]
        assert _PIN1.values == [0]

    def test_pattern_voice_pulses_three_times(self, firmware):
        _PIN0.values.clear(); _PIN1.values.clear()
        firmware._pattern_voice(255)
        # 3 motor pulses + 3 _off calls => 6 writes per pin
        assert len(_PIN0.values) == 6
        assert len(_PIN1.values) == 6
        # alternating pattern: [on, off, on, off, on, off]
        assert _PIN0.values[0::2] == [firmware._ANALOG_MAX] * 3
        assert _PIN0.values[1::2] == [0] * 3

    def test_pattern_doorbell(self, firmware):
        _PIN0.values.clear(); _PIN1.values.clear()
        firmware._pattern_doorbell(128)
        # 2 pulses
        assert len(_PIN0.values) == 4

    def test_pattern_alarm_alternates_left_right(self, firmware):
        _PIN0.values.clear(); _PIN1.values.clear()
        firmware._pattern_alarm(255)
        # 8 steps each producing 1 motor write + 1 off write per pin.
        assert len(_PIN0.values) == 16
        # Even steps drive left only, odd steps drive right only.
        on_writes_left = _PIN0.values[0::2]
        on_writes_right = _PIN1.values[0::2]
        # First write: even step -> left on, right off
        assert on_writes_left[0] == firmware._ANALOG_MAX
        assert on_writes_right[0] == 0
        # Second write: odd step -> left off, right on
        assert on_writes_left[1] == 0
        assert on_writes_right[1] == firmware._ANALOG_MAX

    def test_pattern_dog_drives_right_only(self, firmware):
        _PIN0.values.clear(); _PIN1.values.clear()
        firmware._pattern_dog(255)
        # _motors then _off => 2 writes per pin
        assert _PIN0.values == [0, 0]
        assert _PIN1.values == [firmware._ANALOG_MAX, 0]

    def test_pattern_traffic_drives_left_only(self, firmware):
        _PIN0.values.clear(); _PIN1.values.clear()
        firmware._pattern_traffic(255)
        assert _PIN0.values == [firmware._ANALOG_MAX, 0]
        assert _PIN1.values == [0, 0]

    def test_pattern_media(self, firmware):
        _PIN0.values.clear(); _PIN1.values.clear()
        firmware._pattern_media(255)
        # 2 pulses, 4 writes per pin.
        assert len(_PIN0.values) == 4

    def test_patterns_table_has_all_seven(self, firmware):
        assert set(firmware.PATTERNS.keys()) == set(range(7))
        for handler in firmware.PATTERNS.values():
            assert callable(handler)


@pytest.mark.parametrize("firmware", FIRMWARES)
class TestReadPacket:
    def test_returns_none_when_no_data(self, firmware):
        uart = _FakeUART()
        assert firmware._read_packet(uart) is None

    def test_returns_none_for_short_packet(self, firmware):
        uart = _FakeUART()
        uart.queued.append(b"\x01\x02")
        assert firmware._read_packet(uart) is None

    def test_returns_three_byte_tuple(self, firmware):
        uart = _FakeUART()
        uart.queued.append(b"\x03\x80\x02")
        assert firmware._read_packet(uart) == (3, 128, 2)


@pytest.mark.parametrize("firmware", FIRMWARES)
class TestAdvertise:
    def test_uses_bluetooth_set_advertisement(self, firmware):
        uart = _FakeUART()
        # set_advertisement and advertise are no-ops here; just verify no error.
        firmware._advertise(uart)

    def test_falls_back_to_uart_start_advertising(self, firmware, monkeypatch):
        # Strip the bluetooth.set_advertisement helper so the next branch fires.
        bt = sys.modules["bluetooth"]
        monkeypatch.delattr(bt, "set_advertisement", raising=False)
        uart = _FakeUART()
        firmware._advertise(uart)
        assert uart.advertised is True
        assert uart.advertised_name == firmware.DEVICE_NAME

    def test_falls_back_to_bluetooth_advertise(self, firmware, monkeypatch):
        bt = sys.modules["bluetooth"]
        monkeypatch.delattr(bt, "set_advertisement", raising=False)

        # UART without start_advertising, forcing the third branch.
        class _NoAdvertUart:
            pass

        called = {"count": 0}

        def _adv(*args, **kwargs):  # noqa: ARG001
            called["count"] += 1

        monkeypatch.setattr(bt, "advertise", _adv)
        firmware._advertise(_NoAdvertUart())
        assert called["count"] == 1
