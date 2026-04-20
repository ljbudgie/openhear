"""Tests for ``stream/wristband_runtime.py``."""

from __future__ import annotations

from stream.haptic_mapper import HapticMapper
from stream.wristband_runtime import WristbandRuntime


class _StubBleClient:
    async def send_packet(self, packet):  # pragma: no cover - not used here.
        self.packet = packet


def test_packet_from_classification(audiogram_path: str):
    runtime = WristbandRuntime(HapticMapper(audiogram_path), _StubBleClient())
    packet = runtime.packet_from_classification("dog", 0.5)
    assert list(packet.to_bytes()) == [4, 64, 4]
