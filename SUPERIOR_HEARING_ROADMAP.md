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

**Status:** Draft v0.2 · Author: Lewis James Burgess · Built on the
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
| S1 — *scaffolded v0* | `dsp/contact_profiles.py`, `dsp/contact_cli.py`, `dsp/profile_delta.py`, `dsp/CONTACT_PROFILES.md`. Bounded delta + consent + BSEP disable + local-only `~/.openhear/contacts.json`. Voice-print fingerprinting deliberately deferred to §8 Q5. Pipeline: `python -m dsp.pipeline --contact CONTACT_ID`. |
| S2 | **Haptic groove channel for music** — wire `stream/tempo_channel.py` + `stream/crowd_arousal.py` to a music source, expose a "music mode" in `haptic_commander.py` | `stream/`, `wristband/` | M4 with haptic-on rated ≥ +2 vs haptic-off over ≥ 10 listening sessions across ≥ 3 genres |
| S3 | **Fatigue-aware auto-gain v0** — read Whoop recovery score at session start; bias compression knee and noise-reduction aggressiveness | `dsp/compression.py`, `dsp/noise_reduction.py`, Whoop ingest | M6: subjective fatigue at session end ≤ baseline on ≥ 70 % of low-recovery days |
| S3 — *scaffolded v0* | `dsp/fatigue.py`, `dsp/fatigue_cli.py`, `dsp/FATIGUE_AWARE.md`. Local-file Whoop adapter (`~/.openhear/whoop_recovery.json`, env override `OPENHEAR_WHOOP_FILE`); §9 Q3 three-tier bucket scheme; bounded `ProfileDelta` composed cleanly with S1; red bucket *suggests* low-effort preset (Burgess: never auto-arms). No HTTP. Pipeline: `python -m dsp.pipeline --fatigue`. |
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

## 9. Open questions — Draft v0.2 resolutions

The five questions raised in Draft v0.1 are resolved here with defensible
defaults. **Q1 (your contacts) and Q2 (your measured personal baselines)
are facts only the user can confirm**; the values below are seed
placeholders to unblock `SH-S-001` and are flagged as such. Q3, Q4, Q5
are design defaults grounded in the existing repo and are ready to be
promoted to v1 unless overridden.

### Q1 — Three contacts to seed SH-S-001 (D1) — *user to confirm names*

Use **roles**, not names, in committed records (names stay local per §5).

| Slot | Role | Why this slot | Voice-sample target |
|------|------|---------------|---------------------|
| `contact_a` | Partner / closest daily speaker | Highest D1 leverage; most conversation minutes/week; easiest consent | ≥ 5 min clean speech + ≥ 5 min in-noise (kitchen, café) |
| `contact_b` | Parent or sibling | Phone/video-call dominant; tests prosody under codec loss; relational weight | ≥ 5 min clean + ≥ 3 min over the call channel actually used |
| `contact_c` | Close friend or frequent collaborator | Diversifies F0 / accent; tests schema generalises beyond family | ≥ 5 min clean + ≥ 3 min in a noisy social setting |

Status: **placeholder roles accepted; names assigned by user at run time
and never committed**. Consent flow per Q5.

### Q2 — Personal v1.x baselines for M1 and M5 — *to be measured before SH-S-001 lands*

The committed [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) v1 (May 2026) is
a DSP-engineering benchmark (latency / `realtime_factor_p95` /
bit-parity), **not** a user-outcome benchmark. There is no committed
v1.x SRT or focus-session number to anchor to. So we explicitly capture
both as `TBM` with a fixed protocol, rather than invent numbers:

- **M1 — Speech-in-noise SRT (dB):** `baseline: TBM`. Protocol —
  adaptive matrix-style sentence list (open Oldenburg-style list or
  equivalent) at +10 / +5 / 0 / −5 dB SNR, 20 sentences per SNR,
  generic profile only, single quiet session. Median SNR for 50 %
  words-correct = baseline SRT. Captured *before* the `SH-S-001` change
  set lands. Guardrail after `SH-S-001`: regression ≤ 1 dB (§6).
- **M5 — Focus-session length to first interruption-by-sound (min):**
  `baseline: TBM`. Protocol — 5 working sessions over 1 week on the 3
  nominated focus tasks, current generic profile, current environment,
  log time-to-first-self-reported-interruption. Median = baseline.
  Phase M target (M4 acoustic "rooms"): ≥ 2× baseline median.

If the user has private measurements taken outside the repo, those
override these placeholders and get committed as a signed JSON in
`experiments/superior_hearing/SH-S-000_baselines/`.

### Q3 — Whoop recovery floor for S3 / M6 — three-tier, not a single number

A single floor is insufficient. Default scheme, all three thresholds
user-tunable in `dsp/config.py`:

| Whoop recovery | DSP behaviour (S3) | Training behaviour (M6) | Rationale |
|----------------|--------------------|--------------------------|-----------|
| **≥ 67 (green)** | Full user-preset aggressiveness | Full training session permitted | Headroom for cognitive load |
| **34–66 (yellow)** | Less noise reduction, gentler compression knee, slightly lower MPO ceiling | ≤ 50 % normal duration; prefer passive (music) over active (phonemic drills) | Reduce listening effort on partial-recovery days |
| **≤ 33 (red)** | "Low-effort" preset; optional haptic-only focus room | **Skip active training entirely.** Passive only. | Protect against compounded fatigue + tinnitus risk |

The `whoop_recovery_floor: 30` in §6 is rounded up to **34** to align
with the standard Whoop yellow boundary.

### Q4 — Haptic daily-dose budget per skin site

Firmware already enforces the **thermal envelope and simultaneous
duty-cycle cap**
(`hardware/wristband/firmware/openhear_firmware_v1.py`: `MAX_INTENSITY =
180`, `THERMAL_DERATE_C = 38.0`, `THERMAL_SHUTOFF_C = 40.0`;
`hardware/wristband/power_budget_v1.md`: "Cap simultaneous duty cycle to
25 % starter build", "derate at 38 °C", "hard-shutdown at 40 °C",
"refuse charging while worn unless skin temperature below 36 °C"). What
this roadmap **adds** is a per-skin-site **daily-dose** abstraction on
top of that envelope.

| Parameter | Default | Source |
|-----------|---------|--------|
| `max_intensity` (firmware floor) | **180 / 255** | `openhear_firmware_v1.py:21` (committed) |
| `simultaneous_duty_cycle_pct` | **25 %** | `power_budget_v1.md` starter build (committed) |
| `per_site_duty_cycle_24h_pct` | **40 %** (~9.6 h active per actuator site per 24 h) | New; conservative continuous-wear ceiling |
| `per_site_continuous_max_min` | **20 min active, then ≥ 5 min rest** | New; gives 38 °C envelope time to settle |
| `thermal_derate_c` | **38.0 °C** | `openhear_firmware_v1.py:22` (committed) |
| `thermal_shutoff_c` | **40.0 °C** | `openhear_firmware_v1.py:23` (committed) |
| `nightly_quiet_window` | **23:00–07:00 local; all haptics off except safety class** | New; sleep hygiene + tinnitus risk reduction |
| `safety_class_override` | Whitelist (`door`, `name-call`, `alarm`) bypasses quiet window only; **never** bypasses thermal | New |
| Tunability | All values **user-tunable in `dsp/config.py`**, but firmware refuses values that exceed the committed thermal envelope or `max_intensity` | BSEP-compatible: user can reduce, never exceed hardware-safe ceiling |

Pattern: **firmware owns the hard envelope; `dsp/config.py` owns the
soft user-tunable budget within it** — same shape as how `dsp/config.py`
already wraps DSP parameters today.

### Q5 — Consent UX for per-contact voice fingerprints (S1, L2)

`clinical/CONSENT_TEMPLATE.md` is the correct *legal* base but is
clinical-trial framed; a social-tier equivalent is needed.
Sovereignty constraint (§5 + `docs/SOVEREIGN_PHILOSOPHY.md`): nothing
leaves the device, everything is revocable, plain-JSON exit.

**Five-step opt-in flow, all local, no cloud, no telemetry:**

1. **Plain-language ask** (paper or in-person, not in-app): one-paragraph
   script — *"I'd like to record about 5 minutes of you speaking so my
   hearing system understands your voice better. The recording stays on
   my device, nothing goes online, and you can ask me to delete it at
   any time and I'll show you it's gone."*
2. **On-device consent record** (signed JSON, BGSP-anchored) at
   `contacts/<contact_id>/consent.json` with fields: `contact_id`
   (locally-generated UUID, never the real identifier), `consent_granted_at`,
   `consent_scope` ∈ {`voiceprint_only`, `voiceprint_plus_prosody`,
   `voiceprint_plus_prosody_plus_relational_history`}, `revocation_method`
   (`one_click_in_app` always present), `expiry` (default 12 months,
   then re-ask), `signed_sha256` (canonical-JSON SHA-256, matching the
   advocacy-layer pattern).
3. **Visible capture session:** UI shows level meter + elapsed time +
   hard stop. Mic indicator on the entire time. No background capture, ever.
4. **Revoke = delete + prove:** one button. Deletes the voiceprint,
   prosody delta, and relational-history slice. Emits
   `consent_revoked.json` provenance record; shows the contact the
   empty directory (or a hash-zero attestation).
5. **Re-consent on scope widening:** if the `ContactProfile` schema
   bumps in a way that widens scope, previous consent does **not**
   auto-carry. BSEP rule: **scope can only narrow without re-consent,
   never widen.**

Fall-out defaults:

- `default_scope = voiceprint_only` (narrowest)
- `default_expiry_months = 12`
- `cloud_sync = false` (no toggle to enable in Phase S/M)
- `shared_with_other_contacts = false`

---

## 10. Defaults summary (Draft v0.2)

Single table for downstream agents and `dsp/config.py` to anchor against:

| Key | Default | Tunable? | Source |
|-----|---------|----------|--------|
| `SH-S-001.contacts` | `[contact_a, contact_b, contact_c]` (roles) | User assigns names locally | §9 Q1 |
| `M1.baseline_db` | `TBM` (run baseline before SH-S-001) | n/a | §9 Q2 |
| `M5.baseline_min` | `TBM` (5-session protocol) | n/a | §9 Q2 |
| `whoop_recovery.green` | `≥ 67` | yes | §9 Q3 |
| `whoop_recovery.yellow` | `34–66` | yes | §9 Q3 |
| `whoop_recovery.red` | `≤ 33` | yes | §9 Q3 |
| `whoop_recovery_floor` (training, §6) | `34` (was `30`) | yes | §9 Q3 |
| `haptic.max_intensity` | `180 / 255` | no (firmware floor) | §9 Q4 |
| `haptic.simultaneous_duty_cycle_pct` | `25` | yes, ≤ firmware cap | §9 Q4 |
| `haptic.per_site_duty_cycle_24h_pct` | `40` | yes | §9 Q4 |
| `haptic.per_site_continuous_max_min` | `20` (then ≥ 5 rest) | yes | §9 Q4 |
| `haptic.thermal_derate_c` | `38.0` | no (firmware) | §9 Q4 |
| `haptic.thermal_shutoff_c` | `40.0` | no (firmware) | §9 Q4 |
| `haptic.nightly_quiet_window` | `23:00–07:00 local` | yes | §9 Q4 |
| `haptic.safety_class_override` | `[door, name-call, alarm]` | yes (cannot bypass thermal) | §9 Q4 |
| `consent.default_scope` | `voiceprint_only` | yes (narrow only without re-consent) | §9 Q5 |
| `consent.default_expiry_months` | `12` | yes | §9 Q5 |
| `consent.cloud_sync` | `false` | no in Phase S/M | §9 Q5 |
| `consent.shared_with_other_contacts` | `false` | no in Phase S/M | §9 Q5 |
