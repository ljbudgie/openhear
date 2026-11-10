"""Pin the full YAMNet-label -> OpenHear-class table so any change shows up in review."""

import csv
import json
from pathlib import Path

import pytest

from stream.sound_classifier import map_label_to_sound_key

_ROOT = Path(__file__).resolve().parent.parent
_LABELS = _ROOT / "stream" / "data" / "yamnet_class_map.csv"
_SNAPSHOT = Path(__file__).resolve().parent / "data" / "yamnet_label_map_snapshot.json"


def _current_table() -> dict[str, str]:
    with open(_LABELS, newline="", encoding="utf-8") as fh:
        labels = [row["display_name"] for row in csv.DictReader(fh)]
    assert len(labels) == 521
    return {label: key for label in labels if (key := map_label_to_sound_key(label))}


def test_label_table_matches_snapshot():
    """If this fails on purpose, regenerate the snapshot and explain why in the commit."""
    snapshot = json.loads(_SNAPSHOT.read_text(encoding="utf-8"))
    assert _current_table() == snapshot


@pytest.mark.parametrize(
    "label",
    ["Scary music", "Carnatic music", "Shuffling cards", "Busy signal", "Wind chime"],
)
def test_substring_lookalikes_do_not_fire_traffic_or_doorbell(label):
    assert map_label_to_sound_key(label) not in {"traffic", "doorbell"}


@pytest.mark.parametrize("label", ["Door", "Sliding door", "Cupboard open or close"])
def test_a_door_moving_is_not_a_knock(label):
    """Decision, Nov 2026: only the 'Knock' label fires the knock pattern."""
    assert map_label_to_sound_key(label) is None


def test_dialling_is_not_ringing():
    """Decision, Nov 2026: DTMF dialling tones do not fire the phone pattern."""
    assert map_label_to_sound_key("Telephone dialing, DTMF") is None
    assert map_label_to_sound_key("Telephone bell ringing") == "phone"
    assert map_label_to_sound_key("Ringtone") == "phone"


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Knock", "knock"),
        ("Baby cry, infant cry", "baby_cry"),
        ("Doorbell", "doorbell"),
        ("Smoke detector, smoke alarm", "alarm"),
        ("Vehicle horn, car horn, honking", "traffic"),
        ("Reversing beeps", "traffic"),
        ("Engine knocking", None),
        ("Engine", None),
        ("Traffic noise, roadway noise", None),
    ],
)
def test_named_everyday_sounds_map_to_their_class(label, expected):
    assert map_label_to_sound_key(label) == expected
