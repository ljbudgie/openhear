"""Tests for ``stream/virtual_cable.py``."""

from __future__ import annotations

import pytest

from stream import virtual_cable
from stream.virtual_cable import (
    VirtualCable,
    _is_virtual,
    best_virtual_cable,
    detect_virtual_cables,
    main,
)


# ---------------------------------------------------------------------------
# _is_virtual
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", [
    "VB-Audio Virtual Cable",
    "VB-Cable Output",
    "BlackHole 2ch",
    "Loopback Audio",
    "Voicemeeter Output",
    "Soundflower (2ch)",
    "openhear-virtual",
    "alsa_output.OpenHear-virtual.monitor",
    "null sink",
])
def test_is_virtual_positive(name):
    assert _is_virtual(name) is True


@pytest.mark.parametrize("name", [
    "Built-in Microphone",
    "Realtek HD",
    "USB Audio CODEC",
])
def test_is_virtual_negative(name):
    assert _is_virtual(name) is False


# ---------------------------------------------------------------------------
# detect_virtual_cables
# ---------------------------------------------------------------------------


class _FakePyAudio:
    def __init__(self, devices):
        self._devices = devices
        self.terminated = False

    def get_device_count(self):
        return len(self._devices)

    def get_device_info_by_index(self, i):
        return self._devices[i]

    def terminate(self):
        self.terminated = True


def test_detect_virtual_cables_finds_input_and_output():
    devices = [
        {"name": "VB-Cable", "maxOutputChannels": 2,
         "maxInputChannels": 2, "defaultSampleRate": 48000.0},
        {"name": "Built-in", "maxOutputChannels": 2,
         "maxInputChannels": 0, "defaultSampleRate": 48000.0},
        {"name": "alsa_output.openhear.monitor", "maxOutputChannels": 0,
         "maxInputChannels": 1, "defaultSampleRate": 16000.0},
    ]
    pa = _FakePyAudio(devices)
    cables = detect_virtual_cables(pa=pa)
    # VB-Cable has both directions => 2 entries; monitor is input only.
    assert len(cables) == 3
    directions = sorted(c.direction for c in cables)
    assert directions == ["input", "input", "output"]
    # Caller-provided pa must NOT be terminated.
    assert pa.terminated is False


def test_detect_virtual_cables_terminates_owned_pa(monkeypatch):
    pa = _FakePyAudio([])
    monkeypatch.setattr(virtual_cable.pyaudio, "PyAudio", lambda: pa)
    detect_virtual_cables()
    assert pa.terminated is True


# ---------------------------------------------------------------------------
# best_virtual_cable ranking
# ---------------------------------------------------------------------------


class TestBestVirtualCable:
    def test_returns_none_when_empty(self):
        assert best_virtual_cable("input", cables=[]) is None

    def test_returns_none_when_no_match_for_direction(self):
        cables = [VirtualCable(0, "VB-Cable", "input", 48000.0)]
        assert best_virtual_cable("output", cables=cables) is None

    def test_invalid_direction_raises(self):
        with pytest.raises(ValueError):
            best_virtual_cable("nope", cables=[])

    def test_prefers_vb_cable_over_blackhole(self):
        cables = [
            VirtualCable(1, "BlackHole", "output", 48000.0),
            VirtualCable(2, "VB-Cable Out", "output", 48000.0),
            VirtualCable(3, "Voicemeeter VAIO", "output", 48000.0),
        ]
        pick = best_virtual_cable("output", cables=cables)
        assert pick.name == "VB-Cable Out"

    def test_prefers_blackhole_over_voicemeeter(self):
        cables = [
            VirtualCable(1, "Voicemeeter VAIO", "output", 48000.0),
            VirtualCable(2, "BlackHole", "output", 48000.0),
        ]
        pick = best_virtual_cable("output", cables=cables)
        assert pick.name == "BlackHole"

    def test_prefers_voicemeeter_over_openhear(self):
        cables = [
            VirtualCable(1, "openhear-virtual", "output", 48000.0),
            VirtualCable(2, "Voicemeeter VAIO", "output", 48000.0),
        ]
        pick = best_virtual_cable("output", cables=cables)
        assert pick.name == "Voicemeeter VAIO"

    def test_unknown_falls_to_default_rank(self):
        cables = [
            VirtualCable(1, "weird-bridge", "input", 48000.0),
            VirtualCable(2, "VB-Cable", "input", 48000.0),
        ]
        pick = best_virtual_cable("input", cables=cables)
        assert pick.name == "VB-Cable"

    def test_uses_detect_when_no_cables_given(self, monkeypatch):
        monkeypatch.setattr(
            virtual_cable, "detect_virtual_cables",
            lambda: [VirtualCable(7, "VB-Cable", "input", 48000.0)],
        )
        pick = best_virtual_cable("input")
        assert pick.index == 7


# ---------------------------------------------------------------------------
# CLI main()
# ---------------------------------------------------------------------------


class TestMainCli:
    def test_list_with_no_cables_prints_help_message(self, monkeypatch, capsys):
        monkeypatch.setattr(virtual_cable, "detect_virtual_cables", lambda: [])
        rc = main(["--list"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "No virtual audio cables detected" in out

    def test_list_prints_table(self, monkeypatch, capsys):
        monkeypatch.setattr(
            virtual_cable, "detect_virtual_cables",
            lambda: [
                VirtualCable(1, "VB-Cable", "output", 48000.0),
                VirtualCable(2, "BlackHole", "input", 48000.0),
            ],
        )
        rc = main(["--list"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "VB-Cable" in out
        assert "BlackHole" in out

    def test_best_returns_index(self, monkeypatch, capsys):
        monkeypatch.setattr(
            virtual_cable, "detect_virtual_cables",
            lambda: [VirtualCable(9, "VB-Cable", "output", 48000.0)],
        )
        rc = main(["--best", "output"])
        assert rc == 0
        assert capsys.readouterr().out.strip() == "9"

    def test_best_returns_failure_when_missing(self, monkeypatch, capsys):
        monkeypatch.setattr(virtual_cable, "detect_virtual_cables", lambda: [])
        rc = main(["--best", "input"])
        err = capsys.readouterr().err
        assert rc == 1
        assert "No virtual input cable" in err

    def test_requires_one_action(self):
        with pytest.raises(SystemExit):
            main([])
