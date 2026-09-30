# Freedom-to-operate note — Sonitus / SoundBite family

**This is a working director note, not legal advice.**
It exists so OpenHear contributors do not publish an oral-appliance design
that walks onto live claims. Before any tooth-mounted, intra-oral, or
dental-acrylic hardware is described in this tree, instruct a UK patent
attorney to update this file against current registers.

Last public-register pass: 30 September 2026.

## What SoundBite is

Sonitus Medical (San Mateo) shipped the SoundBite Hearing System: a
behind-the-ear microphone plus a removable in-the-mouth transducer that
couples vibration into a back tooth so bone conduction reaches the cochleae
without surgery. FDA-cleared for single-sided deafness and conductive loss.
The US company ceased operations in 2015 after a CMS coverage decision.
IP later moved Soundmed LLC → **Sonitus Medical (Shanghai) Co., Ltd.**, which
still markets a dental bone-conduction system and states a large patent
family across ~22 countries. The **SOUNDBITE** word mark remains registered
in the US (s.8 & 15 accepted October 2024).

Bone conduction itself is not theirs. Teeth-as-coupler *products* are.

## Live claims that matter to this repo

Treat as **live until an attorney says otherwise**:

| Family / number | What it covers (plain) | Why it matters |
|---|---|---|
| US 11,696,080 B2 (granted 4 Jul 2023; priority 12 Jun 2020; assignee Sonitus Medical Shanghai) | Bone-conduction aid: housing, piezoelectric vibration assembly, vibration transmission element, vibration output portion that outputs vibration through contact | New hardware family, not the 2006 US wind-down |
| EP 3 952 342 B1 (granted 20 Sep 2023; GB designated) | Same Shanghai bone-conduction device family | UK/EP exposure if we ship a contact transducer that looks like the claim |
| SOUNDBITE trade mark | Word mark, Class 10 | Do not use the name on hardware, docs-as-product, or domain |
| Shanghai company statements | “130+ patents, 22 countries”; NMPA / FDA / CE history | Assume more CN/JP/US filings exist than this table lists |

Some **2006-priority US grants** in the original Abolfathi / Sonitus Medical
Inc. family have **lapsed for non-payment of maintenance fees** in late 2025
and 2026 (example: US 8,585,575 B2 lapsed Dec 2025). A lapse in one number
is **not** a dead family. Continuations, EP/GB designations, and the 2020
Shanghai grants are a separate problem. Do not treat “Sonitus Inc. died in
2015” as clearance.

## What OpenHear will publish

Safe in this tree (signal path, not appliance):

- Audiogram-driven gain for a **bone-conduction output pathway**
  (`dsp/bone_conduction.py`, `docs/BONE_CONDUCTION_PATHWAY.md`).
- Using **bone-conduction thresholds** as the cochlear target when the
  person has them, otherwise air-conduction thresholds.
- A generic transducer-compensation table labelled as ours, not a copied
  SoundBite EQ.
- Single-sided-deafness **routing** (dead-side mic → better-cochlea BC
  output). Contralateral routing is older than SoundBite (CROS, 1960s).
- Coupling sites named as **mastoid, forehead, implant abutment, or
  unspecified**. Oral is named only as a reserved, unpublished option.

## What OpenHear will not publish until counsel signs off

Do not add CAD, STL, dental-acrylic recipes, tooth-bracket geometry,
molar-clasp drawings, “custom fit around upper back teeth” claims,
ITM + BTE system diagrams that reproduce the SoundBite split, or marketing
that says OpenHear *is* SoundBite / Molar Mic / 品音.

The folder `modules/optional/oral_appliance/` is a hold, not a kit.

## Director rule

The Burgess Principle Limited publishes this repository. Contributors copy
what they see. An oral-appliance file that lands here is an exhibit.
Keep the exhibit empty until a named attorney has applied their mind to the
specific claims above and written that the proposed drawing does not fall
inside them.
