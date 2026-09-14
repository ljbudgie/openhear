# Measurement context

A Living Hearing Profile must not treat a single audiogram as the person.

## Rule

When a threshold graph is ingested, record *how the test was taken* as a first-class field, not a footnote.

In scope:

- Severe tinnitus on the test day
- Fatigue or illness at the session
- First test versus a known previous graph that has moved
- Aids in or out during the booth test, if known
- Speech-banana overlay: which phonemes sit above the measured line

Out of scope in the public tree: names, clinic identifiers, device serials, appointment diaries, dates of birth.

## Why it belongs

A graph taken in a bad tinnitus week can look like progression. Without the context field, the next clinician, or the DSP, will treat the worse numbers as the new baseline. The profile should say: these thresholds were measured under X. Recheck when X is quieter.

The speech-banana overlay is the same idea applied to *what the person cannot collect*. Vowels and low consonants can remain on the page while s, f and th sit above the line. A general lip-reading class then feels like failure. The profile should name the missing set so practice can target those shapes, including with a familiar face rather than a long course.

This is user-declared. It is not inferred from the image by a clinic cloud.

## Anonymised shapes added from consented panel correspondence

**Flat-ish moderate-to-severe through the speech frequencies, with a further drop at 8 kHz.** Distinct from a steep industrial slope (preserved lows, cliff after 500–750 Hz). DSP implication: broadband lift rather than a high-frequency-only shelf; watch residual dynamic range; do not discard a prior graph because one noisy-tinnitus session moved the points.

**Sloping moderate-to-severe, high-frequency drop, speech-banana consonants above the line.** Adult long-term aid user. Approximate PTA mid-50s to mid-60s; right a little worse than left at 4–8 kHz. Distinct from the flat-ish shape above and from the industrial cliff. DSP implication: preserve low-to-mid speech; do not treat residual vowel hearing as proof that s / f / th are available; haptic or visual second channel still earns its place when aids are out. No name, date of birth or clinic header in this tree.
