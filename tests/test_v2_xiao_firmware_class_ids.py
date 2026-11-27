"""Contract test: v2 XIAO firmware class IDs match stream.haptic_mapper.

The Arduino sketch is not compiled in CI. This test only parses the
CLASS_EFFECTS table in the source so the canonical 10-class IDs cannot
drift silently from the Python mapper.
"""

from __future__ import annotations

import re
from pathlib import Path

from stream.haptic_mapper import SOUND_CLASS_IDS

FIRMWARE_PATH = (
    Path(__file__).resolve().parents[1]
    / "hardware"
    / "wristband"
    / "v2-xiao-nrf52840"
    / "firmware"
    / "openhear_v2_xiao_nrf52840.ino"
)

_NUM_CLASSES_RE = re.compile(
    r"static const uint8_t\s+NUM_SOUND_CLASSES\s*=\s*(\d+)\s*;"
)
_TABLE_RE = re.compile(
    r"static const ClassEffect CLASS_EFFECTS\[NUM_SOUND_CLASSES\]\s*=\s*\{(.*?)\};",
    re.DOTALL,
)
_ENTRY_RE = re.compile(
    r'\{\s*"(?P<label>[a-z_]+)"\s*,'
    r"\s*(?P<primary>\d+)\s*,"
    r"\s*(?P<accent>\d+)\s*,"
    r"\s*(?P<repeat>\d+)\s*,"
    r"\s*(?P<min_intensity>\d+)\s*\}"
)


def _parse_firmware_class_table(source: str) -> tuple[int, list[dict[str, str | int]]]:
    num_match = _NUM_CLASSES_RE.search(source)
    assert num_match is not None, "NUM_SOUND_CLASSES not found in the v2 XIAO sketch"
    declared = int(num_match.group(1))

    table_match = _TABLE_RE.search(source)
    assert table_match is not None, "CLASS_EFFECTS table not found in the v2 XIAO sketch"

    entries: list[dict[str, str | int]] = []
    for match in _ENTRY_RE.finditer(table_match.group(1)):
        entries.append(
            {
                "label": match.group("label"),
                "primary": int(match.group("primary")),
                "accent": int(match.group("accent")),
                "repeat": int(match.group("repeat")),
                "min_intensity": int(match.group("min_intensity")),
            }
        )
    return declared, entries


def test_firmware_source_is_present():
    assert FIRMWARE_PATH.is_file(), f"missing firmware sketch at {FIRMWARE_PATH}"


def test_firmware_class_ids_match_haptic_mapper():
    declared, entries = _parse_firmware_class_table(FIRMWARE_PATH.read_text(encoding="utf-8"))

    assert declared == len(SOUND_CLASS_IDS)
    assert len(entries) == declared

    by_id = {profile_id: name for name, profile_id in SOUND_CLASS_IDS.items()}
    firmware_labels = [entry["label"] for entry in entries]
    assert firmware_labels == [by_id[i] for i in range(declared)]

    for index, entry in enumerate(entries):
        assert SOUND_CLASS_IDS[str(entry["label"])] == index


def test_firmware_silence_has_no_vibration():
    _, entries = _parse_firmware_class_table(FIRMWARE_PATH.read_text(encoding="utf-8"))
    silence = entries[SOUND_CLASS_IDS["silence"]]
    assert silence["label"] == "silence"
    assert silence["primary"] == 0
    assert silence["accent"] == 0
    assert silence["repeat"] == 0
