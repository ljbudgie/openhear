# Candidate rules on stored FSD50K scores — full tables

Generated from the signed report `rules_v1.9.0_fsd50k.json`. The model was not run. Classifier only, recorded clips, no wearers, not a clinical result. Nothing here has been independently reviewed.

Clips: 8403, windows: 79241. Baseline: label map v1.8.0 at threshold 0.20.

Hits per class (change against the baseline in brackets):

| Rule | alarm (of 48) | dog (of 137) | doorbell (of 27) | knock (of 88) | media (of 1613) | phone (of 139) | traffic (of 56) | voice (of 656) |
|---|---|---|---|---|---|---|---|---|
| C1 | 36 (0) | 100 (0) | 8 (0) | 54 (0) | 1305 (0) | 62 (0) | 32 (0) | 526 (-4) |
| H1 | 36 (0) | 100 (0) | 8 (0) | 54 (0) | 1305 (0) | 62 (0) | 32 (0) | 530 (0) |
| H2 | 36 (0) | 100 (0) | 8 (0) | 54 (0) | 1305 (0) | 21 (-41) | 32 (0) | 530 (0) |
| V1 | 36 (0) | 100 (0) | 8 (0) | 54 (0) | 1305 (0) | 62 (0) | 32 (0) | 526 (-4) |
| V2 | 36 (0) | 100 (0) | 8 (0) | 54 (0) | 1305 (0) | 62 (0) | 32 (0) | 369 (-161) |
| V3 | 36 (0) | 100 (0) | 8 (0) | 54 (0) | 1305 (0) | 62 (0) | 32 (0) | 513 (-17) |
| V4 | 36 (0) | 100 (0) | 8 (0) | 54 (0) | 1305 (0) | 62 (0) | 32 (0) | 470 (-60) |
| baseline | 36 | 100 | 8 | 54 | 1305 | 62 | 32 | 530 |

False alerts and wrong fires (negative clips: 5586):

| Rule | False-alert clips | Led by voice | Wrong alarm clips | Wrong traffic clips |
|---|---|---|---|---|
| C1 | 1277 (-9) | 546 | 186 | 111 |
| H1 | 1286 (0) | 555 | 186 | 111 |
| H2 | 1286 (0) | 555 | 247 | 111 |
| V1 | 1277 (-9) | 546 | 185 | 107 |
| V2 | 988 (-298) | 229 | 185 | 107 |
| V3 | 1198 (-88) | 463 | 185 | 107 |
| V4 | 1047 (-239) | 300 | 185 | 107 |
| baseline | 1286 | 555 | 185 | 107 |

Rules: C1 = H1 with V1 (H1 applied first); H1 = Alarm and traffic outrank voice and media; H2 = Alarm and traffic outrank everything; V1 = Speech dominance: voice fires only if the top label of all 521 is a voice label; V2 = Persistence: voice fires only if a neighbouring window was also won by voice; V3 = Voice minimum 0.30; V4 = Voice minimum 0.50.

Horn clips at the baseline: 32 of 56 hit at 0.20, 34 at 0.05 (where traffic also fires on 293 non-target clips).

| Why a horn clip was missed at 0.20 | Clips |
|---|---|
| index mapping: top label is a vehicle or engine label outside the allowlist | 4 |
| not detected: no horn label reached 0.05 | 15 |
| threshold: horn won a window but scored 0.05 to 0.20 | 2 |
| weak and outscored: horn scored 0.05 to 0.20 and another class won | 3 |

Hits by clip length: 1 window 5/6, 11 or more windows 9/24, 2 to 5 windows 14/16, 6 to 10 windows 4/10.
Horn and alarm: alarm fired on 5 horn clips (4 of them missed horns); traffic fired on 4 of 48 alarm clips.

Voice false alerts at the baseline: 600 negative clips, by YAMNet index: 0 Speech: 598, 3 Narration, monologue: 2.

Report SHA-256: `d8cd7049e94fc1c6ce5a0f1fb2135bdbeff6e7c07c6926351579887ad98ce3c5`
