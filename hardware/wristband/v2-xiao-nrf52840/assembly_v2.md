# OpenHear Wristband v2 – Print &amp; Assembly Guide

Licences: hardware **CERN-OHL-S-2.0**, docs **CC-BY-SA-4.0**.

Status: DIY research prototype. **Not a certified hearing aid.** Does not
diagnose, treat, or cure hearing loss. Builders assume prototype risk and
must read [`../assembly_v1.md`](../assembly_v1.md) for the full safety
checklist that still applies in v2.

This guide extends the v1 and v1.5-no-solder philosophy:

- **v1**         = compact, advanced, soldered.
- **v1.5**       = beginner-friendly, no-solder modular, larger.
- **v2 (this)**  = **slim daily-wear**, no-solder by default, looks/feels
  like an Apple Watch Ultra or Whoop 4.0, still 100 % open-source.

## 1. What you’ll print

From `parametric_wristband_v2.scad`, generate two STLs by changing the
`build_part` parameter (or use the pre-oriented STLs in
[`print_pack/stl/`](print_pack/stl/) and the one-page
[`print_pack/PRINT_ME.md`](print_pack/PRINT_ME.md) if you just want to
hand the files to a 3D-print service):

```bash
# from hardware/wristband/v2-xiao-nrf52840/
openscad -D build_part=\"case\" -o case_v2.stl parametric_wristband_v2.scad
openscad -D build_part=\"lid\"  -o lid_v2.stl  parametric_wristband_v2.scad
# Optional integrated TPU stub strap:
openscad -D build_part=\"strap_tpu\" -D strap_style=\"integrated_tpu\" \
         -o strap_stub_v2.stl parametric_wristband_v2.scad
```

### Print settings (FDM, recommended)

| Part   | Material              | Layer  | Walls | Infill         | Supports |
|--------|-----------------------|--------|-------|----------------|----------|
| Case   | PETG **or** PA12-CF   | 0.12 mm| 4     | 30 % gyroid    | None (lugs print over short bridge) |
| Lid    | PETG matte black      | 0.10 mm| 4     | 60 % gyroid    | None |
| Strap  | TPU 95A (community)   | 0.16 mm| 3     | 100 % concentric | None |

Hard-shell **resin** is also fine if you fully seal the skin side with
medical silicone, exactly as documented in v1.

Print the **case lid in matte black PETG** or PA12-CF for the “titanium
black” daily-wear look. Lightly bead-blast or fine-sand the lid for the
matte finish.

## 2. What you’ll buy

See [`BOM_v2.csv`](./BOM_v2.csv). The recommended no-solder kit:

- **1 ×** Seeed XIAO nRF52840 **Sense** (BLE 5, onboard LiPo charger, PDM mic, IMU)
- **1 ×** Seeed XIAO Expansion Board Base (Grove I²C + JST-PH battery socket)
- **1 ×** Adafruit DRV2605L STEMMA QT haptic driver
- **1 ×** Grove → STEMMA QT/Qwiic cable
- **2 ×** 10 mm pre-wired LRA coin motors (JST-PH lead)
- **1 ×** 3.7 V 300–500 mAh protected LiPo with JST-PH (e.g. **LP502535**)
- **1 ×** 2-pin magnetic pogo pair (one half lives on the case, the other
  becomes your charging dock)
- **1 ×** 20–22 mm quick-release sport band (any CC-licensed community
  parametric Apple-Watch-Ultra-style TPU band from
  **Printables** or **MakerWorld** drops straight in)
- **2 ×** 1.5 mm stainless quick-release spring bars

## 3. Strap options

The case ships with **`strap_style = "lugs"`** by default. That gives you
standard 20 mm or 22 mm quick-release lug pockets so you can use **any**
community-parametric Apple-Watch-style TPU/silicone band as a drop-in
strap. Search Printables / MakerWorld for:

- **“Apple Watch Ultra TPU band parametric”** – many CC-BY-licensed designs.
- **“22 mm quick release strap OpenSCAD”** – fork into the OpenHear repo
  later as a sibling SCAD file.

Set `strap_style = "integrated_tpu"` in the SCAD to print a one-piece TPU
band stub fused to the case (less swappable, but lighter and more
splash-tolerant).

## 4. Assembly steps (no-solder path)

1. **Print** `case_v2.stl` + `lid_v2.stl`. Test-fit the XIAO, LRAs, and
   battery in their pockets. Sand pockets lightly rather than forcing parts.
2. **Click** the XIAO nRF52840 Sense into the Seeed Expansion Board Base.
3. **Plug** the Grove-to-STEMMA QT cable from the expansion board’s I²C
   Grove port into the DRV2605L STEMMA QT input.
4. **Plug** the first LRA into the DRV2605L screw terminal / JST output.
   (For 2 LRAs, daisy-chain a second DRV2605L by changing its I²C address
   – open the ADDR jumper – and adding a second STEMMA QT cable.)
5. **Plug** the LiPo JST-PH lead into the expansion board battery socket.
6. **Flash** the firmware (`firmware/openhear_v2_xiao_nrf52840.ino`)
   over USB-C with the XIAO still outside the case. Confirm it advertises
   as `OpenHear-v2` and that your existing OpenHear phone/companion sees it.
7. **Disconnect** USB-C. Place the XIAO + expansion board into the wrist-side
   pocket, LRAs into their cylinders, battery flat in the lid-side pocket.
8. **Press-fit** the magnetic pogo pair through the two pads on the case
   floor near the lug end; route VBUS to the expansion board USB-C-side
   5 V test pad and GND to a GND pad.
9. **Optional:** line the seal groove on the case rim with a thin strip of
   1 mm self-adhesive silicone foam.
10. **Snap** the lid down. The tongue-and-groove seal lip mates with a
    light press. Add four M1.6 nylon screws only if you plan to sleep or
    swim in the prototype – do **not** swim with a prototype until you
    have completed the IP dry test.
11. **Fit** spring bars + your chosen 20/22 mm strap, and you’re wearing v2.

## 5. Charging dock

The pogo pair gives you an Apple-Watch-style **magnetic snap-on charger**:

- Print or buy a small dock that holds the *other* half of the pogo pair.
- Wire that dock to any standard USB-C 5 V source.
- The XIAO nRF52840 onboard LiPo charger handles termination automatically.
- Never charge unattended during prototyping; protected cells only.

## 6. First-run safety checklist (unchanged from v1)

- Start with `intensity_cap = 32 / 255` and no more than **5 minutes**
  continuous wear.
- Stop for numbness, pain, skin redness, heat, dizziness, or headache.
- Keep user-facing surface below **40 °C**; derate at 38 °C.
- Do **not** sleep with a prototype until battery, charger, and thermal
  tests pass.
- Burgess-Principle binary test: if any raw audio, audiogram data, or
  adaptation data must leave the device/cloud to function, the build
  fails. v2 keeps the same companion-only BLE architecture as v1.

## 7. Compatibility statement

v2 is **wire-compatible** with everything else in the repo:

- Same 3-byte BLE packet `[sound_class_id, intensity, pattern_id]`.
- Same 7-class YAMNet head and same audiogram JSON intensity weighting.
- Same GATT service / characteristic UUIDs as
  `wristband/openhear_firmware.py` and the v1 reference firmware.
- micro:bit v2, ESP32-S3, and RP2040 builds **remain supported as
  legacy options** under `hardware/wristband/` and
  `hardware/wristband/v1.5-no-solder/`. v2 is an additional path, not
  a replacement.
