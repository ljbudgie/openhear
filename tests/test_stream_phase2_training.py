"""Tests for ``stream/phase2_training.py``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from stream.haptic_mapper import PATTERN_IDS, SOUND_CLASS_IDS
from stream.phase2_training import (
    OUTCOME_CORRECT,
    OUTCOME_INCORRECT,
    OUTCOME_PARTIAL,
    OUTCOME_SILENCE,
    SCHEMA_VERSION,
    Phase2ProgressStore,
    Phase2TrainingSession,
    classify_phase2_scores,
    get_target,
    list_targets,
    main,
    map_label_to_phase2_target,
    target_to_sound_class,
)


def test_phase2_catalog_has_stable_ids_and_types():
    targets = list_targets()
    target_ids = [target.target_id for target in targets]
    assert target_ids == [
        "alarm_smoke",
        "alarm_siren",
        "alarm_timer",
        "env_doorbell",
        "traffic_car",
        "traffic_truck",
        "traffic_horn",
        "traffic_motorcycle",
        "env_dog_bark",
        "env_knock",
        "env_phone",
        "word_yes",
        "word_no",
        "word_help",
        "word_stop",
        "name_placeholder",
    ]
    assert {target.target_type for target in targets} == {
        "alarm",
        "environment",
        "name",
        "traffic",
        "word",
    }


@pytest.mark.parametrize(
    ("target_id", "sound_class"),
    [
        ("alarm_siren", "alarm"),
        ("traffic_horn", "traffic"),
        ("word_help", "voice"),
        ("name_placeholder", "voice"),
        ("env_dog_bark", "dog"),
        ("env_doorbell", "doorbell"),
    ],
)
def test_target_to_sound_class_collapses_to_existing_ble_classes(target_id, sound_class):
    assert target_to_sound_class(target_id) == sound_class
    assert sound_class in SOUND_CLASS_IDS
    assert PATTERN_IDS[sound_class] == SOUND_CLASS_IDS[sound_class]


def test_map_label_to_phase2_target_uses_detailed_targets():
    assert map_label_to_phase2_target("Smoke detector, smoke alarm").target_id == "alarm_smoke"
    assert map_label_to_phase2_target("Vehicle horn").target_id == "traffic_horn"
    assert map_label_to_phase2_target("Spoken help").target_id == "word_help"
    assert map_label_to_phase2_target("Unmapped acoustic event") is None


def test_classify_phase2_scores_prefers_specific_phase2_target():
    target, sound_class, source_label, confidence = classify_phase2_scores(
        {"Speech": 0.95, "Vehicle horn": 0.81}
    )
    assert target.target_id == "traffic_horn"
    assert sound_class == "traffic"
    assert source_label == "Vehicle horn"
    assert confidence == pytest.approx(0.81)


def test_classify_phase2_scores_falls_back_to_existing_classifier():
    target, sound_class, source_label, confidence = classify_phase2_scores({"Speech": 0.8})
    assert target is None
    assert sound_class == "voice"
    assert source_label == "Speech"
    assert confidence == pytest.approx(0.8)


def test_session_scores_exact_match():
    session = Phase2TrainingSession(session_id="s1")
    event = session.evaluate_scores("alarm_smoke", {"Smoke detector": 0.9})
    assert event.outcome == OUTCOME_CORRECT
    assert event.predicted_target_id == "alarm_smoke"
    assert event.predicted_sound_class == "alarm"
    assert session.summary()["accuracy"] == 1.0


def test_session_scores_category_level_partial_match():
    session = Phase2TrainingSession(session_id="s1")
    event = session.evaluate_scores("alarm_smoke", {"Siren": 0.9})
    assert event.outcome == OUTCOME_PARTIAL
    assert event.predicted_target_id == "alarm_siren"
    assert event.predicted_sound_class == "alarm"
    assert event.is_success


def test_session_scores_incorrect_and_silence():
    session = Phase2TrainingSession(session_id="s1")
    incorrect = session.evaluate_scores("traffic_car", {"Dog bark": 0.9})
    silence = session.evaluate_scores("word_yes", {"Mystery": 0.9})
    assert incorrect.outcome == OUTCOME_INCORRECT
    assert silence.outcome == OUTCOME_SILENCE
    summary = session.summary()
    assert summary["attempts"] == 2
    assert summary["successes"] == 0


def test_session_rejects_unknown_target():
    with pytest.raises(KeyError, match="Unknown Phase 2 target"):
        get_target("missing")


def test_progress_store_serializes_without_raw_audio(tmp_path: Path):
    path = tmp_path / "phase2.json"
    session = Phase2TrainingSession(session_id="s1")
    event = session.evaluate_scores(
        "traffic_horn",
        {"Vehicle horn": 0.8},
        reaction_time_ms=350.0,
        user_rating=4,
    )
    data = Phase2ProgressStore(path).append(event)
    raw = path.read_text(encoding="utf-8")
    assert data["schema_version"] == SCHEMA_VERSION
    assert "raw_audio" not in raw
    assert "waveform" not in raw
    assert json.loads(raw)["events"][0]["target_id"] == "traffic_horn"


def test_progress_store_rejects_unknown_schema(tmp_path: Path):
    path = tmp_path / "phase2.json"
    path.write_text('{"schema_version": "future", "events": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        Phase2ProgressStore(path).load()


def test_cli_list_outputs_catalog(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["phase2", "list"])
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["target_id"] == "alarm_smoke"


def test_cli_run_writes_progress(monkeypatch, capsys, tmp_path: Path):
    progress = tmp_path / "phase2.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "phase2",
            "run",
            "--target",
            "alarm_smoke",
            "--score",
            "Smoke detector=0.9",
            "--session-id",
            "s1",
            "--progress",
            str(progress),
        ],
    )
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["event"]["outcome"] == OUTCOME_CORRECT
    assert progress.exists()


def test_cli_summary_reads_progress(monkeypatch, capsys, tmp_path: Path):
    progress = tmp_path / "phase2.json"
    session = Phase2TrainingSession(session_id="s1")
    event = session.evaluate_scores("word_help", {"Spoken help": 0.9})
    Phase2ProgressStore(progress).append(event)
    monkeypatch.setattr("sys.argv", ["phase2", "summary", "--progress", str(progress)])
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["attempts"] == 1
    assert payload["accuracy"] == 1.0
    assert payload["session_id"] == "s1"


def test_cli_summary_ignores_extra_event_fields(monkeypatch, capsys, tmp_path: Path):
    progress = tmp_path / "phase2.json"
    session = Phase2TrainingSession(session_id="s1")
    event = session.evaluate_scores("word_help", {"Spoken help": 0.9})
    data = Phase2ProgressStore(progress).append(event)
    data["events"][0]["future_field"] = "ignored"
    progress.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["phase2", "summary", "--progress", str(progress)])
    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["attempts"] == 1


def test_cli_summary_rejects_missing_event_fields(monkeypatch, tmp_path: Path):
    progress = tmp_path / "phase2.json"
    progress.write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "events": [{"session_id": "s1"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["phase2", "summary", "--progress", str(progress)])
    with pytest.raises(ValueError, match="missing fields"):
        main()
