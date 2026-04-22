"""Tests for ``core/future_memory.py``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.future_memory import (
    MEMORY_FORMAT_VERSION,
    FutureMemoryStore,
    main,
)


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


# ── Additional coverage ──────────────────────────────────────────────────────


def test_load_returns_empty_skeleton_when_file_missing(tmp_path: Path):
    store = FutureMemoryStore(tmp_path / "missing.json")
    data = store.load()
    assert data == {"format_version": MEMORY_FORMAT_VERSION, "notes": []}


def test_rejects_empty_note(tmp_path: Path):
    store = FutureMemoryStore(tmp_path / "memory.json")
    with pytest.raises(ValueError, match="note"):
        store.add_note("topic", "   ")


def test_topic_filter_is_case_insensitive(tmp_path: Path):
    store = FutureMemoryStore(tmp_path / "memory.json")
    store.add_note("Sharp-Hearing", "Note", created_at="2026-04-20T19:40:00+00:00")
    notes = store.list_notes("SHARP-HEARING")
    assert len(notes) == 1


def test_list_notes_without_topic_returns_all(tmp_path: Path):
    store = FutureMemoryStore(tmp_path / "memory.json")
    store.add_note("a", "n1", created_at="2026-04-20T19:40:00+00:00")
    store.add_note("b", "n2", created_at="2026-04-20T19:41:00+00:00")
    assert len(store.list_notes()) == 2
    # ``latest`` without filter also returns all (sorted descending).
    latest = store.latest(limit=10)
    assert [n.note for n in latest] == ["n2", "n1"]


def test_load_rejects_unknown_format_version(tmp_path: Path):
    store_path = tmp_path / "memory.json"
    store_path.write_text(json.dumps({"format_version": "bogus", "notes": []}))
    store = FutureMemoryStore(store_path)
    with pytest.raises(ValueError, match="Unsupported memory format"):
        store.load()


def test_load_rejects_malformed_notes_field(tmp_path: Path):
    store_path = tmp_path / "memory.json"
    store_path.write_text(
        json.dumps({"format_version": MEMORY_FORMAT_VERSION, "notes": "not-a-list"})
    )
    store = FutureMemoryStore(store_path)
    with pytest.raises(ValueError, match="malformed"):
        store.load()


def test_tags_are_deduplicated_and_sorted(tmp_path: Path):
    store = FutureMemoryStore(tmp_path / "memory.json")
    entry = store.add_note(
        "topic",
        "note",
        tags=["beta", "alpha", "alpha", " ", ""],
        created_at="2026-04-20T19:40:00+00:00",
    )
    assert entry.tags == ["alpha", "beta"]


def test_add_uses_now_when_no_timestamp_provided(tmp_path: Path):
    store = FutureMemoryStore(tmp_path / "memory.json")
    entry = store.add_note("topic", "note")
    # ISO-8601 with timezone has a "T" separator and a trailing offset.
    assert "T" in entry.created_at
    assert entry.created_at.endswith("+00:00")


# ── CLI ───────────────────────────────────────────────────────────────────────


class TestCli:
    def test_add_command_writes_note_and_prints_json(self, tmp_path, monkeypatch, capsys):
        store_path = tmp_path / "memory.json"
        monkeypatch.setattr(
            "sys.argv",
            [
                "future_memory",
                "--path", str(store_path),
                "add",
                "--topic", "test",
                "--note", "Hello",
                "--tag", "alpha",
                "--tag", "beta",
            ],
        )
        main()
        printed = capsys.readouterr().out
        assert "Hello" in printed
        # Verify persistence on disk.
        data = json.loads(store_path.read_text(encoding="utf-8"))
        assert data["notes"][0]["topic"] == "test"
        assert data["notes"][0]["tags"] == ["alpha", "beta"]

    def test_list_command_prints_filtered_notes(self, tmp_path, monkeypatch, capsys):
        store_path = tmp_path / "memory.json"
        store = FutureMemoryStore(store_path)
        store.add_note("a", "first", created_at="2026-04-20T19:40:00+00:00")
        store.add_note("b", "second", created_at="2026-04-20T19:41:00+00:00")

        monkeypatch.setattr(
            "sys.argv",
            ["future_memory", "--path", str(store_path), "list", "--topic", "a"],
        )
        main()
        notes = json.loads(capsys.readouterr().out)
        assert len(notes) == 1
        assert notes[0]["note"] == "first"

    def test_latest_command_respects_limit(self, tmp_path, monkeypatch, capsys):
        store_path = tmp_path / "memory.json"
        store = FutureMemoryStore(store_path)
        store.add_note("a", "older", created_at="2026-04-20T19:40:00+00:00")
        store.add_note("a", "newer", created_at="2026-04-20T19:41:00+00:00")

        monkeypatch.setattr(
            "sys.argv",
            [
                "future_memory",
                "--path", str(store_path),
                "latest",
                "--topic", "a",
                "--limit", "1",
            ],
        )
        main()
        notes = json.loads(capsys.readouterr().out)
        assert len(notes) == 1
        assert notes[0]["note"] == "newer"

