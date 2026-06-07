# SUPERIOR_HEARING_ROADMAP.md — OpenHear and the Path to Functionally Superior Hearing

> **⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE. NOT A CURE.**
> OpenHear does not restore or replace biological hearing. This roadmap
> describes how the existing OpenHear stack (DSP, haptics, social acoustic
> layer, therapy, Iris guidance, Whoop integration, 3D/DIY hardware) can be
> extended so that the *experienced* hearing of a profoundly deaf user is —
> in the domains that matter most to that user — **functionally and
> experientially superior to pre-deafness natural hearing**. Superior here
> means richer, more controllable, less fatiguing, and more relationally
> powerful — not louder, not "normal."

**Status:** Draft v0.1 · Author: Lewis James Burgess · Built on the
[Burgess Principle](docs/BURGESS_PRINCIPLE.md) · Governed by BGSP (Git /
Iris / AI governance) and BSEP (Sovereign Exit Paths) · Complements
[`REGEN_VISION.md`](REGEN_VISION.md) (regeneration as *complementary*
optimisation, never replacement) and
[`docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md`](docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md).

Scope tags used throughout (consistent with `REGEN_VISION.md`):

- **[OPENHEAR-NOW]** — already in the repo today; this roadmap composes it.
- **[OPENHEAR-SHORT]** — buildable in weeks–months on current hardware.
- **[OPENHEAR-MED]** — new agents / profiles / experiments, 3–12 months.
- **[OPENHEAR-LONG]** — horizon: hybrid bio-tech, advanced haptics, future interfaces.
- **[ASPIRATION]** — stated goal with no current evidence base; flagged as such.

---

## 0. Theory — Why a sovereign, multimodal, plasticity-first stack can exceed natural hearing

Natural hearing is a single biological channel optimised by evolution for
survival in the ancestral environment — not for modern conversation in
restaurants, not for music a listener actually loves, not for emotional
nuance over a video call, not for sustained focus under cognitive load,
and not for relational depth with specific people who matter. It is also
fixed: a hearing person cannot turn down the fridge, amplify their
partner's voice in a crowd, feel the bassline of a song through their
skin, or have an AI quietly surface the emotional valence of a colleague's
sentence. OpenHear can. The thesis of this roadmap is that **four
compounding levers — neuroplasticity, multimodal substitution, AI
gap-filling with emotional/relational intelligence, and closed-loop
self-experimentation under sovereign data — can be combined so that the
user's *experienced* hearing exceeds natural hearing in the domains that
matter most**. Plasticity lets the brain learn new mappings (haptic →
phonemic, haptic → spatial, haptic → emotional) that natural hearing
never trained. Multimodality means information lost in the audio channel
can arrive through the wrist, the visual layer, or the social profile.
AI gap-filling adds capabilities natural hearing never had: per-speaker
boosting, prosodic highlighting, semantic summarisation of background,
fatigue-aware gain shaping. Closed-loop self-experimentation, logged
under BGSP with full provenance, turns every day of use into measurable,
reversible optimisation. None of this requires sacrificing sovereignty:
every channel, model, and profile remains local-first, user-owned, and
exit-able under BSEP.

---

## 1. Domains of "superior" — what we are actually optimising

This roadmap refuses the abstract goal "hear better." Every phase is
scored against the six domains the user has named as the ones that
matter:

| # | Domain | Pre-deafness natural ceiling | OpenHear superior target |
|---|--------|------------------------------|--------------------------|
| D1 | **Social / relational connection** | Generic speech intelligibility; everyone equal | Per-contact tuned profiles (partner, parents, close friends) with prosody and emotional-valence highlighting |
| D2 | **Conversation flow in noise** | ~+0 dB SNR in crowds; fatigue dominant | Effective ≤ −5 dB SNR via selective DSP + haptic spatial cues + AI turn-taking prompts |
| D3 | **Music / enjoyment** | Whatever the ear delivers; no skin/body channel | DSP shaped to musical preference + haptic groove channel + therapy-grade frequency delivery |
| D4 | **Focus during work** | Constant low-level distraction; ear cannot mute | User-defined acoustic "rooms"; haptic-only mode; fatigue-aware auto-gain |
| D5 | **Emotional nuance** | Limited to acoustic cues most listeners miss | AI-derived prosody + valence channel surfaced via Iris and haptic micro-cues |
| D6 | **Environmental awareness** | 360° hearing but no semantic labelling | YAMNet-class events + bearing → haptic + Iris annotation; sleep/training/work modes |

All KPIs in §3 are tagged D1–D6.

---

## 2. Architectural integration map (what plugs into what)

| Lever | Existing OpenHear surface | Extension point |
|-------|---------------------------|-----------------|
| Personalised DSP from audiogram | `dsp/pipeline`, `dsp/compression.py`, `dsp/voice_clarity.py`, `dsp/config.py`, `core/` fitting reader | New per-context and per-contact profile bank (§4.1) |
| Haptic sensory substitution | `wristband/`, `stream/haptic_packet`, `stream/haptic_primitive.py`, `stream/crowd_arousal.py`, `stream/tempo_channel.py`, `haptic_commander.py` | New phoneme / prosody / spatial / emotional channels (§4.2) |
| Social acoustic layer | Trusted-contact profiles, social acoustic engine | Per-contact tuning + relational metrics logging (§4.3) |
| Iris guidance | Iris agent surface | Sub-agent pack: Plasticity Coach, Social Listener, Music Enhancer, Fatigue Sentinel (§4.4) |
| Whoop integration | Whoop ingest | Fatigue-aware DSP, recovery-gated training load (§4.5) |
| Therapy / plasticity | `therapy/`, `therapy/entrainment.py` | Audiogram-aware plasticity training programmes (§4.6) |
| Governance / sovereignty | `advocacy/`, BGSP, BSEP, `NOTICE`, `LICENSE` | Provenance for every experiment + exit path for every model (§5) |
| Hardware / DIY | `hardware/`, `hardware/ite-shells/`, OpenHear Wristband, local 3D printing | Rapid wristband iteration; multi-actuator v2 (§4.2, §7) |

---

## 3. Outcome metrics (single shared scoreboard)

Every phase below references metrics from this scoreboard. All logs are
written under BGSP with the canonical JSON + SHA-256 anchoring already
used by the advocacy layer, so any result can be independently verified
or rolled back.

| ID | Metric | Channel | Domain |
|----|--------|---------|--------|
| M1 | Speech-in-noise SRT (dB) on standard list (e.g., matrix sentence) | DSP eval harness | D2 |
| M2 | Per-contact intelligibility (% words correct) on partner/parent/friend voice samples | DSP + social profile A/B | D1 |
| M3 | Conversational turn-success rate (self-logged, 1–5) per session | Iris journal | D1, D2 |
| M4 | Music enjoyment rating (1–10) + haptic-on/off A/B preference | Iris journal + DSP profile | D3 |
| M5 | Focus session length to first interruption-by-sound | DSP "room" telemetry | D4 |
| M6 | Subjective fatigue Δ vs Whoop strain / recovery | Whoop + Iris | D2, D4 |
| M7 | Prosody / emotion call-out accuracy (vs labelled clip set) | Iris emotion sub-agent | D5 |
| M8 | Environmental event detection latency & precision (haptic + Iris) | YAMNet + wristband | D6 |
| M9 | Haptic phonemic discrimination (forced-choice over training) | Wristband + training app | D1, D2 |
| M10 | "Superior to memory of natural hearing?" weekly self-rating per domain (−5 … +5) | Iris weekly review | D1–D6 |

Success threshold for declaring a domain "functionally superior": **M10
≥ +2 sustained ≥ 8 weeks AND ≥ 1 objective metric (M1/M2/M5/M7/M8/M9)
exceeding the user's documented pre-deafness or first-week baseline**.

---

## 4. Phased roadmap

### Phase S — Short term (weeks–months, current hardware) · [OPENHEAR-SHORT]

Goal: prove the *direction* on three domains (D1, D2, D3) using only the
modules already in the repo plus thin extensions.

| # | Extension | Touch points | MVE / success criterion |
|---|-----------|--------------|-------------------------|
| S1 | **Per-contact DSP profile bank** — extend `dsp/config.py` schema with a `ContactProfile` (contact_id, voice-print fingerprint, EQ delta, compression delta, noise-reduction aggressiveness) | `dsp/config.py`, social profile store | A/B: M2 improves ≥ 15 % on the user's top-3 contacts over generic profile, n ≥ 20 utterances each |
| S2 | **Haptic groove channel for music** — wire `stream/tempo_channel.py` + `stream/crowd_arousal.py` to a music source, expose a "music mode" in `haptic_commander.py` | `stream/`, `wristband/` | M4 with haptic-on rated ≥ +2 vs haptic-off over ≥ 10 listening sessions across ≥ 3 genres |
| S3 | **Fatigue-aware auto-gain v0** — read Whoop recovery score at session start; bias compression knee and noise-reduction aggressiveness | `dsp/compression.py`, `dsp/noise_reduction.py`, Whoop ingest | M6: subjective fatigue at session end ≤ baseline on ≥ 70 % of low-recovery days |
| S4 | **BGSP-anchored experiment log** — minimal `experiments/superior_hearing/` directory; each experiment a signed JSON record (hypothesis, change set, metrics, decision) | `advocacy/`, `experiments/` | At least 4 experiments anchored, each verifiable end-to-end via the existing advocacy verify path |

### Phase M — Medium term (3–12 months) · [OPENHEAR-MED]

Goal: open D5 (emotional nuance), strengthen D1/D2, begin D6 work.

| # | Extension | Touch points | MVE / success criterion |
|---|-----------|--------------|-------------------------|
| M1 | **Prosody + emotional-valence channel** — local prosody model emits arousal / valence / turn-end probability; surfaced via Iris and via subtle wristband micro-pulses | `voice/`, Iris, `stream/haptic_primitive.py` | M7 ≥ 70 % match against a user-labelled clip set (n ≥ 100); +2 on M10/D5 over 4 weeks |
| M2 | **Phonemic haptic alphabet (training)** — distinct haptic primitives for high-confusion phoneme pairs (s/sh, f/th, b/d); paired with a training mini-app | `wristband/`, `stream/`, `therapy/`, new training app | M9 reaches ≥ 80 % forced-choice over 6-week protocol |
| M3 | **Social Listener Iris sub-agent** — runs during conversations, suggests "ask X to repeat", "lean in", "switch to quieter table"; cites BGSP-logged metric trail | Iris, social profile, journal | M3 weekly mean ≥ +1 over 6 weeks vs pre-agent baseline |
| M4 | **Acoustic "rooms" for focus** — user-defined DSP/haptic presets bound to calendar / location / Whoop state | `dsp/config.py`, Iris, Whoop, calendar | M5 doubles vs Phase S baseline on 3 nominated focus tasks |
| M5 | **YAMNet → wristband bearing channel** — `yamnet_classifier.py` events with direction estimate → directional haptic primitive | `yamnet_classifier.py`, `wristband/` | M8 ≥ 80 % precision on a personal event set (door, name-call, alarm, partner footsteps); subjective +2 on M10/D6 |
| M6 | **Plasticity Coach Iris sub-agent** — schedules short daily training (M2, frequency therapy, music ear-training) using `therapy/` programmes, gated by Whoop recovery | Iris, `therapy/`, Whoop | ≥ 5 sessions / week sustained 8 weeks with M9 trending ↑ |

### Phase L — Long horizon (≥ 12 months, partly aspirational) · [OPENHEAR-LONG] / [ASPIRATION]

Goal: cross-modal capabilities natural hearing never had, while
preserving full sovereignty and an explicit exit path.

| # | Extension | Notes |
|---|-----------|-------|
| L1 | **Multi-actuator wristband v2** — angle-of-arrival haptic spatialisation using the `spatial_balance` axis already defined in `stream/haptic_primitive.py` | Local 3D-printed iteration; firmware backward-compatible per existing v1 wire format |
| L2 | **Per-relationship "depth" profiles** — combines per-contact DSP (S1), prosody channel (M1), and a relational-history layer logged under BGSP | Surfaces "you missed two emotional cues with X this week"; opt-in, deletable |
| L3 | **Hybrid bio-tech complementarity** — if biological restoration becomes relevant (per `REGEN_VISION.md`), OpenHear remains the *training, baseline, outcome, and substitution* layer around it, never the replacement | Already the position of `REGEN_VISION.md`; this roadmap reinforces it |
| L4 | **Sensory super-channels** [ASPIRATION] — sub-audible (infrasound), ultrasonic event detection, room-state semantics (e.g., "tension rising") surfaced via Iris + haptics | Strictly opt-in; always paired with BSEP exit |
| L5 | **Federated, sovereign improvement** [ASPIRATION] — opt-in, locally trained model deltas shareable without raw audio leaving the device | Must satisfy `docs/SOVEREIGN_PHILOSOPHY.md` constraints in full |

---

## 5. Safety, sovereignty, and Burgess alignment (non-negotiable)

- **No overstimulation / tinnitus risk:** every new DSP profile (S1, M4)
  must pass the existing MPO / loudness checks before activation; every
  new haptic primitive (M2, L1) must respect a per-skin-site daily-dose
  budget logged in `wristband/` telemetry; auto-throttle on Whoop strain
  ≥ user threshold.
- **No cure framing:** all user-facing copy from any Iris sub-agent
  shipped under this roadmap must use enhancement / training language,
  consistent with the scope discipline in `REGEN_VISION.md`.
- **Local-first by default:** prosody (M1), per-contact voice fingerprints
  (S1), and any model deltas (L5) run on-device. Cloud is opt-in and
  off by default. No raw audio leaves the device under any phase.
- **BGSP (Git / Iris / AI governance):** every experiment in §4 is a
  signed, anchored record under `experiments/superior_hearing/` with
  hypothesis, change set, metrics, decision, and rollback commit;
  any automated suggestion from Iris passes through a human review gate
  before it can rewrite a profile.
- **BSEP (Sovereign Exit Path):** every profile, model, and contact
  record exports to plain JSON; every Iris sub-agent in §4.4 can be
  disabled with a single switch; nothing in this roadmap may introduce
  a dependency the user cannot remove without losing their hearing
  capability.
- **Burgess Principle conformance:** any clinical-grade audiogram or
  fitting data touched by this roadmap continues to flow through
  `advocacy/gate.py` and `advocacy/adapters.py`; no new pathway bypasses
  the five commitments in `docs/BURGESS_PRINCIPLE.md`.
- **Consent in the social layer:** per-contact profiles (S1, L2) require
  explicit, revocable consent from the contact for any voice-fingerprint
  storage; default to local-only, never shared.

---

## 6. Minimal viable experiment — Phase S kickoff (copy-paste-ready)

```yaml
experiment_id: SH-S-001
title: "Per-contact DSP profile vs generic profile — top-3 contacts"
domain: [D1, D2]
hypothesis: >
  A per-contact DSP profile (EQ delta + compression delta + NR delta)
  tuned over 3 short sessions yields ≥ 15 % improvement in M2
  (per-contact word-correct %) over the user's current generic profile,
  without degrading M1 (speech-in-noise SRT) on standard material.
change_set:
  files:
    - dsp/config.py        # add ContactProfile dataclass + loader
    - dsp/pipeline         # honour active ContactProfile when set
    - experiments/superior_hearing/SH-S-001/
  reversible: true
  rollback_commit: <git sha before change>
procedure:
  contacts: [partner, parent_a, close_friend_b]
  per_contact_sessions: 3
  utterances_per_session: 20    # balanced sentence list
  conditions: [generic_profile, contact_profile]
  randomisation: block, counter-balanced
metrics:
  - M2  # primary
  - M1  # guardrail (must not regress > 1 dB)
  - M6  # fatigue guardrail
  - M10 # weekly subjective, D1
safety_gates:
  mpo_check: pass
  haptic_dose: n/a
  whoop_recovery_floor: 30
governance:
  bgsp_anchor: required        # signed JSON in experiments/superior_hearing/SH-S-001/
  human_review_gate: required  # no profile auto-promoted without explicit accept
  bsep_exit: contact_profile can be deleted; falls back to generic in one call
success_criteria:
  primary:   M2 improves ≥ 15 % on ≥ 2 of 3 contacts (paired, p ≤ 0.05 or effect size ≥ 0.5)
  guardrail: M1 regression ≤ 1 dB
  subjective: M10/D1 ≥ +1 at week 4
decision_rule:
  on_success: promote ContactProfile schema to dsp/config.py default;
              open Phase M experiment SH-M-001 (prosody channel)
  on_failure: archive, document, no rollout; consider haptic-first variant
```

---

## 7. Iris sub-agent prompt seeds (excerpt — full pack tracked under §4.4)

- **Plasticity Coach** — *"You are the user's sovereign plasticity coach.
  Schedule ≤ 15 min daily training drawn from `therapy/` programmes and
  the phonemic haptic alphabet (M2). Skip days when Whoop recovery <
  user_floor. Never frame training as cure. Log every session under BGSP.
  Surface weekly trend on M9 and M2."*
- **Social Listener** — *"You observe conversation telemetry (turn
  success, asked-to-repeat count, prosody confidence). You may suggest
  in-the-moment moves (lean in, switch table, ask to repeat) but never
  override the user. Cite the BGSP-logged metric you are reacting to.
  Respect per-contact consent flags."*
- **Music Enhancer** — *"You manage the haptic groove channel (S2) and
  per-genre DSP presets. You ask before changing presets mid-track. You
  treat enjoyment (M4), not loudness, as the optimisation target."*
- **Fatigue Sentinel** — *"You watch M6 and Whoop strain. You may reduce
  DSP aggressiveness or propose a haptic-only focus room (M4) when
  fatigue rises. You can be disabled with one switch (BSEP)."*

---

## 8. Cross-references

- [`README.md`](README.md) — eight-pillar platform; this roadmap operates
  across Pillars 1, 2, 3, 5, 6, 7.
- [`docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md`](docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md)
  — architectural ground truth; all extensions in §4 must conform.
- [`docs/AIDS_FREE_ARCHITECTURE.md`](docs/AIDS_FREE_ARCHITECTURE.md) —
  the wristband-as-hearing-system endpoint; L1 is its natural ally.
- [`REGEN_VISION.md`](REGEN_VISION.md) — biological restoration as
  *complementary*; L3 enforces that boundary.
- [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) — existing benchmark suite
  that M1, M5, M8 should plug into.
- [`docs/SOVEREIGN_PHILOSOPHY.md`](docs/SOVEREIGN_PHILOSOPHY.md) — design
  rationale every new module in §4 must satisfy.
- [`docs/BURGESS_PRINCIPLE.md`](docs/BURGESS_PRINCIPLE.md) — the five
  commitments; no extension in §4 may weaken them.

---

## 9. Open questions (answer before promoting from draft to v1)

1. Which 3 contacts seed SH-S-001 (D1)?
2. Current documented v1.x baselines for M1 and M5 — anchor exactly.
3. Whoop recovery floor for S3 / M6 (default 30 sufficient?).
4. Haptic daily-dose budget per skin site (firmware default vs user-tunable).
5. Consent UX for per-contact voice fingerprints (S1, L2) — opt-in flow.
