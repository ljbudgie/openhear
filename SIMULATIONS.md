# OpenHear Population Simulations for Neuroplasticity Training

**Status**: Proposed / In Development  
**Purpose**: In-silico Monte Carlo validation of the 5-phase neuroplasticity training protocol for the OpenHear haptic wristband, using only audiogram data plus realistic individual variance.

This document describes the simulation framework that will model how well the somatosensory substitution approach (sound → on-device AI classification → audiogram-weighted directional haptics) enables neural adaptation across a large, diverse virtual population.

## Why These Simulations Matter

The long-term vision of OpenHear is an **aids-free wristband** where the brain learns to interpret wrist vibrations as meaningful auditory information via neuroplasticity (inspired by Bach-y-Rita's tactile sensory substitution work).  

Before committing to hardware pilots or claiming robustness, we want to test — at scale — whether the current haptic encoding, audiogram weighting, and 5-phase protocol are likely to succeed across typical hearing loss profiles.

Simulating ~1,000,000 virtual users lets us:
- Quantify expected success rates by loss severity, asymmetry, and age band.
- Identify failure modes and edge cases (e.g., profound high-frequency loss).
- Guide improvements to haptic patterns, training duration, or motor resolution.
- Provide transparent, reproducible evidence for researchers, clinicians, and the community.

**Important Disclaimers**  
- These are **in-silico statistical models only** — not clinical evidence.  
- OpenHear is experimental and **not a medical device**.  
- Results are hypothetical and intended for research/exploration. Real-world adaptation varies by individual factors (motivation, consistent wear, skin sensitivity, etc.).  
- Always consult a qualified audiologist or clinician. Use at your own risk.

## Simulation Design Overview

### Core Inputs
- **Audiogram**: Imported from the existing `audiogram/` module (JSON format with left/right thresholds at standard frequencies: 250 Hz – 8 kHz).  
- Realistic population sampling: normal hearing + common pathological distributions (age-related high-frequency sloping loss, asymmetric loss, moderate-to-profound cases).  
- Individual variance: age-dependent plasticity decay, skin sensitivity noise, training adherence variation.

### Haptic Rendering Model
- Reuses logic from `haptic_commander.py` (dry-run mode with `--audiogram`).  
- Multi-motor array simulation (configurable: 24 → 64 actuators in lattice).  
- Encoding: YAMNet sound classes + frequency bands → directional patterns (compass-point mapping) + audiogram-weighted intensity (bias toward worse ear).  
- Mechanoreceptor constraints: effective range ~5 Hz–1 kHz; higher frequencies encoded via temporal structure and position illusions.

### Neuroplasticity Adaptation Model
Simple, tunable logistic / exponential learning curve with noise:  
`accuracy = base_rate + learning_rate × exposure × (1 - e^(-k × exposure)) + Gaussian_noise`

Parameters are loosely informed by public sensory substitution literature (including Neosensory Buzz-style studies showing linear gains over weeks and qualitative perceptual shifts around 3–4 months).  
Age and consistency modulate the learning rate.

### Training Phases Simulated
- **Phase 0**: Calibration (perceptual mapping + motor thresholds)  
- **Phase 1**: Phoneme sandbox (minimal-pair discrimination)  
- **Phase 2**: Words & environment (common words, alarms, traffic, names)  
- **Phase 3**: Open conversation (passive daily wear + periodic checks)  
- **Phase 4**: Spatial & extended (direction, elevation, extended frequency bands)

Metrics tracked per phase: phoneme accuracy, word recognition rate, environmental sound identification, spatial accuracy, and “perceptual integration” (vibrations becoming more automatic/subconscious).

### Success Criteria (configurable)
Example: ≥80% accuracy on target tasks after the simulated phase duration, or reaching a defined integration threshold.

## Implementation Plan (tests/simulations/)

A new module will be added at `tests/simulations/simulate_population.py` (and supporting files).

Features to include:
- Efficient vectorized Monte Carlo (numpy) with optional multiprocessing.  
- Support for subsampling (e.g., 10k users for quick runs, full 1M for final statistics).  
- Statistical outputs: overall success rate, breakdowns by subgroups (age, loss severity, asymmetry), confidence intervals, learning curves.  
- Visualizations (matplotlib/seaborn): accuracy histograms, audiogram-vs-success heatmaps, phase-wise progress plots.  
- Sensitivity analysis: vary motor count, latency assumptions, training adherence.  
- Reproducibility: random seeds, results saved as Parquet (consistent with repo data philosophy).  
- Full integration with existing `audiogram/` and `haptic_commander.py` modules where possible.

## How to Run (once implemented)

```bash
# Quick test run
python -m tests.simulations.simulate_population --n-users 10000 --seed 42

# Full population simulation (may take time)
python -m tests.simulations.simulate_population --n-users 1000000 --output results/
```

## Phase 2 dry-run training scaffold

The first implementation of Phase 2 is a local-only dry-run scaffold in
`stream.phase2_training`. It covers the "Words & environment" stage from the
aids-free adaptation protocol without adding model files, datasets, cloud
services, or raw-audio storage.

The built-in catalog includes deterministic targets for alarms, traffic,
household/environmental sounds, a small closed word set, and a configurable
name placeholder. Detailed targets collapse back to the existing wristband BLE
classes (`voice`, `doorbell`, `alarm`, `dog`, `traffic`, `media`, `silence`),
so the current firmware packet ids remain stable.

Examples:

```bash
# List the built-in Phase 2 target catalog.
python -m stream.phase2_training list

# Score one dry-run classifier result and append a local progress JSON record.
python -m stream.phase2_training run \
  --target alarm_smoke \
  --score "Smoke detector=0.90" \
  --session-id phase2-demo \
  --progress /tmp/openhear-phase2-progress.json

# Summarise local progress.
python -m stream.phase2_training summary \
  --progress /tmp/openhear-phase2-progress.json
```

Progress files use the `openhear-phase2-progress-v1` schema and store target
ids, classifier labels, confidence, reaction time, user rating, and outcomes.
They intentionally do not store raw audio or waveforms. These records are
experimental training telemetry only and are not clinical evidence.

## Phase 3 open-conversation scaffold

The Phase 3 implementation lives in `stream.phase3_open_conversation`. It
covers passive daily wear plus periodic active-recall checks for the "Open
conversation" stage without adding cloud services, speaker identity, raw audio
storage, or new wristband firmware packet ids.

Examples:

```bash
# List built-in active-recall prompts.
python -m stream.phase3_open_conversation list-prompts

# Append one passive exposure event using derived classifier/haptic metadata.
python -m stream.phase3_open_conversation passive   --sound-class voice   --source-label Speech   --confidence 0.90   --intensity 128   --environment quiet_home   --progress /tmp/openhear-phase3-progress.json

# Append one active-recall check and summarise longitudinal progress.
python -m stream.phase3_open_conversation recall   --prompt classify_voice   --predicted-class voice   --user-response voice   --progress /tmp/openhear-phase3-progress.json
python -m stream.phase3_open_conversation summary   --progress /tmp/openhear-phase3-progress.json
```

Progress files use the `openhear-phase3-progress-v1` schema and store only
local derived metadata: sound class, source label, confidence, haptic intensity,
pattern id, environment tag, reaction time, user response, rating, and outcomes.
They intentionally exclude raw audio, waveforms, speaker embeddings, cloud ids,
and clinical claims. These records are experimental adaptation telemetry only
and are not clinical evidence.

## Phase 4 spatial/extended scaffold

The Phase 4 implementation lives in `stream.phase4_spatial_extended`. It covers
direction, elevation, and extended-band drills for the "Spatial & extended"
stage without storing raw audio, location traces, biometric identifiers, cloud
services, or clinical claims.

Examples:

```bash
# List built-in spatial and extended-band tasks.
python -m stream.phase4_spatial_extended list-tasks

# Append one spatial-localisation check.
python -m stream.phase4_spatial_extended spatial \
  --task localise_left \
  --predicted-azimuth -80 \
  --confidence 0.85 \
  --user-response answered \
  --progress /tmp/openhear-phase4-progress.json

# Append one extended-band recognition check and summarise progress.
python -m stream.phase4_spatial_extended extended \
  --task band_ultrasonic \
  --predicted-band ultrasonic \
  --user-response ultrasonic \
  --progress /tmp/openhear-phase4-progress.json
python -m stream.phase4_spatial_extended summary \
  --progress /tmp/openhear-phase4-progress.json
```

Progress files use the `openhear-phase4-progress-v1` schema and store only
derived localisation, haptic, timing, environment, rating, and outcome metadata.
They intentionally exclude raw audio, waveforms, location traces, biometric
identifiers, cloud ids, and clinical claims. These records are experimental
adaptation telemetry only and are not clinical evidence.
