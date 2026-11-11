# Bench plan for v1.9.0 — written before any run

**Status:** Committed before any candidate rule was run on any dataset. The commit that adds this file contains no results. If a later commit changes a rule or a pass condition, it says so and says why.

Scope is unchanged: environmental sound awareness only. Not a hearing aid. Not a medical device. Classifier only, on recorded clips: no wearers, no real rooms, not a clinical result.

## What is already known

These come from the signed v1.8.0 reports under `docs/bench/` and are the baseline. They were known when this plan was written.

- Baseline is the v1.8.0 label map at the shipped threshold of 0.20 (commit `ee4d0b0`).
- Every voice false alert came from YAMNet index 0, "Speech".
- Horn misses are not mainly a threshold problem: lowering the threshold recovers few horns and adds many wrong fires.
- The model's scores take few distinct values, with none between 0.20 and 0.25 or between 0.35 and 0.40.

What is **not** known when this plan is committed: how any of the seven rules below performs on any dataset.

## The seven candidate rules

All are bench-only. They are applied to stored model scores, one 0.975 s window at a time, starting from the baseline decision (the highest-scoring mapped label wins the window and fires if it reaches 0.20).

Voice rules. A voice window that a rule holds back fires nothing; it does not pass to the next class.

| Rule | Name | A window won by voice fires only if |
|---|---|---|
| V1 | Speech dominance | the highest-scoring of all 521 YAMNet labels in that window is a label mapped to voice |
| V2 | Persistence | the window before or after it in the same clip was also won by voice at 0.20 or more |
| V3 | Voice minimum 0.30 | its score is at least 0.30 |
| V4 | Voice minimum 0.50 | its score is at least 0.50 |

Horn rules. They only apply when the best alarm label or the best traffic label in the window scores at least 0.20.

| Rule | Name | Then alarm or traffic (whichever scored higher; alarm on a tie) wins the window instead of |
|---|---|---|
| H1 | Alarm and traffic outrank voice and media | a voice or media winner |
| H2 | Alarm and traffic outrank everything | any other winner |

## Measures

- **Hit:** a target clip where its class fires in at least one window.
- **False alert:** a negative clip where any pattern fires in at least one window.
- **Wrong alarm or traffic fire:** a clip that is not a target for alarm (or traffic) where the alarm (or traffic) pattern fires.
- **Missed speech:** FSD50K voice target clips that the baseline hits and a rule does not.

## Roles of the datasets

- **ESC-50 chooses.** A rule is *selected* only on ESC-50.
- **FSD50K (eval, CC0 and CC BY clips) and SONYC-UST v2.3.0 only confirm.** They cannot rescue a rule that ESC-50 did not select, and no rule is adjusted after its held-out result is seen.

## Pass conditions

These are checked by code (`scripts/bench_rules.py`), not by eye.

**Gate, on every dataset.** A rule that loses a single alarm-class hit against the baseline does not ship. Alarm-class targets are siren and alarm-clock clips on ESC-50, siren clips on FSD50K, and siren and car-alarm clips on SONYC-UST.

**Selected on ESC-50.**

- A voice rule is selected if it passes the gate, has fewer false-alert clips than the baseline, and no target class has fewer hits than the baseline.
- A horn rule is selected if it passes the gate, has more car-horn hits than the baseline, adds no more wrong alarm-or-traffic clips than the horn hits it gains, and no target class has fewer hits than the baseline.

**Confirmed on FSD50K and on SONYC-UST (each separately).**

- A voice rule is confirmed if it passes the gate and has no more false-alert clips than the baseline.
- A horn rule is confirmed if it passes the gate, traffic hits are not lower than the baseline, the wrong alarm-or-traffic clips it adds are no more than the alarm and traffic hits it gains, and the hits other classes lose are no more than the alarm and traffic hits it gains.

**Result.**

- A rule *passes* only if it is selected on ESC-50 and confirmed on both held-out sets.
- **Voice rules stay switched off in this release whatever their result.** Each one's missed-speech cost on FSD50K is reported, and the decision on that trade-off is left to the project owner.
- At most one horn rule may be enabled. If both pass, H1 is preferred because it changes less.
- A rule that does not pass is reported with its numbers and is not enabled.

## What will be published

Before-and-after tables per dataset and per class for the baseline and all seven rules, including the ones that fail, with signed reports under `docs/bench/`. Weak numbers are published alongside good ones.
