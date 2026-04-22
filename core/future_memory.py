"""
future_memory.py – lightweight repo-local memory for ongoing OpenHear work.

Stores timestamped development notes in a JSON file inside the repository so
future sessions can keep a practical breadcrumb trail without needing any
external service.

Usage:
    python -m core.future_memory add --topic sharp-hearing --note "Prototype flashed."
    python -m core.future_memory list
    python -m core.future_memory latest --topic sharp-hearing
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_MEMORY_PATH = (
    Path(__file__).resolve().parent.parent / ".openhear_future_memory.json"
)
MEMORY_FORMAT_VERSION = "openhear-future-memory-v1"


@dataclass(frozen=True)
class MemoryNote:
    """One timestamped development note."""

    created_at: str
    topic: str
    note: str
    tags: list[str]


class FutureMemoryStore:
    """Append-only JSON note store for project context."""

    def __init__(self, path: str | Path = DEFAULT_MEMORY_PATH) -> None:
        self.path = Path(path)

    def load(self) -> dict:
        """Load the store, returning an empty structure if it does not exist."""
        if not self.path.exists():
            return {"format_version": MEMORY_FORMAT_VERSION, "notes": []}

        with self.path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        if data.get("format_version") != MEMORY_FORMAT_VERSION:
            raise ValueError(
                f"Unsupported memory format: {data.get('format_version')!r}. "
                f"Expected {MEMORY_FORMAT_VERSION!r}."
            )

        if not isinstance(data.get("notes"), list):
            raise ValueError("Memory store is malformed: 'notes' must be a list.")

        return data

    def list_notes(self, topic: str | None = None) -> list[MemoryNote]:
        """Return all notes, optionally filtered by *topic*."""
        data = self.load()
        notes = [MemoryNote(**entry) for entry in data["notes"]]
        if topic is None:
            return notes
        topic = topic.strip().lower()
        return [note for note in notes if note.topic.lower() == topic]

    def add_note(
        self,
        topic: str,
        note: str,
        *,
        tags: list[str] | None = None,
        created_at: str | None = None,
    ) -> MemoryNote:
        """Append one note and persist the JSON store."""
        topic = topic.strip()
        note = note.strip()
        if not topic:
            raise ValueError("topic must not be empty.")
        if not note:
            raise ValueError("note must not be empty.")

        entry = MemoryNote(
            created_at=created_at or datetime.now(timezone.utc).isoformat(),
            topic=topic,
            note=note,
            tags=sorted({tag.strip() for tag in (tags or []) if tag.strip()}),
        )

        data = self.load()
        data["notes"].append(asdict(entry))
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return entry

    def latest(self, topic: str | None = None, *, limit: int = 1) -> list[MemoryNote]:
        """Return the newest *limit* notes, optionally filtered by topic."""
        notes = self.list_notes(topic=topic)
        notes.sort(key=lambda entry: entry.created_at, reverse=True)
        return notes[:limit]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenHear future memory store.")
    parser.add_argument(
        "--path",
        default=str(DEFAULT_MEMORY_PATH),
        help="Path to the JSON memory store.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Append a development note.")
    add_parser.add_argument("--topic", required=True, help="Topic key, e.g. sharp-hearing.")
    add_parser.add_argument("--note", required=True, help="Human-readable note text.")
    add_parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help="Optional tag. Pass multiple times to add more than one.",
    )

    list_parser = subparsers.add_parser("list", help="List stored notes.")
    list_parser.add_argument("--topic", help="Optional topic filter.")

    latest_parser = subparsers.add_parser("latest", help="Show the newest notes.")
    latest_parser.add_argument("--topic", help="Optional topic filter.")
    latest_parser.add_argument("--limit", type=int, default=5, help="Maximum notes to print.")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    store = FutureMemoryStore(args.path)

    if args.command == "add":
        entry = store.add_note(args.topic, args.note, tags=args.tag)
        print(json.dumps(asdict(entry), indent=2))
        return

    if args.command == "list":
        print(json.dumps([asdict(note) for note in store.list_notes(args.topic)], indent=2))
        return

    if args.command == "latest":
        print(
            json.dumps(
                [asdict(note) for note in store.latest(args.topic, limit=args.limit)],
                indent=2,
            )
        )
        return

    parser.error(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
