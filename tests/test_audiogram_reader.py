"""Tests for ``audiogram/reader.py``."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from audiogram import reader
from audiogram.reader import (
    CMD_GET_AUDIOGRAM,
    STANDARD_FREQUENCIES_HZ,
    main,
    parse_audiogram_response,
    read_audiogram,
)
from core.read_fitting import HID_REPORT_LENGTH


class _FakeHidDevice:
    def __init__(self, *, responses=None, write_return=HID_REPORT_LENGTH + 1):
        self._responses = list(responses or [])
        self._write_return = write_return
        self.writes = []
        self.closed = False
        self.opened = None
        self.nonblocking = None

    def open(self, vendor_id, product_id):
        self.opened = (vendor_id, product_id)

    def set_nonblocking(self, value):
        self.nonblocking = value

    def write(self, data):
        self.writes.append(bytes(data))
        return self._write_return

    def read(self, length, timeout_ms=0):
        if not self._responses:
            return []
        return list(self._responses.pop(0))

    def close(self):
        self.closed = True


# ── parse_audiogram_response ─────────────────────────────────────────────────


class TestParseAudiogramResponse:
    def test_returns_left_and_right_dicts(self):
        n = len(STANDARD_FREQUENCIES_HZ)
        # Bytes 0..1 are a placeholder header; left ear starts at byte 2.
        payload = bytes(2) + bytes(range(10, 10 + n)) + bytes(range(50, 50 + n))
        result = parse_audiogram_response(payload)
        assert set(result.keys()) == {"left", "right"}
        for ear in ("left", "right"):
            assert set(result[ear].keys()) == set(STANDARD_FREQUENCIES_HZ)
        # Spot-check one frequency per ear.
        assert result["left"][STANDARD_FREQUENCIES_HZ[0]] == 10.0
        assert result["right"][STANDARD_FREQUENCIES_HZ[0]] == 50.0

    def test_values_are_floats(self):
        payload = bytes([0xFF] * (2 + 2 * len(STANDARD_FREQUENCIES_HZ)))
        result = parse_audiogram_response(payload)
        for value in result["left"].values():
            assert isinstance(value, float)

    def test_short_payload_pads_with_zero(self):
        # Provide only the header — both ears should default to 0.0 dB HL.
        result = parse_audiogram_response(bytes(2))
        for ear in ("left", "right"):
            assert all(v == 0.0 for v in result[ear].values())

    def test_partial_payload_keeps_provided_values(self):
        n = len(STANDARD_FREQUENCIES_HZ)
        payload = bytes(2) + bytes([20, 30, 40])  # only 3 left thresholds
        result = parse_audiogram_response(payload)
        assert result["left"][STANDARD_FREQUENCIES_HZ[0]] == 20.0
        assert result["left"][STANDARD_FREQUENCIES_HZ[1]] == 30.0
        assert result["left"][STANDARD_FREQUENCIES_HZ[2]] == 40.0
        assert result["left"][STANDARD_FREQUENCIES_HZ[n - 1]] == 0.0


# ── read_audiogram ────────────────────────────────────────────────────────────


class TestReadAudiogram:
    def test_writes_command_and_returns_thresholds(self):
        n = len(STANDARD_FREQUENCIES_HZ)
        payload = bytes(2) + bytes([15] * n) + bytes([25] * n)
        device = _FakeHidDevice(responses=[payload])

        result = read_audiogram(device)

        # The first three command bytes are the audiogram opcode.
        assert device.writes[0][1:1 + len(CMD_GET_AUDIOGRAM)] == CMD_GET_AUDIOGRAM
        assert "timestamp" in result
        assert all(v == 15.0 for v in result["left"].values())
        assert all(v == 25.0 for v in result["right"].values())


# ── CLI ───────────────────────────────────────────────────────────────────────


class TestMainCli:
    def test_main_dumps_audiogram_to_json(self, tmp_path, monkeypatch, capsys):
        n = len(STANDARD_FREQUENCIES_HZ)
        payload = bytes(2) + bytes([10] * n) + bytes([20] * n)
        fake = _FakeHidDevice(responses=[payload])
        monkeypatch.setattr(reader, "open_device", lambda *a, **k: fake)

        out = tmp_path / "audiogram.json"
        monkeypatch.setattr(
            "sys.argv",
            ["audiogram.reader", "--output", str(out)],
        )
        main()

        printed = capsys.readouterr().out
        assert str(out) in printed
        data = json.loads(out.read_text(encoding="utf-8"))
        # JSON keys come back as strings — confirm both ears present.
        assert "left" in data
        assert "right" in data
        assert "timestamp" in data
        assert fake.closed is True

    def test_main_closes_device_when_read_fails(self, tmp_path, monkeypatch):
        fake = _FakeHidDevice(write_return=-1)
        monkeypatch.setattr(reader, "open_device", lambda *a, **k: fake)
        monkeypatch.setattr(
            "sys.argv",
            ["audiogram.reader", "--output", str(tmp_path / "x.json")],
        )
        with pytest.raises(IOError):
            main()
        assert fake.closed is True
