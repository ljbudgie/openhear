# OpenHear v2 – XIAO nRF52840 carrier board outline

Licence: CERN-OHL-S-2.0.

The v2 “Premium Slim” build is designed to be **buildable with zero custom
PCBs** by using the pre-made **Seeed Studio XIAO Expansion Board Base**
(Grove + JST-PH battery) plus an off-the-shelf **Adafruit DRV2605L STEMMA QT**
breakout. That is the recommended starter path and matches the v1.5
no-solder philosophy.

This document is the **optional** open-source KiCad carrier board for
builders who want a single PCB that fits inside the slim 44 × 38 × 12 mm
case, replaces the Seeed expansion board, and exposes:

- A 14-pin **castellated socket** for the XIAO nRF52840 (drop-in).
- An **I²C breakout** (SDA / SCL / 3V3 / GND) on a 4-pin JST-SH (STEMMA QT
  compatible) for the DRV2605L module.
- A **2-pin JST-PH** for the 300–500 mAh LiPo battery.
- Two **pogo / magnetic charging pads** routed to VBUS and GND (paralleled
  with the XIAO USB-C VBUS so the onboard charger does the work).
- A **slide power switch footprint** (optional) in-line with the LiPo
  positive lead.
- A **TP solder pad** for an external antenna (left no-pop; the XIAO
  onboard ceramic antenna is the default).

No proprietary parts; all footprints come from KiCad’s default libraries or
the open-source `Seeed-KiCad-Library`.

## Mechanical outline (must match `parametric_wristband_v2.scad`)

```
+---------------------------------------+
|        OpenHear v2 carrier            |  ← 41.5 × 35.5 mm, 1.6 mm FR4
|                                       |
|   [XIAO socket, castellated 2×7]      |   pocket centred on (0, +6) mm
|                                       |
|   [STEMMA QT JST-SH 4-pin]            |
|   [LiPo JST-PH 2-pin] [SW slide]      |
|                                       |
|       o   o   ← pogo pads (VBUS, GND) |   centred on (0, −16) mm
+---------------------------------------+
```

Corner radius 3 mm. Mounting: snap-fit against the four internal posts in
the printed case (no screws). Maximum component height on the wrist side:
**3.6 mm** (the XIAO itself). Maximum height on the lid side: **5.5 mm**
(battery + LRA stack share that volume; see SCAD pockets).

## Net list (functional, vendor-agnostic)

| Net   | XIAO pin | Notes |
|-------|----------|-------|
| VBUS  | VBUS / pogo+ | 5 V from USB-C **or** magnetic dock |
| 3V3   | 3V3      | XIAO LDO output, powers DRV2605L |
| GND   | GND / pogo− | star ground at XIAO GND pad |
| SDA   | D4       | I²C to DRV2605L (and optional TCA9548A) |
| SCL   | D5       | I²C to DRV2605L (and optional TCA9548A) |
| BAT+  | BAT+     | LiPo + via slide switch |
| BAT−  | GND      | LiPo − |
| LRA+  | DRV OUT+ | from DRV2605L module, off-board JST-PH |
| LRA−  | DRV OUT− | from DRV2605L module, off-board JST-PH |

## Routing constraints

- Keep the **ceramic antenna keep-out** on the XIAO clear: no copper,
  ground pour, or large metal under the antenna tip (top edge of XIAO).
- Star-route LRA return current; do not share with I²C ground returns.
- Add a **10 µF / 6.3 V X5R** decoupling cap close to the 3V3 net and a
  **2.2 µF** on VBUS.
- Pogo pads: **3 mm gold-flash pads**, 4 mm pitch, with a 0.5 mm
  silkscreen polarity dot on the VBUS pad.

## Build options

| Variant | Board | Notes |
|---------|-------|-------|
| **A. No-solder (recommended starter)** | Seeed XIAO Expansion Base + DRV2605L STEMMA QT | No KiCad build needed. |
| **B. Slim carrier (this doc)**         | OpenHear v2 KiCad carrier                     | One PCB order from JLCPCB/PCBWay/Aisler, hand-assembled with JST connectors. |
| **C. Future rigid-flex**               | XIAO + flex-tail to 4 LRAs                    | Roadmap item; not in v2 release. |

Build A and B share the **same firmware, same case, same BOM (minus the
expansion board row)** and produce the same daily-wear device.

## ERC/DRC + manufacturing

- KiCad **v8** project files should live next to this document
  (`xiao_carrier_v2.kicad_pro/.kicad_sch/.kicad_pcb`) once contributed.
- Run **ERC** and **DRC** before ordering: minimum track/space
  **0.15/0.15 mm**, minimum drill **0.20 mm**, finish **ENIG** for skin
  proximity (no exposed nickel).
- Cover all skin-facing copper with solder mask + the printed enclosure.
- Order: 1.6 mm FR-4, 2-layer, ENIG, lead-free HASL acceptable for
  research builds.
