# Bench results — classifier only

**Status:** v1.8.0 results measured on 10 November 2026. Candidate rules for v1.9.0 measured on 11 November 2026; none is enabled. Every figure on this page comes from a signed report of a GitHub Actions run of `scripts/bench_awareness.py`. The v1.7.0 results this page replaces are in [bench/awareness_bench_v1.7.0.json](bench/awareness_bench_v1.7.0.json) and are reproduced below.

## Read this first

- Recorded clips only.
- Classifier only.
- No wearers.
- No real rooms.
- Not a clinical result.
- Nothing on this page has been independently reviewed.

This page says how often the classifier fires the right wristband pattern for a recorded sound, and how often it fires a pattern for a sound that has no OpenHear class. It says nothing about whether a person can feel or name a pattern. The claim these numbers sit under is [INTENDED_PURPOSE.md](INTENDED_PURPOSE.md).

## v1.9.0 work in progress: seven candidate rules, none enabled

**Status:** Measured on 11 November 2026 on the `v1.9.0-dev` branch. The shipped classifier is unchanged from v1.8.0.

v1.8.0 left two problems: the voice pattern causes most false alerts, and horn detection is weak. Seven candidate decision rules were tested against the v1.8.0 baseline by re-analysing the scores stored from the v1.8.0 runs. The model was not run again. The baseline computed from the stored scores matches the signed v1.8.0 reports exactly on all three datasets.

The rules, the measures and the pass conditions were committed in [BENCH_PLAN_v1.9.md](BENCH_PLAN_v1.9.md) before any rule was run. ESC-50 chooses; FSD50K and SONYC-UST only confirm; a rule that costs a siren or alarm hit does not ship. Pass or fail is computed by `scripts/bench_rules.py`.

### Result

- **No rule is enabled.**
- **Both horn rules failed.** Letting alarm and traffic outrank other classes recovered no horn clip on any dataset. On FSD50K the wider rule (H2) also took the phone pattern from 41 ringing-phone clips and gave them to alarm.
- **Horn misses are mostly not a masking problem.** At the baseline, a horn label scored 0.20 or more and lost the window to another class on 1 ESC-50 clip, no FSD50K clip and 1 SONYC-UST clip. On FSD50K and SONYC-UST most missed clips had no horn label reaching 0.05; on ESC-50 the largest group won a window with a score between 0.05 and 0.20. The fix is not in the decision rule.
- **All four voice rules passed the plan's conditions, and all stay switched off.** Each one trades false alerts for missed speech. That trade-off is a decision for the project owner and has not been made.

### Verdict, computed from the three reports

| Rule | No alarm hit lost | Selected on ESC-50 | Confirmed on FSD50K | Confirmed on SONYC-UST | Passes | Missed speech on FSD50K |
|---|---|---|---|---|---|---|
| C1: H1 with V1 (H1 applied first) | yes | no | no | yes | no | 4 |
| H1: Alarm and traffic outrank voice and media | yes | no | no | yes | no | 0 |
| H2: Alarm and traffic outrank everything | yes | no | no | yes | no | 0 |
| V1: Speech dominance: voice fires only if the top label of all 521 is a voice label | yes | yes | yes | yes | yes | 4 |
| V2: Persistence: voice fires only if a neighbouring window was also won by voice | yes | yes | yes | yes | yes | 161 |
| V3: Voice minimum 0.30 | yes | yes | yes | yes | yes | 17 |
| V4: Voice minimum 0.50 | yes | yes | yes | yes | yes | 60 |

The combined rule C1 is treated as a voice rule and would stay off in any case.

### The voice trade-off

Fewer false alerts against speech clips no longer caught. The baseline catches 530 of 656 FSD50K speech clips.

| Rule | False-alert clips, ESC-50 (of 1,760) | False-alert clips, FSD50K (of 5,586) | False-alert clips, SONYC-UST (of 374) | Speech clips caught, FSD50K (of 656) | Speech clips lost |
|---|---|---|---|---|---|
| Baseline (v1.8.0) | 262 | 1,286 | 16 | 530 |  |
| V1: Speech dominance | 259 | 1,277 | 16 | 526 | 4 |
| V2: Persistence | 180 | 988 | 4 | 369 | 161 |
| V3: Voice minimum 0.30 | 239 | 1,198 | 13 | 513 | 17 |
| V4: Voice minimum 0.50 | 196 | 1,047 | 3 | 470 | 60 |

- **Persistence (V2) removes the most false alerts and loses the most speech**: 161 of 530 speech clips. A one-window clip can never fire under this rule, and many FSD50K speech clips are short.
- **Voice minimum 0.50 (V4)** removes nearly as many false alerts as V2 on ESC-50 and SONYC-UST and loses 60 speech clips.
- **Voice minimum 0.30 (V3)** is the mildest effective rule: 17 speech clips lost.
- **Speech dominance (V1) does almost nothing.** When the voice pattern fires wrongly, "Speech" is nearly always the model's top label of all 521.

### Before and after, per dataset and class

Rules: V1 speech dominance; V2 persistence; V3 voice minimum 0.30; V4 voice minimum 0.50; H1 alarm and traffic outrank voice and media; H2 alarm and traffic outrank everything; C1 is H1 with V1. Figures in brackets are the change against the baseline. A "wrong" alarm or traffic clip is one that is not a target for that class where its pattern fired.

#### ESC-50

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

#### FSD50K

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

#### SONYC-UST

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

### Why horns are missed

Horn target clips at the baseline, by the first cause that applies:

| Cause | ESC-50 (18 missed of 40) | FSD50K (24 missed of 56) | SONYC-UST (149 missed of 185) |
|---|---|---|---|
| No horn label reached 0.05 | 3 | 15 | 103 |
| Horn won a window but scored 0.05 to 0.20 | 7 | 2 | 32 |
| Horn scored 0.05 to 0.20 and another class won | 3 | 3 | 7 |
| No horn label reached 0.05 and the top label was a vehicle or engine label outside the allowlist | 4 | 4 | 6 |
| Horn scored 0.20 or more but another class scored higher | 1 | 0 | 1 |

- **Lowering the threshold does not rescue horns.** Hits at 0.05 against 0.20: ESC-50 29 against 22 of 40, with the traffic pattern then firing on 51 clips that are not horns; FSD50K 34 against 32 of 56, with 293 wrong clips; SONYC-UST 68 against 36 of 185, with 16 wrong clips.
- **Horn and alarm are confused.** The alarm pattern fired on 11 ESC-50 horn clips (9 of them missed horns) and on 23 SONYC-UST horn clips (15 missed). The traffic pattern fired on 2 of 80 ESC-50 alarm clips and 7 of 107 SONYC-UST alarm clips.
- **What the model reported instead.** On ESC-50 the top label of a missed horn clip was most often the generic "Vehicle" (8 of 18). On SONYC-UST it was most often "Speech" (57 of 149).
- **Clip length (FSD50K, the only set with varied lengths).** Horn hits were 5 of 6 for 1 window, 9 of 24 for 11 or more windows, 14 of 16 for 2 to 5 windows, 4 of 10 for 6 to 10 windows. Longer clips are mostly field recordings where the horn is a small part.

### Voice false alerts by YAMNet label

Negative clips where the voice pattern fired in any window: ESC-50 125, all from index 0 "Speech"; FSD50K 600, of which 598 from index 0 "Speech" and 2 from index 3 "Narration, monologue"; SONYC-UST 16, all from index 0. The v1.8.0 tables count a clip under the pattern with the highest score, which gives 555 voice-led clips on FSD50K; the 600 here counts every clip where voice fired at all.

### The score grid

Every stored score is a multiple of 1/256, and the model uses few of those steps: 32 distinct values across all ESC-50 scores, 32 on FSD50K and 29 on SONYC-UST. Between 0.15 and 0.55 the only values are 0.199, 0.262, 0.332, 0.414, 0.500. Full per-class score distributions are in the signed reports.

### Provenance for the rules

| Dataset | Signed report | Full tables |
|---|---|---|
| ESC-50 | [json](bench/rules_v1.9.0_esc50.json) (SHA-256 `c524ccc131fcaa09…`) | [tables](bench/rules_v1.9.0_esc50.md) |
| FSD50K | [json](bench/rules_v1.9.0_fsd50k.json) (SHA-256 `d8cd7049e94fc1c6…`) | [tables](bench/rules_v1.9.0_fsd50k.md) |
| SONYC-UST | [json](bench/rules_v1.9.0_sonyc.json) (SHA-256 `8926bca70a847941…`) | [tables](bench/rules_v1.9.0_sonyc.md) |
| Verdict | [json](bench/rules_v1.9.0_verdict.json) (SHA-256 `e0f99daa9d3a91c0…`) | |

- Workflow run: https://github.com/ljbudgie/openhear/actions/runs/43066209373 (commit `391f711`).
- Stored scores came from the v1.8.0 runs, and their SHA-256 values match the signed v1.8.0 reports.
- To repeat it: run the **Bench — awareness classifier** workflow with mode `reanalyse-stored-scores`. It takes about two minutes. GitHub keeps the stored scores for 90 days from 10 November 2026; after that, run the model mode first and pass the new run numbers.

## What changed in v1.8.0

v1.7.0 fired the traffic pattern on any engine sound. It fired on chainsaws, trains, aircraft and washing machines. From v1.8.0 the traffic pattern is an allowlist of six YAMNet labels: vehicle horn, air horn, reversing beeps, skidding, tyre squeal and train horn. Engine, car, truck, bus, motorcycle and road-noise labels no longer fire it.

Both label maps were scored on the same stored model output, so every difference below comes from the label map alone.

## Headline

- **Traffic false alerts are close to zero.** On real street recordings with an engine and no horn (SONYC-UST), the traffic pattern fired on 79 of 374 (21%) clips under the v1.7.0 map and 0 of 374 (0%) under the v1.8.0 map.
- **All false alerts fell on ESC-50**, from 429 of 1720 (24.9%) to 262 of 1760 (14.9%) of clips with no OpenHear class. On FSD50K they fell from 1316 of 5087 (25.9%) to 1286 of 5586 (23.0%).
- **Horn detection is weak, and it got weaker.** The traffic pattern fired on 22 of 40 (55%) ESC-50 car-horn clips (v1.7.0 map: 32 of 40 (80%)), 32 of 56 (57%) FSD50K horn clips (v1.7.0 map: 39 of 56 (70%)), and 28 of 157 (18%) real street horn clips (v1.7.0 map: 36 of 157 (23%)). Under v1.7.0, part of the horn figure was the engine and car labels firing on horn recordings.
- **The traffic pattern is not a safety feature.** It must not be relied on to warn of a vehicle.
- **Sirens held.** The alarm pattern fired on 39 of 40 (98%) ESC-50 siren clips, 36 of 48 (75.0%) FSD50K siren clips and 71 of 106 (67%) street siren clips.
- **First figures for four classes** (FSD50K): voice 530 of 656 (80.8%), media 1305 of 1613 (80.9%), phone 62 of 139 (44.6%), doorbell 8 of 27 (29.6%). Doorbell and phone are weak.
- **Not tested anywhere:** skidding, tyre squeal and train horn as targets. No dataset here has clips labelled for them. Baby cry is tested on ESC-50 only.

## Datasets

| Dataset | Role | Clips used | Licence |
|---|---|---|---|
| ESC-50 | Before/after comparison with v1.7.0. Used to choose the v1.8.0 label map. | 2,000 | CC BY-NC 3.0. Non-commercial. |
| FSD50K, eval split | Held out. First figures for voice, media, phone and doorbell. | 8,403 (1,828 CC BY-NC and CC Sampling+ clips excluded) | CC0 and CC BY clips only |
| SONYC-UST v2.3.0 | Held out. Real street recordings: horns and sirens against engines. | 636 of 1,380 verified recordings | CC BY 4.0 |

No audio and no model file is committed to this repository. Each run downloads them.

The v1.8.0 label map was chosen after seeing ESC-50 results under v1.7.0, so ESC-50 is not a held-out test of it. FSD50K and SONYC-UST were first run after the label map was committed.

## Method

Each clip is cut into consecutive 0.975 s windows at its native sample rate (clips over 30 s are cut off there). Each window goes through `YamnetClassifier.score_window`, the model call the wristband runtime makes, and the score for every YAMNet class is stored. The decision rule is then applied to the stored scores as `classify_scores` applies it: the highest-scoring mapped label wins the window, and its pattern fires if the score reaches 0.20.

- A target clip is a hit when its class fires in at least one window.
- A negative clip is a false alert when any pattern fires in at least one window.
- Intervals are 95% Wilson intervals.

## ESC-50: before and after

2,000 five-second clips, 40 per category. Under the v1.7.0 map this reproduces the published v1.7.0 figures exactly (241 of 280 hits, 429 of 1,720 false alerts). Under the v1.8.0 map the 40 engine clips are negatives, not traffic targets.

| | v1.7.0 map | v1.8.0 map |
|---|---|---|
| False alerts on negative clips | 429 of 1720 (24.9%, 95% CI 22.9 to 27.0%) | 262 of 1760 (14.9%, 95% CI 13.3 to 16.6%) |
| Negative clips where the traffic pattern led | 177 | 4 |
| car_horn: traffic pattern fired | 32 of 40 (80%) | 22 of 40 (55%) |
| siren: alarm pattern fired | 39 of 40 (98%) | 39 of 40 (98%) |
| clock_alarm: alarm pattern fired | 33 of 40 (82%) | 33 of 40 (82%) |
| dog: dog pattern fired | 40 of 40 (100%) | 40 of 40 (100%) |
| crying_baby: baby_cry pattern fired | 35 of 40 (88%) | 35 of 40 (88%) |
| door_wood_knock: knock pattern fired | 27 of 40 (68%) | 27 of 40 (68%) |
| engine: any pattern fired | 35 of 40 (88%) | 0 of 40 (0%) |
| chainsaw: any pattern fired | 40 of 40 (100%) | 4 of 40 (10%) |
| train: any pattern fired | 40 of 40 (100%) | 8 of 40 (20%) |
| airplane: any pattern fired | 23 of 40 (57%) | 2 of 40 (5%) |
| helicopter: any pattern fired | 21 of 40 (52%) | 1 of 40 (2%) |
| washing_machine: any pattern fired | 20 of 40 (50%) | 6 of 40 (15%) |
| vacuum_cleaner: any pattern fired | 19 of 40 (48%) | 1 of 40 (2%) |

Of the 18 car-horn clips the v1.8.0 map missed, 7 fired alarm, 1 fired media, 8 fired nothing, 2 fired voice.

What still fires on negative clips under the v1.8.0 map: alarm 14, baby_cry 8, dog 29, knock 8, media 71, phone 3, traffic 4, voice 125. The Speech label led on 125 clips (laughing, coughing, sneezing and similar) and the Music label on 70 (church bells were the largest group).

## FSD50K: held-out clips

Clips vary in length and can carry several labels. A clip is a target for every OpenHear class its labels map to. Clips with none are negatives.

| Class | FSD50K labels counted as targets | Hit rate (v1.8.0 map) |
|---|---|---|
| voice | Speech and its sub-labels | 530 of 656 (80.8%, 95% CI 77.6 to 83.6%) |
| media | Music | 1305 of 1613 (80.9%, 95% CI 78.9 to 82.8%) |
| dog | Dog, Bark | 100 of 137 (73.0%, 95% CI 65.0 to 79.7%) |
| alarm | Siren | 36 of 48 (75.0%, 95% CI 61.2 to 85.1%) |
| knock | Knock | 54 of 88 (61.4%, 95% CI 50.9 to 70.9%) |
| traffic | Vehicle horn | 32 of 56 (57.1%, 95% CI 44.1 to 69.2%) |
| phone | Telephone, Ringtone | 62 of 139 (44.6%, 95% CI 36.6 to 52.9%) |
| doorbell | Doorbell | 8 of 27 (29.6%, 95% CI 15.8 to 48.5%) |

False alerts: 1286 of 5586 (23.0%, 95% CI 21.9 to 24.1%) of negative clips under the v1.8.0 map, 1316 of 5087 (25.9%, 95% CI 24.7 to 27.1%) under v1.7.0. By pattern under v1.8.0: alarm 77, baby_cry 31, dog 68, doorbell 4, knock 113, media 365, phone 35, traffic 38, voice 555.

Notes on these figures:

- **Phone.** 31 of 65 (48%) clips labelled Ringtone fired the phone pattern. On the same clips the media pattern fired on 31 of 65 (48%): ringtones are often music.
- **Doorbell.** Only 27 clips, so the interval is wide. The media pattern fired on 9 of 27 (33%) of them.
- **Alarm, and a change made after the first run.** FSD50K tags each clip with its ancestor labels as well as its own. "Alarm" is the ancestor of telephones, doorbells and bicycle bells as well as sirens. The first run counted every clip tagged "Alarm" as an alarm target and gave 134 of 480 (27.9%). That mostly measured telephones and bells. The figure above counts Siren clips only, and clips tagged only "Alarm" are left out. Both runs are linked under Provenance.
- **Engines.** Under the v1.8.0 map the traffic pattern still fired on 35 of 470 (7%) clips labelled Engine (v1.7.0 map: 299 of 470 (64%)) and 53 of 279 (19%) labelled Car (v1.7.0 map: 181 of 279 (65%)). Some of those recordings contain horns or squealing tyres; the labels cannot say which.

## SONYC-UST: real street recordings

Ten-second recordings from street sensors in New York, with annotations agreed by the SONYC team. A clip is used when it has a car horn, reversing beeper, siren or car alarm, or when it has an engine and no alert signal, voice, dog or music. The sensors are mounted on buildings, so many sounds are distant.

| | v1.7.0 map | v1.8.0 map |
|---|---|---|
| Engine-only clips: any pattern fired | 93 of 374 (25%) | 16 of 374 (4%) |
| Engine-only clips: traffic pattern fired | 79 of 374 (21%) | 0 of 374 (0%) |
| Car-horn clips: traffic pattern fired | 36 of 157 (23%) | 28 of 157 (18%) |
| Reversing-beeper clips: traffic pattern fired | 4 of 33 (12%) | 9 of 33 (27%) |
| Siren clips: alarm pattern fired | 69 of 106 (65%) | 71 of 106 (67%) |

On the car-horn clips the voice pattern fired on 62 of 157 (39%) and the alarm pattern on 19 of 157 (12%). All 16 false alerts on engine-only clips under the v1.8.0 map were the voice pattern. There was one car-alarm clip, too few for a figure.

## Why some thresholds give identical results

v1.7.0 reported identical results at thresholds 0.20 and 0.25, and at 0.35 and 0.40, without an explanation. The stored scores explain it. This model's scores take few distinct values: across 7,240 winning window scores on ESC-50 there were 31 distinct values. Near the shipped threshold the steps are 0.199, 0.262, 0.332, 0.414. No score lies between 0.20 and 0.25, between 0.35 and 0.40, or between 0.45 and 0.50, so those threshold pairs cannot differ. The same steps appear on FSD50K and SONYC-UST.

One consequence: the shipped threshold of 0.20 sits just above the 0.199 step and excludes it.

## Precision and recall

Precision for a class is the share of clips where its pattern fired that were targets for it. ESC-50, v1.8.0 map:

| Class | Precision / recall at 0.20 | at 0.30 | at 0.50 | at 0.70 |
|---|---|---|---|---|
| alarm | 73% / 90% | 75% / 86% | 85% / 82% | 91% / 72% |
| baby_cry | 81% / 88% | 83% / 88% | 89% / 85% | 93% / 68% |
| dog | 49% / 100% | 58% / 100% | 75% / 100% | 89% / 98% |
| knock | 75% / 68% | 77% / 60% | 83% / 60% | 90% / 45% |
| traffic | 73% / 55% | 83% / 50% | 95% / 48% | 100% / 32% |

Full precision and recall tables at every threshold from 0.05 to 0.95, for all three datasets and both label maps, are in the signed reports and the generated tables linked below.

## What the numbers show

- **Narrowing the traffic class removed its false alerts.** That part of the v1.7.0 problem is fixed.
- **It also showed that horn detection was never as good as it looked.** The remaining horn figures are weak on clean clips and poor on real streets.
- **Voice is now the largest source of false alerts.** The Speech label fires on laughing, coughing and other human sounds, and on street recordings.
- **Media is second.** The Music label fires on bells, ringtones and doorbells, and it takes hits away from knock, phone and doorbell.
- **Doorbell and phone are weak** on the first dataset that could test them.

## Not compared with other systems

SoundWatch (Jain et al., ASSETS 2020, doi.org/10.1145/3373625.3416991) reports 81.2% accuracy over 20 sound classes for a smartwatch app for deaf and hard of hearing users, with 88.6% at home and 71.2% outdoors. It reports accuracy, not false alerts, on different sounds and its own recordings. It is context, not a comparison.

## Provenance and full tables

| Dataset | Signed report | Full tables | Workflow run |
|---|---|---|---|
| ESC-50 | [json](bench/awareness_bench_v1.8.0_esc50.json) (SHA-256 `737286adfc5118e8…`) | [tables](bench/awareness_bench_v1.8.0_esc50.md) | https://github.com/ljbudgie/openhear/actions/runs/42899256052 |
| FSD50K | [json](bench/awareness_bench_v1.8.0_fsd50k.json) (SHA-256 `b42b407c343acc7e…`) | [tables](bench/awareness_bench_v1.8.0_fsd50k.md) | https://github.com/ljbudgie/openhear/actions/runs/42911082407 |
| SONYC-UST | [json](bench/awareness_bench_v1.8.0_sonyc.json) (SHA-256 `2b5e7b384d3047ef…`) | [tables](bench/awareness_bench_v1.8.0_sonyc.md) | https://github.com/ljbudgie/openhear/actions/runs/42899256052 |

- Model SHA-256: `4d8b4a53282dc83ef04e3e7dbc4fbc98082e34e44ed798e16c3a0cdd4c584faf` (the same file as v1.7.0).
- The first FSD50K run, which counted every "Alarm" tag as an alarm target: https://github.com/ljbudgie/openhear/actions/runs/42899256052
- The v1.7.0 label map used for comparison: [bench/label_map_v1.7.0.json](bench/label_map_v1.7.0.json).
- Raw scores for every window and class are attached to each workflow run as an artifact. GitHub keeps artifacts for 90 days. Their SHA-256 values are in the signed reports.

To check a report, set `report_sha256` to `null`, serialise with sorted keys and compact separators, and take the SHA-256.

## Credits

OpenHear did not create the model or the recordings these results rest on. It is built by someone who has lived with hearing loss all his life, building on these foundations:

- **YAMNet**, the sound classifier, by Manoj Plakal and Dan Ellis at Google, released under Apache 2.0 and distributed as a TensorFlow Lite model through MediaPipe.
- **AudioSet**, the dataset YAMNet was trained on and the source of its 521 labels, by Gemmeke and colleagues at Google (ICASSP 2017).
- **ESC-50**, by Karol J. Piczak (ACM Multimedia 2015), CC BY-NC.
- **FSD50K**, by Eduardo Fonseca, Xavier Favory, Jordi Pons, Frederic Font and Xavier Serra at the Music Technology Group, Universitat Pompeu Fabra (2022), made from sounds shared by Freesound contributors under Creative Commons licences.
- **SONYC-UST**, by Mark Cartwright and colleagues in the Sounds of New York City project at New York University (DCASE 2020), with labels from Zooniverse volunteers and the SONYC team, CC BY 4.0.
- **SoundWatch**, by Dhruv Jain and colleagues (ASSETS 2020), cited above for context.
- Everyone who has contributed code, testing and feedback to OpenHear.

None of these people or organisations has reviewed or endorsed OpenHear or these results. Nothing on this page has been independently reviewed. The scope is environmental sound awareness only: OpenHear is not a hearing aid and not a medical device.

## Reproduce

Run the **Bench — awareness classifier** workflow from the Actions tab and choose a dataset. ESC-50 takes about a minute, FSD50K about 35 minutes and SONYC-UST about 70 minutes.
