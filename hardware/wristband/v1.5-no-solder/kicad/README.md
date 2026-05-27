# KiCad and No-Custom-PCB Path for v1.5

v1.5 is designed to work **without any custom PCB**. The recommended beginner build uses off-the-shelf dev boards, STEMMA QT/Qwiic JST-SH cables, DRV2605L modules, TCA9548A mux modules, pre-wired actuators, and a protected battery cartridge.

The KiCad files in this folder document the optional interconnect board for builders who want a cleaner internal layout later. It is intentionally simple: no fine-pitch MCU, no solder-required first build, and no hidden hearing path.

## Beginner no-PCB wiring

```text
USB-C dev board
   │  JST-SH / STEMMA QT: 3V3, GND, SDA, SCL
   ▼
TCA9548A I2C mux module
   ├─ branch 0 → DRV2605L bank 0 → A00-A02 via pre-wired JST adapters
   ├─ branch 1 → DRV2605L bank 1 → A03-A05
   ├─ branch 2 → DRV2605L bank 2 → A06-A08
   ├─ branch 3 → DRV2605L bank 3 → A09-A11
   ├─ branch 4 → DRV2605L bank 4 → A12-A14
   ├─ branch 5 → DRV2605L bank 5 → A15-A17
   ├─ branch 6 → DRV2605L bank 6 → A18-A20
   └─ branch 7 → DRV2605L bank 7 → A21-A23
```

For 64 actuators, duplicate the mux/driver-bay pattern and label rows `R0-R3`.

## Optional interconnect board intent

- Main interconnect board routes magnetic pogo/JST connectors only.
- Optional haptic driver board repeats DRV2605L footprints or module headers.
- Battery cartridge remains removable and protected.
- The PCB is not required for the weekend starter build.

## Files

- `openhear_v1.5_no_solder.kicad_pro`: KiCad 8 project placeholder.
- `openhear_v1.5_no_solder.kicad_sch`: schematic skeleton showing connector-level intent.
- `openhear_v1.5_no_solder.kicad_pcb`: small connector-router board outline skeleton.

Before fabricating any PCB, review current KiCad syntax, connector footprints, battery safety, and creepage/clearance against the actual modules you bought.
