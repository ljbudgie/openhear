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
from stream.phase2_training import Phase2ProgressStore, Phase2TrainingSession
from stream.phase3_open_conversation import (
    Phase3OpenConversationSession,
    Phase3ProgressStore,
)
from stream.sound_classifier import WINDOW_SECONDS, YamnetClassifier, classify_scores


class WristbandRuntime:
    """Orchestrate classifier output, haptic mapping, and BLE transport."""

    def __init__(
        self,
        mapper: HapticMapper,
        ble_client: OpenHearBLEClient,
        *,
        phase2_session: Phase2TrainingSession | None = None,
        phase2_progress: Phase2ProgressStore | None = None,
        phase3_session: Phase3OpenConversationSession | None = None,
        phase3_progress: Phase3ProgressStore | None = None,
        phase3_environment: str = "",
        phase3_passive_log: bool = False,
    ) -> None:
        self.mapper = mapper
        self.ble_client = ble_client
        self.phase2_session = phase2_session
        self.phase2_progress = phase2_progress
        self.phase3_session = phase3_session
        self.phase3_progress = phase3_progress
        self.phase3_environment = phase3_environment
        self.phase3_passive_log = phase3_passive_log

    def packet_from_classification(self, sound_key: str, confidence: float) -> HapticPacket:
        sound_class_id, intensity, pattern_id = self.mapper.build_command(
            sound_key, confidence=confidence
        )
        return HapticPacket(sound_class_id, intensity, pattern_id)

    async def send_scores(self, scores_by_label: dict[str, float]) -> HapticPacket:
        classified = classify_scores(scores_by_label)
        packet = self.packet_from_classification(classified.sound_key, classified.confidence)
        await self.ble_client.send_packet(packet)
        if self.phase3_passive_log:
            if self.phase3_session is None:
                self.phase3_session = Phase3OpenConversationSession()
            event = self.phase3_session.record_passive(
                classified.sound_key,
                source_label=classified.source_label,
                confidence=classified.confidence,
                intensity=packet.intensity,
                pattern_id=packet.pattern_id,
                duration_seconds=WINDOW_SECONDS,
                environment_tag=self.phase3_environment,
            )
            if self.phase3_progress is not None:
                self.phase3_progress.append_passive(event)
        return packet

    async def send_phase2_scores(
        self,
        target_id: str,
        scores_by_label: dict[str, float],
        *,
        reaction_time_ms: float | None = None,
        user_rating: int | None = None,
    ) -> tuple[HapticPacket, object]:
        """Score Phase 2 labels, send the existing BLE packet, and optionally log."""
        if self.phase2_session is None:
            self.phase2_session = Phase2TrainingSession()
        event = self.phase2_session.evaluate_scores(
            target_id,
            scores_by_label,
            reaction_time_ms=reaction_time_ms,
            user_rating=user_rating,
        )
        packet = self.packet_from_classification(event.predicted_sound_class, event.confidence)
        await self.ble_client.send_packet(packet)
        if self.phase2_progress is not None:
            self.phase2_progress.append(event)
        return packet, event

    async def send_phase3_recall_scores(
        self,
        prompt_id: str,
        scores_by_label: dict[str, float],
        *,
        user_response: str = "",
        reaction_time_ms: float | None = None,
        user_rating: int | None = None,
        notes: str = "",
    ) -> tuple[HapticPacket, object]:
        """Score Phase 3 recall, send the existing BLE packet, and optionally log."""
        classified = classify_scores(scores_by_label)
        packet = self.packet_from_classification(classified.sound_key, classified.confidence)
        await self.ble_client.send_packet(packet)
        if self.phase3_session is None:
            self.phase3_session = Phase3OpenConversationSession()
        event = self.phase3_session.record_recall(
            prompt_id,
            predicted_sound_class=classified.sound_key,
            confidence=classified.confidence,
            user_response=user_response,
            reaction_time_ms=reaction_time_ms,
            user_rating=user_rating,
            notes=notes,
            environment_tag=self.phase3_environment,
        )
        if self.phase3_progress is not None:
            self.phase3_progress.append_recall(event)
        return packet, event


async def _run_live(args) -> None:
    try:
        import sounddevice as sd
    except ImportError as exc:  # pragma: no cover - runtime-only path.
        raise RuntimeError("Live microphone capture requires the 'sounddevice' package.") from exc

    mapper = HapticMapper(
        args.audiogram,
        comfort_scale=args.comfort_scale,
        ear_strategy=args.ear_strategy,
    )
    classifier = YamnetClassifier(args.model, args.labels)
    client = OpenHearBLEClient()
    phase2_session = Phase2TrainingSession() if args.phase2_target else None
    phase2_progress = Phase2ProgressStore(args.phase2_progress) if args.phase2_progress else None
    phase3_session = (
        Phase3OpenConversationSession()
        if args.phase3_passive_log or args.phase3_recall_prompt
        else None
    )
    phase3_progress = Phase3ProgressStore(args.phase3_progress) if args.phase3_progress else None
    runtime = WristbandRuntime(
        mapper,
        client,
        phase2_session=phase2_session,
        phase2_progress=phase2_progress,
        phase3_session=phase3_session,
        phase3_progress=phase3_progress,
        phase3_environment=args.phase3_environment,
        phase3_passive_log=args.phase3_passive_log,
    )
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
                scores = {classified.source_label: classified.confidence}
                if args.phase2_target:
                    packet, event = await runtime.send_phase2_scores(args.phase2_target, scores)
                    suffix = f" phase2={event.outcome}"
                elif args.phase3_recall_prompt:
                    packet, event = await runtime.send_phase3_recall_scores(
                        args.phase3_recall_prompt,
                        scores,
                        user_response=args.phase3_user_response or "",
                        reaction_time_ms=args.phase3_reaction_time_ms,
                        user_rating=args.phase3_user_rating,
                    )
                    suffix = f" phase3={event.outcome}"
                else:
                    packet = await runtime.send_scores(scores)
                    if args.phase3_passive_log and args.phase3_progress:
                        suffix = " phase3=passive"
                    elif args.phase3_passive_log:
                        suffix = " phase3=passive-memory"
                    else:
                        suffix = ""
                print(
                    f"{classified.sound_key:<8} conf={classified.confidence:.2f} "
                    f"packet={list(packet.to_bytes())}{suffix}"
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
        "--phase2-target",
        help="Optional Phase 2 target id for live training progress logging.",
    )
    parser.add_argument(
        "--phase2-progress",
        help="Optional local Phase 2 progress JSON path used with --phase2-target.",
    )
    parser.add_argument(
        "--phase3-progress",
        help="Optional local Phase 3 progress JSON path.",
    )
    parser.add_argument(
        "--phase3-environment",
        default="",
        help="Optional Phase 3 environment tag, such as quiet_home or cafe.",
    )
    parser.add_argument(
        "--phase3-passive-log",
        action="store_true",
        help="Log normal live classifier windows as Phase 3 passive exposure metadata.",
    )
    parser.add_argument(
        "--phase3-recall-prompt",
        help="Optional Phase 3 recall prompt id for live active-recall checks.",
    )
    parser.add_argument("--phase3-user-response", help="User response for Phase 3 recall.")
    parser.add_argument("--phase3-user-rating", type=int, help="Optional Phase 3 recall rating.")
    parser.add_argument(
        "--phase3-reaction-time-ms",
        type=float,
        help="Optional Phase 3 recall reaction time in milliseconds.",
    )
    parser.add_argument(
        "--scan-timeout",
        type=float,
        default=5.0,
        help="BLE scan timeout in seconds.",
    )
    args = parser.parse_args()

    if args.phase3_passive_log and not args.phase3_progress:
        parser.error("--phase3-progress is required when --phase3-passive-log is enabled.")

    if args.sound_class:
        asyncio.run(_run_manual(args))
        return

    if not args.model or not args.labels:
        parser.error("--model and --labels are required unless --manual-sound is used.")

    asyncio.run(_run_live(args))


if __name__ == "__main__":
    main()
