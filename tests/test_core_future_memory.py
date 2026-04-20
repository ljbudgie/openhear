"""Tests for ``core/future_memory.py``."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.future_memory import FutureMemoryStore, MEMORY_FORMAT_VERSION


def test_add_note_creates_store(tmp_path: Path):
    store_path = tmp_path / "memory.json"
    store = FutureMemoryStore(store_path)

    entry = store.add_note(
        "sharp-hearing",
        "Prototype uses a micro:bit v2 wristband.",
        tags=["clinic", "prototype"],
        created_at="2026-04-20T19:40:00+00:00",
    )

    assert store_path.exists()
    assert entry.topic == "sharp-hearing"
    assert store.load()["format_version"] == MEMORY_FORMAT_VERSION


def test_list_notes_filters_by_topic(tmp_path: Path):
    store = FutureMemoryStore(tmp_path / "memory.json")
    store.add_note("sharp-hearing", "First note", created_at="2026-04-20T19:40:00+00:00")
    store.add_note("yamnet", "Second note", created_at="2026-04-20T19:41:00+00:00")

    notes = store.list_notes("sharp-hearing")

    assert len(notes) == 1
    assert notes[0].note == "First note"


def test_latest_returns_most_recent_first(tmp_path: Path):
    store = FutureMemoryStore(tmp_path / "memory.json")
    store.add_note("sharp-hearing", "Older", created_at="2026-04-20T19:40:00+00:00")
    store.add_note("sharp-hearing", "Newer", created_at="2026-04-20T19:41:00+00:00")

    latest = store.latest("sharp-hearing", limit=1)

    assert latest[0].note == "Newer"


def test_rejects_empty_topic(tmp_path: Path):
    store = FutureMemoryStore(tmp_path / "memory.json")
    with pytest.raises(ValueError, match="topic"):
        store.add_note("", "Note")
