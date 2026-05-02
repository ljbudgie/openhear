"""
phase2_training.py – local Phase 2 word/environment training helpers.

Phase 2 is the aids-free neuroplasticity training stage for closed-set words,
names, alarms, traffic, and environmental sounds.  This module deliberately
stores only classifier labels, scores, timing, and outcomes; it never stores
raw audio.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from stream.sound_classifier import DEFAULT_MIN_CONFIDENCE, classify_scores

SCHEMA_VERSION = "openhear-phase2-progress-v1"
OUTCOME_CORRECT = "correct"
OUTCOME_PARTIAL = "partial"
OUTCOME_INCORRECT = "incorrect"
OUTCOME_SILENCE = "silence"
_REQUIRED_EVENT_FIELDS = (
    "session_id",
    "timestamp",
    "target_id",
    "predicted_target_id",
    "predicted_sound_class",
    "source_label",
    "confidence",
    "outcome",
)
_OPTIONAL_EVENT_FIELDS = ("reaction_time_ms", "user_rating")


@dataclass(frozen=True)
class Phase2Target:
    """One stable Phase 2 training target."""

    target_id: str
    display_label: str
    target_type: str
    expected_sound_class: str
    dominant_frequency_hz: int | None
    difficulty: int
    active: bool = True


@dataclass(frozen=True)
class Phase2Evaluation:
    """Result of scoring one classifier output against one Phase 2 target."""

    session_id: str
    timestamp: str
    target_id: str
    predicted_target_id: str | None
    predicted_sound_class: str
    source_label: str
    confidence: float
    outcome: str
    reaction_time_ms: float | None = None
    user_rating: int | None = None

    @property
    def is_success(self) -> bool:
        """Return true for exact or category-level success."""
        return self.outcome in {OUTCOME_CORRECT, OUTCOME_PARTIAL}


DEFAULT_TARGETS: tuple[Phase2Target, ...] = (
    Phase2Target("alarm_smoke", "Smoke alarm", "alarm", "alarm", 3150, 1),
    Phase2Target("alarm_siren", "Siren", "alarm", "alarm", 3150, 1),
    Phase2Target("alarm_timer", "Timer alarm", "alarm", "alarm", 2000, 2),
    Phase2Target("env_doorbell", "Doorbell", "environment", "doorbell", 2000, 1),
    Phase2Target("traffic_car", "Car", "traffic", "traffic", 500, 1),
    Phase2Target("traffic_truck", "Truck", "traffic", "traffic", 500, 2),
    Phase2Target("traffic_horn", "Vehicle horn", "traffic", "traffic", 1000, 2),
    Phase2Target("traffic_motorcycle", "Motorcycle", "traffic", "traffic", 500, 2),
    Phase2Target("env_dog_bark", "Dog bark", "environment", "dog", 500, 1),
    Phase2Target("env_knock", "Knocking", "environment", "doorbell", 1000, 2),
    Phase2Target("env_phone", "Phone ringing", "environment", "alarm", 2000, 2),
    Phase2Target("word_yes", "Yes", "word", "voice", 1000, 1),
    Phase2Target("word_no", "No", "word", "voice", 1000, 1),
    Phase2Target("word_help", "Help", "word", "voice", 1000, 1),
    Phase2Target("word_stop", "Stop", "word", "voice", 1000, 1),
    Phase2Target("name_placeholder", "Configured name", "name", "voice", 1000, 2),
)

_TARGETS_BY_ID: dict[str, Phase2Target] = {target.target_id: target for target in DEFAULT_TARGETS}

_TARGET_KEYWORDS: dict[str, tuple[str, ...]] = {
    "alarm_smoke": ("smoke alarm", "smoke detector", "fire alarm"),
    "alarm_siren": ("siren", "emergency vehicle"),
    "alarm_timer": ("timer", "alarm clock", "buzzer"),
    "env_doorbell": ("doorbell", "ding-dong", "chime"),
    "traffic_car": ("car", "automobile"),
    "traffic_truck": ("truck", "lorry"),
    "traffic_horn": ("horn", "vehicle horn", "car horn"),
    "traffic_motorcycle": ("motorcycle", "motorbike"),
    "env_dog_bark": ("dog", "bark", "bow-wow", "howl"),
    "env_knock": ("knock", "knocking", "tap"),
    "env_phone": ("telephone", "phone", "ringtone", "ringing"),
    "word_yes": ("word yes", "spoken yes", "yes"),
    "word_no": ("word no", "spoken no", "no"),
    "word_help": ("word help", "spoken help", "help"),
    "word_stop": ("word stop", "spoken stop", "stop"),
    "name_placeholder": ("name", "called name", "wake word"),
}


def list_targets(*, active_only: bool = True) -> list[Phase2Target]:
    """Return Phase 2 training targets in stable catalog order."""
    if active_only:
        return [target for target in DEFAULT_TARGETS if target.active]
    return list(DEFAULT_TARGETS)


def get_target(target_id: str) -> Phase2Target:
    """Return one Phase 2 target by stable id."""
    try:
        return _TARGETS_BY_ID[target_id]
    except KeyError as exc:
        raise KeyError(f"Unknown Phase 2 target {target_id!r}.") from exc


def target_to_sound_class(target_id: str) -> str:
    """Collapse a detailed Phase 2 target to the stable wristband sound class."""
    return get_target(target_id).expected_sound_class


def map_label_to_phase2_target(label: str) -> Phase2Target | None:
    """Map a classifier label to a detailed Phase 2 target when possible."""
    label_normalised = label.lower().strip()
    for target in DEFAULT_TARGETS:
        keywords = _TARGET_KEYWORDS[target.target_id]
        if any(keyword in label_normalised for keyword in keywords):
            return target
    return None


def classify_phase2_scores(
    scores_by_label: dict[str, float],
    *,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> tuple[Phase2Target | None, str, str, float]:
    """Return ``(target, sound_class, source_label, confidence)`` for scores."""
    best_target: Phase2Target | None = None
    best_score = 0.0
    best_label = "silence"

    for label, score in scores_by_label.items():
        target = map_label_to_phase2_target(label)
        if target is None:
            continue
        score_float = float(score)
        if score_float > best_score:
            best_target = target
            best_score = score_float
            best_label = label

    if best_target is not None and best_score >= min_confidence:
        return best_target, best_target.expected_sound_class, best_label, best_score

    classified = classify_scores(scores_by_label, min_confidence=min_confidence)
    return None, classified.sound_key, classified.source_label, classified.confidence


class Phase2TrainingSession:
    """Score Phase 2 classifier outputs and track rolling accuracy."""

    def __init__(self, *, session_id: str | None = None) -> None:
        self.session_id = session_id or f"phase2-{uuid4()}"
        self.events: list[Phase2Evaluation] = []

    def evaluate_scores(
        self,
        target_id: str,
        scores_by_label: dict[str, float],
        *,
        reaction_time_ms: float | None = None,
        user_rating: int | None = None,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    ) -> Phase2Evaluation:
        """Evaluate classifier scores for one prompted target."""
        target = get_target(target_id)
        predicted_target, predicted_sound_class, source_label, confidence = classify_phase2_scores(
            scores_by_label,
            min_confidence=min_confidence,
        )
        outcome = _score_outcome(target, predicted_target, predicted_sound_class, confidence)
        event = Phase2Evaluation(
            session_id=self.session_id,
            timestamp=datetime.now(UTC).isoformat(),
            target_id=target.target_id,
            predicted_target_id=predicted_target.target_id if predicted_target else None,
            predicted_sound_class=predicted_sound_class,
            source_label=source_label,
            confidence=confidence,
            outcome=outcome,
            reaction_time_ms=reaction_time_ms,
            user_rating=user_rating,
        )
        self.events.append(event)
        return event

    def summary(self) -> dict[str, object]:
        """Return rolling accuracy metrics for the current session."""
        total = len(self.events)
        successes = sum(1 for event in self.events if event.is_success)
        by_type: dict[str, dict[str, int | float]] = {}
        for event in self.events:
            target_type = get_target(event.target_id).target_type
            bucket = by_type.setdefault(
                target_type, {"attempts": 0, "successes": 0, "accuracy": 0.0}
            )
            bucket["attempts"] = int(bucket["attempts"]) + 1
            if event.is_success:
                bucket["successes"] = int(bucket["successes"]) + 1

        for bucket in by_type.values():
            attempts = int(bucket["attempts"])
            bucket["accuracy"] = float(bucket["successes"]) / attempts if attempts else 0.0

        return {
            "session_id": self.session_id,
            "attempts": total,
            "successes": successes,
            "accuracy": successes / total if total else 0.0,
            "by_target_type": by_type,
        }


class Phase2ProgressStore:
    """Append-only local JSON store for Phase 2 progress events."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, object]:
        """Load the progress document, or return an empty v1 document."""
        if not self.path.exists():
            return {"schema_version": SCHEMA_VERSION, "events": []}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"Unsupported Phase 2 progress schema: {data.get('schema_version')!r}")
        if "events" not in data or not isinstance(data["events"], list):
            raise ValueError("Phase 2 progress file must contain an events list.")
        return data

    def append(self, event: Phase2Evaluation) -> dict[str, object]:
        """Append one event and write the local JSON progress file."""
        data = self.load()
        events = data["events"]
        assert isinstance(events, list)
        events.append(asdict(event))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return data


def _score_outcome(
    target: Phase2Target,
    predicted_target: Phase2Target | None,
    predicted_sound_class: str,
    confidence: float,
) -> str:
    if confidence <= 0.0 or predicted_sound_class == "silence":
        return OUTCOME_SILENCE
    if predicted_target and predicted_target.target_id == target.target_id:
        return OUTCOME_CORRECT
    if predicted_sound_class == target.expected_sound_class:
        return OUTCOME_PARTIAL
    return OUTCOME_INCORRECT


def _parse_score(value: str) -> tuple[str, float]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("scores must use LABEL=CONFIDENCE syntax")
    label, score = value.split("=", 1)
    label = label.strip()
    if not label:
        raise argparse.ArgumentTypeError("score label cannot be empty")
    try:
        confidence = float(score)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("score confidence must be a number") from exc
    return label, confidence


def _event_from_mapping(raw_event: object) -> Phase2Evaluation:
    if not isinstance(raw_event, dict):
        raise ValueError("Phase 2 progress events must be JSON objects.")

    missing = [field for field in _REQUIRED_EVENT_FIELDS if field not in raw_event]
    if missing:
        raise ValueError(f"Phase 2 progress event is missing fields: {', '.join(missing)}")

    payload = {
        field: raw_event[field]
        for field in (*_REQUIRED_EVENT_FIELDS, *_OPTIONAL_EVENT_FIELDS)
        if field in raw_event
    }
    payload.setdefault("reaction_time_ms", None)
    payload.setdefault("user_rating", None)
    return Phase2Evaluation(**payload)


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenHear Phase 2 training dry-run tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List built-in Phase 2 targets.")
    list_parser.add_argument("--all", action="store_true", help="Include inactive targets.")

    run_parser = subparsers.add_parser("run", help="Score one dry-run Phase 2 attempt.")
    run_parser.add_argument("--target", required=True, help="Target id from the Phase 2 catalog.")
    run_parser.add_argument(
        "--score",
        action="append",
        required=True,
        type=_parse_score,
        help="Classifier score as LABEL=CONFIDENCE. May be repeated.",
    )
    run_parser.add_argument("--session-id", help="Existing session id to reuse.")
    run_parser.add_argument("--progress", help="Optional local JSON progress path.")
    run_parser.add_argument("--reaction-time-ms", type=float)
    run_parser.add_argument("--user-rating", type=int)

    summary_parser = subparsers.add_parser("summary", help="Summarise a progress JSON file.")
    summary_parser.add_argument("--progress", required=True, help="Local JSON progress path.")

    args = parser.parse_args()
    if args.command == "list":
        _print_json([asdict(target) for target in list_targets(active_only=not args.all)])
        return

    if args.command == "run":
        session = Phase2TrainingSession(session_id=args.session_id)
        event = session.evaluate_scores(
            args.target,
            dict(args.score),
            reaction_time_ms=args.reaction_time_ms,
            user_rating=args.user_rating,
        )
        if args.progress:
            Phase2ProgressStore(args.progress).append(event)
        _print_json({"event": asdict(event), "summary": session.summary()})
        return

    if args.command == "summary":
        data = Phase2ProgressStore(args.progress).load()
        raw_events = [_event_from_mapping(raw_event) for raw_event in data["events"]]
        first_session_id = raw_events[0].session_id if raw_events else None
        session = Phase2TrainingSession(session_id=first_session_id)
        session.events.extend(raw_events)
        _print_json(session.summary())


if __name__ == "__main__":
    main()
