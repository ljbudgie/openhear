"""
phase4_spatial_extended.py – local Phase 4 spatial/extended helpers.

Phase 4 is the aids-free neuroplasticity training stage for direction,
elevation, and extended-band haptic perception.  This module stores only
derived localization, haptic, timing, and user-response metadata; it never
stores raw audio, waveforms, location traces, biometric identifiers, cloud
identifiers, or clinical claims.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from stream.sound_classifier import DEFAULT_MIN_CONFIDENCE

SCHEMA_VERSION = "openhear-phase4-progress-v1"
OUTCOME_CORRECT = "correct"
OUTCOME_PARTIAL = "partial"
OUTCOME_INCORRECT = "incorrect"
OUTCOME_MISSED = "missed"
OUTCOME_SILENCE = "silence"
OUTCOME_SKIPPED = "skipped"

TASK_SPATIAL = "spatial"
TASK_EXTENDED_BAND = "extended_band"
EXTENDED_BANDS = ("infrasonic", "tactile_low", "speech", "high_frequency", "ultrasonic")
_SUCCESS_OUTCOMES = {OUTCOME_CORRECT, OUTCOME_PARTIAL}
_FORBIDDEN_EVENT_FIELDS = {
    "raw_audio",
    "audio",
    "waveform",
    "samples",
    "gps",
    "location_trace",
    "biometric_id",
    "cloud_id",
    "medical_claim",
    "clinical_claim",
}
_REQUIRED_SPATIAL_FIELDS = (
    "session_id",
    "timestamp",
    "task_id",
    "expected_azimuth_degrees",
    "predicted_azimuth_degrees",
    "azimuth_error_degrees",
    "expected_elevation_degrees",
    "predicted_elevation_degrees",
    "elevation_error_degrees",
    "confidence",
    "outcome",
)
_OPTIONAL_SPATIAL_FIELDS = ("reaction_time_ms", "user_rating", "environment_tag", "notes")
_REQUIRED_EXTENDED_FIELDS = (
    "session_id",
    "timestamp",
    "task_id",
    "expected_band",
    "predicted_band",
    "confidence",
    "outcome",
)
_OPTIONAL_EXTENDED_FIELDS = ("reaction_time_ms", "user_rating", "environment_tag", "notes")


@dataclass(frozen=True)
class Phase4Task:
    """One stable Phase 4 training task."""

    task_id: str
    display_label: str
    task_type: str
    expected_azimuth_degrees: float | None
    expected_elevation_degrees: float | None
    expected_band: str | None
    azimuth_tolerance_degrees: float
    elevation_tolerance_degrees: float
    difficulty: int
    active: bool = True


@dataclass(frozen=True)
class Phase4SpatialEvent:
    """One derived spatial-localization check."""

    session_id: str
    timestamp: str
    task_id: str
    expected_azimuth_degrees: float
    predicted_azimuth_degrees: float
    azimuth_error_degrees: float
    expected_elevation_degrees: float
    predicted_elevation_degrees: float
    elevation_error_degrees: float
    confidence: float
    outcome: str
    reaction_time_ms: float | None = None
    user_rating: int | None = None
    environment_tag: str = ""
    notes: str = ""

    @property
    def is_success(self) -> bool:
        """Return true for exact or near Phase 4 spatial success."""
        return self.outcome in _SUCCESS_OUTCOMES


@dataclass(frozen=True)
class Phase4ExtendedBandEvent:
    """One derived extended-band recognition check."""

    session_id: str
    timestamp: str
    task_id: str
    expected_band: str
    predicted_band: str
    confidence: float
    outcome: str
    reaction_time_ms: float | None = None
    user_rating: int | None = None
    environment_tag: str = ""
    notes: str = ""

    @property
    def is_success(self) -> bool:
        """Return true for exact or category-level Phase 4 band success."""
        return self.outcome in _SUCCESS_OUTCOMES


@dataclass(frozen=True)
class Phase4SessionSummary:
    """Aggregated Phase 4 spatial and extended-band metrics."""

    session_id: str | None
    spatial_attempts: int
    spatial_successes: int
    spatial_accuracy: float
    average_azimuth_error_degrees: float | None
    average_elevation_error_degrees: float | None
    extended_attempts: int
    extended_successes: int
    extended_accuracy: float
    average_confidence: float
    average_reaction_time_ms: float | None
    active_days: int
    by_band: dict[str, dict[str, int | float]]
    by_environment: dict[str, dict[str, int | float]]


DEFAULT_TASKS: tuple[Phase4Task, ...] = (
    Phase4Task(
        "localise_front", "Localise sound in front", TASK_SPATIAL, 0.0, 0.0, None, 30.0, 20.0, 1
    ),
    Phase4Task(
        "localise_left", "Localise sound to the left", TASK_SPATIAL, -90.0, 0.0, None, 30.0, 20.0, 1
    ),
    Phase4Task(
        "localise_right",
        "Localise sound to the right",
        TASK_SPATIAL,
        90.0,
        0.0,
        None,
        30.0,
        20.0,
        1,
    ),
    Phase4Task(
        "localise_behind", "Localise sound behind", TASK_SPATIAL, 180.0, 0.0, None, 35.0, 20.0, 2
    ),
    Phase4Task(
        "elevation_above", "Detect elevated sound", TASK_SPATIAL, 0.0, 45.0, None, 35.0, 20.0, 2
    ),
    Phase4Task(
        "elevation_below", "Detect lowered sound", TASK_SPATIAL, 0.0, -30.0, None, 35.0, 20.0, 2
    ),
    Phase4Task(
        "band_infrasonic",
        "Recognise infrasonic-coded cue",
        TASK_EXTENDED_BAND,
        None,
        None,
        "infrasonic",
        0.0,
        0.0,
        2,
    ),
    Phase4Task(
        "band_high_frequency",
        "Recognise high-frequency-coded cue",
        TASK_EXTENDED_BAND,
        None,
        None,
        "high_frequency",
        0.0,
        0.0,
        2,
    ),
    Phase4Task(
        "band_ultrasonic",
        "Recognise ultrasonic-coded cue",
        TASK_EXTENDED_BAND,
        None,
        None,
        "ultrasonic",
        0.0,
        0.0,
        3,
    ),
)

_TASKS_BY_ID: dict[str, Phase4Task] = {task.task_id: task for task in DEFAULT_TASKS}
_BAND_ALIASES: dict[str, str] = {
    "infra": "infrasonic",
    "infrasound": "infrasonic",
    "low": "tactile_low",
    "low_tactile": "tactile_low",
    "high": "high_frequency",
    "ultra": "ultrasonic",
    "ultrasound": "ultrasonic",
}


def list_tasks(*, active_only: bool = True) -> list[Phase4Task]:
    """Return Phase 4 training tasks in stable catalog order."""
    if active_only:
        return [task for task in DEFAULT_TASKS if task.active]
    return list(DEFAULT_TASKS)


def get_task(task_id: str) -> Phase4Task:
    """Return one Phase 4 task by stable id."""
    try:
        return _TASKS_BY_ID[task_id]
    except KeyError as exc:
        raise KeyError(f"Unknown Phase 4 task {task_id!r}.") from exc


class Phase4SpatialExtendedSession:
    """Track Phase 4 spatial localization and extended-band checks locally."""

    def __init__(self, *, session_id: str | None = None) -> None:
        self.session_id = session_id or f"phase4-{uuid4()}"
        self.spatial_events: list[Phase4SpatialEvent] = []
        self.extended_events: list[Phase4ExtendedBandEvent] = []

    def record_spatial(
        self,
        task_id: str,
        *,
        predicted_azimuth_degrees: float,
        confidence: float,
        predicted_elevation_degrees: float = 0.0,
        user_response: str = "",
        reaction_time_ms: float | None = None,
        user_rating: int | None = None,
        environment_tag: str = "",
        notes: str = "",
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    ) -> Phase4SpatialEvent:
        """Record and score one spatial-localization check."""
        task = get_task(task_id)
        if task.task_type != TASK_SPATIAL:
            raise ValueError(f"Phase 4 task {task_id!r} is not a spatial task.")
        assert task.expected_azimuth_degrees is not None
        assert task.expected_elevation_degrees is not None
        azimuth_error = angular_error_degrees(
            predicted_azimuth_degrees, task.expected_azimuth_degrees
        )
        elevation_error = abs(float(predicted_elevation_degrees) - task.expected_elevation_degrees)
        outcome = score_spatial(
            task,
            azimuth_error_degrees=azimuth_error,
            elevation_error_degrees=elevation_error,
            confidence=confidence,
            user_response=user_response,
            min_confidence=min_confidence,
        )
        event = Phase4SpatialEvent(
            session_id=self.session_id,
            timestamp=datetime.now(UTC).isoformat(),
            task_id=task.task_id,
            expected_azimuth_degrees=task.expected_azimuth_degrees,
            predicted_azimuth_degrees=normalise_azimuth(predicted_azimuth_degrees),
            azimuth_error_degrees=azimuth_error,
            expected_elevation_degrees=task.expected_elevation_degrees,
            predicted_elevation_degrees=float(predicted_elevation_degrees),
            elevation_error_degrees=elevation_error,
            confidence=float(confidence),
            outcome=outcome,
            reaction_time_ms=reaction_time_ms,
            user_rating=user_rating,
            environment_tag=environment_tag,
            notes=notes,
        )
        self.spatial_events.append(event)
        return event

    def record_extended_band(
        self,
        task_id: str,
        *,
        predicted_band: str,
        confidence: float,
        user_response: str = "",
        reaction_time_ms: float | None = None,
        user_rating: int | None = None,
        environment_tag: str = "",
        notes: str = "",
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    ) -> Phase4ExtendedBandEvent:
        """Record and score one extended-band recognition check."""
        task = get_task(task_id)
        if task.task_type != TASK_EXTENDED_BAND:
            raise ValueError(f"Phase 4 task {task_id!r} is not an extended-band task.")
        assert task.expected_band is not None
        predicted = normalise_band(predicted_band)
        outcome = score_extended_band(
            expected_band=task.expected_band,
            predicted_band=predicted,
            confidence=confidence,
            user_response=user_response,
            min_confidence=min_confidence,
        )
        event = Phase4ExtendedBandEvent(
            session_id=self.session_id,
            timestamp=datetime.now(UTC).isoformat(),
            task_id=task.task_id,
            expected_band=task.expected_band,
            predicted_band=predicted,
            confidence=float(confidence),
            outcome=outcome,
            reaction_time_ms=reaction_time_ms,
            user_rating=user_rating,
            environment_tag=environment_tag,
            notes=notes,
        )
        self.extended_events.append(event)
        return event

    def extend_from_store(self, store: "Phase4ProgressStore") -> None:
        """Load historical events from *store* into this session."""
        data = store.load()
        self.spatial_events.extend(
            _spatial_event_from_mapping(raw_event) for raw_event in data["spatial_events"]
        )
        self.extended_events.extend(
            _extended_event_from_mapping(raw_event) for raw_event in data["extended_events"]
        )

    def summary(self) -> Phase4SessionSummary:
        """Return rolling Phase 4 adaptation metrics for this session."""
        return summarise_events(
            self.spatial_events,
            self.extended_events,
            session_id=self.session_id,
        )


class Phase4ProgressStore:
    """Append-only local JSON store for Phase 4 derived progress metadata."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, object]:
        """Load the progress document, or return an empty v1 document."""
        if not self.path.exists():
            return {"schema_version": SCHEMA_VERSION, "spatial_events": [], "extended_events": []}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"Unsupported Phase 4 progress schema: {data.get('schema_version')!r}")
        for key in ("spatial_events", "extended_events"):
            if key not in data or not isinstance(data[key], list):
                raise ValueError(f"Phase 4 progress file must contain a {key} list.")
        return data

    def append_spatial(self, event: Phase4SpatialEvent) -> dict[str, object]:
        """Append one spatial event and write the local JSON progress file."""
        data = self.load()
        spatial_events = data["spatial_events"]
        assert isinstance(spatial_events, list)
        spatial_events.append(asdict(event))
        return self._write(data)

    def append_extended(self, event: Phase4ExtendedBandEvent) -> dict[str, object]:
        """Append one extended-band event and write the local JSON progress file."""
        normalise_band(event.expected_band)
        normalise_band(event.predicted_band)
        data = self.load()
        extended_events = data["extended_events"]
        assert isinstance(extended_events, list)
        extended_events.append(asdict(event))
        return self._write(data)

    def _write(self, data: dict[str, object]) -> dict[str, object]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return data


def score_spatial(
    task: Phase4Task,
    *,
    azimuth_error_degrees: float,
    elevation_error_degrees: float,
    confidence: float,
    user_response: str = "",
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> str:
    """Score one Phase 4 spatial check with transparent, non-clinical outcomes."""
    response = user_response.strip().lower()
    if response in {"skip", "skipped"}:
        return OUTCOME_SKIPPED
    if response in {"", "miss", "missed"}:
        return OUTCOME_MISSED
    if confidence < min_confidence:
        return OUTCOME_SILENCE
    azimuth_ok = azimuth_error_degrees <= task.azimuth_tolerance_degrees
    elevation_ok = elevation_error_degrees <= task.elevation_tolerance_degrees
    if azimuth_ok and elevation_ok:
        return OUTCOME_CORRECT
    azimuth_near = azimuth_error_degrees <= task.azimuth_tolerance_degrees * 2
    elevation_near = elevation_error_degrees <= task.elevation_tolerance_degrees * 2
    if azimuth_near and elevation_near:
        return OUTCOME_PARTIAL
    return OUTCOME_INCORRECT


def score_extended_band(
    *,
    expected_band: str,
    predicted_band: str,
    confidence: float,
    user_response: str = "",
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> str:
    """Score one Phase 4 extended-band check."""
    expected = normalise_band(expected_band)
    predicted = normalise_band(predicted_band)
    response = user_response.strip().lower()
    if response in {"skip", "skipped"}:
        return OUTCOME_SKIPPED
    response_band = _normalise_band_response(response) if response else None
    if response_band is None:
        return OUTCOME_MISSED
    if confidence < min_confidence or predicted == "silence":
        return OUTCOME_SILENCE
    if predicted == expected and response_band == expected:
        return OUTCOME_CORRECT
    if predicted == expected or response_band == expected:
        return OUTCOME_PARTIAL
    return OUTCOME_INCORRECT


def normalise_azimuth(value: float) -> float:
    """Normalise an azimuth angle into the [-180, 180] degree range."""
    normalised = (float(value) + 180.0) % 360.0 - 180.0
    return 180.0 if normalised == -180.0 else normalised


def angular_error_degrees(a: float, b: float) -> float:
    """Return the smallest absolute angular distance between two azimuths."""
    return abs(normalise_azimuth(float(a) - float(b)))


def normalise_band(value: str) -> str:
    """Collapse a user or classifier band label into a stable Phase 4 band."""
    raw = value.lower().strip()
    band = _normalise_band_key(raw)
    if band in EXTENDED_BANDS or band == "silence":
        return band
    alias = _BAND_ALIASES.get(band)
    if alias in EXTENDED_BANDS or alias == "silence":
        return alias
    raise ValueError(
        f"Unsupported Phase 4 band {value!r}. "
        f"Expected one of: {', '.join((*EXTENDED_BANDS, 'silence'))}."
    )


def _normalise_band_key(value: str) -> str:
    return value.replace("-", "_").replace(" ", "_")


def _normalise_band_response(value: str) -> str | None:
    try:
        return normalise_band(value)
    except ValueError:
        return None


def summarise_events(
    spatial_events: list[Phase4SpatialEvent],
    extended_events: list[Phase4ExtendedBandEvent],
    *,
    session_id: str | None = None,
) -> Phase4SessionSummary:
    """Aggregate Phase 4 events into spatial and extended-band metrics."""
    spatial_attempts = len(spatial_events)
    spatial_successes = sum(1 for event in spatial_events if event.is_success)
    extended_attempts = len(extended_events)
    extended_successes = sum(1 for event in extended_events if event.is_success)
    azimuth_errors = [event.azimuth_error_degrees for event in spatial_events]
    elevation_errors = [event.elevation_error_degrees for event in spatial_events]
    confidence_values = [event.confidence for event in [*spatial_events, *extended_events]]
    reaction_times = [
        event.reaction_time_ms
        for event in [*spatial_events, *extended_events]
        if event.reaction_time_ms is not None
    ]
    active_days = len(
        {
            event.timestamp[:10]
            for event in [*spatial_events, *extended_events]
            if len(event.timestamp) >= 10
        }
    )
    return Phase4SessionSummary(
        session_id=session_id,
        spatial_attempts=spatial_attempts,
        spatial_successes=spatial_successes,
        spatial_accuracy=spatial_successes / spatial_attempts if spatial_attempts else 0.0,
        average_azimuth_error_degrees=sum(azimuth_errors) / len(azimuth_errors)
        if azimuth_errors
        else None,
        average_elevation_error_degrees=sum(elevation_errors) / len(elevation_errors)
        if elevation_errors
        else None,
        extended_attempts=extended_attempts,
        extended_successes=extended_successes,
        extended_accuracy=extended_successes / extended_attempts if extended_attempts else 0.0,
        average_confidence=sum(confidence_values) / len(confidence_values)
        if confidence_values
        else 0.0,
        average_reaction_time_ms=sum(reaction_times) / len(reaction_times)
        if reaction_times
        else None,
        active_days=active_days,
        by_band=_summarise_by_band(extended_events),
        by_environment=_summarise_by_environment(spatial_events, extended_events),
    )


def _summarise_by_band(
    extended_events: list[Phase4ExtendedBandEvent],
) -> dict[str, dict[str, int | float]]:
    band_stats: dict[str, dict[str, int | float]] = {}
    for event in extended_events:
        bucket = band_stats.setdefault(
            event.expected_band, {"attempts": 0, "successes": 0, "accuracy": 0.0}
        )
        bucket["attempts"] = int(bucket["attempts"]) + 1
        if event.is_success:
            bucket["successes"] = int(bucket["successes"]) + 1
    for bucket in band_stats.values():
        attempts = int(bucket["attempts"])
        bucket["accuracy"] = int(bucket["successes"]) / attempts if attempts else 0.0
    return band_stats


def _summarise_by_environment(
    spatial_events: list[Phase4SpatialEvent],
    extended_events: list[Phase4ExtendedBandEvent],
) -> dict[str, dict[str, int | float]]:
    environment_stats: dict[str, dict[str, int | float]] = {}
    for event in spatial_events:
        key = event.environment_tag or "unspecified"
        bucket = environment_stats.setdefault(key, _empty_environment_bucket())
        bucket["spatial_attempts"] = int(bucket["spatial_attempts"]) + 1
        if event.is_success:
            bucket["spatial_successes"] = int(bucket["spatial_successes"]) + 1
    for event in extended_events:
        key = event.environment_tag or "unspecified"
        bucket = environment_stats.setdefault(key, _empty_environment_bucket())
        bucket["extended_attempts"] = int(bucket["extended_attempts"]) + 1
        if event.is_success:
            bucket["extended_successes"] = int(bucket["extended_successes"]) + 1
    for bucket in environment_stats.values():
        spatial_attempts = int(bucket["spatial_attempts"])
        extended_attempts = int(bucket["extended_attempts"])
        bucket["spatial_accuracy"] = (
            int(bucket["spatial_successes"]) / spatial_attempts if spatial_attempts else 0.0
        )
        bucket["extended_accuracy"] = (
            int(bucket["extended_successes"]) / extended_attempts if extended_attempts else 0.0
        )
    return environment_stats


def _empty_environment_bucket() -> dict[str, int | float]:
    return {
        "spatial_attempts": 0,
        "spatial_successes": 0,
        "spatial_accuracy": 0.0,
        "extended_attempts": 0,
        "extended_successes": 0,
        "extended_accuracy": 0.0,
    }


def _spatial_event_from_mapping(raw_event: object) -> Phase4SpatialEvent:
    if not isinstance(raw_event, dict):
        raise ValueError("Phase 4 spatial events must be JSON objects.")
    _reject_forbidden_fields(raw_event)
    missing = [field for field in _REQUIRED_SPATIAL_FIELDS if field not in raw_event]
    if missing:
        raise ValueError(f"Phase 4 spatial event is missing fields: {', '.join(missing)}")
    payload = {
        field: raw_event[field]
        for field in (*_REQUIRED_SPATIAL_FIELDS, *_OPTIONAL_SPATIAL_FIELDS)
        if field in raw_event
    }
    payload.setdefault("reaction_time_ms", None)
    payload.setdefault("user_rating", None)
    payload.setdefault("environment_tag", "")
    payload.setdefault("notes", "")
    return Phase4SpatialEvent(**payload)


def _extended_event_from_mapping(raw_event: object) -> Phase4ExtendedBandEvent:
    if not isinstance(raw_event, dict):
        raise ValueError("Phase 4 extended-band events must be JSON objects.")
    _reject_forbidden_fields(raw_event)
    missing = [field for field in _REQUIRED_EXTENDED_FIELDS if field not in raw_event]
    if missing:
        raise ValueError(f"Phase 4 extended-band event is missing fields: {', '.join(missing)}")
    payload = {
        field: raw_event[field]
        for field in (*_REQUIRED_EXTENDED_FIELDS, *_OPTIONAL_EXTENDED_FIELDS)
        if field in raw_event
    }
    payload.setdefault("reaction_time_ms", None)
    payload.setdefault("user_rating", None)
    payload.setdefault("environment_tag", "")
    payload.setdefault("notes", "")
    return Phase4ExtendedBandEvent(**payload)


def _reject_forbidden_fields(raw_event: dict[str, object]) -> None:
    forbidden = sorted(_FORBIDDEN_EVENT_FIELDS.intersection(raw_event))
    if forbidden:
        raise ValueError(f"Phase 4 progress events cannot contain: {', '.join(forbidden)}")


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenHear Phase 4 spatial/extended tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-tasks", help="List built-in Phase 4 tasks.")
    list_parser.add_argument("--all", action="store_true", help="Include inactive tasks.")

    spatial_parser = subparsers.add_parser("spatial", help="Append one spatial Phase 4 check.")
    spatial_parser.add_argument("--task", required=True)
    spatial_parser.add_argument("--predicted-azimuth", required=True, type=float)
    spatial_parser.add_argument("--predicted-elevation", type=float, default=0.0)
    spatial_parser.add_argument("--confidence", type=float, default=1.0)
    spatial_parser.add_argument("--user-response", default="answered")
    spatial_parser.add_argument("--reaction-time-ms", type=float)
    spatial_parser.add_argument("--user-rating", type=int)
    spatial_parser.add_argument("--environment", default="")
    spatial_parser.add_argument("--notes", default="")
    spatial_parser.add_argument("--session-id")
    spatial_parser.add_argument("--progress", required=True)

    extended_parser = subparsers.add_parser("extended", help="Append one extended-band check.")
    extended_parser.add_argument("--task", required=True)
    extended_parser.add_argument("--predicted-band", required=True)
    extended_parser.add_argument("--confidence", type=float, default=1.0)
    extended_parser.add_argument("--user-response", default="")
    extended_parser.add_argument("--reaction-time-ms", type=float)
    extended_parser.add_argument("--user-rating", type=int)
    extended_parser.add_argument("--environment", default="")
    extended_parser.add_argument("--notes", default="")
    extended_parser.add_argument("--session-id")
    extended_parser.add_argument("--progress", required=True)

    summary_parser = subparsers.add_parser("summary", help="Summarise a Phase 4 progress file.")
    summary_parser.add_argument("--progress", required=True)

    args = parser.parse_args()
    if args.command == "list-tasks":
        _print_json([asdict(task) for task in list_tasks(active_only=not args.all)])
        return

    if args.command == "spatial":
        session = Phase4SpatialExtendedSession(session_id=args.session_id)
        event = session.record_spatial(
            args.task,
            predicted_azimuth_degrees=args.predicted_azimuth,
            predicted_elevation_degrees=args.predicted_elevation,
            confidence=args.confidence,
            user_response=args.user_response,
            reaction_time_ms=args.reaction_time_ms,
            user_rating=args.user_rating,
            environment_tag=args.environment,
            notes=args.notes,
        )
        Phase4ProgressStore(args.progress).append_spatial(event)
        _print_json({"event": asdict(event), "summary": asdict(session.summary())})
        return

    if args.command == "extended":
        session = Phase4SpatialExtendedSession(session_id=args.session_id)
        event = session.record_extended_band(
            args.task,
            predicted_band=args.predicted_band,
            confidence=args.confidence,
            user_response=args.user_response,
            reaction_time_ms=args.reaction_time_ms,
            user_rating=args.user_rating,
            environment_tag=args.environment,
            notes=args.notes,
        )
        Phase4ProgressStore(args.progress).append_extended(event)
        _print_json({"event": asdict(event), "summary": asdict(session.summary())})
        return

    if args.command == "summary":
        store = Phase4ProgressStore(args.progress)
        data = store.load()
        spatial_events = [
            _spatial_event_from_mapping(raw_event) for raw_event in data["spatial_events"]
        ]
        extended_events = [
            _extended_event_from_mapping(raw_event) for raw_event in data["extended_events"]
        ]
        _print_json(asdict(summarise_events(spatial_events, extended_events)))


if __name__ == "__main__":
    main()
