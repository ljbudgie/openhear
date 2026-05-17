# OpenHear v2 — Print-Service-Ready Pack

Drop-in package for any FDM 3D-printing company or makerspace. The two
STL files are **pre-oriented** for FDM, with the optimal face flat on
the build plate and no supports required.

## Contents

| File | Purpose |
|---|---|
| [`PRINT_ME.md`](PRINT_ME.md) | One-page instruction card: material, slicer settings, orientation diagram, assembly steps, service + cost recommendation. |
| [`stl/openhear_v2_case.stl`](stl/openhear_v2_case.stl) | Main case (44 × 38 × ~9 mm). Lid-opening rim is on the build plate. |
| [`stl/openhear_v2_lid.stl`](stl/openhear_v2_lid.stl)   | Snap-fit lid (~42 × 36 × 2 mm). Tongue seal is on the build plate, engraved logo faces up. |

## How a print service should use this pack

1. Open `PRINT_ME.md` (one page).
2. Load the two STL files in `stl/` directly into the slicer — **do not
   rotate**.
3. Use the suggested PETG profile (0.12 mm layers, 4 walls, 30 % gyroid,
   no supports, 5 mm brim on the case).
4. Total filament ≈ 11 g, total print time ≈ 2 h.

For a 1-unit quote, the **PETG-on-FDM** path via JLCPCB or a local
makerspace lands around **US $5–20 delivered** in under a week.

## Regenerating the STLs

The STLs are generated from
[`../parametric_wristband_v2.scad`](../parametric_wristband_v2.scad) with
OpenSCAD ≥ 2021.01:

```bash
# from hardware/wristband/v2-xiao-nrf52840/
openscad -D 'build_part="case"' -o /tmp/case_raw.stl parametric_wristband_v2.scad
openscad -D 'build_part="lid"'  -o /tmp/lid_raw.stl  parametric_wristband_v2.scad
```

The print-pack STLs additionally apply the FDM-optimal orientation:
- **Case** — rotated 180° about the X axis so the open lid-opening face
  lies on the build plate (curved wrist underside facing up).
- **Lid**  — left in its native orientation (tongue down, logo up) and
  dropped so the lowest point sits at Z = 0.

Both parts are recentred in XY around the build-plate origin.

## Licence

Hardware **CERN-OHL-S-2.0**, docs **CC-BY-SA-4.0**.
Not a medical device. DIY research prototype.
