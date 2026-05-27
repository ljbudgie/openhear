# shell/ — 3D Printed Custom Ear Moulds

This guide walks you through making custom ear moulds for your OpenHear hearing aid. Custom moulds matter because they create an acoustic seal between the receiver (speaker) and your ear canal. A good seal means better bass response, less feedback, and all-day comfort. A bad seal means whistling, tinny sound, and a device you take out after an hour.

Every ear is different. That's the whole point of custom moulds.

---

## Overview of the Process

1. Take ear impressions with medical silicone
2. Scan the impressions to create 3D models (STL files)
3. Prepare the STL in Meshmixer or Blender (add vent channel, receiver bore, sound tube)
4. Print on a resin printer at 0.05mm layer height
5. Post-process (wash, cure, sand)
6. Fit, test, and iterate

Total time: 2–3 days including print time and cure time. Active work: about 4–6 hours spread across those days.

---

## Step 1: Taking Ear Impressions

You are making a physical copy of your ear canal and concha (the bowl-shaped part of your outer ear). This is done with two-part medical-grade silicone that you mix and inject into your ear.

### What You Need

- Two-part medical silicone ear impression kit (available on Amazon, ~£15)
- Foam ear dams (otoblock) — these should be included in the kit
- Otoscope or penlight (to check ear canal is clear of wax)
- A helper — do not do this alone

### ⚠️ Safety Warnings

> **Do not skip the foam dam.** The foam dam (otoblock) sits in your ear canal before the silicone. It prevents silicone from going too deep. Without it, silicone can reach your eardrum and cause serious injury.

> **Do not insert anything into your ear canal if you have pain, infection, discharge, or a perforated eardrum.** See a clinician first.

> **Have someone help you.** You cannot see your own ear canal. A helper can position the foam dam correctly and inject the silicone evenly.

> **Maximum insertion depth:** The foam dam should sit at the second bend of the ear canal, approximately 15–20mm from the canal entrance. If you are unsure, use a shorter impression. A short impression is safe. A too-deep impression is dangerous.

### Technique

1. **Check the ear canal** with an otoscope or penlight. It should be clean and free of excessive wax. If you see a wax blockage, have it removed by a professional before proceeding.

2. **Insert the foam dam.** Using the included insertion tool, gently place the foam dam into the ear canal. It should sit snugly at the second bend. You should feel mild pressure but no pain. If it hurts, stop and reposition.

3. **Mix the silicone.** Follow the kit instructions — typically equal parts base and catalyst, mixed for 30 seconds until the colour is uniform. You have about 2–3 minutes of working time before it sets.

4. **Inject into the ear.** Using the syringe, fill the ear canal from the foam dam outward. Fill the concha (bowl of the ear) completely. Overfill slightly — you can trim excess later.

5. **Hold still for 5 minutes.** The silicone needs to fully cure. Don't talk, chew, or move your jaw.

6. **Remove by pulling down and out** on the earlobe while gently wiggling the impression. It should come out in one piece. If it tears, redo it — a torn impression will produce a bad scan.

7. **Inspect the impression.** You should see clear detail of the ear canal, the concha, and the helix. The canal portion should be at least 10mm long. If it's too short, the mould won't seal properly.

8. **Repeat for the other ear.**

---

## Step 2: Scanning Impressions

Convert your physical silicone impressions into 3D digital models (STL files).

### Recommended Scanning Apps

| App | Platform | Cost | Notes |
|-----|----------|------|-------|
| [Polycam](https://poly.cam/) | iOS (LiDAR) | Free tier available | Best results with iPhone 12 Pro or newer. Use LiDAR mode, not photo mode |
| [Qlone](https://www.qlone.pro/) | iOS / Android | Free with watermark | Use the printed scanning mat for best results |
| [Kiri Engine](https://www.kiriengine.com/) | iOS / Android | Free tier available | Cloud processing, works with any phone camera |

### Scanning Tips

- Place the impression on a contrasting background (white impression on dark surface)
- Use even, diffuse lighting — avoid harsh shadows
- Scan slowly, overlapping each angle
- Capture at least 50 photos / angles for photogrammetry apps
- Export as STL or OBJ format

### Alternative: Desktop 3D Scanner

If you have access to a desktop 3D scanner (e.g., Revopoint POP, Creality CR-Scan), use it. Desktop scanners produce more accurate results than phone-based photogrammetry, especially for the small details of the ear canal.

---

## Step 3: Preparing the STL

The raw scan gives you the outer shape of your ear. You now need to add internal channels for the receiver (speaker), vent (pressure equalisation), and sound tube.

### Software Options

| Software | Cost | Notes |
|----------|------|-------|
| [Meshmixer](https://meshmixer.com/) | Free | Best for boolean operations on organic shapes. Recommended |
| [Blender](https://www.blender.org/) | Free | More powerful but steeper learning curve |

### Operations

1. **Clean the scan.** Remove any scanning artifacts, fill small holes, smooth rough surfaces. In Meshmixer: Edit → Make Solid → Smooth.

2. **Trim to mould shape.** Cut the impression to the correct length — you want the canal portion plus enough concha to anchor the mould in your ear. Leave 2–3mm of margin.

3. **Hollow the mould.** The mould should be a shell, not a solid block. Target wall thickness: 1.5–2.0mm. In Meshmixer: Edit → Hollow.

4. **Add the receiver bore.** This is the hole where the balanced armature receiver sits. See [parametric_mould.md](parametric_mould.md) for exact dimensions based on your receiver model. The bore runs from the tip of the canal portion to a pocket where the receiver body sits.

5. **Add the vent channel.** The vent equalises pressure and reduces the occlusion effect (the "plugged up" feeling). Vent size depends on your hearing loss — see the vent sizing guide below. The vent runs parallel to the receiver bore, from the canal tip to the outer surface of the mould.

6. **Add the sound tube channel.** If using a sound tube instead of a direct receiver, add a 1.93mm ID channel (standard #13 tubing). See [parametric_mould.md](parametric_mould.md) for details.

7. **Export as STL** at maximum resolution for printing.

### Vent Sizing Guide

The vent channel equalises pressure between the sealed ear canal and the outside. Larger vents reduce the occlusion effect but also reduce bass amplification (low-frequency sound leaks out through the vent). Choose based on your hearing loss:

| Hearing Loss | Vent Diameter | Vent Type | Rationale |
|-------------|---------------|-----------|-----------|
| Severe-to-profound (71+ dB) | 0.8mm | Pressure vent | Maximum seal. You need all the bass amplification you can get. The small vent only equalises static pressure |
| Moderate (41–70 dB) | 1.5mm | Standard vent | Balance between seal and comfort. Some bass leakage is acceptable |
| Mild (26–40 dB) | 2.5mm | Open vent | Comfort is more important than seal. Natural bass hearing is mostly intact. Larger vent reduces occlusion |

### Receiver Bore Dimensions

The receiver (balanced armature speaker) sits inside the mould. The bore must be sized to fit the specific receiver model with a snug fit.

| Receiver | Bore Diameter | Bore Length | Notes |
|----------|--------------|-------------|-------|
| Knowles ED-29689 | 2.5mm | 8.0mm | 0.1mm tolerance. Friction fit — no adhesive needed if sized correctly |
| Knowles WBFK-30019 | 2.8mm | 9.5mm | 0.1mm tolerance |
| Knowles WBFK-30095 | 2.8mm | 9.5mm | Same housing as WBFK-30019 |

---

## Step 4: Printing

### Recommended Printers

| Printer | Resolution | Build Volume | Price | Notes |
|---------|-----------|-------------|-------|-------|
| Elegoo Mars 4 | 0.05mm (50μm) | 132×74×150mm | ~£200 | Recommended. Good resolution for ear moulds |
| Anycubic Photon Mono 2 | 0.05mm | 143×89×165mm | ~£180 | Good alternative |
| FormLabs Form 3 | 0.025mm | 145×145×185mm | ~£2500 | Professional quality. Overkill for most users |

### Resin Selection

**You must use biocompatible resin for anything that contacts your skin or ear canal.**

| Resin | Type | Skin Contact | Price | Notes |
|-------|------|-------------|-------|-------|
| Elegoo Bio Resin | Plant-based, Class I biocompatible | Yes (after full UV cure) | ~£40/500ml | Recommended. Low odour, easy to work with |
| FormLabs BioMed Clear | Class I biocompatible | Yes | ~£150/L | Medical grade. Expensive |
| Siraya Tech Tenacious | Flexible, biocompatible | Yes (after full cure) | ~£50/500ml | Good for comfort — slightly flexible moulds |

> **Warning:** Standard resin (not labelled biocompatible) can cause skin irritation, allergic reactions, or chemical burns. Do not use standard resin for ear moulds. This is not optional.

### Print Settings

- **Layer height:** 0.05mm (50μm) — this gives a smooth surface that won't irritate the ear canal
- **Exposure time:** Per resin manufacturer's recommendation (typically 2–3 seconds per layer)
- **Bottom exposure:** Per manufacturer (typically 30–45 seconds for first 5 layers)
- **Orientation:** Print the mould at 45° angle with the canal tip pointing up. This minimises support marks on the canal surface
- **Supports:** Light supports only. Remove support contact points from canal surface before fitting

---

## Step 5: Post-Processing

### Washing

1. Remove the print from the build plate
2. Wash in **99% IPA (isopropyl alcohol)** for 3–5 minutes. Use an ultrasonic cleaner or agitate by hand
3. Rinse with fresh IPA
4. Air dry completely (10–15 minutes)

> **Wear nitrile gloves.** Uncured resin is a skin irritant. Do not touch the print with bare hands until after UV curing.

### UV Curing

1. Place the washed, dry print in a UV curing station (405nm)
2. Cure for the time specified by your resin manufacturer (typically 10–30 minutes)
3. Rotate the print halfway through for even curing
4. **The mould must be fully cured before any skin contact.** Undercured resin is not biocompatible regardless of what it says on the bottle

### Sanding

1. Sand any rough spots with 400-grit wet sandpaper
2. Follow with 800-grit for a smooth finish
3. Pay special attention to the canal portion — any roughness will cause discomfort
4. The surface should feel smooth and polished when you run your fingernail across it

---

## Step 6: Fitting and Testing

### First Fit

1. **Inspect the mould** for sharp edges, rough surfaces, or printing artifacts. Sand anything that doesn't feel smooth
2. **Insert gently.** The mould should slide in with light pressure. If it requires force, it's too tight — sand down or reprint
3. **Check the seal.** With the mould inserted, you should feel a slight reduction in ambient sound (occlusion). If you hear normally, the seal is poor — the mould may be too loose or the canal portion too short
4. **Check comfort immediately.** Any pain means remove it and investigate. Pain is never acceptable

### Wear Testing

| Duration | What to Check |
|----------|---------------|
| 1 hour | Comfort, seal quality, any pressure points |
| 4 hours | Sustained comfort, any developing soreness, any itching (possible resin sensitivity) |
| 8 hours | Full-day wearability, moisture buildup, any loosening |

### Iteration

This is normal. Most people need 2–3 iterations to get the fit right.

| Problem | Fix |
|---------|-----|
| Too tight (pain, pressure) | Sand down the canal portion by 0.1–0.2mm, or reprint with 0.2mm offset |
| Too loose (falls out, poor seal) | Reprint with -0.1mm offset (slightly larger), or add a thin layer of medical-grade silicone |
| Feedback (whistling) | Usually means a seal leak. Check for gaps between mould and ear canal. May need a longer canal portion |
| Occlusion (own voice sounds boomy) | Increase vent diameter by 0.5mm. This trades some bass amplification for comfort |
| Itching after extended wear | Check that resin is fully cured. Re-cure under UV for 30 more minutes. If itching persists, try a different resin — you may be sensitive to this formulation |
| Discomfort at one specific point | Mark the pressure point on the mould with a marker, remove, and sand that specific area |

---

## Safety Reminders

- **Never force a mould into your ear.** If it doesn't fit easily, sand it down or reprint.
- **Maximum canal depth:** The mould canal should not extend deeper than 15mm past the canal entrance. Deeper insertion risks contact with the eardrum.
- **Inspect before every use.** Check for cracks, rough spots, or degradation. Replace any mould that shows wear.
- **Clean regularly.** Wipe with IPA or mild soap and water after each use. Allow to dry fully before reinserting.
- **Replace every 6–12 months**, or sooner if the fit changes or the mould shows degradation.
