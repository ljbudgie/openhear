"""
mpo_calculator.py – Maximum Power Output calculator for OpenHear hardware.

Takes an audiogram JSON file and computes safe MPO limits per frequency,
recommended zener diode voltages, and series resistor values for the
hardware MPO limiter circuit.

The hardware limiter is a passive zener diode clamp that caps the
electrical signal to the receiver regardless of what the software does.
It is the final safety layer and cannot be overridden by software.

Usage:
    python -m hardware.safety.mpo_calculator audiogram/data/burgess_2021.json

    # Specify ear and custom safety margin:
    python -m hardware.safety.mpo_calculator audiogram.json --ear left --margin 10

Your hearing is irreplaceable.  When in doubt, use a lower MPO.
"""

import argparse
import math
import sys
from typing import Any

from audiogram.loader import (
    get_thresholds,
    get_pta,
    get_severity,
    load_audiogram,
)


# ── Constants ────────────────────────────────────────────────────────────────

# Receiver sensitivity: approximate dB SPL per volt for Knowles BA receivers.
# This is used to convert a target SPL to a zener clamping voltage.
# Actual values depend on the specific receiver model and ear canal volume.
# Calibration is ALWAYS required after building the circuit.
_RECEIVER_SENSITIVITY_DB_SPL_PER_VOLT: float = 95.0  # dB SPL at 1 Vrms (typical BA receiver in 2cc coupler)

# Standard series resistor value (ohms).
_SERIES_RESISTOR_OHMS: int = 100

# Absolute maximum MPO regardless of hearing loss (dB SPL).
_ABSOLUTE_MAX_MPO_DB: float = 120.0

# Minimum useful MPO (below this, the aid provides negligible benefit).
_MINIMUM_MPO_DB: float = 85.0

# Standard audiometric frequencies for MPO calculation.
_STANDARD_FREQS: list[int] = [250, 500, 1000, 2000, 3000, 4000, 6000, 8000]


# ── Core Functions ───────────────────────────────────────────────────────────


def calculate_mpo(
    audiogram_path: str,
    ear: str = "right",
    safety_margin_db: int = 5,
) -> dict[str, Any]:
    """Calculate recommended MPO limits and hardware limiter component values.

    For each audiometric frequency:
    - Estimates the Uncomfortable Loudness Level (UCL) from the threshold
    - UCL = min(threshold + 10, 100) as a conservative estimate
    - For profound loss (threshold > 90 dB), caps UCL at 120 dB SPL
    - Subtracts the safety margin to get the target MPO
    - Computes the zener voltage needed to clamp at that MPO
    - Recommends the series resistor value

    Args:
        audiogram_path: Path to openhear-audiogram-v1 JSON file.
        ear: Which ear to calculate for ('right' or 'left').
        safety_margin_db: Safety margin in dB subtracted from estimated UCL.
            Default is 5 dB.  Higher values are more conservative (safer).

    Returns:
        Dict with keys:
            - ear: str
            - safety_margin_db: int
            - pta: float
            - severity: str
            - frequencies: list of dicts with per-frequency data:
                - freq_hz: int
                - threshold_db: int
                - estimated_ucl_db: float
                - recommended_mpo_db: float
                - zener_voltage: float
                - series_resistor_ohms: int
                - expected_clamping_spl: float
    """
    audiogram = load_audiogram(audiogram_path)
    thresholds = get_thresholds(audiogram, ear)
    pta = get_pta(audiogram, ear)
    severity = get_severity(int(pta))

    # Build a lookup dict for thresholds
    threshold_dict: dict[int, int] = dict(thresholds)

    freq_results: list[dict[str, Any]] = []

    for freq in _STANDARD_FREQS:
        if freq not in threshold_dict:
            continue

        threshold = threshold_dict[freq]

        # Estimate UCL: threshold + 10 or 100 dB SPL, whichever is LOWER
        # This is conservative — real UCL testing would be more accurate
        ucl_estimate = min(float(threshold + 10), 100.0)

        # For profound loss (>90 dB threshold), allow higher UCL but cap
        # at absolute maximum
        if threshold > 90:
            ucl_estimate = min(float(threshold + 10), _ABSOLUTE_MAX_MPO_DB)

        # Apply safety margin
        mpo = ucl_estimate - safety_margin_db

        # Floor at minimum useful MPO
        mpo = max(mpo, _MINIMUM_MPO_DB)

        # Cap at absolute maximum
        mpo = min(mpo, _ABSOLUTE_MAX_MPO_DB)

        # Compute zener voltage from target MPO
        # Using: SPL = sensitivity_per_volt + 20*log10(V_zener)
        # Therefore: V_zener = 10^((target_SPL - sensitivity) / 20)
        voltage_ratio = (mpo - _RECEIVER_SENSITIVITY_DB_SPL_PER_VOLT) / 20.0
        zener_voltage = math.pow(10, voltage_ratio)

        # Round to nearest standard zener voltage
        zener_voltage = _nearest_standard_zener(zener_voltage)

        # Recalculate actual clamping SPL from the standard zener voltage
        if zener_voltage > 0:
            actual_spl = _RECEIVER_SENSITIVITY_DB_SPL_PER_VOLT + 20.0 * math.log10(
                zener_voltage
            )
        else:
            actual_spl = _MINIMUM_MPO_DB

        freq_results.append({
            "freq_hz": freq,
            "threshold_db": threshold,
            "estimated_ucl_db": round(ucl_estimate, 1),
            "recommended_mpo_db": round(mpo, 1),
            "zener_voltage": zener_voltage,
            "series_resistor_ohms": _SERIES_RESISTOR_OHMS,
            "expected_clamping_spl": round(actual_spl, 1),
        })

    return {
        "ear": ear,
        "safety_margin_db": safety_margin_db,
        "pta": pta,
        "severity": severity,
        "frequencies": freq_results,
    }


def _nearest_standard_zener(voltage: float) -> float:
    """Find the nearest standard zener diode voltage.

    Standard zener voltages from the E24 series commonly available
    from electronics suppliers.

    Args:
        voltage: Target voltage in volts.

    Returns:
        Nearest standard zener voltage.
    """
    standard_voltages: list[float] = [
        0.47, 0.51, 0.56, 0.62, 0.68, 0.75, 0.82, 0.91,
        1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4,
        2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2,
        6.8, 7.5, 8.2, 9.1, 10.0, 11.0, 12.0, 13.0, 15.0,
        16.0, 18.0, 20.0, 22.0, 24.0, 27.0, 30.0, 33.0, 36.0,
    ]

    # Find the nearest standard voltage that does not exceed the target
    # (always round down for safety — lower voltage = lower MPO = safer)
    candidates = [v for v in standard_voltages if v <= voltage]
    if not candidates:
        return standard_voltages[0]  # Lowest available
    return candidates[-1]


def print_mpo_table(audiogram_path: str, ear: str = "right") -> None:
    """Print a formatted MPO table for the given audiogram.

    Args:
        audiogram_path: Path to openhear-audiogram-v1 JSON file.
        ear: Which ear to calculate for ('right' or 'left').
    """
    result = calculate_mpo(audiogram_path, ear=ear)

    print("\n" + "=" * 72)
    print("  OpenHear MPO Calculator — Hardware Limiter Component Values")
    print("=" * 72)
    print(f"\n  Ear:            {result['ear'].capitalize()}")
    print(f"  PTA:            {result['pta']:.1f} dB HL ({result['severity']})")
    print(f"  Safety margin:  {result['safety_margin_db']} dB")

    print("\n  " + "-" * 68)
    print(
        f"  {'Freq':>6}  {'Thresh':>8}  {'Est UCL':>8}  "
        f"{'Rec MPO':>8}  {'Zener V':>8}  {'R (Ω)':>6}  {'Clamp SPL':>10}"
    )
    print("  " + "-" * 68)

    for f in result["frequencies"]:
        print(
            f"  {f['freq_hz']:>5} Hz  {f['threshold_db']:>5} dB  "
            f"{f['estimated_ucl_db']:>6.1f} dB  {f['recommended_mpo_db']:>6.1f} dB  "
            f"{f['zener_voltage']:>6.2f} V  {f['series_resistor_ohms']:>5}  "
            f"{f['expected_clamping_spl']:>7.1f} dB SPL"
        )

    print("\n  " + "-" * 68)
    print("\n  Notes:")
    print("  - Zener voltage rounded DOWN to nearest standard value (safer)")
    print("  - Use back-to-back zener pair (anode-to-anode) for bipolar clamping")
    print(f"  - Series resistor: {_SERIES_RESISTOR_OHMS} Ω (1/4W minimum)")
    print("  - ALWAYS calibrate after building — these are starting values")
    print("  - If measured SPL exceeds target: use LOWER zener voltage")
    print("  - Receiver sensitivity assumed: "
          f"{_RECEIVER_SENSITIVITY_DB_SPL_PER_VOLT:.0f} dB SPL/Vrms")
    print("=" * 72)
    print()


# ── CLI Entry Point ──────────────────────────────────────────────────────────


def main() -> None:
    """Command-line entry point for the MPO calculator."""
    parser = argparse.ArgumentParser(
        description=(
            "Calculate recommended MPO limits and hardware limiter "
            "component values from an OpenHear audiogram."
        ),
        epilog="Your hearing is irreplaceable.  When in doubt, use a lower MPO.",
    )
    parser.add_argument(
        "audiogram",
        help="Path to openhear-audiogram-v1 JSON audiogram file",
    )
    parser.add_argument(
        "--ear",
        choices=["right", "left"],
        default="right",
        help="Which ear to calculate for (default: right)",
    )
    parser.add_argument(
        "--margin",
        type=int,
        default=5,
        help="Safety margin in dB (default: 5).  Higher = more conservative",
    )

    args = parser.parse_args()

    # Calculate and print
    print_mpo_table(args.audiogram, ear=args.ear)


if __name__ == "__main__":
    main()
