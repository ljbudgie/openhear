# OpenHear v1.5 No-Solder Modular Edition

**Print it. Plug it. Flash it. Wear it.**

This is the beginner-friendly OpenHear wristband path: a true **Modular Lego** build that uses 3D-printed snap-fit parts, plug-in modules, magnetic pogo pins or JST connectors, and USB flashing. No soldering iron. No crimping. No wire stripping. No bench tools beyond a 3D printer and a USB cable.

The original compact v1 hardware in [`../`](../) remains the advanced/smallest option for experienced electronics builders. v1.5 is deliberately a little larger and about 10-15% more expensive so a complete beginner can build a working aids-free haptic wristband in a weekend.

## One-page quickstart

1. **Buy the plug-and-play parts** from [`BOM.csv`](BOM.csv).
   - Easiest MCU: Seeed Studio XIAO ESP32S3 Sense or Adafruit Feather ESP32-S3.
   - Easiest haptic driver chain: Adafruit TCA9548A + Adafruit DRV2605L STEMMA QT modules.
   - Easiest actuators: pre-wired 10 mm LRA coin motors with 2-pin JST leads.
   - Easiest power: protected LiPo with JST-PH plus USB-C LiPo charger module.
2. **Print the enclosure** from [`cad/parametric_modular_wristband_v1.5.scad`](cad/parametric_modular_wristband_v1.5.scad).
3. **Click in modules**: MCU bay, haptic-driver bay, battery cartridge, mic bay, and actuator lattice.
4. **Plug cables by label**: A00-A23 for the starter build, A00-A63 for the dense research build.
5. **Flash by USB-C** using the instructions in [`firmware_notes.md`](firmware_notes.md).
6. **Run the first haptic test at low intensity** and start the local-only Bark-band/audiogram mapper.

## Folder structure

```text
hardware/wristband/v1.5-no-solder/
├── README.md
├── BOM.csv
├── assembly_v1.5_no_solder.md
├── firmware_notes.md
├── cad/
│   ├── export_stls.sh
│   └── parametric_modular_wristband_v1.5.scad
└── kicad/
    ├── README.md
    ├── openhear_v1.5_no_solder.kicad_pcb
    ├── openhear_v1.5_no_solder.kicad_pro
    └── openhear_v1.5_no_solder.kicad_sch
```

## Shopping list with direct links

Use equivalent stocked parts where local distributors are easier. Prefer official shops for first builds.

- Seeed XIAO ESP32S3 Sense: https://www.seeedstudio.com/XIAO-ESP32S3-Sense-p-5639.html
- Adafruit Feather ESP32-S3: https://www.adafruit.com/search?q=Feather%20ESP32-S3
- Adafruit TCA9548A STEMMA QT mux: https://www.adafruit.com/product/5626
- Adafruit DRV2605L haptic controller: https://www.adafruit.com/product/2305
- STEMMA QT / Qwiic JST-SH cables: https://www.adafruit.com/category/1005
- Protected LiPo batteries with JST-PH: https://www.adafruit.com/category/574
- USB-C LiPo charger modules: https://www.adafruit.com/search?q=usb-c%20lipo%20charger
- Pre-wired LRA coin motors: Precision Microdrives, Jinlong, or vetted JST-lead AliExpress listings.
- Magnetic pogo connectors: Adafruit magnetic pogo products or keyed 2.54 mm magnetic pogo pairs from reputable sellers.

## Print settings

### FDM beginner path

- Hard shell: PETG, 0.16 mm layers, 3-4 perimeters, 35% gyroid infill.
- Strap/liner: TPU 85A-95A, 0.20 mm layers, 3 perimeters, 20-30% gyroid infill.
- Tolerance: start with `snap_fit_tolerance = 0.35`; raise to 0.50 if parts are tight.
- Orientation: print the main body open side up; print the actuator lattice flat.

### Resin high-detail path

- Resin: ISO 10993 biocompatible surgical-guide resin where possible.
- Layer height: 0.05 mm.
- Wash/cure: follow vendor instructions exactly; uncured resin must never touch skin.
- Seal: if the resin is not certified for skin contact, seal all skin-facing surfaces with cured medical-grade silicone.

## First flash: USB only

- Plug the dev board into your computer with USB-C.
- Install MicroPython/CircuitPython or the board vendor's Arduino/ESP-IDF image using the vendor web flasher.
- Copy or adapt the existing v1 reference firmware from [`../firmware/openhear_firmware_v1.py`](../firmware/openhear_firmware_v1.py).
- Keep BLE/cloud features off for first tests. OpenHear's hearing path is local-only and sovereign.

## Architecture links

- Aids-free north star: [`../../../docs/AIDS_FREE_ARCHITECTURE.md`](../../../docs/AIDS_FREE_ARCHITECTURE.md)
- Burgess Principle: [`../../../docs/BURGESS_PRINCIPLE.md`](../../../docs/BURGESS_PRINCIPLE.md)
- v1 advanced compact hardware: [`../README.md`](../README.md)
- v1 haptic mapper: [`../firmware/haptic_mapper.py`](../firmware/haptic_mapper.py)

## Trade-offs

- **Larger** than compact v1 because every module needs a finger-friendly bay and connector clearance.
- **10-15% higher cost** because pre-crimped cables, breakouts, pogo pins, and magnets replace hand wiring.
- **Excellent for beginners** because failure points are visible, swappable, and reversible.
- **Same OpenHear goal**: 24 Bark-band + audiogram haptic mapping, sub-10 ms starter latency target, local-only operation, and no ear-worn device.
