# OpenHear Roadmap

*Where we have been, where we are, and where we are going.*

---

## Completed (2024–2026)

The foundation is built. These modules are implemented, tested, and working.

| Module | Description | Status |
|--------|-------------|--------|
| `core/` | Fitting data reader — reads audiogram and fitting profiles from hearing aids via Noahlink Wireless 2, exports as plain JSON | ✅ Complete |
| `audiogram/` | Audiogram reader, visualiser, and open-format exporter — your thresholds in a format you can read | ✅ Complete |
| `dsp/pipeline` | Real-time Python DSP pipeline — PyAudio + NumPy audio processing engine | ✅ Complete |
| `dsp/compression.py` | Wide Dynamic Range Compression (WDRC) — tunable knee point, ratio, attack/release | ✅ Complete |
| `dsp/noise_reduction.py` | Adaptive noise floor estimation and reduction | ✅ Complete |
| `dsp/voice_clarity.py` | Voice-frequency emphasis (1–4 kHz) for speech intelligibility | ✅ Complete |
| `dsp/feedback_canceller.py` | LMS adaptive feedback cancellation — eliminates whistling in real time | ✅ Complete |
| `dsp/own_voice_bypass.py` | Own-voice detection and DSP bypass — hear yourself as you are | ✅ Complete |
| `dsp/config.py` | Central configuration — every parameter exposed, user-editable | ✅ Complete |
| `stream/` | Bluetooth audio output module — streams processed audio to hearing aids | ✅ Complete |
| `hardware/ite-shells/` | Parametric ITE shell system — OpenSCAD design, photogrammetry workflow, print settings | ✅ Complete |
| `hardware/ite-shells/sweatproof.md` | Sweat-proofing guide — nano-coating, lotus-effect microstructures | ✅ Complete |
| `voice/` | Voice analysis module | ✅ Complete |
| Noahlink Wireless 2 bridge | USB HID communication with HIMSA protocol for fitting data access | ✅ Complete |
| Tympan integration | Compatibility with Tympan open-source hearing aid platform | ✅ Complete |

---

## In Progress (2026)

Active development. These modules are being built right now.

| Module | Description | Status |
|--------|-------------|--------|
| `mobile/` | Android real-time DSP app — Kotlin + Oboe, native audio processing on your phone. The sovereign pipeline in your pocket. | 🔨 In progress |
| Learn module v1 | Thumbs-up / thumbs-down preference learning — the simplest possible feedback loop. You tell it what sounds good. It remembers. | 🔨 In progress |

---

## Planned (2026–2027)

Designed, scoped, and ready for implementation. Community contributions welcome.

### Software

| Feature | Description | Target |
|---------|-------------|--------|
| **iOS mobile app** | Port of the Android DSP app to iOS using Swift + AVAudioEngine. Same sovereignty, different platform. | 2026–2027 |
| **Desktop GUI** | Full graphical interface for the DSP pipeline — the OSCAR moment. Audiogram visualisation, real-time parameter adjustment, fitting profile management. The day OpenHear becomes accessible to non-technical users. | 2027 |
| **tinyML Learn module v2** | On-device neural preference learner. Runs on the phone's NPU. Learns your preferences from usage patterns, not cloud data. Your hearing profile improves every day. | 2027 |
| **ASHA Bluetooth LE Audio streaming** | Audio Streaming for Hearing Aid (ASHA) protocol support for direct streaming from Android to compatible hearing aids without intermediate Bluetooth Classic pairing. | 2027 |
| **Auracast broadcast audio support** | Bluetooth LE Audio broadcast support — receive shared audio streams in public venues (cinemas, lecture halls, airports) directly through OpenHear. | 2027 |

### Hardware

| Feature | Description | Target |
|---------|-------------|--------|
| **Community scan library** | Anonymised ear canal scan repository — statistical shell templates derived from community-contributed photogrammetry scans. Start with a good-enough shell before scanning your own ear. | 2026–2027 |
| **Multi-material ITE shells** | Dual-vat resin printing — rigid structural shell with soft silicone canal tip in a single print. Better comfort, better seal, better sound. | 2027 |
| **Temperature-adaptive canal tips** | Shape-memory polymer tips that soften at body temperature for a conforming seal and stiffen at room temperature for easy insertion. | 2027 |

---

## Long-term (2027+)

Research-stage ideas. Some may never ship. All are worth pursuing.

| Feature | Description |
|---------|-------------|
| **AI-assisted shell design** | Automatic shell geometry generation from ear canal scan — upload a scan, receive a printable shell. Neural mesh-to-CAD pipeline. |
| **Injection-moulded silicone shells** | Move beyond resin printing to medical-grade silicone shells produced via 3D-printed moulds. Professional durability, DIY manufacturing. |
| **Open scan-to-shell pipeline** | Fully automated end-to-end workflow: scan ear → generate mesh → fit parametric model → export STL → slice → print. Zero manual intervention. |
| **Shared fitting database** | Community-contributed, anonymised fitting profiles indexed by audiogram shape. New users start with profiles from people with similar hearing losses. Privacy-preserving, opt-in, locally stored. |

---

## Contributing to the roadmap

This roadmap is a community document. If you have an idea, a correction, or a feature request — open an issue. If you have the skills to build something on this list — open a pull request.

The best contributions come from people who wear hearing aids and know what is broken. If that is you, this is your roadmap too.

---

## Safety & Disclaimer

> **⚠️ EXPERIMENTAL PROJECT — NOT A MEDICAL DEVICE**
>
> OpenHear is an experimental open-source project. It has not been evaluated, approved, or cleared by any regulatory body (FDA, MHRA, CE/UKCA, or equivalent). It is not a medical device. It is not intended to diagnose, treat, cure, or prevent any medical condition.
>
> Hearing loss is a medical condition. Consult a qualified audiologist before making any changes to your hearing aid configuration. Incorrect amplification settings can cause discomfort or, in extreme cases, further hearing damage. Always start with conservative gain values and increase gradually.
>
> Features listed under "Planned" and "Long-term" are forward-looking descriptions of intended development. They are not commitments, guarantees, or promises of delivery. Use all released software at your own risk.

---

*OpenHear, 2026*
*MIT Licensed — copy, share, translate, improve.*
