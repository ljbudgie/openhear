"""
fatigue_cli.py – manage the local Whoop recovery file (roadmap S3).

Five subcommands:

    python -m dsp.fatigue_cli show
    python -m dsp.fatigue_cli set --score 64
    python -m dsp.fatigue_cli classify --score 30
    python -m dsp.fatigue_cli clear        # delete the local recovery file
    python -m dsp.fatigue_cli where        # print the resolved path

Use ``--path FILE`` (or the ``OPENHEAR_WHOOP_FILE`` environment
variable) to point at a recovery file outside the default location.

No network call is ever made — this CLI only manipulates a single
local JSON file.  Sensitive health data per `SECURITY.md`.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from dsp.fatigue import (
    DEFAULT_GREEN_FLOOR,
    DEFAULT_RED_CEILING,
    WhoopRecovery,
    bucket,
    default_recovery_path,
    fatigue_bias,
    forget_recovery,
    read_recovery,
    write_recovery,
)


def _cmd_show(args: argparse.Namespace) -> int:
    try:
        recovery = read_recovery(args.path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if recovery is None:
        print("(no recovery file)")
        return 0
    b = bucket(
        recovery.score,
        green_floor=args.green_floor,
        red_ceiling=args.red_ceiling,
    )
    bias = fatigue_bias(b, source_score=recovery.score)
    print(
        json.dumps(
            {
                "score": recovery.score,
                "timestamp": recovery.timestamp,
                "source": recovery.source,
                "bucket": b.value,
                "suggest_low_effort_preset": bias.suggest_low_effort_preset,
            },
            indent=2,
        )
    )
    print()
    print(bias.explanation)
    if not bias.delta.is_identity():
        print(bias.delta.explain())
    return 0


def _cmd_set(args: argparse.Namespace) -> int:
    if not (0 <= args.score <= 100):
        print("error: --score must be 0–100", file=sys.stderr)
        return 2
    timestamp = args.timestamp or datetime.now(timezone.utc).isoformat()
    recovery = WhoopRecovery(score=args.score, timestamp=timestamp, source=args.source)
    target = write_recovery(recovery, args.path)
    print(f"wrote recovery score={recovery.score} to {target}")
    return 0


def _cmd_classify(args: argparse.Namespace) -> int:
    b = bucket(
        args.score,
        green_floor=args.green_floor,
        red_ceiling=args.red_ceiling,
    )
    bias = fatigue_bias(b, source_score=args.score)
    print(b.value)
    print(bias.explanation)
    if not bias.delta.is_identity():
        print(bias.delta.explain())
    return 0


def _cmd_clear(args: argparse.Namespace) -> int:
    removed = forget_recovery(args.path)
    if removed:
        print("recovery file deleted")
    else:
        print("(no recovery file to delete)")
    return 0


def _cmd_where(args: argparse.Namespace) -> int:
    print(args.path or default_recovery_path())
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m dsp.fatigue_cli",
        description=(
            "Manage the local Whoop recovery file used by the fatigue-aware "
            "DSP hooks (roadmap S3 → M6).  No network call is ever made."
        ),
    )
    parser.add_argument(
        "--path",
        default=None,
        help=(
            "Path to the recovery JSON file.  Defaults to "
            "~/.openhear/whoop_recovery.json (or $OPENHEAR_WHOOP_FILE)."
        ),
    )
    parser.add_argument(
        "--green-floor",
        type=int,
        default=DEFAULT_GREEN_FLOOR,
        help="Inclusive lower bound for the green bucket (default 67).",
    )
    parser.add_argument(
        "--red-ceiling",
        type=int,
        default=DEFAULT_RED_CEILING,
        help="Inclusive upper bound for the red bucket (default 33).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "show", help="Show the current recovery reading and resolved bias."
    ).set_defaults(func=_cmd_show)

    set_p = sub.add_parser("set", help="Manually set the local recovery score (0–100).")
    set_p.add_argument("--score", type=int, required=True)
    set_p.add_argument(
        "--timestamp",
        default=None,
        help="ISO 8601 timestamp; defaults to now (UTC).",
    )
    set_p.add_argument(
        "--source",
        default="manual",
        help="Free-text source tag (default: 'manual').",
    )
    set_p.set_defaults(func=_cmd_set)

    cl_p = sub.add_parser(
        "classify",
        help="Classify a hypothetical score without writing anything.",
    )
    cl_p.add_argument("--score", type=int, required=True)
    cl_p.set_defaults(func=_cmd_classify)

    sub.add_parser(
        "clear",
        help="Delete the local recovery file (full deletion path).",
    ).set_defaults(func=_cmd_clear)

    sub.add_parser("where", help="Print the resolved recovery file path and exit.").set_defaults(
        func=_cmd_where
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover - thin CLI shim
    sys.exit(main())
