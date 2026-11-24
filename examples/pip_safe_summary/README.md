# Communication needs summary — fictional example

**Everything in this folder is fictional.** "Alex Example" is not a real person and
none of the content is real data.

| File | What it is |
|------|------------|
| `alex_example_self_report.json` | Fictional self-reported input. |
| `alex_example_pip_safe_summary.md` | Markdown output, exactly as the exporter writes it. |
| `alex_example_pip_safe_summary.json` | `openhear-pip-safe-summary-v1` JSON output, with the optional integrity hash. |

Regenerate locally (the CLI shows a preview and asks you to type `write`):

```bash
python -m audiogram.pip_safe_summary_cli examples/pip_safe_summary/alex_example_self_report.json \
    --out /tmp/alex_example_pip_safe_summary --include display_name \
    --include reasonable_adjustments --include channels_that_do_not_work_for_me \
    --include functional_impact --include variation_over_time
```

The committed example was built with a fixed export time (2026-11-24T20:00:00+00:00) so
that its integrity hash is reproducible in `tests/test_pip_safe_summary.py`.

What this is and is not: see [`docs/PIP_SAFE_SUMMARY.md`](../../docs/PIP_SAFE_SUMMARY.md).
