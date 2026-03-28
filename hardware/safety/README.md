# safety/ — Hearing Protection and Hardware Safety

**This module exists to prevent harm. Every other module in hardware/ is optional. This one is not.**

A hearing aid puts a speaker inside your ear canal. If that speaker plays sound that is too loud, it will damage your hearing permanently. This is not a theoretical risk. It is the primary failure mode of any amplification device, and it is irreversible.

Every design decision in this module prioritises one thing: **making it physically impossible for the device to produce sound loud enough to cause harm.** Software can crash, firmware can have bugs, users can set gain too high. The hardware limiter does not care. It is a circuit that clamps the electrical signal before it reaches the receiver, regardless of what the software is doing.

Read this entire document before building anything in the hardware/ module.

---

## 1. Maximum Power Output (MPO)

### What It Is

MPO is the loudest sound the hearing aid can produce, measured in dB SPL (decibels Sound Pressure Level) at the receiver output. Every commercial hearing aid has an MPO limit. OpenHear does too.

### Why It Matters

| Exposure | Duration to Damage |
|----------|--------------------|
| 85 dB SPL | 8 hours |
| 94 dB SPL | 1 hour |
| 100 dB SPL | 15 minutes |
| 110 dB SPL | Less than 2 minutes |
| 120 dB SPL | Pain threshold. Immediate risk |

A hearing aid receiver in an ear canal with a sealed mould can produce 110–120 dB SPL. Without limiting, a software bug or feedback oscillation could drive the receiver to maximum output and cause permanent hearing damage in seconds.

### How OpenHear Handles It

OpenHear uses **defence in depth** — multiple independent safety layers:

1. **Hardware MPO limiter** (this section) — a circuit that physically caps the electrical signal to the receiver. Cannot be overridden by software. Cannot be disabled by firmware bugs.
2. **Software safety layer** — digital peak limiter, gain ceiling, watchdog timer. Defence in depth. Works in normal operation but not relied upon as the sole protection.
3. **Calibration procedure** — measures actual SPL output and verifies it matches expected values.

---

## 2. Hardware MPO Limiter Circuit

This is the most important circuit in the entire build. It is simple, cheap, and it prevents hearing damage.

### How It Works

A pair of back-to-back zener diodes clamps the voltage across the receiver. When the signal voltage exceeds the zener voltage, the diodes conduct and shunt the excess energy through a series resistor. The receiver never sees more than the zener voltage, regardless of what the amplifier is doing.

This is a passive circuit. It has no power supply, no microcontroller, no firmware. It cannot crash, hang, or be misconfigured by software. It works by physics.

### Circuit Design

```
                     R_series (100Ω)
Amplifier Output ───/\/\/\/──┬──── Receiver (+)
                             │
                          ┌──┴──┐
                          │     │
                        ┌─┤     ├─┐
                        │ │ ZD1 │ │
                        │ └──┬──┘ │
                        │    │    │
                        │ ┌──┴──┐ │
                        │ │ ZD2 │ │
                        │ └──┬──┘ │
                        └────┤────┘
                             │
Ground ──────────────────────┴──── Receiver (-)
```

**Components:**
- **R_series:** 100Ω resistor in series with the receiver. Limits current and dissipates excess power as heat. Use a 1/4W or higher rated resistor.
- **ZD1 and ZD2:** Zener diodes connected back-to-back (anode-to-anode). This clamps the signal symmetrically in both polarities. The zener voltage determines the MPO.

### Component Values for Different MPO Targets

The zener voltage determines the maximum voltage across the receiver, which determines the maximum SPL output. Select based on the user's UCL (Uncomfortable Loudness Level).

| Target MPO (dB SPL) | Zener Voltage | Series Resistor | Zener Part Number | Notes |
|---------------------|---------------|-----------------|-------------------|-------|
| 90 dB SPL | 0.47V | 100Ω | BZX79-C0V47 | Very conservative. For mild loss with normal UCL |
| 100 dB SPL | 1.5V | 100Ω | BZX79-C1V5 | Conservative. For moderate loss |
| 110 dB SPL | 4.7V | 100Ω | BZX79-C4V7 | Standard. For moderately-severe to severe loss |
| 120 dB SPL | 15V | 100Ω | BZX79-C15 | Maximum. For profound loss only. This is the absolute ceiling — never exceed this |

> **Important:** These values are approximate and depend on the specific receiver model's sensitivity (SPL per volt). The [calibration procedure](#4-calibration-procedure) verifies the actual output. Always calibrate after building the limiter circuit. If measured MPO exceeds the target, use a lower zener voltage.

> **When in doubt, use a lower zener voltage.** A limiter that is too conservative reduces maximum volume. A limiter that is too permissive risks hearing damage. There is no symmetry here — one outcome is inconvenient, the other is permanent.

### The Critical Property

**This circuit CANNOT be overridden by software.**

No firmware update, no configuration change, no bug, no hack can make the receiver produce more than the clamped voltage. The zener diodes are passive components. They do not execute code. They do not have an off switch. They are always active.

This is intentional. The hardware limiter is the last line of defence, and it must be unconditionally reliable.

---

## 3. Software Safety Layer (Defence in Depth)

The hardware limiter is the primary safety mechanism. The software safety layer is the secondary mechanism. It handles things the hardware limiter cannot — like detecting abnormal conditions and muting output before the limiter even needs to engage.

### Digital Peak Limiter

The Tympan sketch includes a digital peak limiter that prevents the DSP output from exceeding a configurable maximum level. This is set below the hardware limiter threshold so that in normal operation, the hardware limiter never activates.

```
Software limiter threshold: MPO - 5 dB (safety margin)
Hardware limiter threshold: MPO (absolute maximum)
```

The 5 dB gap means the software limiter handles normal peaks, and the hardware limiter only engages if the software fails.

### Maximum Gain Ceiling

Each frequency channel has a maximum gain ceiling that cannot be exceeded regardless of the audiogram-derived gain target. This prevents a data entry error or corrupted audiogram file from producing dangerous gain values.

| Frequency Range | Maximum Gain Ceiling |
|----------------|---------------------|
| 125–500 Hz | 50 dB |
| 500–2000 Hz | 55 dB |
| 2000–8000 Hz | 60 dB |

These ceilings are set in the Arduino sketch and are not adjustable via the Tympan Remote App.

### Startup Self-Test

When the Tympan powers on, the sketch runs a self-test before enabling audio output:

1. **Mute output** — receivers are silent during self-test
2. **Check input levels** — verify microphone signals are within expected range (not open-circuit, not shorted)
3. **Check output path** — send a sub-audible test tone and verify the signal path is intact
4. **Verify MPO limiter** — send a brief over-limit signal and verify the output is clamped (requires measurement circuit, optional)
5. **Enable output** — if all tests pass, unmute and begin normal operation
6. **If any test fails** — remain muted, flash error LED, log error to SD card

### Watchdog Timer

A hardware watchdog timer monitors the DSP processing loop. If the DSP stalls (crashes, hangs, enters an infinite loop), the watchdog triggers and mutes the output within 10ms.

**Why this matters:** A DSP stall could leave the last output sample playing continuously. If that sample happens to be at maximum amplitude, the receiver would produce a continuous loud tone. The watchdog prevents this by muting the output if the DSP doesn't "check in" within 10ms.

---

## 4. Calibration Procedure

Calibration verifies that the actual sound output matches the expected output at every frequency. It must be done after every hardware change and after every configuration change.

### Equipment Needed

- Calibration microphone: Dayton Audio iMM-6 or equivalent with known sensitivity
- 2cc coupler (simulates the volume of a sealed ear canal) — can be 3D printed or purchased
- Audio signal generator (software: REW, Audacity, or similar)
- SPL meter app or measurement software calibrated to the microphone

### Procedure

1. **Connect the ear mould to the 2cc coupler.** The coupler simulates the ear canal volume. Place the calibration microphone at the measurement port.

2. **Generate known-level tones.** Play pure tones at each audiometric frequency (250, 500, 1000, 2000, 3000, 4000, 6000, 8000 Hz) through the hearing aid at the programmed gain level.

3. **Measure SPL at each frequency.** Record the measured dB SPL. Compare with the expected output (input level + programmed gain at that frequency).

4. **Verify MPO at each frequency.** Increase the input level until the output reaches the expected MPO limit. Verify that the output does not exceed the target MPO. The hardware limiter should engage and cap the output.

5. **Log results to SD card.** The Tympan sketch logs calibration measurements for future reference.

6. **Pass/fail criteria:**
   - Output at programmed gain: within ±3 dB of target at all frequencies
   - MPO limit: must not exceed target MPO at any frequency
   - If MPO is exceeded at any frequency: **stop, do not use the device, check the hardware limiter circuit**

### When to Recalibrate

- After any configuration change (gain, compression, MPO targets)
- After replacing the receiver
- After reprinting or modifying the ear mould
- After replacing the battery
- Every 3 months during regular use
- Whenever the device sounds "different" — trust your ears, then verify with measurements

---

## 5. Risk Register

Every identified failure mode, its potential harm, and how OpenHear mitigates it.

| # | Risk | Severity | Likelihood | Mitigation | Residual Risk |
|---|------|----------|-----------|-------------|---------------|
| 1 | Software bug produces loud output | **Critical** — hearing damage | Medium | **Hardware zener clamp** caps output regardless of software state. Cannot be overridden | Low — hardware limiter is passive and unconditional |
| 2 | Receiver failure (shorted voice coil) | **Critical** — loud transient | Low | **Hardware clamp** limits transient amplitude. **Watchdog timer** mutes within 10ms if DSP detects anomaly | Low |
| 3 | Feedback oscillation (whistling) | **High** — sustained loud tone | Medium | **Hardware clamp** caps amplitude. **Adaptive feedback cancellation** in DSP. **Gain ceiling** prevents runaway loop gain | Low — three independent mitigations |
| 4 | User sets gain too high | **High** — gradual hearing damage from chronic overexposure | Medium | **Software warning** when gain exceeds recommended levels. **Hardware clamp** prevents acute damage. **Gain ceiling** in firmware | Medium — user can override software warnings. Hardware clamp prevents acute harm but not chronic overexposure at levels below MPO |
| 5 | Battery voltage sag under load | **Medium** — unpredictable DSP behaviour | Medium | **Low-battery detection** in firmware. **Graceful shutdown** with user notification. Tympan hardware includes voltage monitoring | Low |
| 6 | Ear mould causes physical discomfort or injury | **Medium** — ear canal irritation or injury | Low | **Fitting guide** with safety warnings. **Maximum insertion depth** specified. **Biocompatible resin** required. **Wear testing protocol** | Low — following the fitting guide minimises risk |
| 7 | Uncured resin causes skin reaction | **Medium** — chemical irritation or allergic reaction | Low | **Post-processing guide** specifies full UV cure. **Biocompatible resin** required. Itching noted as warning sign requiring investigation | Low |
| 8 | Calibration drift over time | **Low** — gradual change in output levels | Medium | **Recalibration schedule** (every 3 months). **Calibration logging** for trend detection | Low |

---

## 6. Statement of Responsibility

**OpenHear is not a regulated medical device.** It has not been submitted to or approved by any regulatory body including the FDA, CE/UKCA, or any equivalent authority. It is not sold, prescribed, dispensed, or fitted by a licensed professional.

**You build this device. You use this device. You are responsible for your own hearing health.**

The safety module described in this document is designed to **exceed the safety margins of commercial hearing aids.** The hardware MPO limiter is a passive, unconditional circuit that cannot be overridden by software. The calibration procedure verifies actual output levels. The risk register identifies and mitigates every failure mode we can identify.

But no safety system is perfect. Components can fail. Designs can have flaws we haven't identified. Your hearing is irreplaceable.

**If in doubt, reduce gain.** A hearing aid that is slightly too quiet is inconvenient. A hearing aid that is too loud causes permanent damage. There is no symmetry between these outcomes.

**If something sounds wrong, remove the device immediately.** Pain, sudden loudness changes, or unusual sounds are all signals to stop using the device and investigate before continuing.

**Hearing damage cannot be undone.** Act accordingly.

---

## Files in This Module

| File | Description |
|------|-------------|
| `README.md` | This document. Safety design, MPO limiter circuit, calibration procedure, risk register |
| `mpo_calculator.py` | Python script: takes an audiogram, calculates recommended MPO limits and component values per frequency |
