"""
compare.py – CLI front-end for comparing audiograms over time.

Wraps :func:`audiogram.loader.compare_audiograms` with a
:mod:`click`-based command line so users can quickly print a
side-by-side diff of two audiograms and spot frequencies where their
hearing has changed.

Usage::

    python -m audiogram.compare OLD.json NEW.json
    python -m audiogram.compare OLD.json NEW.json --json
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path

import click

from audiogram.loader import compare_audiograms


def _format_diff_line(freq: int, diff: int) -> str:
    """Return a single human-readable line for a per-frequency delta."""
    if diff > 0:
        marker = click.style(f"+{diff:>3d}", fg="red")
        suffix = " (worse)"
    elif diff < 0:
        marker = click.style(f"{diff:>4d}", fg="green")
        suffix = " (better)"
    else:
        marker = f"{diff:>4d}"
        suffix = ""
    return f"  {freq:>5d} Hz : {marker} dB{suffix}"


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "old_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "new_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--json", "as_json", is_flag=True,
    help="Emit the comparison as JSON instead of a human-readable report.",
)
def main(old_path: Path, new_path: Path, as_json: bool) -> None:
    """Compare two OpenHear audiogram JSON files and report deltas.

    A positive delta means the threshold in NEW is higher (worse) than
    in OLD at that frequency.  Negative means improvement.
    """
    result = compare_audiograms(str(old_path), str(new_path))

    if as_json:
        click.echo(_json.dumps(result, indent=2, sort_keys=True))
        return

    click.echo(f"Comparing:\n  old : {old_path}\n  new : {new_path}\n")
    for ear in ("right", "left"):
        click.echo(click.style(f"{ear.capitalize()} ear", bold=True))
        diffs = result.get(ear, [])
        if not diffs:
            click.echo("  (no overlapping frequencies)")
        for freq, diff in diffs:
            click.echo(_format_diff_line(freq, diff))
        pta_diff = result.get(f"{ear}_pta_diff")
        if pta_diff is None:
            click.echo("  PTA delta: insufficient data\n")
        else:
            click.echo(f"  PTA delta: {pta_diff:+.1f} dB\n")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
