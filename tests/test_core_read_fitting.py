"""Tests for ``core/read_fitting.py``.

The module talks to the Noahlink Wireless 2 USB programmer via the
``hid`` library.  These tests exercise the pure-Python plumbing
(framing, parsing, JSON export, CLI) by injecting a fake HID device
that records writes and replays canned reads.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from core import read_fitting
from core.read_fitting import (
    CMD_GET_FITTING,
    HID_REPORT_LENGTH,
    NOAHLINK_PRODUCT_ID,
    NOAHLINK_VENDOR_ID,
    _utc_now_iso,
    export_json,
    main,
    open_device,
    read_fitting_data,
    read_response,
    send_command,
)


class _FakeHidDevice:
    """In-memory HID device stand-in for tests."""

    def __init__(
        self,
        *,
        responses: list[bytes] | None = None,
        write_return: int = HID_REPORT_LENGTH + 1,
        open_error: Exception | None = None,
    ) -> None:
        self._responses = list(responses or [])
        self._write_return = write_return
        self._open_error = open_error
        self.opened: tuple[int, int] | None = None
        self.nonblocking: bool | None = None
        self.writes: list[bytes] = []
        self.read_calls: list[tuple[int, int]] = []
        self.closed = False

    def open(self, vendor_id: int, product_id: int) -> None:
        if self._open_error is not None:
            raise self._open_error
        self.opened = (vendor_id, product_id)

    def set_nonblocking(self, value: bool) -> None:
        self.nonblocking = value

    def write(self, data) -> int:
        self.writes.append(bytes(data))
        return self._write_return

    def read(self, length: int, timeout_ms: int = 0):
        self.read_calls.append((length, timeout_ms))
        if not self._responses:
            return []
        return list(self._responses.pop(0))

    def close(self) -> None:
        self.closed = True


# ── send_command ──────────────────────────────────────────────────────────────


class TestSendCommand:
    def test_pads_command_to_report_length_plus_one(self):
        device = _FakeHidDevice()
        send_command(device, CMD_GET_FITTING)
        assert len(device.writes) == 1
        report = device.writes[0]
        assert len(report) == HID_REPORT_LENGTH + 1
        # Leading byte is the HID report ID (0x00 on Windows).
        assert report[0] == 0x00
        # The payload begins immediately after the report ID byte.
        assert report[1:1 + len(CMD_GET_FITTING)] == CMD_GET_FITTING

    def test_truncates_oversized_command(self):
        device = _FakeHidDevice()
        oversized = bytes([0xAB] * (HID_REPORT_LENGTH + 32))
        send_command(device, oversized)
        report = device.writes[0]
        assert len(report) == HID_REPORT_LENGTH + 1
        # Bytes after the report ID match the truncated command.
        assert report[1:] == oversized[:HID_REPORT_LENGTH]

    def test_short_command_is_zero_padded(self):
        device = _FakeHidDevice()
        send_command(device, bytes([0x01, 0x02, 0x03]))
        report = device.writes[0]
        # Bytes 1..3 carry the command, the rest are zero padding.
        assert report[0] == 0x00
        assert report[1:4] == bytes([0x01, 0x02, 0x03])
        assert report[4:] == bytes(HID_REPORT_LENGTH - 3)

    def test_raises_when_write_fails(self):
        device = _FakeHidDevice(write_return=-1)
        with pytest.raises(IOError, match="Failed to write"):
            send_command(device, CMD_GET_FITTING)


# ── read_response ─────────────────────────────────────────────────────────────


class TestReadResponse:
    def test_returns_bytes_payload(self):
        payload = bytes([0x01, 0x02, 0x03, 0x04])
        device = _FakeHidDevice(responses=[payload])
        result = read_response(device)
        assert isinstance(result, bytes)
        assert result == payload
        assert device.read_calls == [(HID_REPORT_LENGTH, 2000)]

    def test_custom_timeout_is_forwarded(self):
        device = _FakeHidDevice(responses=[b"\x00"])
        read_response(device, timeout_ms=750)
        assert device.read_calls == [(HID_REPORT_LENGTH, 750)]

    def test_raises_timeout_when_no_data(self):
        device = _FakeHidDevice(responses=[b""])
        with pytest.raises(TimeoutError, match="No response"):
            read_response(device)


# ── open_device ───────────────────────────────────────────────────────────────


class TestOpenDevice:
    def test_open_success_sets_blocking(self):
        fake = _FakeHidDevice()
        with patch.object(read_fitting.hid, "device", return_value=fake):
            handle = open_device()
        assert handle is fake
        assert fake.opened == (NOAHLINK_VENDOR_ID, NOAHLINK_PRODUCT_ID)
        assert fake.nonblocking is False

    def test_open_failure_wraps_oserror_with_helpful_message(self):
        fake = _FakeHidDevice(open_error=OSError("not found"))
        with patch.object(read_fitting.hid, "device", return_value=fake):
            with pytest.raises(OSError, match="Cannot open Noahlink Wireless 2"):
                open_device(0x1234, 0x5678)


# ── read_fitting_data ─────────────────────────────────────────────────────────


class TestReadFittingData:
    def test_returns_payload_and_timestamp(self):
        payload = bytes(range(8))
        device = _FakeHidDevice(responses=[payload])
        result = read_fitting_data(device)
        assert result["raw_payload"] == payload.hex()
        assert "timestamp" in result and result["timestamp"]
        # The fitting command must have been written verbatim (after report ID).
        assert device.writes[0][1:1 + len(CMD_GET_FITTING)] == CMD_GET_FITTING

    def test_logs_payload_at_debug(self, caplog):
        device = _FakeHidDevice(responses=[bytes([0xAB, 0xCD])])
        with caplog.at_level(logging.DEBUG, logger=read_fitting.logger.name):
            read_fitting_data(device)
        assert any("abcd" in record.getMessage().lower() for record in caplog.records)


# ── export_json / _utc_now_iso ────────────────────────────────────────────────


class TestExportJson:
    def test_writes_pretty_json(self, tmp_path: Path):
        out = tmp_path / "fitting.json"
        export_json({"raw_payload": "deadbeef"}, str(out))
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded == {"raw_payload": "deadbeef"}
        # indent=2 means a multi-line file.
        assert "\n" in out.read_text(encoding="utf-8")


class TestUtcNowIso:
    def test_includes_timezone_offset(self):
        ts = _utc_now_iso()
        # ISO-8601 with timezone always ends with +00:00 for UTC.
        assert ts.endswith("+00:00")
        assert "T" in ts


# ── CLI ───────────────────────────────────────────────────────────────────────


class TestMainCli:
    def test_main_writes_output_file(self, tmp_path, monkeypatch, capsys):
        fake = _FakeHidDevice(responses=[bytes(range(16))])
        monkeypatch.setattr(read_fitting.hid, "device", lambda: fake)

        out = tmp_path / "fit.json"
        monkeypatch.setattr(
            "sys.argv",
            ["read_fitting", "--output", str(out)],
        )

        main()

        captured = capsys.readouterr()
        assert str(out) in captured.out
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert "raw_payload" in loaded
        assert "timestamp" in loaded
        assert fake.closed is True

    def test_main_closes_device_even_on_failure(self, tmp_path, monkeypatch):
        fake = _FakeHidDevice(write_return=-1)
        monkeypatch.setattr(read_fitting.hid, "device", lambda: fake)
        monkeypatch.setattr(
            "sys.argv",
            ["read_fitting", "--output", str(tmp_path / "out.json")],
        )
        with pytest.raises(IOError):
            main()
        assert fake.closed is True

    def test_main_accepts_hex_vendor_and_product_ids(self, tmp_path, monkeypatch):
        fake = _FakeHidDevice(responses=[bytes(8)])
        monkeypatch.setattr(read_fitting.hid, "device", lambda: fake)
        monkeypatch.setattr(
            "sys.argv",
            [
                "read_fitting",
                "--output", str(tmp_path / "f.json"),
                "--vendor-id", "0x1234",
                "--product-id", "0x5678",
            ],
        )
        main()
        assert fake.opened == (0x1234, 0x5678)
