"""
explain_cli.py – CLI front-end for plain-English fitting explanation.

Wraps :func:`dsp.explain.explain` with a :mod:`click` command so a person
can understand the fitting OpenHear prescribes for their own audiogram.

Usage::

    python -m dsp.explain_cli AG.json
    python -m dsp.explain_cli AG.json --json
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path

import click

from audiogram.audiogram import Audiogram
from dsp.explain import explain, summarise


@click.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--json", "as_json", is_flag=True, help="Emit the explanation as JSON.")
def main(path: Path, as_json: bool) -> None:
    """Explain the fitting prescribed for the audiogram at PATH."""
    try:
        audiogram = Audiogram.from_path(path)
    except (ValueError, OSError) as exc:
        click.echo(f"Could not read audiogram: {exc}", err=True)
        sys.exit(1)

    explanation = explain(audiogram)
    if as_json:
        click.echo(_json.dumps(explanation.to_dict(), indent=2))
    else:
        click.echo(summarise(explanation))


if __name__ == "__main__":  # pragma: no cover
    main()
