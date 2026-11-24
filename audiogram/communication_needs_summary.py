"""
communication_needs_summary.py – minimal communication-needs summary export for OpenHear.

Builds an ``openhear-communication-needs-summary-v1`` document: a short, person-held
summary of self-reported communication needs that the person can choose to
keep, print or attach to correspondence themselves.  It is written to local
files only.

What it carries (self-reported only, each item with provenance and dates):

- reasonable adjustments, e.g. email-only contact recorded as a reasonable
  adjustment rather than a preference, or live speech-to-text / palantypist;
- channels that do not work for the person;
- functional impact in the person's own words;
- dated variation-over-time entries in the person's own words.

What it never carries, by construction:

- hearing thresholds, pure-tone averages, severity labels or diagnosis;
- DSP gain, haptic weights or any other clinical-core data;
- any persistent or linking identifier (no record id, NHS number, National
  Insurance number, date of birth or address).

Fields are copied from an explicit allow-list, so anything else in the source
(including a full Living Hearing Profile with a clinical core) is dropped.  A
second, independent key scan (:func:`find_forbidden_keys`) runs before every
write and refuses to write if a forbidden key is present.

This module makes no network calls.  It imports nothing that opens a socket.

The optional SHA-256 value is an **integrity hash** over canonical JSON.  It
lets the holder notice accidental changes.  It is not a signature, not a
certificate, not cryptographic proof of authorship, and not a digital ID.

See ``docs/COMMUNICATION_NEEDS_SUMMARY.md`` for the do-not-claim list.  OpenHear's
intended purpose is unchanged (``docs/INTENDED_PURPOSE.md``).

Usage::

    from audiogram.communication_needs_summary import build_summary, build_markdown, write_summary

    pending = build_summary(source, include=["reasonable_adjustments"])
    print(build_markdown(pending))          # preview: consent shown as PENDING
    # ... only after the person explicitly confirms:
    final = confirm_consent(pending)        # consent given, date, integrity hash
    write_summary(final, "my_summary")      # writes my_summary.md and my_summary.json

Previewed consent: only the CLI flow (``communication_needs_summary_cli``),
which shows the exact preview and requires the person to type ``write``,
counts as previewed consent.  A programmatic call to :func:`confirm_consent`
records consent as given in the document, but it is **not** previewed consent:
code that calls it directly is responsible for showing the person the preview
and obtaining their explicit confirmation first.

Privacy defaults: no export timestamp (opt in with ``include_export_time``) and
entry dates coarsened to month (``date_precision="month"``; ``"day"`` and
``"year"`` are available).
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_ID = "openhear-communication-needs-summary-v1"
SCHEMA_VERSION = 1

#: Path of the JSON Schema shipped with the package.
SCHEMA_PATH = Path(__file__).with_name("communication_needs_summary.schema.json")

#: Sections the person may choose to include, in display order.
SECTIONS: tuple[str, ...] = (
    "display_name",
    "reasonable_adjustments",
    "channels_that_do_not_work_for_me",
    "functional_impact",
    "variation_over_time",
)

#: Default selection: everything except a name, which is opt-in.
DEFAULT_SECTIONS: tuple[str, ...] = tuple(s for s in SECTIONS if s != "display_name")

ADJUSTMENT_CATEGORIES: tuple[str, ...] = (
    "contact_channel",
    "live_communication_support",
    "written_information",
    "time_and_breaks",
    "other",
)

SELF_REPORTED = "self_reported"

#: Allowed date precisions, most to least precise, with output length.
DATE_PRECISIONS: dict[str, int] = {"day": 10, "month": 7, "year": 4}

#: Default precision.  Month keeps the order and recency of entries readable
#: (enough to show how needs vary over time) while making each file less
#: distinctive and less linkable than exact days.  Exact days are opt-in.
DEFAULT_DATE_PRECISION = "month"

CONSENT_STATEMENT = (
    "I have previewed this summary and I chose which sections it includes. "
    "It is written to local files on my device only. Nothing is uploaded. "
    "It is my own document, not a digital ID."
)

DISCLAIMERS: tuple[str, ...] = (
    "Self-reported communication needs, written by the person and held by them.",
    "Not PIP evidence and does not replace any assessment. No descriptor scoring.",
    "Not endorsed by DWP or the Timms Review. Not an official 'Tell Us Once' profile.",
    "Not a medical or clinical document. OpenHear is a research platform for "
    "environmental sound awareness; it is not a hearing aid or a medical device.",
    "Written to local files only. No upload, no account, no central storage.",
    "Contains no hearing test results, diagnosis or identifier, and is not a digital ID.",
    "The optional SHA-256 value is an integrity hash, not a signature.",
)

CLINICIAN_STUB_NOTE = "Not included. The minimal version carries self-reported content only."

# ── Forbidden keys ────────────────────────────────────────────────────────────

#: Whole key names that must never appear anywhere in the output.
FORBIDDEN_KEYS: frozenset[str] = frozenset(
    {
        "subject",
        "clinical_core",
        "classification",
        "date_of_birth",
        "birth_date",
        "national_insurance_number",
        "nhs_number",
        "pure_tone_average",
        "pure_tone_averages",
        "four_frequency_average",
        "right_ear",
        "left_ear",
        "freq_hz",
        "gain_profile",
        "dsp_gain_profile",
        "haptic_layer",
        "haptic_weights",
        "sound_classes",
        "preference_layer",
        "persistent_identifier",
        "cross_service_identifier",
        "history",
    }
)

#: Tokens (split on ``_``, ``-`` and camelCase) that must never appear in a key.
FORBIDDEN_KEY_TOKENS: frozenset[str] = frozenset(
    {
        "id",
        "ids",
        "uuid",
        "guid",
        "identifier",
        "nhs",
        "nino",
        "ni",
        "dob",
        "address",
        "postcode",
        "threshold",
        "thresholds",
        "pta",
        "severity",
        "diagnosis",
        "diagnoses",
        "diagnostic",
        "audiogram",
        "audiometry",
        "hl",
        "db",
        "dbhl",
        "spl",
    }
)

_TOKEN_SPLIT = re.compile(r"[_\-\s.]+|(?<=[a-z0-9])(?=[A-Z])")
_ISO_DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")

# Patterns that, in free text, suggest clinical data or personal details have
# been typed or pasted in.  They only produce a warning for the preview; the
# person's own words are theirs and are never edited.
_CLINICAL_TEXT_HINTS = re.compile(
    r"\b(\d{1,3}\s?dB(\s?HL)?|\d+(\.\d+)?\s?k?Hz|PTA|pure[- ]tone|audiogram|audiometr\w*|"
    r"threshold\w*|hearing test|test results?|diagnos\w*|severity|severe|profound|"
    r"NHS number|National Insurance|NI number|date of birth)\b",
    re.IGNORECASE,
)

#: Personal-detail patterns (label, regex).  Deliberately broad: a false alarm
#: costs a second look; a miss costs a leaked identifier.
_PERSONAL_DETAIL_HINTS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "National Insurance number",
        re.compile(
            r"\b[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z]\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b",
            re.IGNORECASE,
        ),
    ),
    ("email address", re.compile(r"\b[\w.+-]+@[\w-]+(\.[\w-]+)+\b")),
    (
        "phone number",
        re.compile(
            r"(?<![\w])(\+44\s?\(?0?\)?\s?\d{2,4}|\(?0\d{2,4}\)?)[\s-]?\d{3,4}[\s-]?\d{3,4}\b"
        ),
    ),
    ("NHS number", re.compile(r"\b\d{3}[\s-]?\d{3}[\s-]?\d{4}\b")),
    (
        "UK postcode",
        re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b", re.IGNORECASE),
    ),
    (
        "street address",
        re.compile(
            r"\b\d{1,4}[A-Za-z]?,?\s+(?:[A-Z][\w'-]*\s+){1,3}"
            r"(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Close|Drive|Dr|Way|Crescent|Cres|"
            r"Place|Pl|Court|Ct|Terrace|Gardens|Grove|Square|Row|Mews|Walk|Parade)\b"
        ),
    ),
)


def _text_hints(text: str) -> list[str]:
    hints = []
    match = _CLINICAL_TEXT_HINTS.search(text)
    if match:
        hints.append(f"mentions '{match.group(0)}'")
    for label, pattern in _PERSONAL_DETAIL_HINTS:
        if pattern.search(text):
            hints.append(f"may contain a {label}")
    return hints


#: Shown before the free-text preview, every time, whether or not anything is spotted.
FREE_TEXT_WARNING_LINES: tuple[str, ...] = (
    "CHECK YOUR OWN WORDS BEFORE YOU CONFIRM",
    "",
    "This tool never edits or removes anything you typed.",
    "Your free text is written exactly as it is, including anything",
    "clinical you may have pasted in, for example:",
    "  - hearing test results or audiogram figures",
    "  - dB or Hz values (e.g. '70 dB HL', '4 kHz')",
    "  - diagnoses, severity words (e.g. 'severe', 'profound')",
    "  - NHS or National Insurance numbers, date of birth",
    "  - addresses, postcodes, phone numbers, email addresses",
    "If you do not want any of that in the file, cancel, edit your",
    "self-report file, and run this again.",
)


def free_text_warning_box(doc: dict[str, Any]) -> str:
    """Return a boxed warning about free text, listing anything spotted in *doc*."""
    lines = list(FREE_TEXT_WARNING_LINES)
    spotted = clinical_text_warnings(doc)
    if spotted:
        lines += ["", "Spotted in your text (left unchanged):"]
        lines += [f"  * {w}" for w in spotted]
    width = max(len(line) for line in lines) + 2
    out = ["!" * (width + 2)]
    out += [f"!{(' ' + line).ljust(width)}!" for line in lines]
    out.append("!" * (width + 2))
    return "\n".join(out)


def _key_tokens(key: str) -> list[str]:
    return [t.lower() for t in _TOKEN_SPLIT.split(key) if t]


def is_forbidden_key(key: str) -> bool:
    """Return True if *key* names data a communication-needs summary must never hold."""
    lowered = key.lower()
    if lowered in FORBIDDEN_KEYS:
        return True
    return any(tok in FORBIDDEN_KEY_TOKENS for tok in _key_tokens(key))


def find_forbidden_keys(obj: Any, _path: str = "$") -> list[str]:
    """Return JSON paths of every forbidden key found anywhere in *obj*."""
    found: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{_path}.{key}"
            if is_forbidden_key(str(key)):
                found.append(path)
            found.extend(find_forbidden_keys(value, path))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            found.extend(find_forbidden_keys(value, f"{_path}[{i}]"))
    return found


def clinical_text_warnings(doc: dict[str, Any]) -> list[str]:
    """Return free-text locations that look like clinical data or personal details.

    This is advisory only and shown in the preview.  Nothing is removed from
    the person's own words.
    """
    warnings: list[str] = []

    def _walk(obj: Any, path: str) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("disclaimers", "consent", "integrity", "clinician_sourced"):
                    continue
                _walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _walk(v, f"{path}[{i}]")
        elif isinstance(obj, str):
            for hint in _text_hints(obj):
                warnings.append(f"{path}: {hint}")

    _walk(doc, "$")
    return warnings


# ── Source extraction ─────────────────────────────────────────────────────────


def extract_self_report(source: dict[str, Any]) -> dict[str, Any]:
    """Return the self-reported communication-needs block from *source*.

    *source* may be either a standalone self-report document or a Living
    Hearing Profile carrying a ``communication_needs`` block.  Nothing else in
    a Living Hearing Profile is read.
    """
    if not isinstance(source, dict):
        raise ValueError("Source must be a JSON object.")
    block = source.get("communication_needs", source)
    if not isinstance(block, dict):
        raise ValueError("'communication_needs' must be a JSON object.")
    return block


def available_sections(source: dict[str, Any]) -> list[str]:
    """Return the sections that have content in *source*, in display order."""
    block = extract_self_report(source)
    return [s for s in SECTIONS if block.get(s)]


def _check_date(value: Any, where: str) -> str:
    if not isinstance(value, str) or not _ISO_DATE.match(value):
        raise ValueError(f"{where}: expected a date as YYYY-MM-DD, YYYY-MM or YYYY, got {value!r}.")
    padded = value + "-01-01"[len(value) - 4 :] if len(value) < 10 else value
    try:
        date.fromisoformat(padded)
    except ValueError as exc:
        raise ValueError(f"{where}: invalid date {value!r}.") from exc
    return value


def coarsen_date(value: str, precision: str) -> str:
    """Reduce an ISO date to *precision* (``day``, ``month`` or ``year``).

    A date already coarser than *precision* is returned unchanged; precision
    is never invented.
    """
    if precision not in DATE_PRECISIONS:
        raise ValueError(f"Unknown date precision {precision!r}.")
    return value[: DATE_PRECISIONS[precision]]


def _text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}: expected non-empty text.")
    return value.strip()


def _provenance(item: dict[str, Any], where: str, precision: str) -> dict[str, str]:
    prov = item.get("provenance")
    if not isinstance(prov, dict):
        raise ValueError(f"{where}: every item needs a 'provenance' object.")
    source_type = prov.get("source_type")
    if source_type != SELF_REPORTED:
        raise ValueError(
            f"{where}: source_type must be '{SELF_REPORTED}' in this version, "
            f"got {source_type!r}. Clinician-sourced items are not supported."
        )
    out = {
        "source_type": SELF_REPORTED,
        "recorded_on": coarsen_date(
            _check_date(prov.get("recorded_on"), f"{where}.recorded_on"), precision
        ),
    }
    if prov.get("last_reviewed") is not None:
        out["last_reviewed"] = coarsen_date(
            _check_date(prov["last_reviewed"], f"{where}.last_reviewed"), precision
        )
    return out


def _adjustments(items: Any, precision: str) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        raise ValueError("reasonable_adjustments must be a list.")
    out = []
    for i, item in enumerate(items):
        where = f"reasonable_adjustments[{i}]"
        if not isinstance(item, dict):
            raise ValueError(f"{where}: expected an object.")
        category = item.get("category", "other")
        if category not in ADJUSTMENT_CATEGORIES:
            raise ValueError(f"{where}.category: unknown category {category!r}.")
        if "is_reasonable_adjustment" not in item:
            raise ValueError(
                f"{where}.is_reasonable_adjustment is required: say explicitly whether "
                "this is a reasonable adjustment (true) or a preference (false)."
            )
        is_ra = item["is_reasonable_adjustment"]
        if not isinstance(is_ra, bool):
            raise ValueError(
                f"{where}.is_reasonable_adjustment must be true or false, got {is_ra!r}."
            )
        out.append(
            {
                "description": _text(item.get("description"), f"{where}.description"),
                "category": category,
                "is_reasonable_adjustment": is_ra,
                "provenance": _provenance(item, where, precision),
            }
        )
    return out


def _channels(items: Any, precision: str) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        raise ValueError("channels_that_do_not_work_for_me must be a list.")
    out = []
    for i, item in enumerate(items):
        where = f"channels_that_do_not_work_for_me[{i}]"
        if not isinstance(item, dict):
            raise ValueError(f"{where}: expected an object.")
        entry = {"channel": _text(item.get("channel"), f"{where}.channel")}
        if item.get("in_my_own_words"):
            entry["in_my_own_words"] = _text(item["in_my_own_words"], f"{where}.in_my_own_words")
        entry["provenance"] = _provenance(item, where, precision)
        out.append(entry)
    return out


def _impact(item: Any, precision: str) -> dict[str, Any]:
    where = "functional_impact"
    if not isinstance(item, dict):
        raise ValueError(f"{where}: expected an object.")
    out: dict[str, Any] = {
        "in_my_own_words": _text(item.get("in_my_own_words"), f"{where}.in_my_own_words")
    }
    for key in ("what_helps", "what_does_not_help"):
        if item.get(key):
            values = item[key]
            if not isinstance(values, list):
                raise ValueError(f"{where}.{key} must be a list of text.")
            out[key] = [_text(v, f"{where}.{key}[{j}]") for j, v in enumerate(values)]
    out["provenance"] = _provenance(item, where, precision)
    return out


def _variation(items: Any, precision: str) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        raise ValueError("variation_over_time must be a list.")
    out = []
    for i, item in enumerate(items):
        where = f"variation_over_time[{i}]"
        if not isinstance(item, dict):
            raise ValueError(f"{where}: expected an object.")
        out.append(
            {
                "recorded_on": coarsen_date(
                    _check_date(item.get("recorded_on"), f"{where}.recorded_on"), precision
                ),
                "in_my_own_words": _text(item.get("in_my_own_words"), f"{where}.in_my_own_words"),
                "provenance": _provenance(item, where, precision),
            }
        )
    return sorted(out, key=lambda e: e["recorded_on"])


_BUILDERS = {
    "reasonable_adjustments": _adjustments,
    "channels_that_do_not_work_for_me": _channels,
    "functional_impact": _impact,
    "variation_over_time": _variation,
}


# ── Build, render, hash, write ────────────────────────────────────────────────


def canonical_json(doc: dict[str, Any]) -> bytes:
    """Canonical UTF-8 JSON of *doc* without its ``integrity`` field."""
    body = {k: v for k, v in doc.items() if k != "integrity"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def integrity_hash(doc: dict[str, Any]) -> str:
    """SHA-256 hex digest of :func:`canonical_json` (an integrity hash only)."""
    return hashlib.sha256(canonical_json(doc)).hexdigest()


def verify_integrity(doc: dict[str, Any]) -> bool:
    """Return True if *doc* carries an integrity hash that matches its content.

    A match only shows the JSON has not changed since the hash was computed.
    It says nothing about who wrote it or whether the content is true.
    """
    block = doc.get("integrity")
    if not isinstance(block, dict) or block.get("algorithm") != "SHA-256":
        return False
    return block.get("value") == integrity_hash(doc)


def build_summary(
    source: dict[str, Any],
    *,
    include: Iterable[str] | None = None,
    include_export_time: bool = False,
    date_precision: str = DEFAULT_DATE_PRECISION,
    language: str = "en-GB",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build a **pending** ``openhear-communication-needs-summary-v1`` document for preview.

    Only allow-listed, self-reported fields are copied.  Everything else in
    *source* is ignored.  Consent is recorded as pending and there is no
    integrity hash yet: call :func:`confirm_consent` only after the person has
    seen the preview and explicitly confirmed.

    Args:
        source:              Standalone self-report, or a Living Hearing Profile
                             with a ``communication_needs`` block.
        include:             Sections the person chose (see :data:`SECTIONS`).
                             Defaults to :data:`DEFAULT_SECTIONS` that have content.
        include_export_time: Add an ``exported_at`` timestamp.  Off by default.
        date_precision:      ``"month"`` (default), ``"day"`` or ``"year"`` for
                             recorded, last-reviewed and variation dates.
        language:            BCP 47 language tag of the content.
        now:                 Export time (for tests); defaults to now, UTC.

    Raises:
        ValueError: on unknown sections, unknown precision, malformed items, or
            non-self-reported provenance.
    """
    if date_precision not in DATE_PRECISIONS:
        raise ValueError(
            f"Unknown date precision {date_precision!r}; use one of {', '.join(DATE_PRECISIONS)}."
        )
    block = extract_self_report(source)
    chosen = list(DEFAULT_SECTIONS if include is None else include)
    unknown = [s for s in chosen if s not in SECTIONS]
    if unknown:
        raise ValueError(f"Unknown section(s): {', '.join(unknown)}.")
    chosen = [s for s in SECTIONS if s in chosen and block.get(s)]

    doc: dict[str, Any] = {"schema": SCHEMA_ID, "schema_version": SCHEMA_VERSION}
    if include_export_time:
        when = (now or datetime.now(tz=timezone.utc)).replace(microsecond=0)
        doc["exported_at"] = when.isoformat()
    doc.update(
        {
            "language": language,
            "date_precision": date_precision,
            "disclaimers": list(DISCLAIMERS),
            "consent": {
                "status": "pending",
                "given": False,
                "given_at": None,
                "statement": CONSENT_STATEMENT,
                "preview_confirmed": False,
                "destination": "local_files_only",
                "upload_performed": False,
                "sections_included": chosen,
                "sections_not_included": [s for s in SECTIONS if s not in chosen],
            },
        }
    )
    if "display_name" in chosen:
        doc["display_name"] = _text(block["display_name"], "display_name")
    for section in SECTIONS[1:]:
        if section in chosen:
            doc[section] = _BUILDERS[section](block[section], date_precision)
    doc["clinician_sourced"] = {"included": False, "note": CLINICIAN_STUB_NOTE}

    bad = find_forbidden_keys(doc)
    if bad:  # pragma: no cover - allow-list makes this unreachable; kept as a guard
        raise ValueError(f"Forbidden keys in summary: {', '.join(bad)}")
    return doc


def confirm_consent(
    pending: dict[str, Any],
    *,
    with_integrity_hash: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Record consent on a previewed document.  Call only after explicit confirmation.

    Returns a new document with consent ``given``, the preview marked as
    confirmed, and (optionally) the integrity hash.  ``given_at`` is a full
    UTC timestamp only if the person opted in to an export timestamp;
    otherwise it is the date at the document's ``date_precision``, so the
    consent record does not reintroduce an exact time.
    """
    consent = pending.get("consent") or {}
    if consent.get("status") != "pending":
        raise ValueError("Consent can only be confirmed on a pending document.")
    doc = copy.deepcopy(pending)
    when = (now or datetime.now(tz=timezone.utc)).replace(microsecond=0)
    if "exported_at" in doc:
        given_at = when.isoformat()
    else:
        given_at = coarsen_date(when.date().isoformat(), doc["date_precision"])
    doc["consent"].update(
        {"status": "given", "given": True, "given_at": given_at, "preview_confirmed": True}
    )
    if with_integrity_hash:
        doc["integrity"] = {
            "algorithm": "SHA-256",
            "encoding": "hex",
            "canonical_form": (
                "UTF-8 JSON of this document without the integrity field, "
                "keys sorted, separators (',', ':')"
            ),
            "label": "integrity hash - not a signature, not a certificate, not a digital ID",
            "value": integrity_hash(doc),
        }
    return doc


_SECTION_TITLES = {
    "reasonable_adjustments": "Reasonable adjustments",
    "channels_that_do_not_work_for_me": "Channels that do not work for me",
    "functional_impact": "Day-to-day impact, in my own words",
    "variation_over_time": "How this varies over time",
}


_PRECISION_LABELS = {
    "day": "day (YYYY-MM-DD)",
    "month": "month (YYYY-MM)",
    "year": "year (YYYY)",
}


def _prov_line(prov: dict[str, str]) -> str:
    text = f"_Self-reported. Recorded {prov['recorded_on']}"
    if prov.get("last_reviewed"):
        text += f"; last reviewed {prov['last_reviewed']}"
    return text + "._"


def build_markdown(doc: dict[str, Any]) -> str:
    """Render the exact Markdown that :func:`write_summary` will write."""
    lines: list[str] = []
    title = "Communication-needs summary"
    if doc.get("display_name"):
        title += f" — {doc['display_name']}"
    lines += [f"# {title}", ""]
    for d in doc["disclaimers"]:
        lines.append(f"> {d}")
    lines += [
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Format | `{doc['schema']}` (version {doc['schema_version']}) |",
    ]
    if doc.get("exported_at"):
        lines.append(f"| Exported | {doc['exported_at']} |")
    lines += [
        f"| Dates shown to | {_PRECISION_LABELS[doc['date_precision']]} |",
        f"| Language | {doc['language']} |",
        "",
    ]

    if doc.get("reasonable_adjustments"):
        lines += [f"## {_SECTION_TITLES['reasonable_adjustments']}", ""]
        for item in doc["reasonable_adjustments"]:
            tag = (
                " (reasonable adjustment)" if item["is_reasonable_adjustment"] else " (preference)"
            )
            lines.append(f"- {item['description']}{tag}  ")
            lines.append(f"  {_prov_line(item['provenance'])}")
        lines.append("")

    if doc.get("channels_that_do_not_work_for_me"):
        lines += [f"## {_SECTION_TITLES['channels_that_do_not_work_for_me']}", ""]
        for item in doc["channels_that_do_not_work_for_me"]:
            extra = f" — {item['in_my_own_words']}" if item.get("in_my_own_words") else ""
            lines.append(f"- **{item['channel']}**{extra}  ")
            lines.append(f"  {_prov_line(item['provenance'])}")
        lines.append("")

    impact = doc.get("functional_impact")
    if impact:
        lines += [f"## {_SECTION_TITLES['functional_impact']}", "", impact["in_my_own_words"], ""]
        if impact.get("what_helps"):
            lines += ["**What helps**", ""] + [f"- {v}" for v in impact["what_helps"]] + [""]
        if impact.get("what_does_not_help"):
            lines += ["**What does not help**", ""]
            lines += [f"- {v}" for v in impact["what_does_not_help"]] + [""]
        lines += [_prov_line(impact["provenance"]), ""]

    if doc.get("variation_over_time"):
        lines += [f"## {_SECTION_TITLES['variation_over_time']}", ""]
        for item in doc["variation_over_time"]:
            lines.append(f"- **{item['recorded_on']}** — {item['in_my_own_words']}  ")
            lines.append(f"  {_prov_line(item['provenance'])}")
        lines.append("")

    consent = doc["consent"]
    lines += ["## Consent", "", f"> {consent['statement']}", ""]
    if consent.get("status") == "given":
        lines += [
            f"- Status: given ({consent['given_at']})",
            "- Preview confirmed: yes",
        ]
    else:
        lines += [
            "- Status: **PENDING — not given.** Consent is recorded only after you "
            "type `write` to confirm. Nothing has been written.",
            "- Preview confirmed: not yet",
        ]
    lines += [
        "- Destination: local files only. Upload performed: no.",
        f"- Sections included: {', '.join(consent['sections_included']) or 'none'}",
        f"- Sections not included: {', '.join(consent['sections_not_included']) or 'none'}",
        "",
    ]
    integ = doc.get("integrity")
    if integ:
        lines += [
            "## Integrity hash",
            "",
            f"SHA-256 of the canonical JSON companion file: `{integ['value']}`",
            "",
            "This is an integrity hash. It shows whether the JSON has changed since "
            "export. It is not a signature, not proof of who wrote it, and not a digital ID.",
            "",
        ]
    return "\n".join(lines)


def build_json_text(doc: dict[str, Any]) -> str:
    """Render the exact JSON text that :func:`write_summary` will write."""
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def validate_document(doc: dict[str, Any]) -> None:
    """Minimal structural checks that do not need a JSON Schema library."""
    if doc.get("schema") != SCHEMA_ID:
        raise ValueError(f"Unsupported schema: {doc.get('schema')!r}.")
    version = doc.get("schema_version")
    if not isinstance(version, int) or version < 1 or version > SCHEMA_VERSION:
        raise ValueError(f"Unsupported schema_version: {version!r}.")
    bad = find_forbidden_keys(doc)
    if bad:
        raise ValueError(f"Forbidden keys present: {', '.join(bad)}.")
    if doc.get("date_precision") not in DATE_PRECISIONS:
        raise ValueError(f"Unknown date_precision: {doc.get('date_precision')!r}.")
    consent = doc.get("consent") or {}
    if consent.get("destination") != "local_files_only" or consent.get("upload_performed"):
        raise ValueError("Consent block must record local files only and no upload.")
    if doc.get("clinician_sourced", {}).get("included"):
        raise ValueError("Clinician-sourced content is not supported in this version.")


def write_summary(
    doc: dict[str, Any],
    output_path: str | Path,
    *,
    overwrite: bool = False,
) -> tuple[Path, Path]:
    """Write *doc* as ``<output_path>.md`` and ``<output_path>.json`` locally.

    Refuses to write unless :func:`confirm_consent` has recorded consent.
    Refuses to overwrite existing files unless *overwrite* is True.

    Returns:
        The Markdown and JSON paths written.
    """
    consent = doc.get("consent") or {}
    if not (
        consent.get("status") == "given"
        and consent.get("given") is True
        and consent.get("preview_confirmed") is True
        and consent.get("given_at")
    ):
        raise PermissionError(
            "Consent has not been given. Confirm the preview (confirm_consent) before writing."
        )
    validate_document(doc)

    base = Path(output_path)
    if base.suffix in (".md", ".json"):
        base = base.with_suffix("")
    md_path = base.with_name(base.name + ".md")
    json_path = base.with_name(base.name + ".json")
    if not overwrite:
        existing = [p for p in (md_path, json_path) if p.exists()]
        if existing:
            raise FileExistsError(f"Refusing to overwrite: {', '.join(map(str, existing))}")

    md_text = build_markdown(doc)
    json_text = build_json_text(copy.deepcopy(doc))
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md_text)
    with open(json_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json_text)
    return md_path, json_path
