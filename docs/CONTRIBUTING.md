# Contributing to OpenHear

Thanks for taking the time to help out!  OpenHear is built by and for
hearing-aid users, so every contribution — code, protocol captures,
audiograms, docs — moves the project forward.

## Getting started

```bash
git clone https://github.com/ljbudgie/openhear
cd openhear
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
pytest -q
```

The full test suite runs without PyAudio, a Noahlink dongle, or real
Bluetooth hardware — those paths are stubbed in `tests/conftest.py`.

## What the automated CI checks

* `pytest -q` on Python 3.10, 3.11, and 3.12 (`.github/workflows/ci.yml`).
* No linter / formatter is enforced *yet*; follow the existing style
  (PEP 8, 4-space indents, Google-style docstrings, `from __future__
  import annotations` at the top of new modules).

## Before opening a PR

1. Make sure `pytest -q` is green.
2. Add or update tests that prove your change works.
3. If you are touching the Noahlink bridge, update
   `docs/PROTOCOL_NOTES.md` with the new evidence.
4. Keep each PR focused on one concern — phases 1 to 6 are recipes for
   *how many* PRs, not how few.

## Types of contributions we especially welcome

* **Protocol captures.**  Record a short Noahlink session, sanitise
  any personal data, and open an issue with the bytes and what action
  was happening.  See `docs/PROTOCOL_NOTES.md` → *How to contribute
  new captures*.
* **Audiograms.**  Anonymised audiogram JSON files go in
  `audiogram/data/` (the `burgess_2021.json` file is the template).
* **Hearing-aid hardware support.**  Add vendor-specific bridges under
  `hardware/<vendor>/`.
* **Tuning presets.**  Share your `~/.openhear/config.yaml` as
  `examples/config-<your-name>.yaml` with a short write-up of the
  hearing loss it targets.

## Safety rules (non-negotiable)

* **Never** loosen the allow-list in `core/write_fitting.py` in the
  same PR that adds the feature — the widening should come only after
  the message type has been confirmed against real devices.
* **Never** remove the backup-before-write hook.
* **Never** implement `core.backup.restore_backup` without test
  coverage against a simulated brick scenario.

## Licence

OpenHear is MIT-licensed (see `LICENSE`).  By submitting a PR you are
licensing your contribution under the same terms.


## Hardware PRs and safety sign-off

Hardware contributions are welcome under CERN-OHL-S-2.0 for designs, MIT or
Apache-2.0 for firmware/software, and CC-BY-SA-4.0 for documentation. If a PR
changes wearer-contacting hardware, haptic drive limits, battery charging, sealing,
or medical/regulatory claims, include a safety sign-off section in the PR body.

Minimum hardware PR checklist:

1. Identify the affected files and intended prototype configuration.
2. State whether the acoustic-to-haptic path still passes the Burgess Principle
   binary test: local processing, no cloud dependency, and no ear-worn dependency.
3. Document maximum actuator intensity, duty cycle, thermal limits, and battery
   protection assumptions.
4. Note biocompatibility and IP67 assumptions; do not imply certification unless
   test evidence is attached.
5. Request review from hardware maintainers listed in `.github/CODEOWNERS` when
   the PR touches `hardware/`, firmware, CAD, PCB, or safety documentation.

Never merge a hardware PR that removes thermal derating, bypasses battery
protection, hides raw-audio/cloud dependencies, or presents a DIY prototype as a
certified hearing aid.
