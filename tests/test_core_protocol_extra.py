"""Additional tests for ``core/protocol.py`` – covering the decode_session
edge-cases and partial-frame handling that the main test file doesn't reach."""

from __future__ import annotations

import pytest

from core.protocol import (
    SYNC_BYTE,
    MessageType,
    ParsedFrame,
    _xor_checksum,
    decode_session,
    encode_frame,
    parse_frame,
)


class TestEncodeDecodeRoundtrip:
    def test_hello_frame(self):
        raw = encode_frame(MessageType.HELLO, b"")
        frame, consumed = parse_frame(raw)
        assert frame is not None
        assert frame.seq == 0
        assert frame.msg_type == MessageType.HELLO
        assert frame.payload == b""
        assert frame.checksum_ok is True
        assert consumed == len(raw)

    def test_payload_preserved(self):
        payload = bytes(range(10))
        raw = encode_frame(MessageType.FITTING_BLOB, payload, seq=7)
        frame, _ = parse_frame(raw)
        assert frame.payload == payload
        assert frame.seq == 7

    def test_checksum_detected_bad(self):
        raw = bytearray(encode_frame(MessageType.ACK, b"\x01", seq=1))
        raw[-1] ^= 0xFF  # corrupt the checksum byte
        frame, _ = parse_frame(bytes(raw))
        assert frame is not None
        assert frame.checksum_ok is False


class TestEncodeFrameValidation:
    def test_seq_out_of_range_raises(self):
        with pytest.raises(ValueError, match="seq"):
            encode_frame(MessageType.HELLO, b"", seq=256)

    def test_msg_type_out_of_range_raises(self):
        with pytest.raises(ValueError, match="msg_type"):
            encode_frame(256, b"")

    def test_payload_too_long_raises(self):
        with pytest.raises(ValueError, match="payload too long"):
            encode_frame(MessageType.HELLO, b"x" * 256)


class TestParsedFrameMsgTypeName:
    def test_known_type_name(self):
        f = ParsedFrame(seq=0, msg_type=MessageType.HELLO, payload=b"", checksum_ok=True)
        assert f.msg_type_name == "HELLO"

    def test_unknown_type_name(self):
        f = ParsedFrame(seq=0, msg_type=0xAB, payload=b"", checksum_ok=True)
        assert f.msg_type_name == "UNKNOWN_TYPE_AB"


class TestParseFrame:
    def test_empty_buffer_returns_none(self):
        frame, consumed = parse_frame(b"")
        assert frame is None
        assert consumed == 0

    def test_no_sync_byte_skips_all(self):
        data = b"\x00\x01\x02\x03\x04\x05"
        frame, consumed = parse_frame(data)
        assert frame is None
        assert consumed == len(data)

    def test_partial_frame_returns_none_at_start(self):
        # Only sync byte + 3 bytes: too short to have a complete header
        data = bytes([SYNC_BYTE, 0x01, 0x02, 0x03])
        frame, consumed = parse_frame(data)
        assert frame is None
        # consumed should be the position of the sync byte
        assert consumed == 0

    def test_incomplete_payload_returns_none(self):
        # Encode a frame then truncate it before the checksum
        raw = encode_frame(MessageType.BACKUP, b"\xde\xad\xbe\xef")
        truncated = raw[:-2]  # remove last 2 bytes
        frame, consumed = parse_frame(truncated)
        assert frame is None

    def test_junk_before_sync_is_skipped(self):
        raw = encode_frame(MessageType.GET_DEVICE_INFO, b"\x42")
        data = b"\xbb\xcc" + raw
        frame, consumed = parse_frame(data)
        assert frame is not None
        assert frame.checksum_ok is True
        assert consumed == len(data)


class TestDecodeSession:
    def test_empty_stream_yields_nothing(self):
        frames = list(decode_session(b""))
        assert frames == []

    def test_single_frame(self):
        raw = encode_frame(MessageType.DEVICE_INFO, b"\x01\x02\x03")
        frames = list(decode_session(raw))
        assert len(frames) == 1
        assert frames[0].msg_type == MessageType.DEVICE_INFO

    def test_two_consecutive_frames(self):
        f1 = encode_frame(MessageType.HELLO, b"", seq=0)
        f2 = encode_frame(MessageType.ACK, b"\xff", seq=1)
        frames = list(decode_session(f1 + f2))
        assert len(frames) == 2
        assert frames[0].msg_type == MessageType.HELLO
        assert frames[1].msg_type == MessageType.ACK

    def test_stream_with_no_sync_byte_yields_nothing(self):
        frames = list(decode_session(b"\x00\x01\x02\x03\x04"))
        assert frames == []

    def test_partial_frame_at_end_does_not_crash(self):
        raw = encode_frame(MessageType.GET_FITTING, b"\xaa\xbb")
        partial = raw[:3]  # just sync + seq + type, no payload
        frames = list(decode_session(partial))
        assert frames == []

    def test_frame_with_bad_checksum_still_yielded(self):
        raw = bytearray(encode_frame(MessageType.WRITE_FITTING, b"\x01"))
        raw[-1] ^= 0xFF  # corrupt checksum
        frames = list(decode_session(bytes(raw)))
        assert len(frames) == 1
        assert frames[0].checksum_ok is False

    def test_junk_between_valid_frames(self):
        f1 = encode_frame(MessageType.HELLO, b"", seq=0)
        f2 = encode_frame(MessageType.ACK, b"", seq=1)
        stream = f1 + b"\xde\xad" + f2  # junk bytes between frames
        frames = list(decode_session(stream))
        # Both frames should be found; the junk bytes before f2's sync are skipped
        msg_types = [f.msg_type for f in frames]
        assert MessageType.HELLO in msg_types
        assert MessageType.ACK in msg_types

    def test_stream_ending_with_partial_payload_terminates_cleanly(self):
        """A stream that ends with a truncated payload should just stop."""
        raw = encode_frame(MessageType.FITTING_BLOB, b"\x01\x02\x03\x04")
        truncated = raw[:-1]  # cut off checksum byte
        frames = list(decode_session(truncated))
        assert frames == []


class TestXorChecksum:
    def test_empty_is_zero(self):
        assert _xor_checksum(b"") == 0

    def test_single_byte(self):
        assert _xor_checksum(b"\xab") == 0xAB

    def test_two_same_bytes_is_zero(self):
        assert _xor_checksum(b"\xff\xff") == 0

    def test_known_value(self):
        assert _xor_checksum(b"\x01\x02\x03") == 0x01 ^ 0x02 ^ 0x03
