"""Tests for ``stream/bluetooth_output.py``."""

from __future__ import annotations

import logging
from unittest.mock import patch

import numpy as np
import pytest

from stream import bluetooth_output


# ---------------------------------------------------------------------------
# is_likely_bluetooth_device
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", [
    "Phonak Marvel BT Headset",
    "Signia Insio AX",
    "Bluetooth Audio Device",
    "OTICON More 1",
    "ReSound Naida",
    "AUDEO P90",
])
def test_is_likely_bluetooth_device_positive(name):
    assert bluetooth_output.is_likely_bluetooth_device(name) is True


@pytest.mark.parametrize("name", [
    "Realtek HD Audio",
    "USB Microphone",
    "Built-in Output",
])
def test_is_likely_bluetooth_device_negative(name):
    assert bluetooth_output.is_likely_bluetooth_device(name) is False


# ---------------------------------------------------------------------------
# resample_to
# ---------------------------------------------------------------------------


class TestResampleTo:
    def test_same_rate_returns_input(self):
        x = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        out = bluetooth_output.resample_to(x, 16_000, 16_000)
        np.testing.assert_array_equal(out, x)
        assert out.dtype == np.float32

    def test_empty_array_returns_empty(self):
        x = np.zeros(0, dtype=np.float32)
        out = bluetooth_output.resample_to(x, 16_000, 48_000)
        assert out.size == 0

    def test_upsample_doubles_length(self):
        x = np.linspace(0.0, 1.0, 100, dtype=np.float32)
        out = bluetooth_output.resample_to(x, 16_000, 48_000)
        # 100 * 3 = 300 samples expected
        assert out.size == 300
        assert out.dtype == np.float32
        # End points preserved exactly.
        assert abs(out[0] - x[0]) < 1e-5
        assert abs(out[-1] - x[-1]) < 1e-5

    def test_downsample_halves_length(self):
        x = np.linspace(0.0, 1.0, 100, dtype=np.float32)
        out = bluetooth_output.resample_to(x, 48_000, 16_000)
        assert out.size == 33  # round(100 * 1/3)

    def test_invalid_rate_raises(self):
        x = np.zeros(4, dtype=np.float32)
        with pytest.raises(ValueError):
            bluetooth_output.resample_to(x, 0, 16_000)
        with pytest.raises(ValueError):
            bluetooth_output.resample_to(x, 16_000, -1)

    def test_tiny_input_handled(self):
        x = np.array([0.5], dtype=np.float32)
        out = bluetooth_output.resample_to(x, 16_000, 48_000)
        assert out.size >= 1


# ---------------------------------------------------------------------------
# list_output_devices / _print_device_table
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

    def open(self, *args, **kwargs):
        raise RuntimeError("not used")


def _devices_fixture():
    return [
        {"name": "Built-in Output", "maxOutputChannels": 2,
         "maxInputChannels": 0, "defaultSampleRate": 48000.0},
        {"name": "Built-in Microphone", "maxOutputChannels": 0,
         "maxInputChannels": 1, "defaultSampleRate": 48000.0},
        {"name": "Phonak Marvel Bluetooth", "maxOutputChannels": 2,
         "maxInputChannels": 0, "defaultSampleRate": 16000.0},
    ]


class TestListOutputDevices:
    def test_filters_input_only_devices(self):
        pa = _FakePyAudio(_devices_fixture())
        devices = bluetooth_output.list_output_devices(pa=pa)
        # The microphone should be skipped.
        assert len(devices) == 2
        names = [d["name"] for d in devices]
        assert "Built-in Microphone" not in names

    def test_marks_likely_bluetooth(self):
        pa = _FakePyAudio(_devices_fixture())
        devices = bluetooth_output.list_output_devices(pa=pa)
        marker = {d["name"]: d["likely_bluetooth"] for d in devices}
        assert marker["Phonak Marvel Bluetooth"] is True
        assert marker["Built-in Output"] is False

    def test_terminates_owned_pa(self):
        captured = {}

        def _factory():
            pa = _FakePyAudio(_devices_fixture())
            captured["pa"] = pa
            return pa

        with patch.object(bluetooth_output.pyaudio, "PyAudio", _factory):
            bluetooth_output.list_output_devices()
        assert captured["pa"].terminated is True

    def test_does_not_terminate_caller_owned_pa(self):
        pa = _FakePyAudio(_devices_fixture())
        bluetooth_output.list_output_devices(pa=pa)
        assert pa.terminated is False


def test_print_device_table_renders_rows(capsys):
    devices = [
        {"index": 0, "name": "Built-in Output", "max_output_channels": 2,
         "default_sample_rate": 48000.0, "likely_bluetooth": False},
        {"index": 3, "name": "Phonak Bluetooth Headset", "max_output_channels": 2,
         "default_sample_rate": 16000.0, "likely_bluetooth": True},
    ]
    bluetooth_output._print_device_table(devices, bluetooth_only=False)
    out = capsys.readouterr().out
    assert "Built-in Output" in out
    assert "Phonak Bluetooth Headset" in out
    assert "✓" in out


def test_print_device_table_bluetooth_only(capsys):
    devices = [
        {"index": 0, "name": "Built-in Output", "max_output_channels": 2,
         "default_sample_rate": 48000.0, "likely_bluetooth": False},
        {"index": 3, "name": "Phonak BT", "max_output_channels": 2,
         "default_sample_rate": 16000.0, "likely_bluetooth": True},
    ]
    bluetooth_output._print_device_table(devices, bluetooth_only=True)
    out = capsys.readouterr().out
    assert "Built-in Output" not in out
    assert "Phonak BT" in out


# ---------------------------------------------------------------------------
# BluetoothAudioOutput
# ---------------------------------------------------------------------------


class _FakeStream:
    def __init__(self):
        self.opened_with: dict = {}
        self.writes: list[bytes] = []
        self.stopped = False
        self.closed = False

    def write(self, payload: bytes) -> None:
        self.writes.append(payload)

    def stop_stream(self) -> None:
        self.stopped = True

    def close(self) -> None:
        self.closed = True


class _FakePyAudioWithStream:
    def __init__(self, devices=None, raise_on_open: Exception | None = None):
        self._devices = devices or []
        self.streams: list[_FakeStream] = []
        self.terminated = False
        self.opened_with = None
        self._raise = raise_on_open

    def open(self, **kwargs):
        if self._raise is not None:
            raise self._raise
        self.opened_with = kwargs
        s = _FakeStream()
        self.streams.append(s)
        return s

    def terminate(self):
        self.terminated = True

    def get_device_count(self):
        return len(self._devices)

    def get_device_info_by_index(self, i):
        return self._devices[i]


@pytest.fixture
def patched_pyaudio(monkeypatch):
    pa = _FakePyAudioWithStream()
    monkeypatch.setattr(bluetooth_output.pyaudio, "PyAudio", lambda: pa)
    return pa


class TestBluetoothAudioOutput:
    def test_open_write_close_cycle(self, patched_pyaudio):
        bt = bluetooth_output.BluetoothAudioOutput(
            sample_rate=16_000, channels=2, frames_per_buffer=128, device_index=4
        )
        bt.open()
        assert patched_pyaudio.opened_with["rate"] == 16_000
        assert patched_pyaudio.opened_with["channels"] == 2
        assert patched_pyaudio.opened_with["output_device_index"] == 4

        bt.write(b"\x01\x02\x03\x04")
        assert patched_pyaudio.streams[0].writes == [b"\x01\x02\x03\x04"]

        bt.close()
        assert patched_pyaudio.streams[0].stopped is True
        assert patched_pyaudio.streams[0].closed is True
        assert patched_pyaudio.terminated is True

    def test_write_before_open_raises(self, patched_pyaudio):
        bt = bluetooth_output.BluetoothAudioOutput(sample_rate=16_000)
        with pytest.raises(RuntimeError, match="not open"):
            bt.write(b"\x00")

    def test_open_wraps_oserror(self, monkeypatch):
        pa = _FakePyAudioWithStream(raise_on_open=OSError("device busy"))
        monkeypatch.setattr(bluetooth_output.pyaudio, "PyAudio", lambda: pa)
        bt = bluetooth_output.BluetoothAudioOutput(sample_rate=16_000, device_index=2)
        with pytest.raises(OSError, match="Cannot open Bluetooth output device"):
            bt.open()

    def test_close_is_idempotent_when_unopened(self, patched_pyaudio):
        bt = bluetooth_output.BluetoothAudioOutput(sample_rate=16_000)
        # Should terminate PyAudio without raising.
        bt.close()
        assert patched_pyaudio.terminated is True

    def test_context_manager(self, patched_pyaudio):
        bt = bluetooth_output.BluetoothAudioOutput(sample_rate=16_000)
        with bt as opened:
            opened.write(b"\x00\x00")
        assert patched_pyaudio.streams[0].closed is True
        assert patched_pyaudio.terminated is True

    def test_device_name_hint_resolves_index(self, monkeypatch, caplog):
        pa = _FakePyAudioWithStream(devices=[
            {"name": "Built-in", "maxOutputChannels": 2,
             "maxInputChannels": 0, "defaultSampleRate": 48000.0},
            {"name": "Phonak Naida BT", "maxOutputChannels": 2,
             "maxInputChannels": 0, "defaultSampleRate": 16000.0},
        ])
        monkeypatch.setattr(bluetooth_output.pyaudio, "PyAudio", lambda: pa)
        bt = bluetooth_output.BluetoothAudioOutput(
            sample_rate=16_000, device_name_hint="phonak"
        )
        bt.open()
        assert pa.opened_with["output_device_index"] == 1

    def test_device_name_hint_not_found_logs_warning(self, monkeypatch, caplog):
        pa = _FakePyAudioWithStream(devices=[
            {"name": "Built-in", "maxOutputChannels": 2,
             "maxInputChannels": 0, "defaultSampleRate": 48000.0},
        ])
        monkeypatch.setattr(bluetooth_output.pyaudio, "PyAudio", lambda: pa)
        with caplog.at_level(logging.WARNING):
            bt = bluetooth_output.BluetoothAudioOutput(
                sample_rate=16_000, device_name_hint="missing"
            )
        assert any("missing" in r.message and "fallback" in r.message.lower() or
                   "missing" in r.message and "default" in r.message.lower()
                   for r in caplog.records)
        # When not found, default (None) is used.
        bt.open()
        assert pa.opened_with["output_device_index"] is None


# ---------------------------------------------------------------------------
# CLI main()
# ---------------------------------------------------------------------------


class TestMainCli:
    def test_list_command(self, monkeypatch, capsys):
        pa = _FakePyAudio(_devices_fixture())
        monkeypatch.setattr(bluetooth_output.pyaudio, "PyAudio", lambda: pa)
        rc = bluetooth_output.main(["--list"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Phonak Marvel Bluetooth" in out
        assert "Built-in Output" in out

    def test_list_bluetooth_only(self, monkeypatch, capsys):
        pa = _FakePyAudio(_devices_fixture())
        monkeypatch.setattr(bluetooth_output.pyaudio, "PyAudio", lambda: pa)
        rc = bluetooth_output.main(["--list", "--bluetooth-only"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Phonak" in out
        assert "Built-in Output" not in out

    def test_device_index_plays_silence(self, monkeypatch, capsys):
        pa = _FakePyAudioWithStream()
        monkeypatch.setattr(bluetooth_output.pyaudio, "PyAudio", lambda: pa)
        rc = bluetooth_output.main(["--device-index", "2"])
        assert rc == 0
        # ~1 second of silence => 16000/256 = 62 buffers
        assert len(pa.streams) == 1
        assert len(pa.streams[0].writes) == int(16_000 / 256)

    def test_requires_one_of_list_or_device(self):
        with pytest.raises(SystemExit):
            bluetooth_output.main([])
