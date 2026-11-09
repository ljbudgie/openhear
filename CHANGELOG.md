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
