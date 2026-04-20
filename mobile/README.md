# OpenHear — Android App

<!-- ⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE -->
<!-- Consult an audiologist before using any hearing device. -->
<!-- Use at your own risk. MIT Licensed. -->

> **⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE**
> Consult an audiologist before using any hearing device.
> Use at your own risk.

Real-time hearing assistance on Android. Captures mic input, processes it
through a sovereign DSP pipeline (no cloud, no telemetry), and streams the
result to Bluetooth hearing devices or earbuds.

**Current repo status:** the Android app is a public scaffold. The Compose UI,
audio engine wiring, and audiogram loader exist, but most DSP and Bluetooth
features below are still skeleton implementations rather than production-ready
hearing-aid processing.

## Features

| Category | Feature | Status |
|---|---|---|
| **DSP** | Multi-band compression (WDRC) | ✅ skeleton |
| **DSP** | Adaptive noise floor estimation | ✅ skeleton |
| **DSP** | Voice-emphasis filter | ✅ skeleton |
| **DSP** | Basic beamforming (dual-mic) | ✅ skeleton |
| **DSP** | On-device feedback cancellation (LMS) | ✅ skeleton |
| **DSP** | Own-voice detection bypass | ✅ skeleton |
| **DSP** | Safety limiter (hard clip at 0 dBFS) | ✅ skeleton |
| **Audiogram** | JSON audiogram loader | ✅ skeleton |
| **Audiogram** | Visual audiogram editor | 🔲 planned |
| **Learn** | Thumbs-up/down preference learner (v1) | ✅ skeleton |
| **Learn** | TinyML preference model (v2) | 🔲 roadmap |
| **Bluetooth** | ASHA streaming | 🔲 planned |
| **Bluetooth** | Classic A2DP / HFP streaming | 🔲 planned |
| **Bluetooth** | Auracast broadcast stub | 🔲 planned |
| **Monitoring** | Latency monitor (< 80 ms target) | ✅ skeleton |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Android App (Kotlin)              │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ Audiogram │  │  Learn   │  │   Jetpack Compose │  │
│  │  Loader   │  │  Module  │  │       UI          │  │
│  └────┬─────┘  └────┬─────┘  └────────┬──────────┘  │
│       │              │                 │             │
│       ▼              ▼                 ▼             │
│  ┌──────────────────────────────────────────────┐    │
│  │            OboeEngine (Kotlin wrapper)       │    │
│  └──────────────────┬───────────────────────────┘    │
│                     │ JNI                            │
│  ┌──────────────────▼───────────────────────────┐    │
│  │         openhear_dsp.cpp (C++ / Oboe)        │    │
│  │                                              │    │
│  │  Mic ──► Noise ──► Compress ──► Voice ──►    │    │
│  │         Reduce     (WDRC)      Emphasis      │    │
│  │                                              │    │
│  │  ──► Feedback ──► Own-Voice ──► Limiter ──►  │    │
│  │      Cancel        Bypass       (0 dBFS)     │    │
│  │                                         BT   │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## Build Requirements

| Requirement | Version |
|---|---|
| Android Studio | Hedgehog (2023.1) or later |
| Android NDK | r25+ (for Oboe native build) |
| CMake | 3.22+ |
| Min SDK | 26 (Android 8.0) |
| Target SDK | 35 |
| Kotlin | 2.0+ |
| Jetpack Compose BOM | 2024.x |

```bash
# Clone and open in Android Studio
git clone https://github.com/ljbudgie/openhear.git
cd openhear/mobile
# Open this directory in Android Studio — Gradle sync will pull Oboe and Compose.
```

## Loading an Audiogram

The app accepts audiogram data as a JSON file matching the format used by
the Python `audiogram/loader.py` module in this repository:

```json
{
  "left": {
    "250": 20, "500": 25, "1000": 30,
    "2000": 40, "4000": 55, "8000": 60
  },
  "right": {
    "250": 15, "500": 20, "1000": 25,
    "2000": 35, "4000": 50, "8000": 55
  }
}
```

Load it from the app's **Audiogram** screen, or place the file at:
```
/sdcard/Android/data/org.openhear.app/files/audiogram.json
```

The loader computes per-frequency insertion gains using a half-gain rule and
a Pure Tone Average (PTA) from 500 / 1000 / 2000 Hz.

## Safety Disclaimer

**This software is NOT a medical device.** It is an experimental, open-source
hearing-assistance tool. Incorrect settings can damage hearing.

- Always start at low volume.
- Consult a licensed audiologist before relying on any hearing device.
- The planned safety limiter stage does **not** guarantee safe output levels
  for every listener; validate the full output chain on your own hardware.

## License

MIT — see [LICENSE](../LICENSE) in the repository root.
