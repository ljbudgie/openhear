"""
preferences.py – listener preference capture (Phase 6 stub).

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

All functions currently raise :class:`NotImplementedError` but the
signatures, dataclasses, and file format are frozen so downstream
code (the adaptive engine, the mobile UI, the offline evaluator) can
be written against them today.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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

    timestamp: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )
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
        NotImplementedError: Always — implementation pending.
    """
    _ = event, store_path  # silence linters until implemented
    raise NotImplementedError(
        "learn.preferences.record_choice is a Phase 6 scaffold.  "
        "See docs/ARCHITECTURE.md for the intended data flow and open "
        "an issue describing your use case before implementing."
    )


def load_events(store_path: Path) -> list[PreferenceEvent]:
    """Load all :class:`PreferenceEvent` records from *store_path*.

    Raises:
        NotImplementedError: Always — implementation pending.
    """
    _ = store_path
    raise NotImplementedError(
        "learn.preferences.load_events is a Phase 6 scaffold.  "
        "The JSONL format is documented in learn/preferences.py."
    )


def summarise(events: list[PreferenceEvent]) -> dict[str, dict[str, int]]:
    """Return ``{environment: {'A': n, 'B': n, 'undecided': n}}``.

    Raises:
        NotImplementedError: Always — implementation pending.
    """
    _ = events
    raise NotImplementedError(
        "learn.preferences.summarise is a Phase 6 scaffold."
    )
