"""
visualiser.py – audiogram plotter for OpenHear.

Renders a standard clinical audiogram from hearing threshold data.  The
audiogram is the primary diagnostic tool in audiology: it plots Hearing
Threshold Level (HTL, dB HL) on the Y-axis against frequency (Hz) on the
X-axis, with the Y-axis inverted (worse hearing at the bottom).

Conventions followed:
  - Frequency axis: 125 Hz – 8,000 Hz (standard clinical range).
  - Level axis:     -10 dB HL (top) to 120 dB HL (bottom) — ITU-T / ISO 8253.
  - Left ear:       blue circles (○), right ear: red crosses (×).
  - Shaded zones:   normal (<25 dB HL), mild (25-40), moderate (40-60),
                    moderately-severe (60-80), severe (80-100), profound (>100).

Input:
    A dict produced by audiogram/reader.py::

        {
            "left":  {250: 30.0, 500: 35.0, 1000: 45.0, ...},
            "right": {250: 25.0, 500: 30.0, 1000: 40.0, ...},
        }

Usage:
    python -m audiogram.visualiser --input audiogram.json
    python -m audiogram.visualiser --input audiogram.json --output audiogram.png
"""

import argparse
import json
import logging
import sys

logger = logging.getLogger(__name__)

# Standard clinical audiogram frequency axis (Hz).
PLOT_FREQUENCIES = [125, 250, 500, 1000, 2000, 4000, 8000]

# Severity zone boundaries (upper edge of zone in dB HL).
_ZONES = [
    (25,  "Normal",              "#e8f5e9"),  # green tint
    (40,  "Mild",                "#fff9c4"),  # yellow tint
    (60,  "Moderate",            "#ffe0b2"),  # orange tint
    (80,  "Moderately-Severe",   "#ffccbc"),  # red-orange tint
    (100, "Severe",              "#ef9a9a"),  # red tint
    (120, "Profound",            "#e53935"),  # deep red
]


def _prepare_ear_data(thresholds: dict, frequencies: list) -> list:
    """Return a list of (freq, htl) pairs for frequencies present in thresholds.

    Missing frequencies are skipped (not plotted) rather than assumed zero.
    Frequency keys may be int or string (JSON loads keys as strings).
    """
    pairs = []
    for freq in frequencies:
        key_int = int(freq)
        key_str = str(freq)
        if key_int in thresholds:
            pairs.append((key_int, float(thresholds[key_int])))
        elif key_str in thresholds:
            pairs.append((key_int, float(thresholds[key_str])))
    return pairs


def plot_audiogram(
    data: dict,
    output_path: str | None = None,
    show: bool = True,
) -> None:
    """Render an audiogram from *data*.

    Args:
        data:        Threshold dict with 'left' and/or 'right' sub-dicts.
        output_path: If given, save the figure to this file (PNG/PDF/SVG).
        show:        If True, open an interactive matplotlib window.
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
    except ImportError:
        logger.error(
            "matplotlib is required for audiogram visualisation. "
            "Install it with: pip install matplotlib"
        )
        sys.exit(1)

    fig, ax = plt.subplots(figsize=(10, 7))

    # ── Severity zone shading ────────────────────────────────────────────────
    prev_upper = -10
    for upper, label, colour in _ZONES:
        ax.axhspan(prev_upper, upper, alpha=0.25, color=colour, zorder=0)
        ax.text(
            PLOT_FREQUENCIES[-1] * 1.15, (prev_upper + upper) / 2,
            label, va="center", ha="left", fontsize=7, color="#555555",
        )
        prev_upper = upper

    # ── Per-ear traces ────────────────────────────────────────────────────────
    left_data = _prepare_ear_data(data.get("left", {}), PLOT_FREQUENCIES)
    right_data = _prepare_ear_data(data.get("right", {}), PLOT_FREQUENCIES)

    if left_data:
        lf, lh = zip(*left_data)
        ax.plot(lf, lh, color="royalblue", marker="o", markersize=9,
                linewidth=1.8, label="Left ear (○)", zorder=3)

    if right_data:
        rf, rh = zip(*right_data)
        ax.plot(rf, rh, color="firebrick", marker="x", markersize=9,
                linewidth=1.8, markeredgewidth=2.5, label="Right ear (×)", zorder=3)

    # ── Axes formatting ───────────────────────────────────────────────────────
    ax.set_xscale("log")
    ax.set_xlim(100, 10_000)
    ax.set_xticks(PLOT_FREQUENCIES)
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.set_xlabel("Frequency (Hz)", fontsize=12)

    ax.invert_yaxis()
    ax.set_ylim(120, -10)
    ax.set_yticks(range(-10, 130, 10))
    ax.set_ylabel("Hearing Level (dB HL)", fontsize=12)

    ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.6, zorder=1)
    ax.set_title("Audiogram", fontsize=15, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150)
        logger.info("Audiogram saved to %s", output_path)

    if show:
        plt.show()

    plt.close(fig)


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="Plot an audiogram from a JSON threshold file."
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Path to audiogram JSON file produced by audiogram/reader.py.",
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Optional output file path (PNG, PDF, SVG).  "
             "If omitted, an interactive window is shown.",
    )
    parser.add_argument(
        "--no-show", action="store_true",
        help="Do not open the interactive window (useful for headless rendering).",
    )
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as fh:
        data = json.load(fh)

    plot_audiogram(data, output_path=args.output, show=not args.no_show)


if __name__ == "__main__":
    main()
