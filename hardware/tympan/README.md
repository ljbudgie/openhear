# tympan/ — Tympan Integration

This module connects OpenHear's audiogram-driven software pipeline to the [Tympan](https://tympan.org/) open-source hearing aid development board.

---

## Why Tympan?

The Tympan is the only open-source hearing aid hardware platform with validated clinical performance. Here's why OpenHear builds on it:

- **Open source.** Hardware schematics, firmware, and DSP algorithms are all publicly available under open licences. No black boxes.
- **Clinical validation.** Developed with NIH (National Institutes of Health) funding. The WDRC (Wide Dynamic Range Compression) algorithms have been tested in clinical settings.
- **Active community.** Forum, GitHub issues, and a development team that responds. You are not building alone.
- **Programmable via Arduino IDE.** If you can upload a sketch, you can program a hearing aid. No proprietary toolchain required.
- **Low latency.** Under 3ms input-to-output latency. You will not hear a delay — this is critical for a natural listening experience.
- **High sample rate.** Supports up to 96 kHz sample rate for full-bandwidth audio processing.
- **Hardware:** Teensy 4.1 based, 600 MHz ARM Cortex-M7 processor. More than enough power for real-time multi-band compression, noise reduction, and feedback cancellation simultaneously.
- **Earpiece design.** Tympan has an open-source BTE-RIC (Behind-The-Ear, Receiver-In-Canal) earpiece design with dual MEMS microphones.
- **Arduino library.** Includes WDRC, noise reduction, feedback cancellation, and frequency shifting algorithms ready to use.

### Platform Status

- **Rev F** is the current production board. This is what OpenHear targets.
- **Rev G** is in development. OpenHear will support it when it ships.

---

## Data Flow: Audiogram to Hearing Aid

```
┌──────────────────┐
│  Audiogram JSON   │  Your hearing test data (openhear-audiogram-v1 format)
│  (.json file)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  audiogram.loader │  Python: load_audiogram(), get_thresholds(), get_pta()
│  audiogram.export │  Python: get_gain_profile(), to_dsp_config()
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│  audiogram_to_tympan.py  │  Python: reads gain profile + DSP config,
│  (this module)           │  generates a complete Arduino .ino sketch
└────────┬─────────────────┘
         │
         ▼
┌──────────────────┐
│  Arduino IDE      │  Upload the generated .ino sketch to Tympan
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Tympan Rev F     │  Real-time audio processing tuned to YOUR audiogram
│  (on your ear)    │  WDRC + noise reduction + feedback cancellation
└──────────────────┘
```

### Step by Step

1. **Start with your audiogram.** You need a hearing test in `openhear-audiogram-v1` JSON format. See [`audiogram/data/FORMAT.md`](../../audiogram/data/FORMAT.md) for the format specification and [`audiogram/data/burgess_2021.json`](../../audiogram/data/burgess_2021.json) for a real example.

2. **Generate a Tympan sketch.** Run the bridge script:

   ```bash
   # For one ear (right ear by default):
   python -m hardware.tympan.audiogram_to_tympan audiogram/data/burgess_2021.json output.ino

   # For binaural (both ears):
   python -m hardware.tympan.audiogram_to_tympan audiogram/data/burgess_2021.json output.ino --binaural
   ```

   This reads your audiogram, computes gain profiles and DSP parameters using OpenHear's audiogram module, and writes a complete Arduino sketch file.

3. **Open in Arduino IDE.** Open the generated `.ino` file. Install the [Tympan Library](https://github.com/Tympan/Tympan_Library) via Arduino Library Manager if you haven't already.

4. **Upload to Tympan.** Connect your Tympan via USB, select the Teensy 4.1 board, and upload. The sketch includes a startup self-test that verifies the MPO limiter is active.

5. **Fine-tune via Tympan Remote App.** The generated sketch enables Bluetooth control. Use the [Tympan Remote App](https://play.google.com/store/apps/details?id=com.creare.tympanRemote) to adjust gain, compression, and noise reduction in real time.

---

## Files in This Module

| File | Description |
|------|-------------|
| `audiogram_to_tympan.py` | Python bridge: reads audiogram JSON, generates Arduino .ino sketch |
| `templates/basic_openhear.ino` | Arduino template with placeholder values filled by the bridge script |

---

## Tympan Resources

- **Website:** [tympan.org](https://tympan.org/)
- **Shop:** [shop.tympan.org](https://shop.tympan.org/)
- **GitHub (hardware):** [github.com/Tympan/Tympan_Rev_F](https://github.com/Tympan/Tympan_Rev_F)
- **GitHub (library):** [github.com/Tympan/Tympan_Library](https://github.com/Tympan/Tympan_Library)
- **Documentation wiki:** [github.com/Tympan/Docs/wiki](https://github.com/Tympan/Docs/wiki)
- **Forum:** [forum.tympan.org](https://forum.tympan.org/)
- **Arduino library install:** Search "Tympan" in Arduino IDE Library Manager, or clone from GitHub

---

## Tympan Arduino Library: Key Algorithms

The Tympan Library provides these DSP algorithms out of the box. The generated sketch uses all of them:

| Algorithm | What It Does | Why It Matters |
|-----------|-------------|----------------|
| **WDRC** (Wide Dynamic Range Compression) | Makes quiet sounds louder and loud sounds quieter, per frequency band | Core hearing aid function. Matches amplification to your hearing loss at each frequency |
| **Noise Reduction** | Reduces steady-state background noise (fans, traffic, hum) | Improves speech clarity in noisy environments |
| **Feedback Cancellation** | Detects and suppresses acoustic feedback (whistling) | Prevents the high-pitched squeal that occurs when amplified sound leaks from the ear canal back to the microphone |
| **Frequency Shifting** | Shifts high frequencies down to ranges with better hearing | Useful for severe high-frequency loss where amplification alone is not enough |
