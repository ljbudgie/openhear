"""Tests for ``stream/wristband_runtime.py``."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from stream import wristband_runtime
from stream.ble_haptic import HapticPacket
from stream.haptic_mapper import HapticMapper
from stream.wristband_runtime import WristbandRuntime, main


class _FakeBLEClient:
    def __init__(self):
        self.sent: list[HapticPacket] = []

    async def send_packet(self, packet: HapticPacket) -> None:
        self.sent.append(packet)


def _make_runtime(audiogram_path: str) -> tuple[WristbandRuntime, _FakeBLEClient]:
    mapper = HapticMapper(audiogram_path)
    fake = _FakeBLEClient()
    return WristbandRuntime(mapper, fake), fake


class TestWristbandRuntime:
    def test_packet_from_classification_returns_haptic_packet(self, audiogram_path):
        runtime, _ = _make_runtime(audiogram_path)
        packet = runtime.packet_from_classification("voice", confidence=1.0)
        assert isinstance(packet, HapticPacket)
        assert packet.to_bytes() != b"\x00\x00\x00"

    def test_silence_yields_zero_intensity(self, audiogram_path):
        runtime, _ = _make_runtime(audiogram_path)
        packet = runtime.packet_from_classification("silence", confidence=1.0)
        # Silence has no dominant frequency => intensity byte is 0.
        assert packet.intensity == 0

    def test_send_scores_routes_through_mapper_and_ble(self, audiogram_path):
        runtime, fake = _make_runtime(audiogram_path)
        # A score map that should classify as 'voice'.
        scores = {"Speech": 0.9, "Dog bark": 0.05, "Silence": 0.05}
        packet = asyncio.run(runtime.send_scores(scores))
        assert isinstance(packet, HapticPacket)
        assert fake.sent == [packet]

    def test_send_scores_propagates_silence_for_empty_input(self, audiogram_path):
        runtime, fake = _make_runtime(audiogram_path)
        packet = asyncio.run(runtime.send_scores({}))
        assert fake.sent == [packet]


class TestManualRun:
    def test_run_manual_prints_packet_bytes(self, audiogram_path, capsys):
        # Build an args namespace as argparse would.
        class _Args:
            audiogram = audiogram_path
            comfort_scale = 1.0
            ear_strategy = "worst"
            sound_class = "voice"
            confidence = 1.0

        asyncio.run(wristband_runtime._run_manual(_Args()))
        out = capsys.readouterr().out.strip()
        # Expect a printed list of three integers in [0, 255].
        as_list = eval(out, {"__builtins__": {}})  # noqa: S307
        assert isinstance(as_list, list)
        assert len(as_list) == 3
        for value in as_list:
            assert 0 <= value <= 255


class TestMainCli:
    def test_manual_sound_path(self, audiogram_path, monkeypatch, capsys):
        monkeypatch.setattr(
            "sys.argv",
            ["wristband_runtime", "--audiogram", audiogram_path, "--manual-sound", "doorbell"],
        )
        # Should not require --model/--labels in manual mode.
        main()
        out = capsys.readouterr().out.strip()
        assert out.startswith("[") and out.endswith("]")

    def test_live_mode_requires_model_and_labels(self, audiogram_path, monkeypatch):
        monkeypatch.setattr(
            "sys.argv",
            ["wristband_runtime", "--audiogram", audiogram_path],
        )
        with pytest.raises(SystemExit):
            main()

    def test_invalid_ear_strategy_rejected(self, audiogram_path, monkeypatch):
        monkeypatch.setattr(
            "sys.argv",
            [
                "wristband_runtime",
                "--audiogram",
                audiogram_path,
                "--manual-sound",
                "voice",
                "--ear-strategy",
                "loud",
            ],
        )
        with pytest.raises(SystemExit):
            main()

    def test_invalid_manual_sound_rejected(self, audiogram_path, monkeypatch):
        monkeypatch.setattr(
            "sys.argv",
            ["wristband_runtime", "--audiogram", audiogram_path, "--manual-sound", "thunder"],
        )
        with pytest.raises(SystemExit):
            main()
