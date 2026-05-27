# Workflow — Ear Scan to Finished ITE Shell

> Every step, every parameter, every tool. No mystery, no gatekeeping.

This guide takes you from a bare ear to a complete, coated, assembled ITE shell ready for OpenHear electronics. Each step includes recommended tools, parameters, and troubleshooting.

---

## Prerequisites

Before you start, ensure you have:

- [ ] Read the [safety module](../safety/README.md) completely
- [ ] A resin 3D printer (SLA/MSLA/DLP) with ≤50μm XY resolution
- [ ] Biocompatible resin (see [materials.md](materials.md))
- [ ] 99% IPA, nitrile gloves, UV curing station
- [ ] Sandpaper: 400, 800, 1000, 1500, 2000 grit (wet/dry)
- [ ] A method for ear scanning (phone with LiDAR or photogrammetry app, or silicone impression kit)
- [ ] CAD software installed (Blender, Fusion 360, or Meshmixer)
- [ ] OpenHear electronics ready for assembly (see [BOM](../BOM.md))

---

## Step 1: Ear Scanning

You need a 3D model of your ear canal and concha. There are three approaches, from simplest to most accurate.

### Option A: Smartphone LiDAR Scan (Quickest)

**Requirements:** iPhone 12 Pro or newer (or iPad Pro with LiDAR)

| App | Platform | Cost | Best For |
|-----|----------|------|----------|
| [Polycam](https://poly.cam/) | iOS | Free tier | Quick scans with LiDAR mode |
| [Scaniverse](https://scaniverse.com/) | iOS | Free | Good mesh quality, easy export |
| [3d Scanner App](https://apps.apple.com/app/3d-scanner-app/id1419913995) | iOS | Free | Direct STL/OBJ export |

**Procedure:**

1. Ensure your ear is clean and free of excessive wax
2. Open the scanning app in LiDAR mode
3. Hold the phone 10–15cm from your ear
4. Slowly move around the ear, capturing the concha, tragus, and as much of the ear canal entrance as visible
5. Export as STL or OBJ file

> **Limitation:** LiDAR cannot scan inside the ear canal. The canal portion of your shell will need to be estimated or based on a silicone impression scan. For an ITE shell, this method alone is usually insufficient — use it for the concha shape and combine with an impression scan for the canal.

### Option B: Silicone Impression + Photogrammetry (Most Accurate)

**Requirements:** Silicone impression kit (~£15), any smartphone

This is the method used by professional hearing aid labs and is recommended for ITE shells.

1. **Take a silicone ear impression** — follow the complete procedure in [shell/README.md](../shell/README.md#step-1-taking-ear-impressions). All safety warnings apply.

2. **Scan the impression** using photogrammetry:

   **Using a Smartphone:**

   | App | Platform | Cost | Notes |
   |-----|----------|------|-------|
   | [Polycam](https://poly.cam/) | iOS / Android | Free tier | Photo mode (not LiDAR) — take 50–80 overlapping photos |
   | [Kiri Engine](https://www.kiriengine.com/) | iOS / Android | Free tier | Cloud-processed photogrammetry. Good detail |
   | [Meshroom](https://alicevision.org/#meshroom) | Desktop (Win/Linux) | Free, open-source | Best quality free photogrammetry. Process photos on your PC |

   **Scanning Tips:**
   - Place the impression on a contrasting surface (dark mat for light silicone)
   - Use soft, diffuse lighting — avoid harsh shadows
   - Photograph from every angle, overlapping each shot by 60–70%
   - Include close-ups of the canal portion
   - Take at least 50 photos for Polycam/Kiri, 80+ for Meshroom
   - Export as STL at maximum resolution

3. **Alternative: Desktop 3D Scanner**

   If available, a structured-light desktop scanner produces the best results:

   | Scanner | Resolution | Price | Notes |
   |---------|-----------|-------|-------|
   | Revopoint MINI 2 | 0.02mm | ~£400 | Excellent for small objects. Best affordable option for impressions |
   | Creality CR-Scan Raptor | 0.02mm | ~£500 | Good quality, large scanning volume |
   | Revopoint RANGE 2 | 0.1mm | ~£700 | Higher range but lower resolution — adequate for ear impressions |

### Option C: Photogrammetry Replication from Existing Shell Photos (No Impression Needed)

If you already have a well-fitting hearing aid shell (commercial or custom), you can replicate it using photogrammetry without taking a new ear impression.

**Requirements:** Any smartphone (iOS or Android), your existing well-fitting shell, good lighting

**Why this works:** Your existing shell already represents a validated fit. Replicating its geometry gives you a starting point that you know is comfortable, which you can then modify in CAD.

**Exact 100+ Photo Technique:**

1. **Prepare the shell**
   - Clean the shell thoroughly with IPA
   - Place it on a contrasting surface (dark mat for light shell, white paper for dark shell)
   - Mark 3–4 small reference dots on the shell with a fine-tip marker (helps photogrammetry alignment)
   - Ensure soft, diffuse lighting — no harsh shadows (overcast daylight or a ring light works well)

2. **Capture sequence** (aim for 100–120 photos minimum)

   | Ring | Angle from horizontal | Number of photos | Spacing |
   |------|----------------------|------------------|---------|
   | Ring 1 (top) | 70–80° (nearly overhead) | 12–16 | Every 22–30° around the shell |
   | Ring 2 (high) | 50–60° | 16–20 | Every 18–22° |
   | Ring 3 (mid) | 30–40° | 20–24 | Every 15–18° |
   | Ring 4 (low) | 10–20° | 20–24 | Every 15–18° |
   | Ring 5 (level) | 0° (eye level) | 16–20 | Every 18–22° |
   | Close-ups | Various | 16–20 | Focus on canal tip, vent, mic ports, faceplate edge |

   - Move around the shell in each ring, keeping the shell centred in frame
   - Overlap each photo by 60–70% with its neighbours
   - Keep the phone at the same distance within each ring (~15cm for close rings, ~25cm for wider rings)
   - Do NOT move the shell between photos — move yourself

3. **Process with photogrammetry software**

   | Software | Platform | Cost | Notes |
   |----------|----------|------|-------|
   | [Polycam](https://poly.cam/) | iOS / Android | Free tier | Photo mode — upload all photos, process on device or cloud |
   | [Scaniverse](https://scaniverse.com/) | iOS | Free | Good mesh quality from photos |
   | [Kiri Engine](https://www.kiriengine.com/) | iOS / Android | Free tier | Cloud-processed, good detail |
   | [Meshroom](https://alicevision.org/#meshroom) | Desktop (Win/Linux) | Free, open-source | Best quality. Process on your PC with GPU |
   | [COLMAP](https://colmap.github.io/) | Desktop | Free, open-source | Research-grade. Requires more setup |

4. **Post-processing the scan**
   - Import the mesh into Meshmixer or Blender
   - Clean up noise, fill holes, smooth artefacts
   - Scale-calibrate: measure your original shell with callipers and scale the mesh to match (critical for fit accuracy)
   - The result is a watertight STL that replicates your existing shell geometry

5. **Modify and improve**
   - Open the replicated shell in your CAD tool
   - Adjust wall thickness, vent size, mic port positions using the parametric approach (see [parametric_shell.scad](parametric_shell.scad))
   - Add features from the OpenHear design that your commercial shell lacks (better venting, lotus-effect microstructures, etc.)
   - Print and iterate

> **Tip:** This method is especially useful if your commercial shell fits well but you want to add OpenHear-specific features (better venting, sweat-proofing microstructures, custom faceplate) without starting from scratch.

### Option D: OpenScan DIY Photogrammetry Rig (Budget-Friendly)

**Requirements:** Raspberry Pi, Pi Camera, 3D printed turntable

The [OpenScan](https://www.openscan.eu/) project provides open-source plans for a photogrammetry turntable that automates the scanning process.

1. Build or buy an OpenScan Mini turntable (~£80 for the kit, or print your own)
2. Place the silicone impression on the turntable
3. The OpenScan software automatically captures photos at every angle
4. Process with OpenScan Cloud or Meshroom
5. Export as STL

---

## Step 2: CAD Design — Shell Modelling

### Software Options

| Software | Cost | Skill Level | Best For |
|----------|------|------------|---------|
| [Blender](https://www.blender.org/) | Free, open-source | Intermediate | Organic shape editing, boolean operations, STL repair |
| [Meshmixer](https://meshmixer.com/) | Free | Beginner | Mesh hollowing, boolean subtract, support generation |
| [Fusion 360](https://www.autodesk.com/products/fusion-360/personal) | Free (personal use) | Intermediate | Parametric design, precise measurements, history-based modelling |
| [FreeCAD](https://www.freecadweb.org/) | Free, open-source | Intermediate | Parametric design. Community add-ons for mesh operations |
| [OpenSCAD](https://openscad.org/) | Free, open-source | Beginner (code-based) | Parametric templates, reproducible designs |

### Workflow in Blender (Recommended)

#### 2a. Import and Clean the Scan

1. **Import STL:** File → Import → STL
2. **Inspect mesh quality:** Tab into Edit Mode. Look for non-manifold edges (Select → All by Trait → Non-Manifold)
3. **Repair mesh:** Use Mesh → Clean Up → Fill Holes and Merge by Distance to fix common scan issues
4. **Smooth the surface:** Apply a Smooth modifier (factor: 0.5, iterations: 2–5) to remove scan noise without losing ear anatomy detail
5. **Scale check:** Verify dimensions match your physical impression. The canal should measure 8–15mm in length, concha bowl ~18–25mm across

#### 2b. Create the Shell Body

1. **Duplicate the mesh** (Shift+D) — keep the original as a reference
2. **Offset inward** to create wall thickness:
   - Select all faces → Mesh → Extrude → Shrink/Fatten → type `-1.5` (for 1.5mm wall thickness)
   - Or use the **Solidify modifier** with thickness: 1.5mm, offset: -1 (inward)
3. **Trim the shell** to the correct boundary — the shell should cover the concha and extend into the canal, but not cover the entire ear
4. **Create the faceplate opening** — cut the lateral (outer) face flat to accept a removable faceplate

#### 2c. Add Internal Features

Refer to [shell/parametric_mould.md](../shell/parametric_mould.md) for exact channel dimensions.

| Feature | Method | Dimensions |
|---------|--------|-----------|
| **Receiver bore** | Boolean subtract a cylinder along canal axis | 2.5mm dia × 8mm (ED-29689) or 2.8mm × 9.5mm (WBFK series) |
| **Vent channel** | Boolean subtract a cylinder parallel to receiver bore | 0.8–2.5mm dia (see [vent sizing](../shell/README.md#vent-sizing-guide)) |
| **Battery compartment** | Boolean subtract a rectangular pocket | Sized to your LiPo cell (e.g., 10×20×3mm for 100mAh) |
| **Microphone port** | Boolean subtract a small cylinder through the faceplate area | 1.0–1.5mm dia |
| **Wire routing** | Boolean subtract 1.2mm channels connecting component pockets | Route to avoid sharp bends |
| **Wax guard recess** | Boolean subtract a shallow cylinder at the canal tip | 2.0mm dia × 1.5mm deep |

#### 2d. Design the Faceplate

The faceplate is the removable outer cover that provides access to the battery and electronics.

1. **Extract the faceplate outline** from the shell opening
2. **Extrude to 0.8–1.2mm thickness**
3. **Add a friction-fit rim** (0.3mm overlap on each side) or snap-fit clips
4. **Add the microphone port hole** and any button/control openings
5. **Export faceplate as a separate STL** — it prints separately from the shell body

### Parametric Templates (OpenSCAD)

For users who prefer code-based parametric design, the following OpenSCAD template creates the internal channel geometry. Import your ear scan as an STL and boolean-subtract these channels:

```openscad
// OpenHear ITE Shell — Internal Channel Template
// Customise parameters below, then boolean-subtract from your ear scan

/* [Receiver Bore] */
receiver_dia = 2.5;        // mm — 2.5 for ED-29689, 2.8 for WBFK
receiver_length = 8.0;     // mm — 8.0 for ED-29689, 9.5 for WBFK
receiver_tolerance = 0.1;  // mm — manufacturing tolerance

/* [Vent Channel] */
vent_dia = 1.5;            // mm — 0.8 pressure, 1.5 standard, 2.5 open
vent_offset = 2.0;         // mm — centre-to-centre distance from receiver bore

/* [Wire Channel] */
wire_dia = 1.2;            // mm
wire_length = 15;          // mm — adjust to shell depth

/* [Wax Guard Recess] */
wax_guard_dia = 2.0;       // mm
wax_guard_depth = 1.5;     // mm

/* [Battery Compartment] */
battery_x = 10;            // mm
battery_y = 20;            // mm
battery_z = 3;             // mm — adjust to your LiPo cell

// Receiver bore
module receiver_bore() {
    cylinder(d = receiver_dia + receiver_tolerance,
             h = receiver_length, $fn = 64);
}

// Vent channel
module vent_channel() {
    translate([vent_offset, 0, 0])
        cylinder(d = vent_dia, h = receiver_length + 5, $fn = 64);
}

// Wire channel
module wire_channel() {
    translate([0, receiver_dia / 2 + 1, receiver_length])
        rotate([0, 90, 0])
            cylinder(d = wire_dia, h = wire_length, $fn = 32);
}

// Wax guard recess
module wax_guard() {
    cylinder(d = wax_guard_dia, h = wax_guard_depth, $fn = 64);
}

// Battery pocket
module battery_pocket() {
    translate([-battery_x / 2, -battery_y / 2, receiver_length + 2])
        cube([battery_x, battery_y, battery_z]);
}

// Combined subtraction volume
module all_channels() {
    receiver_bore();
    vent_channel();
    wire_channel();
    wax_guard();
    battery_pocket();
}

// Preview — shows what will be subtracted
all_channels();
```

> **Usage:** Import your scanned ear shell STL into OpenSCAD using `import("my_ear_shell.stl")`, then `difference()` it with `all_channels()`. Adjust the parameters at the top to match your receiver model and hearing loss severity.

### Finding Existing Templates

Several community-shared designs can accelerate your workflow:

| Resource | Link | Notes |
|----------|------|-------|
| GrabCAD — ITE shell models | [grabcad.com](https://grabcad.com/library?query=hearing+aid+shell) | Search for "hearing aid shell" or "ITE shell" |
| Printables — ear mould designs | [printables.com](https://www.printables.com/search/models?q=ear+mould) | Community-contributed parametric moulds |
| Thingiverse — hearing aid shells | [thingiverse.com](https://www.thingiverse.com/search?q=hearing+aid) | Older but useful reference designs |
| NIH 3D Print Exchange | [3dprint.nih.gov](https://3dprint.nih.gov/) | Some medical ear models available |

---

## Step 3: Slicing & Printing

### Slicer Software

| Slicer | Compatible Printers | Cost | Notes |
|--------|-------------------|------|-------|
| **ChiTuBox** | Most MSLA (Elegoo, Anycubic, Phrozen) | Free (Basic) | Industry standard for resin printing. Good support generation |
| **Lychee Slicer** | Most MSLA | Free (Basic) | Excellent support placement, clean UI |
| **PreForm** | Formlabs only | Free (with printer) | Best auto-orientation and supports for Formlabs printers |
| **UVtools** | Most MSLA | Free, open-source | Advanced layer inspection and repair |

### Recommended Print Settings

```
Printer Type:    MSLA / SLA resin printer
Layer Height:    0.03–0.05mm (30–50μm)
                 Use 0.03mm for final shells, 0.05mm for test prints

Exposure Time:   Per resin datasheet (typical: 2.0–3.0s for 0.05mm layers)
                 Increase by 10–20% if using pigmented resin

Bottom Layers:   5–8 layers
Bottom Exposure: Per resin datasheet (typical: 25–40s)

Lift Speed:      1.0–2.0 mm/s (slow = fewer failures, better detail)
Lift Height:     6–8mm

Orientation:     45° angle, canal tip pointing UP
                 This minimises support marks on the ear-contact surfaces

Supports:        Light supports (0.3–0.4mm tip diameter)
                 Place supports on the OUTER (faceplate) side of the shell
                 Avoid supports on the canal surface — marks cause discomfort
                 Use at least 3 heavy supports on the base for adhesion

Hollowing:       NOT needed — your CAD model should already be hollow
                 If slicing a solid model, use slicer hollowing at 1.5mm wall
                 Add 2 drain holes (1.5mm) for uncured resin to escape
```

### Print Orientation Diagram

```
Build Plate (bottom)
    |
    |   ╱ Heavy supports (base adhesion)
    |  ╱
    | ╱
    |╱
    ╲────────────────╲
     ╲  FACEPLATE     ╲     ← Faceplate faces down (toward build plate)
      ╲  (outer face)  ╲
       ╲────────────────╲
        ╲                ╲
         ╲  SHELL BODY    ╲   ← Shell body at 45° angle
          ╲                ╲
           ╲────────────────╲
            ╲                ╲
             ╲  CANAL TIP     ╲  ← Canal tip points UP (away from plate)
              ╲________________╲
                                 ↑
                         Light supports only on outer surface
```

This orientation ensures:
- The canal surface (which touches your skin) has minimal support contact points
- Layer lines run at 45° to the canal axis — smoother feel than horizontal lines
- Overhangs on the canal are self-supporting at 45°

---

## Step 4: Post-Processing

### 4a. Washing

1. **Remove the print** from the build plate with a plastic scraper (not metal — metal scratches the surface)
2. **First wash:** Submerge in 99% IPA for 3 minutes. Agitate gently or use an ultrasonic cleaner
3. **Second wash:** Transfer to fresh IPA for 2 minutes
4. **Precision cleaning:** Use a soft brush or compressed air to clear uncured resin from the receiver bore, vent channel, and wire routing channels
5. **Rinse** with clean IPA
6. **Air dry** for 15–20 minutes. Ensure no IPA remains in internal channels

> **Wear nitrile gloves throughout.** Uncured resin is a skin sensitiser.

### 4b. UV Curing

1. **Place the shell** in a 405nm UV curing station
2. **Cure for the time specified** by your resin manufacturer — typically:
   - Rigid biocompatible resins: 15–30 minutes
   - Flexible resins: 10–20 minutes (over-curing makes flex resins brittle)
3. **Rotate halfway through** for even curing
4. **Post-cure in warm water** (60°C) for additional 15 minutes if using Formlabs BioMed resins — per Formlabs instructions
5. **Verify cure:** The surface should be completely dry and non-tacky. If sticky, cure for 10 more minutes

> **Critical: The shell is not biocompatible until fully cured.** Do not touch with bare skin or insert into your ear until curing is complete.

### 4c. Support Removal

1. **Clip supports** at the base with flush cutters
2. **Sand support contact points** flush with the surface
3. **Inspect the canal surface** for any support marks — these must be completely smooth

### 4d. Sanding (Progressive)

This is the most important step for comfort. A poorly sanded shell feels like sandpaper in your ear.

| Grit | Method | Purpose |
|------|--------|---------|
| 400 | Wet-sand with water | Remove support nubs and major imperfections |
| 800 | Wet-sand with water | Smooth layer lines and surface roughness |
| 1000 | Wet-sand with water | Further smoothing — most ridges eliminated |
| 1500 | Wet-sand with water | Near-polished surface — feels smooth to fingertip |
| 2000 | Wet-sand with water | Final finish — glass-smooth. Feels like skin against skin |

**Sanding technique:**
- Always wet-sand resin (prevents dust, gives smoother finish)
- Use small pieces of sandpaper wrapped around your finger for the canal portion
- Sand in circular motions, not back-and-forth
- Rinse frequently to check progress
- Pay extra attention to the canal tip (deepest insertion point) — this area must be flawless

### 4e. Polishing (Optional)

For a high-gloss finish (skip if you want matte):

1. Apply a small amount of plastic polish (Novus #2 or equivalent) to a soft cloth
2. Buff the shell surface in circular motions
3. Wipe clean

> **For a matte skin-like finish:** Stop at 1500–2000 grit sanding and do NOT polish. The matte surface feels more natural against skin than a glossy finish and provides better coating adhesion.

---

## Step 5: Pigmentation (Skin-Tone Colouring)

See [materials.md — Pigmentation](materials.md#pigmentation--skin-tone-matching) for full details.

### Quick Summary

**Best method:** Pre-mix pigment into resin before printing (1–2% by weight).

**If printing in clear/white resin:**
1. Sand to 1500 grit
2. Apply flesh-tone airbrushed paint (2–3 thin coats)
3. Allow to dry fully (30 minutes between coats)
4. Apply matte clear coat (Tamiya TS-80 or equivalent)
5. Proceed to sweat-proofing

---

## Step 6: Sweat-Proofing & Coating

See [sweat-proofing.md](sweat-proofing.md) for full details.

### Quick Summary

1. Clean the finished shell with 99% IPA
2. Mask acoustic openings (mic port, vent, receiver bore) with Kapton tape
3. Apply hydrophobic/omniphobic coating (2 thin coats)
4. Allow to cure per manufacturer instructions
5. Remove masking
6. Verify with water bead test

---

## Step 7: Assembly with OpenHear Electronics

### Component Placement

| Component | Location in Shell | Connection | Notes |
|-----------|------------------|------------|-------|
| **Balanced armature receiver** | Receiver bore (canal tip) | Wire to Tympan output | Friction-fit. Sound output faces ear canal |
| **MEMS microphone** | Behind mic port in faceplate area | Wire to Tympan input | Ensure port is not blocked by coating |
| **Rechargeable LiPo battery** | Battery compartment | JST connector to Tympan | 100–150mAh for ITE form factor |
| **Tympan board** (or custom PCB) | Main shell cavity | All connections | May need modified mounting for ITE |
| **Volume control / button** | Faceplate | Wire to Tympan GPIO | Optional — can use phone app instead |

### Assembly Procedure

1. **Test-fit all components** in the shell before any adhesive. Verify that everything fits within the cavity with the faceplate closed

2. **Route wires** through the wire channels. Use 30 AWG silicone-insulated wire for flexibility. Leave 5mm of service loop at each connection

3. **Secure the receiver** in the bore. It should friction-fit. If loose, apply a tiny amount of medical-grade cyanoacrylate around the edge (not on the sound output)

4. **Install the microphone** behind the mic port. Secure with a small drop of adhesive. Verify the port is clear of debris

5. **Connect the battery.** Verify polarity before connecting to the Tympan. Secure the battery in its compartment with a small piece of foam tape

6. **Connect all wires to the Tympan board.** Follow the pinout in the [Tympan module](../tympan/README.md)

7. **Power on and verify basic function** before closing the faceplate:
   - Audio pass-through works
   - Receiver produces sound
   - Microphone picks up voice
   - Battery charges correctly

8. **Close the faceplate.** Verify it sits flush and the friction/snap fit holds

9. **Final acoustic test** — see the [safety module](../safety/README.md) for the complete calibration procedure

### Faceplate Sealing

The faceplate seam should be moisture-resistant but not permanently sealed (you need battery access).

| Method | Removal | Moisture Seal | Notes |
|--------|---------|--------------|-------|
| **Friction fit** (0.3mm interference) | Easy | Moderate | Simplest. May loosen over months. Reprint if too loose |
| **Silicone gasket** (0.5mm O-ring or silicone bead) | Easy | Good | Apply a thin bead of medical silicone around the faceplate rim |
| **Snap-fit clips** (2–4 small clips designed into the shell) | Moderate | Moderate | Requires careful CAD design. Very secure |
| **Magnetic closure** (2mm × 1mm neodymium magnets) | Easy | Moderate | Glue magnets into shell and faceplate. Satisfying snap closure |

---

## Step 8: Fitting, Testing & Iteration

### First Fit Checklist

```
□ Shell is fully cured, sanded, coated, and dry
□ All electronics are powered off for first physical fit
□ Insert the shell gently — it should slide in with light pressure
□ No pain at any point during insertion
□ Shell sits flush with the ear — not protruding significantly
□ Faceplate is accessible for removal
□ Shell does not fall out when you tilt your head or open your jaw
□ Occlusion effect present (own voice sounds boomy) — indicates good seal
□ No sharp edges felt anywhere
```

### Powered Testing (After First Fit is Comfortable)

1. **Power on at minimum gain**
2. **Gradually increase gain** while listening for:
   - Feedback (whistling) — indicates seal leak. Check canal fit
   - Distortion — check receiver placement
   - Uneven frequency response — may need DSP adjustment
3. **Run the MPO verification** from the [safety module](../safety/README.md) — **mandatory before extended wear**

### Wear Schedule

| Day | Duration | Activity |
|-----|----------|----------|
| Day 1 | 1 hour | Quiet environment. Note any discomfort |
| Day 2 | 2 hours | Normal conversation. Check voice quality |
| Day 3 | 4 hours | Mixed environments. Note any fatigue or soreness |
| Day 4–5 | 6 hours | Extended wear. Check for moisture buildup |
| Day 6–7 | 8+ hours | Full-day wear. This is your target |

### Common Issues and Fixes

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| Pain at a specific point | Shell pressing on a bony prominence | Mark the spot, sand 0.1–0.2mm at that point |
| Falls out easily | Canal portion too short or too narrow | Reprint with longer canal or -0.1mm offset |
| Feedback (whistling) | Air leak around canal | Check fit. May need longer canal or different vent size |
| Own voice too boomy | Occlusion from tight seal | Increase vent diameter by 0.5mm |
| Itching after 2+ hours | Resin sensitivity or inadequate curing | Re-cure under UV for 30 min. If persistent, try different resin |
| Difficulty removing | Canal portion too tight | Sand canal walls 0.1–0.2mm. Apply thin silicone lubricant |
| Moisture buildup inside | Inadequate venting or coating failure | Check vent patency. Reapply hydrophobic coating |

### Iteration

Most people need **2–3 print iterations** to get a perfect fit. This is normal and expected.

Each iteration, note what changed and why:

```
Iteration 1: Prototype fit. Canal too tight at second bend. Solution: sand 0.2mm.
Iteration 2: Comfort improved. Faceplate too loose. Solution: increase rim overlap 0.1mm.
Iteration 3: Final fit. All checks pass. Proceed to coating and assembly.
```

Keep all iteration STL files with version numbers (e.g., `left_shell_v1.stl`, `left_shell_v2.stl`). The cost per print is £2–£5 in resin — iteration is cheap.

---

## Summary Workflow Checklist

```
□ Step 1: Ear scan — digital 3D model acquired
□ Step 2: CAD design — shell body, channels, faceplate modelled
□ Step 3: Slicing — orientation, supports, settings configured
□ Step 4: Printing — shell printed on resin printer
□ Step 5: Post-processing — wash, cure, sand to 2000 grit
□ Step 6: Pigmentation — flesh tone applied (optional)
□ Step 7: Sweat-proofing — hydrophobic coating applied
□ Step 8: Assembly — electronics installed and tested
□ Step 9: Fitting — comfort verified over progressive wear schedule
□ Step 10: Calibration — MPO verified per safety module
□ DONE: Your sovereign ITE shell is ready
```

---

*Next: [resources.md](resources.md) — links, BOM, and community resources.*
