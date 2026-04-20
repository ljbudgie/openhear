# OpenHear Research Roadmap — 15 Critical Open Questions

This roadmap identifies the highest-value open questions across all nine pillars of OpenHear. Each question includes why it matters, a suggested approach, and anchor literature or prior art that contributors can use immediately.

---

## Q1. What is the maximum usable information bandwidth of the wrist and forearm for auditory substitution?

**Why it matters.** Pillars 1, 2, 3, and 9 all depend on how much structured acoustic information the skin can carry.

**Suggested approach.**
- Build 24-, 64-, and 128-actuator rigs across wrist-only and wrist-plus-forearm layouts.
- Measure channel capacity across spatial, temporal, and mixed encodings.
- Compare speech, localisation, and anomaly-detection tasks.

**Existing literature.**
- Bach-y-Rita et al. (1969), *Vision substitution by tactile image projection*.
- Novich & Eagleman (2015), *Using space and time to encode vibrotactile information*.
- Reed et al. (2019), *A phonemic-based tactile display for speech communication*.

---

## Q2. Which actuator topology best balances bandwidth, latency, comfort, sleep wearability, and manufacturability?

**Why it matters.** Pillars 1, 2, and 5 fail if the actuation stack is too slow, too hot, too bulky, or too power-hungry.

**Suggested approach.**
- Benchmark LRA, piezo, voice-coil, and hybrid arrays on rise time, thermal profile, comfort, and perceived distinctness.
- Run overnight and exercise tests to capture sweat, sleep, and motion behaviour.
- Publish open BOM trade-off tables.

**Existing literature.**
- Choi & Kuchenbecker (2013), reviews on vibrotactile actuation.
- TDK haptics documentation.
- Boréas Technologies piezo driver documentation and evaluation notes.

---

## Q3. What adaptation curve does a dense 24-band, 32-band, or 64-band haptic encoding produce compared with current low-channel systems?

**Why it matters.** The aids-free architecture depends on whether richer structured haptics materially improve usable perception and shorten training time.

**Suggested approach.**
- Run developer-led longitudinal studies immediately.
- Expand to small deaf, hard-of-hearing, and hearing cohorts.
- Track phoneme accuracy, open-set word recognition, localisation, and fatigue over weeks and months.

**Existing literature.**
- Perrotta et al. (2021), *Deciphering sounds through patterns of vibration on the skin*.
- Huang et al. (2017), Neosensory / VEST adaptation studies.
- Cochlear-implant plasticity literature.

---

## Q4. How should an audiogram and a peak-hearing target be translated into a mixed acoustic-plus-haptic restoration map?

**Why it matters.** Pillar 3 requires a formal way to decide what should be amplified, duplicated, substituted, or suppressed.

**Suggested approach.**
- Implement and compare `RestorationGap` strategies for partially hearing users.
- Measure speech-in-noise, user comfort, and overload under different band-allocation rules.
- Test child and adult onboarding variants.

**Existing literature.**
- NAL-NL2 and DSL fitting logic.
- Electric-acoustic stimulation research.
- Residual-hearing sensory-substitution literature.

---

## Q5. What onboarding protocol safely teaches users frequencies they have never perceived or have not perceived for years?

**Why it matters.** Pillars 2 and 3 need a training path that increases access without overwhelming the user.

**Suggested approach.**
- Compare progressive band unlocks with full-band exposure.
- Add explicit fatigue scoring and rest logic.
- Develop child-safe and adult-late-onset variants.

**Existing literature.**
- Cochlear implant rehabilitation protocols.
- BrainPort training literature.
- Auditory training for age-related hearing loss.

---

## Q6. What is the true end-to-end latency floor of the open wristband stack, and where do the dominant costs sit?

**Why it matters.** Pillars 1 and 2 only work conversationally if latency remains in the low-millisecond range.

**Suggested approach.**
- Build a closed-loop latency rig with acoustic trigger and accelerometer or laser vibrometry measurement at the actuator surface.
- Break out mic, DSP, classification, render, driver, and mechanical onset costs separately.
- Compare mobile, SBC, FPGA, and ASIC-oriented paths.

**Existing literature.**
- Hearing-aid latency studies.
- Embedded DSP benchmarking papers.
- Wearable haptics timing reports where available.

---

## Q7. Which on-device model architecture best separates “what matters” from background in real time?

**Why it matters.** Pillar 4 depends on scene-aware selective hearing that is fast, predictable, and explainable.

**Suggested approach.**
- Compare compact source-separation models, speaker-conditioned enhancement, and class-aware suppression pipelines.
- Evaluate false suppression of critical cues, battery cost, and user trust.
- Validate against athletics, music, transport, and home environments.

**Existing literature.**
- Conv-TasNet, DPRNN, and SepFormer lineages.
- Hearing-aid scene-analysis literature.
- On-device speech-enhancement work from Apple, Google, and related mobile ML teams.

---

## Q8. How accurately can OpenHear preserve user-critical voices and sounds in dynamic environments?

**Why it matters.** Parent mode, coach mode, first-responder sleep mode, and surgeon mode fail if the one important cue is missed.

**Suggested approach.**
- Build local voice and sound enrolment with no cloud embeddings.
- Test recognition across noise, reverberation, and distance.
- Add haptic fallback when confidence drops.

**Existing literature.**
- Speaker verification research.
- Child-cry detection literature.
- Alarm-detection and patient-monitoring studies.

---

## Q9. Which 30-300 Hz therapeutic protocols have the strongest evidence and safest implementation path on the wrist?

**Why it matters.** Pillar 5 should start with evidence-led delivery rather than speculative pattern design.

**Suggested approach.**
- Create a protocol registry graded by evidence quality.
- Begin with 40 Hz, low-frequency relaxation, and recovery candidates.
- Run local n-of-1 studies through HealthKit and Health Connect with explicit adverse-event logging.

**Existing literature.**
- Clements-Cortes and vibroacoustic therapy literature.
- 40 Hz sensory stimulation work from MIT Picower / Li-Huei Tsai collaborators.
- Whole-body vibration reviews on bone, circulation, and muscle outcomes.

---

## Q10. How should sleep-stage-linked filtering and therapeutic scheduling be timed?

**Why it matters.** Pillars 4 and 5 converge in sleep mode, one of OpenHear's most broadly relevant sovereignty use cases.

**Suggested approach.**
- Compare stage-triggered and phase-window-triggered delivery using Apple Watch and Wear OS sleep-stage inputs.
- Track awakenings, HRV, sleep continuity, and subjective rest.
- Separate parents, shift workers, and first responders into distinct protocol families.

**Existing literature.**
- Closed-loop sleep stimulation research.
- Wearable sleep-stage validation studies.
- Caregiver alerting literature.

---

## Q11. Which biomarkers best distinguish positive arousal from stress in acoustic contexts?

**Why it matters.** Pillar 7 should not treat a concert high like a panic response.

**Suggested approach.**
- Combine HRV, heart-rate slope, motion, location, calendar context, and correction signals into a personal classifier.
- Test across commuting, concerts, sport, and focused work.
- Keep all model training local.

**Existing literature.**
- HRV and stress-detection literature.
- Affective computing research.
- Consumer wearable physiology validation studies.

---

## Q12. What notification and explainability style preserves sovereignty without creating cognitive noise?

**Why it matters.** Pillars 4 and 7 fail if the system constantly interrupts or silently overrides the user.

**Suggested approach.**
- Compare silent adaptation, digest summaries, haptic nudges, and explicit prompts.
- Measure trust, annoyance, perceived control, and correction rate.
- Test accessibility across deaf, hard-of-hearing, and hearing users.

**Existing literature.**
- Calm technology literature.
- Explainable AI interaction research.
- Multimodal accessibility notification studies.

---

## Q13. How should a shared haptic language be standardised without flattening personal or cultural variation?

**Why it matters.** Pillar 8 needs enough interoperability for sharing without imposing a central authority over meaning.

**Suggested approach.**
- Define a small core lexicon plus user-definable overlays.
- Test comprehension, memorability, emotional interpretation, and conflict rates.
- Publish open phrase-pack schemas and governance rules.

**Existing literature.**
- Social haptics research.
- DeafBlind tactile communication systems.
- Tacton and haptic-icon literature.

---

## Q14. How can community acoustic maps remain useful while preserving privacy and avoiding raw-audio surveillance?

**Why it matters.** Pillar 8 is powerful only if it stays local-first and privacy-preserving.

**Suggested approach.**
- Use coarse spatial bins, structured notes, and consensus scoring instead of raw-audio uploads.
- Compare differential-privacy-inspired aggregation against purely local contribution models.
- Study moderation models drawn from open mapping communities.

**Existing literature.**
- Differential privacy literature.
- Participatory sensing and accessibility mapping research.
- OpenStreetMap governance patterns.

---

## Q15. What regulatory and evidence package best fits each deployment mode across the UK, US, and EU?

**Why it matters.** Companion DSP, therapeutic wrist haptics, and aids-free sensory substitution are not the same product and should not be forced through one pathway.

**Suggested approach.**
- Split strategy by mode: companion pipeline, therapeutic delivery, aids-light receiver, aids-free substitution.
- Seek written pre-submission feedback from MHRA, FDA, and at least one EU notified body.
- Maintain a living technical file tied to open validation artefacts.

**Existing literature.**
- BrainPort regulatory materials.
- Neosensory Buzz positioning.
- MHRA Innovation Office, FDA Q-Sub, and EU MDR guidance.

---

## Execution order

1. Q1, Q2, Q6 — bandwidth, actuator choice, latency
2. Q3, Q4, Q5 — adaptation, restoration mapping, onboarding
3. Q7, Q8 — selective hearing core
4. Q9, Q10, Q11, Q12 — therapeutic and emotional intelligence
5. Q13, Q14 — social layer and privacy-preserving mapping
6. Q15 — deployment-mode regulatory packaging

OpenHear does not wait for certainty before building. It publishes the protocol, instruments the system, measures the result, and improves in public.
