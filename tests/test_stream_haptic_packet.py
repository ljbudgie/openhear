"""Golden + parity tests for the shared wristband haptic packet codec.

This is the contract test for ``stream/haptic_packet.py``: it pins the
exact bytes on the wire so any drift in the 3-byte format is caught in
CI, and it proves the v1 firmware decodes the packet the same way the
codec encodes it.
"""

from __future__ import annotations

import pytest

from hardware.wristband.firmware.openhear_firmware_v1 import (
    HapticScheduler,
    NullHapticDriver,
)
from stream import ble_haptic
from stream.haptic_packet import (
    FIELD_INDEX,
    PACKET_FIELDS,
    PACKET_LENGTH,
    HapticPacket,
    decode_packet,
    encode_packet,
)

# ── Golden wire format ──────────────────────────────────────────────────────
#
# byte 0 = sound_class_id, byte 1 = intensity, byte 2 = pattern_id.
# These exact bytes are the contract. Changing the table means changing
# the wire format — and every firmware/app that speaks it.
_GOLDEN: tuple[tuple[tuple[int, int, int], bytes], ...] = (
    ((0, 0, 0), b"\x00\x00\x00"),
    ((3, 255, 1), b"\x03\xff\x01"),
    ((7, 150, 4), b"\x07\x96\x04"),
    ((255, 1, 240), b"\xff\x01\xf0"),
    ((12, 64, 6), b"\x0c\x40\x06"),
)


@pytest.mark.parametrize("fields,raw", _GOLDEN)
def test_encode_matches_golden_bytes(fields, raw):
    assert encode_packet(*fields) == raw
    assert len(raw) == PACKET_LENGTH


@pytest.mark.parametrize("fields,raw", _GOLDEN)
def test_decode_matches_golden_fields(fields, raw):
    assert decode_packet(raw).to_tuple() == fields


@pytest.mark.parametrize("fields,raw", _GOLDEN)
def test_round_trip(fields, raw):
    assert encode_packet(*decode_packet(raw).to_tuple()) == raw
    assert HapticPacket(*fields).to_bytes() == raw
    assert HapticPacket.from_bytes(raw).to_tuple() == fields


# ── Field layout ────────────────────────────────────────────────────────────


def test_field_order_is_stable():
    assert PACKET_FIELDS == ("sound_class_id", "intensity", "pattern_id")
    assert PACKET_LENGTH == 3
    assert FIELD_INDEX == {"sound_class_id": 0, "intensity": 1, "pattern_id": 2}


# ── Validation ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("bad", [-1, 256, 1000])
def test_encode_rejects_out_of_range(bad):
    with pytest.raises(ValueError):
        encode_packet(bad, 0, 0)
    with pytest.raises(ValueError):
        encode_packet(0, bad, 0)
    with pytest.raises(ValueError):
        encode_packet(0, 0, bad)


def test_encode_rejects_non_int():
    with pytest.raises(TypeError):
        encode_packet(1.5, 0, 0)  # type: ignore[arg-type]


@pytest.mark.parametrize("length", [0, 1, 2, 4, 5])
def test_decode_rejects_wrong_length(length):
    with pytest.raises(ValueError, match="exactly 3 bytes"):
        decode_packet(bytes(length))


# ── Backward compatibility: stream.ble_haptic re-exports the same objects ───


def test_ble_haptic_reexports_are_identical():
    assert ble_haptic.encode_packet is encode_packet
    assert ble_haptic.HapticPacket is HapticPacket
    assert ble_haptic.PACKET_FIELDS == PACKET_FIELDS
    assert ble_haptic.PACKET_LENGTH == PACKET_LENGTH
    # The pre-extraction private name still resolves.
    assert ble_haptic._validate_uint8("intensity", 1) == 1


# ── Firmware parity: v1 firmware decodes what the codec encodes ─────────────


def test_v1_firmware_reads_intensity_and_pattern_by_index():
    """The codec encodes intensity at byte 1 and pattern at byte 2; the v1
    firmware's submit_v0_packet must read those same offsets.

    pattern_id 4 drives a single actuator at the (capped) intensity, so the
    logged intensity proves the firmware took byte 1 — not byte 0 or 2.
    """
    driver = NullHapticDriver()
    scheduler = HapticScheduler(driver)

    packet = encode_packet(sound_class_id=99, intensity=150, pattern_id=4)
    scheduler.submit_v0_packet(packet)

    drives = [entry for entry in driver.log if entry[0] >= 0]
    assert drives, "pattern 4 should have driven an actuator"
    # entry = (actuator_index, frequency_hz, intensity, duration_ms)
    assert all(entry[2] == 150 for entry in drives)
    # sound_class_id (byte 0) is intentionally ignored by v0 firmware.


def test_v1_firmware_all_off_on_zero_intensity():
    driver = NullHapticDriver()
    scheduler = HapticScheduler(driver)
    scheduler.submit_v0_packet(encode_packet(5, 0, 3))
    assert driver.log == [(-1, 0, 0, 0)]  # all_off marker
