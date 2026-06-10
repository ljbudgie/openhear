"""
contact_cli.py – manage the per-contact DSP profile bank from the shell.

This is the user-facing surface for roadmap S1 (see
``dsp/CONTACT_PROFILES.md``).  It deliberately keeps every action local
and reversible:

    python -m dsp.contact_cli list
    python -m dsp.contact_cli show partner
    python -m dsp.contact_cli set partner --label "Partner" --consent \\
        --voice-gain-delta 0.1 --comp-ratio-delta -0.1
    python -m dsp.contact_cli clear partner
    python -m dsp.contact_cli where

All commands operate on a single local JSON file (default
``~/.openhear/contacts.json``).  Override with ``--path FILE`` if you
want to keep contacts elsewhere (e.g. on an encrypted volume).

Burgess Principle: writes are explicit (no implicit consent toggling),
and the ``set`` command refuses to enable a profile without
``--consent`` so a profile cannot accidentally become active.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dsp.contact_profiles import (
    ContactProfile,
    default_contacts_path,
    load_bank,
    save_bank,
)


def _cmd_list(args: argparse.Namespace) -> int:
    bank = load_bank(args.path)
    ids = bank.list_ids()
    if not ids:
        print("(no contacts saved)")
        return 0
    print(f"{'id':20}  {'label':30}  {'consent':8}  {'enabled':8}")
    print("-" * 70)
    for cid in ids:
        p = bank.profiles[cid]
        print(
            f"{p.contact_id:20}  {p.label:30}  "
            f"{'yes' if p.consent else 'NO':8}  "
            f"{'yes' if p.enabled else 'NO':8}"
        )
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    bank = load_bank(args.path)
    profile = bank.get(args.contact_id)
    if profile is None:
        print(f"error: no contact named {args.contact_id!r}", file=sys.stderr)
        return 1
    print(json.dumps(profile.to_dict(), indent=2))
    delta = profile.to_delta()
    print()
    print(delta.explain())
    return 0


def _cmd_set(args: argparse.Namespace) -> int:
    bank = load_bank(args.path)
    existing = bank.get(args.contact_id)

    label = args.label if args.label is not None else (existing.label if existing else "")
    consent = (
        args.consent if args.consent is not None else (existing.consent if existing else False)
    )
    enabled = args.enabled if args.enabled is not None else (existing.enabled if existing else True)
    notes = args.notes if args.notes is not None else (existing.notes if existing else "")

    def _field(name: str, value: float | None) -> float:
        if value is not None:
            return value
        return float(getattr(existing, name)) if existing else 0.0

    profile = ContactProfile(
        contact_id=args.contact_id.strip().lower(),
        label=label,
        eq_delta_db=dict(existing.eq_delta_db) if existing else {},
        compression_ratio_delta=_field("compression_ratio_delta", args.comp_ratio_delta),
        compression_knee_delta_db=_field("compression_knee_delta_db", args.comp_knee_delta_db),
        voice_gain_delta=_field("voice_gain_delta", args.voice_gain_delta),
        nr_aggressiveness_delta=_field("nr_aggressiveness_delta", args.nr_delta),
        consent=consent,
        enabled=enabled,
        fingerprint=None,
        notes=notes,
    )

    bank.add(profile)
    target = save_bank(bank, args.path)
    print(f"saved contact {profile.contact_id!r} to {target}")
    if not profile.consent:
        print(
            "note: profile stored with consent=False; it will NOT be applied "
            "to the DSP chain until you re-run with --consent."
        )
    print(profile.to_delta().explain())
    return 0


def _cmd_clear(args: argparse.Namespace) -> int:
    bank = load_bank(args.path)
    if args.contact_id == "*":
        if not args.yes:
            print(
                "error: refusing to clear all contacts without --yes",
                file=sys.stderr,
            )
            return 2
        count = len(bank.profiles)
        bank.profiles.clear()
        target = save_bank(bank, args.path)
        print(f"cleared {count} contact(s) in {target}")
        return 0
    removed = bank.remove(args.contact_id)
    if not removed:
        print(f"error: no contact named {args.contact_id!r}", file=sys.stderr)
        return 1
    target = save_bank(bank, args.path)
    print(f"removed contact {args.contact_id!r} from {target}")
    return 0


def _cmd_where(args: argparse.Namespace) -> int:
    path: Path = Path(args.path) if args.path else default_contacts_path()
    print(path)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m dsp.contact_cli",
        description=(
            "Manage the per-contact DSP profile bank (local file only). "
            "All deltas are clipped to the dsp.profile_delta safe envelope."
        ),
    )
    parser.add_argument(
        "--path",
        default=None,
        help=(
            "Path to contacts.json.  Defaults to ~/.openhear/contacts.json.  "
            "No network call is ever made."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List stored contacts.").set_defaults(func=_cmd_list)

    show = sub.add_parser("show", help="Show one contact as JSON.")
    show.add_argument("contact_id")
    show.set_defaults(func=_cmd_show)

    set_p = sub.add_parser(
        "set",
        help=(
            "Create or update a contact profile.  Numeric deltas are clipped to the safe envelope."
        ),
    )
    set_p.add_argument("contact_id")
    set_p.add_argument("--label", default=None, help="Human-readable display name.")
    set_p.add_argument(
        "--comp-ratio-delta",
        type=float,
        default=None,
        dest="comp_ratio_delta",
        help="Bounded delta added to the compressor ratio.",
    )
    set_p.add_argument(
        "--comp-knee-delta-db",
        type=float,
        default=None,
        dest="comp_knee_delta_db",
        help="Bounded delta added to the compressor knee (dB).",
    )
    set_p.add_argument(
        "--voice-gain-delta",
        type=float,
        default=None,
        dest="voice_gain_delta",
        help="Bounded delta added to the voice-clarity gain.",
    )
    set_p.add_argument(
        "--nr-delta",
        type=float,
        default=None,
        dest="nr_delta",
        help="Bounded delta added to the noise-reduction over-subtraction multiplier.",
    )
    set_p.add_argument(
        "--consent",
        dest="consent",
        action="store_const",
        const=True,
        default=None,
        help=("Mark the profile as consented (required before the pipeline will apply it)."),
    )
    set_p.add_argument(
        "--no-consent",
        dest="consent",
        action="store_const",
        const=False,
        help="Withdraw consent for this profile (keeps the tuning on file).",
    )
    set_p.add_argument(
        "--enable",
        dest="enabled",
        action="store_const",
        const=True,
        default=None,
        help="Enable the profile (default for new contacts).",
    )
    set_p.add_argument(
        "--disable",
        dest="enabled",
        action="store_const",
        const=False,
        help="Disable the profile without deleting it (BSEP-style switch).",
    )
    set_p.add_argument("--notes", default=None, help="Free-text notes (kept local).")
    set_p.set_defaults(func=_cmd_set)

    clear = sub.add_parser(
        "clear",
        help="Remove a single contact, or pass '*' with --yes to remove all.",
    )
    clear.add_argument("contact_id")
    clear.add_argument(
        "--yes",
        action="store_true",
        help="Required when contact_id is '*' (remove all contacts).",
    )
    clear.set_defaults(func=_cmd_clear)

    sub.add_parser(
        "where",
        help="Print the resolved path to contacts.json and exit.",
    ).set_defaults(func=_cmd_where)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover - thin CLI shim
    sys.exit(main())
