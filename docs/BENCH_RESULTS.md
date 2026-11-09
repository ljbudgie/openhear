# Bench results — classifier only

**Status:** Pending workflow run. No measured numbers have been committed yet.

This file will hold the output of `scripts/bench_awareness.py` once the GitHub Actions workflow (`.github/workflows/bench-awareness.yml`) has been run. The workflow downloads the official YAMNet TFLite model and the ESC-50 recordings at runtime. No audio is committed to the repository.

## What the bench measures

- Hit rate per supported class (with 95% Wilson interval)
- What each miss was classified as
- False-alert rate on negative clips
- Threshold table from 0.10 to 0.50

## Limits (will be restated with the numbers)

- Recorded clips only
- Classifier only
- No wearers
- No real rooms
- Not a clinical result
- ESC-50 has no doorbell or speech class, so no figure will be invented for those

Once the workflow has run, paste the signed JSON summary here and update this status line.
