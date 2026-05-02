"""Tests for the Phase 6 learn/ implementation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dsp.user_config import load_config
from learn import engine, preferences, profiles
from learn.engine import EngineState, suggest_next_config, update_from_feedback
from learn.preferences import PreferenceEvent, load_events, record_choice, summarise
from learn.profiles import (
    PROFILES_ROOT,
    delete_profile,
    list_profiles,
    load_profile,
    save_profile,
)


def _write_test_config(path: Path, *, ratio: float = 2.5, boost_db: float = 6.0) -> Path:
    path.write_text(
        "\n".join(
            [
                "compression:",
                f"  ratio: {ratio}",
                "  knee_db: -40",
                "  attack_ms: 5",
                "  release_ms: 50",
                "noise:",
                "  floor_db: -45",
                "  reduction_strength: 0.6",
                "  gate_enabled: true",
                "voice:",
                "  boost_hz: [1000, 4000]",
                f"  boost_db: {boost_db}",
                "beamforming:",
                "  enabled: false",
                "  width_deg: 60",
                "  direction_deg: 0",
                "system:",
                "  sample_rate: 16000",
                "  buffer_size: 256",
                "  input_device: null",
                "  output_device: null",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_learn_package_exposes_subpackages():
    assert preferences is not None
    assert engine is not None
    assert profiles is not None


def test_preference_event_has_sane_defaults():
    ev = PreferenceEvent()
    assert ev.choice == "undecided"
    assert ev.environment == ""
    assert ev.timestamp
    from datetime import datetime

    datetime.fromisoformat(ev.timestamp)


def test_preference_jsonl_round_trip_and_summary(tmp_path):
    store = tmp_path / "nested" / "preferences.jsonl"
    first = PreferenceEvent(
        environment="restaurant",
        config_a_path="a.yaml",
        config_b_path="b.yaml",
        choice="A",
        notes="clearer",
    )
    second = PreferenceEvent(environment="restaurant", choice="undecided")

    record_choice(first, store_path=store)
    record_choice(second, store_path=store)

    assert store.read_text(encoding="utf-8").count("\n") == 2
    events = load_events(store)
    assert events == [first, second]
    assert summarise(events) == {"restaurant": {"A": 1, "B": 0, "undecided": 1}}


def test_preference_load_missing_file_returns_empty_list(tmp_path):
    assert load_events(tmp_path / "missing.jsonl") == []


def test_preference_rejects_invalid_choice(tmp_path):
    event = PreferenceEvent(choice="C")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Invalid preference choice"):
        record_choice(event, store_path=tmp_path / "preferences.jsonl")


def test_engine_state_json_round_trip_is_deterministic():
    state = EngineState(data={"z": 2, "a": {"b": 1}})
    encoded = state.to_json()
    assert encoded == '{"a":{"b":1},"z":2}'
    assert EngineState.from_json(encoded) == state
    with pytest.raises(ValueError, match="object"):
        EngineState.from_json("[]")


def test_update_from_feedback_returns_new_state_with_summary():
    original = EngineState(data={})
    event = PreferenceEvent(environment="office", choice="B")

    updated = update_from_feedback(original, event)

    assert original.data == {}
    assert updated.data["events"] == [event.__dict__]
    assert updated.data["summary"] == {"office": {"A": 0, "B": 1, "undecided": 0}}
    assert updated.data["last_environment"] == "office"


def test_suggest_next_config_blends_toward_preferred_config(tmp_path):
    base = _write_test_config(tmp_path / "base.yaml", ratio=2.0, boost_db=4.0)
    preferred = _write_test_config(
        tmp_path / "preferred.yaml",
        ratio=6.0,
        boost_db=12.0,
    )
    output = tmp_path / "candidate.yaml"
    state = update_from_feedback(
        EngineState(data={}),
        PreferenceEvent(
            environment="restaurant",
            config_a_path=str(base),
            config_b_path=str(preferred),
            choice="B",
        ),
    )

    result = suggest_next_config(state, base_config_path=base, output_path=output)

    assert result == output
    candidate = load_config(output)
    assert candidate.compression.ratio == pytest.approx(4.0)
    assert candidate.voice.boost_db == pytest.approx(8.0)


def test_suggest_next_config_clamps_explicit_overrides(tmp_path):
    base = _write_test_config(tmp_path / "base.yaml")
    output = tmp_path / "candidate.yaml"
    state = EngineState(
        data={
            "config_overrides": {
                "compression": {"ratio": 99},
                "voice": {"boost_db": -99},
            }
        }
    )

    suggest_next_config(state, base_config_path=base, output_path=output)

    candidate = load_config(output)
    assert candidate.compression.ratio == 10.0
    assert candidate.voice.boost_db == -24.0


def test_suggest_next_config_explores_when_feedback_has_no_files(tmp_path):
    base = _write_test_config(tmp_path / "base.yaml", boost_db=4.0)
    output = tmp_path / "candidate.yaml"
    state = update_from_feedback(
        EngineState(data={}),
        PreferenceEvent(environment="commute", choice="A"),
    )

    suggest_next_config(state, base_config_path=base, output_path=output)

    assert load_config(output).voice.boost_db == pytest.approx(4.5)


def test_profiles_save_load_list_delete(tmp_path):
    config = _write_test_config(tmp_path / "config.yaml", ratio=3.0)
    root = tmp_path / "profiles"

    profile_dir = save_profile(
        config,
        "Quiet Home",
        environment="home",
        notes="evening",
        root=root,
    )

    assert profile_dir == root / "quiet_home"
    assert list_profiles(root=root) == ["Quiet Home"]
    loaded = load_profile("Quiet Home", root=root)
    assert loaded["metadata"]["name"] == "Quiet Home"
    assert set(loaded["metadata"]) == {
        "created_at",
        "environment",
        "name",
        "notes",
        "slug",
    }
    assert loaded["metadata"]["environment"] == "home"
    assert loaded["metadata"]["notes"] == "evening"
    assert loaded["metadata"]["slug"] == "quiet_home"
    assert loaded["config"]["compression"]["ratio"] == 3.0
    assert Path(loaded["config_path"]).name == "config.yaml"

    delete_profile("Quiet Home", root=root)
    assert list_profiles(root=root) == []
    with pytest.raises(FileNotFoundError, match="Profile not found"):
        load_profile("Quiet Home", root=root)


def test_profile_save_rejects_blank_name_and_missing_config(tmp_path):
    config = _write_test_config(tmp_path / "config.yaml")
    with pytest.raises(ValueError, match="must not be blank"):
        save_profile(config, " ", root=tmp_path / "profiles")
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        save_profile(tmp_path / "missing.yaml", "Missing", root=tmp_path / "profiles")


def test_list_profiles_ignores_invalid_metadata(tmp_path):
    root = tmp_path / "profiles"
    bad = root / "bad"
    bad.mkdir(parents=True)
    (bad / "metadata.json").write_text("{", encoding="utf-8")
    assert list_profiles(root=root) == []


def test_profiles_root_default_location():
    assert PROFILES_ROOT.name == "profiles"
    assert PROFILES_ROOT.parent.name == ".openhear"


@pytest.mark.parametrize("invalid_metadata", [["not", "object"], "not an object", 7, None])
def test_profile_metadata_is_json_object(tmp_path, invalid_metadata):
    config = _write_test_config(tmp_path / "config.yaml")
    profile_dir = save_profile(config, "Restaurant", root=tmp_path / "profiles")
    (profile_dir / "metadata.json").write_text(json.dumps(invalid_metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="metadata"):
        load_profile("Restaurant", root=tmp_path / "profiles")
