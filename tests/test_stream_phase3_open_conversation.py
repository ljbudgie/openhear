"""Tests for ``stream/phase3_open_conversation.py``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from stream.haptic_mapper import PATTERN_IDS, SUPPORTED_SOUND_CLASSES
from stream.phase3_open_conversation import (
    OUTCOME_CORRECT,
    OUTCOME_INCORRECT,
    OUTCOME_MISSED,
    OUTCOME_PARTIAL,
    OUTCOME_SILENCE,
    OUTCOME_SKIPPED,
    SCHEMA_VERSION,
    Phase3OpenConversationSession,
    Phase3ProgressStore,
    get_prompt,
    list_prompts,
    main,
    prompt_to_sound_class,
    score_recall,
)


def test_prompt_catalog_has_stable_ids_and_supported_classes():
    prompts = list_prompts()
    prompt_ids = [prompt.prompt_id for prompt in prompts]
    assert prompt_ids == [
        "conversation_present",
        "classify_voice",
        "classify_music",
        "classify_traffic",
        "classify_alarm",
        "classify_silence",
        "last_cue_important",
        "automatic_vibration_rating",
    ]
    for prompt in prompts:
        if prompt.expected_sound_class is not None:
            assert prompt.expected_sound_class in SUPPORTED_SOUND_CLASSES


@pytest.mark.parametrize(
    ("prompt_id", "sound_class"),
    [
        ("conversation_present", "voice"),
        ("classify_music", "media"),
        ("classify_traffic", "traffic"),
        ("classify_alarm", "alarm"),
        ("classify_silence", "silence"),
    ],
)
def test_prompt_to_sound_class_collapses_to_existing_classes(prompt_id, sound_class):
    assert prompt_to_sound_class(prompt_id) == sound_class


def test_passive_event_records_derived_metadata_only(tmp_path: Path):
    session = Phase3OpenConversationSession(session_id="s1")
    event = session.record_passive(
        "voice",
        source_label="Speech",
        confidence=0.8,
        intensity=128,
        pattern_id=PATTERN_IDS["voice"],
        duration_seconds=0.975,
        environment_tag="cafe",
    )
    data = Phase3ProgressStore(tmp_path / "phase3.json").append_passive(event)
    raw = json.dumps(data)
    assert data["schema_version"] == SCHEMA_VERSION
    assert "raw_audio" not in raw
    assert "waveform" not in raw
    assert data["passive_events"][0]["is_conversation"] is True


def test_progress_store_empty_document(tmp_path: Path):
    data = Phase3ProgressStore(tmp_path / "missing.json").load()
    assert data == {"schema_version": SCHEMA_VERSION, "passive_events": [], "recall_events": []}


def test_progress_store_appends_recall_event(tmp_path: Path):
    session = Phase3OpenConversationSession(session_id="s1")
    event = session.record_recall(
        "classify_alarm",
        predicted_sound_class="alarm",
        confidence=0.9,
        user_response="alarm",
        reaction_time_ms=450.0,
        user_rating=4,
    )
    data = Phase3ProgressStore(tmp_path / "phase3.json").append_recall(event)
    assert data["recall_events"][0]["outcome"] == OUTCOME_CORRECT
    assert data["recall_events"][0]["reaction_time_ms"] == 450.0


def test_progress_store_rejects_unknown_schema(tmp_path: Path):
    path = tmp_path / "phase3.json"
    path.write_text('{"schema_version": "future", "passive_events": [], "recall_events": []}')
    with pytest.raises(ValueError, match="Unsupported"):
        Phase3ProgressStore(path).load()


def test_summary_rejects_missing_event_fields(monkeypatch, tmp_path: Path):
    progress = tmp_path / "phase3.json"
    progress.write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "passive_events": [{"session_id": "s1"}],
                "recall_events": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["phase3", "summary", "--progress", str(progress)])
    with pytest.raises(ValueError, match="missing fields"):
        main()


def test_summary_ignores_future_fields(monkeypatch, capsys, tmp_path: Path):
    progress = tmp_path / "phase3.json"
    session = Phase3OpenConversationSession(session_id="s1")
    event = session.record_recall(
        "classify_voice", predicted_sound_class="voice", confidence=0.9, user_response="voice"
    )
    data = Phase3ProgressStore(progress).append_recall(event)
    data["recall_events"][0]["future_field"] = "ignored"
    progress.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["phase3", "summary", "--progress", str(progress)])
    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["recall_attempts"] == 1


def test_summary_rejects_raw_audio_fields(monkeypatch, tmp_path: Path):
    progress = tmp_path / "phase3.json"
    session = Phase3OpenConversationSession(session_id="s1")
    event = session.record_passive(
        "voice",
        source_label="Speech",
        confidence=0.9,
        intensity=128,
        pattern_id=PATTERN_IDS["voice"],
        duration_seconds=0.975,
    )
    data = Phase3ProgressStore(progress).append_passive(event)
    data["passive_events"][0]["raw_audio"] = "not allowed"
    progress.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["phase3", "summary", "--progress", str(progress)])
    with pytest.raises(ValueError, match="cannot contain"):
        main()


def test_score_recall_outcomes():
    prompt = get_prompt("classify_voice")
    assert (
        score_recall(prompt, predicted_sound_class="voice", confidence=0.9, user_response="voice")
        == OUTCOME_CORRECT
    )
    assert (
        score_recall(prompt, predicted_sound_class="media", confidence=0.9, user_response="voice")
        == OUTCOME_PARTIAL
    )
    assert (
        score_recall(prompt, predicted_sound_class="media", confidence=0.9, user_response="traffic")
        == OUTCOME_INCORRECT
    )
    assert (
        score_recall(prompt, predicted_sound_class="voice", confidence=0.9, user_response="")
        == OUTCOME_MISSED
    )
    assert (
        score_recall(prompt, predicted_sound_class="voice", confidence=0.9, user_response="skip")
        == OUTCOME_SKIPPED
    )
    assert (
        score_recall(prompt, predicted_sound_class="voice", confidence=0.05, user_response="voice")
        == OUTCOME_SILENCE
    )


def test_session_summary_computes_exposure_recall_and_environment():
    session = Phase3OpenConversationSession(session_id="s1")
    session.record_passive(
        "voice",
        source_label="Speech",
        confidence=0.8,
        intensity=128,
        pattern_id=PATTERN_IDS["voice"],
        duration_seconds=1.0,
        environment_tag="home",
    )
    session.record_passive(
        "traffic",
        source_label="Car",
        confidence=0.6,
        intensity=64,
        pattern_id=PATTERN_IDS["traffic"],
        duration_seconds=2.0,
        environment_tag="street",
    )
    session.record_recall(
        "classify_voice",
        predicted_sound_class="voice",
        confidence=0.9,
        user_response="voice",
        reaction_time_ms=300.0,
        environment_tag="home",
    )

    summary = session.summary()

    assert summary.passive_windows == 2
    assert summary.conversation_windows == 1
    assert summary.passive_duration_seconds == 3.0
    assert summary.recall_accuracy == 1.0
    assert summary.average_reaction_time_ms == 300.0
    assert summary.by_environment["home"]["passive_windows"] == 1
    assert summary.by_environment["home"]["recall_attempts"] == 1


def test_cli_list_prompts(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["phase3", "list-prompts"])
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["prompt_id"] == "conversation_present"


def test_cli_passive_writes_progress(monkeypatch, capsys, tmp_path: Path):
    progress = tmp_path / "phase3.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "phase3",
            "passive",
            "--sound-class",
            "voice",
            "--source-label",
            "Speech",
            "--confidence",
            "0.9",
            "--intensity",
            "128",
            "--environment",
            "home",
            "--session-id",
            "s1",
            "--progress",
            str(progress),
        ],
    )
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["event"]["predicted_sound_class"] == "voice"
    assert progress.exists()


def test_cli_recall_and_summary(monkeypatch, capsys, tmp_path: Path):
    progress = tmp_path / "phase3.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "phase3",
            "recall",
            "--prompt",
            "classify_voice",
            "--predicted-class",
            "voice",
            "--confidence",
            "0.9",
            "--user-response",
            "voice",
            "--session-id",
            "s1",
            "--progress",
            str(progress),
        ],
    )
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["event"]["outcome"] == OUTCOME_CORRECT

    monkeypatch.setattr("sys.argv", ["phase3", "summary", "--progress", str(progress)])
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["recall_attempts"] == 1
    assert payload["recall_accuracy"] == 1.0
