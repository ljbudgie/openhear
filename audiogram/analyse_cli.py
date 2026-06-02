"""
analyse_cli.py – CLI front-end for plain-English audiogram interpretation.

Wraps :func:`audiogram.analyse.analyse` with a :mod:`click` command so a
person can understand their own audiogram from the terminal without a
clinic visit.

Usage::

    python -m audiogram.analyse_cli AG.json
    python -m audiogram.analyse_cli AG.json --json
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path

import click

from audiogram.analyse import analyse, summarise
from audiogram.audiogram import Audiogram


@click.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--json", "as_json", is_flag=True, help="Emit the analysis as JSON.")
def main(path: Path, as_json: bool) -> None:
    """Interpret the audiogram at PATH in plain English."""
    try:
        audiogram = Audiogram.from_path(path)
    except (ValueError, OSError) as exc:
        click.echo(f"Could not read audiogram: {exc}", err=True)
        sys.exit(1)

    analysis = analyse(audiogram)
    if as_json:
        click.echo(_json.dumps(analysis.to_dict(), indent=2))
    else:
        click.echo(summarise(analysis))


if __name__ == "__main__":  # pragma: no cover
    main()
