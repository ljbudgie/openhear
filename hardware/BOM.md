# Bill of Materials

All prices in GBP (£). Prices are approximate and may vary by supplier and region. See [sourcing notes](#sourcing-notes) at the bottom for international alternatives.

---

## Tier 1: Explorer (~£300)

Everything you need to hear your audiogram-tuned audio through headphones. No soldering required.

| Component | Part | Supplier | Approx Cost | Notes |
|-----------|------|----------|-------------|-------|
| Dev board | [Tympan Rev F](https://shop.tympan.org/) | shop.tympan.org | £250 | Open-source hearing aid dev board. Teensy 4.1 based, 600 MHz ARM Cortex-M7. [Datasheet](https://github.com/Tympan/Docs/wiki) |
| Headphones | Any wired over-ear headphones, 32Ω impedance | Amazon / local | £30 | 3.5mm jack. Over-ear recommended for comfort during testing. Avoid noise-cancelling models — they add latency |
| Microphone | 3.5mm lavalier / lapel microphone | Amazon / local | £10 | Omnidirectional. Clip to collar for voice pickup during testing |
| Cable | USB-C to USB-A cable | Amazon / local | £5 | For programming the Tympan via Arduino IDE. At least 1m length recommended |
| | | | **~£295** | |

---

## Tier 2: Builder (~£450)

Adds BTE earpieces, balanced armature receivers, custom moulds, and the mandatory MPO limiter circuit. This tier produces a wearable hearing aid.

| Component | Part | Supplier | Approx Cost | Notes |
|-----------|------|----------|-------------|-------|
| *All Tier 1 components above* | | | £295 | Headphones become optional once earpieces are built |
| Earpiece kit | [Tympan Earpiece Kit](https://shop.tympan.org/) | shop.tympan.org | £80 | Includes L+R BTE housings with dual MEMS microphones. [Docs](https://github.com/Tympan/Docs/wiki/Tympan-Earpieces) |
| Receivers | Knowles ED-series or WBFK-series balanced armature | [DigiKey](https://www.digikey.co.uk/) / [Mouser](https://www.mouser.co.uk/) | £20 | ED-29689 for mild-moderate loss. WBFK-30019 for severe-profound. See [receiver selection](#receiver-selection) |
| Ear moulds | 3D printed custom moulds | Self-made (resin or FDM) | £30 | Material cost only. See [shell/ module](shell/README.md) for printing guide |
| Impression kit | Two-part medical silicone ear impression kit | Amazon | £15 | Food-grade or medical-grade silicone. Includes mixing cups and syringe. See [shell/ safety warnings](shell/README.md#taking-ear-impressions) |
| Battery | 3.7V LiPo 500mAh | Amazon / Pimoroni | £10 | JST-PH 2.0mm connector for Tympan. [Datasheet](https://www.olimex.com/Products/Power/BATTERY-LIPO500mAh/) — check connector polarity before connecting |
| Misc | Wire (30 AWG silicone), JST connectors, heat shrink | Amazon / local | £15 | Silicone wire recommended for flexibility. Include spare connectors |
| | | | **~£465** | Subtract £30 if headphones not needed |

---

## Tier 3: Sovereign (~£550)

Adds precision printing capability, calibration equipment, and hardware limiter components for a fully self-contained build.

| Component | Part | Supplier | Approx Cost | Notes |
|-----------|------|----------|-------------|-------|
| *All Tier 2 components above* | | | £435 | Without headphones |
| 3D printer | [Elegoo Mars 4](https://www.elegoo.com/products/elegoo-mars-4) | Elegoo / Amazon | £200 | MSLA resin printer. 0.05mm layer height for smooth ear moulds. Alternative: any resin printer with ≤0.05mm resolution |
| Resin | Biocompatible resin (Class I) | Elegoo / FormLabs / Amazon | £40 | Must be rated for skin contact. [Elegoo Bio Resin datasheet](https://www.elegoo.com/products/elegoo-bio-photopolymer-resin). UV cure fully before skin contact |
| Calibration mic | [Dayton Audio iMM-6](https://www.daytonaudio.com/product/1117/imm-6-idevice-calibrated-measurement-microphone) | Parts Express / Amazon | £20 | Calibrated measurement microphone. Comes with individual calibration file. Essential for MPO verification |
| MPO limiter | Zener diodes, resistors, perfboard | DigiKey / Mouser / local | £5 | See [safety module](safety/README.md) for circuit design and component values |
| | | | **~£700** | Or **~£500** if you already own a resin printer |

> **Note:** Tier 3 cost includes a resin printer, which is a one-time purchase. If you already own one, the marginal cost is around £500 total for a complete binaural system. Many makerspaces and libraries have resin printers available for free or low cost.

---

## Receiver Selection

The balanced armature receiver converts electrical signal to sound inside the ear canal. Choosing the right one matters.

| Hearing Loss | Recommended Receiver | Max Output | Notes |
|-------------|---------------------|------------|-------|
| Mild (26–40 dB) | Knowles ED-29689 | ~108 dB SPL | Lower power, longer battery life. [Datasheet](https://www.knowles.com/docs/default-source/default-document-library/ed-29689.pdf) |
| Moderate (41–55 dB) | Knowles ED-29689 | ~108 dB SPL | Same receiver, higher gain in DSP |
| Moderately-severe (56–70 dB) | Knowles WBFK-30019 | ~114 dB SPL | Higher output capability. [Datasheet](https://www.knowles.com/docs/default-source/default-document-library/wbfk-30019.pdf) |
| Severe (71–90 dB) | Knowles WBFK-30019 | ~114 dB SPL | Use with hardware MPO limiter (mandatory) |
| Profound (91+ dB) | Knowles WBFK-30095 | ~120 dB SPL | Maximum output. Hardware MPO limiter is **critical**. [Datasheet](https://www.knowles.com/docs/default-source/default-document-library/wbfk-30095.pdf) |

**Critical components (do not substitute):**
- Tympan Rev F — the entire software pipeline depends on this board
- Knowles balanced armature receivers — output characteristics are calibrated to these specific models
- Biocompatible resin for anything that contacts skin or ear canal

**Substitutable components:**
- Headphones (any wired 32Ω over-ear)
- Lavalier microphone (any 3.5mm omnidirectional)
- USB cable (any USB-C cable)
- Wire and connectors (any 30 AWG silicone wire)
- Soldering iron (any temperature-controlled iron)
- 3D printer (any resin printer with ≤0.05mm layer resolution)

---

## Sourcing Notes

### UK Suppliers (Primary)
- **Tympan:** [shop.tympan.org](https://shop.tympan.org/) — ships internationally
- **Knowles receivers:** [DigiKey UK](https://www.digikey.co.uk/), [Mouser UK](https://www.mouser.co.uk/), [Farnell](https://uk.farnell.com/)
- **General electronics:** [Pimoroni](https://shop.pimoroni.com/), [The Pi Hut](https://thepihut.com/)

### US Suppliers
- **Knowles receivers:** [DigiKey](https://www.digikey.com/), [Mouser](https://www.mouser.com/)
- **Calibration mic:** [Parts Express](https://www.parts-express.com/)
- **3D printing supplies:** [MatterHackers](https://www.matterhackers.com/)

### EU Suppliers
- **Knowles receivers:** [DigiKey EU](https://www.digikey.eu/), [Mouser EU](https://www.mouser.eu/)
- **Electronics:** [Reichelt](https://www.reichelt.de/), [Conrad](https://www.conrad.com/)

### Rest of World
- **Tympan ships internationally.** Check customs and import duties for your country.
- **Knowles receivers** are available from DigiKey and Mouser in most countries.
- **AliExpress** carries compatible LiPo batteries, wire, and connectors at lower prices. Verify specifications before purchasing — counterfeit components are common.

---

## Datasheet Links (Quick Reference)

| Component | Datasheet |
|-----------|-----------|
| Tympan Rev F | [Tympan Wiki](https://github.com/Tympan/Docs/wiki) |
| Teensy 4.1 (Tympan CPU) | [PJRC Teensy 4.1](https://www.pjrc.com/store/teensy41.html) |
| Knowles ED-29689 | [ED-29689 PDF](https://www.knowles.com/docs/default-source/default-document-library/ed-29689.pdf) |
| Knowles WBFK-30019 | [WBFK-30019 PDF](https://www.knowles.com/docs/default-source/default-document-library/wbfk-30019.pdf) |
| Knowles WBFK-30095 | [WBFK-30095 PDF](https://www.knowles.com/docs/default-source/default-document-library/wbfk-30095.pdf) |
| Dayton Audio iMM-6 | [iMM-6 Product Page](https://www.daytonaudio.com/product/1117/imm-6-idevice-calibrated-measurement-microphone) |
