"""Tests for therapy/adapt.py — closed-loop n-of-1 personalisation."""

from __future__ import annotations

import pytest

from therapy.adapt import (
    MAX_SESSION_S,
    MIN_SESSION_S,
    SessionOutcome,
    load_outcomes,
    personalise,
    record_outcome,
)
from therapy.protocol import get_protocol

_ALPHA = get_protocol("alpha_relax")  # 10 Hz, alpha band (8-13 Hz)


def _o(beat_hz, rating, *, length=600):
    return SessionOutcome(beat_hz=beat_hz, session_length_s=length, rating=rating)


# ── Outcome validation ──────────────────────────────────────────────────────


def test_outcome_validates_rating_and_fields():
    with pytest.raises(ValueError):
        SessionOutcome(beat_hz=10, session_length_s=600, rating=1.5)
    with pytest.raises(ValueError):
        SessionOutcome(beat_hz=0, session_length_s=600, rating=0.0)
    with pytest.raises(ValueError):
        SessionOutcome(beat_hz=10, session_length_s=0, rating=0.0)


# ── Cold start ──────────────────────────────────────────────────────────────


def test_cold_start_returns_protocol_default():
    s = personalise(_ALPHA, [])
    assert s.beat_hz == 10.0
    assert s.session_length_s == _ALPHA.session_length_s
    assert s.basis == 0
    assert s.explored is False
    assert "starting from the protocol default" in s.rationale.lower()


# ── Exploit: converge on liked settings ─────────────────────────────────────


def test_converges_toward_liked_frequency():
    history = [_o(11.5, 1.0), _o(11.5, 0.8), _o(8.5, -1.0)]
    s = personalise(_ALPHA, history)
    assert s.explored is False
    # Weighted by positive ratings, the suggestion sits near 11.5 Hz.
    assert s.beat_hz == pytest.approx(11.5, abs=0.2)
    assert s.basis == 3


def test_weighted_average_between_two_liked_frequencies():
    history = [_o(9.0, 1.0), _o(11.0, 1.0)]
    s = personalise(_ALPHA, history)
    assert s.beat_hz == pytest.approx(10.0, abs=0.1)


def test_session_length_follows_liked_sessions():
    history = [_o(10.0, 1.0, length=1200), _o(10.0, 1.0, length=1200)]
    s = personalise(_ALPHA, history)
    assert s.session_length_s == 1200


# ── Explore: nothing liked yet ──────────────────────────────────────────────


def test_explores_when_nothing_rated_positively():
    history = [_o(10.0, -1.0), _o(10.0, 0.0)]
    s = personalise(_ALPHA, history, step_hz=1.0)
    assert s.explored is True
    # Steps away from the most recent setting, staying in the alpha band.
    assert s.beat_hz != 10.0
    assert 8.0 <= s.beat_hz < 13.0


def test_exploration_steps_down_near_band_top():
    # Most recent at 12.5 Hz; +1 would leave the band, so step down.
    history = [_o(12.5, -1.0)]
    s = personalise(_ALPHA, history, step_hz=1.0)
    assert s.explored is True
    assert s.beat_hz < 12.5
    assert 8.0 <= s.beat_hz < 13.0


# ── Stays in band ───────────────────────────────────────────────────────────


def test_other_band_history_is_ignored():
    # Delta (2 Hz) outcomes must not influence an alpha protocol.
    history = [_o(2.0, 1.0), _o(2.0, 1.0)]
    s = personalise(_ALPHA, history)
    assert s.basis == 0  # no in-band data
    assert s.beat_hz == 10.0  # cold-start default


def test_suggestion_never_leaves_band():
    history = [_o(12.9, 1.0), _o(12.9, 1.0)]
    s = personalise(_ALPHA, history)
    assert 8.0 <= s.beat_hz < 13.0


# ── Bounded session length ──────────────────────────────────────────────────


def test_session_length_is_clamped():
    long_hist = [_o(10.0, 1.0, length=99999)]
    assert personalise(_ALPHA, long_hist).session_length_s <= MAX_SESSION_S
    short_hist = [_o(10.0, 1.0, length=1)]
    assert personalise(_ALPHA, short_hist).session_length_s >= MIN_SESSION_S


# ── Persistence round-trip ──────────────────────────────────────────────────


def test_record_and_load_round_trip(tmp_path):
    store = tmp_path / "outcomes.jsonl"
    record_outcome(_o(10.0, 1.0), store_path=store)
    record_outcome(_o(11.0, -0.5), store_path=store)
    loaded = load_outcomes(store)
    assert [o.beat_hz for o in loaded] == [10.0, 11.0]
    assert loaded[1].rating == -0.5


def test_load_missing_file_is_empty(tmp_path):
    assert load_outcomes(tmp_path / "nope.jsonl") == []


def test_load_rejects_malformed_line(tmp_path):
    store = tmp_path / "bad.jsonl"
    store.write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid session outcome"):
        load_outcomes(store)


# ── End-to-end loop: a record → personalise cycle improves toward a sweet spot ─


def test_closed_loop_converges_over_sessions(tmp_path):
    store = tmp_path / "loop.jsonl"
    # User consistently likes ~9 Hz, dislikes the 10 Hz default.
    record_outcome(_o(10.0, -0.8), store_path=store)
    record_outcome(_o(9.0, 1.0), store_path=store)
    record_outcome(_o(9.0, 0.9), store_path=store)
    s = personalise(_ALPHA, load_outcomes(store))
    assert s.beat_hz == pytest.approx(9.0, abs=0.2)
    assert s.explored is False
