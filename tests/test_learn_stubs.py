"""Tests for the Phase 6 learn/ scaffolding.

Each public function must raise NotImplementedError with a helpful
message pointing contributors at docs/ARCHITECTURE.md or the module
docstring.  These tests guard against accidental half-implementations
that would otherwise silently succeed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

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


def test_learn_package_exposes_subpackages():
    assert preferences is not None
    assert engine is not None
    assert profiles is not None


def test_preference_event_has_sane_defaults():
    ev = PreferenceEvent()
    assert ev.choice == "undecided"
    assert ev.environment == ""
    assert ev.timestamp  # auto-populated ISO string
    # Round-trip: ISO format must be parseable.
    from datetime import datetime
    datetime.fromisoformat(ev.timestamp)


def test_preference_event_accepts_valid_choices():
    for choice in ("A", "B", "undecided"):
        ev = PreferenceEvent(choice=choice)  # type: ignore[arg-type]
        assert ev.choice == choice


def test_record_choice_is_documented_stub(tmp_path):
    with pytest.raises(NotImplementedError, match="Phase 6"):
        record_choice(PreferenceEvent(), store_path=tmp_path / "log.jsonl")


def test_load_events_is_documented_stub(tmp_path):
    with pytest.raises(NotImplementedError, match="Phase 6"):
        load_events(tmp_path / "log.jsonl")


def test_summarise_is_documented_stub():
    with pytest.raises(NotImplementedError, match="Phase 6"):
        summarise([])


def test_engine_stubs_raise_not_implemented(tmp_path):
    state = EngineState(data={})
    with pytest.raises(NotImplementedError, match="Phase 6"):
        state.to_json()
    with pytest.raises(NotImplementedError, match="Phase 6"):
        EngineState.from_json("{}")
    with pytest.raises(NotImplementedError, match="Phase 6"):
        suggest_next_config(state,
                            base_config_path=tmp_path / "a.yaml",
                            output_path=tmp_path / "b.yaml")
    with pytest.raises(NotImplementedError, match="Phase 6"):
        update_from_feedback(state, PreferenceEvent())


def test_profiles_stubs_raise_not_implemented(tmp_path):
    with pytest.raises(NotImplementedError, match="Phase 6"):
        save_profile(tmp_path / "c.yaml", "Restaurant", root=tmp_path)
    with pytest.raises(NotImplementedError, match="Phase 6"):
        load_profile("Restaurant", root=tmp_path)
    with pytest.raises(NotImplementedError, match="Phase 6"):
        list_profiles(root=tmp_path)
    with pytest.raises(NotImplementedError, match="Phase 6"):
        delete_profile("Restaurant", root=tmp_path)


def test_profiles_root_default_location():
    # Must live under the user's ~/.openhear dir for discoverability.
    assert PROFILES_ROOT.name == "profiles"
    assert PROFILES_ROOT.parent.name == ".openhear"
