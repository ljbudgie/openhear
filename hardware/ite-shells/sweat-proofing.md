# Sweat-Proofing & Moisture Resistance — ITE Shells

> Your ear canal is a warm, humid, waxy environment. Your shell needs to survive it.

This guide covers every method for making your ITE shell resistant to sweat, earwax (cerumen), and moisture. A well-protected shell stays clean, lasts longer, and feels better against your skin.

---

## Why Sweat-Proofing Matters

The human ear canal maintains ~37°C and 60–80% relative humidity. It produces cerumen (earwax) continuously. During exercise, the temperature and moisture increase further. An untreated resin shell will:

- Absorb sweat and oil into surface micropores
- Develop a biofilm (bacterial/fungal colonisation) over weeks
- Discolour and develop odour
- Become harder to clean as contaminants penetrate the surface
- Degrade mechanically as absorbed moisture weakens the cured polymer

A properly treated shell repels all of this. Water beads up. Earwax slides off. Cleaning is a wipe, not a scrub.

---

## Method 1: Post-Print Hydrophobic / Omniphobic Nano-Coatings

The most effective and accessible approach. Apply a thin chemical coating that makes the shell surface repel water, oils, and biological fluids.

### Recommended Coatings

| Coating | Type | Water Contact Angle | Oil Resistant | Durability | Application | Price | Notes |
|---------|------|-------------------|---------------|-----------|-------------|-------|-------|
| **Nasiol NanoHearShield** | Fluoropolymer nano-coating | >110° | Yes | 6–12 months | Spray / wipe | ~£25/50mL | Purpose-made for hearing aids. Biocompatible top layer |
| **NANOMYTE SR-500HP** | Fluorinated silane SAM | >115° | Yes (omniphobic) | 12+ months | Dip / spray | ~£60/100mL | Industrial-grade. Medical device compatible. Exceptional longevity |
| **Aculon NanoProof** | Fluorinated polymer | >105° | Moderate | 6–12 months | Spray | ~£30/30mL | Designed for electronics. Protects shell and internal components |
| **NeverWet Industrial** | Superhydrophobic silicone | >160° | No (hydrophobic only) | 3–6 months | Two-part spray | ~£15/kit | Budget option. Very high water repellency but does not resist oils/earwax |
| **Glaco Mirror Coat Zero** | Fluoropolymer glass coating | >110° | Moderate | 3–6 months | Wipe-on | ~£12/bottle | Originally for car glass. Works well on smooth resin. Easy to apply |
| **Medical-grade fluoropolymer (P2i-style)** | Plasma-deposited fluoropolymer | >120° | Yes (omniphobic) | 2+ years | Vacuum plasma chamber | £5–£10/unit via service | Professional service only. Extremely durable but requires sending shells to a coating service |

> **Best choice for most makers:** **Nasiol NanoHearShield** or **Glaco Mirror Coat Zero** — both are easy to apply at home, affordable, and provide good sweat and earwax resistance. Reapply every 3–6 months.
>
> **Best professional-grade option:** **NANOMYTE SR-500HP** — exceptional omniphobic performance that resists both water and oils (including earwax).

### Step-by-Step Application Guide

#### Materials Needed

- Your fully cured, sanded, and cleaned ITE shell
- Chosen hydrophobic coating
- Nitrile gloves
- Lint-free microfibre cloth
- 99% IPA for surface preparation
- Well-ventilated workspace (or outdoors)
- Small paintbrush or cotton swab for precision areas

#### Procedure

1. **Surface preparation**
   - The shell must be fully UV-cured, sanded (minimum 800 grit), and completely clean
   - Wipe the entire shell with 99% IPA on a lint-free cloth
   - Allow to dry completely (5 minutes minimum)
   - Do not touch the surface with bare fingers after cleaning — oils from skin interfere with coating adhesion

2. **Mask electronics openings** (if shell is already assembled)
   - Cover microphone ports, vent openings, and receiver bore with small pieces of Kapton tape or Blu Tack
   - The coating must not block acoustic openings

3. **Apply the coating**
   - **Spray coatings** (NeverWet, Aculon): Hold 15–20cm away, apply a thin, even coat. Two light passes are better than one heavy pass. Allow 1 minute between passes.
   - **Wipe-on coatings** (Glaco, Nasiol): Apply a thin layer with the applicator or a lint-free cloth. Spread evenly. Remove excess immediately.
   - **Dip coatings** (NANOMYTE): Submerge the shell in the solution for 30 seconds. Remove slowly and allow to drip-dry vertically for 2 minutes.

4. **Cure the coating**
   - Most coatings cure at room temperature in 1–24 hours
   - Place the coated shell in a dust-free area, elevated on a rack or wire stand
   - Do not handle until the manufacturer's recommended cure time has elapsed
   - Some coatings (NANOMYTE) benefit from a 30-minute heat cure at 60°C in a domestic oven — check the product datasheet

5. **Remove masking tape/Blu Tack** from all openings

6. **Inspect and test** (see [Testing Methods](#testing-methods) below)

#### Safety Notes

- **Most hydrophobic coatings contain fluorinated compounds or silicone solvents.** Work in a well-ventilated area or outdoors. Wear nitrile gloves. Avoid inhalation of spray mist.
- **Do not spray near open flames.** Many carrier solvents are flammable.
- **Dispose of applicator cloths and gloves as chemical waste.** Do not put solvent-soaked materials in general waste bins.
- **Keep coatings away from eyes.** If eye contact occurs, rinse with clean water for 15 minutes and seek medical advice.

---

## Method 2: Built-In Microstructure (Re-Entrant Surfaces)

Advanced technique that uses the 3D printer itself to create hydrophobic surface textures — no coating needed.

### How It Works

Certain surface geometries — called "re-entrant" structures — trap air pockets that prevent liquid from wetting the surface. Think of a lotus leaf: the surface is covered in microscopic pillars that prevent water from making full contact. Water sits on top of the trapped air and rolls off.

Resin printers at 25–50μm XY resolution can approximate these structures by adding microscale texture to the STL file before printing.

### Implementation

1. **Generate a micro-pillar texture** in CAD software:
   - Pillar diameter: 50–100μm
   - Pillar height: 50–100μm
   - Pillar spacing: 100–200μm (centre to centre)
   - Arrangement: hexagonal grid for optimal packing

2. **Apply as a surface modifier** to the external surfaces of the shell STL:
   - In Blender: use a displacement modifier with a procedural texture
   - In OpenSCAD: create a module that generates a pillar array and subtract/union with shell surface

3. **Print at maximum resolution** (0.025–0.035mm layer height) to resolve the pillars

> **Limitations:**
> - Requires very high-resolution printer (sub-35μm XY)
> - Micropillars are fragile and wear down with handling
> - Less effective than chemical coatings for oil/earwax resistance
> - Best used in combination with a chemical coating for maximum performance
>
> **Recommendation:** Micro-texturing is an interesting experiment but is not a replacement for chemical coatings. Use it as an additional layer of protection if your printer can resolve the features.

---

## Method 3: Sealing / Impregnation (Porosity Reduction)

Cured resin has microscopic pores, especially at layer lines. These pores absorb moisture and harbour bacteria. Sealing them improves both hygiene and coating adhesion.

### Recommended Sealants

| Sealant | Type | Application | Effect | Price | Notes |
|---------|------|------------|--------|-------|-------|
| **dichtol AM Hydro** | Impregnation resin | Dip / vacuum impregnation | Fills micropores, creates sealed surface | ~€40/250mL | Purpose-designed for 3D printed parts. Excellent for resin prints |
| **UV-cure clear coat (resin)** | Thin UV resin | Brush / spray | Fills surface pores, adds gloss or matte (with matting agent) | ~£15/100mL | Use the same biocompatible resin you printed with, thinned with a small amount of IPA |
| **Polyurethane conformal coat** | Spray / dip PU coating | Spray thin coat, air cure | Seals surface, adds chemical resistance | ~£10/spray can | MG Chemicals 4223 or equivalent. Good for electronic protection too |

### Application Process (dichtol AM Hydro)

1. **Submerge the cured and sanded shell** in dichtol AM Hydro for 2–5 minutes
2. **Remove and wipe excess** with a lint-free cloth
3. **UV cure** under 405nm light for 10 minutes
4. **The surface is now sealed** — micropores are filled with cured polymer
5. Apply hydrophobic coating on top for maximum protection

### Self-Sealing with Print Resin

A simpler alternative that requires no extra materials:

1. **Thin your biocompatible resin** with 10% IPA by volume (e.g., 9mL resin + 1mL IPA)
2. **Brush a thin coat** over the sanded shell surface with a fine brush
3. **UV cure** for 10 minutes under 405nm
4. **Sand lightly** (2000 grit) to remove any brush marks
5. The thinned resin fills micropores and creates a sealed, smooth base for coating

---

## Earwax (Cerumen) Resistance

Earwax is a mixture of lipids, fatty acids, cholesterol, and dead skin cells. It is more challenging to repel than water because it is oily and viscous.

### Strategies

| Strategy | Implementation | Effectiveness |
|----------|---------------|---------------|
| **Omniphobic coating** | Use NANOMYTE SR-500HP or equivalent fluorinated coating that repels both water AND oils | ★★★★★ — Best option |
| **Smooth surface finish** | Sand to 2000 grit + polish. Wax cannot mechanically grip a smooth surface | ★★★★☆ — Very good as a baseline |
| **Oleophobic top coat** | Apply fluoropolymer coating (same as anti-fingerprint phone screen coatings) | ★★★★☆ — Effective, reapply every 3 months |
| **Replaceable wax guard** | Install a standard cerumen filter (e.g., Phonak CeruShield Disc) at the receiver bore exit | ★★★★★ — Industry standard. Replace monthly |
| **Wax-resistant geometry** | Design the canal tip with a slight flare (1–2° taper) so wax cannot accumulate in corners | ★★★☆☆ — Helpful but not sufficient alone |

> **Recommended combination:** Smooth surface (2000 grit) + omniphobic nano-coating + replaceable wax guard at receiver port. This three-layer approach provides excellent long-term wax resistance.

---

## Anti-Bacterial / Anti-Fungal Properties

The warm, moist ear canal is an ideal environment for microbial growth. Reducing bacterial adhesion on the shell surface is important for hygiene and comfort.

### Options

| Method | Implementation | Notes |
|--------|---------------|-------|
| **Silver nanoparticle additive** | Mix colloidal silver solution (10–50 ppm) into resin at 0.5–1% by weight before printing | Well-studied antimicrobial. Does not affect resin cure. Adds slight yellow tint |
| **Copper-infused resin** | Use copper-particle-containing resin or add copper powder at 1% by weight | Copper is naturally antimicrobial. Adds metallic appearance |
| **Antimicrobial spray** | Apply BioCote or Microban antimicrobial spray to cured surface | Surface-level protection. Reapply monthly |
| **Regular cleaning** | Wipe with 70% IPA or antibacterial hearing aid wipes after each use | Simplest and most reliable method |

> **Recommendation:** Do not overthink antimicrobial additives. **Regular cleaning with IPA wipes after each use** is more effective than any built-in antimicrobial treatment. The coating and smooth surface make cleaning easy — that's the real win.

---

## Testing Methods

After applying any coating or treatment, verify its performance:

### 1. Water Bead Test (Hydrophobicity)

1. Place the coated shell on a flat surface
2. Apply a single drop of water from a pipette (or squeeze bottle) onto the shell surface
3. **Pass criteria:** The water drop forms a round bead with a visible contact angle >90° (the drop sits on the surface rather than spreading flat)
4. **Excellent performance:** Contact angle >110° — the drop rolls off when the shell is tilted 15–20°

### 2. Sweat Simulation Test

Prepare simulated sweat solution:

```
Simulated Eccrine Sweat (ISO 105-E04 simplified)
- 5g NaCl (table salt)
- 1g urea (available from garden supply or pharmacy)
- 1000mL distilled water
- Mix until dissolved
```

1. Apply several drops of the simulated sweat to the coated shell
2. Tilt the shell at 45°
3. **Pass criteria:** Liquid runs off cleanly without leaving residue or wet patches
4. **Leave a pool of simulated sweat on the surface for 1 hour.** Wipe off and inspect — there should be no visible absorption, staining, or surface change

### 3. Oil/Earwax Resistance Test

1. Apply a thin smear of petroleum jelly (Vaseline) — a reasonable earwax substitute — to the coated surface
2. Wait 10 minutes
3. Wipe with a dry cloth
4. **Pass criteria:** The petroleum jelly wipes away cleanly with minimal effort. No residue visible on the surface

### 4. Durability Simulation

1. Submerge the coated shell in warm water (37°C) with a drop of washing-up liquid for 1 hour — this simulates warm, soapy cleaning
2. Remove, rinse, and dry
3. Repeat the water bead test
4. **Pass criteria:** Water beading performance is unchanged after the submersion
5. Repeat 10 times to simulate weeks of daily cleaning

### 5. Wear Test (Final Validation)

1. Wear the treated shell in your ear for 4 hours during normal activity
2. Remove and inspect the surface under good light
3. **Pass criteria:** No visible moisture absorption, discolouration, or surface degradation. Earwax (if present) wipes off easily

---

## Maintenance & Reapplication Schedule

| Coating Type | Reapplication Interval | How to Reapply |
|-------------|----------------------|----------------|
| NeverWet | Every 3–4 months | Clean shell with IPA → re-spray |
| Glaco Mirror Coat Zero | Every 3–6 months | Clean shell with IPA → re-wipe |
| Nasiol NanoHearShield | Every 6–12 months | Clean shell with IPA → re-spray |
| NANOMYTE SR-500HP | Every 12+ months | Clean shell with IPA → re-dip |
| P2i plasma coating | Every 2+ years | Send shell to P2i coating service |

> **Signs you need to reapply:** Water no longer beads on the surface. Earwax becomes harder to wipe off. The shell surface feels "grippy" instead of slick.

---

## Quick-Reference Sweat-Proofing Checklist

```
□ Shell fully UV-cured
□ Sanded to 1500–2000 grit (smooth, matte finish)
□ Cleaned with 99% IPA, dried completely
□ (Optional) Sealed with dichtol AM Hydro or resin self-seal
□ Acoustic openings masked with Kapton tape / Blu Tack
□ Hydrophobic/omniphobic coating applied (2 thin coats)
□ Coating cured per manufacturer instructions
□ Masking removed from all openings
□ Water bead test: PASS
□ Oil/wax resistance test: PASS
□ Wear test (4 hours): PASS
□ Reapplication date noted in calendar
```

---

*Next: [workflow.md](workflow.md) — the full build process from ear scan to finished shell.*
