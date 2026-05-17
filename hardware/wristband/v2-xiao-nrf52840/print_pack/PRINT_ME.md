# PRINT ME — OpenHear v2 Wristband

**One page. Hand this to any FDM print service. Print time ≈ 2 h for both parts.**

Licences: hardware **CERN-OHL-S-2.0**, docs **CC-BY-SA-4.0**.
Not a medical device. DIY research prototype.

---

## 1 · Files (already pre-oriented — load and slice)

| File | Part | Footprint (X × Y × Z) | Qty |
|---|---|---|---|
| `stl/openhear_v2_case.stl` | Main case (XIAO + LRA + battery pockets) | 44 × 38 × 9 mm | 1 |
| `stl/openhear_v2_lid.stl`  | Snap-fit lid with tongue seal + logo     | 42 × 36 × 2 mm | 1 |

Both STLs rest flat on the build plate at Z = 0. **Do not rotate.**

---

## 2 · Material

| Choice | Recommended | Why |
|---|---|---|
| **Best value (default)** | **PETG, matte black** | Skin-safe, tough, low warp, prints on any FDM machine. |
| Premium daily-wear | PA12-CF (nylon + carbon fibre) | Lighter, stiffer, sweat-proof, matte finish. |
| Hypoallergenic skin | PETG **medical-grade** or PLA + silicone liner | For sensitive skin (always seal the wrist face). |

Avoid raw ABS (warps), and avoid plain PLA for the case (softens with body heat / sun).

---

## 3 · Slicer settings (FDM, 0.4 mm nozzle)

| Setting | Case | Lid |
|---|---|---|
| Layer height | **0.12 mm** | **0.10 mm** |
| Wall / perimeters | **4** | **4** |
| Top / bottom layers | 5 | 5 |
| Infill | **30 % gyroid** | **60 % gyroid** |
| Supports | **None** | **None** |
| Brim | **5 mm** (improves first-layer adhesion on the curved underside) | None |
| Print speed | 40–60 mm/s | 30–40 mm/s (for crisp engraved logo) |
| Bed / nozzle (PETG) | 80 °C / 235 °C | 80 °C / 235 °C |
| Bed / nozzle (PA12-CF) | 90 °C / 280 °C, hardened nozzle | — |

**Estimated material:** ~8 g case + ~3 g lid ≈ **11 g total** per unit.
**Estimated print time:** case ≈ 1 h 30 min, lid ≈ 30 min (Prusa MK4-class).

---

## 4 · Orientation (already baked into the STLs)

```
            ┌──────────────┐   ← curved wrist underside faces UP
   CASE     │   ⌒⌒⌒⌒⌒    │      (open lid-opening rim sits flat on bed)
            └──────────────┘
              ▲ build plate

            ┌──────────────┐   ← engraved “OpenHear” logo faces UP
   LID      │  OpenHear    │      (tongue sealing lip sits flat on bed)
            └──────────────┘
              ▲ build plate
```

Why: the lid-opening rim of the case is the largest flat surface in the
part — putting it on the build plate gives a strong first layer, lets all
internal pockets (XIAO, LRAs, battery) print as straight downward
cavities, and removes any need for supports. The USB-C side cut-out is
small enough to self-bridge.

---

## 5 · Assembly (no tools beyond the parts themselves)

1. Slot the **Seeed XIAO nRF52840 (Sense)** into the labelled pocket; USB-C aligns with the side cut-out.
2. Drop the **2 × 10 mm LRA coin** actuators into their cylindrical pockets (double-sided foam tape OK).
3. (Optional) Slot the **DRV2605L STEMMA QT** into its square pocket and run a Grove cable to the XIAO.
4. Place the **300–500 mAh LiPo (e.g. LP502535)** in the battery bay above the XIAO.
5. Press the **lid** down — the tongue seats into the case groove (snap-fit, no screws).
6. Clip into a standard **20–22 mm quick-release watch strap** at the lugs.

Full electrical wiring, firmware flashing, and the BLE 3-byte packet
contract are in `../assembly_v2.md` and `../firmware/README.md`.

---

## 6 · Recommended print services for 1 unit

| Service | Material | Est. cost (1 unit, case + lid) | Lead time |
|---|---|---|---|
| **JLCPCB 3D printing** | PETG (FDM) | **~US $4–6** + shipping (~$10) | 3–5 days + shipping |
| **Craftcloud / Sculpteo** (price-compare hub) | PETG (FDM) | ~US $8–12 + shipping | 5–7 days |
| **Shapeways** | PA12 (MJF nylon) | ~US $20–25 + shipping | 7–10 days |
| **Local makerspace / Bambu / Prusa owner** | PETG (FDM) | **~US $1–2 in filament** | same day |

**Default recommendation:** PETG on FDM via a local maker or **JLCPCB** —
under US $20 delivered, under 1 week, and a perfect match for the slim
daily-wear case.

---

*Print Me card v1 · OpenHear v2 (XIAO nRF52840) · CC-BY-SA-4.0*
