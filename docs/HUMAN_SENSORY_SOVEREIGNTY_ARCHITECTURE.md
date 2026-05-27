# OpenHear Human Sensory Sovereignty Architecture

### Your senses. Your data. Your world.

This document is the full technical architecture for OpenHear as a human sensory sovereignty platform. It is written so an open-source engineering community can begin contributing immediately across all nine pillars, from the current sovereign DSP pipeline to the future wrist-native, aids-free sensory system.

## The nine pillars

1. The OpenHear Wristband — active environmental intelligence
2. Aids-free architecture — the wristband as the complete hearing system
3. Peak hearing for all users
4. Selective acoustic sovereignty
5. Therapeutic frequency delivery — 30 to 300 Hz
6. iOS and Android native integration
7. Emotional and cognitive acoustic intelligence
8. Social acoustic layer
9. Beyond biological hearing

---

## 0. Non-negotiables

1. **The user is sovereign.** No hidden policy engine gets final authority over the user's senses.
2. **Everything critical works locally.** Capture, classification, profile switching, haptic rendering, and biometric correlation must function on-device.
3. **Open formats at every layer.** JSON, ONNX, Parquet, WAV, KiCad, OpenSCAD, FreeCAD, Verilog/SystemVerilog, Rust, Kotlin, Swift.
4. **Companion first, replacement second, augmentation always.** The platform starts beside today's aids and progresses toward a wrist-native sensory stack.
5. **Biology is a baseline, not a ceiling.** OpenHear restores what has been lost and then goes beyond it.
6. **The Burgess Principle is an engineering requirement.** Any layer that recentralises control fails architecture review.

---

## 1. System overview

OpenHear is a layered system with clear module boundaries.

```text
Environment
  ↓
Perception layer
  • Wrist microphones
  • Ear microphones / existing aid microphones
  • Phone microphones
  • IMU / compass / UWB / GPS
  • Watch biometrics / sleep stages
  • Optional ultrasonic / infrasonic sensors
  ↓
OpenHear sovereignty kernel
  • Audiogram profile
  • Peak-hearing target model
  • Acoustic scene graph
  • Focus policy engine
  • Therapeutic protocol engine
  • Emotional state correlation model
  • Privacy and retention policy
  ↓
Real-time engines
  • DSP pipeline
  • Sound classifier
  • Source separator
  • Spatial mapper
  • Haptic renderer
  • Therapeutic scheduler
  • Anomaly detector
  ↓
Outputs
  • Existing hearing aids
  • Open-fit earbuds / bone-conduction receiver
  • Wrist haptic lattice
  • Apple Watch / Wear OS secondary haptics
  • Local analytics and community profile bundles
  ↓
User-owned storage
  • Local encrypted files
  • HealthKit / Health Connect summaries
  • Optional local-first profile-store mirrors
```

### 1.1 Deployment modes

| Mode | Hardware | Primary value |
|---|---|---|
| Pipeline mode | Phone/desktop + existing aids | Sovereign DSP, audiogram ownership, real-time streaming |
| Companion wristband mode | Wristband + existing aids | Environmental intelligence, haptics, selective focus |
| Aids-light mode | Wristband + minimal receiver | Wrist owns intelligence; ear only delivers |
| Aids-free mode | Wristband only | Somatosensory hearing substitution and augmentation |

### 1.2 Required repository boundaries

Contributors should be able to work on isolated subsystems with stable interfaces.

- `core/` — audiogram, fitting, and user profile schemas
- `dsp/` — real-time audio transforms, compression, feedback cancellation, source conditioning
- `stream/` — Bluetooth LE Audio / classic Bluetooth control and output paths
- `mobile/` — Kotlin/Swift front ends, profile switching, health integration, training protocols
- `hardware/wristband/` — KiCad, BOM, power tree, antenna, mechanics, strap geometry
- `hardware/npu/` — FPGA validation path, RISC-V subsystem, accelerator RTL
- `dsp/haptic/` — band mapping, tacton rendering, spatial illusions, safety limits
- `models/` — classifier, separator, on-device fine-tuning manifests, quantised runtimes
- `training/protocol/` — calibration, adaptation tasks, metrics capture, replay tools
- `profiles/` — focus modes, profession packs, therapeutic protocols, social haptic packs
- `docs/` — architecture, evidence, governance, funding, field notes

### 1.3 Core runtime abstractions

These schemas should exist early and remain versioned.

- `AudiogramProfile` — thresholds, discomfort levels, recruitment, dead regions, preferred compensation
- `PeakTargetProfile` — childhood-reference sensitivity model plus user comfort modifiers
- `RestorationGap` — per-band difference between current accessible perception and target perception
- `AcousticSceneGraph` — source class, identity, confidence, direction, motion, privacy class, anomaly score
- `FocusPolicy` — preserve, suppress, isolate, duplicate-to-haptics, exception rules, exit conditions
- `TherapeuticProtocol` — frequency set, amplitude envelope, duty cycle, schedule, contraindications
- `StateCorrelationModel` — relationships between acoustics, physiology, user corrections, and outcomes
- `HapticPhrasePack` — named social haptic patterns and confirmation rules
- `PrivacyPolicy` — retention, redaction, profile-sharing, microphone null zones, export rights

### 1.4 Open file contract

```text
~/.openhear/
  audiogram.json
  peak_target.json
  profile.json
  focus_modes/*.json
  therapeutic/*.json
  model_manifest.json
  models/base.onnx
  models/personal_delta.bin
  training/*.parquet
  health/correlation_state.json
  phrasepacks/*.json
```

No critical user state should require a proprietary container or a remote service.

---

## 2. Pillar 1 — The OpenHear Wristband: active environmental intelligence

The wristband is the first new hardware surface. Its job is to sense the environment continuously, classify it locally, and render useful environmental information as haptics in real time.

### 2.1 Hardware baseline

- 4- to 8-microphone array distributed across the band or clasp for usable azimuth estimation
- 24-actuator MVP, 64-actuator v1, 96–128 actuator v2 lattice
- 9-axis IMU for orientation compensation and gesture input
- BLE Audio + BLE GATT control plane, with optional UWB for precise spatial alignment in later revisions
- 12–24 hour battery target with magnetic charging and sealed sweat-resistant enclosure
- Skin-safe strap materials and modular actuator cartridges for serviceability

### 2.2 On-device pipeline

```text
Mic array → ADC → front-end DSP → sound classifier → scene graph update
         ↘ beamformer ↗                 ↘ haptic mapper → motor drivers
```

Required first-pass sound classes:

- speech
- my name
- child cry
- doorbell / knock
- alarm / siren
- traffic / bicycle / approaching vehicle
- appliance / machinery anomaly
- crowd
- music / performance
- user-defined custom class

### 2.3 Contributor entry points

- microphone-array geometry simulation
- low-power keyword / event detector models
- haptic pattern authoring tools
- BLE profile definition for control and telemetry-free pairing
- waterproofing and mechanical service design

### 2.4 Immediate build targets

1. Benchtop 24-motor development ring
2. Raspberry Pi / Android tethered classifier demo
3. Wrist orientation compensation layer
4. Local sound library enrolment flow
5. Battery and thermal profiling under continuous wear

---

## 3. Pillar 2 — Aids-free architecture: the wristband as the complete hearing system

OpenHear progresses from companion wristband to full hearing system by moving intelligence onto the wrist and reducing the ear-worn hardware to zero or near-zero.

### 3.1 Architecture states

| State | Capture | Processing | Delivery |
|---|---|---|---|
| Companion | Existing aids + wristband | Phone/wrist | Aids + haptics |
| Aids-light | Wristband | Wrist NPU | Bone-conduction puck or open earbud |
| Aids-free | Wristband | Wrist NPU | Wrist haptic lattice only |

### 3.2 Hearing-specific NPU

The wrist processor is not a general-purpose AI chip with hearing as an afterthought.

Target blocks:

- RISC-V control core
- fixed-function filterbank and beamforming front-end
- quantised MAC array for classification and source separation
- single-cycle audiogram and profile lookup
- deterministic haptic scheduler
- SRAM-resident model store with no DRAM dependency in the real-time path

Latency budget:

| Stage | Target |
|---|---|
| Mic capture + ADC | 0.3 ms |
| Front-end DSP | 0.7 ms |
| Filterbank + audiogram weighting | 0.6 ms |
| Classification / separation | 1.5 ms |
| Haptic render | 0.6 ms |
| Driver + actuator onset | 1.3 ms |
| **End-to-end target** | **≤ 5.0 ms** |

### 3.3 Somatosensory substitution protocol

The skin is the output surface and the brain is the decoder.

Phases:

1. Calibration — thresholds, comfort ceilings, temporal acuity, spatial confusion matrix
2. Phoneme sandbox — consonant and vowel contrasts mapped to stable tactons
3. Word and environment grounding — names, alarms, traffic, key household sounds
4. Open conversation — continuous wear with periodic active recall checks
5. Extended spectrum — ultrasound, infrasound, anomaly cues, full spatial overlays

### 3.4 Minimal receiver path

For early clinical and user validation, OpenHear supports a minimal ear-worn receiver:

- coin-sized bone-conduction driver
- wireless receive-only path
- no microphones and no hidden DSP
- commodity replaceable transducer
- open hardware reference design

### 3.5 Hardware roadmap

1. CM4 / Edge TPU prototype for adaptation experiments
2. RISC-V SBC + quantised runtime for lower-latency validation
3. FPGA validation on ECP5 or equivalent open toolchain path
4. Open ASIC exploration once the model/data path is stable

---

## 4. Pillar 3 — Peak hearing for all users

Peak hearing is not defined as “normal adult hearing.” It is a personalised target based on childhood-range sensitivity and high-resolution access to acoustic structure.

### 4.1 Functional goals

- restore access to 20 Hz–20 kHz where possible through mixed acoustic and haptic delivery
- extend high-frequency and spatial access for hearing adults experiencing age-related loss
- create child-development pathways for earlier intervention and training
- deliver profession-specific acuity modes for sport, music, medicine, engineering, and safety-critical work

### 4.2 Restoration-gap model

```text
RestorationGap = PeakTargetProfile - CurrentAccessibleProfile
```

Each band can be handled in one of four ways:

- preserve biologically
- amplify acoustically
- duplicate to haptics for training
- substitute entirely via haptics

### 4.3 Training and metrics

Required metrics:

- phoneme discrimination
- speech-in-noise performance
- localisation accuracy
- reaction time in alert tasks
- fatigue and clarity self-report
- child-development milestone alignment where relevant

### 4.4 Contributor entry points

- paediatric-safe training flows
- hearing-age reference datasets
- mixed acoustic/haptic fitting logic
- adaptation visualisation dashboards

---

## 5. Pillar 4 — Selective acoustic sovereignty

This pillar turns OpenHear from “better hearing” into “authorable hearing.”

### 5.1 Acoustic scene graph

Every 10–50 ms frame updates a scene graph containing:

- source class
- source identity where enrolled
- azimuth, elevation, and motion
- relevance per active focus policy
- privacy class
- confidence and anomaly state

### 5.2 Focus policy model

```json
{
  "id": "crowd-filter-athletics-v1",
  "targets": ["coach", "teammate", "referee", "starter_pistol"],
  "suppressed_classes": ["crowd"],
  "fallback_haptics": ["siren", "collision_warning"],
  "auto_enter": ["stadium_geofence"],
  "auto_exit": ["event_end"],
  "therapeutic_overlay": null
}
```

### 5.3 First-party modes

- crowd filter
- concert mode
- deep focus
- situational awareness
- sleep mode
- performance mode
- privacy mode

### 5.4 Required engine blocks

- class-conditioned source separation
- directional beam steering
- known-voice preservation
- wake-sound exception handling
- per-class compression / attenuation
- haptic safety fallback for hidden critical cues

### 5.5 Acoustic Profile Store

The store behaves like a code forge:

- signed bundles
- forks and diffs
- semantic versioning
- local mirrors
- community ratings and field notes
- no central approval gate for publication

### 5.6 Privacy mode requirements

- directional null zones
- raw-audio retention off by default
- acoustic fingerprint masking for exports
- visible hardware indicator if capture buffers exist
- auditable retention log controlled by the user

---

## 6. Pillar 5 — Therapeutic frequency delivery: 30 to 300 Hz

The wristband doubles as a programmable therapeutic frequency-delivery system with a strong bias toward evidence-led protocols and user-owned outcomes.

### 6.1 Protocol families

- 40 Hz gamma-aligned entrainment experiments
- 30–80 Hz relaxation and regulation protocols
- 80–150 Hz circulation / muscle-activation exploration
- 150–300 Hz tissue-response and athletic-recovery research

### 6.2 Runtime constraints

- therapeutic sessions must never interfere with critical alerts
- amplitudes remain below skin safety and comfort ceilings established during calibration
- contraindication gates are explicit in protocol files
- sleep-coupled delivery must respect sleep stage and user override

### 6.3 Data model

`TherapeuticProtocol` should include:

- `frequencies`
- `carrier_shape`
- `duty_cycle`
- `session_length`
- `evidence_grade`
- `contraindications`
- `target_outcomes`
- `washout_period`
- `allowed_sleep_stages`

### 6.4 Contributor entry points

- evidence registry tooling
- n-of-1 outcome dashboards
- sleep-stage integration
- skin-comfort and actuation safety benchmarking

---

## 7. Pillar 6 — iOS and Android native integration

The mobile stack is both the first shipping runtime and the control surface for the wristband.

### 7.1 Platform responsibilities

| Capability | Apple stack | Android stack |
|---|---|---|
| DSP companion | Core Audio, AVAudioEngine, Metal / Neural Engine | Oboe, AAudio, NNAPI, TensorFlow Lite |
| Haptics | Core Haptics, WatchKit | VibratorManager, OEM rich haptics |
| Health | HealthKit, Apple Watch | Health Connect, Wear OS |
| Context | Core Location, Maps, ARKit, Shortcuts | Maps SDK, geofences, sensors, automation |
| Model runtime | Core ML / ONNX Runtime | TFLite / ONNX Runtime Mobile |

### 7.2 Integration rules

- location-triggered profile switching is always optional and locally evaluated
- HealthKit / Health Connect store summaries, not raw audio
- third-party SDK access never implies third-party server access
- manual override must beat automation immediately

### 7.3 Required mobile surfaces

- profile editor
- live scene graph inspector
- training app
- therapeutic scheduler
- profession pack installer
- community annotation client

### 7.4 Contributor entry points

- Swift profile editor and Core Haptics runtime
- Kotlin Oboe pipeline integration
- watchOS and Wear OS haptic companion apps
- open SDK and local automation bindings

---

## 8. Pillar 7 — Emotional and cognitive acoustic intelligence

OpenHear learns how the user's body responds to sound and uses that model to reduce overload without taking control away.

### 8.1 Signals

- HRV
- heart rate and slope
- blood oxygen where available
- skin temperature / conductance proxies
- sleep debt
- workload and movement context
- current acoustic scene and active focus policy
- direct user corrections

### 8.2 State model outputs

- calm
- focused
- positively aroused
- overloaded
- fatigued
- sleep fragile

### 8.3 Decision model requirements

- explain every automatic action in plain language
- allow one-tap reversal and local retraining
- distinguish positive arousal from stress using multimodal context
- operate without exporting physiological data off-device

### 8.4 Contributor entry points

- wearable biometrics adapters
- explainability UI
- correction-driven local fine-tuning
- longitudinal outcome analysis tooling

---

## 9. Pillar 8 — Social acoustic layer

OpenHear users should be able to exchange acoustic meaning and community knowledge while preserving privacy.

### 9.1 Shared acoustic presence

Shared sessions allow:

- mirrored focus policies for trusted contacts
- shared live annotations during events or travel
- guardian / child alert mirroring without exposing raw audio
- collaborative training sessions

### 9.2 Haptic communication

A phrase pack contains:

- pattern waveform and actuator sequence
- semantic label
- urgency class
- acknowledgement expectation
- optional cultural / group namespace

### 9.3 Community acoustic mapping

Contributions should include:

- coarse location tile
- acoustic accessibility rating
- structured notes
- relevant profile bundle link
- confidence / consensus state

Raw audio upload is not required for mapping contributions.

### 9.4 Contributor entry points

- phrase-pack schema design
- privacy-preserving venue annotations
- trust / consensus algorithms
- maps integration clients

---

## 10. Pillar 9 — Beyond biological hearing

Once the system is built around an editable sensory pipeline, new senses become a straightforward extension of the same architecture.

### 10.1 Augmentation channels

- ultrasonic capture for machinery, leak detection, specialised instruments, and animal activity
- infrasonic capture for structural resonance, weather-adjacent cues, and seismic signatures
- vertical and behind-wall spatial cues through multi-sensor fusion
- anomaly detection against learned local baselines

### 10.2 Rendering model

Extended-spectrum cues must not overload the base hearing map. They are overlaid as:

- reserved actuator regions
- distinct carrier patterns
- user-selectable urgency tiers
- opt-in profession packs and augmentation modes

### 10.3 Professional augmentation examples

- structural engineer hearing stress signatures in a bridge
- clinician hearing extended-spectrum information through an OpenHear-enhanced stethoscope pipeline
- musician perceiving harmonic overtones and room anomalies beyond unaided human access

### 10.4 Contributor entry points

- ultrasonic / infrasonic sensor evaluation
- anomaly-detection models
- profession-pack authoring
- cross-modal rendering experiments

---

## 11. Cross-cutting technical standards

### 11.1 Safety

- hard ceilings for haptic intensity and duty cycle
- explicit comfort calibration
- fail-open alert paths for critical sounds
- visible state when any recording buffer exists
- reversible automation at all times

### 11.2 Security and privacy

- no mandatory cloud
- optional encrypted local backups with user-held keys
- signed bundles, user-signable firmware, and reproducible builds
- per-feature retention settings in open config files

### 11.3 Validation harnesses

Every major subsystem needs a bench harness:

- latency harness
- actuator distinctness harness
- battery and thermal harness
- speech-in-noise harness
- localisation harness
- therapeutic session logging harness
- profile-switch automation harness

---

## 12. Execution sequence

1. Stabilise schemas and local file contracts
2. Ship mobile and desktop profile editors against current pipeline mode
3. Build 24-actuator benchtop wrist rig and classifier demo
4. Implement scene graph, focus policy engine, and profile bundles
5. Add HealthKit / Health Connect summaries and local state correlation
6. Publish training protocol and adaptation metrics tooling
7. Validate aids-light hardware path and sub-5 ms latency stack
8. Expand to community mapping, phrase packs, and augmentation modes

OpenHear moves forward by publishing interfaces early, proving each layer in public, and never surrendering the sovereignty path to a closed dependency.
