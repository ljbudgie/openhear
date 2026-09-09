# Measurement context

A Living Hearing Profile must not treat a single audiogram as the person.

## Rule

When a threshold graph is ingested, record *how the test was taken* as a first-class field, not a footnote.

In scope:

- Severe tinnitus on the test day
- Fatigue or illness at the session
- First test versus a known previous graph that has moved
- Aids in or out during the booth test, if known

Out of scope in the public tree: names, clinic identifiers, device serials, appointment diaries.

## Why it belongs

A graph taken in a bad tinnitus week can look like progression. Without the context field, the next clinician, or the DSP, will treat the worse numbers as the new baseline. The profile should say: these thresholds were measured under X. Recheck when X is quieter.

This is user-declared. It is not inferred from the image.

## Anonymised shape added from consented panel correspondence

**Flat-ish moderate-to-severe through the speech frequencies, with a further drop at 8 kHz.** Distinct from a steep industrial slope (preserved lows, cliff after 500–750 Hz). DSP implication: broadband lift rather than a high-frequency-only shelf; watch residual dynamic range; do not discard a prior graph because one noisy-tinnitus session moved the points.
