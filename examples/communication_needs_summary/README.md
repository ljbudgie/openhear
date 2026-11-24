# Communication-needs summary — fictional example

**Everything in this folder is fictional.** "Alex Example" is not a real person and
none of the content is real data.

| File | What it is |
|------|------------|
| `alex_example_self_report.json` | Fictional self-reported input. |
| `alex_example_communication_needs_summary.md` | Markdown output, exactly as the exporter writes it. |
| `alex_example_communication_needs_summary.json` | `openhear-communication-needs-summary-v1` JSON output, with the optional integrity hash. |

Regenerate locally (the CLI shows a preview and asks you to type `write`):

```bash
python -m audiogram.communication_needs_summary_cli examples/communication_needs_summary/alex_example_self_report.json \
    --out /tmp/alex_example_communication_needs_summary --include display_name \
    --include reasonable_adjustments --include channels_that_do_not_work_for_me \
    --include functional_impact --include variation_over_time
```

The source self-report input (`alex_example_self_report.json`) holds **exact dates**
(YYYY-MM-DD). The export coarsens them to the month by default, so the output shows only
YYYY-MM. Keep the input file private if exact dates matter to you; only the exported files are
meant to leave your hands, and only if you choose.

The example deliberately shows one item marked as a preference
(`"is_reasonable_adjustment": false`). Every adjustment must say `true` or `false` explicitly.

The committed example uses the privacy defaults: no export timestamp, and dates shown to the
month. It was built with a fixed clock (2026-11-24, UTC) so that the consent date and integrity
hash are reproducible in `tests/test_communication_needs_summary.py`.

What this is and is not: see [`docs/COMMUNICATION_NEEDS_SUMMARY.md`](../../docs/COMMUNICATION_NEEDS_SUMMARY.md).
