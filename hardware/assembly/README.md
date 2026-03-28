# assembly/ — Build Guide

A step-by-step guide to building your OpenHear hearing aid. Written for someone who has never soldered before. If you have soldered before, you will move faster, but read every step anyway — the safety-critical steps are marked and must not be skipped.

---

## 1. Tools Needed

You do not need expensive tools. A basic kit costs about £40 and will last for years.

| Tool | What It's For | Approx Cost | Notes |
|------|--------------|-------------|-------|
| Soldering iron (temperature-controlled) | Joining wires to connectors and circuit boards | £15–25 | Entry-level is fine. Look for adjustable temperature (set to 350°C for lead-free solder). Recommended: Pinecil or TS100 |
| Lead-free solder, 0.8mm diameter | Filler material for solder joints | £5 | 0.8mm is thin enough for small joints. Lead-free (Sn99.3/Cu0.7) is safer to work with. Do not use leaded solder |
| Wire strippers | Removing insulation from wire ends | £5 | Adjustable type recommended. Set for 30 AWG wire |
| Flush cutters | Trimming wire and component leads | £5 | Small, sharp. One clean cut — don't use scissors |
| Helping hands / third hand tool | Holding components while you solder | £8 | Alligator clips on an adjustable arm. Essential when you only have two hands |
| Multimeter | Measuring voltage, resistance, and continuity | £10–15 | Basic digital multimeter. Must have continuity beep function |
| Magnifying glass or loupe | Inspecting solder joints | £3 | 5x–10x magnification. A head-mounted magnifier works too |

**Optional but helpful:**
- Solder wick or solder sucker (for fixing mistakes)
- Silicone soldering mat (protects your work surface)
- Fume extractor or desk fan (for solder fume ventilation)

---

## 2. Workspace Setup

### Ventilation

Solder fume (flux smoke) is an irritant. Do not breathe it directly.

- Work near an open window, or
- Use a small desk fan blowing fumes away from your face, or
- Use a fume extractor with activated carbon filter

You do not need laboratory-grade ventilation. A gentle breeze away from your face is sufficient.

### ESD Safety

ESD (Electrostatic Discharge) can damage the Tympan board. Basic precautions:

- Touch a grounded metal object before handling the Tympan (a radiator, the metal case of a plugged-in computer)
- Work on an anti-static mat if you have one. If not, avoid working on carpet or synthetic surfaces
- Handle the Tympan by its edges. Avoid touching the components on the board

### Lighting

Good lighting prevents mistakes. Use a desk lamp positioned to eliminate shadows on your work area. Daylight-colour LED is ideal.

---

## 3. Tier 1 Build: Explorer (~30 minutes)

**What you're building:** Tympan connected to headphones and a lavalier microphone. Your audiogram loaded as a DSP configuration. Real-time personalised audio processing.

**Components needed:** Tympan Rev F, wired over-ear headphones, 3.5mm lavalier mic, USB cable. See [BOM](../BOM.md) Tier 1.

### Steps

**3.1 — Unbox and inspect the Tympan**

Open the Tympan packaging. Verify you have the board, USB cable, and any included documentation. Inspect the board for obvious damage (bent pins, cracked components). If anything looks damaged, contact Tympan support before proceeding.

**3.2 — Install Arduino IDE and Tympan Library**

1. Download and install [Arduino IDE](https://www.arduino.cc/en/software) (version 2.x recommended)
2. In Arduino IDE, go to Tools → Board → Boards Manager. Search for "Teensy" and install Teensyduino
3. Go to Sketch → Include Library → Manage Libraries. Search for "Tympan" and install the Tympan Library
4. Verify installation: File → Examples → Tympan Library. You should see example sketches

**3.3 — Connect headphones and microphone**

1. Plug the headphones into the Tympan's 3.5mm output jack
2. Plug the lavalier microphone into the Tympan's 3.5mm input jack
3. Connect the Tympan to your computer via USB

**3.4 — Generate your personalised sketch**

Run the OpenHear bridge script to generate an Arduino sketch from your audiogram:

```bash
# Generate a sketch for your right ear:
python -m hardware.tympan.audiogram_to_tympan audiogram/data/burgess_2021.json my_sketch.ino

# Or for both ears (binaural):
python -m hardware.tympan.audiogram_to_tympan audiogram/data/burgess_2021.json my_sketch.ino --binaural
```

Replace `burgess_2021.json` with your own audiogram file. The script prints a summary of the gain profile and DSP parameters it generated.

**3.5 — Upload the sketch**

1. Open the generated `.ino` file in Arduino IDE
2. Select board: Tools → Board → Teensy 4.1
3. Select port: Tools → Port → (your Tympan's USB port)
4. Click Upload (arrow button)
5. Wait for "Done uploading" message

**3.6 — Verify audio passthrough**

1. Put on the headphones
2. Speak into the lavalier microphone
3. You should hear your voice through the headphones with the gain profile applied
4. Sound should be clear, with no distortion at normal speaking levels
5. If you hear nothing: check connections, verify the sketch uploaded successfully
6. If you hear distortion: reduce the master gain in the sketch and re-upload

**3.7 — Fine-tune with Tympan Remote App**

1. Install the Tympan Remote App on your phone ([Android](https://play.google.com/store/apps/details?id=com.creare.tympanRemote) / [iOS](https://apps.apple.com/app/tympan-remote/id1530523124))
2. Enable Bluetooth on the Tympan (it should be enabled by default in the generated sketch)
3. Connect to the Tympan from the app
4. Adjust gain, compression, and noise reduction in real time
5. Find settings that sound best to you

**Tier 1 is complete.** You have a working, audiogram-personalised hearing device.

---

## 4. Tier 2 Build: Builder (3–4 hours)

**What you're building:** A wearable binaural hearing aid with BTE earpieces, custom ear moulds, balanced armature receivers, and a hardware MPO limiter circuit.

**Components needed:** Everything from Tier 1, plus Tympan Earpiece Kit, Knowles receivers, 3D printed ear moulds, impression kit, LiPo battery, wire and connectors. See [BOM](../BOM.md) Tier 2.

**Prerequisites:**
- Complete [Tier 1](#3-tier-1-build-explorer-30-minutes) first
- Read the [safety module](../safety/README.md) completely
- Make your ear moulds using the [shell/ guide](../shell/README.md)

### Steps

**4.1 — Connect the Tympan Earpiece Kit**

The Tympan Earpiece Kit includes left and right BTE housings with built-in dual MEMS microphones. Connect them to the Tympan board following the kit instructions.

1. Connect the earpiece cables to the Tympan's earpiece connectors
2. Verify microphone input: speak near the earpieces and check for signal in the Arduino Serial Monitor

**4.2 — Solder receiver wires**

Each Knowles balanced armature receiver has two solder pads. You need to attach thin wire (30 AWG silicone) to connect them to the Tympan's output.

1. Cut two 15cm lengths of 30 AWG silicone wire per receiver (4 total for binaural)
2. Strip 3mm of insulation from each end
3. Tin the wire tips: apply a small amount of solder to each stripped end
4. Tin the receiver pads: apply a tiny amount of solder to each pad on the receiver
5. Solder the wires to the receiver pads. This is the smallest soldering in the build — use magnification and steady hands. Touch the tinned wire to the tinned pad, briefly touch with the iron. The joint should be shiny and smooth
6. Allow to cool. Tug gently to verify the joint is solid
7. Slide heat shrink over each joint and shrink with the iron's heat or a heat gun

> **Tip:** If you've never soldered before, practice on some scrap wire first. Make 10 joints, inspect each one. A good joint is shiny, smooth, and conical. A bad joint is dull, blobby, or has visible gaps.

**4.3 — Install receivers in ear moulds**

1. Thread the receiver wire through the wire channel in the ear mould
2. Insert the receiver into the receiver bore. It should slide in with light pressure and hold by friction
3. Verify the receiver tip is flush with the medial (inner) end of the mould
4. Verify the wire exits cleanly from the lateral (outer) end without kinking

**4.4 — Build the MPO limiter circuit** ⚠️ SAFETY CRITICAL

**Read the [safety module](../safety/README.md#2-hardware-mpo-limiter-circuit) before starting this step.**

Use the [MPO calculator](../safety/mpo_calculator.py) to determine the correct component values for your audiogram:

```bash
python -m hardware.safety.mpo_calculator audiogram/data/burgess_2021.json
```

Build the circuit on a small piece of perfboard (stripboard):

1. Place the 100Ω series resistor on the perfboard
2. Place two zener diodes back-to-back (anode-to-anode) in parallel across the output
3. Solder all connections
4. Use the multimeter to verify:
   - Continuity from input to output through the resistor (should read ~100Ω)
   - No short circuit between output and ground (should read high resistance in both directions until zener voltage is reached)
5. Build one limiter circuit per ear (two total for binaural)

**4.5 — Connect limiter inline**

The limiter circuit goes between the Tympan's output and the receiver:

```
Tympan output → Limiter input → Limiter output → Receiver
```

1. Connect the Tympan output wire to the limiter input
2. Connect the limiter output to the receiver wire
3. Connect the limiter ground to the Tympan ground
4. Verify all connections with the multimeter (continuity check)

**4.6 — Upload binaural sketch**

Generate and upload a binaural sketch:

```bash
python -m hardware.tympan.audiogram_to_tympan audiogram/data/burgess_2021.json binaural.ino --binaural
```

Upload via Arduino IDE as in Tier 1.

**4.7 — Calibrate** ⚠️ SAFETY CRITICAL

Follow the [calibration procedure](../safety/README.md#4-calibration-procedure) completely. Do not skip this step. Do not wear the device until calibration is complete and all frequencies pass.

---

## 5. Tier 3 Build: Sovereign (2–3 days including print time)

**What you're building:** A fully custom integrated device with a precision-printed shell, integrated components, and calibrated with a measurement microphone.

**Components needed:** Everything from Tier 2, plus resin printer, biocompatible resin, calibration microphone. See [BOM](../BOM.md) Tier 3.

**Prerequisites:**
- Complete [Tier 2](#4-tier-2-build-builder-3-4-hours) first — you need a working system before integrating into a custom shell
- Read the [3D printing guide](../shell/README.md) completely

### Steps

**5.1 — Print custom shells**

Follow the complete [3D printing guide](../shell/README.md):

1. Take ear impressions with medical silicone
2. Scan impressions to STL
3. Add channels using the [parametric mould template](../shell/parametric_mould.md)
4. Print at 0.05mm layer height with biocompatible resin
5. Post-process: IPA wash, UV cure, sand

Allow 24 hours for printing and curing.

**5.2 — Integrate components into custom shell**

1. Install receivers into the custom moulds (same process as Tier 2, step 4.3)
2. Route wires through the shell channels
3. Mount the MPO limiter circuit inside the BTE housing (secure with hot glue or mounting tape)
4. Connect all wiring
5. Verify with multimeter: continuity through the signal chain, no shorts to ground

**5.3 — Full wiring**

1. Connect earpiece microphones to Tympan input
2. Connect MPO limiter output to receivers
3. Connect LiPo battery to Tympan
4. Verify the Tympan powers on from battery
5. Verify all audio paths with multimeter continuity check

**5.4 — Calibrate with measurement microphone** ⚠️ SAFETY CRITICAL

Use the Dayton Audio iMM-6 calibration microphone and a 2cc coupler:

1. Follow the [calibration procedure](../safety/README.md#4-calibration-procedure)
2. Measure output SPL at all audiometric frequencies
3. Verify MPO at all frequencies
4. Log all results to SD card
5. Do not proceed until all frequencies pass calibration

**5.5 — Wear testing**

1. Insert moulds (unpowered first — verify comfort)
2. Power on at minimum gain
3. Gradually increase to target gain
4. Wear for 1 hour — check comfort and sound quality
5. Wear for 4 hours — check for developing discomfort
6. Wear for 8 hours — full day test
7. Log any issues and iterate on fit or settings

---

## 6. Verification Checklist

Before using your OpenHear device for regular wear, every item on this list must be checked. No exceptions.

- [ ] **MPO limiter installed and tested** — hardware limiter circuit is in-line for both ears. Verified with multimeter (resistance reading across limiter matches expected value)
- [ ] **Calibration completed at all frequencies** — SPL output measured and verified at 250, 500, 1000, 2000, 3000, 4000, 6000, and 8000 Hz. All within ±3 dB of target
- [ ] **MPO verified** — output does not exceed target MPO at any frequency. Hardware limiter engages correctly
- [ ] **Feedback cancellation active** — no sustained whistling with moulds in place and gain at target levels
- [ ] **Battery life tested** — minimum 8 hours of continuous operation on a full charge
- [ ] **Comfort tested over 4+ hours** — no pain, no pressure points, no developing soreness
- [ ] **Emergency mute configured** — button or gesture to immediately mute output is configured and tested
- [ ] **Calibration log saved** — all calibration data saved to SD card with date and configuration details

---

## 7. Troubleshooting

### Feedback (Whistling)

**Symptom:** High-pitched whistling or squealing, especially at higher gain settings.

**Causes and fixes:**

| Cause | Fix |
|-------|-----|
| Poor ear mould seal | Reprint mould with tighter fit (reduce canal diameter by 0.1mm). Check for wax buildup in ear canal |
| Gain too high at specific frequencies | Reduce gain at the feedback frequency. Check gain ceiling settings |
| Feedback cancellation not active | Verify feedback cancellation is enabled in the sketch. Reupload if needed |
| Vent too large | Reduce vent diameter (switch to next smaller size in the [vent guide](../shell/README.md#vent-sizing-guide)) |
| Receiver not fully seated in bore | Remove and reseat the receiver. Verify bore dimensions match receiver |

### Distortion

**Symptom:** Sound is crunchy, clipping, or harsh, especially on loud inputs.

| Cause | Fix |
|-------|-----|
| Software limiter clipping too aggressively | Increase the software limiter threshold (but never above hardware MPO) |
| Compression ratio too high | Reduce compression ratios. Regenerate sketch with updated audiogram if needed |
| Hardware limiter engaging on normal signals | Zener voltage may be too low. Recalculate MPO targets and consider higher zener voltage |
| Input overload | Tympan input is overloading on loud sounds. Reduce input gain or add input attenuation |

### Intermittent Audio (Dropouts)

**Symptom:** Audio cuts in and out, crackles, or has gaps.

| Cause | Fix |
|-------|-----|
| Loose solder joint | Inspect all solder joints with magnification. Reflow any that look dull or cracked |
| Damaged wire | Check all wires for kinks, breaks, or frayed insulation. Replace damaged wire |
| Connector not fully seated | Reseat all connectors. Check for bent pins |
| Low battery | Check battery voltage. Charge or replace. The Tympan may behave unpredictably below 3.3V |
| SD card error | Remove SD card and test without it. If audio returns, the SD card may be failing (replace) |

### Discomfort

**Symptom:** Pain, pressure, soreness, or itching from ear moulds.

| Cause | Fix |
|-------|-----|
| Mould too tight | Sand down the canal portion by 0.1–0.2mm at the pressure point. See [fitting guide](../shell/README.md#iteration) |
| Mould too long | Shorten the canal portion. Maximum depth is 15mm from canal entrance |
| Rough surface | Sand with 800-grit wet sandpaper until smooth |
| Resin sensitivity | Re-cure under UV for 30 minutes. If itching persists, try a different biocompatible resin |
| Moisture buildup | Remove and dry the mould and ear canal hourly until you identify a comfortable wear duration |

### No Audio Output

**Symptom:** Device powers on but no sound from receivers.

| Cause | Fix |
|-------|-----|
| Sketch not uploaded | Verify the sketch compiled and uploaded successfully in Arduino IDE |
| Muted | Check if the device is in mute mode (startup self-test may have failed — check serial output) |
| Wrong output selected | Verify the sketch is configured for earpiece output, not headphone output |
| Receiver wiring reversed | Check polarity. Reversed wiring won't damage the receiver but may produce very quiet or phase-cancelled output |
| Receiver damaged | Test with a multimeter — the receiver should show 10–100Ω impedance. If open circuit (infinite resistance), the receiver is damaged. Replace it |
