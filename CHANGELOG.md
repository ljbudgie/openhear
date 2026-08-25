# Changelog

All notable changes to OpenHear will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
once it reaches `1.0.0`. Until then, breaking changes may land in any `0.x`
release; they will be called out under a **Breaking** subsection.

## [Unreleased]

### Added

- **Auracast design relationship** (`docs/AURACAST.md`) — records how Bluetooth LE Audio Auracast (clean one-to-many broadcast in public venues) complements OpenHear. Living Hearing Profile includes `auracast_venue` context; continuous stream speech does not drive continuous haptic voice pulses.
- **Hearing loss and dementia — clinical context** (`docs/HEARING_LOSS_AND_DEMENTIA.md`) — association established; causation not proven; OpenHear justified by lived function, not dementia-prevention claims.
- **Living Hearing Profile v8** — loudness intolerance, multi-talker failure, social/professional avoidance, medical appointment difficulty.
- **Consented anonymised audiogram — moderate-severe bilateral with severe speech-in-noise loss** (`audiogram/data/mccullough_2025_anonymised.json`) — PTA ~58 both ears with QuickSIN severe SNR loss (11–24 dB); explicit consent 23 Aug 2026.
- **Living Hearing Profile v9** — lived-experience refinement from detailed RNID-panel account (sudden-onset single-sided deafness, long NHS-then-private pathway):
  - Spatial awareness loss (“bubble”, reduced rear/deaf-side localisation, visual compensation near roads) → outdoors/traffic and haptic notes
  - Conversation processing lag and turn-taking misjudgement in multi-person meetings → phone_call / meeting context
  - Tinnitus triggered by unmatched amplification and dual-earpiece/stereo content → preference and music context (mono/single-sided friendly)
  - Deliberate aid-out recovery time (morning / before sleep) treated as legitimate self-management, not non-compliance
  - Hard acoustic environments (schools, tiled corridors) where environmental modification matters
  - Institutional pattern of full needs review then ignore — reinforces citizen-owned Living Hearing Profile as the record that cannot be discarded between appointments
  - Auracast chicken-and-egg and unusable platform announcements reinforced in transport and `auracast_venue` notes

## [1.5.0] - 2026-08-16

### Added

- Living Hearing Profile advancement, consented profound-asymmetric audiogram example, live wristband accessibility profiles, Residual Witness protocol (draft).

### Research & engagement

- Active RNID Research Panel responses shaping preference offsets, context presets, and haptic prioritisation.

## [1.4.0] - 2026-07-08

### Added

- Output-safety limiter, fatigue-aware DSP hooks, per-contact profile bank, Superior Hearing roadmap, performer beat channel, parametrised haptic primitives, crowd-energy estimation.

## [1.3.0] - 2026-06-02

### Added

- Therapeutic frequency delivery (Pillar 5).

## [1.2.0] - 2026-06-02

### Added

- Plain-English audiogram interpretation and fitting explanation; shared haptic-packet codec and decision policy.

## [1.1.0]

### Added

- Burgess Principle reference layer, Apache 2.0 + Sovereign Use Addendum, aids-free scaffolds, Phase 5/6 modules, wristband stack, north-star documents, CI and tooling.
