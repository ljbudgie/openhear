"""Tests for ``haptic_commander.py``."""

from __future__ import annotations

import asyncio

from haptic_commander import HapticCommander


class _StubBleClient:
    def __init__(self):
        self.is_connected = False
        self.sent_packets = []

    async def connect(self, timeout=5.0):
        self.is_connected = True

    async def send_packet(self, packet):
        self.sent_packets.append(packet)

    async def disconnect(self):
        self.is_connected = False


def test_build_packet_uses_existing_mapper(audiogram_path: str):
    commander = HapticCommander(audiogram_path, ble_client=_StubBleClient())
    packet = commander.build_packet("dog", confidence=0.5)
    assert list(packet.to_bytes()) == [4, 64, 4]


def test_send_sound_uses_ble_transport(audiogram_path: str):
    ble_client = _StubBleClient()
    commander = HapticCommander(audiogram_path, ble_client=ble_client)
    packet = asyncio.run(commander.send_sound("alarm", timeout=1.0))
    assert ble_client.sent_packets == [packet]
    assert list(packet.to_bytes()) == [3, 255, 3]
