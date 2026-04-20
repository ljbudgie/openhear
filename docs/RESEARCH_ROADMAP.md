# OpenHear Research Roadmap — 15 Critical Open Questions

This roadmap identifies the most important open questions across all eight pillars of OpenHear. Each question includes why it matters, the suggested approach, and anchor literature or prior art worth engaging immediately.

These questions do not block the build. They define where the engineering community, academic collaborators, clinicians, and users can produce the highest-value evidence fastest.

---

## Q1. What is the maximum information bandwidth of the wrist and forearm for auditory substitution?

**Why it matters.** The entire aids-free and augmentation roadmap depends on the wrist carrying enough information for speech, direction, and environmental meaning.

**Suggested approach.**
- Build a 24-, 64-, and 128-actuator benchtop sleeve.
- Run channel-capacity studies across spatial, temporal, and mixed encodings.
- Compare wrist-only against wrist+forearm lattices.

**Existing literature.**
- Bach-y-Rita et al. (1969), *Vision substitution by tactile image projection*.
- Novich & Eagleman (2015), *Using space and time to encode vibrotactile information*.
- Reed et al. (2019), *A phonemic-based tactile display for speech communication*.

---

## Q2. What adaptation curve does a 24-band or 32-band haptic encoding produce versus current 4-channel devices?

**Why it matters.** OpenHear is betting that richer, structured haptics shorten training time and increase usable word recognition.

**Suggested approach.**
- Run a developer-first longitudinal n=1 protocol immediately.
- Replicate with a small deaf and hard-of-hearing cohort.
- Track phoneme accuracy, open-set word recognition, and fatigue.

**Existing literature.**
- Perrotta et al. (2021), *Deciphering sounds through patterns of vibration on the skin*.
- Huang et al. (2017), Neosensory/VEST adaptation studies.
- Cochlear-implant adaptation literature on central plasticity timelines.

---

## Q3. Which haptic actuator topology gives the best trade-off between bandwidth, power, comfort, and manufacturability?

**Why it matters.** LRA, piezo, voice-coil, and hybrid stacks imply different limits for speech cues, therapeutic delivery, and sleep wearability.

**Suggested approach.**
- Benchmark LRA, wideband piezo, and compact voice-coil arrays on rise time, thermal profile, skin comfort, and perceived distinctness.
- Test continuous-wear performance over 8-hour and overnight sessions.

**Existing literature.**
- Choi & Kuchenbecker (2013), review work on vibrotactile actuation.
- bHaptics, Boréas, TDK/TacHammer actuator and driver documentation.
- Human factors work from wearable haptics literature.

---

## Q4. How should an audiogram be translated into a mixed acoustic+haptic restoration map?

**Why it matters.** The system must fill missing bands without redundantly saturating bands the user already hears biologically.

**Suggested approach.**
- Build a formal `RestorationGap` model.
- Compare acoustic-only, haptic-only, and mixed strategies for partially hearing users.
- Measure speech-in-noise and fatigue outcomes.

**Existing literature.**
- NAL-NL2 and DSL fitting logic as comparators.
- Cochlear electric-acoustic stimulation research.
- Sensory substitution studies using residual sensory channels.

---

## Q5. What onboarding protocol lets users safely learn frequencies they have never perceived or have not perceived for years?

**Why it matters.** Sudden exposure to previously absent information can overwhelm, fatigue, or discourage users even if the encoding is technically correct.

**Suggested approach.**
- Create a staged protocol with exposure ceilings, band unlocks, and fatigue scoring.
- Compare rapid full-band exposure against progressive unlock models.
- Add child-specific and adult-late-onset variants.

**Existing literature.**
- Cochlear implant habilitation and rehabilitation protocols.
- TVSS and BrainPort adaptation training literature.
- Auditory training literature for age-related high-frequency loss.

---

## Q6. What is the true end-to-end latency floor of the open wristband stack, and where are the dominant costs?

**Why it matters.** Conversational use, timing-sensitive performance, and spatial awareness all degrade sharply if latency drifts too high.

**Suggested approach.**
- Build a closed-loop latency rig with acoustic trigger and laser vibrometry or accelerometer measurement at the skin.
- Measure mic capture, DSP, classification, haptic render, driver, and mechanical onset separately.

**Existing literature.**
- Real-time hearing-aid and cochlear-implant latency studies.
- Open FPGA and embedded DSP benchmarking work.
- Neosensory and wearable haptics timing reports where available.

---

## Q7. Which selective-hearing model architecture best separates “what matters” from background in real time on-device?

**Why it matters.** Crowd filter, concert mode, surgery mode, and ATC mode all depend on class-conditioned separation that is fast enough and predictable enough to trust.

**Suggested approach.**
- Compare compact source-separation models, speaker-conditioned enhancement, and class-aware suppression pipelines.
- Evaluate on speech intelligibility, false suppression of critical cues, and battery cost.

**Existing literature.**
- Conv-TasNet / DPRNN / SepFormer source separation lineages.
- Hearing-aid scene analysis literature.
- Apple/Google on-device speech enhancement work.

---

## Q8. How accurately can OpenHear identify and preserve user-critical voices and sounds in dynamic environments?

**Why it matters.** Parent mode, coach mode, first-responder sleep mode, and teammate mode fail if the system misses the one signal the user actually cares about.

**Suggested approach.**
- Build a user-enrolled sound/voice library with local embeddings only.
- Test recognition across noise, distance, and reverberation.
- Add confidence-linked haptic fallback if certainty drops.

**Existing literature.**
- Speaker verification and wake-word research.
- Child-cry detection literature.
- Clinical alarm detection and monitoring studies.

---

## Q9. Which therapeutic frequencies and duty cycles in the 30–300 Hz range have the strongest evidence and safest implementation path?

**Why it matters.** OpenHear should start with protocols that are evidence-led, measurable, and low-risk.

**Suggested approach.**
- Create a protocol registry graded by evidence quality.
- Start with literature-backed 40 Hz, low-frequency relaxation, and recovery candidates.
- Run local n-of-1 and small cohort tracking through HealthKit/Health Connect.

**Existing literature.**
- Clements-Cortes et al. on vibroacoustic therapy.
- 40 Hz sensory stimulation work from MIT Picower / Li-Huei Tsai collaborators.
- Whole-body vibration review literature for bone, muscle, and circulation outcomes.

---

## Q10. How should sleep-stage-linked acoustic filtering and therapeutic scheduling be timed?

**Why it matters.** Sleep mode is a flagship sovereignty use case: suppress the world, keep the child or emergency alert, and optionally deliver restorative haptics.

**Suggested approach.**
- Use Apple Watch and Wear OS sleep-stage inputs to compare stage-triggered and phase-window delivery.
- Track awakenings, sleep continuity, HRV, and subjective rest.

**Existing literature.**
- Consumer wearable sleep-stage validation studies.
- Closed-loop sleep stimulation research.
- Paediatric monitor and caregiver alerting literature.

---

## Q11. Which biomarkers best distinguish positive arousal from stress in acoustic contexts?

**Why it matters.** Concert excitement and crowd anxiety can produce similar heart-rate changes but should drive opposite acoustic decisions.

**Suggested approach.**
- Build a multimodal classifier using HRV, heart-rate slope, motion, location, recent calendar context, and user correction signals.
- Test across concerts, commuting, exercise, and office work.

**Existing literature.**
- HRV and stress detection literature.
- Affective computing research on multimodal arousal classification.
- Apple Watch / wearable physiology validation literature.

---

## Q12. What notification style keeps OpenHear explainable without becoming cognitively noisy?

**Why it matters.** A sovereignty platform that constantly interrupts the user becomes another controlling system.

**Suggested approach.**
- Compare silent adaptation, periodic digest, haptic nudge, and explicit prompt modes.
- Measure perceived control, annoyance, trust, and correction rate.

**Existing literature.**
- Human factors work on notification load and adaptive interfaces.
- Accessibility studies on multimodal alerting.
- Calm technology and explainable AI interaction research.

---

## Q13. How should a shared haptic language be standardised without flattening personal or cultural variation?

**Why it matters.** Social haptics only work if there is enough interoperability to share meaning without forcing everyone into the same vocabulary.

**Suggested approach.**
- Define a small interoperable core lexicon plus user-definable overlays.
- Test comprehension, memorability, and emotional interpretation across users.

**Existing literature.**
- Social haptics research.
- DeafBlind communication and tactile language systems.
- Haptic icon and tacton literature.

---

## Q14. How can community acoustic maps and accessibility ratings stay useful while preserving privacy?

**Why it matters.** Acoustic mapping is powerful, but it can become surveillance if venue data and user traces are not carefully separated.

**Suggested approach.**
- Use privacy-preserving aggregation, local redaction, and coarse spatial bins.
- Let users contribute structured ratings without uploading raw audio.
- Verify community notes through consensus and repeat observations.

**Existing literature.**
- Differential privacy and local-first civic sensing.
- OpenStreetMap governance patterns.
- Accessibility mapping and participatory sensing literature.

---

## Q15. What regulatory classification and evidence package best fits each deployment mode in the UK, US, and EU?

**Why it matters.** Pipeline mode, therapeutic mode, and aids-free sensory substitution are not the same product and should not be forced into one pathway.

**Suggested approach.**
- Split regulatory strategy by mode: companion DSP, wellness haptics, sensory substitution hardware.
- Seek written pre-submission feedback from MHRA, FDA, and one EU Notified Body.
- Maintain a living technical file and comparator matrix.

**Existing literature.**
- BrainPort 510(k) materials.
- Neosensory Buzz regulatory positioning.
- MHRA Innovation Office, FDA Q-Sub, and EU MDR guidance materials.

---

## Execution order

These questions can run in parallel, but the highest-leverage order is:

1. Q1, Q3, Q6 — wrist bandwidth, actuator choice, latency floor
2. Q4, Q5 — personalisation and onboarding
3. Q7, Q8 — selective hearing core
4. Q9, Q10, Q11, Q12 — therapeutic and emotional intelligence
5. Q13, Q14 — social layer
6. Q15 — regulatory packaging across all modes

OpenHear does not wait for perfect certainty. It publishes the protocol, builds the rig, logs the results, and improves in public.
