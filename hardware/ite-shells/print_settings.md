# Print Settings — Exact Slicer Profiles for ITE Shells

> *Precision is not optional — when the canal is your interface, every micron matters.*

Custom in-the-ear shells demand tighter tolerances than almost any other consumer 3D-printing application.
A 50 µm layer-height error compounds across 200+ layers into a shell that rocks, whistles, or hurts.
This guide provides **tested, copy-paste slicer profiles** so you can skip the calibration lottery and
start with settings that produce wearable shells on the first print.

**Why exact settings matter:**

| Factor | Effect of wrong setting |
|---|---|
| Layer height too large | Visible stair-stepping in the canal — discomfort and poor seal |
| Exposure too short | Under-cured walls — brittle, fails during support removal |
| Exposure too long | Over-cured — detail loss, canal too tight |
| Lift speed too fast | Suction cupping — peels thin canal walls off supports |
| Anti-alias off | Voxel stepping on curved surfaces — rough texture in the ear |

> All profiles below assume **biocompatible, clear or translucent resin** (see [materials.md](materials.md)).
> If you switch resins, run a validation print (see [workflow.md](workflow.md)) before committing to a full shell.

---

## Elegoo Saturn 4 Ultra

The Saturn 4 Ultra's 12K mono LCD (11520 × 5120, 18 µm XY) is the current
sweet spot for ITE shells — enough resolution for canal detail and microstructure
experiments, at a hobbyist-accessible price.

### Chitubox Pro Settings

| Parameter | Value | Notes |
|---|---|---|
| Layer Height | 0.03 mm | 30 µm — maximises canal surface smoothness |
| Normal Exposure Time | 2.5 s | Tuned for Liqcreate Bio-Med Clear; increase 0.3 s for DETAX |
| Bottom Layer Count | 6 | Anchors the raft without over-curing the base |
| Bottom Exposure Time | 30 s | Sufficient adhesion on FEP2 film |
| Lift Speed | 1 mm/s | Slow lift prevents suction damage to thin canal walls |
| Retract Speed | 3 mm/s | Faster retract is safe — no peel force during descent |
| Rest Time After Lift | 1 s | Lets resin settle before next exposure |
| Rest Time After Retract | 0.5 s | Minimal — resin is already level |
| Anti-Aliasing Level | 8 | Smooths voxel edges; critical for curved canal geometry |
| Image Blur | 2 px | Pairs with AA-8 to eliminate jagged contours |
| Transition Layer Count | 4 | Gradual exposure ramp from bottom to normal layers |
| Transition Type | Linear | Even ramp avoids abrupt cure-energy changes |

> **Tip:** Enable "Tolerance Compensation" in Chitubox and set **Inner: −0.05 mm**, **Outer: 0.00 mm**.
> This pre-shrinks the canal bore slightly to compensate for resin swell during post-cure.

### Lychee Slicer Equivalent

| Lychee Parameter | Value | Chitubox Equivalent |
|---|---|---|
| Layer Thickness | 0.03 mm | Layer Height |
| Exposure Time | 2.5 s | Normal Exposure Time |
| Bottom Layers | 6 | Bottom Layer Count |
| Bottom Exposure Time | 30 s | Bottom Exposure Time |
| Lifting Speed | 1 mm/s (60 mm/min) | Lift Speed |
| Retraction Speed | 3 mm/s (180 mm/min) | Retract Speed |
| Wait Before Print | 1 s | Rest Time After Lift |
| Anti-Aliasing | 8× | Anti-Aliasing Level |
| Grey Level | 2 | Image Blur |

> Lychee's "Smart Supports" with **0.3 mm contact diameter** and **medium density**
> work well for shells. Manually add light supports inside the canal where auto-placement misses.

### Recommended Resins

| Resin | Manufacturer | Biocompatibility | Shore Hardness | Notes |
|---|---|---|---|---|
| **Liqcreate Bio-Med Clear** | Liqcreate | ISO 10993 tested | 85D | Excellent clarity, low shrinkage, profiles above tuned for this resin |
| **DETAX Freeprint shell** | DETAX | Class IIa medical device resin | 83D | Industry-standard audiology resin; increase exposure +0.3 s |

> See [materials.md](materials.md) for the full resin comparison table and biocompatibility details.

---

## Anycubic Photon Mono M5s / M7

The Photon Mono M5s (12K, 19 µm XY) and M7 (14K, 18 µm XY) are strong
alternatives. The M7's larger build volume is useful for batch-printing
left + right shells simultaneously.

### Anycubic Photon Workshop Settings

| Parameter | M5s Value | M7 Value | Notes |
|---|---|---|---|
| Layer Height | 0.03 mm | 0.03 mm | Same target as Saturn 4 Ultra |
| Normal Exposure Time | 2.8 s | 2.5 s | M5s light engine is slightly less powerful |
| Bottom Layer Count | 6 | 6 | |
| Bottom Exposure Time | 32 s | 28 s | M7's COB array is more uniform — needs less |
| Lift Speed | 1 mm/s | 1 mm/s | Critical — do not exceed for canal walls |
| Retract Speed | 3 mm/s | 3 mm/s | |
| Rest Time After Lift | 1.5 s | 1 s | M5s benefits from slightly longer settle |
| Anti-Aliasing | 8 | 8 | |
| Light-Off Delay | 1 s | 0.5 s | M5s uses this instead of separate rest timers |
| Bottom Light-Off Delay | 3 s | 2 s | Extra settle time for raft adhesion |

> **M5s note:** If using Lychee or Chitubox instead of Photon Workshop, export as
> `.pwma` (M5s) or `.pm7` (M7). Verify the slicer's machine profile matches your
> firmware version — incorrect profiles cause exposure-time scaling errors.

### Lychee / Chitubox Profiles for Anycubic

Use the same parameter values from the table above. The only difference is the
machine profile and file format:

| Slicer | Machine Profile | Export Format |
|---|---|---|
| Chitubox Pro | Anycubic Photon Mono M5s / M7 | `.pwma` / `.pm7` |
| Lychee Slicer | Anycubic Photon Mono M5s / M7 | `.pwma` / `.pm7` |

---

## Post-Processing Checklist

Post-processing converts a fragile green print into a wearable, skin-safe shell.
Skip a step and you risk skin irritation, poor fit, or premature failure.

### IPA Wash

□ **Bath 1:** Submerge the print (still on supports) in **≥ 90% IPA** for **3 minutes**
  with gentle agitation. Use a magnetic stirrer or swirl by hand every 30 s.

□ **Bath 2:** Transfer to a **fresh IPA bath** for another **3 minutes**.
  The second bath removes residual uncured resin that the first bath dissolved and redeposited.

□ Air-dry for **5 minutes** in a well-ventilated area before UV curing.
  Trapped IPA causes white blooming during cure.

> ⚠️ **Safety:** IPA is flammable and an irritant. Work in a ventilated space, wear nitrile gloves,
> and keep away from ignition sources. See [materials.md](materials.md) for full safety guidance.

### UV Cure

□ Place the shell in a **405 nm UV curing station** (e.g., Anycubic Wash & Cure, Elegoo Mercury).

□ Cure **10 minutes per side** — flip the shell halfway to ensure even cross-linking inside the canal.

□ If water-curing (submerged in water during UV exposure), reduce time to **8 minutes per side**.
  Water transmits UV more evenly and prevents oxygen inhibition on the surface.

□ Verify cure: the shell should be **hard, non-tacky**, and produce a clear "tap" sound against a fingernail.

### Support Removal

□ Remove supports with **flush cutters** — cut as close to the shell surface as possible.

□ For supports inside the canal, use **angled flush cutters** or a **sharp hobby knife** (X-Acto #11).

□ Sand support witness marks with **400-grit wet/dry sandpaper**, working in the direction of the canal curve.

> **Tip:** Remove supports *after* UV curing, not before. Cured supports snap off cleaner and
> leave smaller witness marks than uncured ones.

### Wet Sanding Sequence

Wet sanding removes layer lines and support marks to produce a smooth, skin-friendly surface.
Always sand **wet** — dry sanding creates fine resin dust that is an inhalation hazard.

□ **400 grit** — Remove support marks and obvious layer lines. Light pressure, circular motion.

□ **800 grit** — Blend sanded areas into surrounding surface. The shell should feel uniformly smooth.

□ **1000 grit** — Refine the canal bore. Wrap sandpaper around a dowel that matches the canal diameter.

□ **1500 grit** — Eliminate remaining scratches. The surface should look uniformly hazy.

□ **2000 grit** — Final pass. The surface should be satin-smooth to the touch.

### Final Finish

Choose one:

| Finish | Method | Result |
|---|---|---|
| **Satin matte** | Stop at 2000 grit | Subtle sheen, hides fingerprints, comfortable grip in the ear |
| **Spray matte** | Tamiya TS-80 Clear Flat — light dusting from 20 cm | Uniform matte, masks minor imperfections |
| **Gloss** | Continue sanding to 3000 → 5000 grit, then Novus #2 polish | High-gloss "commercial" look; shows fingerprints |

> For most users, **satin matte (2000-grit stop)** is the best balance of aesthetics,
> comfort, and ease. Gloss looks impressive but requires significantly more effort.

---

## Orientation Guide

How you orient the shell on the build plate determines canal detail quality,
support placement, and suction-cupping risk.

```
            Build plate (top)
            ┌─────────────────┐
            │                 │
            │   ███████████   │  ← Raft / base
            │   ║         ║   │
            │   ║  SHELL  ║   │  Canal opening faces DOWN
            │   ║         ║   │  (toward the FEP)
            │   ║    ●    ║   │  ● = canal bore axis
            │   ║         ║   │
            │   ╚═════════╝   │
            │                 │
            └─────────────────┘
            FEP film (bottom)
```

**Recommended orientation:**

1. **Canal opening faces the build plate** (tilted 15–30° from vertical).
   This lets the canal interior print without internal supports, preserving bore accuracy.

2. **Tilt 15–30° toward the helix side.** This reduces suction-cupping on the
   large concha surface and ensures each layer peels progressively rather than
   all-at-once.

3. **Rotate 5–10° around the vertical axis** so no large flat cross-section is
   parallel to the FEP. This further reduces peel force.

4. **Support the faceplate edge and helix rim** — these are the thickest, most
   tolerant areas. Avoid supports inside the canal or on the concha's skin-contact surface.

> **Test print tip:** Before committing your final shell, print a **50% scale test**
> at the same orientation. It uses less resin and reveals orientation problems in 30 minutes.

---

## Common Print Failures

| Failure | Symptom | Likely Cause | Fix |
|---|---|---|---|
| **Suction cupping** | Thin canal walls deform or detach; hollow "pop" sound during printing | Lift speed too fast; large flat cross-sections parallel to FEP | Reduce lift speed to ≤ 1 mm/s; tilt shell 20–30°; add a 1 mm vent hole in the canal tip |
| **Layer lines (visible stair-stepping)** | Rough texture on curved canal surfaces | Layer height > 0.03 mm; anti-aliasing disabled | Set layer height to 0.03 mm; enable AA-8; verify slicer profile matches printer |
| **Warping / curling** | Edges of the faceplate lift away from supports | Over-exposure on bottom layers; insufficient supports on faceplate edge | Reduce bottom exposure by 2–4 s; add supports along the faceplate perimeter |
| **Adhesion failure** | Print detaches from build plate mid-print; stuck to FEP | Build plate not levelled; bottom exposure too low; FEP worn | Re-level (paper method); increase bottom exposure +4 s; replace FEP if cloudy |
| **Elephant's foot** | Widened base layers; raft edge is flared | Bottom exposure too high; transition layers too few | Reduce bottom exposure; increase transition layers to 6; use bottom-exposure ramp |
| **Cloudy / milky surface** | White haze on cured shell | IPA trapped in surface before UV cure; humidity during cure | Air-dry 10+ min after IPA wash; cure in low-humidity environment or submerged in water |
| **Incomplete canal** | Canal bore is partially filled or collapsed | Supports inside canal blocked resin drainage; incorrect orientation | Orient canal opening downward; remove internal supports; add drainage tilts |

---

## Safety

> ⚠️ **Uncured resin is a skin sensitiser and environmental toxin.**
>
> - Always wear **nitrile gloves** when handling uncured prints or resin.
> - Work in a **well-ventilated area** or use a fume extractor.
> - **Never pour resin down the drain.** Cure waste resin under UV light until solid, then dispose as general waste.
> - IPA wash solution becomes contaminated — cure it under UV, filter, and reuse or dispose responsibly.
> - Cured, post-processed resin is generally inert, but **only use biocompatible resins** for
>   anything that contacts skin or the ear canal (see [materials.md](materials.md)).
>
> This is an experimental, open-source project — **not a certified medical device.**
> See the [safety module](../safety/README.md) and the project [README](../../README.md) for full disclaimers.

---

*Next: [sweat-proofing.md](sweat-proofing.md) — protect your finished shell from moisture and earwax.*

*This module is part of [OpenHear](../../README.md) — sovereign audio for sovereign people.*
*MIT Licensed.*
