"""
wristband_runtime.py – end-to-end Windows runtime for the OpenHear wristband.

Captures microphone audio with ``sounddevice``, classifies each 0.975 second
window with YAMNet, personalises the intensity byte from the user's
audiogram, and forwards the 3-byte packet to the micro:bit over BLE UART.
"""

from __future__ import annotations

import argparse
import asyncio

from stream.ble_haptic import HapticPacket, OpenHearBLEClient
from stream.haptic_mapper import HapticMapper
from stream.sound_classifier import WINDOW_SECONDS, YamnetClassifier, classify_scores


class WristbandRuntime:
    """Orchestrate classifier output, haptic mapping, and BLE transport."""

    def __init__(self, mapper: HapticMapper, ble_client: OpenHearBLEClient) -> None:
        self.mapper = mapper
        self.ble_client = ble_client

    def packet_from_classification(self, sound_key: str, confidence: float) -> HapticPacket:
        sound_class_id, intensity, pattern_id = self.mapper.build_command(
            sound_key, confidence=confidence
        )
        return HapticPacket(sound_class_id, intensity, pattern_id)

    async def send_scores(self, scores_by_label: dict[str, float]) -> HapticPacket:
        classified = classify_scores(scores_by_label)
        packet = self.packet_from_classification(classified.sound_key, classified.confidence)
        await self.ble_client.send_packet(packet)
        return packet


async def _run_live(args) -> None:
    try:
        import sounddevice as sd
    except ImportError as exc:  # pragma: no cover - runtime-only path.
        raise RuntimeError(
            "Live microphone capture requires the 'sounddevice' package."
        ) from exc

    mapper = HapticMapper(
        args.audiogram,
        comfort_scale=args.comfort_scale,
        ear_strategy=args.ear_strategy,
    )
    classifier = YamnetClassifier(args.model, args.labels)
    client = OpenHearBLEClient()
    runtime = WristbandRuntime(mapper, client)
    frame_samples = int(round(16_000 * WINDOW_SECONDS))

    await client.connect(timeout=args.scan_timeout)
    try:
        with sd.InputStream(
            samplerate=16_000,
            channels=1,
            dtype="float32",
            blocksize=frame_samples,
        ) as stream:
            while True:
                samples, _ = stream.read(frame_samples)
                classified = classifier.classify_window(samples[:, 0], 16_000)
                packet = runtime.packet_from_classification(
                    classified.sound_key,
                    classified.confidence,
                )
                await client.send_packet(packet)
                print(
                    f"{classified.sound_key:<8} conf={classified.confidence:.2f} "
                    f"packet={list(packet.to_bytes())}"
                )
    finally:
        await client.disconnect()


async def _run_manual(args) -> None:
    mapper = HapticMapper(
        args.audiogram,
        comfort_scale=args.comfort_scale,
        ear_strategy=args.ear_strategy,
    )
    packet = HapticPacket(*mapper.build_command(args.sound_class, confidence=args.confidence))
    print(list(packet.to_bytes()))


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenHear wristband runtime.")
    parser.add_argument("--audiogram", required=True, help="Path to the patient audiogram JSON.")
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
        "--manual-sound",
        dest="sound_class",
        choices=["voice", "doorbell", "alarm", "dog", "traffic", "media", "silence"],
        help="Skip live audio and print the packet for one sound class.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=1.0,
        help="Manual confidence used with --manual-sound.",
    )
    parser.add_argument("--model", help="Path to the YAMNet .tflite model.")
    parser.add_argument("--labels", help="Path to the YAMNet label CSV/txt.")
    parser.add_argument(
        "--scan-timeout",
        type=float,
        default=5.0,
        help="BLE scan timeout in seconds.",
    )
    args = parser.parse_args()

    if args.sound_class:
        asyncio.run(_run_manual(args))
        return

    if not args.model or not args.labels:
        parser.error("--model and --labels are required unless --manual-sound is used.")

    asyncio.run(_run_live(args))


if __name__ == "__main__":
    main()
