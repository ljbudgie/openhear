# OpenHear Research Roadmap — Five Open Questions Before MVP

This document identifies the five most critical open research questions that must be answered before a minimum viable prototype of the **aids-free OpenHear system** (see `docs/AIDS_FREE_ARCHITECTURE.md`) can be built and deployed for adaptation studies.

Each question is followed by *why it matters*, *what success looks like*, and *the suggested approach*. None of these questions block the start of work; they bound the design space and identify where contribution is most valuable.

---

## Q1. What is the maximum information bandwidth of the wrist as an auditory substitution channel?

**Why it matters.** The entire architecture stands on the assumption that 64–128 wrist actuators, driven at 5–600 Hz, can carry enough information for the brain to remap into usable hearing. Existing devices (Neosensory Buzz: 4 motors) demonstrate proof-of-concept word recognition; we do not yet have a published Shannon-style upper bound on what the wrist can carry, nor a clear ceiling on phoneme distinguishability per actuator-second.

**Success looks like.** A measured information-throughput curve (bits/s perceivable) as a function of (a) actuator count, (b) actuator pitch, (c) carrier frequency, (d) training time. A curve that reaches ≥ 40 bits/s sustained at 64 actuators after 6 weeks of training would be sufficient for open-set speech.

**Suggested approach.**
- Build a benchtop 64-actuator forearm sleeve with software-defined drive.
- Run a *channel-capacity* protocol: closed-set N-AFC discrimination at increasing pattern complexity, fitted to a psychometric curve.
- Compare three encodings: pure spatial, pure temporal, and combined apparent-motion. Publish the curves as open data.
- Replicate independently in two labs.

---

## Q2. What adaptation timeline does a frequency-rich (24-band) haptic encoding actually produce, and how does it compare with current 4-channel devices?

**Why it matters.** Neosensory's published adaptation curves are for a low-channel device. We are betting that increasing channel count by an order of magnitude shortens adaptation from months to weeks — but this is an *assumption*, not a finding. If adaptation time scales unfavourably (e.g. plateaus due to cortical capacity, or degrades from sensory overload), the architecture must reduce channel count and lean harder on classification.

**Success looks like.** A published learning curve showing closed-set phoneme accuracy and open-set word recognition over weeks 1–12 for the 24-band encoding, against a 4-band control. The hypothesis to falsify: 24-band reaches 70 % open-set word recognition in noise within 8 weeks of 30 min/day training.

**Suggested approach.**
- Single-subject longitudinal study (developer first, n=1) — daily data published as `~/.openhear/training/*.parquet` from week 1.
- Replication cohort of 8–12 deaf adult volunteers via an academic partner with audiology IRB capability (UCL Ear Institute, Manchester Centre for Audiology, or equivalent).
- Pre-register the protocol on OSF.
- Periodic fMRI (collaborator-dependent) to confirm or refute auditory-cortex recruitment in the OpenHear cohort.

---

## Q3. What is the actual end-to-end latency floor of an open-source wrist haptic stack, and where in the pipeline are the dominant costs?

**Why it matters.** The architecture targets ≤ 5 ms environment-to-skin. This is at or beyond the published latency of any current consumer haptic device. If latency cannot be brought below ~15 ms in practice, the system is still useful for environmental awareness but degrades for conversational use (where lip-sync to mechanical onset matters). A clean latency budget with measured per-stage costs is the prerequisite for the NPU specification.

**Success looks like.** A measured, reproducible latency profile across a v0 (Pi+Hailo+LRA) and v0.5 (RISC-V SBC + piezo) prototype, broken down by stage, with the bottleneck identified. The deliverable is a CSV + plot that any contributor can re-run with the open test rig.

**Suggested approach.**
- Build a closed-loop latency rig: speaker → wrist → laser doppler vibrometer reading skin displacement, time-stamped against the trigger.
- Publish per-stage timestamps from the firmware (mic ISR → DSP done → render done → SPI fired → mechanical onset).
- Compare LRA, wideband piezo, and voice-coil actuators on rise time only.
- Open the rig as `hardware/test/latency_rig/`.

---

## Q4. What is the right per-user calibration protocol — how do we turn an audiogram + 90 minutes of perceptual testing into a personal haptic mapping that demonstrably outperforms a population-default mapping?

**Why it matters.** Audiograms are dense data about cochlear function but tell us nothing directly about the wearer's *somatosensory* sensitivity, dexterity, hairy-vs-glabrous skin distribution, or cognitive style. A blind population mapping will leave a large fraction of the perceptual gain on the table. The calibration protocol is the equivalent of the audiologist's fitting session and must be entirely user-runnable.

**Success looks like.** A 60–90 minute calibration session, fully automated by the training app, that produces a `profile.json` whose adoption yields a statistically significant improvement (≥ 10 % open-set word accuracy at week 4) over a population-default profile.

**Suggested approach.**
- Borrow methodology from psychophysical fitting in cochlear implant programming and from Bach-y-Rita-era TVSS calibration.
- Calibrate four things: per-motor absolute threshold, per-motor comfort ceiling, two-point discrimination map across the wrist, and rhythmic temporal acuity.
- Combine with the imported audiogram to weight bands the user *needs* over bands they can already hear acoustically (relevant for partially-hearing users in transition).
- A/B test against population default in the multi-user pilot (Q2 cohort).

---

## Q5. What is the regulatory position in the UK / US / EU when the device is genuinely *not* a hearing aid by mechanism — and what is the minimum clinical evidence needed to make that classification stick?

**Why it matters.** The architecture's regulatory pathway is built on the claim that sensory substitution is a different mechanism of action from amplification, and therefore not a hearing aid in the regulatory sense. If regulators reject that framing — or if they accept it but require hearing-aid-class evidence anyway — the time-to-clinic stretches by years. We need a definitive answer, not an inference.

**Success looks like.** Written, citable pre-submission feedback from at least two of {MHRA, FDA Q-Sub, EU Notified Body} confirming (a) sensory substitution classification (UK Class I or IIa / FDA 510(k) Class II / EU Class I or IIa), (b) acceptable comparator predicate (Neosensory Buzz; BrainPort; equivalent), and (c) a defined minimum clinical evidence package.

**Suggested approach.**
- File an FDA Q-Sub for early agency feedback as soon as v0 hardware exists. Q-Subs are free, written, and on the record.
- Engage MHRA Innovation Office for a Scientific Advice meeting; UK is the home jurisdiction and the most pragmatic first regulator.
- Engage a single EU Notified Body (BSI or TÜV SÜD) for an informal MDR classification opinion.
- Engage academic partner (audiology + medical-device law clinic) to draft the technical file outline against the Neosensory Buzz precedent.
- Publish all feedback (with redactions only where required) as `docs/regulatory/`.

---

## Cross-cutting note

These five questions are *parallelisable*. Q1, Q3 and Q4 can begin on the bench immediately. Q2 begins the moment a wearable v0 exists. Q5 begins the moment v0 exists *and* there is a written technical description (this document and the architecture document together meet that bar).

The repo is open. So is the protocol. Anyone may fork, replicate, or contradict any of the above and submit a PR.
