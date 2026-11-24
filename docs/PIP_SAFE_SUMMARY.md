# Communication needs summary (`openhear-pip-safe-summary-v1`)

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
the date it was recorded, with an optional last-reviewed date.

| Section | Content |
|---------|---------|
| `reasonable_adjustments` | Free-text adjustments, each with a category and `is_reasonable_adjustment`. Email-only contact can be recorded as a reasonable adjustment, not a preference. Live speech-to-text or a palantypist goes under `live_communication_support`. |
| `channels_that_do_not_work_for_me` | Channels that do not work for this person, optionally in their own words. This is personal, not a general rule. |
| `functional_impact` | Day-to-day impact in the person's own words, with optional "what helps" and "what does not help" lists. |
| `variation_over_time` | Dated entries in the person's own words. No automatic better or worse score. |
| `display_name` | Optional and off by default. |
| `consent` | What the person confirmed: preview seen, sections included and left out, destination `local_files_only`, `upload_performed: false`. |
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
sets `additionalProperties: false` everywhere. `tests/test_pip_safe_summary.py` fails if a
forbidden key reaches the output, including when the source profile holds one.

Free text is the person's own words and is not edited. If it looks like clinical data has been
pasted in (for example "dB HL" or "PTA"), the preview shows a note so the person can decide.

## How to use it

Write a self-report JSON file (see the fictional
[`examples/pip_safe_summary/alex_example_self_report.json`](../examples/pip_safe_summary/alex_example_self_report.json)),
or add the same content as a `communication_needs` block in your Living Hearing Profile. Then:

```bash
python -m audiogram.pip_safe_summary_cli my_self_report.json --out my_summary
```

1. You choose each section (or pre-select with `--include`). A name is off unless you choose it.
2. The CLI prints the exact Markdown and JSON it will write.
3. You type `write` to confirm. Anything else cancels and nothing is written.
4. `my_summary.md` and `my_summary.json` are written on your device. Existing files are not
   overwritten unless you pass `--overwrite`.

The consent block shown in the preview already reads "given". That is deliberate: the preview
is byte-for-byte what will be written, and it is only written if you confirm.

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

- `audiogram/pip_safe_summary.py` — build, render, hash and write.
- `audiogram/pip_safe_summary_cli.py` — consent-and-preview CLI.
- `audiogram/pip_safe_summary.schema.json` — JSON Schema for `openhear-pip-safe-summary-v1`.
- `examples/pip_safe_summary/` — one fictional example ("Alex Example"), input and output.
- `tests/test_pip_safe_summary.py` — tests.
