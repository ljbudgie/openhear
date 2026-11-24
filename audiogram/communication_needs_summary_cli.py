"""
communication_needs_summary_cli.py – consent-and-preview CLI for the communication-needs summary.

Reads a local self-report file (or a Living Hearing Profile carrying a
``communication_needs`` block), lets the person choose sections, shows a
boxed warning about free text, then the exact Markdown and JSON with consent
shown as PENDING.  Consent is recorded, with its date, only after the person
types ``write``.  Cancelling writes nothing.  No network calls are made.

Privacy defaults: no export timestamp (``--include-export-time`` to add one)
and entry dates shown to the month (``--date-precision day|month|year``).

Usage::

    python -m audiogram.communication_needs_summary_cli SELF_REPORT.json --out my_summary
    python -m audiogram.communication_needs_summary_cli SELF_REPORT.json --out my_summary \\
        --include reasonable_adjustments --include functional_impact \\
        --date-precision year --no-hash
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from audiogram.communication_needs_summary import (
    CONSENT_STATEMENT,
    DATE_PRECISIONS,
    DEFAULT_DATE_PRECISION,
    DEFAULT_SECTIONS,
    SECTIONS,
    available_sections,
    build_json_text,
    build_markdown,
    build_summary,
    confirm_consent,
    free_text_warning_box,
    write_summary,
)

CONFIRM_WORD = "write"


@click.command()
@click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--out",
    "out",
    required=True,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Local output path without extension; .md and .json are added.",
)
@click.option(
    "--include",
    "include",
    multiple=True,
    type=click.Choice(SECTIONS),
    help="Pre-select a section (repeatable). Without this you are asked about each one.",
)
@click.option(
    "--include-export-time",
    is_flag=True,
    help="Add the exact export time. Off by default, because a timestamp makes a file easier to link.",
)
@click.option(
    "--date-precision",
    type=click.Choice(list(DATE_PRECISIONS)),
    default=DEFAULT_DATE_PRECISION,
    show_default=True,
    help=(
        "Precision of recorded, last-reviewed and variation dates. The consent date "
        "(given_at) follows the same precision rule unless --include-export-time is set, "
        "in which case it is a full timestamp."
    ),
)
@click.option("--no-hash", is_flag=True, help="Leave out the optional SHA-256 integrity hash.")
@click.option("--overwrite", is_flag=True, help="Allow replacing existing output files.")
def main(
    source: Path,
    out: Path,
    include: tuple[str, ...],
    include_export_time: bool,
    date_precision: str,
    no_hash: bool,
    overwrite: bool,
) -> None:
    """Build a local communication-needs summary from SOURCE, with preview and consent."""
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        present = available_sections(data)
    except (ValueError, OSError) as exc:
        click.echo(f"Could not read source: {exc}", err=True)
        sys.exit(1)

    if not present:
        click.echo("No self-reported communication-needs sections found in SOURCE.", err=True)
        sys.exit(1)

    click.echo("This writes a local file only. Nothing is uploaded.")
    click.echo("Hearing test results, diagnosis and identifiers are never included as fields.\n")

    if include:
        chosen = [s for s in present if s in include]
    else:
        chosen = [
            s for s in present if click.confirm(f"Include '{s}'?", default=s in DEFAULT_SECTIONS)
        ]

    try:
        pending = build_summary(
            data,
            include=chosen,
            include_export_time=include_export_time,
            date_precision=date_precision,
        )
    except ValueError as exc:
        click.echo(f"Could not build summary: {exc}", err=True)
        sys.exit(1)

    click.echo("")
    click.echo(free_text_warning_box(pending))
    click.echo("\n──── PREVIEW: Markdown (consent PENDING) ────\n")
    click.echo(build_markdown(pending))
    click.echo("──── PREVIEW: JSON (consent PENDING) ────\n")
    click.echo(build_json_text(pending))
    click.echo(
        "If you confirm, the only changes from this preview are: consent status becomes "
        "'given' with today's date"
        + (" and time" if include_export_time else f" (to the {date_precision})")
        + ("" if no_hash else ", and an integrity hash is added")
        + "."
    )

    click.echo(f"\nConsent statement: {CONSENT_STATEMENT}")
    answer = click.prompt(
        f"Type '{CONFIRM_WORD}' to give consent and write these files, or anything else to cancel",
        default="",
        show_default=False,
    )
    if answer.strip().lower() != CONFIRM_WORD:
        click.echo("Cancelled. Consent was not given. Nothing was written.")
        sys.exit(0)

    final = confirm_consent(pending, with_integrity_hash=not no_hash)
    try:
        md_path, json_path = write_summary(final, out, overwrite=overwrite)
    except (FileExistsError, PermissionError, ValueError, OSError) as exc:
        click.echo(f"Not written: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Consent given. Written locally:\n  {md_path}\n  {json_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
