# OpenHear 🦻

### Your senses. Your data. Your world.

[![Licence: Apache 2.0 + Sovereign Use Addendum](https://img.shields.io/badge/licence-Apache%202.0%20%2B%20Sovereign%20Use%20Addendum-blue.svg)](LICENSE)

**Built on the Burgess Principle** — see [`docs/BURGESS_PRINCIPLE.md`](docs/BURGESS_PRINCIPLE.md).  
→ [`Full documentation index`](docs/index.md)

> **⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE**
> OpenHear is a research platform and public build log, not a certified hearing aid.
> Start at low volume, validate every configuration on your own hardware, and do
> not treat any module in this repository as a substitute for clinical care.

OpenHear is a human sensory sovereignty platform: an open-source audio DSP
pipeline, audiogram/fitting-data toolkit, haptic wristband prototype, advocacy
layer, and hardware research programme for people who want control over their own
senses and their own audiological data.

> *The hearing aid industry charges £3,000–£8,000 for hardware, then locks you out of it.*  
> *Your audiogram is a measurement of your body. It belongs to you.*  
> *OpenHear gives it back.*

---

## Table of contents

- [What OpenHear is](#what-openhear-is)
- [Safety status](#safety-status)
- [Current working modules](#current-working-modules)
- [Quick start](#quick-start)
- [Repository map](#repository-map)
- [OpenHear Wristband](#openhear-wristband)
- [Aids-free vision](#aids-free-vision)
- [Documentation map](#documentation-map)
- [Development and validation](#development-and-validation)
- [Contributing](#contributing)
- [Legal and license](#legal-and-license)
- [Author](#author)

---

## What OpenHear is

OpenHear is an open-source platform for user-controlled hearing and sensory
access. It combines:

- **Audiogram sovereignty** — read, store, visualise, compare, and export hearing
  thresholds in open JSON formats.
- **Fitting-data sovereignty** — inspect and back up hearing-aid fitting data
  through the Noahlink Wireless research path.
- **User-controlled DSP** — tune compression, noise reduction, beamforming,
  feedback cancellation, own-voice bypass, output limiting, and voice clarity
  outside manufacturer black boxes.
- **Local learning** — capture listener preferences and produce deterministic,
  bounded configuration suggestions without cloud services.
- **Haptic environmental awareness** — prototype wristband tooling that maps
  sound classes and audiogram-weighted intensities to local haptic output.
- **Sovereign advocacy** — offline commitments and verification bundles for
  clinical facts under the Burgess Principle.
- **Open hardware research** — documentation and prototypes for safety-first,
  user-owned hearing hardware.

OpenHear is not a clinic, not a manufacturer, and not a replacement for clinical
care. It is a public, inspectable engineering project for people who believe the
user should decide what they hear, when they hear it, how they hear it, and where
their data goes.

## Safety status

OpenHear is experimental. Treat every output path as potentially unsafe until you
have validated it on your own hardware.

- Start at low volume and increase slowly.
- Consult a qualified audiologist before making hearing-aid configuration
  changes.
- Do not rely on software limiters alone for wearer-contacting hardware; read
  [`hardware/safety/README.md`](hardware/safety/README.md) before building.
- Do not publish hearing-safety vulnerabilities, private audiograms, fitting
  data, or other personal information in public issues or pull requests. Use
  [`SECURITY.md`](SECURITY.md) for private vulnerability and hearing-safety
  disclosure.
- The repository does not claim FDA, MHRA, CE/UKCA, or equivalent clearance.

## Current working modules

| Area | What exists now | Where to start |
|---|---|---|
| Audiograms | `openhear-audiogram-v1` loading, validation, visualisation, export, comparison, and manual entry | [`audiogram/README.md`](audiogram/README.md), [`audiogram/data/FORMAT.md`](audiogram/data/FORMAT.md) |
| DSP | Python pipeline stages for compression, filters, noise reduction, voice clarity, feedback cancellation, own-voice bypass, beamforming, output limiting, metrics, and config parsing | [`dsp/`](dsp/), [`docs/TUNING_GUIDE.md`](docs/TUNING_GUIDE.md) |
| Streaming | Recorder, Bluetooth output wrapper, virtual cable helpers, latency tooling, and Phase 2/3/4 local training telemetry scaffolds | [`stream/`](stream/) |
| Core fitting path | Noahlink Wireless HID wrapper, protocol framing, fitting dataclasses, read/write/backup CLIs | [`core/`](core/), [`docs/PROTOCOL_NOTES.md`](docs/PROTOCOL_NOTES.md) |
| Advocacy | Burgess Principle gate, adapters, sovereign/null receipt tagging, SHA-256 commitments, raw-audio refusal, and export bundles | [`docs/ADVOCACY_INTEGRATION.md`](docs/ADVOCACY_INTEGRATION.md), [`examples/reference_integration.py`](examples/reference_integration.py) |
| Learn | Local listener preference capture, bounded adaptive suggestions, and per-environment profiles | [`learn/`](learn/) |
| Wristband | micro:bit v2 prototype firmware, haptic command tool, YAMNet classifier wrapper, BLE runtime, and packet contract | [`wristband/README.md`](wristband/README.md), [`HARDWARE.md`](HARDWARE.md) |
| Hardware | Safety notes, Tympan bridge, ITE shell workflow, assembly guide, BOM, and sovereign-device bundle generator | [`hardware/README.md`](hardware/README.md), [`hardware/safety/README.md`](hardware/safety/README.md) |
| Mobile | Android scaffold with Compose UI, Oboe/JNI audio engine wiring, and skeleton DSP/Bluetooth paths | [`mobile/README.md`](mobile/README.md) |

**Tested hearing aids:**

- Phonak Naída M70-SP (Marvel platform)
- Signia Insio 7AX (Augmented Xperience platform)

**Common hardware used during development:**

- Noahlink Wireless 2 for fitting-data research
- Windows laptop for manufacturer fitting software
- iPhone or Android device for streaming/mobile experiments
- micro:bit v2 for the current wristband prototype

## Quick start

### 1. Install the Python package

OpenHear requires Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

For development tooling:

```bash
make install-dev
```

### 2. Load or create an audiogram

Use the open JSON format documented in [`audiogram/data/FORMAT.md`](audiogram/data/FORMAT.md).

```bash
python -m audiogram.visualiser audiogram/data/burgess_2021.json
```

### 3. Run the desktop DSP pipeline

```bash
python -m dsp.pipeline --test-tone
python -m dsp.pipeline --bypass
python -m dsp.pipeline --metrics-csv metrics.csv
```

Copy [`examples/config.yaml`](examples/config.yaml) to `~/.openhear/config.yaml`
and tune it with [`docs/TUNING_GUIDE.md`](docs/TUNING_GUIDE.md).

### 4. Read fitting data through the Noahlink path

```bash
python -m core.read_fitting --session --verbose
python -m core.noahlink
```

The Noahlink extraction path is still on a separate hardening track. Treat direct
parsing in `core/read_fitting.py` and `audiogram/reader.py` as research code that
needs real-device confirmation before clinical use.

### 5. Try the local training scaffolds

```bash
python -m stream.phase2_training list
python -m stream.phase3_open_conversation list-prompts
python -m stream.phase4_spatial_extended list-tasks
```

These tools store only derived training/progress metadata. They do not store raw
audio, waveforms, speaker identity, location traces, biometric identifiers, or
cloud identifiers.

### 6. Build a Phase 5 sovereign-device bundle

```bash
python -m hardware.sovereign_device.pipeline AUDIOGRAM.json ./build --ear right
```

The manifest records firmware, audiogram, and component-database hashes plus
safety and regulatory metadata without embedding the audiogram thresholds. See
[`docs/PHASE5_SOVEREIGN_DEVICE.md`](docs/PHASE5_SOVEREIGN_DEVICE.md).

### 7. Run the wristband prototype flow

```bash
python -m haptic_commander --audiogram PATIENT.json --sound-class alarm --dry-run
python -m haptic_commander --audiogram PATIENT.json --sound-class alarm
python -m yamnet_classifier --model yamnet.tflite --labels stream/data/yamnet_class_map.csv --limit 10
python -m stream.wristband_runtime --audiogram PATIENT.json --model yamnet.tflite --labels stream/data/yamnet_class_map.csv
```

The current wristband prototype supports seven sound classes: `silence`, `voice`,
`doorbell`, `alarm`, `dog`, `traffic`, and `media`.

## Repository map

```text
openhear/
├── audiogram/   Read, validate, compare, visualise, and export audiograms.
├── dsp/         Real-time DSP stages, config parsing, prescriptions, metrics.
├── stream/      Audio I/O, Bluetooth/virtual-cable helpers, latency, training telemetry.
├── core/        Noahlink Wireless bridge, protocol parsing, fitting data, backup/write CLIs.
├── hardware/    Tympan bridge, safety docs, shell workflow, wristband and device bundles.
├── learn/       Local preference capture, adaptive suggestions, saved profiles.
├── advocacy/    Burgess Principle commitments, receipts, export bundles, adapters.
├── wristband/   Prototype haptic wristband firmware and release-facing docs.
├── mobile/      Android scaffold for native mobile DSP and streaming work.
├── voice/       Voice-reference and analysis helpers.
├── examples/    Sample config, demo, and reference integration.
├── docs/        Architecture, tuning, integration, research, and roadmap docs.
└── tests/       pytest suite; hardware paths are exercised through local stubs.
```

For the longer architecture map, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## OpenHear Wristband

The wristband is a continuous-wear haptic environmental-awareness prototype. It
scans the environment locally, maps sound classes to stable packet IDs, weights
haptic intensity by the user's audiogram, and sends a 3-byte BLE UART packet to a
micro:bit v2 firmware target:

```text
[sound_class_id, intensity, pattern_id]
```

The release-facing prototype documentation is in [`wristband/README.md`](wristband/README.md).
Hardware setup, flashing, wiring, and Windows BLE debugging notes are in
[`HARDWARE.md`](HARDWARE.md) and [`hardware/wristband/README.md`](hardware/wristband/README.md).

## Aids-free vision

The long-term OpenHear vision is a wrist-native sensory system: no hearing aid,
no behind-the-ear receiver, no bone-conduction implant, and no ear-canal device.
Sound is captured, classified, processed against the user's audiogram, and
rendered as structured haptics the brain can learn to read.

That deeper roadmap is intentionally moved out of this landing page:

- Full nine-pillar architecture — [`docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md`](docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md)
- Aids-free subsystem architecture — [`docs/AIDS_FREE_ARCHITECTURE.md`](docs/AIDS_FREE_ARCHITECTURE.md)
- Research roadmap — [`docs/RESEARCH_ROADMAP.md`](docs/RESEARCH_ROADMAP.md)
- Prior art and engagement list — [`docs/PRIOR_ART.md`](docs/PRIOR_ART.md)
- Haptic prior art — [`docs/HAPTIC_PRIOR_ART.md`](docs/HAPTIC_PRIOR_ART.md)
- Go-to-market and showcase applications — [`docs/GO_TO_MARKET.md`](docs/GO_TO_MARKET.md)
- Funding and partnerships — [`docs/FUNDING_AND_PARTNERSHIPS.md`](docs/FUNDING_AND_PARTNERSHIPS.md)

## Documentation map

| Audience | Start here |
|---|---|
| New reader | [`docs/index.md`](docs/index.md) |
| Engineer looking for the code layout | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| User tuning processed audio | [`docs/TUNING_GUIDE.md`](docs/TUNING_GUIDE.md) |
| Integrator or AI coding agent | [`docs/INTEGRATORS.md`](docs/INTEGRATORS.md), [`docs/ADVOCACY_INTEGRATION.md`](docs/ADVOCACY_INTEGRATION.md) |
| Regulator or auditor | [`docs/BURGESS_PRINCIPLE.md`](docs/BURGESS_PRINCIPLE.md), [`docs/SOVEREIGN_PHILOSOPHY.md`](docs/SOVEREIGN_PHILOSOPHY.md), [`NOTICE`](NOTICE) |
| Hardware builder | [`hardware/README.md`](hardware/README.md), [`hardware/safety/README.md`](hardware/safety/README.md), [`hardware/assembly/README.md`](hardware/assembly/README.md) |
| Clinical pilot reader | [`clinical/README.md`](clinical/README.md) |
| Mobile contributor | [`mobile/README.md`](mobile/README.md) |
| Security or hearing-safety reporter | [`SECURITY.md`](SECURITY.md) |

## Development and validation

The package metadata lives in [`pyproject.toml`](pyproject.toml):

- package: `openhear`
- current version: `0.1.0`
- Python: `>=3.10`
- runtime dependencies: NumPy, SciPy, `hid`, PyYAML, and Click
- optional extras: `audio`, `plot`, `ble`, and `dev`

Useful entry points installed by the package include:

- `openhear-pipeline`
- `openhear-read-fitting`
- `openhear-noahlink`
- `openhear-bluetooth`
- `openhear-virtual-cable`
- `openhear-latency`
- `openhear-recorder`
- `openhear-demo`
- `openhear-phase2-training`
- `openhear-phase3-open-conversation`
- `openhear-phase4-spatial-extended`
- `openhear-phase5-device`

The [`Makefile`](Makefile) wraps the common local checks:

```bash
make install-dev   # editable install + ruff, pytest-cov, build, pre-commit
make lint          # ruff check + ruff format --check
make format        # ruff format + ruff check --fix
make test          # pytest -q
make coverage      # pytest with coverage (term + xml)
make build         # python -m build -> sdist + wheel into ./dist
make ci            # lint + tests
```

CI runs ruff, pytest on Python 3.10/3.11/3.12, a Windows Python 3.12 test job,
a wheel/sdist build and install smoke test, and CodeQL static analysis. See
[`.github/workflows/ci.yml`](.github/workflows/ci.yml) and
[`.github/workflows/codeql.yml`](.github/workflows/codeql.yml).

## Contributing

If you wear hearing aids and are frustrated, this is your repo too. If you are a
DSP engineer, audiologist, haptics researcher, embedded developer, hardware
builder, clinician, accessibility advocate, or user with lived experience, open
an issue or a focused pull request.

Before contributing, read:

- [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- [`SECURITY.md`](SECURITY.md)
- [`CHANGELOG.md`](CHANGELOG.md)

The repository includes issue templates for bug reports, feature requests, and
hearing-aid compatibility reports, plus a pull request template and CODEOWNERS
review routing under [`.github/`](.github/).

Contribution rules that matter most:

- Keep PRs focused.
- Add or update tests for code changes.
- Update documentation and [`CHANGELOG.md`](CHANGELOG.md) for user-visible
  changes.
- Do not commit secrets, private audiograms, fitting data, raw audio, or other
  personal information.
- Do not introduce hearing-safety regressions. Preserve MPO ceilings, output
  limiters, feedback control, thermal derating, and battery protections.

## Legal and license

OpenHear does not modify, reverse-engineer, or redistribute proprietary firmware.
It uses Noahlink Wireless 2 and standard fitting software interfaces in the same
research context any hearing care professional would use, and it streams audio
through standard Bluetooth audio paths.

Your audiogram is yours. Your fitting data is yours. This software helps you
access both.

Licensed under the Apache License, Version 2.0, with the OpenHear Sovereign Use
Addendum. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE) for the full terms.

## Author

**Lewis Burgess** — also the author of [The Burgess Principle](https://github.com/ljbudgie/Burgessprinciple).

Contact: <lewisjames@theburgessprinciple.com>

*Two repos. One argument. Your data belongs to you.*
