"""
haptic_commander.py – user-facing audiogram-to-BLE command layer for OpenHear.
"""

from __future__ import annotations

import argparse
import asyncio

from stream.ble_haptic import HapticPacket, OpenHearBLEClient
from stream.haptic_mapper import SUPPORTED_SOUND_CLASSES, HapticMapper


class HapticCommander:
    """Combine audiogram-aware mapping with BLE transport for the wristband."""

    def __init__(
        self,
        audiogram_path: str,
        *,
        comfort_scale: float = 1.0,
        ear_strategy: str = "worst",
        ble_client: OpenHearBLEClient | None = None,
    ) -> None:
        self.mapper = HapticMapper(
            audiogram_path,
            comfort_scale=comfort_scale,
            ear_strategy=ear_strategy,
        )
        self.ble_client = ble_client or OpenHearBLEClient()

    def build_packet(self, sound_key: str, *, confidence: float = 1.0) -> HapticPacket:
        """Return the standard 3-byte packet for one OpenHear sound class."""
        return HapticPacket(*self.mapper.build_command(sound_key, confidence=confidence))

    async def connect(self, *, timeout: float = 5.0):
        """Connect to the wristband over BLE."""
        return await self.ble_client.connect(timeout=timeout)

    async def disconnect(self) -> None:
        """Disconnect from the wristband."""
        await self.ble_client.disconnect()

    async def send_sound(
        self,
        sound_key: str,
        *,
        confidence: float = 1.0,
        timeout: float = 5.0,
    ) -> HapticPacket:
        """Connect if needed and send one sound command."""
        if not self.ble_client.is_connected:
            await self.connect(timeout=timeout)
        packet = self.build_packet(sound_key, confidence=confidence)
        await self.ble_client.send_packet(packet)
        return packet


async def _run(args) -> None:
    commander = HapticCommander(
        args.audiogram,
        comfort_scale=args.comfort_scale,
        ear_strategy=args.ear_strategy,
    )
    packet = commander.build_packet(args.sound_class, confidence=args.confidence)

    if args.dry_run:
        print(list(packet.to_bytes()))
        return

    await commander.connect(timeout=args.scan_timeout)
    try:
        await commander.ble_client.send_packet(packet)
        print(list(packet.to_bytes()))
    finally:
        await commander.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(description="Send OpenHear wristband haptic commands.")
    parser.add_argument("--audiogram", required=True, help="Path to the patient audiogram JSON.")
    parser.add_argument(
        "--sound-class",
        choices=SUPPORTED_SOUND_CLASSES,
        required=True,
        help="One of the seven OpenHear wristband prototype sound classes.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=1.0,
        help="Classifier confidence multiplier for intensity scaling.",
    )
    parser.add_argument(
        "--comfort-scale",
        type=float,
        default=1.0,
        help="User comfort multiplier applied after audiogram personalisation.",
    )
    parser.add_argument(
        "--ear-strategy",
        choices=["worst", "average", "better"],
        default="worst",
        help="How to combine left/right thresholds into one intensity byte.",
    )
    parser.add_argument(
        "--scan-timeout",
        type=float,
        default=5.0,
        help="BLE scan timeout in seconds.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the packet without attempting a BLE connection.",
    )
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
