# Candidate rules on stored SONYC-UST scores — full tables

Generated from the signed report `rules_v1.9.0_sonyc.json`. The model was not run. Classifier only, recorded clips, no wearers, not a clinical result. Nothing here has been independently reviewed.

Clips: 636, windows: 6360. Baseline: label map v1.8.0 at threshold 0.20.

Hits per class (change against the baseline in brackets):

| Rule | alarm (of 107) | traffic (of 185) |
|---|---|---|
| C1 | 71 (0) | 36 (0) |
| H1 | 71 (0) | 36 (0) |
| H2 | 71 (0) | 36 (0) |
| V1 | 71 (0) | 36 (0) |
| V2 | 71 (0) | 36 (0) |
| V3 | 71 (0) | 36 (0) |
| V4 | 71 (0) | 36 (0) |
| baseline | 71 | 36 |

False alerts and wrong fires (negative clips: 374):

| Rule | False-alert clips | Led by voice | Wrong alarm clips | Wrong traffic clips |
|---|---|---|---|---|
| C1 | 16 (0) | 16 | 7 | 1 |
| H1 | 16 (0) | 16 | 7 | 1 |
| H2 | 16 (0) | 16 | 7 | 1 |
| V1 | 16 (0) | 16 | 7 | 1 |
| V2 | 4 (-12) | 4 | 7 | 1 |
| V3 | 13 (-3) | 13 | 7 | 1 |
| V4 | 3 (-13) | 3 | 7 | 1 |
| baseline | 16 | 16 | 7 | 1 |

Rules: C1 = H1 with V1 (H1 applied first); H1 = Alarm and traffic outrank voice and media; H2 = Alarm and traffic outrank everything; V1 = Speech dominance: voice fires only if the top label of all 521 is a voice label; V2 = Persistence: voice fires only if a neighbouring window was also won by voice; V3 = Voice minimum 0.30; V4 = Voice minimum 0.50.

Horn clips at the baseline: 36 of 185 hit at 0.20, 68 at 0.05 (where traffic also fires on 16 non-target clips).

| Why a horn clip was missed at 0.20 | Clips |
|---|---|
| index mapping: top label is a vehicle or engine label outside the allowlist | 6 |
| masked: horn scored 0.20 or more but another class scored higher | 1 |
| not detected: no horn label reached 0.05 | 103 |
| threshold: horn won a window but scored 0.05 to 0.20 | 32 |
| weak and outscored: horn scored 0.05 to 0.20 and another class won | 7 |

Masked by: alarm 1.
Hits by clip length: 6 to 10 windows 36/185.
Horn and alarm: alarm fired on 23 horn clips (15 of them missed horns); traffic fired on 7 of 107 alarm clips.

Voice false alerts at the baseline: 16 negative clips, by YAMNet index: 0 Speech: 16.

Report SHA-256: `8926bca70a847941297a17cca6fd961fec43c5b1b1480c9857a89eada3e7c3c3`
