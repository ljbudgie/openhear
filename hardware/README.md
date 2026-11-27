# hardware/ — From Audiogram to Wearable

This module bridges OpenHear's software pipeline to physical wearable hardware.

The intended hardware path is a **haptic wristband** for environmental sound awareness: recognised sound classes are delivered as short, distinct vibration patterns, weighted by the wearer's own audiogram. OpenHear is not a hearing aid, not a certified medical device, and not a replacement for clinical care. It does not amplify sound as its intended use. The only intended-purpose statement is in [`docs/INTENDED_PURPOSE.md`](../docs/INTENDED_PURPOSE.md); also see [`START_HERE.md`](../START_HERE.md).

The wristband is **in development**. Classification on the recommended v2 path runs on a companion device (phone or laptop). The wristband is the haptic endpoint.

---

## Wristband (intended path)

| Build | Folder | Status |
|--------|--------|--------|
| **Wristband v2 (slim, XIAO nRF52840)** | [`wristband/v2-xiao-nrf52840/`](wristband/v2-xiao-nrf52840/) | **Recommended for daily wear.** Off-the-shelf modules; no custom PCB needed for the starter kit. |
| Wristband v1.5 (no-solder, ESP32-S3 / RP2040) | [`wristband/v1.5-no-solder/`](wristband/v1.5-no-solder/) | Beginner modular path: no soldering, slightly larger than compact v1. |
| Wristband v1 (compact, soldered) | [`wristband/`](wristband/) | Legacy, supported. Advanced / smallest soldered option. |
| micro:bit v2 prototype | [`../wristband/`](../wristband/) and [`../HARDWARE.md`](../HARDWARE.md) | Earlier prototype path, still documented. |

All of these use the same 3-byte BLE haptic packet. Traffic patterns, where present, are for awareness only and are **not a safety feature**.

Start with the [v2 README](wristband/v2-xiao-nrf52840/README.md) and [assembly guide](wristband/v2-xiao-nrf52840/assembly_v2.md). Follow the safety checklist in those guides before wearing a prototype.

---

## Exploratory research (not intended use)

This tree also contains **exploratory amplification and in-ear research**: Tympan-based DSP experiments, behind-the-ear and in-the-ear shell notes, MPO limiter circuits, and related bills of materials. Those documents and tools are research material. They are **not** the present intended purpose, **not** a hearing aid or medical device, and **not** a Personal Sound Amplification Product (PSAP) offered as a supported build.

They are left in the repository so the research is inspectable. Do not treat them as a product path or as a substitute for clinical care. Anything that puts sound into the ear can cause harm; read the [safety module](safety/README.md) before opening or building any of that work.

The folders below belong to that exploratory research (cost figures are those already listed in the older tier notes):

### Research tiers (Tympan / in-ear — not intended use)

- **Explorer (~£300)** — A Tympan board connected to standard headphones, used to experiment with audiogram-driven DSP. No soldering or 3D printing.
- **Builder (~£450)** — A Tympan board with behind-the-ear earpieces, custom-moulded tips, and an MPO limiter circuit. Research only.
- **Sovereign (~£550)** — Notes for a fully custom printed in-ear or BTE shell and calibration with a measurement microphone. Research only.

### Sub-modules

| Module | Description |
|--------|-------------|
| [wristband/](wristband/README.md) | **Intended path.** Haptic wristband assets, including the recommended v2 XIAO build |
| [tympan/](tympan/README.md) | Exploratory: Tympan integration, audiogram-to-Arduino bridge, sketch generation |
| [shell/](shell/README.md) | Exploratory: 3D printing notes for custom ear moulds |
| [ite-shells/](ite-shells/README.md) | Exploratory: in-the-ear shell materials and build workflow |
| [safety/](safety/README.md) | Safety notes for the exploratory in-ear work (MPO limiters, calibration, risk register). Read this before touching that research. |
| [assembly/](assembly/README.md) | Exploratory: step-by-step notes for the Tympan / in-ear research tiers |
| [sovereign_device/](sovereign_device/) | Exploratory: local audiogram → firmware + manifest pipeline and component database |
| [BOM.md](BOM.md) | Exploratory bill of materials for the Tympan / in-ear research tiers |
| [ROADMAP.md](ROADMAP.md) | Hardware development notes, including items that go beyond the present intended purpose |

---

## This is not a medical device

OpenHear hardware, including both the wristband path and the exploratory in-ear research, is experimental. It is not a regulated medical device, not a hearing aid, and not a PSAP. It has not been approved by any regulatory body. It is not sold, prescribed, or fitted by a clinician.

If you work with the exploratory in-ear documents, the safety module in this tree is written for that research (including hardware MPO limiting). In doubt, do not build, and do not put sound into an ear.

---

## Getting started

1. Read [`docs/INTENDED_PURPOSE.md`](../docs/INTENDED_PURPOSE.md) and [`START_HERE.md`](../START_HERE.md).
2. For the intended haptic path, open the [v2 wristband README](wristband/v2-xiao-nrf52840/README.md) and follow its assembly and safety checklist.
3. Only if you are reading the exploratory in-ear research: read the [safety module](safety/README.md) first, then the documents in the table above.
