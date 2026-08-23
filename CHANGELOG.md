# Changelog

All notable changes to OpenHear will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
once it reaches `1.0.0`. Until then, breaking changes may land in any `0.x`
release; they will be called out under a **Breaking** subsection.

## [Unreleased]

### Added

- **Auracast design relationship** (`docs/AURACAST.md`) — records how Bluetooth LE Audio Auracast (clean one-to-many broadcast in public venues) complements OpenHear. Auracast delivers the clean source; OpenHear delivers personal, sovereign, context-aware shaping and haptic substitution on top of whatever the person can hear — including a clean feed when one is available. Living Hearing Profile v7 adds `auracast_venue` context and updates preference/haptic notes so continuous stream speech does not drive continuous voice haptics; discrete join/leave cues and residual safety/environmental events remain.
- **Hearing loss and dementia — clinical context** (`docs/HEARING_LOSS_AND_DEMENTIA.md`) — careful evidence note: association is established; causation is not proven; major trial data and 2024 *Lancet* update do not support strong “hearing aids prevent dementia” claims. OpenHear’s justification rests on lived function (speech-in-noise failure, loudness intolerance, listening effort, social and professional participation), not cognitive-protection marketing.
- **Living Hearing Profile v8** — lived-experience refinement from RNID Research Panel detail (long-term aid user, multi-decade pathway): recruitment/loudness intolerance treated as first-class failure mode (amplified sound becomes overwhelming → aid removal); multi-talker and background-music scenes where speech is present but not intelligible; strong accents and group calls as repeated break points; social and professional avoidance after overload; medical appointments remaining difficult when quiet areas and professional adjustment are absent. Preference, `noisy_environment`, `clinical_environment`, and haptic notes strengthened accordingly.
- **Consented anonymised audiogram — moderate-severe bilateral with severe speech-in-noise loss** (`audiogram/data/mccullough_2025_anonymised.json`) — age-related bilateral moderate-to-severe sloping sensorineural loss (PTA ~58 both ears) with QuickSIN results showing severe SNR loss (11–24 dB) and clinic recommendation for maximum SNR improvement / array mic / FM system. Explicit consent 23 Aug 2026. Complements the existing profound-asymmetric and high-frequency-sloping reference profiles; documents the pure-tone vs functional speech-in-noise gap that a Living Hearing Profile is designed to capture.

## [1.5.0] - 2026-08-16

### Added

- **Living Hearing Profile advancement** — the public reference profile moved from a static 2021 clinical snapshot to a true multi-layer, user-owned, versioned sensory record. Preference layer refined for mid-frequency speech under high-frequency sloping loss; context map expanded with clinical/ICU and social-noise environments drawn from RNID Research Panel feedback; haptic priorities strengthened (alarms, speech, infant cry). First authentic non-placeholder history commitment (v5) recorded 12 Aug 2026.
- **Consented anonymised audiogram example** — profound asymmetric sensorineural loss (left anacusis + residual right) added as a public reference (`audiogram/data/richardson_2022_anonymised.json`) with explicit consent for Living Hearing Profile materials.
- **Live wristband accessibility profiles** — opt-in autism, cerebral palsy, and sensory-processing profiles now effective in the live wristband path. Firmware-enforced gentler haptic onset, profile-adjusted confidence gates, refractory timing, intensity scaling, preserved safety-alert perceptibility floor, session-only selection, and bounded CLI overrides. Equal opt-in status for the three starting profiles.
- **Residual Witness protocol (draft)** — `docs/RESIDUAL_WITNESS.md`. Continuous, local-only, Living-Hearing-Profile-weighted presence attestation. Feature hashes only (no raw audio), adaptive sampling, clear threat model, and explicit integration with the Living Hearing Profile and Burgess Principle. Produces citizen-owned cryptographic evidence of continuous biological presence.

### Research & engagement

- Active RNID Research Panel responses with detailed lived experience from adults with sensorineural loss (clinicians, audio engineers, cochlear-implant users, long-term aid users). Multiple real-world feedback threads already influencing preference offsets, context presets, and haptic prioritisation.

## [1.4.0] - 2026-07-08

### Added

- **Always-on output-safety limiter** (`dsp/output_safety.py`) — adds a final, unconditional output ceiling as the last stage of the DSP chain. See `CLINICIAN_GUIDE.md`.
- **Fatigue-aware DSP hooks scaffold** (`dsp/fatigue.py`, `dsp/fatigue_cli.py`) — roadmap item S3.
- **Per-contact DSP profile bank scaffold** (`dsp/contact_profiles.py`, `dsp/contact_cli.py`, `dsp/profile_delta.py`) — roadmap item S1.
- **`SUPERIOR_HEARING_ROADMAP.md`** — top-level phased roadmap.
- **Performer's beat channel**, **parametrised haptic primitives**, **continuous crowd-energy estimation**.

## [1.3.0] - 2026-06-02

### Added

- **Therapeutic frequency delivery (Pillar 5)** — `therapy/` package with protocol, binaural, entrainment, and closed-loop personalisation.

## [1.2.0] - 2026-06-02

### Added

- Plain-English audiogram interpretation and fitting explanation.
- Shared wristband haptic-packet codec and sound→haptic decision policy.

## [1.1.0]

### Added

- Burgess Principle reference layer, Apache 2.0 + Sovereign Use Addendum, aids-free training scaffolds, Phase 5/6 modules, wristband stack, north-star documents, CI and tooling.
