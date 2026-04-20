# OpenHear Human Sensory Sovereignty Architecture

### The user decides what they hear, when they hear it, how they hear it, and what their acoustic environment does to their body and mind.

This document is the full north-star architecture for OpenHear as a **human sensory sovereignty platform**. It extends the existing sovereign audio pipeline, the wristband concept, and the aids-free architecture into a single buildable system spanning eight pillars:

1. Peak hearing for all users
2. Selective acoustic sovereignty
3. Therapeutic frequency delivery
4. Native iOS and Android integration
5. Emotional and cognitive acoustic intelligence
6. Social acoustic layer
7. Beyond biological hearing
8. Sovereign philosophy enforced at every layer

This is written for contributors who want to start shipping modules now: DSP engineers, embedded developers, mobile engineers, haptics researchers, clinicians, hardware builders, machine-learning contributors, accessibility designers, and users.

---

## 0. Non-negotiables

1. **The user is sovereign.** No hidden policy engine decides what matters in the user's environment.
2. **Everything important works on-device.** Classification, adaptation, focus switching, haptic rendering, and therapeutic scheduling remain local.
3. **Open formats, open interfaces, open hardware.** JSON, Parquet, ONNX, WAV, KiCad, OpenSCAD, Verilog/SystemVerilog, MIT/Apache/CERN-OHL-S where appropriate.
4. **Companion first, replacement second, augmentation always.** OpenHear can start beside current hearing aids and progress toward a wrist-native sensory system.
5. **Biology is the baseline, not the ceiling.** The target is not merely to imitate adult hearing. The target is to restore peak hearing and then exceed it.
6. **The Burgess Principle is a technical requirement.** If a design treats the user as a unit inside somebody else's system, redesign it.

---

## 1. System overview

OpenHear is a layered stack. Each layer can be built independently and still compose cleanly with the rest.

```text
Environment
  ↓
Perception layer
  • Ear microphones / wrist microphones / phone microphones
  • IMU, UWB, GPS, watch biometrics, sleep stages
  • Optional ultrasonic / infrasonic sensors
  ↓
OpenHear Sovereignty Kernel
  • Audiogram model
  • Scene graph
  • User profile + focus modes
  • Policy engine chosen by the user
  • Health correlation engine
  ↓
Real-time engines
  • DSP pipeline
  • Classifier + source separator
  • Spatial mapper
  • Haptic renderer
  • Therapeutic scheduler
  ↓
Outputs
  • Hearing aids / open-fit earbuds / bone conduction receiver
  • Wrist haptic lattice / Apple Watch / Wear OS
  • Local insights, automations, community profile sync
  ↓
User-owned storage
  • Local files
  • HealthKit / Health Connect
  • OpenHear profile store mirrors
```

### 1.1 Deployment modes

| Mode | What ships first | Role |
|---|---|---|
| **Pipeline mode** | Existing phone/desktop DSP + hearing aids | Immediate sovereignty over amplification, own voice, feedback, and streaming |
| **Companion wristband mode** | Wristband + existing aids | Environmental intelligence, haptic awareness, selective focus, therapeutic delivery |
| **Aids-light mode** | Wristband + minimal receiver | Wrist owns capture and processing; ear device only delivers |
| **Aids-free mode** | Wristband only | Full sensory substitution and augmentation through haptics |

### 1.2 Core runtime abstractions

- `AudiogramProfile` — thresholds, recruitment curves, dead-band mask, childhood-peak target curve
- `AcousticSceneGraph` — sources, classes, directions, confidence, motion vectors
- `FocusPolicy` — what to amplify, attenuate, isolate, mask, log, or ignore
- `TherapeuticProtocol` — frequencies, duty cycle, timing, contraindication gates
- `StateCorrelationModel` — links acoustic conditions with HRV, heart rate, sleep, workload, and user actions
- `SocialPatternPack` — shared haptic phrases, group modes, acoustic annotations
- `PrivacyPolicy` — microphone retention, null zones, profile sharing, local-only restrictions

These abstractions should exist as versioned schemas before the full hardware exists. That lets the repo accept contributions now.

---

## 2. Pillar 1 — Peak hearing for all users

The target is the best auditory access a human nervous system can plausibly use: the frequency resolution, sensitivity, and learning agility associated with childhood hearing, extended by haptic substitution where biological hearing is absent or degraded.

### 2.1 Functional target

- Restore access to the equivalent of **20 Hz–20 kHz** perception for users with partial or severe loss.
- Preserve and extend hearing users' access to high-frequency and spatial cues lost with age.
- Use biological hearing where it exists and haptic substitution where it does not.

### 2.2 Haptic array specification

OpenHear should support three actuator tiers:

| Tier | Array | Use |
|---|---|---|
| **MVP** | 24 actuators, single-ring or 2×12 | Environmental awareness, basic speech cues, onboarding |
| **v1** | 64 actuators, 4 rings × 16 columns | Speech intelligibility, direction, therapeutic patterns, limited extended spectrum |
| **v2** | 96–128 actuators, wrist + proximal forearm lattice | Dense speech cues, spatial elevation, ultrasonic/infrasonic overlays, professional use |

Recommended rendering split:

- **24 bark-like audio bands** for baseline speech/environment mapping
- **8 transient bands** for consonant edges, alerts, and warnings
- **4 spatial channels** for elevation/distance refinement
- **4 therapeutic carriers** in the 30–300 Hz wellness window
- **2 reserved channels** for social/haptic language overlays

### 2.3 Peak hearing model

Each user gets two curves:

1. **Current profile** — what they hear now
2. **Peak target profile** — a childhood-reference sensitivity model normalised for comfort and training stage

The system computes a `RestorationGap` per frequency band:

```text
RestorationGap = PeakTargetSensitivity - CurrentAccessibleSensitivity
```

That gap determines whether a band is:

- amplified acoustically,
- represented haptically,
- duplicated for training,
- or suppressed to avoid overload.

### 2.4 AI training protocol

Training is progressive, explicit, and measurable.

1. **Calibration** — motor thresholds, comfort ceilings, temporal acuity, two-point discrimination, audiogram import
2. **Symbol grounding** — phonemes, music intervals, alarms, named environmental sounds
3. **Mixed reality exposure** — biological hearing + haptic substitution together
4. **Gap filling** — present only the frequencies the user lacks
5. **Extended spectrum** — ultrasonic, infrasonic, and predictive anomaly cues

The training app logs:

- phoneme discrimination,
- speech-in-noise performance,
- direction finding,
- recall of haptic phrases,
- adaptation speed by band,
- self-reported fatigue and clarity.

### 2.5 Personalisation

OpenHear must never bluntly duplicate the whole spectrum to every output. It should:

- fill the user's absent or weak bands first,
- let partially-hearing users keep biological low-latency cues,
- move dead bands onto higher-information haptic positions,
- and expose all mappings in editable profile files.

### 2.6 Child development track

OpenHear should maintain a dedicated paediatric configuration:

- lower-intensity safe defaults,
- developmentally tuned training games,
- speech and language milestone tracking,
- optional parent/clinician shared reports exported from the child's device,
- early-warning comparisons against age-expected detection curves.

This is not only for diagnosed deafness. It is also for **early drift detection** before formal diagnosis.

---

## 3. Pillar 2 — Selective acoustic sovereignty

OpenHear does not just amplify. It lets the user author the rules of the acoustic world around them.

### 3.1 Acoustic scene graph

The real-time engine should maintain a scene graph with:

- source class (`speech`, `crowd`, `traffic`, `child_cry`, `ATC`, `instrument_cello`, `monitor_beep`)
- source identity when available (`coach`, `teammate`, `my_child`, `my_own_instrument`)
- location (azimuth, elevation, distance, motion)
- relevance score per active profile
- privacy class (`private`, `public`, `sensitive`, `unknown`)

This graph is the substrate for all focus modes.

### 3.2 Focus mode architecture

Each focus mode is a versioned `FocusPolicy` bundle:

```json
{
  "id": "deep-focus-office-v1",
  "targets": ["foreground_speech"],
  "suppressed_classes": ["office_hvac", "keyboard", "crowd", "coffee_machine"],
  "priority_exceptions": ["fire_alarm", "my_name", "calendar_alert"],
  "spatial_bias": "front_60_deg",
  "therapeutic_overlay": null,
  "auto_exit_conditions": ["conversation_ended", "heart_rate_spike"]
}
```

Required first-party modes:

- **Crowd filter**
- **Concert mode**
- **Deep focus**
- **Situational awareness**
- **Sleep mode**
- **Performance mode**
- **Privacy mode**

### 3.3 Required signal-processing blocks

- low-latency speaker separation
- class-conditioned noise suppression
- directional beam steering
- own-voice and known-voice matching
- wake-sound exceptions
- per-class compression profiles
- haptic fallback if acoustic isolation would hide safety-critical sound

### 3.4 Profession packs

Professional packs are just specialised focus policies plus tuned models. Initial packs:

- surgery
- aviation
- firefighting / dispatch
- orchestral strings
- field sports
- endurance athletics
- emergency response sleep alerting

Each pack includes:

- ontology of relevant sounds,
- default attenuation rules,
- training corpus needs,
- validation scenarios,
- sharable haptic patterns.

### 3.5 Acoustic Profile Store

The Profile Store should work more like Git than an app store:

- signed profile bundles
- forks, diffs, merge requests
- ratings and field notes
- no central approval gate for publication
- optional local mirrors for offline use
- trust metadata rather than censorship

Minimum bundle contents:

- `focus_policy.json`
- `profile_card.md`
- `model_manifest.json`
- `validation_notes.md`
- `license`

### 3.6 Privacy mode

Privacy is a first-class acoustic mode, not a settings page.

Hardware and software requirements:

- directional microphone null zones for private sectors
- on-device redaction of saved audio by default
- acoustic fingerprint masking for exported samples
- zero-retention mode for sensitive contexts
- clear hardware indicator when any capture buffer exists
- user-auditable logs of what was retained and why

The user also decides what **not** to be heard doing: meetings, counselling, legal consultations, parenting, prayer, recovery, rest.

---

## 4. Pillar 3 — Therapeutic frequency delivery (30–300 Hz)

OpenHear's therapeutic layer is a programmable haptic frequency-delivery system linked to sleep, recovery, stress, and focus.

### 4.1 Delivery model

Therapeutic outputs run on the same actuator lattice, with separate scheduling and safety gates.

Modes:

- **background regulation** — low-amplitude patterns during work or travel
- **active session** — deliberate 5–30 minute protocols
- **sleep-coupled delivery** — REM/deep-sleep timed sessions
- **recovery mode** — post-exercise or post-stress intervention

### 4.2 Initial evidence-led protocol library

Initial protocol families:

- **40 Hz gamma support**
- **low-frequency relaxation bands** (30–80 Hz)
- **mid-band stimulation for circulation/muscle activation** (80–150 Hz)
- **higher-band mechanostimulation for tissue response exploration** (150–300 Hz)

Every protocol must include:

- evidence grade,
- target outcome,
- contraindications,
- session length ceiling,
- washout period,
- user-reported effects form.

### 4.3 Sleep architecture

Sleep mode combines:

- Apple Watch / Wear OS sleep stage input,
- environmental attenuation policy,
- selective exception detection,
- therapeutic protocol scheduler.

Example policy:

- deep sleep: strong attenuation, child cry + emergency alert exceptions, no therapeutic pattern unless explicitly enabled
- REM: optional gentle 40 Hz or user-selected protocol
- awakening window: taper-in environmental awareness instead of abrupt alarm

### 4.4 Health data integration

HealthKit / Health Connect should store:

- session timestamps,
- protocol IDs,
- HRV before/during/after,
- sleep stage adjacency,
- perceived stress,
- workout recovery status,
- adverse-effect flags.

OpenHear writes summaries to the user's health record and keeps the higher-resolution model state locally.

### 4.5 Wellness and research architecture

To preserve the open-source path:

- protocol library ships as **wellness support**, not clinical treatment claims,
- research mode is opt-in,
- community evidence is versioned and public,
- higher-claim protocols remain clearly marked as exploratory until evidence matures.

---

## 5. Pillar 4 — Native iOS and Android integration

The phone and watch stack already contains most of the non-custom compute OpenHear needs.

### 5.1 Native role split

| Layer | iOS / watchOS | Android / Wear OS |
|---|---|---|
| Real-time DSP companion | Core Audio, AVAudioEngine, Metal / Neural Engine paths | Oboe/AAudio, TensorFlow Lite / NNAPI |
| Haptics | Core Haptics, WatchKit haptics | VibratorManager, RichTap/vendor haptic APIs |
| Health | HealthKit | Health Connect |
| Automation | Shortcuts, Focus Filters, Background Tasks | App Actions, WorkManager, Automation apps |
| Maps/context | Core Location, Maps, geofences | Fused Location Provider, Maps SDK, geofences |

### 5.2 Latency architecture

Real-time path targets:

- wrist-local haptic decisions: **≤ 5 ms**
- phone-assisted hearing-aid pipeline: **≤ 20 ms**
- BLE control-plane updates: **≤ 50 ms**
- profile-switch trigger response: **< 250 ms**

Bluetooth split:

- **hearing path**: local on wrist or phone, avoiding round trips where possible
- **control path**: BLE / LE Audio metadata / profile updates
- **high-bandwidth sync**: optional Wi-Fi/local export for model or profile transfers

### 5.3 Data model

Suggested shared entities:

- `OpenHearProfile`
- `OpenHearFocusEvent`
- `OpenHearTherapySession`
- `OpenHearStressCorrelation`
- `OpenHearAcousticAnnotation`
- `OpenHearChildDevelopmentSnapshot`

Store boundaries:

- HealthKit / Health Connect: summaries, outcomes, correlations, consented metadata
- local encrypted storage: raw model features, per-source confidence histories, optional captured audio

### 5.4 Location-triggered profiles

Geofenced or semantic triggers:

- stadium → crowd filter or athlete mode
- concert venue → concert mode
- school pickup → situational awareness + child voice priority
- hospital theatre → surgery pack
- office calendar event → deep focus
- home bedtime window → sleep mode

Location rules are editable and always overridable by the user.

### 5.5 Open SDK

Third-party SDK priorities:

- read and write focus policies
- trigger mode switches
- register sound classes and profession packs
- receive privacy-preserving state callbacks
- annotate venues and acoustic environments
- import/export profile store bundles

No SDK method should expose user data to third-party servers by default.

---

## 6. Pillar 5 — Emotional and cognitive acoustic intelligence

OpenHear should learn how the user's nervous system reacts to sound, then act before overload arrives.

### 6.1 Input signals

- HRV
- resting and active heart rate
- respiratory rate where available
- blood oxygen where available
- skin temperature / electrodermal proxy where available
- sleep debt
- recent workout load
- calendar context
- current acoustic scene

### 6.2 Personal state model

The state model is personal, local, and longitudinal.

Outputs:

- `calm`
- `focused`
- `positively_aroused`
- `overloaded`
- `fatigued`
- `sleep_fragile`

The system should bias toward transparency:

- show the user why a state was inferred,
- show what changed,
- allow one-tap correction,
- retrain from those corrections locally.

### 6.3 Automatic adaptation logic

Examples:

- HRV drops + crowd class rises + approach to station geofence → offer or auto-enable crowd filter
- high workload calendar block + repeated keyboard/HVAC exposure + rising fatigue score → enter deep focus with periodic safety check-ins
- concert venue + elevated heart rate + stable HRV + manual positive feedback → preserve energy instead of suppressing it
- poor sleep score + child monitor exception armed → keep sleep mode conservative and prevent aggressive therapeutic overlays

### 6.4 Notification architecture

Notifications should be:

- sparse,
- explainable,
- reversible,
- and available as haptic-only, silent, or visual.

Required insight types:

- “This environment usually lowers your HRV.”
- “You focus better when keyboard and HVAC are suppressed.”
- “Your sleep improved on nights when child-voice filtering was enabled.”
- “This concert profile raised arousal without increasing stress.”

### 6.5 Privacy guarantees

- no cloud model training required
- HealthKit / Health Connect remain the external system of record for outcome summaries
- user can delete the correlation model without deleting health data
- model export uses open formats

---

## 7. Pillar 6 — Social acoustic layer

OpenHear users should be able to share acoustic meaning, not just settings.

### 7.1 Shared acoustic presence

Users can join a shared session where:

- one user's profile is mirrored to another,
- live venue annotations are shared,
- the same performance or environmental stream is rendered through each user's preferred outputs,
- guardians and family members can mirror alerts without giving up privacy.

### 7.2 Haptic language

OpenHear should support a user-owned haptic phrasebook:

- `presence`
- `look-left`
- `danger`
- `slow-down`
- `I'm here`
- `this matters`
- `I love this moment`

Phrase packs are:

- editable,
- culture- and family-specific,
- sharable like profiles,
- layered on top of the acoustic engine rather than replacing speech or sign.

### 7.3 Community acoustic mapping

Contributors should be able to publish:

- venue acoustic notes,
- dangerous masking zones,
- quiet therapeutic spaces,
- child-friendly sound environments,
- profession-specific acoustic hazards.

Each record should support:

- anonymous or attributed posting,
- community verification,
- timestamped updates,
- machine-readable tags for automatic profile suggestions.

### 7.4 Acoustic accessibility ratings

Map overlays should expose:

- hearing-loop availability,
- quiet-room availability,
- reverb severity,
- crowd masking severity,
- alert audibility,
- child-cry / parent monitoring suitability,
- first-responder acoustic load.

This turns acoustic accessibility into infrastructure, not anecdote.

---

## 8. Pillar 7 — Beyond biological hearing

OpenHear's augmentation layer begins once the user controls the base spectrum.

### 8.1 Extended-spectrum sensing

Required hardware roadmap:

- standard MEMS mic array for 20 Hz–20 kHz
- optional ultrasonic MEMS path up to ~96 kHz
- low-frequency vibration / pressure sensing for sub-20 Hz events
- IMU and spatial fusion for full-sphere mapping

### 8.2 Rendering strategy

Extended-spectrum content should not drown ordinary perception. It should be translated into:

- reserved haptic lanes,
- specific temporal motifs,
- or profile-controlled overlays.

Examples:

- ultrasonic leak signature → fast localised shimmer
- infrasonic structural resonance → slow pulsed warning band
- anomaly detection → distinct “this does not fit” pattern

### 8.3 Predictive environmental awareness

The anomaly engine compares current acoustic fingerprints with expected local patterns.

Potential uses:

- unusual traffic approach from a blind corner,
- unusual machinery tone in a workshop,
- missing expected alarm in a monitored environment,
- structural resonance drift,
- unusual crowd dynamics in a public venue.

### 8.4 Sports and professional augmentation

Build domain packs that surface cues humans already use implicitly:

- ball spin
- bat/ball seam or impact signature
- instrument harmonic isolation
- stethoscope overtones
- bridge or airframe stress harmonics
- dispatch-radio intelligibility prioritisation

This is where OpenHear stops being only assistive and becomes performance infrastructure.

---

## 9. Pillar 8 — Sovereign philosophy enforced at every layer

Sovereignty must survive contact with code, hardware, law, and partnership pressure.

### 9.1 Technical enforcement

- user-held firmware signing keys
- no mandatory account
- no mandatory cloud relay
- no opaque model files in critical path
- exportable schemas for every important state object
- local-first profile store mirrors
- user-readable audit log for profile changes, automations, and retention events

### 9.2 Governance

OpenHear should maintain:

- public RFCs for architecture changes
- explicit “Burgess Principle review” on major design proposals
- separate safety review for anything touching therapeutic output or high-SPL audio
- public benchmark datasets where consent allows
- transparent deprecation policies for profile formats and SDK APIs

### 9.3 Licensing strategy

- software: MIT or Apache-2.0
- hardware design and RTL: CERN-OHL-S
- documentation and protocol documents: CC-BY-SA where appropriate
- community profile bundles: permissive by default, user-selectable

### 9.4 Threat model

OpenHear should explicitly defend against:

- vendor capture,
- cloud dependence,
- coercive telemetry,
- inaccessible profile formats,
- profile censorship by a central operator,
- silent therapeutic/autonomic changes the user did not request,
- “AI convenience” features that hide decisions from the user.

---

## 10. Immediate engineering workstreams

The architecture is broad. The contribution entry points are not.

### 10.1 Schemas and core libraries

Ship first:

- `schemas/openhear_profile.schema.json`
- `schemas/focus_policy.schema.json`
- `schemas/therapy_protocol.schema.json`
- `schemas/acoustic_annotation.schema.json`
- `schemas/state_correlation.schema.json`

### 10.2 Runtime modules

Open repo targets:

- `dsp/haptic/`
- `models/classifier/`
- `models/separator/`
- `training/protocol/`
- `sdk/ios/`
- `sdk/android/`
- `profiles/`
- `docs/regulatory/`

### 10.3 Hardware tracks

- wristband actuator test rig
- microphone-array geometry validation
- latency instrumentation rig
- watch + wristband cooperative haptics
- battery and thermal safety validation

### 10.4 Research tracks

- psychophysics of wrist bandwidth
- therapeutic protocol evidence registry
- biometrics-to-acoustic-state modelling
- child development adaptation studies
- privacy-preserving community acoustic maps

---

## 11. Success criteria

OpenHear is succeeding when all of the following are true:

1. A user can import their audiogram and own profile without asking permission.
2. A user can decide which sounds matter in a stadium, an office, a ward, a cockpit, or a bedroom.
3. A user's stress and sleep data help them shape their acoustic environment without leaving their device.
4. Two users can share haptic meaning without surrendering privacy.
5. The system delivers information beyond ordinary biological hearing.
6. Every important layer is forkable.

If a feature weakens any of those, it does not belong here.
