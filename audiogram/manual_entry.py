"""
manual_entry.py – CLI for entering audiogram thresholds by hand.

Many people have their audiogram on paper but not in any digital format.
This module walks the user through each standard frequency for each ear,
validates the entered value falls in the clinical range, and writes the
result to a JSON file in ``openhear-audiogram-v1`` format that the rest
of OpenHear can read.

The threshold range accepted is the one defined by ISO 8253-1
(:data:`audiogram.audiogram.MIN_THRESHOLD_DB_HL` to
:data:`MAX_THRESHOLD_DB_HL`).  Frequencies follow the standard
audiometric set in :data:`STANDARD_FREQUENCIES_HZ`.

Usage::

    python -m audiogram.manual_entry --output my_audiogram.json
    python -m audiogram.manual_entry -o ag.json --date 2024-11-15 \\
        --subject "L. Burgess"

Pass ``--skip`` at any prompt to omit that frequency from the saved
audiogram (useful if your paper audiogram does not include 750/1500/3000
Hz, for example).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from audiogram.audiogram import (
    MAX_THRESHOLD_DB_HL,
    MIN_THRESHOLD_DB_HL,
    STANDARD_FREQUENCIES_HZ,
    Audiogram,
)

logger = logging.getLogger(__name__)


def _prompt_threshold(
    freq_hz: int,
    ear: str,
    interactive: bool,
    answers: list[str] | None = None,
) -> float | None:
    """Prompt for a single threshold value, returning ``None`` if skipped.

    Args:
        freq_hz: Frequency being asked about.
        ear: ``"left"`` or ``"right"``.
        interactive: When ``False``, no prompts are issued (used by tests
            that drive the CLI through ``CliRunner``).
        answers: Optional pre-provided answer list (consumed left to right).

    Returns:
        The threshold in dB HL, or ``None`` if the user skipped this
        frequency.

    Raises:
        click.BadParameter: If the entered value is not numeric or falls
            outside the permitted clinical range.
    """
    label = f"{ear.capitalize()} ear, {freq_hz:>5d} Hz [dB HL, or 'skip']"
    while True:
        if answers is not None:
            if not answers:
                return None
            raw = answers.pop(0)
        elif interactive:
            raw = click.prompt(label, default="skip", show_default=True)
        else:  # pragma: no cover - defensive
            return None

        text = str(raw).strip().lower()
        if text in {"skip", "s", ""}:
            return None
        try:
            value = float(text)
        except ValueError:
            click.echo(f"  ✗ '{raw}' is not a number — try again.", err=True)
            if answers is None and interactive:
                continue
            raise click.BadParameter(f"{raw!r} is not a number")
        if not (MIN_THRESHOLD_DB_HL <= value <= MAX_THRESHOLD_DB_HL):
            msg = (
                f"  ✗ {value} dB HL is outside the valid range "
                f"[{MIN_THRESHOLD_DB_HL}, {MAX_THRESHOLD_DB_HL}] — try again."
            )
            click.echo(msg, err=True)
            if answers is None and interactive:
                continue
            raise click.BadParameter(f"{value} out of range")
        return value


def collect_audiogram(
    *,
    subject: str = "",
    date_measured: str = "unknown",
    notes: str = "",
    answers: list[str] | None = None,
    interactive: bool = True,
) -> Audiogram:
    """Walk the user through every standard frequency for each ear.

    Args:
        subject: Subject identifier to record on the audiogram.
        date_measured: Date the test was taken (ISO-8601 ``YYYY-MM-DD``)
            or ``"unknown"``.
        notes: Optional free-form notes.
        answers: Test hook — if provided, these strings are consumed in
            place of interactive prompts (left-to-right, right ear then
            left, frequency-ascending).
        interactive: Whether to issue interactive prompts.  Forced
            ``False`` when ``answers`` is provided.

    Returns:
        The collected :class:`Audiogram` (may have empty ears if the
        user skipped every frequency).
    """
    if answers is not None:
        interactive = False

    if interactive:
        click.echo(
            "Enter your audiogram thresholds in dB HL.\n"
            f"Range: {MIN_THRESHOLD_DB_HL} to {MAX_THRESHOLD_DB_HL}.  "
            "Press <Enter> or type 'skip' to omit a frequency.\n"
        )

    right: dict[int, float] = {}
    left: dict[int, float] = {}
    for ear, store in (("right", right), ("left", left)):
        if interactive:
            click.echo(click.style(f"\n— {ear.capitalize()} ear —", bold=True))
        for freq in STANDARD_FREQUENCIES_HZ:
            value = _prompt_threshold(freq, ear, interactive, answers)
            if value is not None:
                store[freq] = value

    return Audiogram(
        left_ear=left,
        right_ear=right,
        date_measured=date_measured,
        source="manual_entry",
        subject=subject,
        notes=notes,
    )


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    required=True,
    help="Where to write the resulting audiogram JSON file.",
)
@click.option(
    "--subject", default="",
    help="Subject identifier to embed in the file (default: anonymous).",
)
@click.option(
    "--date", "date_measured", default="unknown",
    help="Date the audiogram was taken (ISO-8601 YYYY-MM-DD).",
)
@click.option(
    "--notes", default="",
    help="Free-form notes to embed in the file.",
)
@click.option(
    "--force", is_flag=True,
    help="Overwrite the output file if it already exists.",
)
@click.option(
    "--verbose", is_flag=True,
    help="Enable INFO logging.",
)
def main(
    output: Path,
    subject: str,
    date_measured: str,
    notes: str,
    force: bool,
    verbose: bool,
) -> None:
    """Enter audiogram thresholds at the keyboard and save them to JSON."""
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if output.exists() and not force:
        raise click.UsageError(
            f"{output} already exists; pass --force to overwrite."
        )

    audiogram = collect_audiogram(
        subject=subject,
        date_measured=date_measured,
        notes=notes,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(audiogram.to_json(), encoding="utf-8")
    click.echo(f"\nWrote audiogram to {output}")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
