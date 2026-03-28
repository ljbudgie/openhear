# hardware/ — From Audiogram to Wearable

This module bridges OpenHear's software pipeline to physical wearable hardware.

The goal: a fully open-source hearing aid. 3D printed shell. Commodity transducers. Open DSP. No proprietary firmware. No locked-down fitting software. No gatekeepers between you and your own hearing.

**Total build cost target: under £550 for a complete binaural (both ears) system.**

The hardware design prioritises **safety above all else**. Hardware MPO (Maximum Power Output) limiters are mandatory. They cap the sound level reaching your ear regardless of what the software does. This is non-negotiable. Read the [safety module](safety/README.md) before you build anything.

---

## Build Tiers

OpenHear hardware has three build tiers. Start wherever you are comfortable. Every tier produces a functional hearing device.

### Tier 1: Explorer (~£300)

**What it is:** A Tympan board connected to standard headphones. You load your audiogram, generate a DSP configuration, and hear the difference immediately. No soldering. No 3D printing. Just plug in and listen.

**Who it's for:** Anyone who wants to hear what personalised amplification sounds like before committing to a full build.

**What you get:** Real-time audio processing tuned to your audiogram, running on open-source hardware. Adjustable via the Tympan Remote App on your phone.

### Tier 2: Builder (~£450)

**What it is:** A Tympan board with BTE (Behind-The-Ear) earpieces and custom-moulded ear tips. This is a wearable hearing aid. You solder receiver wires, print ear moulds, build an MPO limiter circuit, and calibrate the system to your ears.

**Who it's for:** Someone comfortable with basic soldering and willing to spend a weekend on the build. Previous electronics experience helpful but not required — the [assembly guide](assembly/README.md) assumes zero experience.

**What you get:** A binaural hearing aid with WDRC compression, noise reduction, feedback cancellation, and hardware safety limiting. Comparable in function to a basic commercial hearing aid.

### Tier 3: Sovereign (~£550)

**What it is:** A fully custom integrated device. You print the complete shell on a resin printer, integrate all components into a single BTE housing, and calibrate with a measurement microphone. This is the endgame: a hearing aid you built entirely yourself.

**Who it's for:** Someone who wants full control over every aspect of their hearing device, and has the patience for iterative 3D printing and fitting.

**What you get:** A self-contained, sovereign hearing device. You own every layer — from the audiogram data to the DSP algorithms to the physical hardware on your ear.

---

## Sub-Modules

| Module | Description |
|--------|-------------|
| [tympan/](tympan/README.md) | Tympan integration: audiogram-to-Arduino bridge, sketch generation, platform docs |
| [shell/](shell/README.md) | 3D printing guide for custom ear moulds: impressions, scanning, printing, fitting |
| [safety/](safety/README.md) | **Mandatory.** MPO limiters, calibration procedures, risk register, safety circuits |
| [assembly/](assembly/README.md) | Step-by-step build guide for all three tiers, assuming zero electronics experience |
| [BOM.md](BOM.md) | Complete bill of materials with suppliers, costs, and substitution notes |
| [ROADMAP.md](ROADMAP.md) | Hardware development roadmap from documentation to sovereign device |

---

## Important: This Is Not a Medical Device

OpenHear hardware is a **Personal Sound Amplification Product (PSAP)** built by and for the user. It is not a regulated medical device. It has not been approved by any regulatory body. It is not sold, prescribed, or fitted by a clinician.

That said, the safety module is designed to **exceed commercial hearing aid safety margins**. The hardware MPO limiter cannot be overridden by software. The calibration procedure verifies output levels at every audiometric frequency. The risk register covers every failure mode we can identify.

You are the builder. You are the user. You are responsible for your own hearing health. If you are unsure about any aspect of this build, consult an audiologist. If in doubt, reduce gain. Hearing damage cannot be undone.

---

## Getting Started

1. Read the [safety module](safety/README.md). This is not optional.
2. Choose your [build tier](#build-tiers) and review the [BOM](BOM.md).
3. Follow the [assembly guide](assembly/README.md) for your tier.
4. Use `hardware/tympan/audiogram_to_tympan.py` to generate your personalised Arduino sketch from your audiogram.
5. Upload, calibrate, and listen.
