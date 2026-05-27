"""
preferences.py – listener preference capture.

The intended data flow is:

    dsp.pipeline (A config)  ──┐
                               ├──→ listener chooses A or B
    dsp.pipeline (B config)  ──┘                │
                                                ▼
                                   learn.preferences.record_choice()
                                                │
                                                ▼
                           ─── persisted as JSONL ───
                                                │
                                                ▼
                                   learn.engine.update_config()

Events are stored as newline-delimited JSON so mobile and desktop tools can
append choices without rewriting the whole log.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

__all__ = [
    "PreferenceEvent",
    "record_choice",
    "load_events",
    "summarise",
]


Choice = Literal["A", "B", "undecided"]
_CHOICES: tuple[Choice, ...] = ("A", "B", "undecided")


@dataclass
class PreferenceEvent:
    """One A/B comparison recorded during a listening trial.

    Attributes:
        timestamp: ISO-8601 UTC timestamp of the trial.
        environment: User-tagged environment (e.g. ``"restaurant"``).
        config_a_path: Path to the YAML that generated option A.
        config_b_path: Path to the YAML that generated option B.
        choice: Which option the listener preferred (or "undecided").
        notes: Free-form user notes.
    """

    timestamp: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())
    environment: str = ""
    config_a_path: str = ""
    config_b_path: str = ""
    choice: Choice = "undecided"
    notes: str = ""


def record_choice(
    event: PreferenceEvent,
    *,
    store_path: Path,
) -> None:
    """Append *event* to the persistent preference log at *store_path*.

    Raises:
        ValueError: If ``event.choice`` is not one of ``"A"``, ``"B"``, or
            ``"undecided"``.
    """
    _validate_choice(event.choice)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(asdict(event), sort_keys=True, separators=(",", ":"))
    with store_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def load_events(store_path: Path) -> list[PreferenceEvent]:
    """Load all :class:`PreferenceEvent` records from *store_path*.

    Raises:
        ValueError: If a non-blank JSONL line is malformed.
    """
    if not store_path.exists():
        return []

    events: list[PreferenceEvent] = []
    for line_no, line in enumerate(store_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                raise TypeError(f"expected object, got {type(data).__name__}")
            event = PreferenceEvent(**data)
            _validate_choice(event.choice)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid preference event at {store_path}:{line_no}: {exc}") from exc
        events.append(event)
    return events


def summarise(events: list[PreferenceEvent]) -> dict[str, dict[str, int]]:
    """Return ``{environment: {'A': n, 'B': n, 'undecided': n}}``."""
    summary: dict[str, dict[str, int]] = {}
    for event in events:
        _validate_choice(event.choice)
        environment = event.environment or "default"
        counts = summary.setdefault(environment, {choice: 0 for choice in _CHOICES})
        counts[event.choice] += 1
    return summary


def _validate_choice(choice: str) -> None:
    if choice not in _CHOICES:
        raise ValueError(f"Invalid preference choice {choice!r}; expected one of {_CHOICES}.")
