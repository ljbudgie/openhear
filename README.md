# OpenHear 🦻

### Your senses. Your data. Your world.

[![Licence: Apache 2.0 + Sovereign Use Addendum](https://img.shields.io/badge/licence-Apache%202.0%20%2B%20Sovereign%20Use%20Addendum-blue.svg)](LICENSE)

**Built on the Burgess Principle** — see [docs/BURGESS_PRINCIPLE.md](docs/BURGESS_PRINCIPLE.md).
→ <a href="docs/index.md">Full documentation index</a>

> **⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE**
> OpenHear is a research platform and public build log, not a certified hearing aid.
> Start at low volume, validate every configuration on your own hardware, and do
> not treat any module in this repository as a substitute for clinical care.

### OpenHear is a human sensory sovereignty platform — not a hearing aid, not a wellness device, not a consumer gadget. It is an open-source sovereign audio pipeline, haptic environment engine, therapeutic delivery layer, and future aids-free sensory system.

### North star: human sensory sovereignty. The user decides what they hear, when they hear it, how they hear it, and what their acoustic environment does to their body and mind. The long-term configuration is still direct: no hearing aid, no behind-the-ear receiver, no bone conduction implant, no ear canal device of any kind. The wristband IS the hearing system. See **[Vision — Aids-Free Hearing](#openhear-vision-2--aids-free-hearing-the-wristband-is-the-hearing-system)** below, the full eight-pillar platform architecture in [`docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md`](docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md), and the aids-free subsystem document in [`docs/AIDS_FREE_ARCHITECTURE.md`](docs/AIDS_FREE_ARCHITECTURE.md).

> *The hearing aid industry charges £3,000–£8,000 for hardware, then locks you out of it.*
> *Your audiogram is a measurement of your body. It belongs to you.*
> *OpenHear gives it back.*

---

## Why OpenHear in 2026

Commercial aids from Phonak, Signia, and Starkey still ship with proprietary AI that mangles your own voice, whistles during hugs, and dies in sweat. Replacements cost £3,000–£8,000 and lock you into manufacturer fitting software. OpenHear is the sovereign alternative: an open-source DSP pipeline with adaptive feedback cancellation, own-voice bypass, and sweat-proof 3D-printed ITE shells you manufacture at home. Every algorithm is inspectable. Every parameter is yours. No cloud. No subscription. No lock-in. MIT licensed.

---

## What this is

OpenHear is an open-source human sensory sovereignty platform for people who are tired of factory AI, clinic gatekeeping, and environmental noise making decisions about their own senses without their consent.

It already works with aids you own and hardware you have. It is being extended into a wrist-native sensory system, a therapeutic haptic platform, a selective-hearing engine, and an acoustic privacy layer. It does not require an audiologist appointment to change a setting.

OpenHear is now both a software pipeline and a hardware concept. The pipeline gives you control over how your aids process sound. The hardware — the OpenHear Wristband (in development) — extends that control outwards into the environment itself, scanning for sounds your aids may not pick up and translating them into haptic awareness on the wrist. Software and hardware are unified by a single principle: the hearing aid user should have full sovereignty over how they perceive their acoustic environment.

OpenHear now has eight explicit pillars:

1. Peak hearing for all users
2. Selective acoustic sovereignty
3. Therapeutic frequency delivery
4. Native iOS and Android integration
5. Emotional and cognitive acoustic intelligence
6. Social acoustic layer
7. Beyond biological hearing
8. Sovereign philosophy enforced at every layer

### New north-star documents

- Full architecture — [`docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md`](docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md)
- Aids-free subsystem architecture — [`docs/AIDS_FREE_ARCHITECTURE.md`](docs/AIDS_FREE_ARCHITECTURE.md)
- Research roadmap — [`docs/RESEARCH_ROADMAP.md`](docs/RESEARCH_ROADMAP.md)
- Immediate engagement list — [`docs/PRIOR_ART.md`](docs/PRIOR_ART.md)
- Go-to-market, mission, and showcase applications — [`docs/GO_TO_MARKET.md`](docs/GO_TO_MARKET.md)
- Funding and partnerships — [`docs/FUNDING_AND_PARTNERSHIPS.md`](docs/FUNDING_AND_PARTNERSHIPS.md)

### Mission

OpenHear gives people control over their own senses. It lets you choose what you hear, what you ignore, what your body learns from sound, and how your environment reaches you, whether you are deaf, hard of hearing, hearing, tired, stressed, training, sleeping, working, or simply wanting peace.

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

## OpenHear Vision — The Wristband as the Hearing System

The wristband section above describes a companion device. This section describes where the architecture is going.

The long-term vision is direct: the wristband stops being a companion and becomes the hearing system. It captures the environment, classifies it, processes it against your audiogram, and transmits a finished audio signal to a minimal receiver worn at the ear. The £3,000–£8,000 behind-the-ear black box — with its proprietary firmware, locked fitting software, and audiologist-gated parameters — is no longer required. It is replaced by a piece of jewellery on the wrist and a passive driver at the ear.

### The architecture — three layers, one user

```
World → Wrist Mic Array + Hearing NPU → Wireless Link → Bone Conduction Receiver / Open-Fit Earbud → Cochlea
        [capture + classify + process]   [low-latency]   [deliver only]
```

**Layer 1 — Wrist (sensor and processor).** The wristband carries the microphone array, the hearing-specific neural processing unit, the audiogram, and the DSP pipeline. All of the intelligence of the system lives here, on the user's wrist, where it can be charged, updated, inspected, and replaced independently of anything worn at the ear.

**Layer 2 — Wireless transmission.** A low-latency link between the wrist and the ear-worn receiver. Sub-5ms end-to-end is the target. Standard, open, and inspectable — no proprietary radio that locks the receiver to a single vendor.

**Layer 3 — Ear (delivery only).** A minimal behind-the-ear bone conduction receiver, or an open-fit earbud, whose only job is to convert the finished signal into vibration or sound. No microphones. No classifier. No DSP. No firmware that does anything other than receive and drive a transducer. When it breaks, you replace a £30 part, not a £6,000 one.

### A hearing-specific NPU — designed for this and only this

The processor on the wrist is not a general-purpose AI chip with a hearing application bolted on top. It is a neural processing unit designed from first principles for one task: real-time, personalised hearing.

- **Sub-5ms end-to-end latency** — capture to ear. Anything slower is felt as delay during conversation.
- **Personalised audiogram-based DSP** — compression curves, frequency shaping, and feedback cancellation derived from *your* thresholds, not a population fit.
- **On-device classification and beamforming** — environmental scene analysis and spatial steering run locally, at the same latency budget as the DSP itself.
- **Performance targets that exceed current hearing aid SoCs** — at a fraction of the silicon cost, because the chip does one job extremely well rather than every job adequately.

A general-purpose chip repurposed for hearing will always lose to a chip that was drawn for hearing. We intend to draw the chip.

### Sovereignty extended to hardware

OpenHear already gives the user sovereignty over their audiogram, their fitting data, and the DSP algorithms that act on them. The wristband-as-hearing-system extends that sovereignty down to the silicon and out to every device worn on the body.

- **No proprietary firmware** at any layer of the stack — wrist, link, or receiver.
- **No locked fitting software.** The audiogram lives on the wrist as plain JSON. Adjusting a parameter means editing a value, not booking an appointment.
- **No audiologist gatekeeping.** Audiologists are welcome as collaborators and clinicians; they are not required as a key to your own hearing.
- **No vendor lock between layers.** The receiver at the ear is interchangeable. The wristband is interchangeable. The link is an open standard. The user owns every layer.

The hearing aid industry's business model depends on the user not being able to see inside the device. This architecture is the device with the lid removed.

### Regulatory pathway

The system enters the world as a **companion device** — running alongside existing hearing aids, augmenting them, doing nothing the aids themselves do. This is the position the current OpenHear pipeline and wristband already occupy and it requires no clinical claim to be made.

The standalone configuration — wristband plus bone conduction receiver, replacing the hearing aid entirely — is the longer pathway. The regulatory target for the standalone device in the United Kingdom is **UK MDR 2002 Class IIa**, the same classification carried by conventional air-conduction hearing aids. Clinical evidence accumulates first; the claim follows.

### Collaboration

Open source hardware and open source software, end to end. Schematics, RTL, firmware, DSP, and fitting tools all under permissive licenses. Specifically invited:

- **Audiologists** — clinical input on fitting protocols, validation, and the standalone regulatory pathway.
- **Chip designers** — architects and RTL engineers interested in a hearing-specific NPU built from first principles.
- **DSP engineers** — compression, beamforming, feedback cancellation, and own-voice detection at sub-5ms latency budgets.
- **Hearing aid users** — the people the system exists for. Lived experience is a design input, not a marketing line.

The **Sharp Hearing collaboration enquiry of 20 April 2026** is recorded here as the first formal industry contact exploring this direction. It will not be the last.

---

## OpenHear Vision 2 — Aids-Free Hearing: the wristband IS the hearing system

The previous section described removing the £3,000–£8,000 behind-the-ear processor and keeping only a minimal ear-worn receiver. This section goes one further. **It removes the receiver too.**

There is no hearing aid in this system.
There is no behind-the-ear receiver.
There is no bone conduction implant.
There is no ear canal device of any kind.

There is a wristband, a personal model, an audiogram, and a brain trained to read them. The user owns all four.

The full eight-pillar platform architecture is in [`docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md`](docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md). The aids-free subsystem architecture is in [`docs/AIDS_FREE_ARCHITECTURE.md`](docs/AIDS_FREE_ARCHITECTURE.md). The 15 most critical open research questions are in [`docs/RESEARCH_ROADMAP.md`](docs/RESEARCH_ROADMAP.md). The immediate engagement list is in [`docs/PRIOR_ART.md`](docs/PRIOR_ART.md). The audience positioning, mission, and showcase applications are in [`docs/GO_TO_MARKET.md`](docs/GO_TO_MARKET.md). The funding and partnership strategy is in [`docs/FUNDING_AND_PARTNERSHIPS.md`](docs/FUNDING_AND_PARTNERSHIPS.md). What follows is the short version.

### Mechanism of action — sensory substitution, not amplification

OpenHear's standalone configuration is not a hearing aid by mechanism. It is a **somatosensory hearing substitution device**. Sound is captured at the wrist, classified by edge AI, weighted against the user's audiogram, and rendered as a high-resolution multi-frequency haptic field on the skin. The brain — through documented neuroplasticity, going back to Bach-y-Rita's 1969 tactile-vision substitution work — learns to read that field as auditory information.

This is the same class of device as the Neosensory Buzz, but with an order of magnitude more channels, true frequency-rich spatial encoding, audiogram-weighted band synthesis, and an open silicon and open RTL stack. It is not a hearing aid. It does not claim to restore cochlear function. It substitutes for it.

### Skin as the transducer

The volar wrist carries Pacinian, Meissner, Merkel and Ruffini mechanoreceptors covering roughly 5 Hz – 1 kHz of perceivable mechanical drive. Audio above this band is *encoded* — into motor position, drive pattern, and temporal structure across the array — not transmitted as raw vibration. Target actuator pitch is 8–12 mm, deliberately tighter than two-point discrimination, exploiting funnelling and apparent-motion illusions to produce a perceived spatial resolution finer than the physical receptor field.

- **Minimum viable**: 24 actuators in a single ring (Neosensory-class density).
- **Target v1**: 64 actuators in a 4-ring × 16-column lattice covering the wrist.
- **Aspirational v2**: 128 actuators extending up the forearm, enabling a 2D haptic "screen".

### Neural adaptation — open protocol, user-owned data

Adaptation is the design target, not raw signal fidelity. The training pipeline is published as a five-phase open protocol — calibration, phoneme sandbox, words and environment, open conversation, spatial and extended-spectrum — running on a cross-platform companion app. All data lives on the user's device as plain Parquet. There is no cloud account.

```
Phase 0  Calibration         (day 0,    ~90 min)   — perceptual mapping, motor thresholds, audiogram import
Phase 1  Phoneme sandbox     (week 1–2, 30 min/d)  — closed-set phoneme → haptic pattern drills
Phase 2  Word & environment  (week 3–6, 30 min/d)  — common words, alarms, name detection, traffic
Phase 3  Open conversation   (week 7+,  passive)   — continuous wear; periodic active-recall checks
Phase 4  Spatial & extended  (month 3+)            — direction, elevation, ultrasonic/infrasonic bands
```

### A Hearing NPU, designed from first principles

A general-purpose mobile SoC running PyTorch Mobile cannot meet the latency or power budget. The Hearing NPU is designed for *one* job: continuous, personalised, low-latency hearing-as-haptics.

| Stage                              | Latency budget |
|---|---|
| Mic capture + ADC                  | 0.3 ms    |
| Front-end DSP (beamform, AEC, VAD) | 0.7 ms    |
| Bark-band analysis (FFT/filterbank)| 0.5 ms    |
| Audiogram weighting                | 0.1 ms    |
| Classification + scene tag         | 1.5 ms    |
| Haptic render (mapping + envelope) | 0.6 ms    |
| Motor driver chain                 | 0.8 ms    |
| Mechanical rise time (LRA/piezo)   | 0.5 ms    |
| **End-to-end target**              | **≤ 5 ms**|

- **ISA**: RISC-V RV32IMC + RVV 1.0 (open ISA, open implementations).
- **Accelerator**: 8 × INT8/INT4 MAC tiles at ~2 TOPS, hardwired bark filterbank, single-cycle audiogram lookup, deterministic haptic scheduler.
- **SRAM-only data path**: 4 MB on-die, no DRAM. The model lives entirely on chip; this is the architectural reason ≤ 5 ms is achievable.
- **Power envelope**: 80–120 mW continuous, < 5 mW idle.
- **Open RTL** under CERN-OHL-S. No proprietary IP in the data path.

Until tape-out, the staged hardware path is: v0 on Raspberry Pi CM4 + Hailo-8L (~30 ms latency, sufficient for adaptation studies) → v0.5 on a RISC-V SBC + Coral Edge TPU (~15 ms) → v1 FPGA validation on Lattice ECP5 with the open RTL (~5 ms) → v1 ASIC at 22 nm FD-SOI.

### Beyond hearing — capabilities a hearing aid cannot have

Once sound is decoupled from the ear and rendered as multi-channel haptics, the system trivially extends past biological limits.

- **Infrasonic** (1–20 Hz) — earthquake precursors, large-vehicle approach, HVAC faults.
- **Ultrasonic** (20–96 kHz with appropriate MEMS) — bat activity, leak detection, dog whistles.
- **Full-sphere spatial awareness** — azimuth via beamformer, elevation via ring index, distance via envelope decay. Above and below the wearer, which biological hearing handles poorly.
- **Multi-source separation** — render two simultaneous speakers to two distinct regions of the wrist, allowing the wearer to "listen" to both in parallel.
- **Persistent acoustic memory** — last 30 s ring buffer, replayable on demand to the haptic field.
- **Contextual silencing** — known irritant classes attenuated by the classifier, not by global compression.

Biological hearing is a 20 Hz – 20 kHz omnidirectional pressure sensor with poor elevation discrimination and no scene understanding. OpenHear, on the wrist, is none of those things and all of the things they cannot be. The aids-free configuration is **superior, not equivalent**.

### Sovereignty enforced at the technical layer

The user owns:

1. **Audiogram** — `~/.openhear/audiogram.json`
2. **Haptic preference profile** — `~/.openhear/profile.json`
3. **Personal adaptation model** — `~/.openhear/model.bin` (LoRA delta over the open base)
4. **Adaptation telemetry** — `~/.openhear/training/*.parquet`
5. **Any captured audio** — opt-in only, encrypted with a key the user holds.

Enforcement is not a policy promise; it is built in:

- The NPU has no IP stack. There is no network egress in the hearing data path.
- Firmware is signed, but the signing key is the user's. A user can sign and load their own firmware. (This is the inverse of the hearing aid industry's lock-down.)
- Plain-file formats end to end — JSON, Parquet, ONNX, WAV. No proprietary container.
- Every parameter an audiologist would set in proprietary fitting software is a writable field in `profile.json`. Audiologists are welcome collaborators; they are not a key.

### Regulatory pathway — sensory substitution, not hearing aid

Regulatory classification follows mechanism, not indication. The aids-free OpenHear has the same mechanism as Neosensory Buzz and BrainPort, both of which are cleared as sensory substitution devices, not hearing aids.

| Jurisdiction | Likely classification                                              | Comparator predicate                                |
|---|---|---|
| **UK (MHRA)** | UK MDR 2002 — Class I (initial), Class IIa if claims tighten      | Neosensory Buzz                                     |
| **US (FDA)**  | 510(k) Class II, sensory substitution                              | Neosensory Buzz, BrainPort Vision Pro              |
| **EU (MDR)**  | Class I or IIa under MDR 2017/745                                  | Same                                                 |

The fastest credible path: bench validation in months → single-user adaptation log (publicly, by the developer) → multi-user pilot (n≈20) in year 1 → controlled trial in year 2 → submission in year 3. Open data at every stage.

### Open hardware path

- Schematics: KiCad 8 wristband package planned for a future `hardware/wristband/` directory; not yet committed in this repo.
- RTL: Verilog/SystemVerilog Hearing NPU package planned for a future `hardware/npu/` directory; not yet committed in this repo.
- Mechanical: FreeCAD/OpenSCAD wristband CAD planned for a future `hardware/wristband/mech/` directory; not yet committed in this repo.
- BOM: globally-available distributors only; no single-source critical parts.
- Targeting OSHWA certification at v0 and a Hackaday Prize / Open Hardware Summit submission.

### Specifically invited

- **Mechanoreceptive psychophysicists** — for Q1 (information bandwidth of the wrist) and Q4 (calibration protocol) of the [research roadmap](docs/RESEARCH_ROADMAP.md).
- **Sensory-substitution neuroscientists** — for Q2 (adaptation timeline) and the cortical remap evidence base.
- **RISC-V RTL engineers** — for the Hearing NPU.
- **Embedded DSP engineers** — for the sub-5 ms front-end and haptic renderer.
- **UK / EU / US audiology clinicians** — for the multi-user pilot and the regulatory pre-submissions.
- **Deaf and hard-of-hearing wearers** — the people the system exists for. Lived experience is a design input, not a marketing line.

The longer this section gets, the closer the architecture is to leaving the page. The architecture document and roadmap are both in this repo. Read them; fork them; contradict them; submit a PR.

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
1. Install the experimental OpenHear Android scaffold from `/mobile/` — see [mobile README](mobile/README.md) for the current skeleton-only status
2. Load your audiogram JSON (export from your audiologist or create one using `audiogram/data/FORMAT.md`)
3. Pair your aids via Bluetooth Classic or ASHA
4. Tap ▶ once you have verified the current mobile build supports the stages you need on your device; the Android app is an active public prototype, not a finished clinical tool

### Path 2 — Desktop pipeline (Windows + Noahlink Wireless 2)
1. Set your aids to linear mode (kill the factory AI — see instructions below)
2. `pip install -e .` (editable install using the new `pyproject.toml`)
   or `pip install -r requirements.txt` for the legacy flow
3. `python -m core.read_fitting` — exports the current raw Noahlink payload to JSON; add `--session` to emit the new structured `FittingSession` format and `--verbose` for DEBUG logging
4. `python -m dsp.pipeline` — starts the real-time audio processor. Useful flags: `--bypass` for A/B, `--test-tone` when no mic is plugged in, `--latency` for per-block latency logs, `--metrics-csv metrics.csv` to record CPU / RMS / latency
5. Copy `examples/config.yaml` to `~/.openhear/config.yaml` and tune it (see `docs/TUNING_GUIDE.md`); `dsp/config.py` defaults still work as a fallback

### Path 2.5 — Wristband prototype (Windows + micro:bit v2)
1. Export or copy the patient's audiogram JSON
2. Flash the micro:bit with [`wristband/openhear_firmware.py`](wristband/openhear_firmware.py) using the Windows editor workflow in [`HARDWARE.md`](HARDWARE.md#firmware-flashing-windows)
3. Wire the two-motor transistor stage exactly as described in [`HARDWARE.md`](HARDWARE.md#exact-motor-driver-wiring-tested-values)
4. Install Python dependencies with `pip install -r requirements.txt`
5. For a dry packet check, run:
   - `python -m haptic_commander --audiogram PATIENT.json --sound-class alarm --dry-run`
6. For a BLE-only smoke test, run:
   - `python -m haptic_commander --audiogram PATIENT.json --sound-class alarm`
7. For live classification, add a local YAMNet `.tflite` model and use the bundled official label CSV:
   - `python -m stream.wristband_runtime --audiogram PATIENT.json --model yamnet.tflite --labels stream/data/yamnet_class_map.csv`
8. To validate the classifier without BLE, run:
   - `python -m yamnet_classifier --model yamnet.tflite --labels stream/data/yamnet_class_map.csv --limit 10`
9. If Windows BLE pairing or discovery fails, use the debugging checklist in [`HARDWARE.md`](HARDWARE.md#windows-ble-debugging-checklist) and the release notes in [`wristband/README.md`](wristband/README.md)

The wristband runtime currently supports:
- 7 sound classes (`voice`, `doorbell`, `alarm`, `dog`, `traffic`, `media`, `silence`)
- audiogram-weighted intensity scaling from either the current v1 format or the legacy OpenHear v0.1.0 JSON export
- BLE UART transport to a micro:bit advertising as `OpenHear`
- patient safety defaults that bias toward the **worst** ear when one intensity byte must represent both ears

The v1.0.0 clinic prototype keeps Noahlink extraction on a separate hardening
track: the wristband already accepts audiogram JSON, while direct parsing in
`core/read_fitting.py` and `audiogram/reader.py` still contains placeholder
frame parsing that needs real-device confirmation.

To keep a running development memory inside the repository, use:

```bash
python -m core.future_memory add --topic sharp-hearing --note "Prototype flashed and paired."
python -m core.future_memory latest --topic sharp-hearing
```

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
- [x] `mobile/` — Android scaffold (Compose UI + Oboe/JNI audio engine skeleton)
- [ ] `mobile/` — production-ready Android DSP + hearing-aid streaming
- [ ] `learn/` — on-device preference learning engine
- [ ] `ui/` — desktop GUI (the OSCAR moment)
- [ ] iOS version of mobile app
- [ ] Community scan library
- [ ] tinyML Learn module v2

### Aids-free configuration (Vision 2)

- [x] Human sensory sovereignty platform architecture — [`docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md`](docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md)
- [x] Architecture document — [`docs/AIDS_FREE_ARCHITECTURE.md`](docs/AIDS_FREE_ARCHITECTURE.md)
- [x] Research roadmap — [`docs/RESEARCH_ROADMAP.md`](docs/RESEARCH_ROADMAP.md)
- [x] Prior art and engagement list — [`docs/PRIOR_ART.md`](docs/PRIOR_ART.md)
- [x] Go-to-market, mission, and showcase applications — [`docs/GO_TO_MARKET.md`](docs/GO_TO_MARKET.md)
- [x] Funding and partnership strategy — [`docs/FUNDING_AND_PARTNERSHIPS.md`](docs/FUNDING_AND_PARTNERSHIPS.md)
- [ ] `hardware/wristband/` — KiCad schematics, mechanical CAD, BOM (planned; directory not yet committed)
- [x] `hardware/wristband/` — micro:bit v2 prototype firmware and wiring guide
- [ ] `hardware/npu/` — open RTL for the Hearing NPU (RISC-V + custom accelerator, CERN-OHL-S; planned, directory not yet committed)
- [ ] `firmware/npu/`, `firmware/mcu/` — bare-metal Rust runtime
- [ ] `dsp/haptic/` — frequency→position mapping, illusion library, audiogram weighting
- [ ] `models/` — base classifier, separator, and personal-LoRA scaffold
- [ ] `training/protocol/` — Phase 0–4 training app and metrics
- [ ] v0 prototype on Raspberry Pi CM4 + Hailo-8L + 24-LRA wrist sleeve
- [ ] v0.5 prototype on RISC-V SBC + 64-piezo lattice
- [ ] v1 FPGA validation on Lattice ECP5
- [ ] FDA Q-Sub and MHRA Innovation Office pre-submission
- [ ] Multi-user adaptation pilot (n≈20) with a UK academic audiology partner

## OpenHear expansion — nine pillars

The pipeline, hardware work, and roadmap above remain in force exactly as written. What follows is the expansion: OpenHear as a human sensory sovereignty platform spanning nine explicit pillars.

## Pillar 1 — The OpenHear Wristband: Active Environmental Intelligence

The OpenHear Wristband is a continuous-wear frequency scanner designed to work alongside existing hearing aids now and make them unnecessary later. It converts passive amplification into active environmental intelligence.

- **Edge AI sound classification** — low-latency on-device AI identifies and classifies environmental sounds in real time, entirely locally. No cloud. No telemetry. No data leaving the wrist.
- **Multi-motor haptic array** — an array of motors creates a spatial sound field through distinct haptic patterns. Different sounds, directions, and frequencies become different signatures on the skin.
- **Directional awareness through haptic mapping** — the wristband tells the user not just what a sound is but where it is coming from, using compass-point mapping around the wrist.
- **Bluetooth LE Audio connectivity** — the wristband pairs with existing hearing aids, smartphones, Apple Watch, and smart home systems, integrating directly with the OpenHear DSP pipeline.
- **Personalised adaptive AI models** — the classifier learns the user's actual environment over time. A barbershop, a stadium, a concert hall, a surgery, and a nursery do not sound the same and should not be treated the same.
- **Proactive frequency scanning** — the wristband actively scans the spectrum and warns about sounds approaching detection threshold before they become relevant. Environmental sonar, not environmental amplification.

The first formal US industry contact for this direction is **Sharp Hearing** on **20 April 2026**, exploring collaboration from an audiology context already adjacent to Neosensory Buzz. OpenHear goes significantly further.

## Pillar 2 — Aids-Free Architecture: The Wristband as the Complete Hearing System

The wristband is not permanently a companion to hearing aids. It is the first step toward a full system in which no hearing aid, no behind-the-ear receiver, and no ear canal device of any kind is required.

- The wristband captures environmental sound via microphones, runs edge AI classification, and processes the full signal on-device.
- A dedicated **hearing-specific neural processing unit** is designed from first principles for this task, targeting sub-5 ms end-to-end latency from environmental sound capture to haptic output.
- **Somatosensory substitution** becomes the delivery path: the skin carries structured auditory information and the brain learns to read it.
- Where a minimal early receiver is useful, the system supports a coin-sized bone-conduction transducer behind the ear, driven wirelessly from the wristband, with no ear canal blockage and no clinic-gated fitting lock.
- The hardware stack is open from chip level upward: **RISC-V**, custom FPGA validation, and community-contributed hardware designs.
- The regulatory path starts as a companion device beside existing aids and builds toward standalone replacement as evidence accumulates, with the UK MDR 2002 Class IIa pathway in view for the standalone device.

## Pillar 3 — Peak Hearing for All Users

OpenHear is not only for people with hearing loss. It treats peak childhood hearing as the baseline reference and rejects progressive acoustic decline as an unchangeable fact of adult life.

- **Hearing users** get restoration and extension of sensitivity lost over time.
- **Deaf users** get full sensory access for the first time through open, trainable substitution pathways.
- **Children** get support for peak auditory development and earlier drift detection before conventional diagnosis.
- **Athletes and performers** get acoustic acuity beyond what biological hearing and training alone can deliver.

The training protocol, adaptation timelines, onboarding flows, and community training programmes are open source and user-owned.

## Pillar 4 — Selective Acoustic Sovereignty

OpenHear does not just help the user hear more. It gives the user complete control over what enters consciousness. The acoustic environment is no longer something that happens to the user; it is something the user configures.

**Required focus modes**

- **Crowd filter** — preserve coach, teammate, referee, or foreground conversation while the crowd drops away.
- **Concert mode** — keep the performance, attenuate chatter, bar noise, and venue distortion, and reconstruct the optimal listening position regardless of where the user is standing.
- **Deep focus** — maximise clarity for one voice or one task while reducing environmental load and tracking cognitive benefit through HRV correlation.
- **Situational awareness** — maximise environmental intelligence, classification, and spatial mapping for cyclists, runners, parents, and public-space safety.
- **Sleep mode** — attenuate traffic, neighbours, and irrelevant noise while preserving the user's child, their alarm, or a specific critical alert tone.
- **Performance mode** — profession-specific acoustic profiles for surgeons, pilots, musicians, athletes, dispatchers, and anyone whose work depends on hearing specific cues.
- **Privacy mode** — directional microphone nulling, acoustic fingerprint masking, and environmental sound signature anonymisation so the user controls not only what they hear but what the environment reveals about them.

The **Acoustic Profile Store** is an open community repository of acoustic profiles: forkable, shareable, reviewable, and governed like code rather than an app store.

## Pillar 5 — Therapeutic Frequency Delivery: 30 to 300 Hz

OpenHear uses the same wristband as a programmable therapeutic delivery surface across the 30-300 Hz range, either alongside hearing substitution or independently of it.

- **40 Hz gamma stimulation** — anchor protocol for cognitive and neural-entrainment research.
- **Whole-body vibration adjacency** — lower-frequency recovery and regulation patterns translated into a wrist-safe, continuous-wear format.
- **Skin and connective tissue stimulation** — 30-100 Hz protocols for collagen, elasticity, and dermal repair research.
- **Athletic recovery** — post-exercise delivery windows for muscle repair and inflammation management.
- **Personal evidence building** — HealthKit and Android Health Connect log HRV, sleep quality, activity, and skin conductance so the user builds their own evidence base locally.

Therapeutic scheduling integrates with Apple Watch and Wear OS sleep-stage detection so timing is phase-aware, measurable, and user-owned.

## Pillar 6 — iOS and Android Native Integration

Apple and Android devices are not a bolt-on companion. They are the first infrastructure layer for OpenHear's mobile runtime.

- **Apple stack** — Neural Engine, Core Haptics, Core Audio, HealthKit, Core Location, Maps, Spatial Audio, Apple Watch, ARKit, Shortcuts, and Automation.
- **Android stack** — TensorFlow Lite, NNAPI, Oboe, Health Connect, advanced haptic APIs, Google Maps Platform, Wear OS, and assistant integrations where the user wants them.
- **Location-triggered profile switching** — entering a barbershop, stadium, nursery, theatre, office, or concert hall automatically activates the right acoustic profile.
- **Open SDK** — third-party developers can build OpenHear-compatible applications without routing user data through a central company server.

All health data stays on-device and inside the user's own health record. There is no platform lock-in and no mandatory vendor cloud.

## Pillar 7 — Emotional and Cognitive Acoustic Intelligence

OpenHear learns how sound affects this specific user, not a statistical average of other people. Apple Watch and Android wearables provide the biometric substrate; OpenHear keeps the model local and the decisions explainable.

- Detect dropping HRV and automatically shift acoustic profile to attenuate stressors and optionally introduce therapeutic frequencies.
- Learn that crowd noise, transport hubs, or certain venues are physiologically stressful for this user and intervene before overload arrives.
- Distinguish positive arousal from negative arousal so a concert high is not treated like commuting stress.
- Keep all correlation data on-device in the user's HealthKit or Health Connect record plus local model storage the user can inspect, export, or delete.

## Pillar 8 — Social Acoustic Layer

OpenHear users should be able to share acoustic meaning, not just settings.

- **Shared acoustic presence** — two users in different places experience the same acoustic profile simultaneously.
- **Haptic communication** — a new non-verbal channel built from user-owned haptic vocabulary. A squeeze can mean “I am here.” A rhythm can mean “pay attention.” A burst can mean “I love this moment.”
- **Community acoustic mapping** — venues, transport hubs, parks, streets, and public spaces become annotatable for acoustic accessibility, safety, and therapeutic quality.
- **Accessibility ratings surfaced through maps** — contributed anonymously, verified by community consensus, and never dependent on uploading raw audio.

## Pillar 9 — Beyond Biological Hearing

With peak childhood hearing as the baseline, OpenHear moves into augmentation.

- **Ultrasonic detection** — 20 kHz to 100 kHz translated into haptic patterns for machinery signatures, structural monitoring, and signals no unaided human has ever perceived.
- **Infrasonic detection** — below 20 Hz for seismic activity, large-system resonance, infrasonic animal communication, and weather-adjacent environmental change.
- **360° plus spatial awareness** — horizontal, vertical, overhead, around-corner, and behind-wall cues rendered as trainable haptic information.
- **Predictive environmental awareness** — anomalies against the learned baseline of a place trigger distinct alerts.
- **Professional augmentation** — engineers hearing stress frequencies in a bridge, clinicians extending auscultation beyond biological limits, musicians hearing harmonic detail beyond the unaided ear.

## Sovereign Philosophy — Enforced at Every Layer

The Burgess Principle binary test applies to every OpenHear decision: does this feature treat the user as a sovereign individual with complete control over their own senses, or does it process them as a unit inside someone else's system. If the answer is the latter, it is redesigned until the answer is the former.

- No proprietary algorithms at any layer.
- No locked firmware.
- No platform gatekeeping.
- No company server receiving user data.
- The user's audiogram, haptic preference profile, acoustic focus modes, therapeutic schedule, trained AI model, neural adaptation data, biometric correlations, and health outcomes belong exclusively and irrevocably to them.
- The Acoustic Profile Store follows the same principles as the codebase: open, forkable, community-governed, and not controlled by a central authority.
- The open-source licence is part of the technical architecture. No future owner gets to close the sovereignty path.

### Burgess Principle extension point

The sovereign philosophy has an explicit API surface in `advocacy/`. It is a minimal, offline, dependency-free extension point that lets a companion advocacy tool (for example [Iris](https://github.com/ljbudgie/Iris), the reference Burgess Principle implementation) consume OpenHear records — audiograms, fitting profiles, MPO safety calculations — without OpenHear ever importing the companion or phoning home to it. The package produces SHA‑256 commitments over sovereign records, tags returning receipts as `SOVEREIGN` or `NULL`, and emits offline export bundles carrying both the OpenHear "experimental, not a medical device" disclaimer and an "advisory only, not legal advice" disclaimer. Raw environmental audio is refused at the adapter boundary by design. See [`docs/ADVOCACY_INTEGRATION.md`](docs/ADVOCACY_INTEGRATION.md) for the full contract. A full advocacy workflow (tribunal-ready bundles, draft challenge language, shared vault formats) is scoped for post-v1.0.0 work with Iris.

### For Industry Integrators

OpenHear's Sovereign Advocacy Layer is designed to be integrated into hearing device manufacturer software, audiology platforms, and AI clinical systems. If you have been granted permission by the author, start with <a href="docs/INTEGRATORS.md">docs/INTEGRATORS.md</a>.

### Advocacy quickstart

For a runnable, self-contained walkthrough of the full integration — happy path (SOVEREIGN bundle), tamper detection (NULL bundle), and the `RawAudioRejectedError` boundary — see [`examples/reference_integration.py`](examples/reference_integration.py). It imports only from `advocacy` and the Python standard library, and runs offline with no flags or configuration:

```bash
python examples/reference_integration.py
```


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
