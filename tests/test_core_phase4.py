"""Tests for the Phase 4 Noahlink bridge: protocol, noahlink, fitting_data,
write_fitting, and backup."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core import noahlink as noahlink_mod
from core.backup import (
    BackupArchive,
    load_backup,
    restore_backup,
    write_backup,
)
from core.fitting_data import (
    CompressionProfile,
    DeviceInfo,
    FittingSession,
    GainTable,
    MPOProfile,
    ProgrammeSlot,
    from_phonak,
    from_signia,
)
from core.fitting_schema import PhonakFittingProfile, SigniaFittingProfile
from core.noahlink import HID_REPORT_LENGTH, NoahlinkDevice, enumerate_devices
from core.protocol import (
    SYNC_BYTE,
    MessageType,
    ParsedFrame,
    decode_session,
    encode_frame,
    parse_frame,
)
from core.write_fitting import (
    ALLOWED_PARAMETERS,
    WriteRequest,
    write_safe_parameters,
)


# ── protocol ───────────────────────────────────────────────────────────────


def test_encode_frame_round_trips():
    raw = encode_frame(MessageType.GET_FITTING, b"\x01\x02\x03", seq=42)
    frame, consumed = parse_frame(raw)
    assert frame is not None
    assert consumed == len(raw)
    assert frame.seq == 42
    assert frame.msg_type == MessageType.GET_FITTING
    assert frame.payload == b"\x01\x02\x03"
    assert frame.checksum_ok


def test_encode_frame_validates_inputs():
    with pytest.raises(ValueError, match="seq must fit"):
        encode_frame(MessageType.HELLO, b"", seq=300)
    with pytest.raises(ValueError, match="msg_type"):
        encode_frame(0x100, b"", seq=0)
    with pytest.raises(ValueError, match="payload too long"):
        encode_frame(MessageType.HELLO, b"\x00" * 256)


def test_parse_frame_skips_junk_before_sync_byte():
    raw = b"\xff\xff" + encode_frame(MessageType.ACK, b"")
    frame, consumed = parse_frame(raw)
    assert frame is not None
    assert frame.msg_type == MessageType.ACK
    assert consumed == len(raw)


def test_parse_frame_returns_none_for_partial_frame():
    full = encode_frame(MessageType.HELLO, b"\x01\x02\x03")
    frame, consumed = parse_frame(full[:4])
    assert frame is None
    assert consumed == 0  # sync byte present, more data needed


def test_parse_frame_returns_none_for_pure_junk():
    frame, consumed = parse_frame(b"\xff\xff")
    assert frame is None
    assert consumed == 2


def test_parse_frame_detects_bad_checksum():
    raw = bytearray(encode_frame(MessageType.HELLO, b"\x10"))
    raw[-1] ^= 0xFF
    frame, _ = parse_frame(bytes(raw))
    assert frame is not None
    assert not frame.checksum_ok


def test_decode_session_yields_multiple_frames():
    a = encode_frame(MessageType.HELLO, b"", seq=1)
    b = encode_frame(MessageType.ACK, b"\x00", seq=2)
    c = encode_frame(MessageType.DEVICE_INFO, b"abc", seq=3)
    frames = list(decode_session(a + b + c))
    assert [f.seq for f in frames] == [1, 2, 3]
    assert [f.msg_type for f in frames] == [
        MessageType.HELLO, MessageType.ACK, MessageType.DEVICE_INFO,
    ]


def test_decode_session_handles_empty_input():
    assert list(decode_session(b"")) == []


def test_message_type_name_handles_unknown():
    frame = ParsedFrame(seq=1, msg_type=0xAB, payload=b"", checksum_ok=True)
    assert frame.msg_type_name == "UNKNOWN_TYPE_AB"


def test_known_message_type_name():
    frame = ParsedFrame(seq=1, msg_type=MessageType.GET_FITTING, payload=b"",
                        checksum_ok=True)
    assert frame.msg_type_name == "GET_FITTING"


# ── noahlink wrapper ───────────────────────────────────────────────────────


class _FakeHidDevice:
    def __init__(self, *, response: bytes | None = None,
                 open_error: Exception | None = None):
        self.response = response
        self.open_error = open_error
        self.open_calls: list[tuple[int, int]] = []
        self.writes: list[bytes] = []
        self.read_calls = 0
        self.closed = False
        self.nonblocking: bool | None = None

    def open(self, vid, pid):
        self.open_calls.append((vid, pid))
        if self.open_error is not None:
            raise self.open_error

    def set_nonblocking(self, v):
        self.nonblocking = v

    def write(self, data):
        self.writes.append(bytes(data))
        return len(data)

    def read(self, length, timeout_ms=0):
        self.read_calls += 1
        if self.response is None:
            return []
        return list(self.response[:length])

    def close(self):
        self.closed = True


def test_noahlink_open_and_write_pads_report(monkeypatch):
    fake = _FakeHidDevice(response=b"\xa5" + b"\x00" * 6)
    monkeypatch.setattr(noahlink_mod.hid, "device", lambda: fake)
    dev = NoahlinkDevice().open()
    dev.write(b"\x01\x02")
    payload = fake.writes[0]
    # 1 leading report-ID byte + HID_REPORT_LENGTH payload bytes.
    assert len(payload) == HID_REPORT_LENGTH + 1
    assert payload[0] == 0x00
    assert payload[1:3] == b"\x01\x02"
    dev.close()
    assert fake.closed


def test_noahlink_write_too_long_rejected(monkeypatch):
    fake = _FakeHidDevice()
    monkeypatch.setattr(noahlink_mod.hid, "device", lambda: fake)
    dev = NoahlinkDevice().open()
    with pytest.raises(ValueError, match="max"):
        dev.write(b"\x00" * (HID_REPORT_LENGTH + 1))


def test_noahlink_read_returns_bytes(monkeypatch):
    fake = _FakeHidDevice(response=b"\xa5\x01\x02\x00\x03")
    monkeypatch.setattr(noahlink_mod.hid, "device", lambda: fake)
    with NoahlinkDevice() as dev:
        out = dev.read()
    assert out == b"\xa5\x01\x02\x00\x03"


def test_noahlink_read_timeout_raises(monkeypatch):
    fake = _FakeHidDevice(response=None)
    monkeypatch.setattr(noahlink_mod.hid, "device", lambda: fake)
    with NoahlinkDevice() as dev:
        with pytest.raises(TimeoutError):
            dev.read(timeout_ms=10)


def test_noahlink_write_before_open_raises():
    dev = NoahlinkDevice()
    with pytest.raises(RuntimeError, match="not open"):
        dev.write(b"\x00")


def test_noahlink_open_retries_on_oserror(monkeypatch):
    attempts = {"n": 0}

    def factory():
        attempts["n"] += 1
        if attempts["n"] < 3:
            return _FakeHidDevice(open_error=OSError("transient"))
        return _FakeHidDevice(response=b"")
    monkeypatch.setattr(noahlink_mod.hid, "device", factory)
    dev = NoahlinkDevice(retries=5).open()
    assert attempts["n"] == 3
    dev.close()


def test_noahlink_open_gives_up_after_retries(monkeypatch):
    monkeypatch.setattr(
        noahlink_mod.hid, "device",
        lambda: _FakeHidDevice(open_error=OSError("nope")),
    )
    with pytest.raises(OSError, match="Cannot open Noahlink"):
        NoahlinkDevice(retries=2).open()


def test_noahlink_traffic_log(monkeypatch, tmp_path):
    fake = _FakeHidDevice(response=b"\xa5" + b"\x01" * 8)
    monkeypatch.setattr(noahlink_mod.hid, "device", lambda: fake)
    log = tmp_path / "trace.log"
    with NoahlinkDevice(log_path=log) as dev:
        dev.write(b"\xde\xad")
        dev.read()
    text = log.read_text()
    assert "TX" in text and "RX" in text
    assert "dead" in text.lower()


def test_enumerate_devices_filters(monkeypatch):
    monkeypatch.setattr(noahlink_mod.hid, "enumerate", lambda: [
        {"vendor_id": 0x0484, "product_id": 0x006E, "path": b"a"},
        {"vendor_id": 0x046D, "product_id": 0xC52B, "path": b"b"},
    ])
    matches = enumerate_devices()
    assert len(matches) == 1
    assert matches[0]["product_id"] == 0x006E


# ── fitting_data dataclasses ───────────────────────────────────────────────


def test_gain_table_validates_lengths():
    with pytest.raises(ValueError, match="same length"):
        GainTable(frequencies_hz=[500, 1000], gains_db=[0.0])


def test_compression_profile_validates_lengths():
    with pytest.raises(ValueError, match="length"):
        CompressionProfile(
            centre_frequencies_hz=[500, 1000],
            ratios=[1.5],
            knee_db=[40, 40],
            attack_ms=[5, 5],
            release_ms=[50, 50],
        )


def test_mpo_profile_validates_lengths():
    with pytest.raises(ValueError, match="equal length"):
        MPOProfile(centre_frequencies_hz=[500], max_db_spl=[100, 100])


def test_fitting_session_round_trips_json():
    session = FittingSession(
        captured_at="2024-01-15T00:00:00+00:00",
        device=DeviceInfo(manufacturer="Phonak", model="Naida", serial="ABC"),
        right_gain=GainTable(frequencies_hz=[500, 1000], gains_db=[5.0, 10.0]),
        left_gain=GainTable(frequencies_hz=[500, 1000], gains_db=[6.0, 11.0]),
        programmes=[ProgrammeSlot(slot_index=0, name="Universal")],
        raw_payload_hex="ab" * 8,
    )
    text = session.to_json(indent=2)
    parsed = FittingSession.from_json(text)
    assert parsed.device.serial == "ABC"
    assert parsed.right_gain.gains_db == [5.0, 10.0]
    assert parsed.programmes[0].name == "Universal"
    assert parsed.raw_payload_hex == "ab" * 8


def test_from_phonak_bridges_legacy_profile():
    legacy = PhonakFittingProfile(device_serial="P-1")
    session = from_phonak(legacy)
    assert session.device.manufacturer == "Phonak"
    assert session.device.serial == "P-1"
    assert session.right_compression.ratios  # populated


def test_from_signia_bridges_legacy_profile():
    legacy = SigniaFittingProfile(device_serial="S-1")
    session = from_signia(legacy)
    assert session.device.manufacturer == "Signia"
    assert session.device.serial == "S-1"


# ── backup ─────────────────────────────────────────────────────────────────


def _toy_session(serial: str = "ABC") -> FittingSession:
    return FittingSession(
        captured_at="2024-01-15T00:00:00+00:00",
        device=DeviceInfo(manufacturer="Phonak", model="Test", serial=serial),
        raw_payload_hex="aa" * 4,
    )


def test_backup_round_trip(tmp_path):
    session = _toy_session()
    raw = b"\x01\x02\x03\x04"
    archive = write_backup(session, raw, output_dir=tmp_path)

    assert isinstance(archive, BackupArchive)
    assert archive.directory.exists()
    assert archive.fitting_path.exists()
    assert archive.raw_path.exists()
    assert archive.manifest_path.exists()
    assert archive.verify()

    loaded_session, loaded_raw = load_backup(archive.directory)
    assert loaded_session.device.serial == "ABC"
    assert loaded_raw == raw


def test_backup_detects_tampering(tmp_path):
    session = _toy_session()
    raw = b"\x01\x02\x03\x04"
    archive = write_backup(session, raw, output_dir=tmp_path)
    archive.raw_path.write_bytes(b"tampered!")
    with pytest.raises(ValueError, match="raw.bin checksum"):
        load_backup(archive.directory)


def test_load_backup_missing_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_backup(tmp_path)


def test_restore_backup_is_stub(tmp_path):
    with pytest.raises(NotImplementedError):
        restore_backup(tmp_path)


def test_safe_label_handles_unsafe_serial(tmp_path):
    session = _toy_session(serial="weird/serial:1")
    archive = write_backup(session, b"\x00", output_dir=tmp_path)
    # No '/' or ':' in directory name.
    assert "/" not in archive.directory.name
    assert ":" not in archive.directory.name


# ── write_fitting safety gates ─────────────────────────────────────────────


def test_allowed_parameters_kept_minimal():
    """Defence in depth: this test fails if someone broadens the
    allow-list without updating PROTOCOL_NOTES.md."""
    assert ALLOWED_PARAMETERS == frozenset({
        "programme_name",
        "volume_offset_db",
        "streaming_preference",
    })


def test_write_safe_parameters_rejects_disallowed_field(tmp_path):
    session = _toy_session()
    with pytest.raises(PermissionError, match="Refusing"):
        write_safe_parameters(
            session, b"raw", [WriteRequest(0, "gain_table", [0.0])],
            backup_dir=tmp_path,
        )


def test_write_safe_parameters_rejects_bad_value(tmp_path):
    session = _toy_session()
    with pytest.raises(ValueError, match="volume_offset_db"):
        write_safe_parameters(
            session, b"raw", [WriteRequest(0, "volume_offset_db", 99.0)],
            backup_dir=tmp_path,
        )
    with pytest.raises(ValueError, match="programme_name"):
        write_safe_parameters(
            session, b"raw", [WriteRequest(0, "programme_name", "")],
            backup_dir=tmp_path,
        )
    with pytest.raises(ValueError, match="streaming_preference"):
        write_safe_parameters(
            session, b"raw",
            [WriteRequest(0, "streaming_preference", "loud")],
            backup_dir=tmp_path,
        )


def test_write_safe_parameters_writes_backup_and_mutates_session(tmp_path):
    session = _toy_session()
    archive = write_safe_parameters(
        session, b"raw bytes",
        [WriteRequest(0, "programme_name", "Quiet Restaurant"),
         WriteRequest(0, "volume_offset_db", 3.0)],
        backup_dir=tmp_path,
    )
    assert archive.directory.exists()
    # Session mutation visible.
    slot = session.programmes[0]
    assert slot.name == "Quiet Restaurant"
    assert slot.volume_offset_db == 3.0


def test_write_safe_parameters_transmit_is_stub(tmp_path):
    session = _toy_session()
    with pytest.raises(NotImplementedError, match="WRITE_FITTING"):
        write_safe_parameters(
            session, b"raw",
            [WriteRequest(0, "programme_name", "Default")],
            backup_dir=tmp_path,
            transmit=True,
        )


def test_write_safe_parameters_requires_at_least_one_request(tmp_path):
    session = _toy_session()
    with pytest.raises(ValueError, match="At least one"):
        write_safe_parameters(session, b"r", [], backup_dir=tmp_path)


# ── read_fitting integration with new helpers ──────────────────────────────


def test_read_session_uses_send_and_receive_when_available():
    from core.read_fitting import read_session

    class _FakeWrapper:
        def __init__(self, response):
            self.response = response
            self.last_request: bytes | None = None

        def send_and_receive(self, request, timeout_ms=2000):
            self.last_request = request
            return self.response

    # Build a synthetic device-info reply.
    payload = b"SN-12345|FW1.0"
    response = encode_frame(MessageType.DEVICE_INFO, payload, seq=1)
    wrapper = _FakeWrapper(response)

    session = read_session(wrapper)
    assert wrapper.last_request is not None
    assert wrapper.last_request[0] == SYNC_BYTE
    assert session.device.serial == "SN-12345"
    assert session.device.firmware == "FW1.0"
    assert session.raw_payload_hex == response.hex()


def test_read_session_raw_only_skips_parser():
    from core.read_fitting import read_session

    class _FakeWrapper:
        def send_and_receive(self, request, timeout_ms=2000):
            return b"\xa5\x00\x11\x05hello\x95"

    session = read_session(_FakeWrapper(), raw_only=True)
    # Device serial should not have been populated since parser was skipped.
    assert session.device.serial == ""
    assert session.raw_payload_hex
