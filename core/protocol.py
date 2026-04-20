"""
protocol.py – HIMSA-style Noahlink message parser.

Implements a *best-effort* open parser for the framed messages that
travel over the Noahlink Wireless 2 USB HID transport.  The framing
is reverse-engineered from publicly visible USB captures (HIMSA's
internal protocol is not published) and is therefore conservative:
when a field's purpose is not yet known the parser exposes it as
``UNKNOWN_FIELD_XX`` rather than guessing.

Frame layout (best-known):

    +----+--------+--------+----------+--------+--------+
    | 0xA5 | seq | type  | payload_len | payload | checksum |
    | 1B   | 1B  |  1B   |     1B      |   N B   |    1B    |
    +------+-----+-------+-------------+---------+----------+

* Sync byte: ``0xA5`` (constant).
* ``seq``: rolling counter increased by the host on each request and
  echoed by the device.
* ``type``: one of :class:`MessageType`.
* ``payload_len``: number of payload bytes that follow.
* ``payload``: opaque to this layer.
* ``checksum``: 8-bit XOR of every byte from ``seq`` through the last
  payload byte.

Only the framing layer is guaranteed.  Higher-level decoders (ack,
session-list, fitting blob…) live in :mod:`core.fitting_data` and will
be filled in as evidence accumulates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Iterator


SYNC_BYTE: int = 0xA5


class MessageType(IntEnum):
    """Best-known message type identifiers used by Noahlink Wireless 2.

    Values for which the meaning is not yet confirmed are kept as
    ``UNKNOWN_TYPE_NN`` so the parser can surface them without
    pretending to understand them.
    """

    HELLO = 0x01
    ACK = 0x02
    GET_DEVICE_INFO = 0x10
    DEVICE_INFO = 0x11
    GET_FITTING = 0x20
    FITTING_BLOB = 0x21
    WRITE_FITTING = 0x22
    BACKUP = 0x30
    RESTORE = 0x31
    UNKNOWN_TYPE_FF = 0xFF


@dataclass
class ParsedFrame:
    """One framed message extracted from the raw HID byte stream.

    Attributes:
        seq: Rolling sequence number echoed by the device.
        msg_type: One of :class:`MessageType`.  Unknown integers are
            represented as their numeric value.
        payload: Raw payload bytes.
        checksum_ok: ``True`` when the checksum matched what the host
            recomputed.
        unknown_fields: ``{field_name: bytes}`` for any layout slots
            whose purpose has not been confirmed.  Populated by higher
            level decoders, not by the framing layer.
    """

    seq: int
    msg_type: int
    payload: bytes
    checksum_ok: bool
    unknown_fields: dict[str, bytes] = field(default_factory=dict)

    @property
    def msg_type_name(self) -> str:
        """Human-readable name of :attr:`msg_type` (or ``UNKNOWN_TYPE_XX``)."""
        try:
            return MessageType(self.msg_type).name
        except ValueError:
            return f"UNKNOWN_TYPE_{self.msg_type:02X}"


def _xor_checksum(data: bytes) -> int:
    """Return the 8-bit XOR of every byte in *data*."""
    cs = 0
    for b in data:
        cs ^= b
    return cs


def encode_frame(msg_type: int, payload: bytes, seq: int = 0) -> bytes:
    """Serialise a single framed message ready for HID transport.

    Args:
        msg_type: The :class:`MessageType` (or raw integer) to send.
        payload: Opaque payload bytes (max 255 due to the 1-byte length
            field).
        seq: Sequence number to embed.

    Returns:
        Bytes suitable for :func:`core.noahlink.NoahlinkDevice.write`.

    Raises:
        ValueError: If the payload is longer than 255 bytes or
            ``msg_type``/``seq`` are out of range.
    """
    if not (0 <= seq <= 0xFF):
        raise ValueError(f"seq must fit in one byte, got {seq}.")
    if not (0 <= int(msg_type) <= 0xFF):
        raise ValueError(f"msg_type must fit in one byte, got {msg_type}.")
    if len(payload) > 0xFF:
        raise ValueError(
            f"payload too long ({len(payload)} bytes); "
            "max 255 due to 1-byte length field."
        )
    body = bytes([seq, int(msg_type), len(payload)]) + payload
    cs = _xor_checksum(body)
    return bytes([SYNC_BYTE]) + body + bytes([cs])


def parse_frame(data: bytes) -> tuple[ParsedFrame | None, int]:
    """Parse a single frame from the start of *data*.

    Args:
        data: Buffer to consume from.  Bytes prior to the first sync
            byte are skipped.

    Returns:
        ``(frame, consumed)``.  ``frame`` is ``None`` if the buffer
        does not yet hold a complete frame; ``consumed`` is the number
        of bytes that were processed (which may be less than
        ``len(data)`` if a partial frame was found).
    """
    # Skip junk before the first sync byte.
    start = 0
    while start < len(data) and data[start] != SYNC_BYTE:
        start += 1
    if start >= len(data):
        return None, len(data)

    if len(data) - start < 5:
        # Need at least sync + seq + type + len + checksum.
        return None, start

    seq = data[start + 1]
    msg_type = data[start + 2]
    payload_len = data[start + 3]
    # Total bytes consumed from `start`: sync(1) + seq(1) + type(1)
    # + len(1) + payload(N) + checksum(1) = 5 + N.
    total_consumed = 5 + payload_len
    if len(data) - start < total_consumed:
        # Wait for more bytes.
        return None, start

    payload = bytes(data[start + 4: start + 4 + payload_len])
    received_cs = data[start + 4 + payload_len]
    body = bytes([seq, msg_type, payload_len]) + payload
    expected_cs = _xor_checksum(body)
    return (
        ParsedFrame(
            seq=seq,
            msg_type=msg_type,
            payload=payload,
            checksum_ok=(received_cs == expected_cs),
        ),
        start + total_consumed,
    )


def decode_session(stream: bytes) -> Iterator[ParsedFrame]:
    """Iterate over every frame found in *stream*.

    Used to convert a raw HID-traffic capture into a sequence of
    structured frames for inspection.

    Yields:
        :class:`ParsedFrame` instances in the order they appear.
    """
    buffer = bytes(stream)
    while buffer:
        frame, consumed = parse_frame(buffer)
        if frame is None:
            # Either malformed bytes were skipped or we ran out of data.
            if consumed == 0:
                # No sync byte at all – nothing more to do.
                return
            buffer = buffer[consumed:]
            if frame is None and len(buffer) < 5:
                return
            continue
        yield frame
        buffer = buffer[consumed:]
