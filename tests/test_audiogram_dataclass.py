"""Tests for the canonical :class:`audiogram.audiogram.Audiogram` dataclass."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from audiogram.audiogram import (
    MAX_THRESHOLD_DB_HL,
    MIN_THRESHOLD_DB_HL,
    STANDARD_FREQUENCIES_HZ,
    Audiogram,
    severity,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = REPO_ROOT / "examples" / "sample_audiogram.json"


def test_standard_frequencies_match_iso_8253_1():
    """Per the master prompt, these are the ten standard test frequencies."""
    assert STANDARD_FREQUENCIES_HZ == (
        250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000,
    )


@pytest.mark.parametrize(
    ("db_hl", "expected"),
    [
        (-5, "normal"),
        (0, "normal"),
        (25, "normal"),
        (26, "mild"),
        (40, "mild"),
        (41, "moderate"),
        (55, "moderate"),
        (70, "moderately-severe"),
        (90, "severe"),
        (95, "profound"),
        (120, "profound"),
        (130, "profound"),
    ],
)
def test_severity_function_matches_clinical_bands(db_hl, expected):
    assert severity(db_hl) == expected


def test_audiogram_construction_and_pta():
    ag = Audiogram(
        right_ear={500: 30, 1000: 40, 2000: 50, 4000: 60},
        left_ear={500: 25, 1000: 35, 2000: 45, 4000: 55},
        date_measured="2024-11-15",
        source="manual_entry",
        subject="anon",
    )
    assert ag.pure_tone_average("right") == pytest.approx(45.0)
    assert ag.pure_tone_average("left") == pytest.approx(40.0)
    assert ag.severity(2000, "right") == "moderate"
    assert ag.severity(4000, "left") == "moderate"


def test_audiogram_pta_raises_when_pta_freqs_missing():
    ag = Audiogram(
        right_ear={500: 30, 1000: 40},  # missing 2000 and 4000
        left_ear={500: 25, 1000: 35, 2000: 45, 4000: 55},
    )
    with pytest.raises(ValueError, match="Cannot compute PTA"):
        ag.pure_tone_average("right")


def test_audiogram_threshold_out_of_range_rejected():
    with pytest.raises(ValueError, match="outside the valid range"):
        Audiogram(right_ear={1000: MAX_THRESHOLD_DB_HL + 1})
    with pytest.raises(ValueError, match="outside the valid range"):
        Audiogram(left_ear={1000: MIN_THRESHOLD_DB_HL - 1})


def test_audiogram_invalid_date_rejected():
    with pytest.raises(ValueError, match="ISO-8601"):
        Audiogram(
            right_ear={1000: 40},
            date_measured="not-a-date",
        )


def test_audiogram_invalid_ear_label_rejected():
    ag = Audiogram(right_ear={1000: 40})
    with pytest.raises(ValueError, match="ear must be"):
        ag.thresholds("centre")


def test_audiogram_severity_for_unknown_freq_raises():
    ag = Audiogram(right_ear={1000: 40})
    with pytest.raises(KeyError, match="No threshold recorded"):
        ag.severity(8000, "right")


def test_audiogram_round_trip_via_json():
    ag = Audiogram(
        right_ear={250: 30, 500: 35, 1000: 45, 2000: 55, 4000: 65},
        left_ear={250: 35, 500: 40, 1000: 50, 2000: 60, 4000: 70},
        date_measured="2024-11-15",
        source="manual_entry",
        subject="anon",
        notes="round-trip test",
    )
    text = ag.to_json()
    rebuilt = Audiogram.from_json(text)
    assert rebuilt.right_ear == ag.right_ear
    assert rebuilt.left_ear == ag.left_ear
    assert rebuilt.date_measured == ag.date_measured
    assert rebuilt.source == ag.source
    assert rebuilt.notes == ag.notes


def test_audiogram_from_dict_accepts_prompt_style_shape():
    """The master-prompt example shape uses {freq: db} maps directly."""
    data = {
        "date": "2024-11-15",
        "source": "manual_entry",
        "left_ear": {"250": 35, "500": 40, "1000": 50},
        "right_ear": {"250": 30, "500": 35, "1000": 45},
        "type": "sensorineural",
    }
    ag = Audiogram.from_dict(data)
    assert ag.right_ear[1000] == 45.0
    assert ag.left_ear[250] == 35.0
    assert ag.source == "manual_entry"


def test_audiogram_from_dict_requires_both_ears():
    with pytest.raises(ValueError, match="must contain 'right_ear'"):
        Audiogram.from_dict({"left_ear": {"1000": 30}})


def test_audiogram_to_dict_uses_canonical_v1_shape():
    ag = Audiogram(
        right_ear={500: 30, 1000: 40},
        left_ear={500: 25, 1000: 35},
        date_measured="2024-11-15",
        source="manual_entry",
        subject="anon",
    )
    d = ag.to_dict()
    assert d["format_version"] == "openhear-audiogram-v1"
    assert d["right_ear"]["symbol"] == "O"
    assert d["left_ear"]["symbol"] == "X"
    # thresholds must be a list of {freq_hz, db_hl}
    entries = d["right_ear"]["thresholds"]
    assert {"freq_hz": 500, "db_hl": 30} in entries
    assert {"freq_hz": 1000, "db_hl": 40} in entries


def test_audiogram_to_csv_has_one_header_and_one_row_per_threshold():
    ag = Audiogram(
        right_ear={500: 30, 1000: 40},
        left_ear={500: 25, 1000: 35},
    )
    csv_text = ag.to_csv()
    lines = [l for l in csv_text.strip().splitlines() if l]
    assert lines[0] == "ear,freq_hz,db_hl"
    assert len(lines) == 1 + 4  # header + 4 thresholds
    assert "right,500,30" in lines
    assert "left,1000,35" in lines


def test_audiogram_from_path_loads_bundled_sample():
    """The bundled examples/sample_audiogram.json must parse cleanly."""
    ag = Audiogram.from_path(SAMPLE_PATH)
    assert ag.source == "manual_entry"
    assert ag.right_ear[1000] == 45.0
    assert ag.left_ear[8000] == 80.0
    assert ag.pure_tone_average("right") == pytest.approx(
        (35 + 45 + 55 + 65) / 4
    )


def test_existing_burgess_v1_file_loads_via_dataclass(burgess_audiogram_path):
    """The dataclass must coexist with the existing v1 sample data."""
    ag = Audiogram.from_path(burgess_audiogram_path)
    assert ag.subject == "Lewis Burgess"
    # 1000 Hz threshold from the bundled file.
    assert ag.right_ear[1000] == 75.0
    assert ag.left_ear[1000] == 75.0


def test_loader_dict_can_be_consumed_by_dataclass(audiogram_path):
    """The dict-based loader and dataclass must agree on the same file."""
    raw = json.loads(Path(audiogram_path).read_text())
    ag = Audiogram.from_dict(raw)
    assert ag.right_ear[2000] == 50.0
    assert ag.left_ear[8000] == 75.0
