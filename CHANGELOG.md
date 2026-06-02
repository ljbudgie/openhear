# Changelog

All notable changes to OpenHear will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
once it reaches `1.0.0`. Until then, breaking changes may land in any `0.x`
release; they will be called out under a **Breaking** subsection.

## [Unreleased]

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
