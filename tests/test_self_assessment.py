"""Tests for the safe, calibration-bound self-assessment foundation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import pytest

from audiogram.self_assessment import Calibration, SelfAssessment


@dataclass
class FakePlayer:
    calibration: Calibration
    played: list[tuple[int, float, str]] = field(default_factory=list)

    def play_tone(self, frequency_hz: int, level_db_hl: float, ear: str, duration_ms: int) -> None:
        self.played.append((frequency_hz, level_db_hl, ear))


def test_requires_explicit_consent():
    session = SelfAssessment(FakePlayer(Calibration("test", "2026-01-01", "2027-01-01", 70)))

    with pytest.raises(PermissionError):
        session.measure_threshold("right", 1000, lambda _: True)


def test_finds_threshold_within_calibrated_limit():
    player = FakePlayer(Calibration("test", "2026-01-01", "2027-01-01", 70))
    session = SelfAssessment(player)
    session.give_consent()

    threshold = session.measure_threshold("right", 1000, lambda level: level >= 35)

    assert threshold == 35
    assert max(level for _, level, _ in player.played) <= 70


def test_stops_at_safe_limit_when_no_tone_is_heard():
    session = SelfAssessment(FakePlayer(Calibration("test", "2026-01-01", "2027-01-01", 50)))
    session.give_consent()

    with pytest.raises(ValueError, match="do not increase"):
        session.measure_threshold("left", 1000, lambda _: False)


def test_does_not_record_an_unbracketed_zero_db_hl_threshold():
    session = SelfAssessment(FakePlayer(Calibration("test", "2026-01-01", "2027-01-01", 50)))
    session.give_consent()

    with pytest.raises(ValueError, match="below this screening range"):
        session.measure_threshold("left", 1000, lambda _: True)


def test_rejects_an_unsafe_or_non_sensical_starting_level():
    session = SelfAssessment(FakePlayer(Calibration("test", "2026-01-01", "2027-01-01", 50)))
    session.give_consent()

    with pytest.raises(ValueError, match="greater than 0"):
        session.measure_threshold("left", 1000, lambda _: True, start_db_hl=0)
    with pytest.raises(ValueError, match="no more than 50"):
        session.measure_threshold("left", 1000, lambda _: True, start_db_hl=55)

    assert session.trials == []


def test_export_labels_result_as_non_clinical_self_assessment():
    session = SelfAssessment(FakePlayer(Calibration("test-device", "2026-01-01", "2027-01-01", 70)))
    session.give_consent()
    session.measure_threshold("right", 1000, lambda level: level >= 35)

    data = json.loads(session.export(subject="anonymous"))

    assert data["schema"] == "openhear-self-assessment-v1"
    assert data["screening_only"] is True
    assert data["calibration"]["device_id"] == "test-device"


def test_expired_calibration_prevents_playback():
    player = FakePlayer(Calibration("test", "2025-01-01", "2025-12-31", 70))
    session = SelfAssessment(player)
    session.give_consent()

    with pytest.raises(ValueError, match="expired"):
        session.measure_threshold("right", 1000, lambda _: True)

    assert player.played == []
