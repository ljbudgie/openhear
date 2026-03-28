"""
export.py – audiogram export functions for OpenHear.

Converts sovereign audiogram data into portable formats: CSV for
spreadsheets, Markdown for documentation, and DSP config dicts that map
directly to the parameters in dsp/config.py.

Your data, your format, your choice.

Usage:
    from audiogram.export import to_csv, to_markdown, to_dsp_config

    to_csv("audiogram/data/burgess_2021.json", "burgess_2021.csv")
    print(to_markdown("audiogram/data/burgess_2021.json"))
    config = to_dsp_config("audiogram/data/burgess_2021.json", "right")
"""

import csv
import io

from audiogram.loader import (
    get_gain_profile,
    get_pta,
    get_severity,
    get_thresholds,
    load_audiogram,
)


def to_csv(path: str, output: str) -> None:
    """Export audiogram thresholds to a flat CSV file.

    Produces one row per frequency per ear with columns:
    ``ear, freq_hz, db_hl``.

    Args:
        path:   Path to an audiogram JSON file.
        output: Path where the CSV file will be written.
    """
    audiogram = load_audiogram(path)

    with open(output, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ear", "freq_hz", "db_hl"])
        for ear in ("right", "left"):
            for freq, db in get_thresholds(audiogram, ear):
                writer.writerow([ear, freq, db])


def to_markdown(path: str) -> str:
    """Generate a Markdown table from an audiogram file.

    Includes a threshold table for each ear, followed by PTA and severity
    classification.

    Args:
        path: Path to an audiogram JSON file.

    Returns:
        A Markdown-formatted string.
    """
    audiogram = load_audiogram(path)
    lines: list[str] = []

    # Header
    lines.append(f"# Audiogram — {audiogram['subject']}")
    lines.append("")
    lines.append(f"**Source:** {audiogram['source']}  ")
    lines.append(f"**Date:** {audiogram['date']}  ")
    if audiogram.get("notes"):
        lines.append(f"**Notes:** {audiogram['notes']}  ")
    lines.append("")

    # Threshold tables
    for ear in ("right", "left"):
        label = "Right Ear (O)" if ear == "right" else "Left Ear (X)"
        lines.append(f"## {label}")
        lines.append("")
        lines.append("| Frequency (Hz) | Threshold (dB HL) | Severity |")
        lines.append("|---------------:|---------:|----------|")
        for freq, db in get_thresholds(audiogram, ear):
            lines.append(f"| {freq} | {db} | {get_severity(db)} |")
        lines.append("")

        try:
            pta = get_pta(audiogram, ear)
            lines.append(f"**PTA:** {pta:.1f} dB HL ({get_severity(int(pta))})")
        except ValueError:
            lines.append("**PTA:** insufficient frequencies")
        lines.append("")

    return "\n".join(lines)


def to_dsp_config(path: str, ear: str) -> dict:
    """Generate DSP configuration parameters from an audiogram.

    Produces a dict of parameters that map to the constants in
    ``dsp/config.py``.  This is the bridge between your clinical audiogram
    and real-time audio processing.

    The output includes:
    - Per-frequency gain profile (what the equaliser should apply).
    - Suggested compression ratios per frequency band (derived from
      threshold severity — more loss means more compression).
    - Noise floor and voice boost settings scaled to the hearing profile.

    Args:
        path: Path to an audiogram JSON file.
        ear:  ``"right"`` or ``"left"``.

    Returns:
        Dict with keys::

            {
                "gain_profile":       [(freq, gain_db), ...],
                "compression_bands":  [(freq, ratio), ...],
                "compression_knee_dbfs": float,
                "noise_floor_multiplier": float,
                "voice_clarity_gain":    float,
                "voice_clarity_low_hz":  float,
                "voice_clarity_high_hz": float,
                "pta":                   float,
                "severity":              str,
            }
    """
    audiogram = load_audiogram(path)
    gain_profile = get_gain_profile(audiogram, ear)
    pta = get_pta(audiogram, ear)
    severity = get_severity(int(pta))

    # ── Compression ratios per frequency band ────────────────────────────────
    # Higher threshold (more loss) → higher compression ratio to keep loud
    # sounds comfortable while making soft sounds audible.
    compression_bands: list[tuple[int, float]] = []
    for freq, gain in gain_profile:
        if gain <= 10:
            ratio = 1.2
        elif gain <= 25:
            ratio = 1.5
        elif gain <= 40:
            ratio = 2.0
        elif gain <= 55:
            ratio = 2.5
        elif gain <= 70:
            ratio = 3.0
        else:
            ratio = 3.5
        compression_bands.append((freq, ratio))

    # ── Compression knee point ───────────────────────────────────────────────
    # With more hearing loss, the knee point should be lower (more negative)
    # to start compressing earlier.
    if pta <= 40:
        knee = -35.0
    elif pta <= 55:
        knee = -40.0
    elif pta <= 70:
        knee = -45.0
    else:
        knee = -50.0

    # ── Noise floor multiplier ───────────────────────────────────────────────
    # More hearing loss → more aggressive noise reduction (higher multiplier)
    # to compensate for reduced ability to separate speech from noise.
    if pta <= 40:
        noise_mult = 1.1
    elif pta <= 55:
        noise_mult = 1.2
    elif pta <= 70:
        noise_mult = 1.3
    else:
        noise_mult = 1.4

    # ── Voice clarity parameters ─────────────────────────────────────────────
    # Scale the voice boost with hearing loss severity.  The speech-critical
    # range stays at 1000–4000 Hz.
    if pta <= 40:
        voice_gain = 1.4
    elif pta <= 55:
        voice_gain = 1.6
    elif pta <= 70:
        voice_gain = 1.8
    else:
        voice_gain = 2.0

    return {
        "gain_profile": gain_profile,
        "compression_bands": compression_bands,
        "compression_knee_dbfs": knee,
        "noise_floor_multiplier": noise_mult,
        "voice_clarity_gain": voice_gain,
        "voice_clarity_low_hz": 1000.0,
        "voice_clarity_high_hz": 4000.0,
        "pta": pta,
        "severity": severity,
    }
