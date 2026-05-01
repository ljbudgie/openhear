# OpenHear wristband prototype hardware assets

This directory keeps the original prototype firmware path for compatibility.

## Canonical v1.0.0 docs and firmware

- Release-facing setup guide: [`../../wristband/README.md`](../../wristband/README.md)
- Canonical firmware file to flash: [`../../wristband/openhear_firmware.py`](../../wristband/openhear_firmware.py)
- Legacy firmware mirror retained here: [`firmware.py`](firmware.py)

## Wiring and Windows support

- Full wiring notes: [`../../HARDWARE.md`](../../HARDWARE.md)
- Flashing steps: [`../../HARDWARE.md#firmware-flashing-windows`](../../HARDWARE.md#firmware-flashing-windows)
- BLE troubleshooting: [`../../HARDWARE.md#windows-ble-debugging-checklist`](../../HARDWARE.md#windows-ble-debugging-checklist)


## Aids-free wristband v1 DIY prototype assets

The v1 directory assets move the project toward `docs/AIDS_FREE_ARCHITECTURE.md`:
wrist-only capture, local processing, skin-as-transducer output, and no cloud or
ear-worn dependency.

```text
hardware/wristband/
├── BOM.csv
├── assembly_v1.md
├── power_budget_v1.md
├── cad/
│   ├── generate_stl.sh
│   └── parametric_wristband_v1.scad
├── firmware/
│   ├── haptic_mapper.py
│   └── openhear_firmware_v1.py
└── kicad/
    ├── gerber_notes.md
    ├── wristband_v1.kicad_pcb
    ├── wristband_v1.kicad_pro
    └── wristband_v1.kicad_sch
```

Start with the 24-actuator configuration unless you already have a current-limited
bench supply, thermal logging, and dense flex-harness experience. The 64- and
128-actuator variants are research targets, not first wearable builds.
