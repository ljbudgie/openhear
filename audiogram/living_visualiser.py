"""
living_visualiser.py – terminal visualiser for the Living Hearing Profile.

Extends the standard audiogram chart (from ``audiogram.visualiser``) with
additional panels for:

- Preference-layer loudness offsets (shown as +/- deltas on the gain profile).
- Haptic substitution weights (horizontal bar chart).
- Active listening context summary.
- A one-line "hearing passport" banner.

No external dependencies — ANSI colours, Unicode blocks.

Usage::

    python -m audiogram.living_visualiser audiogram/data/burgess_living_profile.json

Or pass any ``openhear-audiogram-v1`` file; it will be wrapped automatically.
"""

from __future__ import annotations

import argparse
import math
import sys

from audiogram.living_profile import LivingHearingProfile
from audiogram.loader import get_severity

# ── ANSI colour codes ─────────────────────────────────────────────────────────

_BLUE = "\033[94m"
_RED = "\033[91m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"
_CYAN = "\033[96m"
_YELLOW = "\033[93m"
_GREEN = "\033[92m"
_MAGENTA = "\033[95m"

# Chart dimensions.
PLOT_FREQUENCIES = [125, 250, 500, 1000, 2000, 4000, 8000]
_CHART_WIDTH = 72
_CHART_HEIGHT = 24
_DB_MIN = 0
_DB_MAX = 120

_ZONES = [
    (25,  "Normal"),
    (40,  "Mild"),
    (55,  "Moderate"),
    (70,  "Mod-Severe"),
    (90,  "Severe"),
    (120, "Profound"),
]


def _db_to_row(db: int) -> int:
    clamped = max(_DB_MIN, min(_DB_MAX, db))
    return round((clamped - _DB_MIN) / (_DB_MAX - _DB_MIN) * (_CHART_HEIGHT - 1))


def _freq_to_col(freq: int) -> int:
    log_min = math.log2(PLOT_FREQUENCIES[0])
    log_max = math.log2(PLOT_FREQUENCIES[-1])
    log_freq = math.log2(max(PLOT_FREQUENCIES[0], min(PLOT_FREQUENCIES[-1], freq)))
    return round((log_freq - log_min) / (log_max - log_min) * (_CHART_WIDTH - 1))


def _severity_colour(label: str) -> str:
    if label == "Normal":
        return _GREEN
    if label == "Mild":
        return _YELLOW
    return _RED


def print_living_profile(path: str) -> None:
    """Render a Living Hearing Profile as a rich terminal display.

    Args:
        path: Path to an ``openhear-living-profile-v1`` or
              ``openhear-audiogram-v1`` JSON file.
    """
    profile = LivingHearingProfile.from_file(path)
    summ = profile.summary()

    right_thresh = profile.get_thresholds("right")
    left_thresh = profile.get_thresholds("left")

    # ── Header ─────────────────────────────────────────────────────────────────
    print()
    print(f"  {_BOLD}{_CYAN}Living Hearing Profile — {profile.subject}{_RESET}")
    print(
        f"  {_DIM}Clinical: {profile.clinical_date}   "
        f"Updated: {summ.get('last_updated', 'unknown')}   "
        f"History entries: {summ.get('history_entries', 0)}{_RESET}"
    )
    print()
    print(f"  {_BLUE}O{_RESET} = Right ear   {_RED}X{_RESET} = Left ear")
    print()

    # ── Frequency axis ─────────────────────────────────────────────────────────
    freq_label_line = " " * 8
    for freq in PLOT_FREQUENCIES:
        col = _freq_to_col(freq)
        label = str(freq)
        pos = 8 + col
        while len(freq_label_line) < pos:
            freq_label_line += " "
        freq_label_line = freq_label_line[:pos] + label
    print(f"  {_DIM}Hz{_RESET}  " + freq_label_line[4:])
    print(f"       {'─' * (_CHART_WIDTH + 2)}")

    # ── Grid ───────────────────────────────────────────────────────────────────
    right_pos: dict[tuple[int, int], int] = {}
    for freq, db in right_thresh:
        right_pos[(_db_to_row(db), _freq_to_col(freq))] = db

    left_pos: dict[tuple[int, int], int] = {}
    for freq, db in left_thresh:
        left_pos[(_db_to_row(db), _freq_to_col(freq))] = db

    for row in range(_CHART_HEIGHT):
        db_val = _DB_MIN + row * (_DB_MAX - _DB_MIN) // (_CHART_HEIGHT - 1)
        db_label = f"{db_val:>4d}"

        severity_label = ""
        for upper, label in _ZONES:
            zone_mid = _db_to_row(
                (upper - ([0] + [z[0] for z in _ZONES])[_ZONES.index((upper, label))]) // 2
                + ([0] + [z[0] for z in _ZONES])[_ZONES.index((upper, label))]
            )
            if row == zone_mid:
                severity_label = f" {_severity_colour(label)}{label}{_RESET}"
                break

        row_chars: list[str] = []
        freq_cols = [_freq_to_col(f) for f in PLOT_FREQUENCIES]
        zone_rows = {_db_to_row(z[0]) for z in _ZONES}

        for col in range(_CHART_WIDTH):
            pos = (row, col)
            if pos in right_pos and pos in left_pos:
                row_chars.append(f"{_BLUE}O{_RESET}{_RED}X{_RESET}")
            elif pos in right_pos:
                row_chars.append(f"{_BLUE}O{_RESET}")
            elif pos in left_pos:
                row_chars.append(f"{_RED}X{_RESET}")
            elif col in freq_cols and row in zone_rows:
                row_chars.append(f"{_DIM}+{_RESET}")
            elif col in freq_cols:
                row_chars.append(f"{_DIM}│{_RESET}")
            elif row in zone_rows:
                row_chars.append(f"{_DIM}·{_RESET}")
            else:
                row_chars.append(" ")

        print(f"  {db_label} │{''.join(row_chars)}│{severity_label}")

    print(f"       {'─' * (_CHART_WIDTH + 2)}")
    print()

    # ── Clinical summary ──────────────────────────────────────────────────────
    print(f"  {_BOLD}Clinical Summary{_RESET}")
    print(f"  {'─' * 50}")
    for ear, colour, symbol in [("right", _BLUE, "O"), ("left", _RED, "X")]:
        try:
            pta = profile.get_pta(ear)
            sev = get_severity(int(pta))
            print(f"  {colour}{ear.capitalize()} ({symbol}){_RESET}:  PTA = {pta:.1f} dB HL  →  {sev}")
        except ValueError:
            print(f"  {colour}{ear.capitalize()} ({symbol}){_RESET}:  PTA = insufficient data")
    print()

    # ── Gain profile with preference offsets ──────────────────────────────────
    print(f"  {_BOLD}Gain Profile (clinical + preference offsets){_RESET}")
    print(f"  {'─' * 50}")
    for ear, colour, symbol in [("right", _BLUE, "O"), ("left", _RED, "X")]:
        clinical = dict(profile.get_gain_profile(ear, include_preference=False))
        with_pref = dict(profile.get_gain_profile(ear, include_preference=True))
        parts: list[str] = []
        for freq in sorted(clinical):
            cg = clinical[freq]
            pg = with_pref.get(freq, cg)
            if cg == pg or pg == 0:
                parts.append(f"{freq}Hz:+{pg}dB")
            else:
                diff = pg - cg
                sign = "+" if diff >= 0 else ""
                parts.append(f"{freq}Hz:+{cg}dB{_MAGENTA}({sign}{diff}){_RESET}")
        if parts:
            print(f"  {colour}{ear.capitalize()} ({symbol}){_RESET}: {', '.join(parts)}")
    print()

    # ── Haptic layer ──────────────────────────────────────────────────────────
    weights = profile.get_haptic_weights()
    if weights:
        print(f"  {_BOLD}Haptic Substitution Weights{_RESET}")
        print(f"  {'─' * 50}")
        for cls_name, weight in sorted(weights.items(), key=lambda kv: -kv[1]):
            if cls_name == "silence":
                continue
            bar = _weight_bar(weight)
            print(f"  {cls_name:<14} {_CYAN}{bar}{_RESET}  {weight:.0%}")
        print()

    # ── Active context ─────────────────────────────────────────────────────────
    ctx = profile.get_active_context()
    if ctx:
        label = ctx.get("label", ctx.get("name", "unknown"))
        print(f"  {_BOLD}Active Context:{_RESET} {label}")
        print(
            f"    Noise reduction: {ctx.get('noise_reduction_aggressiveness', 0):.0%}   "
            f"Beamforming: {'on' if ctx.get('beamforming_enabled') else 'off'}   "
            f"Voice boost: ×{ctx.get('voice_clarity_gain', 1.0):.1f}"
        )
        print()

    # ── History snippet ────────────────────────────────────────────────────────
    history = profile.get_history()
    if history:
        last = history[-1]
        ts = last.get("timestamp", "")[:10]
        print(
            f"  {_DIM}Last change ({ts}): {last.get('description', '')} "
            f"[sha256: {last.get('sha256', '')[:12]}…]{_RESET}"
        )
        print()


def _weight_bar(weight: float, width: int = 20) -> str:
    filled = round(weight * width)
    return "█" * filled + "░" * (width - filled)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Visualise a Living Hearing Profile in the terminal."
    )
    parser.add_argument("input", nargs="?", help="Path to profile or audiogram JSON.")
    parser.add_argument("--input", "-i", dest="input_flag", default=None)
    args = parser.parse_args()

    path = args.input or args.input_flag
    if not path:
        parser.error("Please provide a path to a profile JSON file.")
        sys.exit(1)

    print_living_profile(path)


if __name__ == "__main__":
    main()
