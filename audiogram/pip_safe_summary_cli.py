"""
pip_safe_summary_cli.py – consent-and-preview CLI for the communication-needs summary.

Reads a local self-report file (or a Living Hearing Profile carrying a
``communication_needs`` block), lets the person choose sections, shows the
exact Markdown and JSON that would be written, and writes local files only
after an explicit typed confirmation.  Cancelling writes nothing.  No network
calls are made.

Usage::

    python -m audiogram.pip_safe_summary_cli SELF_REPORT.json --out my_summary
    python -m audiogram.pip_safe_summary_cli SELF_REPORT.json --out my_summary \\
        --include reasonable_adjustments --include functional_impact --no-hash
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from audiogram.pip_safe_summary import (
    CONSENT_STATEMENT,
    DEFAULT_SECTIONS,
    SECTIONS,
    available_sections,
    build_json_text,
    build_markdown,
    build_summary,
    clinical_text_warnings,
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
@click.option("--no-hash", is_flag=True, help="Leave out the optional SHA-256 integrity hash.")
@click.option("--overwrite", is_flag=True, help="Allow replacing existing output files.")
def main(source: Path, out: Path, include: tuple[str, ...], no_hash: bool, overwrite: bool) -> None:
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
    click.echo("Hearing test results, diagnosis and identifiers are never included.\n")

    if include:
        chosen = [s for s in present if s in include]
    else:
        chosen = [
            s for s in present if click.confirm(f"Include '{s}'?", default=s in DEFAULT_SECTIONS)
        ]

    try:
        doc = build_summary(
            data,
            include=chosen,
            consent_given=True,
            preview_confirmed=True,
            with_integrity_hash=not no_hash,
        )
    except ValueError as exc:
        click.echo(f"Could not build summary: {exc}", err=True)
        sys.exit(1)

    click.echo("\n──── PREVIEW: Markdown that will be written ────\n")
    click.echo(build_markdown(doc))
    click.echo("──── PREVIEW: JSON that will be written ────\n")
    click.echo(build_json_text(doc))

    for warning in clinical_text_warnings(doc):
        click.echo(f"Note: your own words may include clinical detail — {warning}")

    click.echo(f"\nConsent statement: {CONSENT_STATEMENT}")
    answer = click.prompt(
        f"Type '{CONFIRM_WORD}' to confirm and write these files, or anything else to cancel",
        default="",
        show_default=False,
    )
    if answer.strip().lower() != CONFIRM_WORD:
        click.echo("Cancelled. Nothing was written.")
        sys.exit(0)

    try:
        md_path, json_path = write_summary(doc, out, overwrite=overwrite)
    except (FileExistsError, PermissionError, ValueError, OSError) as exc:
        click.echo(f"Not written: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Written locally:\n  {md_path}\n  {json_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
