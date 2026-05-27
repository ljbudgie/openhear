# Sweatproof Engineering — 10× Durability Through Microstructure + Coating

> *Two defences, one surface. The lotus doesn't wear a raincoat — it grew one.*

Moisture is the **#1 killer of hearing aids**. Sweat, condensation, and earwax
infiltrate every seam and pore, corroding electronics and degrading shell material
within months. Commercial manufacturers solve this with sealed, injection-moulded
enclosures and proprietary nano-coatings — solutions closed to the DIY maker.

This guide combines **two open, reproducible defence layers** — biomimetic
microstructures and chemical nano-coatings — to achieve **superhydrophobic +
oleophobic** performance that exceeds either method alone by an order of magnitude.

> **Relationship to [sweat-proofing.md](sweat-proofing.md):**
> That document covers all sweat-proofing methods individually (coatings, microstructures,
> sealants, earwax resistance, antimicrobial strategies). *This* document is a focused
> deep-dive into the **combined microstructure + coating approach** — the highest-durability
> option available to a home maker.

---

## Why "Combined" Wins

Neither microstructures nor coatings are sufficient alone:

| Defence | Mechanism | Weakness |
|---|---|---|
| **Microstructure only** | Air trapped between pillars prevents liquid contact (Cassie–Baxter state) | Pillars are fragile; oil/earwax fills the gaps over time, destroying the air layer |
| **Coating only** | Low-surface-energy chemistry repels water and oil | Coating wears off with abrasion, cleaning, and UV exposure (3–12 months) |
| **Combined** | Microstructure traps air → coating prevents oil infiltration → each protects the other | Requires sub-35 µm printer resolution and careful application — but the result is 10× durability |

The combined approach creates a **superhydrophobic** surface (water contact angle > 150°)
that is also **oleophobic** (resists earwax and skin oils) — properties neither layer
achieves independently.

---

## Layer 1: Re-Entrant Microstructures (Lotus Effect)

### The Principle

The lotus leaf repels water not because of chemistry alone, but because of
**geometry**. Its surface is covered in microscopic pillars topped with waxy
nanocrystals. Water droplets sit on the pillar tips, separated from the bulk
surface by trapped air (the **Cassie–Baxter state**). Dirt and debris are
carried away by rolling droplets — the "self-cleaning" effect.

We replicate this with **re-entrant (mushroom-cap) micro-pillars** printed
directly into the shell surface:

```
    ┌───┐   ┌───┐   ┌───┐      ← Mushroom caps (overhang traps air)
    │   │   │   │   │   │
    ╽   ╽   ╽   ╽   ╽   ╽      ← Pillar shafts
  ══╧═══╧═══╧═══╧═══╧═══╧══    ← Shell surface

    ~~~air~~~air~~~air~~~air     ← Trapped air layer (Cassie–Baxter)
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~← Water / sweat sits on top
```

The overhang on each cap creates a **re-entrant angle** that pins the liquid–air
interface, preventing water from penetrating even under pressure (e.g., during
insertion or jaw movement).

### Generating Pillar Arrays in OpenSCAD

The `parametric_shell.scad` file in this directory includes a ready-to-use
`lotus_microstructure(area_x, area_y)` module with the following default parameters:

| Parameter | Default | Description |
|---|---|---|
| `pillar_dia` | 0.15 mm | Shaft diameter of each micro-pillar |
| `pillar_cap_dia` | 0.25 mm | Mushroom cap diameter (must be > pillar_dia) |
| `pillar_height` | 0.30 mm | Total height from shell surface to cap top |
| `pillar_spacing` | 0.40 mm | Centre-to-centre pitch (hexagonal grid) |

**Usage (in `parametric_shell.scad`):**

```openscad
// Uncomment in the complete_shell() module to enable microstructure:
//
// difference() {
//     // ... shell body ...
//     translate([canal_offset_x, canal_offset_y, 0])
//         lotus_microstructure(14, 12);   // 14 × 12 mm patch
// }
```

> **Performance note:** A 14 × 12 mm patch generates ~1 050 pillars. Use **F5**
> (preview) during design iteration; reserve **F6** (render) for final STL export.

To customise the patch, override the defaults before calling the module:

```openscad
pillar_dia     = 0.12;   // thinner shafts for higher-resolution printers
pillar_cap_dia = 0.20;
pillar_spacing = 0.35;   // tighter pitch = more pillars = better air trapping
lotus_microstructure(16, 14);
```

### Printer Resolution Requirements

Microstructures demand **sub-35 µm XY resolution** to resolve the pillar shafts
and cap overhangs. Printers that meet this threshold:

| Printer | XY Resolution | Suitable? |
|---|---|---|
| Elegoo Saturn 4 Ultra (12K) | 18 µm | ✅ Yes — recommended |
| Anycubic Photon Mono M7 (14K) | 18 µm | ✅ Yes |
| Anycubic Photon Mono M5s (12K) | 19 µm | ✅ Yes |
| Printers with > 35 µm XY | > 35 µm | ❌ No — pillars will fuse into ridges |

> If your printer cannot resolve microstructures, skip Layer 1 and rely on
> Layer 2 (nano-coating) alone. You will still achieve good protection —
> just not the 10× combined benefit.

### Where to Apply on the Shell

**Apply microstructures to external concha-facing surfaces only.**

```
         ┌──────────────┐
         │   FACEPLATE   │  ← Microstructure ✅ (exposed to sweat)
         │               │
    ┌────┤   CONCHA      │  ← Microstructure ✅ (exposed to sweat)
    │    │   BOWL        │
    │    └───┐           │
    │  HELIX │           │
    │        │  CANAL ●──┼──── NO microstructure ❌ (skin contact —
    │        │           │     must be smooth for comfort and seal)
    └────────┴───────────┘
```

- **YES:** Faceplate, concha bowl, helix rim — any surface exposed to sweat but
  not in direct sliding contact with the ear canal.
- **NO:** Canal bore, canal tip, any surface that touches the ear canal skin.
  Microstructures here would cause irritation and compromise the acoustic seal.

---

## Layer 2: Nano-Coating Recipe

After printing and post-processing (see [print_settings.md](print_settings.md)),
apply a hydrophobic/oleophobic nano-coating to the entire external shell surface —
*including* over the microstructured areas.

### Recommended Coatings

| Coating | Manufacturer | Water Contact Angle | Oil Resistant | Durability | Notes |
|---|---|---|---|---|---|
| **NANOMYTE SR-500HP** | NEI Corporation | > 115° | ✅ Yes | 12–18 months | Best overall durability; spray application |
| **Nasiol NanoHearShield** | Nasiol | > 110° | ✅ Yes | 6–12 months | Formulated for hearing aids; wipe-on |

> Both coatings are fluoropolymer-based. See the Safety section below for handling precautions.
> For a broader coating comparison, see [sweat-proofing.md](sweat-proofing.md).

### Step-by-Step Application

**1. Surface Prep**

□ Confirm the shell is **fully UV-cured** and post-processed
  (see [print_settings.md](print_settings.md) post-processing checklist).

□ Clean the entire shell with **≥ 90% IPA** on a lint-free wipe. Remove all dust,
  fingerprints, and sanding residue.

□ Allow to dry completely — **5 minutes minimum** in open air.

□ *(Optional but recommended)* **Plasma activation:** If you have access to a
  handheld plasma treater (e.g., Relyon PZ2), pass it over the shell surface for
  10–15 seconds at 5 mm distance. Plasma activation increases surface energy,
  allowing the coating to bond more uniformly and last 2–3× longer.

> If you don't have a plasma treater, skip this step. The coating will still work —
> just at the lower end of its durability range.

**2. Masking**

□ Mask the **canal bore** and **receiver port** with Kapton tape or Blu-Tack.
  Coating inside the canal may affect acoustic seal and skin compatibility.

□ Mask any **electrical contacts** or **charging pins** if present.

**3. Coating Application**

For **NANOMYTE SR-500HP** (spray):

□ Shake the can for 30 seconds.

□ Hold 15–20 cm from the shell. Apply **2 light, even passes** — do not flood.

□ Wait **2 minutes** between passes.

□ Allow to air-cure for **24 hours** at room temperature before handling.

For **Nasiol NanoHearShield** (wipe):

□ Apply 3–4 drops to a **microfibre cloth** (supplied in kit).

□ Wipe the shell in smooth, overlapping strokes. Cover all external surfaces.

□ Buff with the dry side of the cloth after **1 minute**.

□ Allow to cure for **12 hours** at room temperature.

**4. Validation**

□ Place a single water droplet (≈ 3 mm diameter) on the coated surface.
  It should bead into a near-sphere and roll off when the shell is tilted > 15°.

□ Expected water contact angle: **> 115°** on coated flat surfaces,
  **> 140°** on coated microstructured surfaces.

□ Apply a thin smear of petroleum jelly (earwax simulant) to the coated surface.
  It should wipe off cleanly with a dry cloth, leaving no residue.

---

## Combined Approach — Why 1 + 1 = 10

Microstructures and coatings protect each other in a reinforcing cycle:

```
  MICROSTRUCTURE alone:              COATING alone:
  ┌───┐ ┌───┐ ┌───┐                 ════════════════
  │   │ │   │ │   │                  ↕ thin coating
  ╽   ╽ ╽   ╽ ╽   ╽                 ════════════════
  ══════════════════                 (wears off in 3–12 months)
  Air trapped ✅
  But oil fills gaps over time ❌

  COMBINED:
  ┌─C─┐ ┌─C─┐ ┌─C─┐    C = coating on every surface
  │ C │ │ C │ │ C │       (pillars + caps + base)
  ╽ C ╽ ╽ C ╽ ╽ C ╽
  ═C════C════C════C═
  Air trapped ✅
  Oil blocked by coating ✅
  Coating protected from abrasion by recessed geometry ✅
```

**Why 10× and not 2×:**

1. **Air-trapping** (microstructure) reduces the liquid–surface contact area by ~90%.
   Less contact = less chemical attack on the coating.

2. **Coating** prevents oil/earwax from wetting into the pillar gaps, maintaining
   the Cassie–Baxter air layer indefinitely.

3. The coating on **recessed surfaces** (between pillars) is shielded from
   mechanical abrasion — only the cap tops touch anything, and they represent
   < 10% of the coated area.

4. If a cap tip's coating wears through, the air layer **still prevents wetting**
   of the exposed pillar. The surface degrades gracefully rather than catastrophically.

The result: coating that would last 6 months alone now lasts **12–18+ months**,
and microstructures that would clog in weeks stay functional for the life of the shell.

---

## Performance Comparison

| Metric | Bare Resin | Coating Only | Microstructure Only | Combined |
|---|---|---|---|---|
| **Water contact angle** | 60–75° | 105–115° | 130–145° | **> 150°** (superhydrophobic) |
| **Earwax resistance** | Poor — wax adheres and stains | Good — wipes off with cloth | Moderate — wax fills pillar gaps over time | **Excellent — wax beads and rolls off** |
| **Durability (months)** | 1–2 (surface degrades) | 3–12 (coating wears) | 1–3 (pillars clog) | **12–18+** |
| **Maintenance interval** | Weekly cleaning required | Monthly wipe | Weekly cleaning + IPA flush | **Monthly wipe only** |
| **Sweat immersion survival** | Degrades within weeks | 6+ months | 2–4 weeks (then pillars clog) | **12+ months** |
| **Self-cleaning effect** | ❌ None | ❌ Minimal | ✅ Moderate (when dry) | **✅ Strong (wet and dry)** |
| **Oleophobic** | ❌ No | ✅ Yes | ❌ No | **✅ Yes** |
| **Complexity** | None | Low (spray/wipe) | High (CAD + high-res printer) | **High (both steps required)** |

---

## Real-World Validation Checklist

These tests mirror those in [sweat-proofing.md](sweat-proofing.md) but include
**pass criteria calibrated for the combined approach**. Run all five tests on your
finished, coated shell before daily use.

### Test 1: Water Bead Test

□ Place a 3 mm water droplet on a coated + microstructured area.

□ **Pass:** Droplet forms a near-perfect sphere (contact angle > 150°).
  Rolls off when shell is tilted ≤ 10°.

□ **Marginal:** Contact angle 120–150°. Re-examine coating application —
  likely insufficient coverage or missed plasma activation.

□ **Fail:** Contact angle < 120°. Strip coating with IPA, re-prep surface, recoat.

### Test 2: Sweat Simulation

□ Prepare synthetic sweat per ISO 105-E04:
  **5 g NaCl + 1 g urea + 1 L distilled water**, pH adjusted to 5.5 with acetic acid.

□ Submerge the shell in the solution for **4 hours** at **37 °C** (body temperature).

□ Remove, rinse with distilled water, air-dry.

□ **Pass:** No visible wetting, staining, or surface change. Water bead test still passes.

□ **Fail:** Surface shows wetting, discolouration, or tackiness. Investigate resin cure
  completeness and coating adhesion.

### Test 3: Earwax / Oil Resistance

□ Apply a 5 mm smear of **petroleum jelly** (cerumen simulant) to the coated surface.

□ Wait **10 minutes** at room temperature.

□ Wipe with a dry microfibre cloth — **one pass, light pressure**.

□ **Pass:** No visible residue. Surface is clean and dry.

□ **Fail:** Residue remains. Coating may be insufficient on that area — apply a second coat.

### Test 4: Durability Simulation

□ Submerge the shell in synthetic sweat solution (see Test 2) for **30 minutes**.

□ Remove, rinse, dry. Repeat for **10 cycles**.

□ After all 10 cycles, repeat the Water Bead Test (Test 1).

□ **Pass:** Contact angle still > 140° after 10 cycles.

□ **Marginal:** Contact angle 110–140°. Coating is functional but consider reapplication
  after 6 months rather than 12.

□ **Fail:** Contact angle < 110°. Coating adhesion is poor — review surface prep steps.

### Test 5: Real-World Wear Test

□ Wear the shell during **moderate exercise** (30-minute walk or light jog) in warm conditions.

□ Remove after exercise. Inspect for:
  - Water ingress into the canal or receiver bore
  - Comfort changes (swelling, itching, pressure)
  - Surface changes (discolouration, tackiness)

□ **Pass:** No water ingress, no comfort change, no surface change.

□ **Fail:** Any of the above. Investigate masking integrity (canal should be uncoated),
  fit (see [workflow.md](workflow.md)), or resin biocompatibility (see [materials.md](materials.md)).

---

## Safety

> ⚠️ **Nano-coating safety precautions:**
>
> - **Fluoropolymer coatings** release harmful fumes if heated above 250 °C.
>   Never heat-cure these coatings — air-cure at room temperature only.
> - Apply coatings in a **well-ventilated area** or outdoors. Wear a **respirator**
>   (P100 or organic vapour cartridge) when spraying.
> - Wear **nitrile gloves** during application. Avoid skin contact with uncured coating.
> - **Disposal:** Follow local regulations for fluorinated chemical waste.
>   Do not pour down drains. Fully cured coating on the shell is inert.
> - **Plasma treaters** generate ozone — use in a ventilated space and do not
>   direct at skin or eyes.
>
> ⚠️ **Microstructured shells:**
>
> - Micro-pillars on the shell exterior are **fragile**. Handle with care during
>   coating application — do not press or rub the microstructured surface.
> - Microstructures must **never** be applied inside the ear canal. They will
>   cause irritation, trap debris, and compromise the acoustic seal.
>
> This is an experimental, open-source project — **not a certified medical device.**
> See the [safety module](../safety/README.md) and the project [README](../../README.md) for full disclaimers.

---

*Next: [resources.md](resources.md) — suppliers, research papers, and community links.*

*This module is part of [OpenHear](../../README.md) — sovereign audio for sovereign people.*
*MIT Licensed.*
