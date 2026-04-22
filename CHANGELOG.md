# Changelog

All notable changes to OpenHear will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
once it reaches `1.0.0`. Until then, breaking changes may land in any `0.x`
release; they will be called out under a **Breaking** subsection.

## [Unreleased]

### Added

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

- License metadata is now consistent across the repository. `pyproject.toml`
  classifier and `README.md` references that previously said "MIT" have been
  corrected to match `LICENSE` / `NOTICE`, which are
  **Apache License 2.0 with the OpenHear Sovereign Use Addendum**.
- `.gitignore` no longer blanket-ignores `*.json`, `*.png`, and `*.pdf` at
  every depth. Build/output directories are ignored explicitly so that new
  fixtures, schemas, and documentation media are not silently dropped.
- `pytest.ini` has been replaced by the consolidated configuration in
  `pyproject.toml`. Test discovery and behaviour are unchanged.

### Fixed

- License inconsistency between `LICENSE`, `NOTICE`, `pyproject.toml`, and
  `README.md` (previously claimed both Apache-2.0 and MIT in different
  places).
- Removed a small number of unused imports and reordered import blocks
  (auto-fixes from `ruff check --fix`) so that the new lint job is clean.
  No behaviour changes.
