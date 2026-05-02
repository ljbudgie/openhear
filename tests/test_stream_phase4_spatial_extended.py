"""Tests for ``stream/phase4_spatial_extended.py``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from stream.phase4_spatial_extended import (
    EXTENDED_BANDS,
    OUTCOME_CORRECT,
    OUTCOME_INCORRECT,
    OUTCOME_MISSED,
    OUTCOME_PARTIAL,
    OUTCOME_SILENCE,
    OUTCOME_SKIPPED,
    SCHEMA_VERSION,
    Phase4ProgressStore,
    Phase4SpatialExtendedSession,
    angular_error_degrees,
    get_task,
    list_tasks,
    main,
    normalise_azimuth,
    normalise_band,
    score_extended_band,
    score_spatial,
)


def test_task_catalog_has_stable_ids_and_supported_bands():
    tasks = list_tasks()
    task_ids = [task.task_id for task in tasks]
    assert task_ids == [
        "localise_front",
        "localise_left",
        "localise_right",
        "localise_behind",
        "elevation_above",
        "elevation_below",
        "band_infrasonic",
        "band_high_frequency",
        "band_ultrasonic",
    ]
    for task in tasks:
        if task.expected_band is not None:
            assert task.expected_band in EXTENDED_BANDS


def test_angle_helpers_wrap_azimuths():
    assert normalise_azimuth(270) == -90
    assert normalise_azimuth(-180) == 180
    assert angular_error_degrees(179, -179) == 2


def test_band_normalisation_resolves_aliases_and_rejects_unknown():
    assert normalise_band("infra") == "infrasonic"
    assert normalise_band("high frequency") == "high_frequency"
    assert normalise_band("low-tactile") == "tactile_low"
    with pytest.raises(ValueError, match="Unsupported Phase 4 band"):
        normalise_band("unknown band")


def test_progress_store_empty_document(tmp_path: Path):
    data = Phase4ProgressStore(tmp_path / "missing.json").load()
    assert data == {"schema_version": SCHEMA_VERSION, "spatial_events": [], "extended_events": []}


def test_spatial_event_records_derived_metadata_only(tmp_path: Path):
    session = Phase4SpatialExtendedSession(session_id="s1")
    event = session.record_spatial(
        "localise_left",
        predicted_azimuth_degrees=-82,
        confidence=0.8,
        user_response="answered",
        environment_tag="street",
    )
    data = Phase4ProgressStore(tmp_path / "phase4.json").append_spatial(event)
    raw = json.dumps(data)
    assert data["schema_version"] == SCHEMA_VERSION
    assert "raw_audio" not in raw
    assert "location_trace" not in raw
    assert data["spatial_events"][0]["outcome"] == OUTCOME_CORRECT


def test_extended_event_records_derived_metadata_only(tmp_path: Path):
    session = Phase4SpatialExtendedSession(session_id="s1")
    event = session.record_extended_band(
        "band_ultrasonic",
        predicted_band="ultrasound",
        confidence=0.9,
        user_response="ultrasonic",
    )
    data = Phase4ProgressStore(tmp_path / "phase4.json").append_extended(event)
    assert data["extended_events"][0]["predicted_band"] == "ultrasonic"
    assert data["extended_events"][0]["outcome"] == OUTCOME_CORRECT


def test_extended_event_rejects_unknown_predicted_band():
    session = Phase4SpatialExtendedSession(session_id="s1")
    with pytest.raises(ValueError, match="Unsupported Phase 4 band"):
        session.record_extended_band(
            "band_ultrasonic",
            predicted_band="unknown band",
            confidence=0.9,
            user_response="ultrasonic",
        )


def test_progress_store_rejects_unknown_schema(tmp_path: Path):
    path = tmp_path / "phase4.json"
    path.write_text('{"schema_version": "future", "spatial_events": [], "extended_events": []}')
    with pytest.raises(ValueError, match="Unsupported"):
        Phase4ProgressStore(path).load()


def test_summary_rejects_missing_event_fields(monkeypatch, tmp_path: Path):
    progress = tmp_path / "phase4.json"
    progress.write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "spatial_events": [{"session_id": "s1"}],
                "extended_events": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["phase4", "summary", "--progress", str(progress)])
    with pytest.raises(ValueError, match="missing fields"):
        main()


def test_summary_rejects_forbidden_fields(monkeypatch, tmp_path: Path):
    progress = tmp_path / "phase4.json"
    session = Phase4SpatialExtendedSession(session_id="s1")
    event = session.record_spatial(
        "localise_front",
        predicted_azimuth_degrees=5,
        confidence=0.9,
        user_response="answered",
    )
    data = Phase4ProgressStore(progress).append_spatial(event)
    data["spatial_events"][0]["raw_audio"] = "not allowed"
    progress.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["phase4", "summary", "--progress", str(progress)])
    with pytest.raises(ValueError, match="cannot contain"):
        main()


def test_scoring_outcomes():
    task = get_task("localise_front")
    assert (
        score_spatial(
            task,
            azimuth_error_degrees=5,
            elevation_error_degrees=5,
            confidence=0.9,
            user_response="answered",
        )
        == OUTCOME_CORRECT
    )
    assert (
        score_spatial(
            task,
            azimuth_error_degrees=45,
            elevation_error_degrees=5,
            confidence=0.9,
            user_response="answered",
        )
        == OUTCOME_PARTIAL
    )
    assert (
        score_spatial(
            task,
            azimuth_error_degrees=120,
            elevation_error_degrees=5,
            confidence=0.9,
            user_response="answered",
        )
        == OUTCOME_INCORRECT
    )
    assert (
        score_spatial(
            task,
            azimuth_error_degrees=5,
            elevation_error_degrees=5,
            confidence=0.05,
            user_response="answered",
        )
        == OUTCOME_SILENCE
    )
    assert (
        score_spatial(
            task,
            azimuth_error_degrees=5,
            elevation_error_degrees=5,
            confidence=0.9,
            user_response="",
        )
        == OUTCOME_MISSED
    )
    assert (
        score_spatial(
            task,
            azimuth_error_degrees=5,
            elevation_error_degrees=5,
            confidence=0.9,
            user_response="skip",
        )
        == OUTCOME_SKIPPED
    )
    assert (
        score_extended_band(
            expected_band="ultrasonic",
            predicted_band="high_frequency",
            confidence=0.9,
            user_response="ultrasonic",
        )
        == OUTCOME_PARTIAL
    )


def test_session_summary_computes_spatial_extended_and_environment():
    session = Phase4SpatialExtendedSession(session_id="s1")
    session.record_spatial(
        "localise_right",
        predicted_azimuth_degrees=80,
        confidence=0.8,
        user_response="answered",
        reaction_time_ms=500.0,
        environment_tag="street",
    )
    session.record_extended_band(
        "band_infrasonic",
        predicted_band="infrasonic",
        confidence=0.7,
        user_response="infrasonic",
        reaction_time_ms=600.0,
        environment_tag="street",
    )
    summary = session.summary()
    assert summary.spatial_accuracy == 1.0
    assert summary.extended_accuracy == 1.0
    assert summary.average_azimuth_error_degrees == 10.0
    assert summary.average_reaction_time_ms == 550.0
    assert summary.by_band["infrasonic"]["accuracy"] == 1.0
    assert summary.by_environment["street"]["spatial_attempts"] == 1
    assert summary.by_environment["street"]["extended_attempts"] == 1


def test_cli_list_tasks(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["phase4", "list-tasks"])
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["task_id"] == "localise_front"


def test_cli_spatial_extended_and_summary(monkeypatch, capsys, tmp_path: Path):
    progress = tmp_path / "phase4.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "phase4",
            "spatial",
            "--task",
            "localise_left",
            "--predicted-azimuth",
            "-80",
            "--confidence",
            "0.9",
            "--user-response",
            "answered",
            "--session-id",
            "s1",
            "--progress",
            str(progress),
        ],
    )
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["event"]["outcome"] == OUTCOME_CORRECT

    monkeypatch.setattr(
        "sys.argv",
        [
            "phase4",
            "extended",
            "--task",
            "band_ultrasonic",
            "--predicted-band",
            "ultrasonic",
            "--confidence",
            "0.9",
            "--user-response",
            "ultrasonic",
            "--session-id",
            "s1",
            "--progress",
            str(progress),
        ],
    )
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["event"]["outcome"] == OUTCOME_CORRECT

    monkeypatch.setattr("sys.argv", ["phase4", "summary", "--progress", str(progress)])
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["spatial_attempts"] == 1
    assert payload["extended_attempts"] == 1
    assert payload["spatial_accuracy"] == 1.0
    assert payload["extended_accuracy"] == 1.0
