"""Tests for ``haptic_commander.py``."""

from __future__ import annotations

import asyncio

import pytest

import haptic_commander
from haptic_commander import HapticCommander


class _StubBleClient:
    def __init__(self):
        self.is_connected = False
        self.sent_packets = []
        self.connect_calls = 0
        self.disconnect_calls = 0

    async def connect(self, timeout=5.0):
        self.is_connected = True
        self.connect_calls += 1

    async def send_packet(self, packet):
        self.sent_packets.append(packet)

    async def disconnect(self):
        self.is_connected = False
        self.disconnect_calls += 1


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


def test_send_sound_skips_connect_when_already_connected(audiogram_path: str):
    """If the BLE client is already connected, ``send_sound`` should not reconnect."""
    ble_client = _StubBleClient()
    ble_client.is_connected = True
    commander = HapticCommander(audiogram_path, ble_client=ble_client)
    asyncio.run(commander.send_sound("doorbell"))
    assert ble_client.connect_calls == 0
    assert len(ble_client.sent_packets) == 1


def test_disconnect_delegates_to_ble_client(audiogram_path: str):
    ble_client = _StubBleClient()
    ble_client.is_connected = True
    commander = HapticCommander(audiogram_path, ble_client=ble_client)
    asyncio.run(commander.disconnect())
    assert ble_client.disconnect_calls == 1


def test_main_dry_run_prints_packet_without_ble(audiogram_path, monkeypatch, capsys):
    """``--dry-run`` must avoid connecting/sending and just print the packet."""
    stub = _StubBleClient()
    monkeypatch.setattr(haptic_commander, "OpenHearBLEClient", lambda: stub)
    monkeypatch.setattr(
        "sys.argv",
        [
            "haptic_commander",
            "--audiogram", audiogram_path,
            "--sound-class", "voice",
            "--dry-run",
        ],
    )
    haptic_commander.main()
    out = capsys.readouterr().out.strip()
    # voice sound_class_id is 1; the printed list begins accordingly.
    assert out.startswith("[1,")
    # Dry-run must not touch the BLE radio at all.
    assert stub.connect_calls == 0
    assert stub.sent_packets == []
    assert stub.disconnect_calls == 0


def test_main_full_path_uses_ble_client(audiogram_path, monkeypatch, capsys):
    """Without ``--dry-run`` the CLI must connect, send, and disconnect."""
    stub = _StubBleClient()
    monkeypatch.setattr(haptic_commander, "OpenHearBLEClient", lambda: stub)
    monkeypatch.setattr(
        "sys.argv",
        [
            "haptic_commander",
            "--audiogram", audiogram_path,
            "--sound-class", "alarm",
            "--scan-timeout", "0.1",
        ],
    )
    haptic_commander.main()

    assert stub.connect_calls == 1
    assert stub.disconnect_calls == 1
    assert len(stub.sent_packets) == 1
    out = capsys.readouterr().out.strip()
    assert out.startswith("[3,")


def test_main_rejects_unknown_sound_class(audiogram_path, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "haptic_commander",
            "--audiogram", audiogram_path,
            "--sound-class", "telephone",  # not in SUPPORTED_SOUND_CLASSES
        ],
    )
    with pytest.raises(SystemExit):
        haptic_commander.main()


def test_main_disconnects_even_on_send_failure(audiogram_path, monkeypatch):
    """If ``send_packet`` raises, the BLE link must still be closed."""
    class _ExplodingBle(_StubBleClient):
        async def send_packet(self, packet):
            raise RuntimeError("BLE link dropped")

    stub = _ExplodingBle()
    monkeypatch.setattr(haptic_commander, "OpenHearBLEClient", lambda: stub)
    monkeypatch.setattr(
        "sys.argv",
        [
            "haptic_commander",
            "--audiogram", audiogram_path,
            "--sound-class", "alarm",
            "--scan-timeout", "0.1",
        ],
    )
    with pytest.raises(RuntimeError):
        haptic_commander.main()
    assert stub.disconnect_calls == 1

