# OpenHear v2 — Standalone Mode (No Phone)

**Wear it. It listens. It vibrates. Nothing else required.**

This guide gets the wristband running completely on its own — no phone,
no app, no Bluetooth needed for normal use. The microphone, classifier,
and haptic drivers all run on the wristband itself.

---

## What you gain that average hearing doesn't give you

The wristband adds a second sensory channel — haptic — that works in
parallel with whatever residual hearing you have. Unlike ears:

- **It works when you're asleep** (smoke alarm at 3am with aids out).
- **It can't be masked by loud music or conversation** — haptics still fire.
- **It encodes direction as texture** — alarm alternates left/right motors so
  you know to scan; vehicle fires the left motor only (UK road side).
- **Seek mode** — flick your wrist sharply, then rotate toward a sound.
  The wristband tells you when you're facing it. No second mic required.
- **Audiogram-weighted intensity** — the sounds you've lost the most are
  felt the hardest. It's calibrated to your specific loss, not generic.

---

## How it works (plain English)

```
  Microphone  →  Classifier  →  Audiogram table  →  Spatial haptics
  (on wrist)     (on wrist)      (baked in)          (left + right motor)
```

1. The onboard PDM microphone listens continuously.
2. A tiny AI model (trained in ~20 minutes, runs locally on the chip)
   recognises what it hears from **10 categories**.
3. Your audiogram (from burgess_2021.json) is baked into the firmware as
   a table. Sounds you've lost the most hearing at hit harder.
4. Two DRV2605L drivers fire the left and right LRA motors independently
   with patterns that encode what the sound is and roughly where.

---

## Step 1 — Train your classifier (~25 minutes, free)

### 1.1 Set up Edge Impulse

1. Go to **https://edgeimpulse.com** — create a free account.
2. **Create new project** → name it `openhear-classifier`.
3. **Data acquisition → Upload existing data**.
4. Upload audio samples for each of the **10 classes** below.
   Each class needs at least 20–30 clips (1–3 seconds each).

| Class | What to find | Free source |
|---|---|---|
| `voice` | People talking | Mozilla Common Voice, FreeSound |
| `alarm` | Fire alarms, beeping | FreeSound (search "alarm") |
| `doorbell` | Door chimes | FreeSound (search "doorbell") |
| `baby_cry` | Infant crying | FreeSound (search "baby cry") |
| `vehicle` | Cars, engines, traffic | FreeSound (search "car engine") |
| `appliance` | Kettle, microwave beeps | FreeSound (search "beep") |
| `dog_bark` | Dog barking, howling | FreeSound (search "dog bark") |
| `phone_ring` | Phone ringing, ringtones | FreeSound (search "phone ring") |
| `music_tv` | Music, TV, radio | FreeSound (search "music") |
| `ambient` | Quiet room, background noise | Record ~30s of silence at home |

**Label order matters.** In the Edge Impulse UI, ensure the labels sort
alphabetically — the firmware class IDs (0–9) map to alphabetical order:
`alarm=1, ambient=9, appliance=5, baby_cry=3, dog_bark=6, doorbell=2,
music_tv=8, phone_ring=7, vehicle=4, voice=0`.

If Edge Impulse sorts differently, adjust the `CLASS_*` constants at the
top of `openhear_v2_standalone.ino` to match.

### 1.2 Build the impulse

5. **Impulse design:**
   - Add **Audio (MFCCs)** as the processing block (16kHz, 1s window).
   - Add **Classification (Keras)** as the learning block.
   - **Save impulse**.

6. **MFCC → Save parameters → Generate features**. Wait ~2 min.

7. **Classifier → Start training**. Wait ~5 min.
   Aim for >85% accuracy. If lower, add more samples per class.

8. **Deployment → Arduino library → Build**. Download the `.zip`.

9. Arduino IDE: **Sketch → Include Library → Add .ZIP Library**.

---

## Step 2 — Flash the firmware (5 minutes)

1. Open `openhear_v2_standalone.ino` in Arduino IDE.
2. Check the `#include` line matches your exported library name.
3. **Library Manager** — install **Seeed_Arduino_LSM6DS3** (for the IMU)
   in addition to the Adafruit DRV2605 library from before.
4. If you only have **one DRV2605L** (not two), set `#define DUAL_MOTOR false`
   near the top of the sketch. Spatial encoding falls back to single-motor.
5. Connect the XIAO nRF52840 Sense via USB-C.
6. **Tools → Board → XIAO nRF52840 Sense (mbed-enabled)**.
7. Click **Upload**.
8. When it finishes, the wristband plays two short taps — it's running.

---

## Step 3 — That's it

Put it on. You'll feel:

| Sound | Motor(s) | Pattern |
|---|---|---|
| Someone speaking nearby | Both | Gentle sustained buzz |
| Alarm / smoke detector | Left then Right (×3) | Urgent alternating — use seek mode |
| Doorbell | Both | Double knock tap |
| Baby crying | Right only | Rising ramp |
| Vehicle / engine | Left only | Single long pulse |
| Appliance (kettle, microwave) | Both | Short double-click |
| Dog barking | Right only | Medium pulse |
| Phone ringing | Left then Right (×2) | Ring cadence |
| Music / TV | Both | Slow soft pulse ×2 |

Ambient and silence produce nothing.

---

## Step 4 — Seek mode (finding where a sound is coming from)

When you want to locate a sound:

1. **Flick your wrist sharply upward** (a quick raise-and-stop gesture).
   A short single buzz confirms seek mode is on.
2. **Slowly rotate your body** to face different directions.
3. When the wristband detects that ambient amplitude is climbing —
   meaning you're removing your body shadow from the mic — it fires
   **two quick double-taps** on both motors: you're facing the source.
4. Seek mode runs for 5 seconds then exits automatically.

This works because an omnidirectional mic still picks up slightly more
signal once your body stops blocking the wavefront. The IMU tracks that
you're rotating rather than just moving, which reduces false triggers.

---

## Step 5 — Two-motor setup (for full spatial encoding)

The v2 assembly guide supports **two DRV2605L drivers**. To add the second:

1. Get a second **Adafruit DRV2605L STEMMA QT breakout**.
2. **Open the ADDR solder jumper** on the back — this changes its I2C
   address from 0x5A to 0x5B.
3. Daisy-chain it via a second STEMMA QT cable to the first DRV2605L's
   OUT port (or directly to the expansion board's second Grove I2C port).
4. Plug the second LRA motor into the second driver's screw terminal.

The firmware auto-detects the second driver on boot. If only one is
present, it runs single-motor mode with no config changes needed.

---

## Updating your audiogram

The intensity table in `openhear_v2_standalone.ino` is set for Lewis's
burgess_2021.json audiogram. To recalculate for a different person:

For each sound class, average the hearing loss (dB HL) across the
frequencies that class mainly occupies, then apply:
`intensity = (average_loss_dB / 100) * 180`

| Class | Main frequencies | Average these thresholds |
|---|---|---|
| voice | 500–2000 Hz | 500, 1000, 1500, 2000 Hz |
| alarm | 2000–4000 Hz | 2000, 3000, 4000 Hz |
| doorbell | 800–2000 Hz | 1000, 1500, 2000 Hz |
| baby_cry | 500–4000 Hz | 500, 1000, 2000, 4000 Hz |
| vehicle | 100–500 Hz | 125, 250, 500 Hz |
| appliance | 1000–3000 Hz | 1000, 1500, 2000, 3000 Hz |
| dog_bark | 500–1000 Hz | 500, 1000 Hz |
| phone_ring | 1000–2000 Hz | 1000, 1500, 2000 Hz |
| music_tv | 500–2000 Hz | 500, 1000, 1500, 2000 Hz |
| ambient | — | use 100 (fixed low-priority) |

Round to the nearest whole number and update `AUDIOGRAM_INTENSITY[]`.
Re-flash.

---

## Adjusting sensitivity

- **`CONFIDENCE_THRESHOLD`** (default `0.75`) — raise to `0.85` if you're
  getting false triggers; lower to `0.65` if it's missing real sounds.
- **`MIN_GAP_MS`** (default `1500`) — minimum ms between haptic fires.
- **`SEEK_GAIN_THRESHOLD`** (default `1.15`) — how much louder the sound
  needs to get as you rotate before "found it" fires. Raise if outdoor
  wind causes false positives.
- **`WRIST_FLICK_G`** (default `2.2`) — G-force needed to trigger seek mode.
  Lower to `1.8` if it's hard to trigger; raise to `2.5` if it fires during
  normal arm movement.

---

## Battery life estimate

On a 400 mAh LiPo (LP502535) with dual motors and IMU running:
**10–15 hours** typical. Seek mode adds negligible drain (IMU polling
is ~0.9mA at 52Hz). Charge overnight via USB-C.

---

*OpenHear v2 Standalone — Licence: MIT OR Apache-2.0 (firmware),
CC-BY-SA-4.0 (docs). Not a certified medical device.*
