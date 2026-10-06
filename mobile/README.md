# OpenHear — Android App

<!-- ⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE -->
<!-- Consult an audiologist before using any hearing device. -->
<!-- Use at your own risk. MIT Licensed. -->

> **⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE**
> Consult an audiologist before using any hearing device.
> Use at your own risk.

OpenHear's Android research app. The first-run screen works without sound:
choose the bundled sample graph or load a JSON graph from the phone, read a
short graph description, and test three labelled vibration patterns.

The selected graph is copied to the app's private internal files as
`audiogram.json`. It is not uploaded, and this app does not request an account
or network permission. The bundled `examples/sample_audiogram.json` is a
synthetic sample, not a personal audiogram.

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
| **Audiogram** | Load sample or phone JSON graph; private local storage | ✅ first-run flow |
| **Audiogram** | Visual audiogram editor | 🔲 planned |
| **Learn** | Thumbs-up/down preference learner (v1) | ✅ skeleton |
| **Haptics** | Door, Alarm, and Voice phone vibration test | ✅ first-run flow |
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

### Import and run in Replit

1. On **replit.com**, choose **Create Repl / Import from GitHub** and import
   `ljbudgie/openhear`.
2. In the Shell, enter the existing Android project: `cd mobile`.
3. The Android module requires JDK 17, Android SDK 35, Android NDK r25+, and
   CMake 3.22.1. With those installed and Gradle available, build the debug APK:
   `gradle :app:assembleDebug`
4. The APK is written to
   `mobile/app/build/outputs/apk/debug/app-debug.apk`. To install and launch it
   from a connected Android device or emulator, run
   `gradle :app:installDebug`; Android Studio's **Run** button can also launch
   `app` on a selected device.

This repository does not include a Gradle wrapper. Replit's Run button alone
does not create an Android emulator; a configured Android SDK/NDK and an
attached device or emulator are needed to install and interact with the app.

## Graph file format and local storage

The phone import accepts either the legacy `left` / `right` object format or
the `left_ear` / `right_ear` threshold-list format used by
`examples/sample_audiogram.json`. For example:

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

On first launch, choose **Use the sample graph** or **Load a graph from this
phone**. A valid graph is copied into app-private internal storage. There is no
network upload, account, or shared-storage access.

The on-screen text is a simplified description of the graph and possible
speech-sound cues; it is not a diagnosis or a hearing-aid fitting.

## Safety Disclaimer

**This software is NOT a medical device.** It is an experimental, open-source
hearing-assistance tool. Incorrect settings can damage hearing.

- Always start at low volume.
- Consult a licensed audiologist before relying on any hearing device.
- The planned safety limiter stage does **not** guarantee safe output levels
  for every listener; validate the full output chain on your own hardware.

## License

MIT — see [LICENSE](../LICENSE) in the repository root.
