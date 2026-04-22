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
