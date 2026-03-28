# Materials Guide — ITE Shell Resins, Coatings & Pigments

> Choose what touches your body. This is sovereign material selection.

This guide covers every material you need to build a comfortable, durable, skin-like ITE shell. All recommendations are current as of 2025–2026 and prioritise biocompatibility, skin feel, and availability to makers.

---

## Biocompatible Resin Comparison

### Rigid Resins (Shell Body)

These resins form the structural shell. They are hard, dimensionally stable, and suitable for housing electronics.

| Resin | Manufacturer | Biocompatibility | Shore Hardness | Tensile Strength | Elongation | UV Stable | Price (approx.) | Notes |
|-------|-------------|-----------------|----------------|-----------------|------------|-----------|-----------------|-------|
| **BioMed Clear** | Formlabs | ISO 10993-5, 10993-10 (cytotoxicity, irritation) | 85D | 51 MPa | 6% | Good | £200/L | Gold standard for hearing aid shells. Optically clear, excellent surface finish. Requires Form 3B+/4B printer |
| **BioMed Durable** | Formlabs | ISO 10993-5, 10993-10 | 78D | 32 MPa | 35% | Good | £200/L | More impact-resistant than BioMed Clear. Slight flexibility reduces cracking. Requires Form 3B+/4B |
| **OTO-A1 Shell** | 3Dresyns | ISO 10993-5 | 82D | 45 MPa | 8% | Moderate | €120/500mL | Purpose-designed for hearing aid shells. Works with open resin printers (Elegoo, Anycubic) |
| **OTO-C1 Clear** | 3Dresyns | ISO 10993-5 | 80D | 40 MPa | 10% | Good | €110/500mL | Clear variant of the OTO series. Good for translucent shells |
| **luxaprint shell** | DETAX | ISO 10993-5, ISO 10993-10, Class IIa | 84D | 55 MPa | 5% | Excellent | €180/1kg | Industry-standard hearing aid shell resin. Exceptional detail and dimensional stability |
| **Freeprint shell** | DETAX | ISO 10993-5, ISO 10993-10 | 82D | 50 MPa | 7% | Excellent | €160/1kg | Slightly more flexible variant. Lower viscosity — easier printing |
| **Bio-Med Clear** | Liqcreate | ISO 10993-5, USP Class VI | 82D | 50 MPa | 5% | Good | €90/1kg | Excellent value. Works with most open MSLA printers. Good dimensional accuracy |
| **Bio Resin** | Elegoo | Class I biocompatible, basic skin contact | 80D | 40 MPa | 6% | Moderate | £40/500mL | Budget option. Suitable for prototyping and iteration. Fully cure before skin contact |

> **Recommendation for most makers:** Start with **Liqcreate Bio-Med Clear** or **Elegoo Bio Resin** for prototyping and fit iteration. Move to **3Dresyns OTO-A1** or **DETAX Freeprint shell** for final-quality shells. Use **Formlabs BioMed Clear** only if you own a Form 3B+/4B.

### Flexible / Skin-Like Resins (Canal Tips, Soft Inserts)

These resins produce soft, flexible parts. Use them for canal tips, comfort liners, or full soft-shell designs that feel like skin rather than hard plastic.

| Resin | Manufacturer | Biocompatibility | Shore Hardness | Elongation | Tear Strength | Feel | Price (approx.) | Notes |
|-------|-------------|-----------------|----------------|------------|---------------|------|-----------------|-------|
| **BioMed Flex 80A** | Formlabs | ISO 10993-5, 10993-10 | 80A | 110% | 25 kN/m | Firm rubber | £200/L | Similar feel to a hearing aid dome. Semi-flexible. Requires Form 3B+/4B |
| **Elastic 50A** | Formlabs | ISO 10993-5, 10993-10 | 50A | 160% | 19 kN/m | Soft silicone-like | £200/L | Very soft. Closest to skin feel. Excellent for canal tips. Requires Form 3B+/4B |
| **Flexible 80A** | Formlabs | ISO 10993-5, 10993-10 | 80A | 120% | 24 kN/m | Firm rubber | £180/L | Non-BioMed version. Fine for prototyping, not for final ear canal use |
| **OTO-F1 Flex** | 3Dresyns | ISO 10993-5 | 60A | 200% | 20 kN/m | Soft, elastic | €140/500mL | Works on open printers. Best flexible option for non-Formlabs users |
| **Resione F69 Bio** | Resione | ISO 10993-5 | 50A–70A (tunable) | 250% | 18 kN/m | Very soft, skin-like | ~£50/500mL | Variable hardness by cure time. Budget-friendly. Available on AliExpress |
| **Siraya Tech Tenacious** | Siraya Tech | Basic biocompatible (skin contact after full cure) | 80A | 140% | 22 kN/m | Firm rubber | £50/500mL | Mix with rigid resin 20:80 for toughened shells. Full flexible at 100% |

> **Shore Hardness Guide for Context:**
>
> | Shore A Rating | Feels Like | Suitability |
> |---------------|-----------|-------------|
> | 30A–40A | Gummy bear, soft gel | Too soft for structural shells. Good for comfort pads |
> | 50A | Rubber band, pencil eraser | Excellent canal tip material. Skin-like softness |
> | 60A–70A | Shoe sole, firm rubber | Good balance of comfort and durability |
> | 80A | Car tyre, hard rubber | Semi-rigid. Good for full-shell flex builds |
> | 85D+ | Hard plastic | Structural shell material |

### Hybrid Approach (Recommended)

The best ITE shells combine rigid and flexible materials:

- **Rigid shell body** (85D resin) — houses electronics, provides structural integrity
- **Flexible canal tip** (50A–80A resin) — contacts ear canal, provides comfort and seal
- **Bonded interface** — the flexible tip is printed separately and bonded to the rigid shell with cyanoacrylate (super glue) or UV-cure adhesive

This mimics how professional hearing aid labs build shells: hard body, soft tip. The soft tip conforms slightly to your ear canal under body heat, creating a better seal and more comfortable fit.

---

## Pigmentation — Skin-Tone Matching

Bare resin is typically clear, white, or translucent. For a natural appearance, ITE shells should be pigmented to match (or approximate) your skin tone.

### Methods

#### 1. Pre-Mix Pigment into Resin (Best Results)

Add pigment directly to the resin before printing. This produces uniform colour throughout the shell — no surface layer to chip or wear.

| Pigment Type | Supplier | Usage Rate | Notes |
|-------------|----------|-----------|-------|
| **Resin pigment paste (skin tones)** | Monocure3D, 3Dresyns | 0.5–2% by weight | Purpose-made for UV resins. Skin tone packs available |
| **Alcohol-based dye (skin tones)** | Smooth-On Silc Pig, custom cosmetic pigments | 0.1–0.5% by weight | Mix thoroughly. Test small batch first |
| **Mica powder (matte finishes)** | Hobbycraft, Amazon cosmetic suppliers | 1–3% by weight | Creates a matte, slightly pearlescent finish. Flesh-tone mica powders available |

**Recommended mix process:**

1. Weigh your resin in a clean mixing cup
2. Add pigment paste/powder at 1% by weight to start
3. Stir thoroughly for 2–3 minutes — no streaks should be visible
4. Print a small test piece and compare to your skin in natural light
5. Adjust pigment percentage up or down and repeat until satisfied
6. Once calibrated, record the exact ratio for future batches

> **Warning:** Adding too much pigment (>3%) can interfere with UV curing. The pigment absorbs UV light, so thicker layers may not cure fully. Increase exposure time by 10–20% when using pigmented resin and always verify cure quality.

#### 2. Post-Print Surface Colouring

If you prefer to print in uncoloured resin, you can apply colour after printing.

| Method | Product | Notes |
|--------|---------|-------|
| **Airbrush with skin-tone paint** | Tamiya flat flesh, Vallejo skin tone set | Best control. Apply 2–3 thin coats. Seal with matte clear coat |
| **Spray paint** | Montana Gold flesh tones | Quick but less precise. Use in well-ventilated area |
| **Dip dye** | iDye Poly (for synthetics) | Immerse cured resin in hot dye bath. Results vary by resin |

#### 3. Matte Texturing (Skin-Like Surface)

A matte finish feels more natural against skin than a glossy surface. Hard, shiny plastic screams "medical device." Matte, soft-touch surfaces feel like skin.

| Technique | How | Result |
|-----------|-----|--------|
| **Matte clear coat** | Spray matte lacquer (e.g., Tamiya TS-80 Flat Clear, Mr. Hobby Flat Clear) over pigmented shell | Removes shine, feels soft to touch |
| **Micro-sandblasting** | Blast cured shell with fine aluminium oxide media (120–220 grit) at low pressure | Uniform matte texture. Excellent skin-like feel |
| **Fine sanding** | Wet-sand with 1500–2000 grit, then do NOT polish — stop at matte | Simple, no equipment needed |
| **Textured print surface** | Add micro-texture to the STL (0.05–0.1mm bumps) in CAD before printing | Built-in matte texture. No post-processing needed |

> **Best combination for skin-like appearance:**
> Pre-mix flesh-tone pigment → print → sand to 1500 grit → apply matte clear coat → apply hydrophobic topcoat (see [sweat-proofing.md](sweat-proofing.md))

---

## Where to Buy

### UK Suppliers

| Material | Supplier | Link | Notes |
|----------|----------|------|-------|
| Elegoo Bio Resin | Amazon UK / Elegoo | [elegoo.com](https://www.elegoo.com/) | Fast UK delivery |
| Liqcreate Bio-Med Clear | 3DJake UK | [3djake.uk](https://www.3djake.uk/) | Free shipping over £50 |
| Siraya Tech Tenacious | Amazon UK | [amazon.co.uk](https://www.amazon.co.uk/) | UK stock available |
| Monocure3D pigments | 3DFilaprint | [3dfilaprint.com](https://www.3dfilaprint.com/) | UK-based resin supplier |
| Matte clear coat (Tamiya TS-80) | Hobbycraft, Amazon UK | [hobbycraft.co.uk](https://www.hobbycraft.co.uk/) | Widely available |
| IPA (99%) | Amazon UK, Boots | — | Buy in 5L containers for economy |

### EU Suppliers

| Material | Supplier | Link | Notes |
|----------|----------|------|-------|
| DETAX luxaprint / Freeprint | DETAX direct, dental supply | [detax.de](https://www.detax.de/) | Ships across EU. Also via dental distributors |
| 3Dresyns OTO series | 3Dresyns | [3dresyns.com](https://www.3dresyns.com/) | Spain-based. Ships EU-wide |
| Liqcreate Bio-Med Clear | 3DJake, iGo3D | [3djake.com](https://www.3djake.com/) | EU warehouses |
| Formlabs BioMed resins | Formlabs, 3D Hubs | [formlabs.com](https://www.formlabs.com/) | EU distributor network |

### US Suppliers

| Material | Supplier | Link | Notes |
|----------|----------|------|-------|
| Formlabs BioMed Clear/Flex | Formlabs direct | [formlabs.com](https://www.formlabs.com/) | Direct US sales |
| Siraya Tech Tenacious | Amazon US, Siraya Tech | [siraya.tech](https://www.siraya.tech/) | US-based manufacturer |
| Elegoo Bio Resin | Amazon US, Elegoo | [elegoo.com](https://www.elegoo.com/) | US warehouse |
| Liqcreate Bio-Med Clear | MatterHackers | [matterhackers.com](https://www.matterhackers.com/) | US distributor |

---

## Biocompatibility Testing — Patch Test Protocol

Before wearing any printed shell in your ear for extended periods, perform this skin patch test:

1. **Print a small test disc** (10mm diameter × 2mm thick) using your chosen resin and exact print/cure settings
2. **Wash and cure** the disc using the same post-processing you will use for the final shell
3. **Tape the disc to the inside of your forearm** using medical tape (Micropore or similar)
4. **Wear for 24 hours**
5. **Remove and inspect:** Any redness, itching, swelling, or rash indicates a reaction
6. **If no reaction:** Repeat for 48 hours on a fresh skin area
7. **If still no reaction:** The resin is likely safe for your ear canal, but start with short wear sessions (1 hour, then 4 hours, then 8 hours)

> **If you experience any skin reaction, do not use that resin in your ear.** Try a different resin formulation and repeat the test. Some people are sensitive to specific photoinitiators or monomers. Switching resin brands usually resolves this.

---

## Material Safety

- **Uncured resin is toxic.** Always wear nitrile gloves when handling liquid resin or freshly printed parts. Avoid skin contact, inhalation, and eye contact.
- **IPA is flammable.** Use in a well-ventilated area away from heat sources. Store in sealed containers.
- **UV curing is essential.** A "biocompatible" resin is only biocompatible after full UV post-cure. Undercured resin leaches unreacted monomers that cause irritation.
- **Dust from sanding cured resin** is an inhalant hazard. Wet-sand whenever possible. Wear a dust mask (FFP2/N95 minimum) when dry sanding.
- **Dispose of resin waste responsibly.** Cure waste resin in sunlight before disposal. Do not pour liquid resin down drains.

---

*Next: [sweat-proofing.md](sweat-proofing.md) — making your shell truly moisture-proof.*
