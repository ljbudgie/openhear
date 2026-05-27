# OpenHear Wristband v2 – “Premium Slim Upgrade” (XIAO nRF52840)

Licences: hardware **CERN-OHL-S-2.0**, code **MIT OR Apache-2.0**, docs **CC-BY-SA-4.0**.

> Daily-wear, Apple-Watch-Ultra / Whoop-4.0-style aids-free wristband on
> the **Seeed Studio XIAO nRF52840 (Sense)** – fully open-source,
> sovereign, local-first, individually buildable, and 100 % compatible
> with the existing OpenHear classifier, audiogram JSON, and 3-byte BLE
> packet contract.

## Folder layout

```text
hardware/wristband/v2-xiao-nrf52840/
├── README.md                          ← you are here
├── parametric_wristband_v2.scad       ← rectangular slim case, lid, strap
├── BOM_v2.csv                         ← XIAO-based bill of materials
├── assembly_v2.md                     ← print + no-solder assembly guide
├── print_pack/                        ← drop-in pack for 3D-print services
│   ├── PRINT_ME.md                    ←   one-page print-me card
│   ├── README.md                      ←   pack overview
│   └── stl/                           ←   pre-oriented case + lid STLs
├── firmware/
│   ├── openhear_v2_xiao_nrf52840.ino  ← Arduino + NimBLE, DRV2605L, sleep
│   └── README.md                      ← toolchain, GATT contract, Zephyr alt
└── kicad/
    └── xiao_carrier_v2.md             ← optional open carrier-board notes
```

The v1 (`hardware/wristband/cad/parametric_wristband_v1.scad`,
`hardware/wristband/kicad/`) and v1.5-no-solder
(`hardware/wristband/v1.5-no-solder/`) builds are **kept as legacy
options** alongside v2. micro:bit v2, ESP32-S3, and RP2040 paths are
unchanged.

## Why XIAO nRF52840 is the right v2 foundation

The Seeed XIAO nRF52840 (Sense) is **the closest open-source hardware
not yet in the repo** and the perfect minimal upgrade from the micro:bit v2:

| | micro:bit v2 (v1)        | XIAO nRF52840 Sense (v2)             |
|-|--------------------------|--------------------------------------|
| SoC          | Nordic nRF52833 | **Nordic nRF52840** – direct evolution |
| Footprint    | 51 × 42 mm board | **20 × 17.5 mm** module – fits a 44 × 38 mm wrist case |
| BLE          | BLE 5.0          | **BLE 5.x**, NimBLE / Bluefruit / Zephyr-ready |
| Charging     | external          | **onboard LiPo charger** (BQ25101) |
| Mic / IMU    | external          | **onboard PDM mic + IMU** on Sense variant |
| Power        | good              | **excellent** low-power sleep, ideal for all-day wear |
| Lock-in      | none              | **none** – castellated pads, open BSP |

It is a **drop-in evolution** from the nRF52833 in the micro:bit, so the
existing radio and SoftDevice-free Nordic experience carries straight
over. There is nothing in the v2 design that requires a proprietary
binary, cloud service, or vendor-locked tool.

## What v2 delivers

1. **Slim daily-wear form factor** – rectangular 44 × 38 mm case,
   ≤ 12 mm total thickness, matte-black/titanium-look PETG/PA12-CF lid,
   curved wrist underside, 2–3 mm fillets, IP-ish seal-lip lid.
2. **Better haptics** – DRV2605L driving 2–4 LRA coin actuators with an
   open-source ROM-effect waveform per YAMNet class, sandwiched between
   the XIAO and lid for tight wrist coupling and good heat spread.
3. **Lower power** – nRF52840 in event-driven sleep (`__WFE`/`__SEV`),
   DRV2605 in standby after every effect, BLE TX capped at −12 dBm.
   Targets all-day wear on a 300–500 mAh LiPo (e.g. LP502535).
4. **Zero lock-in** – Arduino + **NimBLE** is the default path;
   **Bluefruit** and **Zephyr** alternatives are documented and use the
   same characteristic UUIDs and the same 3-byte packet.
5. **No-solder buildable** – the recommended kit pairs the XIAO with the
   Seeed Expansion Board Base + Adafruit DRV2605L STEMMA QT + pre-wired
   LRA + Grove cable + LiPo. Drop in any community-parametric
   Apple-Watch-style TPU band from Printables / MakerWorld via the
   standard 20–22 mm quick-release lugs.
6. **Same software contract** – identical 3-byte BLE packet
   `[sound_class_id, intensity, pattern_id]`, identical YAMNet 7-class
   head, identical audiogram JSON, identical `V0_COMPAT_PATTERN = 240`
   shim for legacy v0 micro:bit packets.

## Compatibility matrix

| Build                  | Folder                                      | Status   |
|------------------------|---------------------------------------------|----------|
| Wristband v1 (compact, soldered)             | `hardware/wristband/`                          | Legacy, supported |
| Wristband v1.5 (no-solder, ESP32-S3 / RP2040)| `hardware/wristband/v1.5-no-solder/`           | Legacy, supported |
| **Wristband v2 (slim, XIAO nRF52840)**       | `hardware/wristband/v2-xiao-nrf52840/`         | **New, recommended for daily wear** |

All three speak the same 3-byte BLE packet, so a phone or companion
edge device can drive any of them without code changes.

## Quick start

1. Open `parametric_wristband_v2.scad` in OpenSCAD ≥ 2021.01, tweak the
   parameters at the top (default values are tuned for a 165–185 mm
   wrist), and export the case + lid STLs. **Or skip this step entirely
   and use the ready-to-print package in [`print_pack/`](print_pack/) —
   pre-oriented STLs plus a one-page `PRINT_ME.md` for any FDM print
   service.**
2. Order the parts in `BOM_v2.csv` (no-solder kit is ~£40–£60).
3. Follow `assembly_v2.md`.
4. Flash `firmware/openhear_v2_xiao_nrf52840.ino` with the Arduino IDE.
5. Pair from the existing OpenHear companion app – nothing else changes.

See `assembly_v2.md` for the full safety checklist (unchanged from v1).
