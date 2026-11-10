# SONYC-UST v2.3.0 (zenodo.org/records/3966543) — full tables

Generated from the signed report `awareness_bench_v1.8.0_sonyc.json`. Classifier only, recorded clips, no wearers, not a clinical result.

#### Label map v1.7.0

Threshold 0.20. Clips: 636 target, 0 negative. Not tested on this dataset: voice, doorbell, dog, media, knock, baby_cry, phone.

| Class | Hit rate | Hits where another pattern also fired | Misses classified as |
|---|---|---|---|
| alarm | 69/107 = 64.5% (95% CI 55.1 to 72.9%) | 13 | nothing 26, traffic 1, voice 11 |
| traffic | 119/559 = 21.3% (95% CI 18.1 to 24.9%) | 16 | alarm 1, media 8, nothing 361, voice 70 |
| **All target clips** | 188/666 = 28.2% (95% CI 24.9 to 31.8%) | | |

False alerts: any pattern fired on n/a of negative clips, and on n/a of their windows.

| Group | Clips | Any pattern fired | Patterns fired |
|---|---|---|---|
| car_alarm | 1 | 1 | traffic 1 |
| car_horn | 157 | 98 | alarm 18, dog 1, media 7, traffic 36, voice 62 |
| engine_only | 374 | 93 | traffic 79, voice 16 |
| reverse_beeper | 33 | 16 | alarm 3, media 4, traffic 4, voice 8 |
| siren | 106 | 84 | alarm 69, media 4, traffic 13, voice 17 |

Threshold sweep:

| Threshold | Target hit rate | False-alert clip rate |
|---|---|---|
| 0.10 | 49% | n/a |
| 0.15 | 35% | n/a |
| 0.20 (shipped) | 28% | n/a |
| 0.25 | 28% | n/a |
| 0.30 | 23% | n/a |
| 0.35 | 18% | n/a |
| 0.40 | 18% | n/a |
| 0.45 | 14% | n/a |
| 0.50 | 14% | n/a |

Precision / recall by class and threshold:

| Class | 0.10 | 0.20 | 0.30 | 0.40 | 0.50 | 0.60 | 0.70 |
|---|---|---|---|---|---|---|---|
| alarm | 87% / 67% | 92% / 64% | 92% / 63% | 97% / 63% | 100% / 58% | 100% / 50% | 100% / 36% |
| traffic | 95% / 46% | 96% / 21% | 97% / 15% | 98% / 9% | 97% / 5% | 94% / 3% | 100% / 2% |

Score distribution: 5702 winning window scores took 27 distinct values (smallest gap 0.003906). No deciding score fell in: 0.20 to 0.25; 0.35 to 0.40; 0.45 to 0.50.

#### Label map v1.8.0

Threshold 0.20. Clips: 262 target, 374 negative. Not tested on this dataset: voice, doorbell, dog, media, knock, baby_cry, phone.

| Class | Hit rate | Hits where another pattern also fired | Misses classified as |
|---|---|---|---|
| alarm | 71/107 = 66.4% (95% CI 57.0 to 74.6%) | 10 | nothing 25, voice 11 |
| traffic | 36/185 = 19.5% (95% CI 14.4 to 25.8%) | 15 | dog 1, media 7, nothing 84, voice 57 |
| **All target clips** | 107/292 = 36.6% (95% CI 31.3 to 42.3%) | | |

False alerts: any pattern fired on 16/374 = 4.3% (95% CI 2.6 to 6.8%) of negative clips, and on 26/3740 = 0.7% (95% CI 0.5 to 1.0%) of their windows.

By pattern: voice 16.

| YAMNet label that fired on a negative clip | Clips |
|---|---|
| Speech -> voice | 16 |

| Group | Clips | Any pattern fired | Patterns fired |
|---|---|---|---|
| car_alarm | 1 | 1 | traffic 1 |
| car_horn | 157 | 95 | alarm 19, dog 1, media 7, traffic 28, voice 62 |
| engine_only | 374 | 16 | voice 16 |
| reverse_beeper | 33 | 19 | alarm 4, media 4, traffic 9, voice 8 |
| siren | 106 | 84 | alarm 71, media 4, traffic 6, voice 17 |

Threshold sweep:

| Threshold | Target hit rate | False-alert clip rate |
|---|---|---|
| 0.10 | 42% | 18% |
| 0.15 | 39% | 7% |
| 0.20 (shipped) | 37% | 4% |
| 0.25 | 37% | 4% |
| 0.30 | 34% | 3% |
| 0.35 | 30% | 2% |
| 0.40 | 30% | 2% |
| 0.45 | 28% | 1% |
| 0.50 | 28% | 1% |

Precision / recall by class and threshold:

| Class | 0.10 | 0.20 | 0.30 | 0.40 | 0.50 | 0.60 | 0.70 |
|---|---|---|---|---|---|---|---|
| alarm | 78% / 69% | 91% / 66% | 92% / 64% | 96% / 64% | 100% / 58% | 100% / 50% | 100% / 36% |
| traffic | 89% / 27% | 97% / 19% | 97% / 16% | 100% / 11% | 100% / 11% | 100% / 8% | 100% / 6% |

Score distribution: 5635 winning window scores took 27 distinct values (smallest gap 0.003906). No deciding score fell in: 0.20 to 0.25; 0.35 to 0.40; 0.45 to 0.50.

Provenance:

- OpenHear commit: `25b443af374fc2ff22c083b270c777f552d30c9e`
- Model SHA-256: `4d8b4a53282dc83ef04e3e7dbc4fbc98082e34e44ed798e16c3a0cdd4c584faf`
- Dataset: SONYC-UST v2.3.0 (zenodo.org/records/3966543) (CC BY 4.0 (audio not redistributed))
- Workflow run: https://github.com/ljbudgie/openhear/actions/runs/42899256052
- Raw scores SHA-256: `b82e9c1903e3d56268676a124a8440d5567f046f14d37d68e90366436ac32a17`
- Report SHA-256: `2b5e7b384d3047ef05323f1129caf272c8756563bab01b625faaaeef00b0982d`
