# OpenHear wristband prototype hardware assets

This directory holds hardware assets for the OpenHear haptic wristband. The wristband is **in development**. Its intended use is environmental sound awareness through vibration, not amplification, and it is not a hearing aid or medical device. See [`docs/INTENDED_PURPOSE.md`](../../docs/INTENDED_PURPOSE.md).

Classification on the recommended v2 path runs on a companion device (phone or laptop). The wristband is the haptic endpoint. An optional standalone sketch exists; it is experimental and is not the shipped classifier.

## Recommended path: Wristband v2 (XIAO nRF52840)

**Recommended for daily wear:** [`v2-xiao-nrf52840/`](v2-xiao-nrf52840/). Slim case, Seeed Studio XIAO nRF52840 Sense, Seeed Expansion Board Base, Adafruit DRV2605L, and pre-wired LRAs. The starter kit is no-solder and needs no custom PCB. Firmware, enclosure files (OpenSCAD and STLs) and a bill of materials are in that folder.

## v1.5 No-Solder Modular Edition

[`v1.5-no-solder/`](v1.5-no-solder/) is the beginner modular build on ESP32-S3 or RP2040 dev boards, with magnetic pogo or JST connectors, snap-fit printed bays, USB flashing, and pre-wired actuators. It uses no soldering, crimping, wire stripping, or special electronics tools. It is slightly larger and about 10–15% more expensive than compact v1.

v1.5 remains a supported beginner path. It is not the recommended daily-wear path; that is v2, above.

## Compact v1 and micro:bit prototype

Compact v1 (this folder’s CAD, KiCad notes, and firmware) remains the advanced / smallest soldered option for experienced builders. The 64- and 128-actuator variants are research targets, not first wearable builds. Start with the 24-actuator configuration unless you already have a current-limited bench supply, thermal logging, and dense flex-harness experience.

The earlier BBC micro:bit v2 prototype is documented separately:

- Release-facing setup guide: [`../../wristband/README.md`](../../wristband/README.md)
- Canonical firmware file to flash: [`../../wristband/openhear_firmware.py`](../../wristband/openhear_firmware.py)
- Legacy firmware mirror retained here: [`firmware.py`](firmware.py)
- Full wiring notes: [`../../HARDWARE.md`](../../HARDWARE.md)
- Flashing steps: [`../../HARDWARE.md#firmware-flashing-windows`](../../HARDWARE.md#firmware-flashing-windows)
- BLE troubleshooting: [`../../HARDWARE.md#windows-ble-debugging-checklist`](../../HARDWARE.md#windows-ble-debugging-checklist)

## Folder layout

```text
hardware/wristband/
├── README.md                          ← you are here
├── BOM.csv
├── assembly_v1.md
├── power_budget_v1.md
├── cad/
│   ├── generate_stl.sh
│   └── parametric_wristband_v1.scad
├── firmware/
│   ├── haptic_mapper.py
│   └── openhear_firmware_v1.py
├── kicad/
│   ├── gerber_notes.md
│   ├── wristband_v1.kicad_pcb
│   ├── wristband_v1.kicad_pro
│   └── wristband_v1.kicad_sch
├── v1.5-no-solder/                    ← beginner modular ESP32-S3 / RP2040 path
└── v2-xiao-nrf52840/                  ← recommended daily-wear path (XIAO nRF52840)
```

The v1 assets also relate to the longer-term notes in `docs/AIDS_FREE_ARCHITECTURE.md`. Those notes are exploratory and are not the present intended purpose.
