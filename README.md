# OpenHear 🦻

### The first open hearing system that is sweat-proof, feedback-free, and 100% yours — a sovereign audio pipeline and active environmental intelligence platform for hearing aid users.

> *The hearing aid industry charges £3,000–£8,000 for hardware, then locks you out of it.*
> *Your audiogram is a measurement of your body. It belongs to you.*
> *OpenHear gives it back.*

---

## Why OpenHear in 2026

Commercial aids from Phonak, Signia, and Starkey still ship with proprietary AI that mangles your own voice, whistles during hugs, and dies in sweat. Replacements cost £3,000–£8,000 and lock you into manufacturer fitting software. OpenHear is the sovereign alternative: an open-source DSP pipeline with adaptive feedback cancellation, own-voice bypass, and sweat-proof 3D-printed ITE shells you manufacture at home. Every algorithm is inspectable. Every parameter is yours. No cloud. No subscription. No lock-in. MIT licensed.

---

## What this is

OpenHear is an open-source sovereign audio pipeline for people who wear commercial hearing aids and are tired of factory AI making decisions about their own hearing without their consent.

It works with aids you already own. It runs on hardware you already have. It does not require an audiologist appointment to change a setting.

OpenHear is now both a software pipeline and a hardware concept. The pipeline gives you control over how your aids process sound. The hardware — the OpenHear Wristband (in development) — extends that control outwards into the environment itself, scanning for sounds your aids may not pick up and translating them into haptic awareness on the wrist. Software and hardware are unified by a single principle: the hearing aid user should have full sovereignty over how they perceive their acoustic environment.

**Tested on:**
- Phonak Naída M70-SP (Marvel platform)
- Signia Insio 7AX (Augmented Xperience platform)

**Required hardware:**
- Noahlink Wireless 2 (~£80 on eBay)
- Windows laptop (for fitting software)
- iPhone or Android (for streaming)
- OpenHear Wristband *(in development)* — continuous-wear haptic frequency scanner, pairs over Bluetooth with the rest of the pipeline. See the OpenHear Wristband section below.

---

## The problem

Modern hearing aids are extraordinary pieces of engineering. They are also, deliberately, black boxes.

When you buy a Phonak or Signia aid, you get a device that:
- Constantly reclassifies your acoustic environment without telling you
- Applies compression, noise reduction, and beamforming algorithms you cannot inspect
- Stores your audiogram and fitting profile in a proprietary format you cannot read
- Requires a registered audiologist and £200+/hr of fitting time to adjust a single parameter
- Reverts to factory defaults if the fitting software version doesn't match

This is not a safety requirement. It is a business model.

The audiogram stored in your hearing aids is a biometric measurement of your nervous system. The fitting profile is a record of how your brain processes sound. You generated that data. You wore the sensors. You sat in the booth.

It is yours.

---

## What OpenHear does
```
World → Microphone → Custom DSP Engine → Bluetooth Stream → Your Aids → Your Ears
```

**Core module** — reads your existing fitting data out of your aids via Noahlink Wireless. Exposes it as plain JSON. No proprietary format, no locked PDF.

**DSP module** — real-time Python audio pipeline. You control the compression curve, the noise floor, the beamforming angle, the voice frequency emphasis. Tuned to your audiogram, not a population average.

**Stream module** — sends processed audio directly to your aids over Bluetooth. No extra hardware. Works on iPhone and Android.

**Audiogram module** — reads, visualises, and exports your hearing thresholds in open formats. The data your audiologist has been keeping in a system you can't access.

**Learn module** *(phase 3)* — a preference engine that adjusts to your own corrections over time. Your hearing profile improves every day, not once every two years.

---

## OpenHear Wristband — Active Environmental Intelligence

The pipeline above improves the sound that already reaches your aids. The wristband does something different: it scans the environment in parallel, on the wrist, and tells you about sounds your aids never delivered — or sounds you weren't oriented toward.

It is a continuous-wear device designed to work *alongside* hearing aids, not replace them. Passive amplification becomes active environmental intelligence.

```
World → Wrist Microphone Array → On-device AI Classifier → Haptic Motor Array → Your Wrist
                                          ↕
                                     Bluetooth
                                          ↕
                                Aids · Phone · Pipeline
```

**Edge AI sound classification** — low-latency on-device inference identifies environmental sounds in real time. Nothing is sent to a cloud. Your environment is your data and it stays on the wrist. The same sovereignty principle that governs your audiogram governs every sample the wristband hears.

**Multi-motor haptic feedback** — an array of small motors arranged around the wrist creates a spatial sound field through haptic patterns. Different sound classes, directions, and frequency bands have distinct haptic signatures. You build a physical sense of your acoustic surroundings without relying solely on what your aids decide to amplify.

**Directional awareness through haptic mapping** — the wristband communicates not just *what* a sound is but *where* it is coming from. Motor positions map to compass points around the wrist, so a siren behind you, a voice to your left, and a doorbell in front feel distinctly different. This is spatial awareness for sounds the aids may not be picking up or that you simply aren't oriented toward.

**Bluetooth connectivity** — pairs with hearing aids, smartphones, and smart home systems. Speaks the same protocols as the rest of the OpenHear pipeline so the wristband, the aids, and the DSP module act as one unified system rather than three separate devices.

**Personalised AI models** — the classifier adapts to the user's specific environment over time. A user in a barbershop has different priority sounds to a user in an office; the model learns the difference and adjusts haptic responses accordingly, with no manual configuration. Adaptation happens locally on the device.

**Proactive frequency-specific scanning** — instead of reacting after a sound has occurred, the wristband actively scans the frequency spectrum and alerts you to sounds approaching your detection threshold *before* they become relevant. Environmental sonar, not environmental amplification.

### How it relates to existing devices

The collaboration enquiry that prompted this work came from Sharp Hearing, a UK audiology clinic that already features the [Neosensory Buzz](https://neosensory.com/) on their site — a basic haptic wristband that converts sound into vibration patterns. The OpenHear Wristband goes significantly further:

| Capability | Neosensory Buzz | OpenHear Wristband |
|---|---|---|
| Sound → vibration | ✓ | ✓ |
| On-device AI sound classification | — | ✓ |
| Directional haptic mapping (compass points on the wrist) | — | ✓ |
| Proactive frequency-specific scanning | — | ✓ |
| Personalised models that adapt to your environment | — | ✓ |
| Pairs into a sovereign open-source DSP pipeline | — | ✓ |
| Local-only — no cloud, no telemetry | partial | ✓ |

### Why this fits OpenHear

The developer wears Phonak Naída and Signia aids. The gap the wristband fills is one lived every day: aids amplify what reaches the microphones in front of your ears, in the direction you happen to be facing, within the frequency response the manufacturer chose. Everything outside that envelope is silence. The wristband closes that gap on the wrist, under the user's control, with the same data-sovereignty guarantees as the rest of the project.

---

## The three pain points this solves

| Problem | Factory behaviour | OpenHear behaviour |
|---|---|---|
| Voices sound unnatural | AutoSense OS reclassifies constantly, smears transients | Linear mode + tunable WDRC compression |
| Constant unwanted adjustments | Environment AI fires every few seconds | You are the AI |
| Too much background noise | Fixed factory noise floor | Tunable beamforming, adjustable noise gate |

---

## Philosophical foundation

This project is the second work in a body of work on **data sovereignty** — the principle that data generated by or about your body belongs to you and not to the institution that measured it.

The first work is [The Burgess Principle](https://github.com/ljbudgie/Burgessprinciple) — a legal framework asserting void ab initio against bulk-processed warrants and tainted data records.

OpenHear applies the same logic to audiological data:

- Your audiogram was generated by measuring *your* auditory nerve response. It is yours.
- Your fitting profile was created by adjusting parameters until *your* perception was satisfied. It is yours.
- The Noahlink Wireless is your key. The open standard is your right. The algorithms are yours to read, copy, modify, and improve.

See `SOVEREIGN_AUDIO.md` for the full framework.

---

## Getting started — three paths

### Path 1 — Quick start (phone + existing aids)
1. Install the OpenHear mobile app (Android) from `/mobile/` — see [mobile README](mobile/README.md)
2. Load your audiogram JSON (export from your audiologist or create one using `audiogram/data/FORMAT.md`)
3. Pair your aids via Bluetooth Classic or ASHA
4. Tap ▶ — the sovereign DSP pipeline runs on your phone in real time

### Path 2 — Desktop pipeline (Windows + Noahlink Wireless 2)
1. Set your aids to linear mode (kill the factory AI — see instructions below)
2. `pip install -r requirements.txt`
3. `python -m core.read_fitting` — reads your current fitting data
4. `python -m dsp.pipeline` — starts the real-time audio processor
5. Edit `dsp/config.py` to tune compression, noise floor, and voice clarity

### Path 3 — Full sovereign build (phone + photogrammetry + resin printer)
1. Scan your ear using Polycam/Scaniverse photogrammetry (see [workflow](hardware/ite-shells/workflow.md))
2. Customise the parametric shell in OpenSCAD (see [parametric_shell.scad](hardware/ite-shells/parametric_shell.scad))
3. Print on Elegoo Saturn 4 / Anycubic (see [print settings](hardware/ite-shells/print_settings.md))
4. Apply nano-coating for sweat-proofing (see [sweatproof guide](hardware/ite-shells/sweatproof.md))
5. Assemble with OpenHear electronics, load the mobile app, and own your sound

### Kill the factory AI

Before using Path 2 or 3, set your aids to linear mode. This alone will transform your sound.

**Phonak Naída (Marvel/Paradise/Lumity):**
1. Install [Phonak Target](https://www.phonakpro.com/com/en/resources/software-and-firmware/phonak-target.html) on Windows
2. Connect Noahlink Wireless 2 via USB
3. Open fitting → Gain & MPO → set processing to Linear
4. Disable AutoSense OS scene classification
5. Save and close

**Signia Insio (AX platform):**
1. Install [Connexx](https://www.signiausa.com/professionals/software/) on Windows
2. Connect Noahlink Wireless 2 via USB
3. Open fitting → set to linear amplification
4. Disable Own Voice Processing auto-switching
5. Save and close

---

## Roadmap

- [x] Hardware identification and compatibility testing
- [x] Noahlink Wireless 2 bridge protocol research
- [x] `core/` — fitting data reader (JSON export)
- [x] `dsp/` — real-time Python pipeline (PyAudio + NumPy)
- [x] `stream/` — Bluetooth audio output module
- [x] `audiogram/` — threshold reader and visualiser
- [x] `hardware/ite-shells/` — parametric ITE shell design + sweat-proofing
- [x] `dsp/feedback_canceller` — adaptive feedback cancellation (LMS)
- [x] `dsp/own_voice_bypass` — own-voice detection and DSP bypass
- [ ] `mobile/` — Android real-time DSP app (Kotlin + Oboe)
- [ ] `learn/` — on-device preference learning engine
- [ ] `ui/` — desktop GUI (the OSCAR moment)
- [ ] iOS version of mobile app
- [ ] Community scan library
- [ ] tinyML Learn module v2

---

## Contributing

If you wear hearing aids and you're frustrated — this is your repo too.

If you're a DSP engineer who wants to build something that actually matters to real people — open an issue.

If you're an audiologist who believes your patients should own their own data — we especially want to hear from you.

---

## Legal

OpenHear does not modify, reverse-engineer, or redistribute any proprietary firmware. It uses the Noahlink Wireless 2 and standard fitting software interfaces in the same way any hearing care professional would. It streams audio to hearing aids using standard Bluetooth audio profiles.

Your audiogram is yours. Your fitting data is yours. This software helps you access both.

MIT Licensed.

---

## Safety & Disclaimer

> **⚠️ EXPERIMENTAL PROJECT — NOT A MEDICAL DEVICE**
>
> OpenHear is an experimental open-source project. It has not been evaluated, approved, or cleared by any regulatory body (FDA, MHRA, CE/UKCA, or equivalent). It is not a medical device. Consult a qualified audiologist before making any changes to your hearing aid configuration. Use at your own risk.

---

## Author

**Lewis Burgess** — also the author of [The Burgess Principle](https://github.com/ljbudgie/Burgessprinciple).

*Two repos. One argument. Your data belongs to you.*
