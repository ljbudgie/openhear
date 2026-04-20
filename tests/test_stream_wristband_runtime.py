"""Tests for ``stream/wristband_runtime.py``."""

from __future__ import annotations

import asyncio

import pytest

from stream.haptic_mapper import HapticMapper
from stream.wristband_runtime import WristbandRuntime, _run_manual


class _StubBleClient:
    def __init__(self):
        self.sent = []

    async def send_packet(self, packet):
        self.sent.append(packet)


def test_packet_from_classification(audiogram_path: str):
    runtime = WristbandRuntime(HapticMapper(audiogram_path), _StubBleClient())
    packet = runtime.packet_from_classification("dog", 0.5)
    assert list(packet.to_bytes()) == [4, 64, 4]


def test_send_scores_dispatches_packet_via_ble(audiogram_path: str):
    """``send_scores`` aggregates YAMNet-style scores and forwards over BLE."""
    client = _StubBleClient()
    runtime = WristbandRuntime(HapticMapper(audiogram_path), client)

    packet = asyncio.run(
        runtime.send_scores({"Doorbell": 0.9, "Music": 0.05})
    )

    assert client.sent == [packet]
    # Doorbell maps to OpenHear sound class id 2 (see haptic_mapper.SOUND_PROFILES).
    assert packet.to_bytes()[0] == 2


def test_send_scores_silence_when_below_confidence(audiogram_path: str):
    """Low-confidence frames should resolve to the silence packet."""
    client = _StubBleClient()
    runtime = WristbandRuntime(HapticMapper(audiogram_path), client)

    packet = asyncio.run(runtime.send_scores({"Speech": 0.05}))

    # The silence profile's sound_class_id is 0.
    assert packet.to_bytes()[0] == 0
    assert client.sent == [packet]


def test_run_manual_prints_packet_for_sound_class(audiogram_path, capsys):
    """The ``--manual-sound`` CLI branch builds a packet without BLE I/O."""
    args = type(
        "Args",
        (),
        {
            "audiogram": audiogram_path,
            "comfort_scale": 1.0,
            "ear_strategy": "worst",
            "sound_class": "alarm",
            "confidence": 1.0,
        },
    )()

    asyncio.run(_run_manual(args))

    out = capsys.readouterr().out.strip()
    # The printed list begins with the alarm sound class id (3).
    assert out.startswith("[3,")


def test_main_requires_model_and_labels_for_live_mode(audiogram_path, monkeypatch):
    """Without ``--manual-sound`` the CLI demands model + labels paths."""
    from stream import wristband_runtime

    monkeypatch.setattr(
        "sys.argv",
        ["wristband_runtime", "--audiogram", audiogram_path],
    )
    with pytest.raises(SystemExit):
        wristband_runtime.main()


def test_main_manual_branch_runs_without_ble(audiogram_path, monkeypatch, capsys):
    from stream import wristband_runtime

    monkeypatch.setattr(
        "sys.argv",
        [
            "wristband_runtime",
            "--audiogram", audiogram_path,
            "--manual-sound", "doorbell",
        ],
    )
    wristband_runtime.main()
    out = capsys.readouterr().out.strip()
    # Doorbell sound_class_id is 2.
    assert out.startswith("[2,")

