# Communication-needs summary (`openhear-communication-needs-summary-v1`)

> **Status: draft, not released.** Awaiting maintainer review and a hostile-reviewer pass.

A small, optional export that lets a person write down their own communication needs once,
preview it, and keep it as a local Markdown and JSON file. They decide whether to print it,
attach it to their own correspondence, or do nothing with it.

OpenHear's intended purpose does not change. OpenHear is a research platform that turns the
wearer's own audiogram into haptic patterns for environmental sound awareness. It is not a
certified medical device, not a hearing aid, and not a replacement for clinical care. See
[INTENDED_PURPOSE.md](INTENDED_PURPOSE.md). This export is a convenience for writing down
self-reported needs. It adds no clinical claim.

## What it contains

Self-reported content only. Every item carries provenance (`source_type: self_reported`) and
the date it was recorded, with an optional last-reviewed date. Dates are shown to the month by
default (see [Dates and timestamps](#dates-and-timestamps)).

| Section | Content |
|---------|---------|
| `reasonable_adjustments` | Free-text adjustments, each with a category and a **required** `is_reasonable_adjustment` (`true` or `false`, never assumed). This lets the person mark, for example, a contact channel such as email as a reasonable adjustment rather than a preference, or mark something as a preference. Live speech-to-text or a palantypist goes under `live_communication_support`. The exporter rejects an adjustment without an explicit `true` or `false`. |
| `channels_that_do_not_work_for_me` | Channels that do not work for this person, optionally in their own words. This is personal, not a general rule. |
| `functional_impact` | Day-to-day impact in the person's own words, with optional "what helps" and "what does not help" lists. |
| `variation_over_time` | Dated entries in the person's own words. No automatic better or worse score. |
| `display_name` | Optional and off by default. |
| `consent` | `status` (`pending` in the preview, `given` in a written file), `given_at`, preview confirmed, sections included and left out, destination `local_files_only`, `upload_performed: false`. |
| `date_precision` | `month` (default), `day` or `year`: the most precise any entry date is shown. |
| `exported_at` | Optional and off by default. |
| `clinician_sourced` | Fixed stub, `included: false`. There is no clinician section in this version. |
| `integrity` | Optional SHA-256 integrity hash (see below). |

## What it never contains

- Hearing thresholds, pure-tone averages, severity labels, or diagnosis.
- DSP gain, haptic weights, or anything else from the Living Hearing Profile's clinical core.
- Any persistent or linking identifier: no record ID, NHS number, National Insurance number,
  date of birth, or address.

The exporter copies fields from an explicit allow-list, so anything else in the source is
dropped, including a full Living Hearing Profile with a clinical core. An independent key scan
runs before every write and refuses to write if a forbidden key is present. The JSON Schema
sets `additionalProperties: false` everywhere. `tests/test_communication_needs_summary.py` fails if a
forbidden key reaches the output, including when the source profile holds one.

Free text is the person's own words and is **never edited or removed**. Before the preview, the
CLI always shows a boxed warning saying so, with examples of what to check for: hearing test
results or audiogram figures, dB or Hz values, diagnoses and severity words, NHS or National
Insurance numbers, date of birth, addresses, postcodes, phone numbers and email addresses. The
scanner also looks for raw National Insurance numbers, NHS numbers, UK postcodes, street
addresses, phone numbers and email addresses. If the text appears to contain any of these, the
box lists where, and leaves the text unchanged. The scanner is deliberately broad and will
sometimes flag harmless text; it is a prompt to check, not a filter. The person can cancel, edit their self-report and run it again.

## How to use it

Write a self-report JSON file (see the fictional
[`examples/communication_needs_summary/alex_example_self_report.json`](../examples/communication_needs_summary/alex_example_self_report.json)),
or add the same content as a `communication_needs` block in your Living Hearing Profile. Then:

```bash
python -m audiogram.communication_needs_summary_cli my_self_report.json --out my_summary
```

1. You choose each section (or pre-select with `--include`). A name is off unless you choose it.
2. The CLI shows the boxed free-text warning.
3. The CLI prints the Markdown and JSON it will write, with consent shown as **PENDING**.
4. You type `write` to give consent. Anything else cancels: consent is not given and nothing is
   written.
5. Only then is consent recorded as given, with its date, and the optional integrity hash added.
   Those are the only differences from the preview, and the CLI says so before you confirm.
6. `my_summary.md` and `my_summary.json` are written on your device. Existing files are not
   overwritten unless you pass `--overwrite`.

A written file always says consent was given. The exporter refuses to write a document whose
consent is still pending.

**Only this CLI flow counts as previewed consent.** Code that calls `confirm_consent()` directly
records consent as given in the document, but that is not previewed consent: the calling code is
responsible for showing the person the exact preview and getting their explicit confirmation
first.

## Dates and timestamps

- **No export timestamp by default.** `--include-export-time` adds `exported_at`.
- **Entry dates shown to the month by default** (`YYYY-MM`). `--date-precision day` keeps full
  dates and `--date-precision year` shows the year only. This applies to recorded, last-reviewed
  and variation dates. A date already less precise than the setting is kept as it is; precision is
  never invented.
- **Consent date follows the same rule.** `given_at` is a full timestamp only if you opted in to
  the export time; otherwise it is the date at the chosen precision.

Why month by default: a variation-over-time record needs order and rough recency to be useful
("on tired days" in October versus November), and month keeps that. Exact days and times make a
file more distinctive and easier to link with other records, which is what this export avoids.
Year alone loses most of the sense of change over time. Full dates are one flag away for anyone
who needs them.

No network calls are made. The modules import nothing that opens a connection, and the tests
block sockets while running the CLI.

## Integrity hash, not a signature

With the default settings the JSON carries a SHA-256 **integrity hash** over the canonical JSON
of the document without the `integrity` field (UTF-8, keys sorted, separators `,` and `:`). It
helps the holder notice whether the file has changed since export. `--no-hash` leaves it out.

It is not a signature. It is not cryptographic proof of who wrote the file or that the content is
true. It is not a certificate and not a digital ID. Anyone can recompute it after editing the file.

## Do not claim

Do not say, imply, or let docs, posts or emails be read as saying any of the following:

1. That DWP or the Timms Review has endorsed, accepted or adopted OpenHear or this export.
   The Review's recommendations are those of its steering group and are not government policy.
2. That this is the official "Tell Us Once" profile, or that such a DWP profile exists today.
3. That this is PIP evidence, that it proves entitlement, or that it replaces any assessment.
4. That it scores, predicts or maps to PIP descriptors. It does no descriptor scoring.
5. That it is a medical device, a clinical document, or clinical advice. OpenHear is for
   environmental sound awareness. It is not a hearing aid.
6. That the integrity hash is a signature, a certificate, or cryptographic proof.
7. That the file is a digital ID or identity credential.
8. That the data is stored centrally. There is no server, account, upload or central storage.

## UK GDPR Article 9 note (not legal advice)

**This is not legal advice.** Information about a person's health or disability, including
their communication needs, is likely to be special category data under Article 9 of the UK GDPR.
This export keeps that data on the person's own device and under their control. If the person
chooses to send the file to an organisation, that organisation's own lawful basis and Article 9
condition apply to what it receives; OpenHear does not process or receive it. Anyone building a
service that receives or stores these files should take their own data-protection advice.

## Scope of this version

Minimal version only. Not included: a clinician-sourced section, a graphical interface, any
sending or sharing path, a verification service, or integration with any government system.
Any later path that sends the file anywhere would need a fresh privacy review.

## Files

- `audiogram/communication_needs_summary.py` — build, render, hash and write.
- `audiogram/communication_needs_summary_cli.py` — consent-and-preview CLI.
- `audiogram/communication_needs_summary.schema.json` — JSON Schema for `openhear-communication-needs-summary-v1`.
- `examples/communication_needs_summary/` — one fictional example ("Alex Example"), input and output.
- `tests/test_communication_needs_summary.py` — tests.
