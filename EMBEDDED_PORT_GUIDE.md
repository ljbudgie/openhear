# Embedded Port Guide: Moving OpenHear to Production Wearables

**Status**: Draft v0.1 (April 22, 2026)  
**Goal**: Provide a practical roadmap and reference implementations to port the current Python-based DSP, wristband runtime, haptic pipeline, and sound classification to low-power embedded environments (C/C++, Rust, or future RISC-V with custom accelerator) while achieving ≤5–10 ms end-to-end latency and low average power for always-on use.

## Why This Guide Exists
The Python DSP (`dsp/`) and prototypes (`wristband/`, `haptic_commander.py`, `yamnet_classifier.py`) work great for desktop/phone testing and sovereignty demos, but real wearable integration (including potential Whoop-style fusion) needs optimized embedded code. This guide bridges that gap and accelerates contributions from embedded developers or manufacturers.

## Target Platforms (Priority Order)
1. nRF52 / micro:bit v2 (current baseline)
2. RP2040 or Raspberry Pi CM4 (quick validation)
3. Custom RISC-V MCU or FPGA with MAC tiles
4. Future Hearing NPU (see `hardware/` plans)

## High-Level Embedded Architecture
Mic Array → Sound Classification (TFLite Micro) → Audiogram-shaped DSP → Haptic Renderer → BLE/Health Data Fusion → Actuators

Key modules to port:
- `dsp/` (WDRC, LMS feedback cancellation, beamforming, own-voice bypass, frequency shaping)
- Wristband runtime + YAMNet inference
- `haptic_commander.py` spatial mapping + audiogram-weighted intensity
- Audiogram JSON loader
- Sovereignty checks (lightweight)

## Latency & Power Budget (Target)
- Total end-to-end: ≤8–10 ms
- Mic acquisition: <1 ms
- Classification: <2 ms
- DSP chain: <3–4 ms
- Haptic rendering: <1 ms
- Power: <100 mW active, aggressive duty-cycling when quiet

## Porting Recommendations
- Use **CMSIS-DSP** (ARM) or equivalent for audio filters
- **TFLite Micro** for the YAMNet classifier
- Fixed-point / integer math for speed and power
- **Rust** (`embassy-rs`) or C++ for safety-critical parts (BLE, haptics)
- Audio sampling: 16–48 kHz

### Quick Starter Skeleton (C++ style for nRF52/RP2040)
```cpp
// dsp_embedded_core.cpp - placeholder
#include "arm_math.h"  // or cmsis_dsp

void process_audio_frame(int16_t* buffer, size_t len, const AudiogramProfile& ag) {
    // 1. Apply audiogram-based FIR/IIR shaping
    // 2. WDRC + noise gating + beamforming
    // 3. LMS feedback cancellation update
    // 4. Map classified sound to haptic commands via haptic_commander logic
    // 5. Optional: Adjust based on HRV/recovery from fused sensor data
}
