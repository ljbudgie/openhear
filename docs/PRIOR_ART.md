# OpenHear Prior Art and Engagement List

The ten papers, projects, and institutions OpenHear should engage with immediately on the way to an aids-free, somatosensory hearing system. Each entry includes *what it is*, *why it matters to OpenHear*, and *the engagement we are seeking*.

This list is a living document. PRs to add, refute, or replace entries are welcome.

---

## 1. Bach-y-Rita, P. — *Tactile vision substitution* (1969 onwards)

**What it is.** The foundational body of work on sensory substitution. Demonstrated that congenitally blind subjects, given a 20×20 tactile grid driven by a head-mounted camera, can develop a *visual percept* — including parallax, looming, and object recognition — through skin alone.

**Why it matters.** Establishes the central hypothesis OpenHear depends on: that the brain treats sensory input as substrate-independent symbols and will remap them to the appropriate cortical area given consistent input.

**Engagement.** Cite as foundational. Build on the methodological lineage — particularly the calibration and training protocols from the original TVSS work (now held by the *Tactile Communication and Neurorehabilitation Laboratory*, University of Wisconsin–Madison).

**Key reference.** Bach-y-Rita, P., Collins, C. C., Saunders, F. A., White, B., & Scadden, L. (1969). *Vision substitution by tactile image projection.* Nature, 221(5184), 963–964.

---

## 2. Neosensory (David Eagleman et al.) — *Buzz wristband, VEST*

**What it is.** A commercial 4-motor haptic wristband (Buzz) that converts environmental sound into vibration, with published evidence of word-recognition gains in deaf adults after weeks of training. The earlier VEST (Versatile Extra-Sensory Transducer) is the academic predecessor — a 32-motor torso vest.

**Why it matters.** Direct functional predecessor. Buzz is the regulatory predicate device most relevant to OpenHear's standalone configuration. Their published learning curves form the baseline OpenHear must beat.

**Engagement.** Public comparison data on Q1/Q2 of the research roadmap. Open dialogue, not competitive. Sharp Hearing already lists Buzz on their site — the 20 April 2026 contact is a natural first conversation.

**Key references.**
- Novich, S. D., & Eagleman, D. M. (2015). *Using space and time to encode vibrotactile information.* Experimental Brain Research, 233, 2777–2788.
- Perrotta, M. V., Asgeirsdottir, T., & Eagleman, D. M. (2021). *Deciphering sounds through patterns of vibration on the skin.* Neuroscience, 458, 77–86.

---

## 3. BrainPort (Wicab, Inc.) — *Tongue-based sensory substitution*

**What it is.** FDA-cleared (2015) sensory substitution device delivering visual or vestibular information through a 400-electrode lingual array. The cleanest contemporary regulatory precedent for a sensory substitution medical device.

**Why it matters.** BrainPort Vision Pro is the FDA 510(k) regulatory roadmap OpenHear should study line by line — same mechanism class (mechanoreceptive substitution), different sense, same agency framing.

**Engagement.** Read the 510(k) summary; engage Wicab's regulatory team if possible for off-the-record route guidance.

---

## 4. Reed, C. M., Tan, H. Z., et al. — *Purdue / MIT TAGA project (Tactile Speech Communication)*

**What it is.** Long-running collaboration developing a phonemic haptic code for the forearm — *TAGA* (Tactile Acoustic Generic Alphabet). Subjects learn to recognise English phonemes delivered as multi-actuator forearm patterns, achieving sustained word recognition.

**Why it matters.** Direct predecessor of OpenHear's Phase 1 phoneme sandbox. Their per-phoneme encoding scheme is the strongest published candidate for a base mapping.

**Engagement.** Approach the *Haptic Interface Research Laboratory* at Purdue (Hong Z. Tan) and *Sensory Communication Group* at MIT for an open-data release of the phoneme corpus and protocol.

**Key reference.** Reed, C. M., Tan, H. Z., Perez, Z. D., Wilson, E. C., Severgnini, F. M., Jung, J., et al. (2019). *A phonemic-based tactile display for speech communication.* IEEE Transactions on Haptics, 12(1), 2–17.

---

## 5. Eagleman Lab, Stanford — *Cortical remapping under sensory substitution*

**What it is.** The academic lab behind VEST and the published fMRI evidence that long-term tactile-to-auditory substitution recruits auditory cortex.

**Why it matters.** Provides the neuroscientific basis for the OpenHear adaptation claim. Without this evidence, OpenHear is an environmental-awareness device; with it, OpenHear is a hearing system.

**Engagement.** Collaborator-class engagement. Offer the OpenHear cohort (Q2 of the roadmap) as a published, open-data extension of their adaptation curves.

---

## 6. *bHaptics* and *TanvasTouch* — open and semi-open haptic actuator stacks

**What they are.** Two of the most advanced multi-actuator wearable platforms on the market (TactSuit; ultrasonic-friction surface haptics). Not directly hearing-related, but the actuator and driver topology is decades ahead of typical maker-grade LRA arrays.

**Why they matter.** Inform v1 actuator selection for the wristband. Particularly the case for piezo / ultrasonic friction over LRA where bandwidth matters.

**Engagement.** Buy and benchmark. Where APIs are open, contribute drivers; where they are not, document the gap.

---

## 7. *RISC-V International* and the *OpenHW Group (CORE-V family)*

**What they are.** The open ISA and the open implementations (CV32E40P, CVA6) that form the most plausible base for the OpenHear Hearing NPU's scalar/vector control core.

**Why they matter.** The aids-free architecture commits to open silicon. RISC-V + OpenHW gives a credible, license-clean route from RTL to wearable in a 2–3 year horizon, including an FPGA-validation step before tape-out.

**Engagement.** Submit the Hearing NPU as a CORE-V derivative; participate in the audio/signal SIG; align our RVV usage with their roadmap.

---

## 8. Lattice Semiconductor *ECP5* + *Project Trellis* (open FPGA toolchain)

**What it is.** A mid-density FPGA family with a fully open synthesis toolchain (Yosys + nextpnr + Project Trellis). The most open path to a wearable-class FPGA prototype with no proprietary toolchain dependency.

**Why it matters.** Q3 of the roadmap (latency-floor characterisation) needs a deterministic, open, FPGA-class compute path before tape-out is justified. ECP5 is that path.

**Engagement.** Build the v1 FPGA validation board on ECP5; publish bitstreams; co-publish with the *Free and Open Source Silicon Foundation (FOSSi)*.

---

## 9. UCL Ear Institute (UK) and Manchester Centre for Audiology and Deafness (UK)

**What they are.** Two of the strongest UK academic audiology programmes, with active research in cochlear implant signal processing, plasticity, and clinical trials of sensory devices.

**Why they matter.** They are the natural UK partners for the multi-user pilot in Q2/Q4 of the roadmap. UK-based aligns with the developer's location, the MHRA pathway, and the NHS context. Both have IRB-equivalent ethics infrastructure and existing relationships with the British Society of Audiology.

**Engagement.** Cold approach to a named PI in each, with the architecture document and roadmap attached. Offer a co-authored protocol and open data.

---

## 10. *Open Source Hardware Association (OSHWA)*, *CERN-OHL-S license community*, and *Hackaday Prize / Open Hardware Summit*

**What they are.** The institutional and licensing infrastructure of the open-hardware movement — the body that defines what "open hardware" means, the license that legally protects it, and the venues that fund and showcase it.

**Why they matter.** The aids-free OpenHear is an *open hardware* commitment from chip up. CERN-OHL-S is the appropriate license for the wristband schematics and the NPU RTL. OSHWA certification is a cheap, durable signal of intent. Hackaday Prize and Open Hardware Summit are the right first venues to surface a working v0.

**Engagement.** Register the project for OSHWA certification at v0; prepare a Hackaday Prize entry; submit a v0 demo to the next Open Hardware Summit.

---

## Honourable mentions (not in the top ten, on the radar)

- **Cochlear Limited's published research on electric-acoustic stimulation** — for the audiogram-weighting maths.
- **OpenEarable (KIT, Karlsruhe)** — open-source ear-worn platform; useful as a contrast (what we are *not* building).
- **Facebook Reality Labs / Meta haptics research** — wristband EMG and haptic work; some open publications.
- **BBC R&D audio accessibility group** — content-side partner for testing comprehension on real broadcast material.
- **The British Society of Audiology** — clinical community access in the UK.

---

## How OpenHear engages

A standard outreach packet exists in `/docs/outreach/` (planned). Each first-contact email includes:

1. The architecture document (`docs/AIDS_FREE_ARCHITECTURE.md`).
2. The research roadmap (`docs/RESEARCH_ROADMAP.md`).
3. This prior-art list.
4. A direct ask — collaboration, data sharing, predicate clarification, or RTL contribution.

No NDAs. No exclusivity. No subscription. Open data in, open data out.
