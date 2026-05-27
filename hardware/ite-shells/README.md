# ite-shells/ — Custom In-The-Ear Shells for OpenHear

> *Your ears. Your shell. Your sovereign sound.*

---

## What This Is

This module provides a complete guide to designing, printing, and finishing custom **In-The-Ear (ITE)** hearing aid shells for the OpenHear project. These shells house the full electronics package — microphone, Bluetooth streaming module, battery, and receiver — inside a single custom-fitted unit that sits entirely within your ear.

ITE shells are the natural next step beyond the BTE (Behind-The-Ear) moulds documented in [`hardware/shell/`](../shell/README.md). Where BTE moulds are acoustic couplers for an externally worn device, ITE shells *are* the device. Everything lives inside.

The goal: a shell that feels like skin, repels sweat, resists earwax, lasts for years, and fits your ear — and only your ear — perfectly. All made on a desktop resin printer.

---

## Why Custom ITE Shells?

### Benefits Over Commercial Shells

| Feature | Commercial ITE | OpenHear ITE |
|---------|---------------|--------------|
| **Fit** | Made from your impression by a lab you never visit | Made from your scan, iterated by you until it's perfect |
| **Cost** | £200–£500 per shell from the manufacturer | £5–£15 in resin per shell, unlimited reprints |
| **Material choice** | Whatever the manufacturer uses | You choose biocompatible resin, flexible inserts, coatings |
| **Comfort** | One attempt, maybe one remake | Iterate until it disappears in your ear |
| **Sweat resistance** | Varies, often inadequate | Hydrophobic/omniphobic nano-coatings you apply yourself |
| **Aesthetics** | Limited colour options | Custom flesh-tone pigmentation, matte skin-like finish |
| **Repairability** | Send back to the lab, wait weeks, pay again | Reprint tonight |
| **Transparency** | Black-box process | Full control over every parameter |

### Philosophy

Commercial hearing aid shells are manufactured in centralised labs using proprietary scan-to-shell pipelines. You send an ear impression, a machine processes it, and a shell comes back. You have no input into the material, the wall thickness, the vent design, or the surface finish. If it doesn't fit, you send it back and wait.

OpenHear ITE shells invert this. You scan your own ear. You design the shell in open-source CAD software. You print it on your own printer. You coat it, sand it, test it, and wear it. If something is wrong, you change it and print again. The iteration loop is hours, not weeks.

This is sovereign hardware. You own the scan. You own the design file. You own the process.

---

## End-to-End Workflow Overview

The complete process from bare ear to finished shell:

```
1. Ear Scanning        →  Digital 3D model of your ear canal and concha
2. CAD Design           →  Shell with ports, vents, receiver bore, faceplate
3. Slicing & Printing   →  High-resolution resin print (0.025–0.05mm layers)
4. Post-Processing      →  Wash, cure, sand (1000–2000 grit), polish
5. Sweat-Proofing       →  Hydrophobic/omniphobic nano-coating application
6. Pigmentation         →  Flesh-tone colouring, matte finish
7. Assembly             →  Install OpenHear electronics, seal faceplate
8. Fitting & Testing    →  Comfort checks, acoustic verification, wear testing
```

Each step is documented in detail:

| Step | Guide |
|------|-------|
| Materials selection | [materials.md](materials.md) |
| Sweat-proofing & coatings | [sweat-proofing.md](sweat-proofing.md) |
| Full workflow (scanning → assembly) | [workflow.md](workflow.md) |
| Resources, BOM, links | [resources.md](resources.md) |

---

## Recommended Printers

ITE shells demand high resolution because they sit inside the ear canal where every ridge is felt. SLA and DLP/MSLA resin printers are strongly preferred over FDM for this reason.

### Budget-Friendly (Under £300)

| Printer | Technology | XY Resolution | Layer Height | Build Volume | Price | Notes |
|---------|-----------|---------------|-------------|-------------|-------|-------|
| **Elegoo Mars 4 Ultra** | MSLA | 35μm | 10–200μm | 153×77×165mm | ~£250 | Excellent price-to-precision. Community favourite |
| **Anycubic Photon Mono M5s** | MSLA | 19μm | 10–200μm | 218×123×200mm | ~£280 | Higher resolution LCD. Good for fine ear canal detail |
| **Elegoo Saturn 4 Ultra** | MSLA | 28μm | 10–200μm | 218×123×260mm | ~£300 | Larger build plate — print both shells and test pieces simultaneously |

### Mid-Range (£300–£800)

| Printer | Technology | XY Resolution | Layer Height | Build Volume | Price | Notes |
|---------|-----------|---------------|-------------|-------------|-------|-------|
| **Phrozen Sonic Mini 8K** | MSLA | 22μm | 10–300μm | 165×72×180mm | ~£400 | 8K LCD — extremely fine detail |
| **Anycubic Photon Mono M7** | MSLA | 24μm | 10–200μm | 170×108×200mm | ~£450 | Fast print speeds with high accuracy |

### Professional (£1,000+)

| Printer | Technology | XY Resolution | Layer Height | Build Volume | Price | Notes |
|---------|-----------|---------------|-------------|-------------|-------|-------|
| **Formlabs Form 3B+** | SLA (laser) | 25μm | 25–300μm | 145×145×185mm | ~£3,500 | Medical/dental validated. Best surface finish. Supports Formlabs BioMed resins directly |
| **Formlabs Form 4B** | SLA (MSLA hybrid) | 50μm | 25–200μm | 200×125×210mm | ~£4,500 | Newer platform. Faster than Form 3B+ |
| **SprintRay Pro 55S** | DLP | 49μm | 25–200μm | 192×120×200mm | ~£4,000 | Dental/audiology industry standard |

> **Recommendation:** For most makers, an **Elegoo Mars 4 Ultra** or **Anycubic Photon Mono M5s** at 0.03–0.05mm layer height produces shells that are indistinguishable in fit quality from professional lab shells. You do not need a Formlabs machine to make excellent ITE shells.

---

## ITE Shell Anatomy

An ITE shell is more than a hollow shape. It has specific functional features:

```
                    ┌─────────────────────┐
                    │     FACEPLATE       │  ← Removable cover for battery access
                    │  ┌───┐  ┌───┐      │
                    │  │MIC│  │VOL│      │  ← Microphone port, volume control
                    │  └───┘  └───┘      │
                    ├─────────────────────┤
                    │                     │
                    │   SHELL BODY        │  ← Custom-fitted to concha
                    │                     │
                    │   ┌─────────┐       │
                    │   │BATTERY  │       │  ← Battery compartment
                    │   └─────────┘       │
                    │                     │
                    │   ┌───────────────┐ │
                    │   │   RECEIVER    │ │  ← Balanced armature speaker
                    │   │   BORE       ─┼─┤  ← Sound output to ear canal
                    │   └───────────────┘ │
                    │        ║            │
                    │   ═════╝  VENT     ─┼─┤  ← Pressure equalisation channel
                    │                     │
                    └──────── CANAL TIP ──┘  ← Extends into ear canal
```

### Key Features

| Feature | Purpose | Typical Dimensions |
|---------|---------|-------------------|
| **Shell body** | Houses all electronics, custom-fitted to concha | 1.2–2.0mm wall thickness |
| **Canal portion** | Extends into ear canal for acoustic seal and retention | 8–15mm length, follows canal curvature |
| **Faceplate** | Removable cover on the lateral (outer) face | 0.8–1.2mm thickness, snap-fit or friction-fit |
| **Receiver bore** | Channel for balanced armature speaker | 2.5–2.8mm diameter (see [materials in shell/](../shell/parametric_mould.md)) |
| **Vent channel** | Pressure equalisation, reduces occlusion | 0.8–2.5mm diameter (depends on hearing loss) |
| **Microphone port** | Opening for MEMS microphone | 1.0–1.5mm diameter, with wind guard recess |
| **Battery compartment** | Houses rechargeable LiPo cell | Sized to battery (typically 10×20×3mm for 100mAh) |
| **Wire routing channels** | Internal paths for connecting components | 1.0–1.5mm diameter |
| **Wax guard recess** | Holds replaceable cerumen filter at canal tip | 2.0mm diameter, 1.5mm depth |

---

## Safety & Legal Disclaimers

> **⚠️ EXPERIMENTAL PROJECT — NOT A MEDICAL DEVICE**
>
> OpenHear ITE shells are experimental personal projects. They have **not** been evaluated, approved, or cleared by any regulatory body (FDA, MHRA, CE/UKCA, TGA, or equivalent).
>
> In most jurisdictions, custom hearing aid shells fall under **Class II medical device** regulations when sold or distributed commercially. OpenHear shells are for **personal, experimental use only** and are not sold, distributed, or prescribed.

### Before You Build

1. **Consult an audiologist.** Get a professional hearing assessment. Know your audiogram. Understand your hearing loss type and severity before building any hearing device.

2. **Understand the risks.** Inserting any object into your ear canal carries risks including irritation, infection, allergic reaction, wax impaction, and in extreme cases, eardrum damage. Read the [safety module](../safety/README.md) completely.

3. **Test biocompatibility.** Even resins labelled "biocompatible" can cause reactions in sensitive individuals. Always perform a skin patch test (see [materials.md](materials.md)) before extended ear canal contact.

4. **Never exceed safe sound levels.** The [hardware MPO limiter](../safety/README.md) is mandatory for any powered ITE device. It caps maximum output regardless of software settings.

5. **Use at your own risk.** The authors of this guide are not responsible for any injury, hearing damage, allergic reaction, or other adverse outcome. This is an open-source project, not a medical product.

### Regulatory Context

| Jurisdiction | Relevant Regulation | Classification | Notes |
|-------------|-------------------|----------------|-------|
| UK | Medical Devices Regulations 2002 (as amended) | Class II (if sold) | Personal-use builds are not regulated as medical devices |
| EU | MDR 2017/745 | Class IIa (if placed on market) | Same — personal builds exempt from CE marking |
| USA | FDA 21 CFR Part 874 | Class II (if sold) | OTC hearing aid rules (2022) may apply to self-fit devices |
| Australia | TGA — Therapeutic Goods Act 1989 | Class IIa (if supplied) | Personal use is not "supply" under the Act |

> **This project does not constitute placing a medical device on the market.** You are building a device for your own personal use. However, if you make shells for others — even for free — you may be subject to medical device regulations in your jurisdiction. Do not distribute shells without understanding local laws.

---

## Getting Started

1. Read the [safety module](../safety/README.md). Non-negotiable.
2. Review [materials.md](materials.md) and choose your resin.
3. Follow the [workflow.md](workflow.md) step by step.
4. Apply sweat-proofing from [sweat-proofing.md](sweat-proofing.md).
5. Assemble with OpenHear electronics per the [assembly guide](../assembly/README.md).
6. Calibrate per the [safety module](../safety/README.md) before first powered use.

---

## Contributing

If you have printed ITE shells — share your experience. Open an issue with:
- Your printer model and resin
- Your post-processing workflow
- Fit quality and comfort notes
- Photos (if you are comfortable sharing)

Every data point makes the next person's shell better. That's the point.

---

*This module is part of [OpenHear](../../README.md) — sovereign audio for sovereign people.*
*MIT Licensed.*
