"""
ble_haptic.py – BLE UART transport for the OpenHear wristband prototype.

The wristband uses a 3-byte packet:

    [sound_class_id, intensity, pattern_id]

and exposes the Nordic UART Service on a micro:bit advertising as
``OpenHear``.  This module handles packet encoding plus a small async BLE
client for the Windows-side Python runtime.
"""

from __future__ import annotations

# The 3-byte wire format lives in stream.haptic_packet — the single source
# of truth shared with the wristband firmware. Re-exported here so callers
# that import from stream.ble_haptic keep working unchanged.
from stream.haptic_packet import (  # noqa: F401
    PACKET_FIELDS,
    PACKET_LENGTH,
    HapticPacket,
    decode_packet,
    encode_packet,
    validate_uint8,
)

try:
    from bleak import BleakClient, BleakScanner
except ImportError:  # pragma: no cover - exercised via runtime error paths.
    BleakClient = None
    BleakScanner = None


OPENHEAR_DEVICE_NAME = "OpenHear"
NORDIC_UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
NORDIC_UART_RX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
NORDIC_UART_TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

# Backwards-compatible private alias for the pre-extraction name.
_validate_uint8 = validate_uint8


def _require_bleak() -> None:
    if BleakClient is None or BleakScanner is None:
        raise RuntimeError(
            "BLE support requires the 'bleak' package. "
            "Install it with 'pip install bleak'."
        )


class OpenHearBLEClient:
    """Minimal async BLE client for the OpenHear micro:bit UART link."""

    def __init__(
        self,
        *,
        device_name: str = OPENHEAR_DEVICE_NAME,
        characteristic_uuid: str = NORDIC_UART_RX_UUID,
        scanner=None,
        client_factory=None,
    ) -> None:
        self.device_name = device_name
        self.characteristic_uuid = characteristic_uuid
        self._scanner = scanner
        self._client_factory = client_factory
        self._client = None
        self._device = None

    @property
    def is_connected(self) -> bool:
        """Return ``True`` when the BLE client is currently connected."""
        if self._client is None:
            return False
        return bool(getattr(self._client, "is_connected", False))

    async def discover(self, *, timeout: float = 5.0):
        """Find the first BLE peripheral advertising as ``OpenHear``."""
        if self._scanner is None:
            _require_bleak()
        scanner = self._scanner or BleakScanner
        devices = await scanner.discover(timeout=timeout)
        for device in devices:
            if (getattr(device, "name", None) or "").strip() == self.device_name:
                self._device = device
                return device
        raise RuntimeError(f"Could not find BLE device named {self.device_name!r}.")

    async def connect(self, *, timeout: float = 5.0):
        """Discover and connect to the wristband."""
        device = self._device or await self.discover(timeout=timeout)
        if self._client_factory is None:
            _require_bleak()
        client_factory = self._client_factory or BleakClient
        self._client = client_factory(device)
        await self._client.connect()
        return device

    async def send_packet(self, packet: HapticPacket) -> None:
        """Write *packet* to the micro:bit UART RX characteristic."""
        if not self.is_connected:
            raise RuntimeError("BLE client is not connected.")
        await self._client.write_gatt_char(self.characteristic_uuid, packet.to_bytes())

    async def send_command(self, sound_class_id: int, intensity: int, pattern_id: int) -> None:
        """Encode and send one haptic command."""
        await self.send_packet(HapticPacket(sound_class_id, intensity, pattern_id))

    async def disconnect(self) -> None:
        """Disconnect from the wristband if connected."""
        if self._client is not None:
            await self._client.disconnect()
        self._client = None
