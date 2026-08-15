"""Calibrated, consent-led self-assessment workflow for an Iris integration.

This module intentionally does not generate sound.  An integration must supply
a calibrated tone player and collect each explicit person response.  Results
are self-assessments, not clinical audiograms or fitting prescriptions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Protocol

from audiogram.audiogram import STANDARD_FREQUENCIES_HZ

SAFE_MAX_TEST_LEVEL_DB_HL = 80
MAX_PRESENTATIONS_PER_FREQUENCY = 20
NON_CLINICAL_NOTICE = (
    "Self-assessed with a calibrated playback device; not a clinical audiogram "
    "or a basis for automatic fitting changes."
)


@dataclass(frozen=True)
class Calibration:
    """Playback calibration declared by the hardware integration."""

    device_id: str
    calibrated_on: str
    expires_on: str
    maximum_db_hl: float

    def __post_init__(self) -> None:
        calibrated_on = date.fromisoformat(self.calibrated_on)
        expires_on = date.fromisoformat(self.expires_on)
        if expires_on < calibrated_on:
            raise ValueError("expires_on must not precede calibrated_on.")
        if not 0 < self.maximum_db_hl <= SAFE_MAX_TEST_LEVEL_DB_HL:
            raise ValueError(
                f"maximum_db_hl must be greater than 0 and no more than "
                f"{SAFE_MAX_TEST_LEVEL_DB_HL}."
            )

    def valid_today(self, *, as_of: date | None = None) -> bool:
        """Whether this calibration is currently valid for a presentation."""
        return (as_of or date.today()) <= date.fromisoformat(self.expires_on)


class CalibratedTonePlayer(Protocol):
    """Hardware boundary; implementations own calibrated tone output."""

    calibration: Calibration

    def play_tone(self, frequency_hz: int, level_db_hl: float, ear: str, duration_ms: int) -> None:
        """Present one calibrated tone without exceeding the declared limit."""


@dataclass(frozen=True)
class Trial:
    """One explicitly acknowledged tone presentation."""

    ear: str
    frequency_hz: int
    level_db_hl: float
    heard: bool


@dataclass
class SelfAssessment:
    """Runs conservative threshold seeking through a calibrated player."""

    player: CalibratedTonePlayer
    consent_given: bool = False
    stopped: bool = False
    trials: list[Trial] = field(default_factory=list)

    def give_consent(self) -> None:
        """Record explicit consent before any tone can be presented."""
        self.consent_given = True

    def stop(self) -> None:
        """Immediately prevent further presentations in this session."""
        self.stopped = True

    def measure_threshold(
        self,
        ear: str,
        frequency_hz: int,
        response: Callable[[float], bool],
        *,
        start_db_hl: float = 40,
    ) -> float:
        """Seek a threshold using 10 dB down / 5 dB up steps.

        ``response`` is deliberately provided by the calling experience (for
        example, Iris asking the person whether they heard the tone).  The
        assistant never infers a response from audio or user data.
        """
        if not self.consent_given:
            raise PermissionError("Explicit consent is required before self-assessment.")
        if self.stopped:
            raise RuntimeError("This self-assessment was stopped by the person.")
        if not self.player.calibration.valid_today():
            raise ValueError("Playback calibration is expired; no tone will be presented.")
        if ear not in {"left", "right"}:
            raise ValueError("ear must be 'left' or 'right'.")
        if frequency_hz not in STANDARD_FREQUENCIES_HZ:
            raise ValueError(f"{frequency_hz} Hz is not a standard test frequency.")

        maximum = self.player.calibration.maximum_db_hl
        if not 0 < start_db_hl <= maximum:
            raise ValueError(
                f"start_db_hl must be greater than 0 and no more than {maximum} dB HL."
            )
        presentations = 0

        def present(level_db_hl: float) -> bool:
            nonlocal presentations
            if presentations >= MAX_PRESENTATIONS_PER_FREQUENCY:
                raise RuntimeError("Presentation limit reached; no threshold was recorded.")
            presentations += 1
            return self._present(ear, frequency_hz, level_db_hl, response)

        level = float(start_db_hl)
        heard = present(level)
        not_heard_seen = not heard
        while heard and level > 0:
            next_level = level - 10.0
            if next_level <= 0:
                raise ValueError(
                    "Response remained audible at the lowest screening level; "
                    "the threshold is below this screening range and was not recorded."
                )
            level = next_level
            heard = present(level)
            not_heard_seen = not_heard_seen or not heard
        while not heard and level < maximum:
            level = min(maximum, level + 5.0)
            heard = present(level)
            not_heard_seen = not_heard_seen or not heard
        if not heard:
            raise ValueError(
                f"No response at the safe calibrated limit ({maximum} dB HL); "
                "do not increase level. Seek a clinical assessment."
            )
        if not not_heard_seen:
            raise RuntimeError("Threshold was not bracketed; no threshold was recorded.")
        return level

    def export(self, *, subject: str = "", notes: str = "") -> str:
        """Export an assessment record, deliberately distinct from an audiogram."""
        data = {
            "schema": "openhear-self-assessment-v1",
            "subject": subject or "anonymous",
            "notes": notes,
            "screening_only": True,
            "notice": NON_CLINICAL_NOTICE,
            "calibration": {
                "device_id": self.player.calibration.device_id,
                "calibrated_on": self.player.calibration.calibrated_on,
                "expires_on": self.player.calibration.expires_on,
                "maximum_db_hl": self.player.calibration.maximum_db_hl,
            },
            "trials": [
                {
                    "ear": trial.ear,
                    "frequency_hz": trial.frequency_hz,
                    "level_db_hl": trial.level_db_hl,
                    "heard": trial.heard,
                }
                for trial in self.trials
            ],
        }
        return json.dumps(data, indent=2)

    def _present(
        self,
        ear: str,
        frequency_hz: int,
        level_db_hl: float,
        response: Callable[[float], bool],
    ) -> bool:
        if self.stopped:
            raise RuntimeError("This self-assessment was stopped by the person.")
        self.player.play_tone(frequency_hz, level_db_hl, ear, duration_ms=1_000)
        heard = bool(response(level_db_hl))
        self.trials.append(Trial(ear, frequency_hz, level_db_hl, heard))
        return heard
