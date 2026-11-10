# Bench results — classifier only

**Status:** Measured on 10 November 2026 for v1.8.0. Every figure on this page comes from a signed report of a GitHub Actions run of `scripts/bench_awareness.py`. The v1.7.0 results this page replaces are in [bench/awareness_bench_v1.7.0.json](bench/awareness_bench_v1.7.0.json) and are reproduced below.

## Read this first

- Recorded clips only.
- Classifier only.
- No wearers.
- No real rooms.
- Not a clinical result.

This page says how often the classifier fires the right wristband pattern for a recorded sound, and how often it fires a pattern for a sound that has no OpenHear class. It says nothing about whether a person can feel or name a pattern. The claim these numbers sit under is [INTENDED_PURPOSE.md](INTENDED_PURPOSE.md).

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

## Reproduce

Run the **Bench — awareness classifier** workflow from the Actions tab and choose a dataset. ESC-50 takes about a minute, FSD50K about 35 minutes and SONYC-UST about 70 minutes.
