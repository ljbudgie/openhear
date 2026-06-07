# REGEN_VISION.md — OpenHear and the Regenerative Future of Hearing

> **⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE. NOT A BIOLOGICAL THERAPY.**
> OpenHear does **not** regenerate biology. It does not repair hair cells,
> spiral ganglion neurons, the otoferlin pathway, or any other inner-ear
> structure. OpenHear is a sovereign software-and-haptics layer that
> **maximises residual function, substitutes missing channels, and trains
> and monitors** the user. Biological hearing regeneration, where it is
> possible at all, requires clinical gene or cell therapy delivered and
> supervised by qualified clinicians. This document describes how OpenHear
> can be the best possible *supportive* layer around those therapies — never
> a replacement for them.

**Status:** Draft v0.1 · Evidence cut-off: June 2026 · Author: Lewis James
Burgess · Built on the [Burgess Principle](docs/BURGESS_PRINCIPLE.md).

**Scope discipline used throughout this document.** Every claim is tagged
as one of:

- **[APPROVED]** — cleared by at least one major regulator and in clinical use.
- **[CLINICAL]** — in human trials, results published, not yet broadly approved.
- **[PRECLINICAL]** — animal or in-vitro evidence only.
- **[OPENHEAR]** — a capability of this project; assistive, not biological.
- **[ASPIRATION]** — a stated goal with no current evidence base; flagged as such.

---

## 1. One-paragraph summary

As of June 2026, biological hearing restoration is **real but narrow**: a
single gene-therapy indication (biallelic *OTOF* / otoferlin loss) is
approved, and everything else remains research-stage. OpenHear's role is
unchanged by this and made *more* valuable by it: OpenHear is the sovereign,
user-owned layer that (a) maximises whatever hearing a person has today,
(b) substitutes missing channels through haptics and the social acoustic
layer, and (c) produces the **baseline, training, and outcome data** that a
person and their clinicians need before, during, and after any biological
intervention. OpenHear is the scaffolding around the surgery, not the
surgery.

---

## 2. State of hearing regeneration — June 2026

### 2.1 Approved: OTOF gene therapy — Otarmeni (lunsotogene parvec-cwha) **[APPROVED]**

| Attribute | Detail |
|-----------|--------|
| Product | **Otarmeni™ (lunsotogene parvec-cwha)**, formerly **DB-OTO** (Regeneron) |
| Regulatory status | **FDA accelerated approval, April 2026** — first gene therapy for genetic hearing loss; first approval to restore a neurosensory function toward normal in humans |
| Indication | Severe-to-profound sensorineural hearing loss caused by **biallelic *OTOF* (otoferlin) mutations** |
| Eligibility | Confirmed biallelic *OTOF* genotype; **preserved hair-cell anatomy** (otoferlin loss is a *synaptic* defect, so hair cells are typically present); **no prior cochlear implant in the treated ear** |
| Mechanism | AAV-delivered functional *OTOF* coding sequence restores otoferlin, the protein that enables calcium-triggered neurotransmitter release at the inner-hair-cell ribbon synapse. (Because *OTOF* exceeds single-AAV packaging limits, a **dual-AAV** split-vector approach is used.) |
| Delivery | Surgical intracochlear administration via the round window under general anaesthesia |
| Outcomes (CHORD Ph1/2) | **~80%** of participants reached the primary hearing threshold endpoint by ~week 24; **~40%** reached near-normal hearing in follow-up; gains were rapid in responders and durable to date |
| Safety | No serious therapy-related adverse events reported; most adverse events procedural (ear pain, transient vestibular symptoms) |
| Access | Regeneron announced provision free of charge in the U.S. for eligible patients at launch |

**Other OTOF programmes [CLINICAL]:** Eli Lilly / Akouos **AK-OTOF**
(NCT05821959, Ph1/2, U.S., completion ~2028; early single-patient hearing
restoration reported) and several academic AAV-*OTOF* trials (notably
multi-centre work in China) reporting bilateral benefit in children and at
least one adult. These corroborate the mechanism but are **not** broadly
approved.

> **Critical scope note for OpenHear users.** *OTOF* deafness is a special
> case: the sensory hair cells are usually **intact**, so the therapy
> repairs a *signalling* defect, not a *structural* one. This is why it
> works so well — and why its success does **not** generalise to most
> congenital profound deafness, where hair cells and/or neurons are absent
> or degenerated. See §3.

### 2.2 Research-stage approaches **[PRECLINICAL] / early [CLINICAL]**

| Approach | What it targets | Status (June 2026) | Key challenges |
|----------|-----------------|--------------------|----------------|
| **Hair-cell regeneration via supporting-cell reprogramming** | Recreating lost sensory hair cells (e.g. Atoh1-driven or Wnt/Notch-modulated transdifferentiation; small-molecule + gene combinations) | Mostly preclinical; prior small human trials of single-pathway approaches did not show meaningful functional hearing | Producing cells that are correctly *patterned* (tonotopy), polarised, and **synaptically connected**; transient vs durable conversion |
| **Stem / progenitor cell therapy for SGN (neuron) repair** | Replacing or protecting **spiral ganglion neurons**, the wire from cochlea to brain | Preclinical, with isolated early-phase human work | **Reinnervation** — new or transplanted neurons must grow to the correct targets and form functional, tonotopically ordered synapses |
| **Combination strategies** | Hair cells **and** neurons **and** synapses together | Preclinical | Orchestration; each component is individually unsolved at scale |
| **Other monogenic gene therapies** (e.g. *GJB2*/connexin-26, *TMC1*, *STRC*) | Specific non-OTOF genetic deafnesses | Mostly preclinical; some entering early trials | Each gene is a separate program, target cell, and delivery problem; many exceed single-AAV capacity |

**Cross-cutting challenges** for everything beyond OTOF: delivery
efficiency and cell-type specificity; durable integration; correct
tonotopic patterning; reinnervation and synaptogenesis; immune response to
vector or transplanted cells; and the **critical-period / central-plasticity
problem** in congenital cases (§3).

### 2.3 Honest summary table

| Question | Answer (June 2026) |
|----------|--------------------|
| Can genetic deafness be treated? | **Only the *OTOF* indication is approved.** Others are research-stage. |
| Can hair cells be regrown in humans today? | **No** approved therapy. Preclinical only. |
| Can auditory neurons be replaced in humans today? | **No** approved therapy. Preclinical only. |
| Does any of this restore hearing in a congenitally, profoundly deaf adult without an *OTOF* genotype? | **No evidence of this today.** See §3. |
| Does OpenHear regenerate any of this? | **No. Never. By design.** |

---

## 3. Congenital profound SNHL — why it is the hard case

The OpenHear creator is **profoundly deaf since birth, bilateral
sensorineural**. This section is deliberately specific to that situation and
deliberately unsentimental.

**Developmental vs acquired loss.** A person who lost hearing after years of
auditory experience has an auditory cortex that was *wired by sound*.
Restoring the periphery reconnects to existing central machinery. A person
deaf **from birth** never had that input during the **critical period** of
auditory-cortex development, so the central auditory pathways may be
under-developed or **cross-wired** to vision and somatosensation. Restoring
peripheral signal in adulthood does **not** automatically produce
intelligible hearing; the brain must learn to use a signal it was never
tuned for.

**The reinnervation bottleneck.** Even a perfectly regenerated hair cell is
useless without an intact, correctly targeted **spiral ganglion neuron**
carrying its signal to the brainstem in tonotopic order. In many congenital
profound cases both the sensory cells **and** the neural wiring are affected.
Regenerating one without the other does not restore function.

**Implications — stated plainly:**

1. For most congenital profound deafness **without** an *OTOF* genotype,
   there is **no approved biological restoration today**, and the central
   critical-period problem means future therapies will likely need to be
   paired with **intensive, sustained perceptual training**.
2. **Genetic diagnosis is decisive.** Whether *any* current therapy applies
   depends entirely on etiology. The first actionable step for any deaf
   person curious about regeneration is a **genetic and structural
   diagnosis**, not a device.
3. This is exactly where an assistive + training + monitoring layer earns
   its place. If a future therapy ever becomes available, the people most
   likely to benefit are those who arrive with **trained multisensory
   pathways, documented baselines, and the habit of structured auditory
   learning** — all of which OpenHear can build *now*, with no biological
   claim attached.

---

## 4. Requirements checklist for successful biological regeneration

A neutral, evidence-based checklist. OpenHear contributes only to the rows
marked **[OPENHEAR]**; it cannot satisfy the biological rows.

| # | Requirement | Why it matters | OpenHear contribution |
|---|-------------|----------------|-----------------------|
| 1 | **Etiology diagnosis** (genotype + structural imaging) | Determines whether any therapy applies at all | **[OPENHEAR]** Sovereign storage/export of audiograms, functional baselines, and history to bring to genetic counselling |
| 2 | **Viable target structures** (hair cells and/or SGNs present or regrowable) | Therapy needs something to act on or restore | None (biological) — but OpenHear functional metrics may *flag* candidates worth imaging |
| 3 | **Delivery** to the correct cells at sufficient efficiency | Vector/cells must reach inner-hair-cell or neuron targets | None (clinical/surgical) |
| 4 | **Integration** — correct tonotopy, polarity, synaptogenesis, reinnervation | A signal in the wrong place is noise | None (biological) |
| 5 | **Plasticity / training** to interpret restored signal | Especially decisive in congenital cases (§3) | **[OPENHEAR]** Adaptive training modes, frequency/neuroplasticity protocols, progress tracking |
| 6 | **Safety & durability** (immune response, longevity, reversibility) | Determines real-world benefit/risk | **[OPENHEAR]** Local, user-owned outcome and adverse-event logging for clinical sharing |

---

## 5. OpenHear's supportive role — pre- and post-intervention

OpenHear is **modality-agnostic and therapy-agnostic**. It does the same
sovereign job whether a person never has biological intervention, is waiting
for one, or has just had one.

### 5.1 Pre-intervention **[OPENHEAR]**

- **Baseline capture.** Detailed audiograms, speech-in-noise scores,
  functional listening logs, and haptic-perception baselines, all
  user-owned and exportable for genetic counselling and surgical workup.
- **Multisensory readiness.** Haptic substitution and frequency-training
  protocols build cross-modal pathways and listening habits *before* any
  signal exists to interpret — directly addressing the §3 plasticity
  problem.
- **Decision support, not medical advice.** OpenHear surfaces a person's own
  data so they can have a better-informed conversation with clinicians. It
  does **not** diagnose, recommend therapy, or predict eligibility.

### 5.2 Post-intervention **[OPENHEAR]**

- **Outcome tracking.** Longitudinal speech-in-noise, threshold, and
  real-world participation metrics to quantify benefit and detect drift.
- **Adaptive rehabilitation.** Training modes tuned to a *newly restored or
  changing* periphery — progressive band unlocks, fatigue-aware pacing, and
  social-context practice during the plasticity window.
- **Hybrid operation.** If a person has partial biological hearing plus
  residual gaps, OpenHear's DSP + haptic restoration mapping fills the gaps
  without claiming to have created the biology.

### 5.3 Mapping to existing OpenHear subsystems

| Existing subsystem | Regeneration-support function |
|--------------------|-------------------------------|
| DSP pipeline (`dsp/`) | Maximises residual/restored acoustic hearing; gap-fills partial restoration |
| Haptic / wristband (`haptic_commander.py`, `wristband/`, `hardware/`) | Multisensory substitution and pre/post-intervention re-learning |
| Social acoustic layer | Real-world conversational practice during plasticity windows |
| Therapy / frequency protocols (`therapy/`, `learn/`) | Structured, fatigue-aware perceptual training |
| Advocacy layer (`advocacy/`) | Sovereign, verifiable export of baselines and outcomes for clinical sharing |
| Whoop / wearable integration | Physiological context (recovery, stress) to pace training safely |

---

## 6. "Regeneration-ready" — what OpenHear must add or refine

Capabilities required for OpenHear to be maximally supportive of a
regenerative future. All are **[OPENHEAR]** assistive features; none is a
biological claim.

1. **Baseline & outcome logging engine.** Standardised, timestamped capture
   of audiograms, speech-in-noise, haptic-perception, and functional-listening
   metrics with versioned history.
2. **Adaptive training modes** tied to the existing neuroplasticity/frequency
   work, with explicit fatigue scoring and rest logic, plus pre- and
   post-intervention variants.
3. **Social acoustic layer extensions** for structured real-world practice
   during plasticity windows (trusted-contact voice profiles, graded
   difficulty, session capture).
4. **Haptic re-learning maps** that can be re-pointed as a person's
   biological hearing changes (partial restoration → shifting restoration
   map).
5. **Sovereign data architecture** — encrypted, user-controlled export of
   detailed audiograms, functional metrics, and session logs for clinical
   sharing or personal audit, using the existing SHA-256 / canonical-JSON
   commitment model (Git-style or crypto-verifiable, offline, no vendor).
6. **Modular / hybrid interfaces** — clean abstraction boundaries so OpenHear
   can sit alongside (never inside) implants or future delivery systems
   without vendor lock-in.
7. **"Social + training" profiles** — reusable profiles optimised either for
   post-regeneration adaptation or for general maximisation in users with no
   intervention.
8. **Claim-standard tooling** — language templates and a lint-style check
   that keep documentation precise (functional gains + sovereignty, never
   biological cure).

---

## 7. Phased roadmap

Milestones are deliberately measurable. Success metrics include
speech-in-noise score deltas, social-participation measures, training
adherence, and a **user-sovereignty score** (proportion of data/models/
profiles fully owned and exportable by the user with no vendor dependency).

### Short-term (3–6 months)

| Milestone | Success metric | Integration point |
|-----------|----------------|-------------------|
| Baseline/outcome logging schema v1 | Captures audiogram + speech-in-noise + functional log; round-trips through advocacy commitment/verify | `advocacy/`, `audiogram/`, new `regen/` logging module |
| Pre/post training-mode flag in existing protocols | At least 2 protocol variants with fatigue scoring | `therapy/`, `learn/` |
| Claim-standard templates + doc lint | 100% of regen-related docs pass claim check | `docs/`, CI |
| This `REGEN_VISION.md` reviewed by user + ≥1 clinician | Documented sign-off | repo |

### Medium-term (6–18 months)

| Milestone | Success metric | Integration point |
|-----------|----------------|-------------------|
| Sovereign export bundle for clinical sharing | Clinician can verify a bundle offline; user can revoke/re-share | `advocacy/` |
| Social acoustic layer "plasticity practice" mode | Measurable improvement in trusted-voice-in-noise scores over a study window | social layer, `dsp/` |
| Re-pointable haptic restoration map | Map updates from a changed audiogram without retraining from scratch | `wristband/`, `haptic_commander.py` |
| Longitudinal outcome dashboard (local-first) | User can audit own trend lines; no cloud | `mobile/`, `regen/` |

### Long-term (18+ months / horizon)

| Milestone | Success metric | Integration point |
|-----------|----------------|-------------------|
| Hybrid-interface abstraction | OpenHear runs unchanged alongside a third-party implant/delivery system | architecture-wide |
| Post-intervention adaptation profile library | Reusable, shareable (opt-in, anonymised) training profiles | profiles, social layer |
| Standing evidence file for assistive-device regulators | Living technical file tied to open validation artefacts | `docs/`, `clinical/` |

---

## 8. Safety, ethics, regulation, and Burgess alignment

### 8.1 Safety **[OPENHEAR]**

- **Overstimulation guardrails** for any training or therapeutic-frequency
  mode: conservative defaults, explicit fatigue scoring, mandatory rest
  logic, and per-session caps.
- **Personalisation-error containment**: changes are inspectable and
  reversible; no silent automatic adjustment without a user-visible record.

### 8.2 Ethics & claims — hard rules

These are non-negotiable. They apply to code comments, UI strings, commit
messages, marketing, and this document.

- **Never** state or imply that OpenHear regenerates, repairs, cures, or
  restores biological hearing.
- **Always** distinguish **[APPROVED]** *OTOF* gene therapy from
  **[PRECLINICAL]** everything-else, and from **[OPENHEAR]** assistive
  function.
- **No false hope.** Describe functional gains and sovereignty; do not
  describe biological outcomes OpenHear cannot produce.
- **Approved language template:** *"OpenHear maximises the hearing you have
  and adds multisensory access and training. It does not regenerate
  biology; biological regeneration, where possible, is a clinical therapy."*

### 8.3 Regulation

- OpenHear remains an **experimental project, not a medical device** (see
  README/roadmap disclaimers). Any future move toward a regulated
  assistive/therapeutic classification (UKCA/MHRA, FDA, EU MDR) is handled
  per the deployment-mode strategy in
  [`docs/RESEARCH_ROADMAP.md`](docs/RESEARCH_ROADMAP.md) Q15.
- Biological therapies referenced here are regulated medicinal products
  delivered by clinicians; OpenHear neither delivers nor advises on them.
- Prioritise user-controlled, non-proprietary elements; avoid any feature
  that creates vendor lock-in around a person's own data.

### 8.4 Sovereignty, accessibility & accountability

- **Full user ownership** of data, models, and profiles; open-source where
  it advances public good without compromising safety.
- **Accessibility for deaf users** and **family/community benefit** are
  first-class (the layer serves the creator, his brother, and a wider deaf
  community).
- **Binary human accountability.** Any automated element that affects a
  person must pass the Burgess **SOVEREIGN/NULL** test: a real human
  reviewing the specific facts yields `SOVEREIGN`; pure automation yields
  `NULL`. There is no third state. See
  [`docs/BURGESS_PRINCIPLE.md`](docs/BURGESS_PRINCIPLE.md).

---

## 9. Feature specs & next actions (starter set)

These are illustrative scaffolds for the §7 short-term milestones, offered
for iteration — not final designs.

**9.1 Baseline/outcome log entry (schema sketch).** A versioned record
containing: timestamp; record type (`audiogram` | `speech_in_noise` |
`haptic_perception` | `functional_log`); the measured values; optional
intervention context (`pre` | `post` | `none`); and a SHA-256 commitment
over the canonical serialisation, so it round-trips through the existing
advocacy commit/verify path. **No raw audio** in any field (enforced by the
existing `RawAudioRejectedError` gate).

**9.2 Training-mode parameter extension.** Add `phase` (`pre` | `post` |
`general`) and `fatigue_cap` to the existing protocol/training config, with
conservative defaults and mandatory rest scheduling.

**9.3 Claim-lint check.** A simple CI check that flags disallowed phrasings
(e.g. "regenerate", "cure", "restore hearing") in OpenHear-authored
docs/UI strings unless accompanied by an approved scope tag.

---

## 10. Iteration hooks — open questions for the user / deeper research

1. **Genotype.** Is the creator's congenital deafness genetically
   characterised? Etiology (e.g. *OTOF* vs *GJB2* vs structural) changes
   everything in §3–§4. This is the single highest-value missing fact.
2. **Priority.** Which short-term milestone matters most first — sovereign
   export, training modes, or the logging schema?
3. **Clinical reviewer.** Who is the named clinician for the §7 sign-off
   milestone (Burgess human-review requirement)?
4. **Metric weighting.** How should the user-sovereignty score weight
   data ownership vs model ownership vs profile portability?
5. **Depth.** Do you want a dedicated technical spec (logging schema +
   advocacy integration) or a feature backlog (issue-ready cards) produced
   next?

---

## 11. Sources (evidence cut-off June 2026)

Primary/most-load-bearing sources for §2; verify before external citation.

- Regeneron investor release — *Otarmeni™ (lunsotogene parvec-cwha)
  approved by FDA as first and only gene therapy for genetic hearing loss.*
- FDA accelerated-approval coverage (Pharmacy Times; reporting on the
  April 2026 decision).
- CHORD Ph1/2 trial reporting (Contemporary Pediatrics; Hearing Health
  Matters) — sustained hearing recovery, ~80% endpoint / ~40% near-normal.
- AK-OTOF / Akouos–Eli Lilly trial (ClinicalTrials.gov NCT05821959; BioSpace;
  GEN reporting on AAV-*OTOF* restoring hearing in children and adults).
- NIDCD and Hearing Restoration Project (HRP) overviews for hair-cell and
  SGN regeneration status (background for §2.2, §3).

> Where this document states trial percentages or approval dates, treat them
> as **reported figures to be re-verified** against the primary regulatory
> and peer-reviewed sources before any external or clinical use.
