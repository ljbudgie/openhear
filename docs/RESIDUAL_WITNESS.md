# Residual Witness

**Status:** Draft / Experimental  
**Depends on:** Living Hearing Profile v1+, haptic layer, local commitment history  
**Non-goals:** Raw audio storage • Cloud attestation services • Claiming current legal admissibility • Overnight replacement of existing signature frameworks

---

## 1. Motivation

Existing systems prove either:

- that a cryptographic key was used, or
- that a one-shot biometric check passed at a single instant.

Neither proves continuous presence of a living body that carries a specific, user-controlled sensory identity. Neither keeps the resulting evidence under the sole control of the person.

OpenHear already contains the required substrate:

- Wearable hardware that samples the auditory environment and drives haptics
- A versioned, user-owned Living Hearing Profile with cryptographic history
- A local-first architecture that refuses to exfiltrate raw sensory data
- The Burgess Principle evaluation framework and the UK00004343685 certification mark

Residual Witness is the thin protocol layer that turns those existing pieces into continuous, sovereign presence attestation.

---

## 2. What Makes This Novel

Residual Witness is the first design that simultaneously satisfies four conditions that have not previously been combined:

1. **Continuous** presence (not a one-shot liveness check)
2. **Sensory identity** — the attestation can be bound to the active Living Hearing Profile
3. **Local-only data minimisation** — feature hashes only; raw audio is never stored or transmitted
4. **Explicit sovereignty framework** — Burgess Principle binary evaluation + certification mark under UK00004343685

No current system meets all four. Digital signatures prove key possession. Conventional liveness checks are momentary and platform-owned. Consumer wearables generate company-controlled telemetry. Content credentials (C2PA etc.) travel with the file and can be stripped. Residual Witness produces citizen-owned evidence that a particular body, carrying a particular hearing profile, was continuously present and physiologically engaged.

That combination can only be built on the OpenHear stack.

---

## 3. Core Mechanism

### 3.1 What is hashed

The wristband never stores raw audio. Compact features are extracted and immediately hashed; the feature vectors themselves are discarded.

| Source | Content hashed | Purpose |
|--------|----------------|---------|
| Microphone features | Environmental sound features (not waveform) | Acoustic context of the moment |
| IMU (gyro + accelerometer) | Motion samples | Continuity of a living body |
| Haptic drive state | Motor pattern / intensity | Physiological engagement |
| Active Living Hearing Profile | Stable commitment of current profile state | Binds attestation to this specific sensory identity |

### 3.2 Chain construction (target design)

```
Every sampling interval (adaptive):
  acoustic_hash  = H(environmental_sound_features)
  motion_hash    = H(gyro_sample ⊕ accel_sample)
  haptic_hash    = H(motor_drive_pattern)
  profile_hash   = H(active_living_profile_commitment)   // distinctive OpenHear element
  chain_link     = H(prev_link ⊕ acoustic_hash ⊕ motion_hash ⊕ haptic_hash ⊕ profile_hash ⊕ timestamp)

Every commitment interval (or on significant event):
  commitment = SHA-256(chain_segment)
  → transferred to paired phone over BLE
  → phone adds wall-clock time and user signature
  → written to local append-only log owned by the user
```

Sampling and commitment rates MUST be adaptive. Continuous high-rate hashing is a power and thermal constraint on wearable hardware; production implementations are required to support duty-cycling and event-triggered commitment.

### 3.3 Privacy boundary (non-negotiable)

- No raw audio is ever written to storage or transmitted.
- Feature vectors are discarded after the hash is computed.
- The only persistent objects are cryptographic commitments and the user’s own signatures over them.
- This is the same data-minimisation posture already expressed by `RawAudioRejectedError` elsewhere in the codebase.

---

## 4. Binding to the Living Hearing Profile

The optional (but strongly recommended) inclusion of a commitment to the active Living Hearing Profile is the element that cannot be replicated by generic wearables or signature platforms.

An attestation can therefore carry the statement:

> “This commitment was produced while the following user-controlled Living Hearing Profile was active.”

Because the profile already contains the locked clinical core, the preference layer, the context map, and the haptic priorities, the attestation moves from “a human was present” to “this specific sensory identity was present and engaged.”

That binding is the unique contribution of OpenHear.

---

## 5. First Applications

### 5.1 Presence-attested actions

When the user performs a high-stakes action (document signature, critical confirmation, etc.), the system may attach a short witness bundle containing:

- Recent chain links (continuity)
- Acoustic context hash
- Motion continuity hash
- Haptic engagement hash
- Living Hearing Profile commitment

This is positioned as a **presence layer** that can strengthen existing signature systems. It is not claimed as a drop-in replacement for them.

### 5.2 Media and likeness claims

If synthetic media is later presented that asserts the user was present, the user’s local Residual Witness log can emit a **NULL attestation**:

- The wristband was operating.
- The acoustic / motion / haptic hashes are inconsistent with the claimed context.
- The presence claim therefore fails the sovereign record.

This is the sensory analogue of likeness sovereignty.

### 5.3 Advocacy boundary (Iris)

Iris may read, verify, and package Residual Witness logs.  
Iris may never generate them.  
Witness data originates from the body and the wristband; the advocacy layer only interprets it.

---

## 6. Threat Model

**Strongly mitigates**
- Remote account takeover (possession of cloud credentials is insufficient)
- Pure key theft without the physical device and living wearer
- Post-hoc fabrication of presence when the local log remains intact

**Detectable after the fact**
- Physical removal of the device (motion and haptic continuity break)
- Certain forms of coercion (chain may continue, but contextual or behavioural anomalies become visible on later inspection)

**Out of scope / residual risk**
- Sophisticated physical-layer sensor spoofing while the device remains on the body
- Compelled production of the device under duress

Residual Witness raises both the cost and the detectability of false presence claims. It does not create an unbreakable physical seal, nor does it claim to.

---

## 7. Relationship to Existing Components

| Component | Role |
|-----------|------|
| Living Hearing Profile | Distinctive identity binding |
| Haptic layer | Source of engagement / motor-state hashes |
| Local commitment history | Existing SHA-256 pattern is extended |
| Burgess Principle | Supplies the SOVEREIGN / NULL evaluation |
| UK00004343685 | Certification / origin mark for issued commitments |
| Iris | Read-only consumer and advocate; never a generator |

---

## 8. Open Questions

- Concrete acoustic feature set (must remain lossy enough that reconstruction is information-theoretically implausible)
- Measured power budget and safe adaptive rates on real hardware
- Recovery and audit procedure after a detected chain break
- Long-term path toward recognition of Residual Witness bundles as evidence (explicitly a future goal, not a present claim)

---

## 9. Summary

Residual Witness is not a new application. It is the protocol that allows the OpenHear wristband to convert continuous, body-bound, hearing-profile-weighted sensory data into citizen-owned cryptographic evidence of presence.

Its novelty lies in the simultaneous satisfaction of continuous presence, sensory identity, local-only minimisation, and an explicit sovereignty framework. That combination does not exist in digital signature platforms, conventional liveness detection, consumer wearables, or content-credential systems.

---

*Draft for discussion and refinement.*
