"""
audiogram_to_tympan.py – Bridge from OpenHear audiogram to Tympan Arduino sketch.

Reads an openhear-audiogram-v1 JSON audiogram file, computes per-frequency
gain profiles and DSP parameters using the audiogram module, and generates
a complete Tympan Arduino .ino sketch ready to compile and upload.

The generated sketch configures 8-band WDRC compression, noise reduction,
feedback cancellation, and MPO limiting — all tuned to the user's audiogram.

Usage:
    # Single ear (right ear by default):
    python -m hardware.tympan.audiogram_to_tympan audiogram.json output.ino

    # Binaural (both ears):
    python -m hardware.tympan.audiogram_to_tympan audiogram.json output.ino --binaural

    # Left ear only:
    python -m hardware.tympan.audiogram_to_tympan audiogram.json output.ino --ear left

Your audiogram, your gain profile, your hardware.
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from audiogram.loader import (
    get_gain_profile,
    get_pta,
    get_severity,
    get_thresholds,
    load_audiogram,
)
from audiogram.export import to_dsp_config


# ── Constants ────────────────────────────────────────────────────────────────

# Standard 8-band crossover frequencies for Tympan WDRC.
# These divide the audio spectrum into 8 bands at standard audiometric
# boundaries.  The Tympan filterbank uses these as crossover points.
_TYMPAN_CROSSOVER_FREQS: list[float] = [
    250.0, 500.0, 1000.0, 2000.0, 3000.0, 4000.0, 6000.0,
]

# Centre frequencies for each of the 8 bands (for display and mapping).
_TYMPAN_BAND_CENTRES: list[int] = [
    125, 375, 750, 1500, 2500, 3500, 5000, 7000,
]

# Standard audiometric test frequencies that we map from.
_AUDIOMETRIC_FREQS: list[int] = [
    125, 250, 500, 1000, 1500, 2000, 3000, 4000, 6000, 8000,
]

# Maximum gain ceiling per band (safety limit).
# Even if the audiogram calls for more gain, the software will cap here.
_MAX_GAIN_CEILING: list[float] = [
    50.0, 50.0, 55.0, 55.0, 55.0, 60.0, 60.0, 60.0,
]

# Path to the Arduino template sketch.
_TEMPLATE_PATH: str = os.path.join(
    os.path.dirname(__file__), "templates", "basic_openhear.ino",
)


# ── Helper Functions ─────────────────────────────────────────────────────────


def _interpolate_to_bands(
    thresholds: list[tuple[int, int]],
    band_centres: list[int],
) -> list[float]:
    """Interpolate audiometric thresholds to Tympan band centre frequencies.

    The audiogram may have thresholds at different frequencies than the
    Tympan's 8 bands.  This function interpolates (or extrapolates at
    edges) to get a value at each band centre.

    Args:
        thresholds: Sorted list of (freq_hz, db_hl) tuples from audiogram.
        band_centres: Target frequencies for interpolation.

    Returns:
        List of interpolated dB HL values, one per band centre.
    """
    freqs = np.array([t[0] for t in thresholds], dtype=float)
    values = np.array([t[1] for t in thresholds], dtype=float)
    centres = np.array(band_centres, dtype=float)
    interpolated = np.interp(centres, freqs, values)
    return [float(round(v, 1)) for v in interpolated]


def _compute_gain_per_band(
    thresholds: list[tuple[int, int]],
    band_centres: list[int],
) -> list[float]:
    """Compute gain needed per Tympan band from audiometric thresholds.

    Gain formula: max(0, threshold_db - 20).  Same as
    audiogram.loader.get_gain_profile() but interpolated to band centres.

    Args:
        thresholds: Sorted list of (freq_hz, db_hl) tuples.
        band_centres: Target band centre frequencies.

    Returns:
        List of gain values in dB, one per band.
    """
    normal_threshold: int = 20
    interpolated_thresholds = _interpolate_to_bands(thresholds, band_centres)
    return [max(0.0, t - normal_threshold) for t in interpolated_thresholds]


def _compute_compression_ratios(gain_per_band: list[float]) -> list[float]:
    """Compute compression ratio per band from gain values.

    Higher gain (more hearing loss) → higher compression ratio.
    Uses the same mapping as audiogram.export.to_dsp_config().

    Args:
        gain_per_band: Gain in dB per band.

    Returns:
        List of compression ratios, one per band.
    """
    ratios: list[float] = []
    for gain in gain_per_band:
        if gain <= 10:
            ratios.append(1.2)
        elif gain <= 25:
            ratios.append(1.5)
        elif gain <= 40:
            ratios.append(2.0)
        elif gain <= 55:
            ratios.append(2.5)
        elif gain <= 70:
            ratios.append(3.0)
        else:
            ratios.append(3.5)
    return ratios


def _compute_mpo_per_band(
    thresholds: list[tuple[int, int]],
    band_centres: list[int],
    safety_margin_db: int = 5,
) -> list[float]:
    """Compute Maximum Power Output per band from thresholds.

    MPO = min(threshold + 10, 100) as a conservative estimate of
    Uncomfortable Loudness Level (UCL).  For profound loss (threshold
    > 90 dB), cap at 120 dB SPL absolute maximum.

    A safety margin is then subtracted for the software limiter (the
    hardware limiter provides the final protection).

    Args:
        thresholds: Sorted list of (freq_hz, db_hl) tuples.
        band_centres: Target band centre frequencies.
        safety_margin_db: Safety margin below estimated UCL for software
            limiter.  Hardware limiter is set at the full MPO.

    Returns:
        List of MPO values in dB SPL, one per band.
    """
    interpolated = _interpolate_to_bands(thresholds, band_centres)
    mpo_values: list[float] = []
    for threshold in interpolated:
        # Estimate UCL: threshold + 10 or 100 dB, whichever is lower
        ucl_estimate = min(threshold + 10, 100.0)
        # For profound loss, allow higher MPO but cap at 120 dB absolute max
        if threshold > 90:
            ucl_estimate = min(threshold + 10, 120.0)
        # Apply safety margin for software limiter
        mpo = ucl_estimate - safety_margin_db
        # Floor at 85 dB SPL (below this, the aid is not useful)
        mpo = max(mpo, 85.0)
        mpo_values.append(round(mpo, 1))
    return mpo_values


def _compute_knee_per_band(
    gain_per_band: list[float],
    pta: float,
) -> list[float]:
    """Compute compression knee point per band.

    The knee point determines at what input level compression starts.
    More hearing loss → lower knee point (compression starts at quieter
    sounds).  Uses PTA as the overall severity indicator.

    Args:
        gain_per_band: Gain in dB per band.
        pta: Pure Tone Average in dB HL.

    Returns:
        List of knee points in dB SPL, one per band.
    """
    if pta <= 40:
        base_knee = 45.0
    elif pta <= 55:
        base_knee = 40.0
    elif pta <= 70:
        base_knee = 35.0
    else:
        base_knee = 30.0
    return [base_knee] * len(gain_per_band)


def _format_float_array(values: list[float], decimals: int = 1) -> str:
    """Format a list of floats as a C array initialiser.

    Args:
        values: List of float values.
        decimals: Number of decimal places.

    Returns:
        String like '{1.0, 2.5, 3.0}'.
    """
    formatted = ", ".join(f"{v:.{decimals}f}" for v in values)
    return "{" + formatted + "}"


def _fill_template(
    template: str,
    replacements: dict[str, str],
) -> str:
    """Fill placeholder values in the Arduino template.

    Args:
        template: Template string with {{PLACEHOLDER}} markers.
        replacements: Dict mapping placeholder names to replacement values.

    Returns:
        Filled template string.
    """
    result = template
    for key, value in replacements.items():
        result = result.replace("{{" + key + "}}", value)
    return result


# ── Main Functions ───────────────────────────────────────────────────────────


def generate_tympan_sketch(
    audiogram_path: str,
    output_path: str,
    ear: str = "right",
) -> str:
    """Generate a Tympan Arduino sketch from an audiogram file.

    Reads the audiogram, computes gain profiles and DSP parameters,
    fills in the Arduino template, and writes the result to output_path.

    Args:
        audiogram_path: Path to openhear-audiogram-v1 JSON file.
        output_path: Path where the .ino file will be written.
        ear: Which ear to generate for ('right' or 'left').

    Returns:
        The generated sketch as a string.
    """
    # Load audiogram and compute parameters
    audiogram = load_audiogram(audiogram_path)
    thresholds = get_thresholds(audiogram, ear)
    gain_profile = get_gain_profile(audiogram, ear)
    dsp_config = to_dsp_config(audiogram_path, ear)
    pta = get_pta(audiogram, ear)
    severity = get_severity(int(pta))

    # Compute per-band parameters for 8-band Tympan WDRC
    gain_per_band = _compute_gain_per_band(thresholds, _TYMPAN_BAND_CENTRES)
    comp_ratios = _compute_compression_ratios(gain_per_band)
    mpo_per_band = _compute_mpo_per_band(thresholds, _TYMPAN_BAND_CENTRES)
    knee_per_band = _compute_knee_per_band(gain_per_band, pta)

    # Determine noise reduction level from PTA
    if pta <= 40:
        noise_level = 1.0
    elif pta <= 55:
        noise_level = 1.5
    elif pta <= 70:
        noise_level = 2.0
    else:
        noise_level = 2.5

    # Attack and release times (same for all bands)
    attack_ms = [5.0] * len(_TYMPAN_BAND_CENTRES)
    release_ms = [200.0] * len(_TYMPAN_BAND_CENTRES)

    # Read template
    template_path = Path(_TEMPLATE_PATH)
    template = template_path.read_text(encoding="utf-8")

    # Build replacements
    ear_desc = f"{ear.capitalize()} ear"
    source = audiogram.get("subject", "unknown")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    replacements: dict[str, str] = {
        "EAR_DESCRIPTION": ear_desc,
        "AUDIOGRAM_SOURCE": source,
        "GENERATION_DATE": now,
        "N_CHAN": str(len(_TYMPAN_BAND_CENTRES)),
        "CROSSOVER_FREQUENCIES": _format_float_array(_TYMPAN_CROSSOVER_FREQS),
        "GAIN_DB": _format_float_array(gain_per_band),
        "COMPRESSION_RATIOS": _format_float_array(comp_ratios),
        "KNEE_DBSPL": _format_float_array(knee_per_band),
        "MPO_DBSPL": _format_float_array(mpo_per_band),
        "ATTACK_MS": _format_float_array(attack_ms),
        "RELEASE_MS": _format_float_array(release_ms),
        "NOISE_REDUCTION_ENABLED": "true",
        "NOISE_REDUCTION_LEVEL": f"{noise_level:.1f}",
        "FEEDBACK_CANCELLATION_ENABLED": "true",
        "MAX_GAIN_CEILING": _format_float_array(_MAX_GAIN_CEILING),
    }

    sketch = _fill_template(template, replacements)

    # Write output
    output = Path(output_path)
    output.write_text(sketch, encoding="utf-8")

    # Print summary
    _print_summary(ear, thresholds, gain_per_band, comp_ratios, mpo_per_band,
                   pta, severity, noise_level, output_path)

    return sketch


def generate_binaural_sketch(
    audiogram_path: str,
    output_path: str,
) -> str:
    """Generate a binaural Tympan sketch for both ears.

    Generates the sketch using the ear with worse hearing (higher PTA)
    as the primary configuration.  Both ears receive the same processing
    because the Tympan Rev F processes a single stereo pair.

    For true independent binaural processing, two Tympan boards would
    be needed (one per ear).  This function generates a single sketch
    that uses the more conservative (worse ear) configuration to ensure
    both ears are adequately served.

    Args:
        audiogram_path: Path to openhear-audiogram-v1 JSON file.
        output_path: Path where the .ino file will be written.

    Returns:
        The generated sketch as a string.
    """
    audiogram = load_audiogram(audiogram_path)
    pta_right = get_pta(audiogram, "right")
    pta_left = get_pta(audiogram, "left")

    # Use the ear with worse hearing (higher PTA) as primary
    if pta_left > pta_right:
        primary_ear = "left"
    else:
        primary_ear = "right"

    print(f"\n  Binaural mode: using {primary_ear} ear (worse hearing) as primary")
    print(f"  Right PTA: {pta_right:.1f} dB HL | Left PTA: {pta_left:.1f} dB HL")

    return generate_tympan_sketch(audiogram_path, output_path, ear=primary_ear)


def _print_summary(
    ear: str,
    thresholds: list[tuple[int, int]],
    gain_per_band: list[float],
    comp_ratios: list[float],
    mpo_per_band: list[float],
    pta: float,
    severity: str,
    noise_level: float,
    output_path: str,
) -> None:
    """Print a human-readable summary of the generated configuration.

    Args:
        ear: Ear name ('right' or 'left').
        thresholds: Original audiometric thresholds.
        gain_per_band: Computed gain per Tympan band.
        comp_ratios: Compression ratio per band.
        mpo_per_band: MPO limit per band.
        pta: Pure Tone Average.
        severity: Severity classification string.
        noise_level: Noise reduction aggressiveness.
        output_path: Where the sketch was written.
    """
    print("\n" + "=" * 60)
    print("  OpenHear → Tympan Sketch Generator")
    print("=" * 60)
    print(f"\n  Ear:      {ear.capitalize()}")
    print(f"  PTA:      {pta:.1f} dB HL ({severity})")
    print(f"  Output:   {output_path}")

    print("\n  Audiogram Thresholds:")
    print("  " + "-" * 40)
    print(f"  {'Frequency':>12}  {'Threshold':>10}")
    print("  " + "-" * 40)
    for freq, db in thresholds:
        print(f"  {freq:>10} Hz  {db:>8} dB HL")

    print(f"\n  8-Band WDRC Configuration:")
    print("  " + "-" * 56)
    print(f"  {'Band':>6}  {'Gain':>8}  {'Ratio':>8}  {'MPO':>10}")
    print("  " + "-" * 56)
    for i, centre in enumerate(_TYMPAN_BAND_CENTRES):
        print(
            f"  {centre:>5} Hz  {gain_per_band[i]:>6.1f} dB  "
            f"{comp_ratios[i]:>6.1f}    {mpo_per_band[i]:>7.1f} dB SPL"
        )

    print(f"\n  Attack time:   5.0 ms (all bands)")
    print(f"  Release time:  200.0 ms (all bands)")
    print(f"  Noise reduction: {noise_level:.1f}")
    print(f"  Feedback cancellation: ON")
    print("=" * 60)
    print()


# ── CLI Entry Point ──────────────────────────────────────────────────────────


def main() -> None:
    """Command-line entry point for audiogram-to-Tympan sketch generation."""
    parser = argparse.ArgumentParser(
        description="Generate a Tympan Arduino sketch from an OpenHear audiogram.",
        epilog="Your audiogram, your gain profile, your hardware.",
    )
    parser.add_argument(
        "audiogram",
        help="Path to openhear-audiogram-v1 JSON audiogram file",
    )
    parser.add_argument(
        "output",
        help="Path for the generated .ino sketch file",
    )
    parser.add_argument(
        "--ear",
        choices=["right", "left"],
        default="right",
        help="Which ear to generate for (default: right). Ignored if --binaural is set",
    )
    parser.add_argument(
        "--binaural",
        action="store_true",
        help="Generate a binaural sketch using the worse ear as primary",
    )

    args = parser.parse_args()

    if args.binaural:
        generate_binaural_sketch(args.audiogram, args.output)
    else:
        generate_tympan_sketch(args.audiogram, args.output, ear=args.ear)


if __name__ == "__main__":
    main()
