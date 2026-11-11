# Candidate rules on stored ESC-50 scores — full tables

Generated from the signed report `rules_v1.9.0_esc50.json`. The model was not run. Classifier only, recorded clips, no wearers, not a clinical result. Nothing here has been independently reviewed.

Clips: 2000, windows: 10000. Baseline: label map v1.8.0 at threshold 0.20.

Hits per class (change against the baseline in brackets):

| Rule | alarm (of 80) | baby_cry (of 40) | dog (of 40) | knock (of 40) | traffic (of 40) |
|---|---|---|---|---|---|
| C1 | 72 (0) | 35 (0) | 40 (0) | 27 (0) | 22 (0) |
| H1 | 72 (0) | 35 (0) | 40 (0) | 27 (0) | 22 (0) |
| H2 | 74 (+2) | 35 (0) | 40 (0) | 27 (0) | 22 (0) |
| V1 | 72 (0) | 35 (0) | 40 (0) | 27 (0) | 22 (0) |
| V2 | 72 (0) | 35 (0) | 40 (0) | 27 (0) | 22 (0) |
| V3 | 72 (0) | 35 (0) | 40 (0) | 27 (0) | 22 (0) |
| V4 | 72 (0) | 35 (0) | 40 (0) | 27 (0) | 22 (0) |
| baseline | 72 | 35 | 40 | 27 | 22 |

False alerts and wrong fires (negative clips: 1760):

| Rule | False-alert clips | Led by voice | Wrong alarm clips | Wrong traffic clips |
|---|---|---|---|---|
| C1 | 259 (-3) | 121 | 26 | 8 |
| H1 | 262 (0) | 125 | 26 | 8 |
| H2 | 262 (0) | 125 | 26 | 8 |
| V1 | 259 (-3) | 121 | 26 | 8 |
| V2 | 180 (-82) | 35 | 26 | 8 |
| V3 | 239 (-23) | 101 | 26 | 8 |
| V4 | 196 (-66) | 55 | 26 | 8 |
| baseline | 262 | 125 | 26 | 8 |

Rules: C1 = H1 with V1 (H1 applied first); H1 = Alarm and traffic outrank voice and media; H2 = Alarm and traffic outrank everything; V1 = Speech dominance: voice fires only if the top label of all 521 is a voice label; V2 = Persistence: voice fires only if a neighbouring window was also won by voice; V3 = Voice minimum 0.30; V4 = Voice minimum 0.50.

Horn clips at the baseline: 22 of 40 hit at 0.20, 29 at 0.05 (where traffic also fires on 51 non-target clips).

| Why a horn clip was missed at 0.20 | Clips |
|---|---|
| index mapping: top label is a vehicle or engine label outside the allowlist | 4 |
| masked: horn scored 0.20 or more but another class scored higher | 1 |
| not detected: no horn label reached 0.05 | 3 |
| threshold: horn won a window but scored 0.05 to 0.20 | 7 |
| weak and outscored: horn scored 0.05 to 0.20 and another class won | 3 |

Masked by: alarm 1.
Hits by clip length: 2 to 5 windows 22/40.
Horn and alarm: alarm fired on 11 horn clips (9 of them missed horns); traffic fired on 2 of 80 alarm clips.

Voice false alerts at the baseline: 125 negative clips, by YAMNet index: 0 Speech: 125.

Report SHA-256: `c524ccc131fcaa09ccc19e4d0eb3502bd3fe78f922f1be5b31895131cc1ac6f9`
