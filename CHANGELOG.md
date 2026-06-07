# Changelog

All notable changes to OpenHear will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
once it reaches `1.0.0`. Until then, breaking changes may land in any `0.x`
release; they will be called out under a **Breaking** subsection.

## [Unreleased]

### Added

- **`SUPERIOR_HEARING_ROADMAP.md`** — top-level phased roadmap (Short /
  Medium / Long) for evolving OpenHear into a system that delivers
  hearing *functionally and experientially superior* to pre-deafness
  natural hearing across six named domains (social/relational,
  conversation in noise, music, focus, emotional nuance, environmental
  awareness). Includes a shared 10-metric scoreboard (M1–M10),
  integration map to existing DSP / haptic / social / Iris / Whoop /
  therapy / wristband / advocacy surfaces, a copy-paste-ready Phase S
  minimal viable experiment (`SH-S-001` per-contact DSP profile),
  Iris sub-agent prompt seeds (Plasticity Coach, Social Listener,
  Music Enhancer, Fatigue Sentinel), and explicit BGSP/BSEP/Burgess
  Principle alignment. Linked from `README.md` and `docs/index.md`.
  - **v0.2** — §9 open questions resolved with repo-grounded defaults
    (three-tier Whoop recovery scheme, per-skin-site haptic dose
    budget on top of the committed firmware thermal envelope, social-
    tier voice-fingerprint consent flow with scope-can-only-narrow
    BSEP rule, `SH-S-001` contact roles with names assigned locally,
    M1/M5 baselines tagged TBM with fixed measurement protocols).
    Adds new §10 "Defaults summary" table for downstream agents and
    `dsp/config.py` to anchor against.
- **Performer's beat channel** (`stream/tempo_channel.py`) — `TempoChannel`
  adapts the rhythmic-scheduling idea from `therapy/entrainment.py` to live
  performance: each `update(bpm)` call drives a `HapticPrimitive` at the
  current room tempo so a hard-of-hearing musician can feel the pulse
  locked to the band. Phase is tracked across back-to-back
  `events_for_window()` calls, so the beat train stays continuous even as
  the tempo shifts. Optional `beats_per_bar` + `accent_intensity` make the
  downbeat punch harder than the offbeats; optional EMA `smoothing` damps a
  jittery tempo tracker. Helpers `bpm_to_pulse_rate_hz` /
  `pulse_rate_hz_to_bpm` formalise the BPM ↔ Hz conversion. Pure Python on
  top of the existing 3-byte `stream.haptic_packet` wire format, so any
  firmware that already speaks v1 will respond without changes.
- **Parametrised haptic primitives** (`stream/haptic_primitive.py`) — replaces the
  seven hard-coded v1 patterns with four composable axes: `pulse_rate_hz` (0.1–30 Hz),
  `intensity` (0–255), `spatial_balance` (−1.0 left → +1.0 right), and `sharpness`
  (soft envelope → sharp click). Each primitive renders to a timed `PrimitiveEvent`
  schedule (`to_events()`) for continuous-channel use or collapses back to the closest
  3-byte v1 packet (`to_packet()`) for backward compatibility. Factory helpers:
  `calm()`, `alert()`, `directional(bearing)`. Spatial balance encodes left/centre/right
  today; same axis carries angle-of-arrival in the multi-actuator v2 hardware path.
- **Continuous crowd-energy estimation** (`stream/crowd_arousal.py`) — frame-by-frame
  stateful estimator of acoustic crowd state. Three dimensions computed from raw audio:
  `arousal` (0–1, log-scaled RMS), `tension` (0–1, half-wave rectified spectral flux),
  `onset_rate_hz` (events/s over a rolling 2 s window). `to_primitive()` maps directly
  to a `HapticPrimitive`: arousal → intensity, tension → pulse rate and sharpness,
  spatial balance always 0.0 (crowd is omnidirectional). Pure numpy, no I/O, fully
  unit-testable. Foundation for the athlete and performer personas described in the
  Expanded Sensory Vocabulary v2 north-star document.

## [1.3.0] - 2026-06-02

### Added

- **Therapeutic frequency delivery (Pillar 5)** — first implementation of
  the therapy pillar, as a coherent, audiogram-aware, evidence-graded,
  closed-loop system. New `therapy/` package:
  - `therapy/protocol.py` — the `TherapeuticProtocol` data model with an
    ordered `EvidenceGrade` (`anecdotal → preliminary → emerging →
    established`) and explicit contraindication gates. Auditory entrainment
    is barred for seizure disorders on every bundled protocol, and
    `TherapeuticProtocol.gate()` refuses to run for matching conditions. The
    bundled brainwave registry is graded conservatively — none claims
    "established".
  - `therapy/binaural.py` — deterministic binaural-beat generation plus the
    novel part: `prescribe_binaural(audiogram, beat)` places the carrier
    where *both* ears hear best and sets per-ear gains to rebalance an
    asymmetric loss, under a safety amplitude ceiling. A binaural beat only
    works if both tones arrive audible and balanced, which silently fails
    for hearing-loss users on a fixed carrier. CLI:
    `python -m therapy.binaural_cli --beat 10 --audiogram AG.json` (16-bit
    WAV via the stdlib, no audio deps).
  - `therapy/entrainment.py` — delivery-agnostic, cross-modal entrainment.
    Renders a beat frequency as an isochronic pulse train emitted as
    timestamped 3-byte wristband packets (via `stream.haptic_packet`), so a
    rhythm can be *felt* on the wrist when it cannot be heard — the path for
    profound loss. The same protocol can be delivered acoustically or
    haptically; `events_for_protocol()` gates contraindications first.
  - `therapy/adapt.py` — closed-loop, n-of-1 personalisation: a
    deterministic, bounded, explainable controller (in the spirit of
    `learn/`) that learns which entrainment frequency and session length
    work for one person from their own `-1..+1` ratings. `personalise()`
    averages toward liked settings (exploit) or nudges to a neighbouring
    in-band frequency (explore); it stays inside the protocol's EEG band and
    clamps session length to 5–60 minutes. Outcomes persist as JSONL.

## [1.2.0] - 2026-06-02

### Added

- **Plain-English audiogram interpretation** (`audiogram/analyse.py` +
  `python -m audiogram.analyse_cli AG.json [--json]`). Derives, per ear, the
  pure-tone average, severity band, and audiometric *configuration* (flat /
  high-frequency sloping / reverse-sloping / cookie-bite / noise notch /
  indeterminate); across ears, the inter-ear asymmetry plus non-diagnostic,
  sovereign flags (asymmetry worth a professional check, possible noise
  damage, output-safety for profound loss). Exported from the `audiogram`
  package API.
- **Plain-English fitting explanation** (`dsp/explain.py` +
  `python -m dsp.explain_cli AG.json [--json]`). Joins the prescription
  engine (`dsp.audiogram_profile.prescribe`) with the audiogram
  configuration and explains *what the fitting does and why* — where it adds
  the most gain, how that ties to the shape of the loss, and how hard
  compression is working — the reasoning commercial fitting software shows
  only to the clinician.
- **Shared wristband haptic-packet codec** (`stream/haptic_packet.py`): a
  dependency-free single source of truth for the 3-byte BLE packet
  `[sound_class_id, intensity, pattern_id]` with `encode_packet` /
  `decode_packet` and a `HapticPacket` dataclass. `stream/ble_haptic.py`
  re-exports it unchanged. A golden contract test pins the wire format and a
  behavioural parity test proves the v1 firmware decodes what the codec
  encodes, so the Python, v2 Arduino, and app implementations cannot drift.
- **Sound→haptic decision policy** (`stream/haptic_policy.py`): the layer
  between classification and the wrist. `HapticPolicy.decide()` applies
  actionability, a confidence gate, and per-class refractory/debounce, and
  ranks classes by priority (safety sounds outrank ambient) so the wristband
  surfaces one clear signal instead of false buzzes and bursts. `packet_for()`
  bridges policy → mapper → wire via the shared codec.

### Changed

- `pyproject.toml` version is now `1.2.0`, aligned with the release tag.

## [1.1.0]

### Added

- Burgess Principle reference layer in `advocacy/` (gate, adapters,
  sovereign/null receipt tagging, SHA-256 commitments, raw-audio refusal at
  the boundary), plus `examples/reference_integration.py` and the
  `docs/BURGESS_PRINCIPLE.md`, `docs/ADVOCACY_INTEGRATION.md`, and
  `docs/INTEGRATORS.md` contracts.
- Apache 2.0 `LICENSE` and `NOTICE` carrying the OpenHear Sovereign Use
  Addendum.
- Aids-free training scaffolds (local-only, no raw audio):
  `stream/phase2_training.py` (closed-set words, names, alarms, traffic),
  `stream/phase3_open_conversation.py` (passive wear + active recall),
  `stream/phase4_spatial_extended.py` (localisation and extended-band tasks).
- Phase 5 sovereign device bundle generator
  (`hardware/sovereign_device/pipeline.py`,
  `python -m hardware.sovereign_device.pipeline AUDIOGRAM.json ./build`)
  producing firmware plus a sovereign build manifest with hashes, safety
  requirements, regulatory status, and cost-target status. Plan documented
  in `docs/PHASE5_SOVEREIGN_DEVICE.md`.
- Phase 6 listener-preference engine in `learn/`:
  `learn/preferences.py` (A/B choice capture as JSONL),
  `learn/engine.py` (deterministic, bounded adaptive config suggestions),
  `learn/profiles.py` (per-environment saved profiles under
  `~/.openhear/profiles/`).
- Wristband stack: micro:bit v2 prototype firmware
  (`wristband/openhear_firmware.py`), `stream/wristband_runtime.py`
  classifier-to-BLE runtime, `haptic_commander.py` audiogram-weighted
  command tool, `yamnet_classifier.py` standalone classifier, and the
  bundled YAMNet label CSV under `stream/data/`.
- New north-star documents:
  `docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md`,
  `docs/AIDS_FREE_ARCHITECTURE.md`, `docs/RESEARCH_ROADMAP.md`,
  `docs/PRIOR_ART.md`, `docs/GO_TO_MARKET.md`,
  `docs/FUNDING_AND_PARTNERSHIPS.md`, `docs/SOVEREIGN_PHILOSOPHY.md`,
  `docs/HAPTIC_PRIOR_ART.md`, and the `docs/index.md` entry point.
- `core/future_memory.py` running development memory CLI.
- `SECURITY.md` describing the private vulnerability disclosure process,
  including a dedicated path for hearing-safety reports.
- `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1, with project-specific
  additions for ableist language and audiometric data privacy).
- `CHANGELOG.md` (this file).
- GitHub issue templates for bug reports, feature requests, and
  hearing-aid compatibility reports, plus a pull request template and
  `CODEOWNERS`.
- `.github/dependabot.yml` to keep `pip` and `github-actions` dependencies
  up to date.
- CodeQL workflow (`.github/workflows/codeql.yml`) for static security
  analysis of the Python codebase.
- CI lint job using `ruff`, coverage reporting via `pytest-cov`, a packaging
  smoke test (`python -m build` + `pip install` of the wheel) and a Windows
  job to match the README's "Windows 11 primary target" claim.
- Tooling configuration in `pyproject.toml`: `[tool.ruff]`, `[tool.mypy]`,
  `[tool.coverage]`, and a consolidated `[tool.pytest.ini_options]` section.
- `.editorconfig`, `.pre-commit-config.yaml`, and a top-level `Makefile`
  with `lint`, `format`, `test`, `coverage`, `build`, and `clean` targets.

### Changed

- `README.md` substantially expanded: nine-pillar platform expansion,
  OpenHear Wristband and aids-free vision sections, Burgess Principle
  summary, Path 2.5 wristband prototype quick-start, and Phase 2/3/4/5/6
  module documentation. Phase tag on the Learn module corrected (Phase 6,
  not phase 3) and Phase 5 sovereign-device bundle generator surfaced in
  the body of the README and the aids-free roadmap.
- License metadata is now consistent across the repository. `pyproject.toml`
  classifier and `README.md` references that previously said "MIT" have been
  corrected to match `LICENSE` / `NOTICE`, which are
  **Apache License 2.0 with the OpenHear Sovereign Use Addendum**.
- `.gitignore` no longer blanket-ignores `*.json`, `*.png`, and `*.pdf` at
  every depth. Build/output directories are ignored explicitly so that new
  fixtures, schemas, and documentation media are not silently dropped.
- `pytest.ini` has been replaced by the consolidated configuration in
  `pyproject.toml`. Test discovery and behaviour are unchanged.
- `dsp/pipeline.py` migrated off `datetime.UTC` to `timezone.utc` for
  Python 3.10 compatibility.

### Fixed

- License inconsistency between `LICENSE`, `NOTICE`, `pyproject.toml`, and
  `README.md` (previously claimed both Apache-2.0 and MIT in different
  places).
- Removed a small number of unused imports and reordered import blocks
  (auto-fixes from `ruff check --fix`) so that the new lint job is clean.
  No behaviour changes.
