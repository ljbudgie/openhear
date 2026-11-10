"""
bench_datasets.py – dataset definitions for scripts/bench_awareness.py.

Each dataset says, for every clip, which OpenHear classes it is a target for
and whether it is a negative, under a named *scheme*. A scheme pairs a label
map (which YAMNet labels fire which wristband pattern) with the matching idea
of what counts as a target:

* ``v1.7.0`` – the label map shipped in v1.7.0, where any engine fired traffic.
* ``v1.8.0`` – the label map in this release, where traffic is an allowlist of
  horns and other vehicle warnings.

No audio is committed. Every dataset is downloaded at run time by the
workflow. Licences are recorded in each dataset's ``LICENCE`` string and in
the signed report.

The metadata functions here are pure (rows in, clip specs out) so they can be
tested without the audio.
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

SCHEMES: tuple[str, ...] = ("v1.7.0", "v1.8.0")
MAX_CLIP_SECONDS = 30.0


@dataclass(frozen=True)
class ClipSpec:
    """One clip's identity and ground truth, before any audio is read."""

    clip_id: str
    path: str  # file path, or member name inside an archive
    labels: tuple[str, ...]  # the dataset's own labels for this clip
    groups: tuple[str, ...] = ()  # named groups for per-group fire rates
    targets: dict[str, frozenset[str]] = field(default_factory=dict)  # scheme -> classes
    negative: dict[str, bool] = field(default_factory=dict)  # scheme -> is a negative


def _targets(label_to_class: dict[str, str], labels: tuple[str, ...]) -> frozenset[str]:
    return frozenset(label_to_class[label] for label in labels if label in label_to_class)


def _spec(
    clip_id: str,
    path: str,
    labels: tuple[str, ...],
    groups: tuple[str, ...],
    maps: dict[str, dict[str, str]],
    *,
    eligible_negative: bool = True,
) -> ClipSpec:
    targets = {scheme: _targets(maps[scheme], labels) for scheme in SCHEMES}
    negative = {scheme: eligible_negative and not targets[scheme] for scheme in SCHEMES}
    return ClipSpec(clip_id, path, labels, groups, targets, negative)


# ---------------------------------------------------------------------------
# ESC-50
# ---------------------------------------------------------------------------

ESC50_LICENCE = "CC BY-NC 3.0 (audio not redistributed; before/after comparison only)"

_ESC50_COMMON: dict[str, str] = {
    "dog": "dog",
    "siren": "alarm",
    "clock_alarm": "alarm",
    "car_horn": "traffic",
    "door_wood_knock": "knock",
    "crying_baby": "baby_cry",
}
ESC50_TARGETS: dict[str, dict[str, str]] = {
    # v1.7.0 treated any engine as traffic, so "engine" was a traffic target.
    "v1.7.0": {**_ESC50_COMMON, "engine": "traffic"},
    # From v1.8.0 the traffic pattern is for vehicle warnings, so an engine
    # clip is a negative: the wristband should stay quiet.
    "v1.8.0": dict(_ESC50_COMMON),
}


def esc50_specs(rows: list[dict[str, str]]) -> list[ClipSpec]:
    """Clip specs from the rows of ESC-50's ``meta/esc50.csv``."""
    specs = []
    for row in sorted(rows, key=lambda item: item["filename"]):
        category = row["category"]
        specs.append(
            _spec(row["filename"], f"audio/{row['filename']}", (category,), (category,), ESC50_TARGETS)
        )
    return specs


def load_esc50(root: Path) -> list[ClipSpec]:
    with open(root / "meta" / "esc50.csv", newline="", encoding="utf-8") as fh:
        return esc50_specs(list(csv.DictReader(fh)))


# ---------------------------------------------------------------------------
# FSD50K (eval split)
# ---------------------------------------------------------------------------

FSD50K_LICENCE = (
    "Per-clip Creative Commons licences. Only CC0 and CC BY clips are used; "
    "CC BY-NC and CC Sampling+ clips are excluded. Audio not redistributed."
)
FSD50K_ALLOWED_LICENCE_MARKERS: tuple[str, ...] = ("/publicdomain/zero/", "/licenses/by/")

_FSD50K_COMMON: dict[str, str] = {
    "Doorbell": "doorbell",
    "Knock": "knock",
    "Telephone": "phone",
    "Ringtone": "phone",
    "Telephone_bell_ringing": "phone",
    "Speech": "voice",
    "Male_speech_and_man_speaking": "voice",
    "Female_speech_and_woman_speaking": "voice",
    "Child_speech_and_kid_speaking": "voice",
    "Conversation": "voice",
    "Speech_synthesizer": "voice",
    "Bark": "dog",
    "Dog": "dog",
    "Siren": "alarm",
    "Alarm": "alarm",
    "Fire_alarm": "alarm",
    "Smoke_detector_and_smoke_alarm": "alarm",
    "Alarm_clock": "alarm",
    "Buzzer": "alarm",
    "Car_alarm": "alarm",
    "Vehicle_horn_and_car_horn_and_honking": "traffic",
    "Baby_cry_and_infant_cry": "baby_cry",
    "Music": "media",
}
_FSD50K_V17_ENGINES: dict[str, str] = {
    name: "traffic"
    for name in (
        "Car",
        "Truck",
        "Bus",
        "Motorcycle",
        "Engine",
        "Engine_starting",
        "Motor_vehicle_(road)",
        "Traffic_noise_and_roadway_noise",
        "Race_car_and_auto_racing",
        "Car_passing_by",
    )
}
FSD50K_TARGETS: dict[str, dict[str, str]] = {
    "v1.7.0": {**_FSD50K_COMMON, **_FSD50K_V17_ENGINES},
    "v1.8.0": dict(_FSD50K_COMMON),
}


def fsd50k_licence_allowed(licence_url: str) -> bool:
    """True for CC0 and CC BY. False for CC BY-NC, CC Sampling+ and anything else."""
    url = (licence_url or "").lower()
    if "/by-nc" in url or "sampling" in url:
        return False
    return any(marker in url for marker in FSD50K_ALLOWED_LICENCE_MARKERS)


def fsd50k_specs(
    ground_truth_rows: list[dict[str, str]],
    clips_info: dict[str, dict],
    vocabulary: set[str],
) -> tuple[list[ClipSpec], dict]:
    """Clip specs for FSD50K eval, plus a note of what was filtered and matched.

    ``ground_truth_rows`` come from ``FSD50K.ground_truth/eval.csv``
    (columns ``fname`` and ``labels``). ``clips_info`` is
    ``eval_clips_info_FSD50K.json``. ``vocabulary`` is the set of label names
    in ``vocabulary.csv``.
    """
    specs: list[ClipSpec] = []
    dropped: dict[str, int] = {}
    for row in sorted(ground_truth_rows, key=lambda item: int(item["fname"])):
        fname = str(row["fname"])
        licence = str(clips_info.get(fname, {}).get("license", ""))
        if not fsd50k_licence_allowed(licence):
            dropped[licence or "unknown"] = dropped.get(licence or "unknown", 0) + 1
            continue
        labels = tuple(label for label in row["labels"].split(",") if label)
        specs.append(_spec(fname, f"{fname}.wav", labels, (), FSD50K_TARGETS))
    wanted = set(FSD50K_TARGETS["v1.7.0"]) | set(FSD50K_TARGETS["v1.8.0"])
    notes = {
        "clips_kept": len(specs),
        "clips_dropped_by_licence": dict(sorted(dropped.items())),
        "labels_found_in_vocabulary": sorted(wanted & vocabulary),
        "labels_not_in_vocabulary": sorted(wanted - vocabulary),
    }
    return specs, notes


def load_fsd50k(root: Path) -> tuple[list[ClipSpec], dict]:
    """Read FSD50K metadata from *root* (holds FSD50K.ground_truth and FSD50K.metadata)."""
    with open(root / "FSD50K.ground_truth" / "eval.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    with open(root / "FSD50K.metadata" / "eval_clips_info_FSD50K.json", encoding="utf-8") as fh:
        clips_info = json.load(fh)
    with open(root / "FSD50K.ground_truth" / "vocabulary.csv", newline="", encoding="utf-8") as fh:
        vocabulary = {row[1] for row in csv.reader(fh) if len(row) > 1}
    return fsd50k_specs(rows, clips_info, vocabulary)


# ---------------------------------------------------------------------------
# SONYC-UST v2.3.0
# ---------------------------------------------------------------------------

SONYC_LICENCE = "CC BY 4.0 (audio not redistributed)"

# Fine-grained SONYC tags -> short names used here.
_SONYC_TAGS: dict[str, str] = {
    "car-horn": "car_horn",
    "reverse-beeper": "reverse_beeper",
    "siren": "siren",
    "car-alarm": "car_alarm",
}
_SONYC_COARSE: dict[str, str] = {
    "engine": "engine",
    "alert-signal": "alert_signal",
    "human-voice": "human_voice",
    "dog": "dog",
    "music": "music",
}
SONYC_TARGETS: dict[str, dict[str, str]] = {
    "v1.7.0": {
        "car_horn": "traffic",
        "reverse_beeper": "traffic",
        "siren": "alarm",
        "car_alarm": "alarm",
        "engine_only": "traffic",  # v1.7.0 fired traffic on engines by design
    },
    "v1.8.0": {
        "car_horn": "traffic",
        "reverse_beeper": "traffic",
        "siren": "alarm",
        "car_alarm": "alarm",
    },
}


def _sonyc_column(fieldnames: list[str], name: str, *, coarse: bool) -> str | None:
    """Find the presence column for a fine tag (``5-1_car-horn_presence``) or a
    coarse class (``5_alert-signal_presence``)."""
    for column in fieldnames:
        if not column.endswith("_presence"):
            continue
        prefix, _, rest = column.partition("_")
        if rest != f"{name}_presence":
            continue
        if coarse == ("-" not in prefix):
            return column
    return None


def sonyc_specs(rows: list[dict[str, str]], fieldnames: list[str]) -> tuple[list[ClipSpec], dict]:
    """Clip specs from SONYC-UST ``annotations.csv`` rows.

    Only verified ground-truth rows (``annotator_id`` 0) are used. A clip is:

    * a traffic target when car-horn or reverse-beeper is present,
    * an alarm target when siren or car-alarm is present,
    * ``engine_only`` when an engine is present and no alert signal, human
      voice, dog or music is tagged. Under v1.8.0 these are the negatives: real
      street audio where the wristband should stay quiet.

    Every other clip is left out, because the tags cannot say what should fire.
    """
    columns = {short: _sonyc_column(fieldnames, tag, coarse=False) for tag, short in _SONYC_TAGS.items()}
    columns.update(
        {short: _sonyc_column(fieldnames, tag, coarse=True) for tag, short in _SONYC_COARSE.items()}
    )
    missing = sorted(short for short, column in columns.items() if column is None)

    def present(row: dict[str, str], short: str) -> bool:
        column = columns.get(short)
        if column is None:
            return False
        try:
            return float(row.get(column, "0") or 0) == 1.0
        except ValueError:
            return False

    specs: list[ClipSpec] = []
    seen: set[str] = set()
    verified = 0
    left_out = 0
    for row in sorted(rows, key=lambda item: item["audio_filename"]):
        if str(row.get("annotator_id", "")).strip() != "0":
            continue
        filename = row["audio_filename"]
        if filename in seen:
            continue
        seen.add(filename)
        verified += 1
        tags = tuple(short for short in _SONYC_TAGS.values() if present(row, short))
        engine_only = (
            present(row, "engine")
            and not present(row, "alert_signal")
            and not present(row, "human_voice")
            and not present(row, "dog")
            and not present(row, "music")
        )
        labels = tags + (("engine_only",) if engine_only and not tags else ())
        if not labels:
            left_out += 1
            continue
        specs.append(
            _spec(filename, filename, labels, labels, SONYC_TARGETS, eligible_negative=engine_only)
        )
    notes = {
        "verified_recordings": verified,
        "clips_kept": len(specs),
        "clips_left_out_no_usable_tag": left_out,
        "columns_used": {short: column for short, column in sorted(columns.items()) if column},
        "columns_missing": missing,
    }
    return specs, notes


def load_sonyc(root: Path) -> tuple[list[ClipSpec], dict]:
    with open(root / "annotations.csv", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    return sonyc_specs(rows, fieldnames)


# ---------------------------------------------------------------------------
# Audio access
# ---------------------------------------------------------------------------


def iter_audio(
    specs: list[ClipSpec], *, audio_dir: Path | None = None, audio_zip: Path | None = None
) -> Iterator[tuple[ClipSpec, object, int]]:
    """Yield (spec, samples, sample_rate). Missing files are skipped.

    Reads from a directory, or straight out of a zip archive without
    extracting it. ``soundfile`` is imported lazily so tests do not need it.
    """
    import soundfile as sf

    if audio_zip is not None:
        with zipfile.ZipFile(audio_zip) as archive:
            members = {Path(name).name: name for name in archive.namelist()}
            for spec in specs:
                member = members.get(Path(spec.path).name)
                if member is None:
                    continue
                samples, rate = sf.read(io.BytesIO(archive.read(member)), dtype="float32")
                yield spec, samples, rate
        return
    assert audio_dir is not None
    for spec in specs:
        path = audio_dir / spec.path
        if not path.exists():
            continue
        samples, rate = sf.read(str(path), dtype="float32")
        yield spec, samples, rate


def keep_needed_files(needed: set[str], source: Path, destination: Path) -> int:
    """Move files named in *needed* from anywhere under *source* into *destination*."""
    destination.mkdir(parents=True, exist_ok=True)
    moved = 0
    for path in source.rglob("*"):
        if path.is_file() and path.name in needed:
            path.replace(destination / path.name)
            moved += 1
    return moved


def main(argv: list[str] | None = None) -> int:
    """``sonyc-keep``: after unpacking one SONYC archive, keep only the clips the bench uses."""
    import argparse

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("command", choices=("sonyc-keep", "sonyc-summary"))
    parser.add_argument("--data", required=True, help="Directory holding annotations.csv")
    parser.add_argument("--source", help="Directory an archive was unpacked into")
    parser.add_argument("--audio-dir", help="Where to keep the needed clips")
    args = parser.parse_args(argv)

    specs, notes = load_sonyc(Path(args.data))
    if args.command == "sonyc-summary":
        print(json.dumps(notes, indent=2, sort_keys=True))
        return 0
    moved = keep_needed_files({spec.path for spec in specs}, Path(args.source), Path(args.audio_dir))
    print(f"kept {moved} of {len(specs)} needed clips from {args.source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
