# Bench plan for the input probes — written before any run

**Status:** Committed before either probe was run on any dataset. The commit that adds this file contains no results.

Scope is unchanged: environmental sound awareness only. Not a hearing aid. Not a medical device. Classifier only, on recorded clips: no wearers, no real rooms, not a clinical result. Nothing here has been independently reviewed.

## Why

The v1.9.0 rules work ([BENCH_PLAN_v1.9.md](BENCH_PLAN_v1.9.md), results in [BENCH_RESULTS.md](BENCH_RESULTS.md)) found that horn misses are not a decision-rule problem: in most missed clips the model reports no horn at all. Two things happen to the audio before the model sees it, and neither has been measured:

1. **Window position.** Clips are cut into fixed 0.975 s windows from the start. A short sound that straddles a window edge is split across two windows.
2. **Resampling.** The shipped code converts audio to 16 kHz by linear interpolation with no low-pass filter. Content above 8 kHz in a 44.1 kHz or 48 kHz recording folds back into the band the model hears.

The idea for both probes came from an earlier session's unmerged patch. The code here is written against the current bench.

## The three inputs

Every clip in every dataset is scored three ways with the same model, label map (v1.8.0) and threshold (0.20). Rule V3 is off.

| Name | What changes |
|---|---|
| `shipped` | Nothing. This must reproduce the signed v1.8.0 figures. |
| `shifted` | Windows start half a window (0.4875 s) later. |
| `bandlimited` | The clip is resampled to 16 kHz with a band-limited polyphase filter (`scipy.signal.resample_poly`) before windowing. |

## What will be reported

For each dataset and each input: hits per class, false-alert clips on negatives, false alerts by pattern, and the per-group tables the v1.8.0 bench reports. For horn target clips: how many fire under each input, under shipped or shifted, and how many change in each direction.

All of it is published, including results that are worse than shipped.

## What this can and cannot decide

- **This work changes nothing in the shipped classifier.** It is measurement only.
- A change to resampling would alter the input for every class, so it is not a horn fix that can be judged on horn clips alone. It would be proposed only if, on **both** FSD50K and SONYC-UST, `bandlimited` has more horn hits than `shipped`, loses no siren or alarm hit, and has no more false-alert clips. ESC-50 is reported but cannot decide it, because ESC-50 was used to choose the v1.8.0 label map.
- Shifting windows is not something a live wristband can do after the fact. If `shifted` recovers horns, the finding is that overlapping windows are worth testing, which would be separate work.
- Any proposal that follows is the project owner's decision. Nothing is enabled by this work.
