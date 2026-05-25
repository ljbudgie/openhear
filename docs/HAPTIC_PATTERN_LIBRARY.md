# OpenHear Haptic Pattern Library

> **Status.** Canonical specification of haptic pattern semantics for
> OpenHear. This document supersedes any pattern definition implied by
> a single firmware or mapper file; the implementations in
> [`stream/haptic_mapper.py`](../stream/haptic_mapper.py),
> [`wristband/openhear_firmware.py`](../wristband/openhear_firmware.py),
> [`wristband/encoding/v0.py`](../wristband/encoding/v0.py), and
> [`hardware/wristband/firmware/haptic_mapper.py`](../hardware/wristband/firmware/haptic_mapper.py)
> must remain consistent with the IDs and semantics below.

OpenHear haptics are an accessibility surface as much as a research
surface. They are the multimodal channel that lets the project meet
the principles described in
[`docs/ACCESSIBILITY_STANDARDS.md`](ACCESSIBILITY_STANDARDS.md). The
pattern registry below exists so that this channel has stable,
testable, *non-confusable* meanings.

---

## 1. Design principles

1. **Stable IDs.** A pattern ID, once assigned, never changes
   meaning. New behaviour gets a new ID.
2. **One canonical source.** Implementations consume IDs from this
   document and from a future `wristband/patterns.py` / `stream/haptic_patterns.py`
   module; no implementation may invent its own IDs.
3. **Distinguishable on the skin.** Each pattern must be
   distinguishable from every other pattern in a controlled study
   ([`docs/EVIDENCE_AND_VALIDATION.md`](EVIDENCE_AND_VALIDATION.md)
   §2 H3).
4. **Safety supremacy.** Safety patterns must be more urgent than
   any informational pattern, including alarm-class environmental
   patterns. Safety mute is unconditional.
5. **Sovereign-honest.** SOVEREIGN and NULL patterns must be
   discriminable without ambiguity, and NULL must never be confused
   with a safety alarm.
6. **Backwards compatibility.** The legacy 3-byte BLE packet
   `[sound_class_id, intensity, pattern_id]` documented in
   [`wristband/README.md`](../wristband/README.md) remains supported.
   New surfaces add packet versions; they do not break v1.0.0.

---

## 2. Pattern registry

The registry is partitioned by purpose. Ranges are reserved so that
future additions remain stable across firmwares.

| Range | Purpose |
|---|---|
| 0–15 | Environmental sound classes (current micro:bit prototype) |
| 16–31 | Burgess Principle status patterns (SOVEREIGN / NULL family) |
| 32–47 | Safety / discomfort patterns |
| 48–127 | Social and phrase-pack patterns (future) |
| 128–239 | High-resolution lattice patterns (24/64/128 actuator research) |
| 240–254 | Compatibility shims (e.g. `v0_compat`) |
| 255 | Reserved for future use |

### 2.1 Environmental sound classes (0–15)

These map 1:1 to the seven-class micro:bit v1.0.0 prototype
([`wristband/README.md`](../wristband/README.md)). IDs 7–15 are
reserved for forward-compatible expansion.

| ID | Key | Meaning | Dominant freq (Hz) | Default motor behaviour |
|---:|---|---|---:|---|
| 0 | silence | No haptic output | — | Idle |
| 1 | voice | Speech / conversation | 1000 | Both motors, gentle 200/100 ms pulse × 3 |
| 2 | doorbell | Doorbells / chimes | 2000 | Both motors, two sharp 50 ms pulses |
| 3 | alarm | Sirens / alarms / buzzers | 3150 | Rapid alternating L/R 30 ms × 8 |
| 4 | dog | Barking / howls | 500 | Right motor single 150 ms pulse |
| 5 | traffic | Road traffic / horns | 500 | Left motor single 300 ms pulse |
| 6 | media | Music / TV / radio | 1000 | Both motors slow 500/500 ms pulse × 2 |
| 7–15 | _reserved_ | Reserved for future environmental classes | — | — |

These IDs must remain stable for as long as any clinic prototype is
in use.

### 2.2 Burgess Principle status patterns (16–31)

These render verification outcomes from the advocacy layer
([`docs/BURGESS_PRINCIPLE.md`](BURGESS_PRINCIPLE.md)) onto the skin.
They are informational, never urgent.

| ID | Key | Meaning | Tactile signature |
|---:|---|---|---|
| 16 | sovereign_ok | Human-verified SOVEREIGN receipt confirmed | Calm, symmetric, low-frequency confirmation pulse; both motors in unison; 120 ms on / 120 ms off × 2 at low intensity. Repeatable but explicitly non-alarming. |
| 17 | null_unverified | Result tagged NULL by the advocacy gate | Asymmetric, interrupted pulse: single motor, 60 ms on / 180 ms off / 60 ms on. Distinct from alarm/safety patterns. Indicates "not human-verified / not trusted" without implying danger. |
| 18 | null_refused | Bundle rejected (e.g. raw audio refusal) | As `null_unverified`, repeated twice with a 400 ms gap. |
| 19 | sovereign_pending | Awaiting human verification | Single, very gentle 80 ms pulse on the non-dominant side. |
| 20–31 | _reserved_ | Reserved for future Burgess Principle states | — |

Key invariants:

- **SOVEREIGN** patterns are calm and symmetric.
- **NULL** patterns are asymmetric and interrupted.
- Neither family may be rendered in a way that resembles ID 3
  (alarm) or any safety pattern in 32–47.

### 2.3 Safety / discomfort patterns (32–47)

Safety patterns take precedence over every other class. The
firmware must render them even if other patterns are queued, and the
mute pattern (ID 32) must be unconditional.

| ID | Key | Meaning | Tactile signature |
|---:|---|---|---|
| 32 | safety_mute | Immediate mute / stop | One distinctive 300 ms long pulse on both motors at high (but bounded) intensity, followed by silence. After delivery, the device suspends all other patterns until reset. |
| 33 | safety_overload | Over-amplification detected | Three short 80 ms pulses on both motors at high intensity; the system simultaneously reduces gain. |
| 34 | safety_thermal | Wristband thermal limit approached | Slow descending 200, 150, 100 ms pulses; intensity tapers down; the system reduces drive duty. |
| 35 | safety_battery_low | Battery critically low | Two long 250 ms pulses spaced 1 s apart on the non-dominant side. |
| 36–47 | _reserved_ | Reserved for further safety states | — |

Safety patterns must always be more urgent than ID 3 (alarm) so that
a user under sensory load can still identify them.

### 2.4 Social / phrase-pack patterns (48–127)

Reserved for the social acoustic layer described in
[`docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md`](HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md)
pillar 8. No IDs are assigned yet; assignments must respect the
"distinguishable on the skin" requirement and pass the confusion
matrix study (H3).

### 2.5 High-resolution lattice patterns (128–239)

For the 24/64/128 actuator research mapper in
[`hardware/wristband/firmware/haptic_mapper.py`](../hardware/wristband/firmware/haptic_mapper.py).
The `COMMON_PATTERNS` dictionary in that file remains the working
draft; promotion to this canonical document requires a study that
demonstrates distinguishability against the existing 0–47 set.

### 2.6 Compatibility shims (240–254)

| ID | Key | Meaning |
|---:|---|---|
| 240 | v0_compat | Legacy v0 wristband encoder packet projected onto the 3-byte BLE contract. |
| 241–254 | _reserved_ | Future compatibility shims. |

---

## 3. SOVEREIGN / NULL haptic semantics

The Burgess Principle binary (SOVEREIGN vs NULL) is rendered to the
skin via IDs 16 and 17 above. The semantic contract is:

- **SOVEREIGN (ID 16):**
  - Calm, symmetric, low-frequency confirmation pulse.
  - Low urgency.
  - Repeatable but never alarming.
  - Must not be louder than the user's stored comfort threshold.

- **NULL (ID 17):**
  - Asymmetric or interrupted pulse.
  - Distinct from alarm/safety patterns.
  - Indicates "not human-verified / not trusted" without implying
    danger.
  - Must not be louder than the user's stored comfort threshold.

- **Safety stop / discomfort (ID 32 family):**
  - More urgent than NULL.
  - Triggers immediate intensity reduction or mute.
  - Bypasses any user-set comfort throttling for the minimum
    duration required to signal the event.

These three families together carry the project's central trust
distinction. They must be testable on the skin per
[`docs/EVIDENCE_AND_VALIDATION.md`](EVIDENCE_AND_VALIDATION.md) §2
H4 and H5.

---

## 4. Packet contract and versioning

The current packet contract is the stable v1.0.0 3-byte BLE UART
packet documented in [`wristband/README.md`](../wristband/README.md):

```text
[sound_class_id, intensity, pattern_id]
```

Future expansion is additive: a higher packet version (e.g. a 5- or
8-byte frame carrying band-energy or actuator-array data) can be
introduced without breaking v1.0.0 by reserving a leading version
byte in a new BLE characteristic. The v1.0.0 packet retains its
exact meaning for as long as any clinic prototype consumes it.

Refactoring direction (non-blocking, see
[`docs/ACCESSIBILITY_STANDARDS.md`](ACCESSIBILITY_STANDARDS.md) §3):

- Introduce `wristband/patterns.py` (or `stream/haptic_patterns.py`)
  as the canonical Python registry — typed enums for sound class IDs
  and pattern IDs.
- Have `stream/haptic_mapper.py`,
  `hardware/wristband/firmware/haptic_mapper.py`, and any new
  firmware consume that registry rather than redeclaring IDs.
- Add pytest cases asserting that the registry's IDs match this
  document, and that the documented IDs never change without an
  intentional, version-bumped update.

---

## 5. Haptic usability study tasks

The patterns above are not validated by virtue of being documented.
They become validated when, per
[`docs/EVIDENCE_AND_VALIDATION.md`](EVIDENCE_AND_VALIDATION.md) §2,
the following studies are run:

1. **Pattern recognition accuracy.** Per-pattern recognition rate
   after a defined training interval (H3).
2. **SOVEREIGN vs NULL discrimination.** Forced-choice
   discrimination, target ≥ 90 % (H4).
3. **Alarm vs NULL discrimination.** Forced-choice discrimination,
   target ≥ 95 %; NULL is never mistaken for an alarm (H5).
4. **Reaction time.** Time from pattern onset to user response on a
   known cue (H6).
5. **Long-wear comfort.** Comfort scale during an 8-hour wear test
   (H2, H8).
6. **Intensity preference.** Per-pattern preferred intensity per
   participant (H1, H2).
7. **Fatigue and habituation.** Recognition decay over 60 minutes
   (H7).

Results, including null and negative results, are published per
[`docs/HAPTIC_PRIOR_ART.md`](HAPTIC_PRIOR_ART.md) §4 — the project
does not claim performance without data.
