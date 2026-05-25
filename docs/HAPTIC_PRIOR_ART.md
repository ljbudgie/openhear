# Haptic Substitution for Hearing — Prior Art and Falsification Anchor

> **Purpose.** Bound the OpenHear "aids-free" claim with the published
> evidence base before designing further wristband encoders. Every
> entry in the table below is the kind of study future OpenHear
> psychoacoustic experiments must compare against, not surpass on
> rhetoric alone.
>
> **Status.** Working bibliography, v0 (May 2026). This document is a
> *living* literature anchor: pull requests adding studies — especially
> null or negative results — are welcomed and explicitly required
> before claims of novelty are made.

## 1. Why this document exists

The OpenHear README states that "the wristband **is** the hearing
system" as a north-star configuration. That is a strong, falsifiable
empirical claim. The history of vibrotactile and other sensory
substitution devices is roughly 100 years old and is not short of
similarly strong claims that did not survive controlled testing
(notably the original Tadoma and Tactaid programs, and several
contemporary vibrotactile vests).

Before designing v1+ of the OpenHear haptic encoder we need a single,
honest summary of:

1. What encodings have been tried.
2. What was actually measured (task, sample size, statistical power).
3. What was reported (effect size, confidence interval, replication
   status).
4. Where the evidence is strong, weak, or absent.

If a proposed novel encoding cannot identify which row in this table
it improves upon, and on what specific metric, it is not yet a
research contribution — it is a demo.

## 2. Survey table (working draft)

The table is intentionally compact; each citation should be expanded
as the team works through it. The "evidence" column is our own
qualitative grading using the rubric in §4.

| # | System / Author(s) | Year | Body site | Encoding | Population | Task & sample | Reported result | Evidence | Notes |
|---|--------------------|-----:|-----------|----------|------------|---------------|-----------------|---------:|-------|
| 1 | Tadoma method (Reed et al.) | 1985–96 | Hand on talker's face | Direct mechanical (lips, jaw, throat) | Deaf-blind, expert users | Speech reception threshold, n≤8 | Near-normal speech reception in a few highly trained users; not generalisable to short-term users | Strong (in scope) | The historical existence proof for tactile speech, but with thousands of training hours. |
| 2 | Tactaid II / VII (Brooks & Frost; Reed) | 1980s–90s | Sternum / forearm | 2–7-channel band-vocoder vibrotactile | Adults with profound hearing loss | Consonant ID, lipreading aid, n=10–30 | Modest *adjunct* to lipreading; standalone speech reception poor | Moderate | Closest historical analogue to a vibrotactile array. Standalone speech failed. |
| 3 | Frequency-Modulated Tactile Aid (Geldard) | 1957–66 | Multiple | Vibrotactile language (Vityphone, Optohapt) | Sighted adults, lab studies | Symbol ID, n<20 | Demonstrated learnable tactile symbol set; no transfer to environmental sound | Weak (off-task) | Foundational but evaluates symbols, not acoustic substitution. |
| 4 | Bach-y-Rita TVSS (and successors) | 1969– | Back / tongue | Visual→tactile pixel array | Mostly blind users | Object localisation, navigation | Repeated demonstrations of perceptual learning; no audiology endpoint | Moderate (cross-modal) | Establishes that cortical remapping is plausible; not specific to hearing. |
| 5 | Eagleman / Novich VEST (later "Buzz" by Neosensory) | 2015– | Torso vest, then wrist (Buzz) | Multi-band vibrotactile vocoder | Hearing-impaired and normal-hearing adults | Word ID with training, n≤90 | Above-chance word ID after training; standalone ASR-replacement claim not independently replicated at clinical strength | Moderate (industry-funded) | The most direct prior art for an OpenHear-style wristband. Independent replications are the gap. |
| 6 | Perrotta et al., bone conduction + haptic hybrid | 2022 | Wrist + mastoid | Audio→haptic envelope + bone conduction | Adults with mild HL | SIN improvement, n<30 | Small improvement vs. bone conduction alone | Moderate | Hybrid approach; suggests haptics may be additive, not substitutive. |
| 7 | Fletcher et al., haptic enhancement of cochlear implants | 2018–24 | Wrist | Low-frequency haptic envelope | CI users | Speech in noise, music, n=10–20 (multiple studies) | Repeatable small improvement when haptics added to CI | Strong (replicated) | Best evidence that wrist haptics add information — but as adjunct to a CI, not as replacement. |
| 8 | Reed et al., TActile Communication of Speech (TACS) | 2018– | Forearm array | Phoneme-level haptic icons | Hearing adults | Phoneme & word ID, n=12–24 | Trained users learn ~150 words; transfer to running speech limited | Moderate | Useful prior on training schedules and trainable bandwidth. |
| 9 | Saunders & Branigan, vibrotactile for tinnitus | 2010s | Wrist / neck | Notched envelope | Tinnitus patients | Loudness/annoyance scales | Mixed; placebo-prone | Weak | Cited because tinnitus is a likely OpenHear adjacent use case. |
| 10 | Russo et al., music-to-haptics for deaf concertgoers | 2020 | Chair / wearable | Bass envelope → vibration | Deaf adults | Subjective enjoyment | Strongly positive subjective; no perceptual content metric | Weak (subjective only) | Important for advocacy/UX framing; not a perception result. |

> **Evidence-rubric column key:** *Strong* = ≥1 peer-reviewed study with
> n≥20, pre-specified primary endpoint, and at least one independent
> replication. *Moderate* = peer-reviewed but small-n or
> single-laboratory. *Weak* = subjective endpoints only, or
> conference-only, or industry-only.

The table is **not** complete. Issues #TBD will track each row to
either (a) full-text retrieval and notes in `clinical/literature/` or
(b) deletion if the citation does not survive scrutiny.

## 3. What the literature actually supports

Reading across rows 1–10:

* **Adjunct, not replacement.** The strongest evidence base
  (Fletcher et al., row 7) shows that wrist haptics measurably *add*
  information when paired with an existing hearing pathway (cochlear
  implant). There is no Phase III-style evidence for a wrist haptic
  array *replacing* a hearing aid or implant for general speech.
* **Training matters as much as the encoding.** Tadoma (row 1) and
  TACS (row 8) both show that trained users vastly outperform naïve
  users on the same hardware. Any OpenHear study that tests an
  encoding without specifying a training schedule is pre-determined
  to show floor performance.
* **Subjective enjoyment ≠ perceptual content.** Music-to-haptics
  (row 10) is genuinely valuable for accessibility, but it is not
  evidence that haptics can convey acoustic information at the
  granularity speech requires.
* **Independent replication is rare.** The most-publicised consumer
  device (row 5) lacks independent peer-reviewed replication of its
  strongest claims. OpenHear should not adopt those claims by
  reference.

## 4. Implication for OpenHear's roadmap

The honest framing for the project is:

* Position the wristband first as an **adjunct and environmental
  awareness layer** (alarms, doorbells, direction-of-arrival cues,
  envelope tracking), where the published evidence base is at least
  moderately supportive.
* Treat the "aids-free" north-star claim as a long-horizon research
  hypothesis to be tested under IRB oversight, not as a near-term
  product positioning.
* Define the v0 encoder ([`v0_spec.md`](../wristband/encoding/v0_spec.md))
  as a **null baseline** so that any v1+ encoding is forced to
  demonstrate measurable improvement on a pre-registered metric.
* Pre-register any human study before data collection (see
  `clinical/PILOT_PROTOCOL_v1.md`).
* Publish raw, anonymised results regardless of sign; the project's
  credibility depends on null findings being visible, not buried.

## 5. Outstanding gaps in this anchor

> **Cross-reference.** The canonical haptic pattern registry,
> including the Burgess Principle SOVEREIGN/NULL semantics, lives in
> [`HAPTIC_PATTERN_LIBRARY.md`](HAPTIC_PATTERN_LIBRARY.md). The
> validation checklists that any haptic study here must satisfy
> before claiming a result live in
> [`EVIDENCE_AND_VALIDATION.md`](EVIDENCE_AND_VALIDATION.md) §2.

Tracked as future work — pull requests welcomed.

* Full-text retrieval and per-study notes for rows 1–10.
* Direct outreach to Fletcher's group (Southampton ISVR) and Reed's
  group (MIT RLE / CSAIL) for collaboration on standardised tasks.
* Addition of the deaf community / cultural perspective: when is
  *not* attempting to replicate hearing the right design choice?
* Coverage of cochlear implant + haptic *interference* studies
  (negative results) which are systematically under-represented in
  the literature.
