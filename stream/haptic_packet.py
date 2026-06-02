"""
haptic_packet.py – the single source of truth for the OpenHear wristband
BLE haptic packet wire format.

Every part of OpenHear that speaks to the wristband agrees on one tiny
contract: a **3-byte packet**

    byte 0: sound_class_id   (uint8)
    byte 1: intensity        (uint8, 0 = off … 255 = max)
    byte 2: pattern_id       (uint8)

That contract is shared across three independent implementations:

* the Windows-side Python runtime (:mod:`stream.ble_haptic`, which
  re-exports this module),
* the v1 micro:bit / RP2040 firmware
  (``hardware/wristband/firmware/openhear_firmware_v1.py`` and
  ``hardware/wristband/firmware.py``), and
* the v2 XIAO nRF52840 Arduino sketch.

Because those live in different languages on different silicon, the wire
format can drift apart silently — a classic cross-implementation bug that
only shows up as "the wrist buzzes wrong". This module pins the format in
one dependency-free place (no ``bleak``, no hardware imports) so a golden
test in CI catches any change to the bytes.

Embedded firmware cannot import this package, so the firmware accesses the
fields *positionally* (``packet[1]`` is intensity, ``packet[2]`` is
pattern). :data:`FIELD_INDEX` records that mapping and the test-suite
asserts the firmware still matches it.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Field order on the wire. Index in this tuple == byte offset in the packet.
PACKET_FIELDS: tuple[str, ...] = ("sound_class_id", "intensity", "pattern_id")

#: Total packet length in bytes.
PACKET_LENGTH: int = len(PACKET_FIELDS)

#: Name → byte offset, the mapping the embedded firmware relies on.
FIELD_INDEX: dict[str, int] = {name: i for i, name in enumerate(PACKET_FIELDS)}


def validate_uint8(name: str, value: int) -> int:
    """Return *value* if it is a valid uint8, else raise.

    Args:
        name: Field name, used in the error message.
        value: The candidate value.

    Raises:
        TypeError: If *value* is not an int.
        ValueError: If *value* is outside ``0..255``.
    """
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}.")
    if not 0 <= value <= 255:
        raise ValueError(f"{name} must be in the range 0..255, got {value}.")
    return value


@dataclass(frozen=True)
class HapticPacket:
    """One validated wristband command."""

    sound_class_id: int
    intensity: int
    pattern_id: int

    def to_bytes(self) -> bytes:
        """Return the validated 3-byte payload."""
        return encode_packet(self.sound_class_id, self.intensity, self.pattern_id)

    def to_tuple(self) -> tuple[int, int, int]:
        """Return ``(sound_class_id, intensity, pattern_id)``."""
        return (self.sound_class_id, self.intensity, self.pattern_id)

    @classmethod
    def from_bytes(cls, payload: bytes | bytearray) -> "HapticPacket":
        """Construct a packet from raw bytes (see :func:`decode_packet`)."""
        return decode_packet(payload)


def encode_packet(sound_class_id: int, intensity: int, pattern_id: int) -> bytes:
    """Pack the OpenHear 3-byte BLE command.

    Args:
        sound_class_id: Detected sound class id (uint8).
        intensity: Haptic drive strength, 0..255.
        pattern_id: Firmware vibration pattern id (uint8).

    Returns:
        Exactly :data:`PACKET_LENGTH` bytes in :data:`PACKET_FIELDS` order.
    """
    return bytes(
        (
            validate_uint8("sound_class_id", sound_class_id),
            validate_uint8("intensity", intensity),
            validate_uint8("pattern_id", pattern_id),
        )
    )


def decode_packet(payload: bytes | bytearray) -> HapticPacket:
    """Parse a 3-byte wristband packet back into a :class:`HapticPacket`.

    The canonical wire format is *exactly* :data:`PACKET_LENGTH` bytes;
    a payload of any other length is rejected so framing drift is caught
    rather than silently truncated. (Firmware tolerates trailing bytes
    for forward-compatibility, but the reference format does not.)

    Args:
        payload: The raw bytes received over BLE.

    Returns:
        The decoded :class:`HapticPacket`.

    Raises:
        ValueError: If *payload* is not exactly :data:`PACKET_LENGTH` bytes.
    """
    if len(payload) != PACKET_LENGTH:
        raise ValueError(
            f"Haptic packet must be exactly {PACKET_LENGTH} bytes, "
            f"got {len(payload)}."
        )
    return HapticPacket(
        sound_class_id=payload[FIELD_INDEX["sound_class_id"]],
        intensity=payload[FIELD_INDEX["intensity"]],
        pattern_id=payload[FIELD_INDEX["pattern_id"]],
    )
