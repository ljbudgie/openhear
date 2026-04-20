# OpenHear Aids-Free Architecture

### A sovereign somatosensory hearing system. No hearing aid. No behind-the-ear receiver. No bone conduction implant. No ear canal device of any kind.

> *"The wristband — or a next-generation version of it — IS the complete hearing system."*

This document is the technical architecture for the standalone configuration of OpenHear: the version of the system in which **nothing is worn at the ear**. Sound is captured at the wrist, classified by edge AI, weighted against the user's audiogram, and rendered to the wearer as a high-resolution multi-frequency haptic field on the skin. The brain — through documented somatosensory plasticity — learns to read that field as auditory information.

This is not amplification. This is not bone conduction. This is not a cochlear implant. It is **direct sensory substitution**: sound delivered to the somatosensory cortex through the skin, and remapped over time by the wearer's own neuroplasticity into a usable representation of the acoustic world.

Audience: open-source firmware, DSP, ML, RTL, mechanical, clinical and HCI contributors who want to build this. The level of detail below is intended to be sufficient to begin contributing modules immediately.

---

## 0. Design principles

1. **No device in or on the ear.** The wrist is the entire system.
2. **Skin is the transducer.** Mechanoreceptors in glabrous and hairy skin are the receivers.
3. **Brain is the codec.** Adaptation, not perfect signal reconstruction, is the design target.
4. **Sub-5 ms end-to-end.** From acoustic event to first haptic edge on the skin.
5. **Sovereign at every layer.** Open silicon, open firmware, open DSP, open models, open data formats, open clinical protocols. The user owns the audiogram, the haptic preference profile, the trained personal model, and the neural-adaptation telemetry.
6. **Superior, not equivalent.** The target is not to imitate biological hearing. It is to exceed it — 360° + vertical spatial awareness, infrasonic and ultrasonic perception, and contextual classification that air-conduction physiology cannot perform.

---

## 1. System overview

```
                     ┌──────────────────────────────────────────────────────┐
                     │                  OpenHear Wristband                  │
                     │                                                      │
World ── acoustic ──▶│  Mic Array (8–16 MEMS, 20 Hz – 96 kHz, beamformable) │
                     │            │                                         │
                     │            ▼                                         │
                     │  Front-end DSP  (AGC, AEC, beamforming, VAD)         │
                     │            │                                         │
                     │            ▼                                         │
                     │  Hearing NPU  (classification, source separation,    │
                     │                audiogram-weighted band synthesis)    │
                     │            │                                         │
                     │            ▼                                         │
                     │  Haptic Renderer (frequency→position, intensity,     │
                     │                   spatial, temporal pattern)         │
                     │            │                                         │
                     │            ▼                                         │
                     │  Multi-Motor Haptic Array  (32–128 actuators)        │
                     │            │                                         │
                     └────────────┼─────────────────────────────────────────┘
                                  ▼
                       Skin → mechanoreceptors → somatosensory cortex
                                  ▼
                       (with training) auditory cortex remap
```

There is no Bluetooth-to-ear leg. There is no receiver. The chain ends on the skin.

A separate, optional, **companion** Bluetooth link exists for: (a) phone-based UI for configuring the personal model, (b) export of the user's data, and (c) interop with the existing OpenHear DSP pipeline for users running both modes during transition.

---

## 2. Skin as the transducer — what the physiology actually allows

### 2.1 Mechanoreceptor classes used

| Receptor      | Sensitive band | Spatial acuity (wrist) | Role in OpenHear |
|---|---|---|---|
| Pacinian (PC) | 40 – 800 Hz, peak ~250 Hz | low (~10 mm) | mid/high frequency carrier; transient detection |
| Meissner (RA1) | 5 – 50 Hz | medium (~3 mm) | onset/offset; rhythm; envelope |
| Merkel (SA1)   | 0.4 – 8 Hz | high (~1 mm) | spatial pattern; static intensity |
| Ruffini (SA2)  | 0.4 – 100 Hz | low | skin stretch; directional cues |

The usable haptic frequency window at the wrist is approximately **5 Hz – 1 kHz** at the body surface. Audio frequencies above this are not represented as raw vibration — they are **encoded** into spatial position, motor identity, and temporal pattern across the array. This is the central insight: we do not transmit a 20 kHz waveform to skin; we transmit a 20 kHz *symbol*.

### 2.2 Spatial resolution target

Two-point discrimination on the volar wrist is ~25–35 mm; on the dorsal wrist ~40 mm; on the fingertips ~2 mm. We target a wrist actuator pitch of **8–12 mm centre-to-centre**, deliberately tighter than two-point discrimination, to exploit *funnelling* and *apparent motion* illusions and yield a perceived spatial resolution finer than the physical receptor field.

- **Minimum viable**: 24 actuators in a single ring (Neosensory-class density).
- **Target v1**: 64 actuators in a 4-ring × 16-column lattice covering the full wrist circumference.
- **Aspirational v2**: 128 actuators extending up the forearm 60–80 mm, enabling a 2D haptic "screen".

### 2.3 Frequency-to-skin mapping

Audible spectrum is partitioned into **N bark-like critical bands** (default N=24 to match cochlear bands). Each band is assigned a triple `(motor_index, drive_freq_Hz, intensity_curve)`:

- `motor_index` — circumferential position; low audio bands → ulnar side, high audio bands → radial side, with the user's audiogram skewing weight toward bands they cannot hear acoustically.
- `drive_freq_Hz` — the actual mechanical frequency the motor outputs, chosen from the receptor-friendly 20–600 Hz window. Different audio bands are distinguished by motor *position* and *drive pattern*, not by drive frequency alone.
- `intensity_curve` — per-user perceptual mapping derived from a calibration session; replaces the audiologist's gain table.

### 2.4 Spatial cues — direction, elevation and distance

- **Azimuth (horizontal direction)**: derived from the wrist mic-array beamformer; encoded as the angular *origin* of a haptic pattern that propagates around the wrist (apparent motion).
- **Elevation**: encoded by *ring index* on the lattice (proximal ring = below, distal ring = above).
- **Distance**: encoded by intensity envelope and decay rate.
- **>360° awareness**: because elevation is independent of azimuth, the wristband can represent the full sphere around the user, including overhead — which biological hearing handles poorly.

---

## 3. Neural adaptation — why this works

### 3.1 Evidence base

- Bach-y-Rita's *tactile-visual sensory substitution* (TVSS, 1969) established that the brain remaps tactile input from a 20×20 grid into a usable visual percept after training.
- Eagleman & Novich's VEST/Neosensory work demonstrates auditory→tactile substitution producing word recognition in deaf adults after a few weeks of daily wear.
- fMRI studies of long-term Neosensory wearers show recruitment of auditory cortex by tactile stimuli — the cortical remap is real and measurable.
- Cochlear-implant research shows central plasticity timelines of weeks to months, even for radically non-natural input codes.

### 3.2 OpenHear adaptation protocol (open, versioned, user-owned)

```
Phase 0  Calibration         (day 0,    ~90 min)   — perceptual mapping, motor thresholds, audiogram import
Phase 1  Phoneme sandbox     (week 1–2, 30 min/d)  — closed-set phoneme → haptic pattern drills
Phase 2  Word & environment  (week 3–6, 30 min/d)  — common words, alarms, name detection, traffic
Phase 3  Open conversation   (week 7+,  passive)   — continuous wear; periodic active-recall checks
Phase 4  Spatial & extended  (month 3+)            — direction, elevation, ultrasonic/infrasonic bands
```

All training data, performance curves, and model checkpoints are stored locally as plain files. The user can export, delete, fork, or share them. There is no cloud account.

### 3.3 Measuring adaptation

Open metrics, logged on-device only:

- Closed-set phoneme accuracy
- Open-set word recognition in quiet / noise (CNC, AzBio analogues)
- Reaction time to spatialised alerts
- Subjective auditory-percept questionnaire (SSQ-12 adapted)
- Optional EEG/fMRI session data ingest (for research collaborators)

---

## 4. The OpenHear Hearing NPU — first-principles silicon

### 4.1 Why a custom NPU

A general-purpose mobile SoC running PyTorch Mobile cannot meet the latency and power budget. The pipeline is small, fixed-shape, and runs continuously — exactly the workload an ASIC wins. We design the chip for *one* job: continuous, personalised, low-latency hearing-as-haptics.

### 4.2 End-to-end latency budget (target ≤ 5 ms)

| Stage                              | Budget    |
|---|---|
| Mic capture + ADC                  | 0.3 ms    |
| Front-end DSP (beamform, AEC, VAD) | 0.7 ms    |
| Bark-band analysis (FFT/filterbank)| 0.5 ms    |
| Audiogram weighting                | 0.1 ms    |
| Classification + scene tag         | 1.5 ms    |
| Haptic render (mapping + envelope) | 0.6 ms    |
| Motor driver chain                 | 0.8 ms    |
| Mechanical rise time (LRA/piezo)   | 0.5 ms    |
| **Total**                          | **5.0 ms**|

Latency is a *first-class* design constraint, not an optimisation target.

### 4.3 NPU architecture

- **ISA base**: RISC-V RV32IMC scalar control core for the orchestration layer.
- **Vector extension**: RVV 1.0, configurable VLEN 256.
- **Custom accelerator block**:
  - 8 × MAC tiles, INT8/INT4 quantised, 2 TOPS sustained at 100 mW envelope.
  - Hardwired bark-filterbank FIR engine (24 bands, fixed, single cycle per sample).
  - Per-band lookup engine for audiogram weighting (single-cycle table read).
  - Haptic scheduler with deterministic, jitter-bounded output to the motor SPI buses.
- **SRAM**: 4 MB on-die, single-cycle, partitioned for model weights / ring buffers / scratch.
- **No DRAM.** The model is small enough to live entirely on-die. This is a hard architectural constraint and the reason latency is achievable.
- **Power envelope**: 80–120 mW in continuous operation; <5 mW in scene-idle.
- **Process target**: 22 nm FD-SOI for v1 (cheap, fab-accessible, low leakage); 12 nm later.
- **Open-source RTL.** Apache-2.0 / CERN-OHL-S. No proprietary IP blocks in the data path.

### 4.4 Fall-back implementation path

Until the ASIC tapes out:

- **v0 prototype**: Raspberry Pi CM4 + Hailo-8L M.2 accelerator, breadboard motor array. ~30 ms latency. Sufficient for adaptation studies.
- **v0.5 prototype**: SiFive HiFive Pro / StarFive VisionFive 2 RISC-V SBC + Coral Edge TPU. ~15 ms latency.
- **v1 FPGA validation**: Lattice ECP5 or Xilinx Artix-7 carrying the open RTL. ~5 ms latency, wearable form factor not yet achievable.
- **v1 ASIC**: as section 4.3.

### 4.5 Audiogram → DSP weighting

The user's audiogram is a vector of hearing thresholds in dB HL across frequency. It is read once, in plain JSON, from the existing `audiogram/` module. The NPU consumes it as a 24-element gain vector applied per bark band, with two derived parameters:

- `dead_band_mask[b]` — bands where threshold > 90 dB HL: that band is *displaced* to a different motor position, not amplified, because amplification cannot recover a non-functioning cochlea but spatial substitution can.
- `recruitment_curve[b]` — compression curve per band, derived from the audiogram contour.

Updating the audiogram is a JSON edit. There is no fitting appointment.

---

## 5. Hardware stack

### 5.1 Mechanical

- Wrist-circumference flexible PCB or rigid-flex segments, hinged.
- Strap material: medical silicone, hypoallergenic, replaceable.
- IP67 sealing.
- Hot-swap battery cartridge (2 × 800 mAh Li-Po), 18–24 h continuous operation.
- Quick-release for charging dock; wireless Qi optional.

### 5.2 Sensing

- 8–16 MEMS microphones (Knowles SPH0645LM4H-class), arranged around the wrist for full-azimuth beamforming.
- IMU (6-axis) for arm-pose compensation: the same world-azimuth sound must not "rotate" on the wrist as the wrist rotates.
- Optional skin-temperature and PPG sensor for actuator safety interlock.

### 5.3 Actuation

- **v0**: 24 × LRA (linear resonant actuators), TI DRV2605L drivers.
- **v1**: 64 × wideband piezo actuators (e.g. TDC TacHammer, Boréas BOS1901 driven piezo) for true 20–600 Hz bandwidth and µs-class onset.
- **v2**: hybrid — piezo for high-band, voice-coil for low-band, electrostatic patches for ultra-low-frequency skin-stretch cues.

### 5.4 Compute

- Hearing NPU (section 4) + companion microcontroller (RP2040 / RISC-V MCU) for power management, USB, BLE companion link.

### 5.5 Wireless (companion only)

- BLE 5.3 to phone for UI, telemetry, and OTA updates of the user's *own* models. **The hearing path does not depend on this radio.** If BLE is off, hearing still works.

### 5.6 Open hardware path

- Schematics: KiCad 8 in `/hardware/wristband/` (planned).
- RTL: Verilog/SystemVerilog under CERN-OHL-S in `/hardware/npu/` (planned).
- Mechanical: FreeCAD/OpenSCAD parametric models in `/hardware/wristband/mech/` (planned).
- Bill of materials sourced from globally-available distributors; no single-source critical parts.
- Contribution model: per-module CODEOWNERS, RFC process for hardware revisions, signed-off-by for clinical-impacting changes.

---

## 6. Software stack

```
/firmware/
  npu/        — Hearing NPU bare-metal runtime (Rust, no_std)
  mcu/        — Companion MCU (Rust + embassy)
  drivers/    — motor, mic, IMU, BLE
/dsp/
  frontend/   — beamform, AEC, VAD, AGC
  bands/      — bark filterbank, audiogram weighting
  haptic/     — frequency→position mapping, spatial render, illusion library
/models/
  classifier/ — environmental sound classifier (≤ 200 kB INT8)
  separator/  — lightweight 2-stream source separator
  personal/   — per-user adaptation deltas (LoRA-style)
/training/
  protocol/   — Phase 0–4 training app (cross-platform, Flutter)
  metrics/    — local logging, export, analysis notebooks
/cli/
  openhear    — single binary for config, export, calibration, model surgery
/mobile/
  android/    — companion UI (Kotlin)
  ios/        — companion UI (Swift)
```

All code MIT or Apache-2.0; RTL CERN-OHL-S; clinical protocol documents CC-BY-SA.

---

## 7. Data sovereignty — enforced at the technical layer

The user *owns*:

1. **Audiogram** — `~/.openhear/audiogram.json`
2. **Haptic preference profile** — `~/.openhear/profile.json` (intensity curves, motor mapping overrides, comfort thresholds)
3. **Personal adaptation model** — `~/.openhear/model.bin` (LoRA delta over the open base model)
4. **Adaptation telemetry** — `~/.openhear/training/*.parquet` (timestamped phoneme accuracy, reaction times)
5. **Raw acoustic recordings** — *not retained by default.* When opt-in capture is on for personal training, files live in `~/.openhear/captures/` and are encrypted with a key the user holds.

Enforcement mechanisms:

- **No network egress in the firmware data path.** The NPU has no IP stack. The companion MCU's BLE stack carries only commands and exported files initiated by the user.
- **Signed firmware, user-controlled keys.** The user holds the signing key; manufacturers do not. A user can sign and load their own firmware. (This is the inverse of the hearing aid industry's lock-down.)
- **Plain-file formats.** JSON for config, Parquet for telemetry, ONNX for models, WAV for any captured audio. No proprietary container.
- **Right to fork.** The personal model is a delta over the open base. The user can publish, fork, or destroy it.
- **No audiologist gatekeeping.** Every parameter that an audiologist would set in proprietary fitting software is a writable field in `profile.json`. Audiologists are welcome collaborators; they are not a key.

---

## 8. Beyond hearing — capabilities a hearing aid cannot have

Once sound is decoupled from the ear and rendered as multi-channel haptics, the system trivially extends past biological limits.

- **Infrasonic** (1–20 Hz) — earthquake precursors, large-vehicle approach, HVAC faults. Mapped to slow proximal-ring SA1 stimulation.
- **Ultrasonic** (20–96 kHz with appropriate MEMS) — bat activity, ultrasonic pest deterrents, industrial leak detection, dog whistles. Mapped to high-band motor positions with rapid temporal pattern.
- **Selective directional gain** — beamform onto a specific speaker by IMU-locked pointing gesture; the rest of the room attenuated.
- **Contextual silencing** — known irritant classes (e.g. crockery clatter) attenuated by the classifier, not by global compression.
- **Multi-source separation** — render two simultaneous speakers to two distinct regions of the wrist, allowing the wearer to "listen" to both in parallel — something binaural air-conduction hearing cannot do.
- **Persistent acoustic memory** — last 30 s ring buffer, replayable on demand to the haptic field. ("What did they just say?" answered without asking.)
- **Cross-modal alarms** — fire alarm, baby cry, name-detection prioritised through the classifier, not buried under a compression curve.

This is why the system is described as **superior**, not equivalent. Biological hearing is a 20 Hz – 20 kHz omnidirectional pressure sensor with poor elevation discrimination and no scene understanding. OpenHear, on the wrist, is none of those things and all of the things they cannot be.

---

## 9. Regulatory pathway

The mechanism of action is **sensory substitution through cutaneous mechanoreception**. It is *not* the mechanism of action of a hearing aid (air-conduction amplification into the ear canal), nor of a bone conduction device, nor of a cochlear implant. This matters because regulatory classification follows mechanism, not indication.

### 9.1 Suggested classifications

| Jurisdiction | Likely classification                                              | Comparator predicate                                |
|---|---|---|
| **UK (MHRA)** | UK MDR 2002 — Class I (initial), Class IIa if claims tighten      | Neosensory Buzz (Class I, sensory substitution)     |
| **US (FDA)** | 510(k) device, **Class II** under sensory substitution / "general wellness" depending on claims | Neosensory Buzz, Brain Port Vision Pro          |
| **EU (MDR)** | Class I or IIa under MDR 2017/745, depending on claims             | Same                                                 |
| **Hearing aid carve-out** | Explicitly *not* a hearing aid and explicitly does not claim restoration of cochlear function. This is critical to the regulatory route. |

### 9.2 Evidence pathway

1. **Phase A — bench**: latency, SPL→haptic mapping fidelity, durability, EMC.
2. **Phase B — single-user adaptation**: the developer (Lewis Burgess) wears v0 daily, logs Phase 0–4 data publicly.
3. **Phase C — multi-user pilot (n≈20)**: deaf and hard-of-hearing volunteers, IRB-equivalent ethics review through an academic partner. Open data.
4. **Phase D — controlled trial**: closed-set phoneme and open-set word recognition vs. baseline, vs. Neosensory Buzz, in quiet and noise. Pre-registered protocol. Open data.
5. **Phase E — submission**: 510(k) / UKCA / CE technical file.

The fastest credible path is **A→B in months, C in ~year 1, D in year 2, E in year 3** — assuming open-source contributor velocity, not commercial timelines.

---

## 10. What lives in this repo, and what is built next

### Already in repo (foundation)
- `core/`, `dsp/`, `audiogram/`, `stream/`, `mobile/`, `hardware/ite-shells/` — the sovereign pipeline for users with existing aids.
- `SOVEREIGN_AUDIO.md` — the data sovereignty framework these all enforce.

### To be added (aids-free system)
- `hardware/wristband/` — KiCad schematics, mechanical CAD, BOM.
- `hardware/npu/` — open RTL for the Hearing NPU.
- `firmware/npu/`, `firmware/mcu/` — runtime.
- `dsp/haptic/` — frequency→position mapping, illusion library, audiogram weighting.
- `models/` — base classifier, separator, and the personal-LoRA scaffold.
- `training/protocol/` — Phase 0–4 training app and metrics.
- `docs/RESEARCH_ROADMAP.md` — the five open questions (companion document).
- `docs/PRIOR_ART.md` — papers, projects, institutions to engage (companion document).

---

## 11. North-star statement

There is no hearing aid in this system.
There is no behind-the-ear receiver.
There is no bone conduction implant.
There is no ear canal device of any kind.

There is a wristband, a personal model, an audiogram, and a brain trained to read them.

The user owns all four.
