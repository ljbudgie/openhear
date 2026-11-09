# Bench results — classifier only

**Status:** Measured on 9 November 2026 for v1.7.0. Every figure on this page comes from the signed report of one GitHub Actions run of `scripts/bench_awareness.py`.

## Read this first

- Recorded clips only.
- Classifier only.
- No wearers.
- No real rooms.
- Not a clinical result.

This page says how often the shipped classifier fires the right wristband pattern for a recorded sound, and how often it fires a pattern for a sound that has no OpenHear class. It says nothing about whether a person can feel or name a pattern. The claim these numbers sit under is [INTENDED_PURPOSE.md](INTENDED_PURPOSE.md).

## Headline

- **Hit rate:** 241 of 280 target clips (86.1%, 95% CI 81.5 to 89.6%).
- **False alerts:** a pattern fired on 429 of 1,720 clips that have no OpenHear class (24.9%, 95% CI 22.9 to 27.0%).
- **Not tested:** voice, doorbell, media and phone. ESC-50 has no clips for these classes, so no figure is given.

The false-alert figure is the conservative one. Every ESC-50 category without an OpenHear class counts as a negative, including sounds a wearer might want to feel, such as a train.

## Method

ESC-50 has 2,000 five-second clips in 50 categories, 40 clips each. Seven categories map to five OpenHear classes; the other 43 are negatives. Each clip is cut into consecutive 0.975 s windows at its native sample rate, and each window goes through `YamnetClassifier.classify_window`, the call the wristband runtime makes. A target clip is a hit when its class fires in at least one window. A negative clip is a false alert when any pattern fires in at least one window.

With 40 clips per category, each per-category rate has a wide interval. The intervals are in the tables.

## Results

Shipped threshold: 0.20. Clips: 280 target, 1720 negative.

### Hit rate by OpenHear class

| Class | Hit rate | Hits where another pattern also fired | Misses classified as |
|---|---|---|---|
| alarm | 72/80 = 90.0% (95% CI 81.5 to 94.8%) | 22 | nothing 4, phone 3, traffic 1 |
| baby_cry | 35/40 = 87.5% (95% CI 73.9 to 94.5%) | 4 | nothing 1, voice 4 |
| dog | 40/40 = 100.0% (95% CI 91.2 to 100.0%) | 3 | none |
| knock | 27/40 = 67.5% (95% CI 52.0 to 79.9%) | 0 | media 7, nothing 5, voice 1 |
| traffic | 67/80 = 83.8% (95% CI 74.2 to 90.2%) | 7 | alarm 2, media 1, nothing 9, voice 1 |
| **All target clips** | 241/280 = 86.1% (95% CI 81.5 to 89.6%) | | |

### Hit rate by ESC-50 category

| ESC-50 category | OpenHear class | Hit rate |
|---|---|---|
| car_horn | traffic | 32/40 = 80.0% (95% CI 65.2 to 89.5%) |
| clock_alarm | alarm | 33/40 = 82.5% (95% CI 68.0 to 91.2%) |
| crying_baby | baby_cry | 35/40 = 87.5% (95% CI 73.9 to 94.5%) |
| dog | dog | 40/40 = 100.0% (95% CI 91.2 to 100.0%) |
| door_wood_knock | knock | 27/40 = 67.5% (95% CI 52.0 to 79.9%) |
| engine | traffic | 35/40 = 87.5% (95% CI 73.9 to 94.5%) |
| siren | alarm | 39/40 = 97.5% (95% CI 87.1 to 99.6%) |

### False alerts on sounds with no OpenHear class

- Clips where any pattern fired: 429/1720 = 24.9% (95% CI 22.9 to 27.0%)
- Windows where any pattern fired: 957/8600 = 11.1% (95% CI 10.5 to 11.8%)
- Pattern fired (by clip): alarm 11, baby_cry 8, dog 31, knock 8, media 69, phone 3, traffic 179, voice 120

| ESC-50 category | Clips with a false alert |
|---|---|
| airplane | 23/40 |
| breathing | 3/40 |
| brushing_teeth | 6/40 |
| can_opening | 2/40 |
| cat | 15/40 |
| chainsaw | 40/40 |
| chirping_birds | 3/40 |
| church_bells | 17/40 |
| clapping | 9/40 |
| clock_tick | 6/40 |
| coughing | 15/40 |
| cow | 15/40 |
| crackling_fire | 2/40 |
| crickets | 6/40 |
| crow | 4/40 |
| door_wood_creaks | 13/40 |
| drinking_sipping | 13/40 |
| fireworks | 1/40 |
| footsteps | 4/40 |
| frog | 4/40 |
| glass_breaking | 2/40 |
| hand_saw | 5/40 |
| helicopter | 21/40 |
| hen | 5/40 |
| insects | 8/40 |
| keyboard_typing | 3/40 |
| laughing | 25/40 |
| mouse_click | 4/40 |
| pig | 11/40 |
| pouring_water | 2/40 |
| rain | 2/40 |
| rooster | 9/40 |
| sea_waves | 3/40 |
| sheep | 6/40 |
| sneezing | 13/40 |
| snoring | 5/40 |
| thunderstorm | 1/40 |
| toilet_flush | 2/40 |
| train | 40/40 |
| vacuum_cleaner | 19/40 |
| washing_machine | 20/40 |
| water_drops | 11/40 |
| wind | 11/40 |

### Threshold sweep

| Threshold | Target hit rate | False-alert clip rate |
|---|---|---|
| 0.10 | 91.8% | 45.9% |
| 0.15 | 87.5% | 32.0% |
| 0.20 (shipped) | 86.1% | 24.9% |
| 0.25 | 86.1% | 24.9% |
| 0.30 | 81.8% | 21.0% |
| 0.35 | 76.8% | 16.4% |
| 0.40 | 76.8% | 16.4% |
| 0.45 | 72.9% | 12.7% |
| 0.50 | 72.9% | 12.7% |

### Provenance

- OpenHear commit: `62d9020a88430d482c1bb62165525999600b57ed`
- Model SHA-256: `4d8b4a53282dc83ef04e3e7dbc4fbc98082e34e44ed798e16c3a0cdd4c584faf`
- Model source: https://storage.googleapis.com/mediapipe-models/audio_classifier/yamnet/float32/1/yamnet.tflite
- ESC-50 commit: `33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6`
- Workflow run: https://github.com/ljbudgie/openhear/actions/runs/42706933359
- Report SHA-256: `f73c53d445c69a2edc34ebd01dcc6fc112c6233d934c37e5aa591b3967aec98f`

## What the numbers show

- **The traffic class is too broad.** It fired on 179 negative clips, more than any other pattern. The label map sends every engine label to traffic, and chainsaw and train clips fired a pattern every time. Narrowing the traffic class is the next change.
- **The voice class fires on human sounds that are not speech**, such as laughing, coughing and sneezing. It was the second most common false alert (120 clips).
- **Knock is the weakest target class** (27 of 40). Seven of the 13 misses fired the media pattern instead.
- **Raising the threshold trades hits for false alerts.** It does not fix the traffic problem on its own.

## Open question

The threshold sweep gives identical results at 0.20 and 0.25, at 0.35 and 0.40, and at 0.45 and 0.50. That would be expected if the model's scores come in coarse steps, but this has not been confirmed. The report holds counts, not raw scores. A later run should record the score distribution.

## Reproduce

Run the **Bench — awareness classifier (ESC-50)** workflow from the Actions tab. It downloads the model and the recordings at run time; neither is committed to this repository (ESC-50 audio is CC BY-NC). Two runs on 9 November 2026 gave identical counts.

The signed report for this page is [bench/awareness_bench_v1.7.0.json](bench/awareness_bench_v1.7.0.json). To check it, set `report_sha256` to `null`, serialise with sorted keys and compact separators, and take the SHA-256.
