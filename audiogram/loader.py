"""
loader.py – audiogram data loader and analysis for OpenHear.

Reads audiogram JSON files in the openhear-audiogram-v1 format, validates
them, and provides functions to extract thresholds, compute the pure tone
average (PTA), classify severity, generate a gain profile for the DSP
pipeline, and compare audiograms over time.

Your audiogram is a measurement of your auditory nerve response.  This
module treats it as sovereign data: load it, analyse it, and feed it
directly into the processing pipeline — no intermediary required.

Usage:
    from audiogram.loader import load_audiogram, get_pta, get_gain_profile

    ag = load_audiogram("audiogram/data/burgess_2021.json")
    print(get_pta(ag, "right"))
    print(get_gain_profile(ag, "right"))
"""

import json
from typing import Optional

# Frequencies used for the standard Pure Tone Average calculation.
_PTA_FREQUENCIES = {500, 1000, 2000, 4000}

# Normal hearing threshold — the target for gain compensation.
_NORMAL_THRESHOLD_DB = 20

# Required top-level fields in an openhear-audiogram-v1 file.
_REQUIRED_FIELDS = {"subject", "source", "date", "format_version", "right_ear", "left_ear"}


def load_audiogram(path: str) -> dict:
    """Read and validate an audiogram JSON file.

    Args:
        path: Path to a JSON file in openhear-audiogram-v1 format.

    Returns:
        The parsed audiogram dict.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If required fields are missing or the format version
            is not recognised.
    """
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    missing = _REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(
            f"Audiogram file is missing required fields: {', '.join(sorted(missing))}"
        )

    if data.get("format_version") != "openhear-audiogram-v1":
        raise ValueError(
            f"Unsupported format version: {data.get('format_version')!r}.  "
            "Expected 'openhear-audiogram-v1'."
        )

    for ear_key in ("right_ear", "left_ear"):
        ear = data[ear_key]
        if "thresholds" not in ear:
            raise ValueError(f"'{ear_key}' is missing the 'thresholds' array.")
        for entry in ear["thresholds"]:
            if "freq_hz" not in entry or "db_hl" not in entry:
                raise ValueError(
                    f"Each threshold entry in '{ear_key}' must have "
                    "'freq_hz' and 'db_hl' fields."
                )

    return data


def get_thresholds(audiogram: dict, ear: str) -> list[tuple[int, int]]:
    """Extract (frequency, dB HL) pairs for the specified ear.

    Args:
        audiogram: A validated audiogram dict (from :func:`load_audiogram`).
        ear:       ``"right"`` or ``"left"``.

    Returns:
        Sorted list of ``(freq_hz, db_hl)`` tuples.

    Raises:
        ValueError: If *ear* is not ``"right"`` or ``"left"``.
    """
    ear_key = _resolve_ear_key(ear)
    thresholds = audiogram[ear_key]["thresholds"]
    return sorted(
        (int(t["freq_hz"]), int(t["db_hl"])) for t in thresholds
    )


def get_pta(audiogram: dict, ear: str) -> float:
    """Compute the Pure Tone Average for the specified ear.

    The PTA is the arithmetic mean of thresholds at 500, 1000, 2000, and
    4000 Hz — the four frequencies most important for speech understanding.

    Args:
        audiogram: A validated audiogram dict.
        ear:       ``"right"`` or ``"left"``.

    Returns:
        PTA in dB HL, rounded to one decimal place.

    Raises:
        ValueError: If the audiogram does not contain all four PTA
            frequencies for the specified ear.
    """
    thresholds = dict(get_thresholds(audiogram, ear))
    missing = _PTA_FREQUENCIES - set(thresholds.keys())
    if missing:
        raise ValueError(
            f"Cannot compute PTA: missing thresholds at "
            f"{', '.join(str(f) for f in sorted(missing))} Hz."
        )
    pta_values = [thresholds[f] for f in sorted(_PTA_FREQUENCIES)]
    return round(sum(pta_values) / len(pta_values), 1)


def get_severity(db: int) -> str:
    """Classify hearing loss severity from a dB HL value.

    Uses the standard clinical classification:

    ========== ==================
    dB HL      Severity
    ========== ==================
    0–25       normal
    26–40      mild
    41–55      moderate
    56–70      moderately-severe
    71–90      severe
    91+        profound
    ========== ==================

    Args:
        db: A threshold or PTA value in dB HL.

    Returns:
        One of ``"normal"``, ``"mild"``, ``"moderate"``,
        ``"moderately-severe"``, ``"severe"``, or ``"profound"``.
    """
    if db <= 25:
        return "normal"
    if db <= 40:
        return "mild"
    if db <= 55:
        return "moderate"
    if db <= 70:
        return "moderately-severe"
    if db <= 90:
        return "severe"
    return "profound"


def get_gain_profile(audiogram: dict, ear: str) -> list[tuple[int, int]]:
    """Compute the gain needed at each frequency to reach normal hearing.

    For every tested frequency, the gain is the difference between the
    measured threshold and the normal hearing target (20 dB HL).  This is
    the bridge between clinical measurement and real-time DSP processing:
    feed this directly into the equaliser stage of the pipeline.

    If the threshold is already at or below 20 dB HL, the gain is 0 (no
    amplification needed at that frequency).

    Args:
        audiogram: A validated audiogram dict.
        ear:       ``"right"`` or ``"left"``.

    Returns:
        Sorted list of ``(freq_hz, gain_db)`` tuples.
    """
    thresholds = get_thresholds(audiogram, ear)
    return [
        (freq, max(0, db - _NORMAL_THRESHOLD_DB))
        for freq, db in thresholds
    ]


def compare_audiograms(path_a: str, path_b: str) -> dict:
    """Compare two audiograms and show threshold differences per ear.

    Useful for longitudinal tracking — see how your hearing has changed
    between two tests.  A positive difference means the threshold in
    audiogram B is higher (worse) than in A at that frequency.

    Args:
        path_a: Path to the first (earlier) audiogram JSON file.
        path_b: Path to the second (later) audiogram JSON file.

    Returns:
        Dict with structure::

            {
                "right": [(freq, diff), ...],
                "left":  [(freq, diff), ...],
                "right_pta_diff": float,
                "left_pta_diff":  float,
            }

        Where *diff* = threshold_b − threshold_a at each frequency
        present in both audiograms.
    """
    ag_a = load_audiogram(path_a)
    ag_b = load_audiogram(path_b)

    result: dict = {}
    for ear in ("right", "left"):
        thresh_a = dict(get_thresholds(ag_a, ear))
        thresh_b = dict(get_thresholds(ag_b, ear))
        common_freqs = sorted(set(thresh_a.keys()) & set(thresh_b.keys()))
        result[ear] = [
            (freq, thresh_b[freq] - thresh_a[freq]) for freq in common_freqs
        ]

        pta_a: Optional[float] = None
        pta_b: Optional[float] = None
        try:
            pta_a = get_pta(ag_a, ear)
        except ValueError:
            pass
        try:
            pta_b = get_pta(ag_b, ear)
        except ValueError:
            pass

        if pta_a is not None and pta_b is not None:
            result[f"{ear}_pta_diff"] = round(pta_b - pta_a, 1)
        else:
            result[f"{ear}_pta_diff"] = None

    return result


# ── Internal helpers ──────────────────────────────────────────────────────────


def _resolve_ear_key(ear: str) -> str:
    """Map 'right'/'left' to the JSON key 'right_ear'/'left_ear'.

    Raises:
        ValueError: If *ear* is not ``"right"`` or ``"left"``.
    """
    ear = ear.lower().strip()
    if ear == "right":
        return "right_ear"
    if ear == "left":
        return "left_ear"
    raise ValueError(f"ear must be 'right' or 'left', got {ear!r}")
