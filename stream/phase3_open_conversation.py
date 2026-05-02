"""
phase3_open_conversation.py – local Phase 3 open-conversation helpers.

Phase 3 is the aids-free neuroplasticity training stage for passive daily
wear plus periodic active-recall checks.  This module deliberately stores
only derived classifier, haptic, timing, and user-response metadata; it never
stores raw audio, waveforms, speaker embeddings, cloud identifiers, or
clinical claims.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from stream.haptic_mapper import PATTERN_IDS, SUPPORTED_SOUND_CLASSES
from stream.sound_classifier import DEFAULT_MIN_CONFIDENCE

SCHEMA_VERSION = "openhear-phase3-progress-v1"
OUTCOME_CORRECT = "correct"
OUTCOME_PARTIAL = "partial"
OUTCOME_INCORRECT = "incorrect"
OUTCOME_MISSED = "missed"
OUTCOME_SILENCE = "silence"
OUTCOME_SKIPPED = "skipped"

_RECALL_SUCCESS_OUTCOMES = {OUTCOME_CORRECT, OUTCOME_PARTIAL}
_FORBIDDEN_EVENT_FIELDS = {
    "raw_audio",
    "audio",
    "waveform",
    "samples",
    "speaker_embedding",
    "speaker_embeddings",
    "cloud_id",
    "medical_claim",
    "clinical_claim",
}
_REQUIRED_PASSIVE_FIELDS = (
    "session_id",
    "timestamp",
    "environment_tag",
    "predicted_sound_class",
    "source_label",
    "confidence",
    "intensity",
    "pattern_id",
    "duration_seconds",
    "is_conversation",
)
_REQUIRED_RECALL_FIELDS = (
    "session_id",
    "timestamp",
    "prompt_id",
    "expected_sound_class",
    "predicted_sound_class",
    "confidence",
    "user_response",
    "outcome",
)
_OPTIONAL_RECALL_FIELDS = ("reaction_time_ms", "user_rating", "notes", "environment_tag")


@dataclass(frozen=True)
class Phase3PassiveEvent:
    """One passive open-conversation exposure window."""

    session_id: str
    timestamp: str
    environment_tag: str
    predicted_sound_class: str
    source_label: str
    confidence: float
    intensity: int
    pattern_id: int
    duration_seconds: float
    is_conversation: bool = False

    @property
    def is_voice_exposure(self) -> bool:
        """Return true when this event likely represents conversation."""
        return self.is_conversation or self.predicted_sound_class == "voice"


@dataclass(frozen=True)
class Phase3RecallPrompt:
    """One stable Phase 3 active-recall prompt."""

    prompt_id: str
    prompt_type: str
    display_label: str
    expected_sound_class: str | None
    difficulty: int
    active: bool = True


@dataclass(frozen=True)
class Phase3RecallEvent:
    """One periodic active-recall check."""

    session_id: str
    timestamp: str
    prompt_id: str
    expected_sound_class: str | None
    predicted_sound_class: str
    confidence: float
    user_response: str
    outcome: str
    reaction_time_ms: float | None = None
    user_rating: int | None = None
    notes: str = ""
    environment_tag: str = ""

    @property
    def is_success(self) -> bool:
        """Return true for exact or category-level Phase 3 recall success."""
        return self.outcome in _RECALL_SUCCESS_OUTCOMES


@dataclass(frozen=True)
class Phase3SessionSummary:
    """Aggregated Phase 3 passive-wear and active-recall metrics."""

    session_id: str | None
    passive_windows: int
    conversation_windows: int
    passive_duration_seconds: float
    recall_attempts: int
    recall_successes: int
    recall_accuracy: float
    average_confidence: float
    average_reaction_time_ms: float | None
    active_days: int
    by_environment: dict[str, dict[str, int | float]]


DEFAULT_PROMPTS: tuple[Phase3RecallPrompt, ...] = (
    Phase3RecallPrompt("conversation_present", "presence", "Did someone speak?", "voice", 1),
    Phase3RecallPrompt("classify_voice", "classification", "Was that speech?", "voice", 1),
    Phase3RecallPrompt("classify_music", "classification", "Was that music or media?", "media", 1),
    Phase3RecallPrompt("classify_traffic", "classification", "Was that traffic?", "traffic", 2),
    Phase3RecallPrompt(
        "classify_alarm", "classification", "Was that an alert or alarm?", "alarm", 2
    ),
    Phase3RecallPrompt("classify_silence", "classification", "Was that silence?", "silence", 1),
    Phase3RecallPrompt(
        "last_cue_important", "importance", "Was the last cue important?", "voice", 2
    ),
    Phase3RecallPrompt(
        "automatic_vibration_rating",
        "integration_rating",
        "Rate how automatic the vibration felt.",
        None,
        3,
    ),
)

_PROMPTS_BY_ID: dict[str, Phase3RecallPrompt] = {
    prompt.prompt_id: prompt for prompt in DEFAULT_PROMPTS
}
_RESPONSE_ALIASES: dict[str, str] = {
    "yes": "voice",
    "y": "voice",
    "spoken": "voice",
    "speech": "voice",
    "conversation": "voice",
    "someone spoke": "voice",
    "music": "media",
    "media": "media",
    "alarm": "alarm",
    "alert": "alarm",
    "siren": "alarm",
    "traffic": "traffic",
    "car": "traffic",
    "vehicle": "traffic",
    "doorbell": "doorbell",
    "dog": "dog",
    "bark": "dog",
    "silence": "silence",
    "silent": "silence",
    "none": "silence",
    "no": "silence",
    "n": "silence",
}


def list_prompts(*, active_only: bool = True) -> list[Phase3RecallPrompt]:
    """Return Phase 3 active-recall prompts in stable catalog order."""
    if active_only:
        return [prompt for prompt in DEFAULT_PROMPTS if prompt.active]
    return list(DEFAULT_PROMPTS)


def get_prompt(prompt_id: str) -> Phase3RecallPrompt:
    """Return one Phase 3 prompt by stable id."""
    try:
        return _PROMPTS_BY_ID[prompt_id]
    except KeyError as exc:
        raise KeyError(f"Unknown Phase 3 recall prompt {prompt_id!r}.") from exc


def prompt_to_sound_class(prompt_id: str) -> str | None:
    """Return the expected OpenHear sound class for a prompt, if any."""
    return get_prompt(prompt_id).expected_sound_class


class Phase3OpenConversationSession:
    """Track passive open-conversation exposure and active recall locally."""

    def __init__(self, *, session_id: str | None = None) -> None:
        self.session_id = session_id or f"phase3-{uuid4()}"
        self.passive_events: list[Phase3PassiveEvent] = []
        self.recall_events: list[Phase3RecallEvent] = []

    def record_passive(
        self,
        predicted_sound_class: str,
        *,
        source_label: str,
        confidence: float,
        intensity: int,
        pattern_id: int,
        duration_seconds: float,
        environment_tag: str = "",
        is_conversation: bool | None = None,
    ) -> Phase3PassiveEvent:
        """Record one passive classifier/haptic window without raw audio."""
        _validate_sound_class(predicted_sound_class)
        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive.")
        event = Phase3PassiveEvent(
            session_id=self.session_id,
            timestamp=datetime.now(UTC).isoformat(),
            environment_tag=environment_tag,
            predicted_sound_class=predicted_sound_class,
            source_label=source_label,
            confidence=float(confidence),
            intensity=_clamp_byte(intensity),
            pattern_id=int(pattern_id),
            duration_seconds=float(duration_seconds),
            is_conversation=(predicted_sound_class == "voice")
            if is_conversation is None
            else bool(is_conversation),
        )
        self.passive_events.append(event)
        return event

    def record_recall(
        self,
        prompt_id: str,
        *,
        predicted_sound_class: str,
        confidence: float,
        user_response: str = "",
        reaction_time_ms: float | None = None,
        user_rating: int | None = None,
        notes: str = "",
        environment_tag: str = "",
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    ) -> Phase3RecallEvent:
        """Record and score one active-recall check."""
        prompt = get_prompt(prompt_id)
        _validate_sound_class(predicted_sound_class)
        outcome = score_recall(
            prompt,
            predicted_sound_class=predicted_sound_class,
            confidence=confidence,
            user_response=user_response,
            user_rating=user_rating,
            min_confidence=min_confidence,
        )
        event = Phase3RecallEvent(
            session_id=self.session_id,
            timestamp=datetime.now(UTC).isoformat(),
            prompt_id=prompt.prompt_id,
            expected_sound_class=prompt.expected_sound_class,
            predicted_sound_class=predicted_sound_class,
            confidence=float(confidence),
            user_response=user_response,
            outcome=outcome,
            reaction_time_ms=reaction_time_ms,
            user_rating=user_rating,
            notes=notes,
            environment_tag=environment_tag,
        )
        self.recall_events.append(event)
        return event

    def extend_from_store(self, store: "Phase3ProgressStore") -> None:
        """Load historical events from *store* into this session."""
        data = store.load()
        self.passive_events.extend(
            _passive_event_from_mapping(raw_event) for raw_event in data["passive_events"]
        )
        self.recall_events.extend(
            _recall_event_from_mapping(raw_event) for raw_event in data["recall_events"]
        )

    def summary(self) -> Phase3SessionSummary:
        """Return rolling Phase 3 adaptation metrics for this session."""
        return summarise_events(
            self.passive_events,
            self.recall_events,
            session_id=self.session_id,
        )


class Phase3ProgressStore:
    """Append-only local JSON store for Phase 3 derived progress metadata."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, object]:
        """Load the progress document, or return an empty v1 document."""
        if not self.path.exists():
            return {"schema_version": SCHEMA_VERSION, "passive_events": [], "recall_events": []}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"Unsupported Phase 3 progress schema: {data.get('schema_version')!r}")
        for key in ("passive_events", "recall_events"):
            if key not in data or not isinstance(data[key], list):
                raise ValueError(f"Phase 3 progress file must contain a {key} list.")
        return data

    def append_passive(self, event: Phase3PassiveEvent) -> dict[str, object]:
        """Append one passive event and write the local JSON progress file."""
        data = self.load()
        passive_events = data["passive_events"]
        assert isinstance(passive_events, list)
        passive_events.append(asdict(event))
        return self._write(data)

    def append_recall(self, event: Phase3RecallEvent) -> dict[str, object]:
        """Append one recall event and write the local JSON progress file."""
        data = self.load()
        recall_events = data["recall_events"]
        assert isinstance(recall_events, list)
        recall_events.append(asdict(event))
        return self._write(data)

    def _write(self, data: dict[str, object]) -> dict[str, object]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return data


def score_recall(
    prompt: Phase3RecallPrompt,
    *,
    predicted_sound_class: str,
    confidence: float,
    user_response: str = "",
    user_rating: int | None = None,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> str:
    """Score one active recall check with transparent, non-clinical outcomes."""
    _validate_sound_class(predicted_sound_class)
    response = user_response.strip().lower()
    if response in {"skip", "skipped"}:
        return OUTCOME_SKIPPED

    expected = prompt.expected_sound_class
    response_class = normalise_user_response(user_response)
    if expected is None:
        return OUTCOME_CORRECT if response or user_rating is not None else OUTCOME_MISSED
    if not response:
        return OUTCOME_MISSED
    if predicted_sound_class == "silence":
        if expected == "silence" and response_class == "silence":
            return OUTCOME_CORRECT
        return OUTCOME_SILENCE
    if confidence < min_confidence:
        return OUTCOME_SILENCE
    if response_class == expected and predicted_sound_class == expected:
        return OUTCOME_CORRECT
    if response_class == expected or predicted_sound_class == expected:
        return OUTCOME_PARTIAL
    return OUTCOME_INCORRECT


def normalise_user_response(value: str) -> str | None:
    """Collapse a user response into a stable OpenHear sound class when possible."""
    response = value.lower().strip()
    if response in SUPPORTED_SOUND_CLASSES:
        return response
    return _RESPONSE_ALIASES.get(response)


def summarise_events(
    passive_events: list[Phase3PassiveEvent],
    recall_events: list[Phase3RecallEvent],
    *,
    session_id: str | None = None,
) -> Phase3SessionSummary:
    """Aggregate passive and recall events into Phase 3 metrics."""
    passive_windows = len(passive_events)
    conversation_windows = sum(1 for event in passive_events if event.is_voice_exposure)
    passive_duration = sum(event.duration_seconds for event in passive_events)
    recall_attempts = len(recall_events)
    recall_successes = sum(1 for event in recall_events if event.is_success)
    confidence_values = [event.confidence for event in passive_events + recall_events]
    reaction_times = [
        event.reaction_time_ms for event in recall_events if event.reaction_time_ms is not None
    ]
    active_days = len(
        {
            event.timestamp[:10]
            for event in [*passive_events, *recall_events]
            if len(event.timestamp) >= 10
        }
    )
    by_environment = _summarise_by_environment(passive_events, recall_events)
    return Phase3SessionSummary(
        session_id=session_id,
        passive_windows=passive_windows,
        conversation_windows=conversation_windows,
        passive_duration_seconds=passive_duration,
        recall_attempts=recall_attempts,
        recall_successes=recall_successes,
        recall_accuracy=recall_successes / recall_attempts if recall_attempts else 0.0,
        average_confidence=sum(confidence_values) / len(confidence_values)
        if confidence_values
        else 0.0,
        average_reaction_time_ms=sum(reaction_times) / len(reaction_times)
        if reaction_times
        else None,
        active_days=active_days,
        by_environment=by_environment,
    )


def _summarise_by_environment(
    passive_events: list[Phase3PassiveEvent], recall_events: list[Phase3RecallEvent]
) -> dict[str, dict[str, int | float]]:
    environment_stats: dict[str, dict[str, int | float]] = {}
    for event in passive_events:
        key = event.environment_tag or "unspecified"
        bucket = environment_stats.setdefault(
            key,
            {
                "passive_windows": 0,
                "conversation_windows": 0,
                "passive_duration_seconds": 0.0,
                "recall_attempts": 0,
                "recall_successes": 0,
                "recall_accuracy": 0.0,
            },
        )
        bucket["passive_windows"] = int(bucket["passive_windows"]) + 1
        bucket["passive_duration_seconds"] = float(bucket["passive_duration_seconds"]) + float(
            event.duration_seconds
        )
        if event.is_voice_exposure:
            bucket["conversation_windows"] = int(bucket["conversation_windows"]) + 1

    for event in recall_events:
        key = event.environment_tag or "unspecified"
        bucket = environment_stats.setdefault(
            key,
            {
                "passive_windows": 0,
                "conversation_windows": 0,
                "passive_duration_seconds": 0.0,
                "recall_attempts": 0,
                "recall_successes": 0,
                "recall_accuracy": 0.0,
            },
        )
        bucket["recall_attempts"] = int(bucket["recall_attempts"]) + 1
        if event.is_success:
            bucket["recall_successes"] = int(bucket["recall_successes"]) + 1

    for bucket in environment_stats.values():
        attempts = int(bucket["recall_attempts"])
        bucket["recall_accuracy"] = int(bucket["recall_successes"]) / attempts if attempts else 0.0
    return environment_stats


def _passive_event_from_mapping(raw_event: object) -> Phase3PassiveEvent:
    if not isinstance(raw_event, dict):
        raise ValueError("Phase 3 passive events must be JSON objects.")
    _reject_forbidden_fields(raw_event)
    missing = [field for field in _REQUIRED_PASSIVE_FIELDS if field not in raw_event]
    if missing:
        raise ValueError(f"Phase 3 passive event is missing fields: {', '.join(missing)}")
    payload = {field: raw_event[field] for field in _REQUIRED_PASSIVE_FIELDS}
    return Phase3PassiveEvent(**payload)


def _recall_event_from_mapping(raw_event: object) -> Phase3RecallEvent:
    if not isinstance(raw_event, dict):
        raise ValueError("Phase 3 recall events must be JSON objects.")
    _reject_forbidden_fields(raw_event)
    missing = [field for field in _REQUIRED_RECALL_FIELDS if field not in raw_event]
    if missing:
        raise ValueError(f"Phase 3 recall event is missing fields: {', '.join(missing)}")
    payload = {
        field: raw_event[field]
        for field in (*_REQUIRED_RECALL_FIELDS, *_OPTIONAL_RECALL_FIELDS)
        if field in raw_event
    }
    payload.setdefault("reaction_time_ms", None)
    payload.setdefault("user_rating", None)
    payload.setdefault("notes", "")
    payload.setdefault("environment_tag", "")
    return Phase3RecallEvent(**payload)


def _reject_forbidden_fields(raw_event: dict[str, object]) -> None:
    forbidden = sorted(_FORBIDDEN_EVENT_FIELDS.intersection(raw_event))
    if forbidden:
        raise ValueError(f"Phase 3 progress events cannot contain: {', '.join(forbidden)}")


def _validate_sound_class(sound_class: str) -> None:
    if sound_class not in SUPPORTED_SOUND_CLASSES:
        raise ValueError(
            f"Unsupported sound class {sound_class!r}. "
            f"Expected one of: {', '.join(sorted(SUPPORTED_SOUND_CLASSES))}."
        )


def _clamp_byte(value: int) -> int:
    return max(0, min(255, int(value)))


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenHear Phase 3 open-conversation tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-prompts", help="List built-in Phase 3 prompts.")
    list_parser.add_argument("--all", action="store_true", help="Include inactive prompts.")

    passive_parser = subparsers.add_parser("passive", help="Append one passive Phase 3 event.")
    passive_parser.add_argument("--sound-class", required=True, choices=SUPPORTED_SOUND_CLASSES)
    passive_parser.add_argument("--source-label", default="manual")
    passive_parser.add_argument("--confidence", type=float, default=1.0)
    passive_parser.add_argument("--intensity", type=int, default=0)
    passive_parser.add_argument("--pattern-id", type=int)
    passive_parser.add_argument("--duration-seconds", type=float, default=0.975)
    passive_parser.add_argument("--environment", default="")
    passive_parser.add_argument("--session-id")
    passive_parser.add_argument("--progress", required=True)

    recall_parser = subparsers.add_parser("recall", help="Append one Phase 3 recall check.")
    recall_parser.add_argument("--prompt", required=True)
    recall_parser.add_argument("--predicted-class", required=True, choices=SUPPORTED_SOUND_CLASSES)
    recall_parser.add_argument("--confidence", type=float, default=1.0)
    recall_parser.add_argument("--user-response", default="")
    recall_parser.add_argument("--reaction-time-ms", type=float)
    recall_parser.add_argument("--user-rating", type=int)
    recall_parser.add_argument("--notes", default="")
    recall_parser.add_argument("--environment", default="")
    recall_parser.add_argument("--session-id")
    recall_parser.add_argument("--progress", required=True)

    summary_parser = subparsers.add_parser("summary", help="Summarise a Phase 3 progress file.")
    summary_parser.add_argument("--progress", required=True)

    args = parser.parse_args()
    if args.command == "list-prompts":
        _print_json([asdict(prompt) for prompt in list_prompts(active_only=not args.all)])
        return

    if args.command == "passive":
        session = Phase3OpenConversationSession(session_id=args.session_id)
        event = session.record_passive(
            args.sound_class,
            source_label=args.source_label,
            confidence=args.confidence,
            intensity=args.intensity,
            pattern_id=args.pattern_id
            if args.pattern_id is not None
            else PATTERN_IDS[args.sound_class],
            duration_seconds=args.duration_seconds,
            environment_tag=args.environment,
        )
        Phase3ProgressStore(args.progress).append_passive(event)
        _print_json({"event": asdict(event), "summary": asdict(session.summary())})
        return

    if args.command == "recall":
        session = Phase3OpenConversationSession(session_id=args.session_id)
        event = session.record_recall(
            args.prompt,
            predicted_sound_class=args.predicted_class,
            confidence=args.confidence,
            user_response=args.user_response,
            reaction_time_ms=args.reaction_time_ms,
            user_rating=args.user_rating,
            notes=args.notes,
            environment_tag=args.environment,
        )
        Phase3ProgressStore(args.progress).append_recall(event)
        _print_json({"event": asdict(event), "summary": asdict(session.summary())})
        return

    if args.command == "summary":
        store = Phase3ProgressStore(args.progress)
        data = store.load()
        passive_events = [
            _passive_event_from_mapping(raw_event) for raw_event in data["passive_events"]
        ]
        recall_events = [
            _recall_event_from_mapping(raw_event) for raw_event in data["recall_events"]
        ]
        _print_json(asdict(summarise_events(passive_events, recall_events)))


if __name__ == "__main__":
    main()
