# Changelog

All notable changes to OpenHear will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
once it reaches `1.0.0`. Until then, breaking changes may land in any `0.x`
release; they will be called out under a **Breaking** subsection.

## [Unreleased]

### Added

- **Bone-conduction output pathway** (`dsp/bone_conduction.py`, `docs/BONE_CONDUCTION_PATHWAY.md`) — audiogram-driven gain retargeted for a contact transducer (mastoid / forehead / abutment / unspecified). Uses BC thresholds when supplied, otherwise AC. Generic compensation table is OpenHear's, not a copied manufacturer curve. SSD contralateral routing is a label. Oral / tooth is not a coupler value.
- **Sonitus / SoundBite FTO working note** (`docs/FTO_SONITUS.md`) and unpublished hold at `modules/optional/oral_appliance/`. Live Shanghai / EP / US claims and the SOUNDBITE mark stay off the public drawings. Not legal advice; attorney review required before any intra-oral file.
- **Speech-banana as measurement context** (`docs/MEASUREMENT_CONTEXT.md`) — which phonemes sit above the measured line is a first-class field. New consented, de-identified archetype: sloping moderate-to-severe with high-frequency consonants (s, f, th) above the line. No name, date of birth or clinic header in the public tree.
- **Measurement context** — tinnitus, fatigue or illness on the test day is a first-class Living Profile field, so one worse booth session is not treated as the new person. Includes an anonymised flat-ish moderate-to-severe / 8 kHz-drop shape.
- **Systemic Context Layer with hard sensory-modulation boundary** (`docs/SYSTEMIC_CONTEXT_LAYER.md`) — optional sixth surface of `openhear-living-profile-v1`. A factor is included only if it directly modulates sensory experience or access to sensory healthcare. In: fatigue, housebound status, transport barriers, ototoxic / auditory-processing medications. Out: renal/metabolic/inflammatory labs as such; housing, finances, energy, and legal matters unless they create a direct sensory-access barrier. User-declared, never inferred. No identifiable results in the public tree.
- **Aids-out night safety and rear-approach awareness** (`docs/AIDS_OUT_AND_REAR_APPROACH.md`).
- **Auracast design relationship** (`docs/AURACAST.md`).
- **Hearing loss and dementia — clinical context** (`docs/HEARING_LOSS_AND_DEMENTIA.md`).
- **Living Hearing Profile v8–v9** and consented anonymised audiogram examples.

## [1.9.0-dev] - not released

Work in progress on the `v1.9.0-dev` branch. The shipped classifier is unchanged from v1.8.0.

### Added

- `docs/BENCH_PLAN_v1.9.md`: seven candidate decision rules, the measures and code-checked pass conditions, committed before any rule was run. ESC-50 chooses; FSD50K and SONYC-UST only confirm; a rule that costs a siren or alarm hit does not ship.
- `scripts/bench_rules.py`: applies the baseline and the seven rules to stored model scores without running the model. Reports hits per class, false alerts, wrong alarm and traffic fires, voice false alerts by YAMNet index, a horn breakdown, per-class score distributions and the pass or fail verdict.
- Bench workflow mode `reanalyse-stored-scores`.
- Credits for YAMNet, AudioSet, ESC-50, FSD50K, SONYC-UST and contributors in docs/BENCH_RESULTS.md.

### Measured (classifier only, recorded clips, no wearers, not a clinical result, not independently reviewed)

- **No rule is enabled.**
- Both horn rules failed: they recovered no horn clip on any dataset, and the wider one cost 41 phone hits on FSD50K. Horn misses are mostly not a masking problem.
- All four voice rules passed the plan's conditions and stay switched off pending a decision on missed speech. On FSD50K: voice minimum 0.30 removes 88 false-alert clips and loses 17 of 530 speech clips; voice minimum 0.50 removes 239 and loses 60; persistence removes 298 and loses 161; speech dominance removes 9 and loses 4.

## [1.8.0] - 2026-11-10

### Changed

- **The traffic class is narrowed.** It is now an allowlist of six YAMNet labels, matched by index and name: vehicle horn, air horn, reversing beeps, skidding, tyre squeal and train horn. Engine, car, truck, bus, motorcycle, road-noise, race-car, ice-cream-van, railroad-car and aircraft-engine labels no longer fire it.
- "Emergency vehicle" now fires the alarm pattern, with the sirens.
- The bench (`scripts/bench_awareness.py`, report schema 2) stores the raw score for every window and class, and scores the v1.7.0 and v1.8.0 label maps on identical model output.

### Added

- Held-out bench datasets, downloaded at run time only: FSD50K eval (CC0 and CC BY clips only) and SONYC-UST v2.3.0 (CC BY 4.0, verified annotations). ESC-50 (CC BY-NC) is kept for before/after comparison.
- Per-class precision and recall, the YAMNet label behind each false alert, and a score distribution.
- `class_scores()`, `YamnetClassifier.score_window()` and `classify_window_detailed()` expose per-class and raw scores.
- Signed reports and full tables for all three datasets under docs/bench/.

### Measured (classifier only, recorded clips, no wearers, not a clinical result)

- Traffic false alerts on real street recordings with an engine and no horn: 79 of 374 clips under the v1.7.0 map, 0 of 374 under v1.8.0.
- All false alerts on ESC-50: 24.9% under the v1.7.0 map, 14.9% under v1.8.0.
- First figures on FSD50K: voice 80.8%, media 80.9%, phone 44.6%, doorbell 29.6% (27 clips).
- The identical results at thresholds 0.20 and 0.25, and at 0.35 and 0.40, are explained: the model's scores take few distinct values, and none lies between those thresholds.

### Known limits

- **Horn detection is weak and fell with this change:** 55% of ESC-50 car-horn clips (80% under the v1.7.0 map), 57% on FSD50K, 18% on real street recordings. The traffic pattern is not a safety feature.
- Doorbell and phone are weak on FSD50K.
- Voice is now the largest source of false alerts, and media the second.
- Skidding, tyre squeal and train horn are in the allowlist but no dataset here tests them as targets.

## [1.7.0] - 2026-11-09

### Added

- **First measured result.** `scripts/bench_awareness.py` and the `bench-awareness` workflow run the shipped classifier on the 2,000 ESC-50 recordings. Results, limits and the signed report are in docs/BENCH_RESULTS.md: 86.1% hit rate on target clips, and a pattern fired on 24.9% of clips with no OpenHear class. Classifier only, recorded clips, no wearers, not a clinical result.
- Sound classes `knock`, `baby_cry` and `phone`, each with a wristband pattern.
- Snapshot test that pins the full YAMNet-label to OpenHear-class table.
- Tinnitus safety notice in README and docs/INTENDED_PURPOSE.md, following written feedback from Tinnitus UK.

### Changed

- Label matching is whole-word. "Scary music", "Carnatic music", "Shuffling cards" and "Busy signal" no longer fire the traffic pattern, and "Wind chime" no longer fires doorbell.
- Only the "Knock" label fires the knock pattern; a door opening or sliding does not. DTMF dialling does not fire the phone pattern.
- README, docs/EVALUATION.md and PRE_REGISTRATION.md list exactly the nine classes the code supports.
- Living Hearing Profile: two notes on dual-earpiece listening and tinnitus reworded as one person's reported preference, not general advice (history version 11).

### Known limits

- The traffic class is too broad: any engine sound fires it. Narrowing it is the next change.
- Voice, doorbell, media and phone have no bench figure, because ESC-50 has no clips for them.

## [1.6.0] - 2026-11-09

### Changed

- README aligned with the intended-purpose statement in docs/INTENDED_PURPOSE.md. Current claim is environmental sound awareness only (detection and identification of everyday sound classes via short wrist vibration patterns weighted by the person's own audiogram). Not a hearing aid, not a certified medical device, not a replacement for clinical care.
- Removed overclaims that the wristband is a hearing system or that aids become unnecessary.
- Licence badge and references corrected to plain Apache 2.0 to match the LICENSE file.
- clinical/README.md updated: pilot description now states hit rate and false alerts for sound-class detection and identification; Southampton removed from partner list; Manchester retained.
- Added PRE_REGISTRATION.md template stating that ethics approval, a sponsor and a clinical lead are still required. No data collected under it.

### Fixed

pyproject.toml version set to 1.6.0.

## [1.5.0] - 2026-08-16

### Added

- Living Hearing Profile advancement, consented profound-asymmetric audiogram example, live wristband accessibility profiles, Residual Witness protocol (draft).

## [1.4.0] - 2026-07-08

### Added

- Output-safety limiter, fatigue-aware DSP hooks, per-contact profile bank, Superior Hearing roadmap.

## [1.3.0] - 2026-06-02

### Added

- Therapeutic frequency delivery (Pillar 5).

## [1.2.0] - 2026-06-02

### Added

- Plain-English audiogram interpretation; shared haptic-packet codec.

## [1.1.0]

### Added

- Burgess Principle reference layer, Apache 2.0, wristband stack, north-star documents.
