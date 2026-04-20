"""Tests for ``stream/ble_haptic.py``."""

from __future__ import annotations

import asyncio

import pytest

from stream.ble_haptic import (
    HapticPacket,
    OpenHearBLEClient,
    encode_packet,
)


class _FakeDevice:
    def __init__(self, name: str):
        self.name = name


class _FakeScanner:
    @staticmethod
    async def discover(timeout: float):
        return [_FakeDevice("Other"), _FakeDevice("OpenHear")]


class _FakeClient:
    def __init__(self, device):
        self.device = device
        self.is_connected = False
        self.writes: list[tuple[str, bytes]] = []

    async def connect(self):
        self.is_connected = True

    async def write_gatt_char(self, uuid: str, payload: bytes):
        self.writes.append((uuid, payload))

    async def disconnect(self):
        self.is_connected = False


def test_encode_packet():
    assert encode_packet(3, 255, 1) == b"\x03\xff\x01"


def test_encode_packet_rejects_invalid_values():
    with pytest.raises(ValueError, match="range 0..255"):
        encode_packet(256, 1, 1)


def test_client_connects_and_sends():
    fake_client = _FakeClient(None)
    client = OpenHearBLEClient(
        scanner=_FakeScanner,
        client_factory=lambda device: fake_client,
    )
    asyncio.run(client.connect())
    asyncio.run(client.send_packet(HapticPacket(1, 128, 4)))
    assert fake_client.writes[0][1] == b"\x01\x80\x04"
