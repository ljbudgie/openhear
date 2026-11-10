# ESC-50 (github.com/karolpiczak/ESC-50) — full tables

Generated from the signed report `awareness_bench_v1.8.0_esc50.json`. Classifier only, recorded clips, no wearers, not a clinical result.

#### Label map v1.7.0

Threshold 0.20. Clips: 280 target, 1720 negative. Not tested on this dataset: voice, doorbell, media, phone.

| Class | Hit rate | Hits where another pattern also fired | Misses classified as |
|---|---|---|---|
| alarm | 72/80 = 90.0% (95% CI 81.5 to 94.8%) | 22 | nothing 4, phone 3, traffic 1 |
| baby_cry | 35/40 = 87.5% (95% CI 73.9 to 94.5%) | 4 | dog 1, nothing 1, voice 3 |
| dog | 40/40 = 100.0% (95% CI 91.2 to 100.0%) | 3 | none |
| knock | 27/40 = 67.5% (95% CI 52.0 to 79.9%) | 0 | media 7, nothing 5, voice 1 |
| traffic | 67/80 = 83.8% (95% CI 74.2 to 90.2%) | 7 | alarm 2, media 1, nothing 9, voice 1 |
| **All target clips** | 241/280 = 86.1% (95% CI 81.5 to 89.6%) | | |

False alerts: any pattern fired on 429/1720 = 24.9% (95% CI 22.9 to 27.0%) of negative clips, and on 957/8600 = 11.1% (95% CI 10.5 to 11.8%) of their windows.

By pattern: alarm 12, baby_cry 8, dog 29, knock 8, media 69, phone 3, traffic 177, voice 123.

| YAMNet label that fired on a negative clip | Clips |
|---|---|
| Aircraft engine -> traffic | 21 |
| Alarm -> alarm | 6 |
| Baby cry, infant cry -> baby_cry | 8 |
| Bark -> dog | 1 |
| Bus -> traffic | 4 |
| Buzzer -> alarm | 3 |
| Car -> traffic | 10 |
| Carnatic music -> media | 1 |
| Dog -> dog | 27 |
| Engine -> traffic | 18 |
| Engine starting -> traffic | 2 |
| Howl -> dog | 1 |

| Group | Clips | Any pattern fired | Patterns fired |
|---|---|---|---|
| airplane | 40 | 23 | media 1, traffic 23 |
| breathing | 40 | 3 | voice 3 |
| brushing_teeth | 40 | 6 | dog 2, media 3, voice 1 |
| can_opening | 40 | 2 | media 1, voice 1 |
| car_horn | 40 | 36 | alarm 8, media 3, traffic 32, voice 2 |
| cat | 40 | 15 | baby_cry 4, dog 8, media 1, voice 5 |
| chainsaw | 40 | 40 | alarm 1, media 2, traffic 40 |
| chirping_birds | 40 | 3 | media 1, voice 2 |
| church_bells | 40 | 17 | media 17 |
| clapping | 40 | 9 | voice 9 |
| clock_alarm | 40 | 36 | alarm 33, phone 11 |
| clock_tick | 40 | 6 | alarm 2, media 3, voice 1 |
| coughing | 40 | 15 | traffic 1, voice 14 |
| cow | 40 | 15 | alarm 4, dog 2, media 5, traffic 1, voice 8 |
| crackling_fire | 40 | 2 | traffic 1, voice 1 |
| crickets | 40 | 6 | alarm 4, media 1, traffic 1 |
| crow | 40 | 4 | dog 1, traffic 1, voice 2 |
| crying_baby | 40 | 39 | baby_cry 35, dog 4, voice 5 |
| dog | 40 | 40 | dog 40, voice 3 |
| door_wood_creaks | 40 | 13 | baby_cry 2, knock 4, media 8, traffic 1 |
| door_wood_knock | 40 | 35 | knock 27, media 7, voice 1 |
| drinking_sipping | 40 | 13 | media 1, voice 12 |
| engine | 40 | 35 | traffic 35 |
| fireworks | 40 | 1 | media 1 |
| footsteps | 40 | 4 | knock 4 |
| frog | 40 | 4 | dog 1, voice 3 |
| glass_breaking | 40 | 2 | media 1, traffic 1 |
| hand_saw | 40 | 5 | dog 1, media 2, traffic 1, voice 1 |
| helicopter | 40 | 21 | traffic 21, voice 1 |
| hen | 40 | 5 | baby_cry 1, dog 3, voice 1 |
| insects | 40 | 8 | dog 1, media 6, voice 2 |
| keyboard_typing | 40 | 3 | media 1, traffic 1, voice 1 |
| laughing | 40 | 25 | baby_cry 1, dog 1, doorbell 1, media 1, voice 24 |
| mouse_click | 40 | 4 | media 2, voice 2 |
| pig | 40 | 11 | dog 6, media 1, traffic 1, voice 4 |
| pouring_water | 40 | 2 | phone 1, voice 1 |
| rain | 40 | 2 | traffic 2 |
| rooster | 40 | 9 | alarm 1, dog 7, knock 1, voice 1 |
| sea_waves | 40 | 3 | traffic 2, voice 1 |
| sheep | 40 | 6 | media 1, traffic 1, voice 4 |
| siren | 40 | 40 | alarm 39, dog 1, media 8, phone 1, traffic 5 |
| sneezing | 40 | 13 | dog 2, voice 11 |
| snoring | 40 | 5 | dog 1, traffic 1, voice 3 |
| thunderstorm | 40 | 1 | media 1 |
| toilet_flush | 40 | 2 | media 1, traffic 1 |
| train | 40 | 40 | media 4, traffic 37, voice 2 |
| vacuum_cleaner | 40 | 19 | alarm 1, traffic 19 |
| washing_machine | 40 | 20 | media 5, traffic 15, voice 1 |
| water_drops | 40 | 11 | media 6, phone 2, voice 3 |
| wind | 40 | 11 | alarm 1, traffic 10 |

Threshold sweep:

| Threshold | Target hit rate | False-alert clip rate |
|---|---|---|
| 0.10 | 92% | 46% |
| 0.15 | 88% | 32% |
| 0.20 (shipped) | 86% | 25% |
| 0.25 | 86% | 25% |
| 0.30 | 82% | 21% |
| 0.35 | 77% | 16% |
| 0.40 | 77% | 16% |
| 0.45 | 73% | 13% |
| 0.50 | 73% | 13% |

Precision / recall by class and threshold:

| Class | 0.10 | 0.20 | 0.30 | 0.40 | 0.50 | 0.60 | 0.70 |
|---|---|---|---|---|---|---|---|
| alarm | 64% / 92% | 77% / 90% | 78% / 86% | 82% / 84% | 84% / 80% | 88% / 75% | 90% / 70% |
| baby_cry | 67% / 92% | 81% / 88% | 83% / 88% | 88% / 88% | 89% / 85% | 94% / 72% | 93% / 68% |
| dog | 27% / 100% | 49% / 100% | 58% / 100% | 68% / 100% | 75% / 100% | 87% / 100% | 89% / 98% |
| knock | 67% / 78% | 75% / 68% | 77% / 60% | 80% / 60% | 83% / 60% | 86% / 48% | 90% / 45% |
| traffic | 20% / 94% | 26% / 84% | 28% / 76% | 27% / 61% | 28% / 52% | 28% / 30% | 27% / 24% |

Score distribution: 7556 winning window scores took 31 distinct values (smallest gap 0.003906). No deciding score fell in: 0.20 to 0.25; 0.35 to 0.40; 0.45 to 0.50.

#### Label map v1.8.0

Threshold 0.20. Clips: 240 target, 1760 negative. Not tested on this dataset: voice, doorbell, media, phone.

| Class | Hit rate | Hits where another pattern also fired | Misses classified as |
|---|---|---|---|
| alarm | 72/80 = 90.0% (95% CI 81.5 to 94.8%) | 19 | nothing 4, phone 3, traffic 1 |
| baby_cry | 35/40 = 87.5% (95% CI 73.9 to 94.5%) | 4 | dog 1, nothing 1, voice 3 |
| dog | 40/40 = 100.0% (95% CI 91.2 to 100.0%) | 3 | none |
| knock | 27/40 = 67.5% (95% CI 52.0 to 79.9%) | 0 | media 7, nothing 5, voice 1 |
| traffic | 22/40 = 55.0% (95% CI 39.8 to 69.3%) | 4 | alarm 7, media 1, nothing 8, voice 2 |
| **All target clips** | 196/240 = 81.7% (95% CI 76.3 to 86.1%) | | |

False alerts: any pattern fired on 262/1760 = 14.9% (95% CI 13.3 to 16.6%) of negative clips, and on 446/8800 = 5.1% (95% CI 4.6 to 5.5%) of their windows.

By pattern: alarm 14, baby_cry 8, dog 29, knock 8, media 71, phone 3, traffic 4, voice 125.

| YAMNet label that fired on a negative clip | Clips |
|---|---|
| Alarm -> alarm | 6 |
| Alarm clock -> alarm | 1 |
| Baby cry, infant cry -> baby_cry | 8 |
| Bark -> dog | 1 |
| Buzzer -> alarm | 3 |
| Carnatic music -> media | 1 |
| Dog -> dog | 27 |
| Emergency vehicle -> alarm | 2 |
| Howl -> dog | 1 |
| Knock -> knock | 8 |
| Music -> media | 70 |
| Police car (siren) -> alarm | 1 |

| Group | Clips | Any pattern fired | Patterns fired |
|---|---|---|---|
| airplane | 40 | 2 | media 1, traffic 1 |
| breathing | 40 | 3 | voice 3 |
| brushing_teeth | 40 | 6 | dog 2, media 3, voice 1 |
| can_opening | 40 | 2 | media 1, voice 1 |
| car_horn | 40 | 32 | alarm 11, media 3, traffic 22, voice 2 |
| cat | 40 | 15 | baby_cry 4, dog 8, media 1, voice 5 |
| chainsaw | 40 | 4 | alarm 1, media 2, traffic 1 |
| chirping_birds | 40 | 3 | media 1, voice 2 |
| church_bells | 40 | 17 | media 17, traffic 1 |
| clapping | 40 | 9 | voice 9 |
| clock_alarm | 40 | 36 | alarm 33, phone 11 |
| clock_tick | 40 | 6 | alarm 2, media 3, voice 1 |
| coughing | 40 | 15 | traffic 1, voice 14 |
| cow | 40 | 14 | alarm 4, dog 2, media 5, voice 8 |
| crackling_fire | 40 | 1 | voice 1 |
| crickets | 40 | 5 | alarm 4, media 1 |
| crow | 40 | 3 | dog 1, voice 2 |
| crying_baby | 40 | 39 | baby_cry 35, dog 4, voice 5 |
| dog | 40 | 40 | dog 40, voice 3 |
| door_wood_creaks | 40 | 12 | baby_cry 2, knock 4, media 8 |
| door_wood_knock | 40 | 35 | knock 27, media 7, voice 1 |
| drinking_sipping | 40 | 13 | media 1, voice 12 |
| engine | 40 | 0 | none |
| fireworks | 40 | 1 | media 1 |
| footsteps | 40 | 4 | knock 4 |
| frog | 40 | 4 | dog 1, voice 3 |
| glass_breaking | 40 | 1 | media 1 |
| hand_saw | 40 | 4 | dog 1, media 2, voice 1 |
| helicopter | 40 | 1 | voice 1 |
| hen | 40 | 5 | baby_cry 1, dog 3, voice 1 |
| insects | 40 | 8 | dog 1, media 6, voice 2 |
| keyboard_typing | 40 | 2 | media 1, voice 1 |
| laughing | 40 | 25 | baby_cry 1, dog 1, doorbell 1, media 1, voice 24 |
| mouse_click | 40 | 4 | media 2, voice 2 |
| pig | 40 | 10 | dog 6, media 1, voice 4 |
| pouring_water | 40 | 2 | phone 1, voice 1 |
| rain | 40 | 0 | none |
| rooster | 40 | 9 | alarm 1, dog 7, knock 1, voice 1 |
| sea_waves | 40 | 1 | voice 1 |
| sheep | 40 | 5 | media 1, voice 4 |
| siren | 40 | 40 | alarm 39, dog 1, media 8, phone 1, traffic 2 |
| sneezing | 40 | 13 | dog 2, voice 11 |
| snoring | 40 | 4 | dog 1, voice 3 |
| thunderstorm | 40 | 1 | media 1 |
| toilet_flush | 40 | 1 | media 1 |
| train | 40 | 8 | alarm 1, media 4, traffic 1, voice 2 |
| vacuum_cleaner | 40 | 1 | alarm 1 |
| washing_machine | 40 | 6 | media 5, traffic 1, voice 1 |
| water_drops | 40 | 11 | media 6, phone 2, voice 3 |
| wind | 40 | 1 | alarm 1 |

Threshold sweep:

| Threshold | Target hit rate | False-alert clip rate |
|---|---|---|
| 0.10 | 87% | 32% |
| 0.15 | 84% | 20% |
| 0.20 (shipped) | 82% | 15% |
| 0.25 | 82% | 15% |
| 0.30 | 78% | 12% |
| 0.35 | 77% | 9% |
| 0.40 | 77% | 9% |
| 0.45 | 76% | 7% |
| 0.50 | 76% | 7% |

Precision / recall by class and threshold:

| Class | 0.10 | 0.20 | 0.30 | 0.40 | 0.50 | 0.60 | 0.70 |
|---|---|---|---|---|---|---|---|
| alarm | 59% / 92% | 73% / 90% | 75% / 86% | 81% / 84% | 85% / 82% | 87% / 78% | 91% / 72% |
| baby_cry | 67% / 92% | 81% / 88% | 83% / 88% | 88% / 88% | 89% / 85% | 94% / 72% | 93% / 68% |
| dog | 27% / 100% | 49% / 100% | 58% / 100% | 68% / 100% | 75% / 100% | 87% / 100% | 89% / 98% |
| knock | 67% / 78% | 75% / 68% | 77% / 60% | 80% / 60% | 83% / 60% | 86% / 48% | 90% / 45% |
| traffic | 52% / 68% | 73% / 55% | 83% / 50% | 90% / 48% | 95% / 48% | 94% / 38% | 100% / 32% |

Score distribution: 7240 winning window scores took 31 distinct values (smallest gap 0.003906). No deciding score fell in: 0.20 to 0.25; 0.35 to 0.40; 0.45 to 0.50.

Provenance:

- OpenHear commit: `25b443af374fc2ff22c083b270c777f552d30c9e`
- Model SHA-256: `4d8b4a53282dc83ef04e3e7dbc4fbc98082e34e44ed798e16c3a0cdd4c584faf`
- Dataset: ESC-50 (github.com/karolpiczak/ESC-50) (CC BY-NC 3.0 (audio not redistributed; before/after comparison only))
- Workflow run: https://github.com/ljbudgie/openhear/actions/runs/42899256052
- Raw scores SHA-256: `769af4e8726016b78d2dc886b3516bb498334795a32c5170a634f031e7c8f61f`
- Report SHA-256: `737286adfc5118e89afa94984cee0d3318f74350e0bcbd52962453f111560c26`
