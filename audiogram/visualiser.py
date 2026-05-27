"""
visualiser.py – terminal-based audiogram display for OpenHear.

Renders a standard clinical audiogram directly in the terminal using Unicode
block characters and ANSI colour codes.  No external dependencies required —
works on any terminal that supports ANSI colours.

The audiogram is the primary diagnostic tool in audiology: it plots Hearing
Threshold Level (HTL, dB HL) on the Y-axis against frequency (Hz) on the
X-axis, with the Y-axis inverted (worse hearing at the bottom).

Conventions followed:
  - Frequency axis: 125 Hz – 8,000 Hz (standard clinical range).
  - Level axis:     0 dB HL (top) to 120 dB HL (bottom).
  - Right ear:      O markers in blue (ANSI).
  - Left ear:       X markers in red (ANSI).
  - Severity bands: shown as background shading labels.

Below the chart, a summary is printed: PTA per ear, severity classification,
and the gain profile needed for DSP processing.

Usage:
    python -m audiogram.visualiser audiogram/data/burgess_2021.json
"""

import argparse
import sys

from audiogram.loader import (
    get_gain_profile,
    get_pta,
    get_severity,
    get_thresholds,
    load_audiogram,
)

# ── ANSI colour codes ────────────────────────────────────────────────────────

_BLUE = "\033[94m"       # Right ear
_RED = "\033[91m"        # Left ear
_DIM = "\033[2m"         # Dimmed text (severity bands)
_BOLD = "\033[1m"        # Bold
_RESET = "\033[0m"       # Reset all formatting
_CYAN = "\033[96m"       # Headings
_YELLOW = "\033[93m"     # Warnings / highlights
_GREEN = "\033[92m"      # Normal severity

# Standard clinical audiogram frequency axis (Hz).
PLOT_FREQUENCIES = [125, 250, 500, 1000, 2000, 4000, 8000]

# Chart dimensions (characters).
_CHART_WIDTH = 72
_CHART_HEIGHT = 24

# dB HL range for the chart.
_DB_MIN = 0
_DB_MAX = 120

# Severity zone boundaries (upper edge of zone in dB HL).
_ZONES = [
    (25,  "Normal"),
    (40,  "Mild"),
    (55,  "Moderate"),
    (70,  "Mod-Severe"),
    (90,  "Severe"),
    (120, "Profound"),
]


def _db_to_row(db: int) -> int:
    """Map a dB HL value to a chart row (0 = top = 0 dB HL)."""
    clamped = max(_DB_MIN, min(_DB_MAX, db))
    return round((clamped - _DB_MIN) / (_DB_MAX - _DB_MIN) * (_CHART_HEIGHT - 1))


def _freq_to_col(freq: int) -> int:
    """Map a frequency to a chart column using log spacing."""
    import math
    log_min = math.log2(PLOT_FREQUENCIES[0])
    log_max = math.log2(PLOT_FREQUENCIES[-1])
    log_freq = math.log2(max(PLOT_FREQUENCIES[0], min(PLOT_FREQUENCIES[-1], freq)))
    return round((log_freq - log_min) / (log_max - log_min) * (_CHART_WIDTH - 1))


def _severity_colour(label: str) -> str:
    """Return an ANSI colour code for a severity label."""
    if label == "Normal":
        return _GREEN
    if label == "Mild":
        return _YELLOW
    return _RED


def print_audiogram(path: str) -> None:
    """Render an audiogram as a text chart in the terminal.

    Loads the audiogram from *path*, plots right ear (O, blue) and left
    ear (X, red) on a frequency × dB HL grid, and prints a summary
    with PTA, severity, and gain profile.

    Args:
        path: Path to an audiogram JSON file in openhear-audiogram-v1 format.
    """
    audiogram = load_audiogram(path)

    right_thresh = get_thresholds(audiogram, "right")
    left_thresh = get_thresholds(audiogram, "left")

    # ── Build the grid ────────────────────────────────────────────────────────
    # Each cell is a single character.  We overlay ear markers on top.
    grid: list[list[str]] = [
        [" "] * _CHART_WIDTH for _ in range(_CHART_HEIGHT)
    ]

    # Place right ear markers (O) — blue
    right_positions: dict[tuple[int, int], int] = {}
    for freq, db in right_thresh:
        col = _freq_to_col(freq)
        row = _db_to_row(db)
        right_positions[(row, col)] = db

    # Place left ear markers (X) — red
    left_positions: dict[tuple[int, int], int] = {}
    for freq, db in left_thresh:
        col = _freq_to_col(freq)
        row = _db_to_row(db)
        left_positions[(row, col)] = db

    # ── Print header ─────────────────────────────────────────────────────────
    subject = audiogram.get("subject", "Unknown")
    date = audiogram.get("date", "Unknown")
    print()
    print(f"  {_BOLD}{_CYAN}Audiogram — {subject}{_RESET}")
    print(f"  {_DIM}Date: {date}   Source: {audiogram.get('source', 'N/A')}{_RESET}")
    print()

    # Legend
    print(f"  {_BLUE}O{_RESET} = Right ear   {_RED}X{_RESET} = Left ear")
    print()

    # ── Frequency axis labels (top) ──────────────────────────────────────────
    freq_label_line = " " * 8  # Space for dB label column
    for freq in PLOT_FREQUENCIES:
        col = _freq_to_col(freq)
        label = str(freq)
        # Position the label centred on its column
        pos = 8 + col
        while len(freq_label_line) < pos:
            freq_label_line += " "
        freq_label_line = freq_label_line[:pos] + label
    print(f"  {_DIM}Hz{_RESET}  " + freq_label_line[4:])

    # Top border
    print(f"       {'─' * (_CHART_WIDTH + 2)}")

    # ── Chart rows ───────────────────────────────────────────────────────────
    for row in range(_CHART_HEIGHT):
        # dB label on the left
        db_val = _DB_MIN + row * (_DB_MAX - _DB_MIN) // (_CHART_HEIGHT - 1)
        db_label = f"{db_val:>4d}"

        # Severity band label on the right
        severity_label = ""
        for upper, label in _ZONES:
            zone_row = _db_to_row(upper)
            zone_mid = _db_to_row(
                (upper - ([0] + [z[0] for z in _ZONES])[_ZONES.index((upper, label))]) // 2
                + ([0] + [z[0] for z in _ZONES])[_ZONES.index((upper, label))]
            )
            if row == zone_mid:
                severity_label = f" {_severity_colour(label)}{label}{_RESET}"
                break

        # Build the row string
        row_chars = []
        for col in range(_CHART_WIDTH):
            pos = (row, col)
            if pos in right_positions and pos in left_positions:
                # Both ears at same position — show combined marker
                row_chars.append(f"{_BLUE}O{_RESET}{_RED}X{_RESET}")
            elif pos in right_positions:
                row_chars.append(f"{_BLUE}O{_RESET}")
            elif pos in left_positions:
                row_chars.append(f"{_RED}X{_RESET}")
            else:
                # Grid dots at frequency tick columns
                is_freq_col = col in [_freq_to_col(f) for f in PLOT_FREQUENCIES]
                # Horizontal zone boundary lines
                is_zone_row = any(
                    row == _db_to_row(z[0]) for z in _ZONES
                )
                if is_freq_col and is_zone_row:
                    row_chars.append(f"{_DIM}+{_RESET}")
                elif is_freq_col:
                    row_chars.append(f"{_DIM}│{_RESET}")
                elif is_zone_row:
                    row_chars.append(f"{_DIM}·{_RESET}")
                else:
                    row_chars.append(" ")

        print(f"  {db_label} │{''.join(row_chars)}│{severity_label}")

    # Bottom border
    print(f"       {'─' * (_CHART_WIDTH + 2)}")
    print()

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"  {_BOLD}Summary{_RESET}")
    print(f"  {'─' * 50}")

    for ear, colour, symbol in [("right", _BLUE, "O"), ("left", _RED, "X")]:
        label = f"{ear.capitalize()} Ear ({symbol})"
        try:
            pta = get_pta(audiogram, ear)
            sev = get_severity(int(pta))
            print(f"  {colour}{label}{_RESET}:  PTA = {pta:.1f} dB HL  →  {sev}")
        except ValueError:
            print(f"  {colour}{label}{_RESET}:  PTA = insufficient data")

    # ── Gain profile ─────────────────────────────────────────────────────────
    print()
    print(f"  {_BOLD}Gain Profile (dB needed to reach 20 dB HL){_RESET}")
    print(f"  {'─' * 50}")
    for ear, colour, symbol in [("right", _BLUE, "O"), ("left", _RED, "X")]:
        gains = get_gain_profile(audiogram, ear)
        gain_strs = [f"{freq}Hz: +{gain}dB" for freq, gain in gains if gain > 0]
        if gain_strs:
            print(f"  {colour}{ear.capitalize()} ({symbol}){_RESET}: {', '.join(gain_strs)}")
        else:
            print(f"  {colour}{ear.capitalize()} ({symbol}){_RESET}: no amplification needed")

    print()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Display an audiogram in the terminal from an "
                    "openhear-audiogram-v1 JSON file."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to audiogram JSON file.",
    )
    parser.add_argument(
        "--input", "-i",
        dest="input_flag",
        default=None,
        help="Path to audiogram JSON file (alternative to positional arg).",
    )
    args = parser.parse_args()

    path = args.input or args.input_flag
    if not path:
        parser.error("Please provide a path to an audiogram JSON file.")
        sys.exit(1)

    print_audiogram(path)


if __name__ == "__main__":
    main()
