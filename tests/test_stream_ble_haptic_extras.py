"""Additional tests for ``stream/ble_haptic.py`` error paths."""

from __future__ import annotations

import asyncio
import importlib
import sys

import pytest

from stream import ble_haptic
from stream.ble_haptic import (
    HapticPacket,
    OpenHearBLEClient,
    _validate_uint8,
    encode_packet,
)


class TestValidateUint8:
    def test_rejects_non_int_type(self):
        with pytest.raises(TypeError, match="must be an integer"):
            _validate_uint8("intensity", 1.5)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            _validate_uint8("intensity", "12")  # type: ignore[arg-type]

    def test_rejects_negative_value(self):
        with pytest.raises(ValueError, match="range 0..255"):
            _validate_uint8("pattern_id", -1)

    def test_returns_value_unchanged_for_valid_input(self):
        assert _validate_uint8("x", 0) == 0
        assert _validate_uint8("x", 255) == 255


class TestEncodePacket:
    def test_encodes_to_three_bytes(self):
        assert encode_packet(0, 0, 0) == b"\x00\x00\x00"

    def test_rejects_invalid_intensity(self):
        with pytest.raises(ValueError, match="intensity"):
            encode_packet(1, 999, 1)


class TestHapticPacket:
    def test_to_bytes_round_trip(self):
        packet = HapticPacket(2, 200, 4)
        assert packet.to_bytes() == bytes((2, 200, 4))


# ---------------------------------------------------------------------------
# OpenHearBLEClient
# ---------------------------------------------------------------------------


class _Device:
    def __init__(self, name):
        self.name = name


class _ScannerOnlyOthers:
    @staticmethod
    async def discover(timeout: float):
        return [_Device("Random"), _Device("AnotherDevice")]


class _ScannerWithMatch:
    @staticmethod
    async def discover(timeout: float):
        return [_Device("Random"), _Device("OpenHear")]


class _Client:
    def __init__(self, device):
        self.device = device
        self.is_connected = False
        self.writes: list[tuple[str, bytes]] = []
        self.disconnected = False

    async def connect(self):
        self.is_connected = True

    async def write_gatt_char(self, uuid, data):
        self.writes.append((uuid, data))

    async def disconnect(self):
        self.is_connected = False
        self.disconnected = True


class TestOpenHearBLEClient:
    def test_send_packet_before_connect_raises(self):
        client = OpenHearBLEClient(scanner=_ScannerWithMatch,
                                   client_factory=lambda d: _Client(d))
        with pytest.raises(RuntimeError, match="not connected"):
            asyncio.run(client.send_packet(HapticPacket(0, 0, 0)))

    def test_is_connected_false_when_no_client(self):
        client = OpenHearBLEClient(scanner=_ScannerWithMatch,
                                   client_factory=lambda d: _Client(d))
        assert client.is_connected is False

    def test_discover_raises_when_device_missing(self):
        client = OpenHearBLEClient(scanner=_ScannerOnlyOthers,
                                   client_factory=lambda d: _Client(d))
        with pytest.raises(RuntimeError, match="Could not find"):
            asyncio.run(client.discover())

    def test_send_command_encodes_packet(self):
        fake = _Client(None)
        client = OpenHearBLEClient(scanner=_ScannerWithMatch,
                                   client_factory=lambda d: fake)
        asyncio.run(client.connect())
        asyncio.run(client.send_command(2, 100, 3))
        assert fake.writes[0][1] == bytes((2, 100, 3))

    def test_disconnect_resets_internal_client(self):
        fake = _Client(None)
        client = OpenHearBLEClient(scanner=_ScannerWithMatch,
                                   client_factory=lambda d: fake)
        asyncio.run(client.connect())
        assert client.is_connected is True
        asyncio.run(client.disconnect())
        assert client.is_connected is False
        assert fake.disconnected is True

    def test_disconnect_safe_when_never_connected(self):
        client = OpenHearBLEClient(scanner=_ScannerWithMatch,
                                   client_factory=lambda d: _Client(d))
        # Should not raise.
        asyncio.run(client.disconnect())


class TestRequireBleak:
    def test_raises_when_bleak_missing(self, monkeypatch):
        monkeypatch.setattr(ble_haptic, "BleakClient", None)
        monkeypatch.setattr(ble_haptic, "BleakScanner", None)
        with pytest.raises(RuntimeError, match="bleak"):
            ble_haptic._require_bleak()

    def test_does_not_raise_when_present(self, monkeypatch):
        monkeypatch.setattr(ble_haptic, "BleakClient", object)
        monkeypatch.setattr(ble_haptic, "BleakScanner", object)
        ble_haptic._require_bleak()
