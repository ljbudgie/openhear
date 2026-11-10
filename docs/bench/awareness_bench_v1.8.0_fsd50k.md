# FSD50K eval split (zenodo.org/records/4060432) — full tables

Generated from the signed report `awareness_bench_v1.8.0_fsd50k.json`. Classifier only, recorded clips, no wearers, not a clinical result.

#### Label map v1.7.0

Threshold 0.20. Clips: 3190 target, 5087 negative. Not tested on this dataset: baby_cry.

| Class | Hit rate | Hits where another pattern also fired | Misses classified as |
|---|---|---|---|
| alarm | 36/48 = 75.0% (95% CI 61.2 to 85.1%) | 11 | media 4, nothing 7, traffic 1 |
| dog | 100/137 = 73.0% (95% CI 65.0 to 79.7%) | 20 | media 3, nothing 27, traffic 1, voice 6 |
| doorbell | 8/27 = 29.6% (95% CI 15.8 to 48.5%) | 4 | alarm 2, media 6, nothing 8, phone 2, voice 1 |
| knock | 54/88 = 61.4% (95% CI 50.9 to 70.9%) | 8 | media 4, nothing 24, voice 6 |
| media | 1305/1613 = 80.9% (95% CI 78.9 to 82.8%) | 75 | alarm 13, dog 1, doorbell 8, knock 2, nothing 254, phone 13, traffic 8, voice 9 |
| phone | 62/139 = 44.6% (95% CI 36.6 to 52.9%) | 27 | alarm 3, doorbell 1, knock 1, media 15, nothing 54, voice 3 |
| traffic | 370/693 = 53.4% (95% CI 49.7 to 57.1%) | 74 | alarm 17, dog 1, knock 12, media 29, nothing 238, phone 2, voice 24 |
| voice | 530/656 = 80.8% (95% CI 77.6 to 83.6%) | 79 | alarm 6, baby_cry 1, dog 3, knock 1, media 15, nothing 92, phone 2, traffic 6 |
| **All target clips** | 2465/3401 = 72.5% (95% CI 71.0 to 74.0%) | | |

False alerts: any pattern fired on 1316/5087 = 25.9% (95% CI 24.7 to 27.1%) of negative clips, and on 4623/48192 = 9.6% (95% CI 9.3 to 9.9%) of their windows.

By pattern: alarm 54, baby_cry 31, dog 66, doorbell 4, knock 102, media 329, phone 34, traffic 192, voice 504.

| YAMNet label that fired on a negative clip | Clips |
|---|---|
| Aircraft engine -> traffic | 9 |
| Alarm -> alarm | 18 |
| Alarm clock -> alarm | 15 |
| Baby cry, infant cry -> baby_cry | 31 |
| Car -> traffic | 15 |
| Civil defense siren -> alarm | 3 |
| Dog -> dog | 63 |
| Doorbell -> doorbell | 4 |
| Engine -> traffic | 36 |
| Engine starting -> traffic | 6 |
| Jet engine -> traffic | 10 |
| Knock -> knock | 102 |

| Group | Clips | Any pattern fired | Patterns fired |
|---|---|---|---|
| Alarm | 480 | 372 | alarm 133, dog 1, doorbell 11, knock 2, media 125, phone 96, traffic 90, voice 69 |
| Bark | 97 | 82 | dog 74, media 3, traffic 4, voice 21 |
| Bus | 50 | 42 | alarm 3, baby_cry 1, media 1, traffic 23, voice 24 |
| Car | 279 | 216 | alarm 24, dog 2, knock 12, media 25, phone 1, traffic 181, voice 40 |
| Car_passing_by | 98 | 73 | alarm 14, dog 1, media 13, traffic 66, voice 17 |
| Child_speech_and_kid_speaking | 72 | 67 | alarm 4, baby_cry 1, dog 2, knock 1, media 7, traffic 4, voice 62 |
| Conversation | 49 | 48 | alarm 2, baby_cry 1, dog 1, media 8, traffic 6, voice 47 |
| Dog | 137 | 116 | alarm 1, dog 100, doorbell 1, media 8, traffic 6, voice 31 |
| Doorbell | 27 | 20 | alarm 3, dog 1, doorbell 8, media 9, phone 3, voice 2 |
| Engine | 470 | 368 | alarm 33, baby_cry 1, dog 4, knock 1, media 53, phone 1, traffic 299, voice 98 |
| Engine_starting | 64 | 58 | media 2, traffic 57, voice 6 |
| Female_speech_and_woman_speaking | 212 | 193 | alarm 3, baby_cry 4, dog 5, media 18, phone 5, traffic 20, voice 185 |
| Knock | 88 | 64 | baby_cry 1, knock 54, media 10, voice 11 |
| Male_speech_and_man_speaking | 397 | 350 | alarm 18, baby_cry 1, dog 10, doorbell 1, knock 1, media 48, phone 5, traffic 45, voice 323 |
| Motor_vehicle_(road) | 507 | 383 | alarm 54, baby_cry 1, dog 5, knock 12, media 52, phone 1, traffic 289, voice 88 |
| Motorcycle | 71 | 65 | alarm 8, dog 1, media 9, traffic 59, voice 9 |
| Music | 1613 | 1367 | alarm 31, dog 3, doorbell 14, knock 3, media 1305, phone 33, traffic 42, voice 50 |
| Race_car_and_auto_racing | 45 | 42 | alarm 8, dog 1, media 17, traffic 37, voice 18 |
| Ringtone | 65 | 60 | alarm 12, doorbell 2, media 31, phone 31, traffic 1, voice 3 |
| Siren | 48 | 44 | alarm 36, media 15, phone 2, traffic 10, voice 7 |
| Speech | 656 | 577 | alarm 27, baby_cry 7, dog 23, doorbell 1, knock 2, media 78, phone 11, traffic 66, voice 530 |
| Speech_synthesizer | 46 | 41 | alarm 3, baby_cry 1, dog 2, media 7, phone 2, voice 37 |
| Telephone | 139 | 107 | alarm 29, doorbell 2, knock 1, media 44, phone 62, traffic 1, voice 10 |
| Traffic_noise_and_roadway_noise | 116 | 66 | alarm 10, dog 1, media 7, traffic 45, voice 25 |
| Truck | 40 | 30 | alarm 3, media 9, traffic 24, voice 8 |
| Vehicle_horn_and_car_horn_and_honking | 56 | 51 | alarm 4, knock 1, media 6, traffic 39, voice 11 |

Threshold sweep:

| Threshold | Target hit rate | False-alert clip rate |
|---|---|---|
| 0.10 | 81% | 45% |
| 0.15 | 76% | 32% |
| 0.20 (shipped) | 72% | 26% |
| 0.25 | 72% | 26% |
| 0.30 | 69% | 21% |
| 0.35 | 65% | 17% |
| 0.40 | 65% | 17% |
| 0.45 | 62% | 14% |
| 0.50 | 62% | 14% |

Precision / recall by class and threshold:

| Class | 0.10 | 0.20 | 0.30 | 0.40 | 0.50 | 0.60 | 0.70 |
|---|---|---|---|---|---|---|---|
| alarm | 12% / 79% | 16% / 75% | 18% / 75% | 20% / 75% | 23% / 73% | 31% / 65% | 32% / 60% |
| dog | 31% / 80% | 48% / 73% | 56% / 73% | 61% / 72% | 69% / 72% | 84% / 67% | 91% / 66% |
| doorbell | 13% / 30% | 26% / 30% | 33% / 26% | 43% / 22% | 60% / 22% | 57% / 15% | 80% / 15% |
| knock | 22% / 67% | 31% / 61% | 36% / 59% | 41% / 56% | 51% / 52% | 66% / 44% | 77% / 39% |
| media | 59% / 87% | 71% / 81% | 74% / 78% | 77% / 76% | 80% / 73% | 86% / 68% | 88% / 65% |
| phone | 34% / 45% | 44% / 45% | 47% / 44% | 53% / 42% | 59% / 42% | 70% / 40% | 77% / 39% |
| traffic | 42% / 69% | 55% / 53% | 60% / 46% | 61% / 37% | 63% / 30% | 62% / 16% | 62% / 11% |
| voice | 31% / 88% | 44% / 81% | 48% / 78% | 53% / 75% | 57% / 72% | 64% / 62% | 68% / 58% |

Score distribution: 61434 winning window scores took 31 distinct values (smallest gap 0.003906). No deciding score fell in: 0.20 to 0.25; 0.35 to 0.40; 0.45 to 0.50.

#### Label map v1.8.0

Threshold 0.20. Clips: 2656 target, 5586 negative. Not tested on this dataset: baby_cry.

| Class | Hit rate | Hits where another pattern also fired | Misses classified as |
|---|---|---|---|
| alarm | 36/48 = 75.0% (95% CI 61.2 to 85.1%) | 11 | media 4, nothing 7, traffic 1 |
| dog | 100/137 = 73.0% (95% CI 65.0 to 79.7%) | 20 | media 3, nothing 28, voice 6 |
| doorbell | 8/27 = 29.6% (95% CI 15.8 to 48.5%) | 4 | alarm 2, media 6, nothing 8, phone 2, voice 1 |
| knock | 54/88 = 61.4% (95% CI 50.9 to 70.9%) | 8 | media 4, nothing 24, voice 6 |
| media | 1305/1613 = 80.9% (95% CI 78.9 to 82.8%) | 73 | alarm 13, dog 1, doorbell 8, knock 2, nothing 255, phone 13, traffic 7, voice 9 |
| phone | 62/139 = 44.6% (95% CI 36.6 to 52.9%) | 27 | alarm 3, doorbell 1, knock 1, media 15, nothing 54, voice 3 |
| traffic | 32/56 = 57.1% (95% CI 44.1 to 69.2%) | 5 | alarm 4, knock 1, media 2, nothing 12, voice 5 |
| voice | 530/656 = 80.8% (95% CI 77.6 to 83.6%) | 69 | alarm 7, baby_cry 1, dog 3, knock 1, media 15, nothing 96, phone 2, traffic 1 |
| **All target clips** | 2127/2764 = 77.0% (95% CI 75.3 to 78.5%) | | |

False alerts: any pattern fired on 1286/5586 = 23.0% (95% CI 21.9 to 24.1%) of negative clips, and on 4283/55336 = 7.7% (95% CI 7.5 to 8.0%) of their windows.

By pattern: alarm 77, baby_cry 31, dog 68, doorbell 4, knock 113, media 365, phone 35, traffic 38, voice 555.

| YAMNet label that fired on a negative clip | Clips |
|---|---|
| Alarm -> alarm | 24 |
| Alarm clock -> alarm | 16 |
| Ambulance (siren) -> alarm | 3 |
| Baby cry, infant cry -> baby_cry | 31 |
| Buzzer -> alarm | 4 |
| Carnatic music -> media | 3 |
| Civil defense siren -> alarm | 4 |
| Dog -> dog | 65 |
| Doorbell -> doorbell | 4 |
| Emergency vehicle -> alarm | 9 |
| Fire alarm -> alarm | 3 |
| Howl -> dog | 3 |

| Group | Clips | Any pattern fired | Patterns fired |
|---|---|---|---|
| Alarm | 480 | 363 | alarm 134, dog 1, doorbell 11, knock 2, media 125, phone 96, traffic 57, voice 69 |
| Bark | 97 | 80 | dog 74, media 3, traffic 2, voice 21 |
| Bus | 50 | 29 | alarm 4, baby_cry 1, media 1, traffic 2, voice 24 |
| Car | 279 | 119 | alarm 26, dog 2, knock 12, media 25, phone 1, traffic 53, voice 40 |
| Car_passing_by | 98 | 38 | alarm 15, dog 1, media 13, traffic 12, voice 17 |
| Child_speech_and_kid_speaking | 72 | 65 | alarm 4, baby_cry 1, dog 2, knock 1, media 7, traffic 1, voice 62 |
| Conversation | 49 | 48 | alarm 2, baby_cry 1, dog 1, media 8, traffic 1, voice 47 |
| Dog | 137 | 113 | alarm 1, dog 100, doorbell 1, media 8, traffic 2, voice 31 |
| Doorbell | 27 | 20 | alarm 3, dog 1, doorbell 8, media 9, phone 3, voice 2 |
| Engine | 470 | 163 | alarm 35, baby_cry 1, dog 4, knock 1, media 53, phone 1, traffic 35, voice 98 |
| Engine_starting | 64 | 8 | media 2, traffic 1, voice 6 |
| Female_speech_and_woman_speaking | 212 | 191 | alarm 3, baby_cry 4, dog 5, media 18, phone 5, traffic 3, voice 185 |
| Knock | 88 | 64 | baby_cry 1, knock 54, media 10, voice 11 |
| Male_speech_and_man_speaking | 397 | 345 | alarm 18, baby_cry 1, dog 10, doorbell 1, knock 1, media 48, phone 5, traffic 12, voice 323 |
| Motor_vehicle_(road) | 507 | 216 | alarm 57, baby_cry 1, dog 5, knock 12, media 52, phone 1, traffic 67, voice 88 |
| Motorcycle | 71 | 20 | alarm 8, dog 1, media 9, traffic 3, voice 9 |
| Music | 1613 | 1366 | alarm 31, dog 3, doorbell 14, knock 3, media 1305, phone 33, traffic 32, voice 50 |
| Race_car_and_auto_racing | 45 | 30 | alarm 8, dog 1, media 17, traffic 14, voice 18 |
| Ringtone | 65 | 60 | alarm 12, doorbell 2, media 31, phone 31, traffic 1, voice 3 |
| Siren | 48 | 44 | alarm 36, media 15, phone 2, traffic 4, voice 7 |
| Speech | 656 | 568 | alarm 27, baby_cry 7, dog 23, doorbell 1, knock 2, media 78, phone 11, traffic 17, voice 530 |
| Speech_synthesizer | 46 | 41 | alarm 3, baby_cry 1, dog 2, media 7, phone 2, voice 37 |
| Telephone | 139 | 107 | alarm 29, doorbell 2, knock 1, media 44, phone 62, traffic 1, voice 10 |
| Traffic_noise_and_roadway_noise | 116 | 42 | alarm 10, dog 1, media 7, traffic 4, voice 25 |
| Truck | 40 | 22 | alarm 3, media 9, traffic 11, voice 8 |
| Vehicle_horn_and_car_horn_and_honking | 56 | 48 | alarm 5, knock 1, media 6, traffic 32, voice 11 |

Threshold sweep:

| Threshold | Target hit rate | False-alert clip rate |
|---|---|---|
| 0.10 | 83% | 40% |
| 0.15 | 79% | 28% |
| 0.20 (shipped) | 77% | 23% |
| 0.25 | 77% | 23% |
| 0.30 | 75% | 19% |
| 0.35 | 72% | 16% |
| 0.40 | 72% | 16% |
| 0.45 | 70% | 12% |
| 0.50 | 70% | 12% |

Precision / recall by class and threshold:

| Class | 0.10 | 0.20 | 0.30 | 0.40 | 0.50 | 0.60 | 0.70 |
|---|---|---|---|---|---|---|---|
| alarm | 12% / 79% | 16% / 75% | 18% / 75% | 20% / 75% | 24% / 73% | 33% / 69% | 33% / 60% |
| dog | 31% / 80% | 48% / 73% | 56% / 73% | 61% / 72% | 69% / 72% | 84% / 67% | 91% / 66% |
| doorbell | 13% / 30% | 26% / 30% | 33% / 26% | 43% / 22% | 60% / 22% | 57% / 15% | 80% / 15% |
| knock | 22% / 67% | 31% / 61% | 36% / 59% | 41% / 56% | 51% / 52% | 66% / 44% | 77% / 39% |
| media | 59% / 87% | 71% / 81% | 74% / 78% | 77% / 76% | 80% / 73% | 86% / 68% | 89% / 65% |
| phone | 34% / 45% | 44% / 45% | 47% / 44% | 53% / 42% | 59% / 42% | 70% / 40% | 77% / 39% |
| traffic | 14% / 61% | 23% / 57% | 30% / 57% | 34% / 55% | 37% / 52% | 46% / 46% | 48% / 41% |
| voice | 31% / 88% | 44% / 81% | 48% / 78% | 53% / 75% | 57% / 72% | 64% / 62% | 68% / 58% |

Score distribution: 59940 winning window scores took 31 distinct values (smallest gap 0.003906). No deciding score fell in: 0.20 to 0.25; 0.35 to 0.40; 0.45 to 0.50.

Provenance:

- OpenHear commit: `45ace506bb9a18e0797710a076d441bd697a2317`
- Model SHA-256: `4d8b4a53282dc83ef04e3e7dbc4fbc98082e34e44ed798e16c3a0cdd4c584faf`
- Dataset: FSD50K eval split (zenodo.org/records/4060432) (Per-clip Creative Commons licences. Only CC0 and CC BY clips are used; CC BY-NC and CC Sampling+ clips are excluded. Audio not redistributed.)
- Workflow run: https://github.com/ljbudgie/openhear/actions/runs/42911082407
- Raw scores SHA-256: `7c1cea926b5e2709e7d13c71634e5c80ab0ed3a247576fe320ccc384cf8717a9`
- Report SHA-256: `b42b407c343acc7e999e4ab81a38186d9fcb01c00b610321004735d6f74143ca`
