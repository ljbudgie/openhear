# Residual Witness

**Status:** Draft / Experimental  
**Depends on:** Living Hearing Profile v1+, haptic layer, local commitment history  
**Non-goals:** Raw audio storage • Cloud attestation services • Overnight replacement of existing legal signature frameworks

---

## 1. Motivation

Current digital signature and liveness systems prove one of two things:

- A cryptographic key was used, or
- A one-shot biometric check passed at a single moment.

Neither proves continuous presence of a living body with a specific sensory profile. Neither keeps the resulting evidence under the sole control of the person.

OpenHear already possesses the necessary substrate:

- A wearable that samples the auditory environment and drives haptics.
- A Living Hearing Profile that is versioned, user-owned, and cryptographically committed.
- A local-first architecture that refuses to exfiltrate raw sensory data.
- The Burgess Principle framework and the UK00004343685 certification mark.

Residual Witness is the protocol layer that turns those existing pieces into continuous, sovereign presence attestation.

---

## 2. Core Mechanism

### 2.1 What is hashed

The wristband never stores raw audio. It extracts compact features and hashes them.

| Source                    | Content hashed                                      | Purpose                              |
|---------------------------|-----------------------------------------------------|--------------------------------------|
| Microphone features       | Environmental sound features (not waveform)         | Acoustic context of the moment       |
| IMU (gyro + accelerometer)| Motion samples                                      | Continuity of a living body          |
| Haptic drive state        | Motor pattern / intensity                           | Physiological engagement             |
| Active Living Hearing Profile (optional) | Stable subset or commitment of current profile | Ties attestation to this specific sensory identity |

### 2.2 Chain construction (target design)

```
Every sampling interval (adaptive, not fixed 100 ms):
  acoustic_hash  = H(environmental_sound_features)
  motion_hash    = H(gyro_sample ⊕ accel_sample)
  haptic_hash    = H(motor_drive_pattern)
  profile_hash   = H(active_living_profile_commitment)   // optional but distinctive
  chain_link     = H(prev_link ⊕ acoustic_hash ⊕ motion_hash ⊕ haptic_hash ⊕ profile_hash ⊕ timestamp)

Every commitment interval (e.g. 5 s, or on significant event):
  commitment = SHA-256(chain_segment)
  → sent to paired phone over BLE
  → phone adds wall-clock time and user signature
  → written to local append-only log owned by the user
```

Rates are deliberately left adaptive. Continuous high-rate hashing is a power and thermal concern on a wearable; production implementations MUST support duty-cycling and event-triggered commitment.

### 2.3 Privacy boundary

- No raw audio is ever written to storage or transmitted.
- Feature vectors are discarded after hashing.
- The only persistent objects are cryptographic commitments and the user’s own signature over them.
- This satisfies the same data-minimisation posture already expressed by `RawAudioRejectedError` elsewhere in the codebase.

---

## 3. Integration with the Living Hearing Profile

The most distinctive element of Residual Witness is the optional inclusion of the active Living Hearing Profile state (or a stable commitment of it) inside the chain.

This means an attestation can carry:

> “This commitment was produced by a body whose current, user-controlled hearing profile was X.”

Because the Living Hearing Profile already contains clinical core + preference layer + context map + haptic priorities, the attestation is no longer a generic “a human was present.” It becomes “this specific sensory identity was present and engaged.”

That linkage is unique to OpenHear.

---

## 4. First Applications

### 4.1 Presence-attested actions (signatures, high-stakes confirmations)

When the user performs a significant action (document signature, high-value confirmation, etc.), the system can attach a short witness bundle containing:

- Preceding chain links (continuity)
- Acoustic context hash
- Motion continuity hash
- Haptic engagement hash
- Optional Living Hearing Profile commitment

The result is stronger than a pure digital signature: it carries evidence of continuous biological presence tied to a specific sensory profile.

This is positioned as a **presence layer** that can sit alongside existing signature systems, not as an overnight replacement for them.

### 4.2 Media & likeness claims

If synthetic media is later presented that claims the user was present, the user’s local Residual Witness log can produce a **NULL attestation**:

- Wristband was running.
- Acoustic / motion / haptic hashes do not match the claimed context.
- Therefore the claim of presence is inconsistent with the sovereign record.

This is the acoustic / sensory analogue of likeness sovereignty.

### 4.3 Advocacy use (Iris boundary)

Iris may read and verify Residual Witness logs. Iris may not generate them. The data originates from the body and the wristband; the advocacy layer only interprets and packages it.

---

## 5. Threat Model & Limitations

**Defends well against**
- Remote account takeover (no cloud credential is sufficient)
- Simple key theft without the physical device and living body
- Post-hoc fabrication of presence claims when the log is intact

**Detects after the fact**
- Physical coercion (chain may continue, but behavioural or contextual anomalies can later be examined)
- Brief removal of the device (motion / haptic continuity breaks)

**Does not prevent**
- Sophisticated physical-layer sensor spoofing while the device remains on the body
- Compelled production of the device itself under duress

Residual Witness raises the cost and detectability of false presence claims; it does not create an unbreakable physical seal.

---

## 6. Relationship to Existing OpenHear Components

| Component                  | Role in Residual Witness                          |
|----------------------------|---------------------------------------------------|
| Living Hearing Profile     | Optional but distinctive identity component       |
| Haptic layer               | Source of engagement / motor-state hashes         |
| Local commitment history   | Existing SHA-256 pattern is reused and extended   |
| Burgess Principle          | Supplies the SOVEREIGN / NULL binary evaluation   |
| UK00004343685              | Certification / origin mark for issued commitments|
| Iris                       | Read-only consumer and advocate, never generator  |

---

## 7. Implementation Notes & Open Questions

- Exact feature extraction for the acoustic hash is deliberately unspecified at this draft stage; it must remain lossy enough that reconstruction of the original audio is information-theoretically implausible.
- Power budget and adaptive sampling rates require measurement on real hardware before rates are fixed.
- Recovery and audit procedures after a detected chain break need further design.
- Legal recognition of Residual Witness bundles as evidence is a long-term goal, not a present claim. The protocol produces the raw material from which such recognition can later be sought.

---

## 8. Summary

Residual Witness is not a new app. It is the protocol that lets the OpenHear wristband turn continuous, body-bound, hearing-profile-weighted sensory data into citizen-owned cryptographic evidence of presence.

It is novel because it is the first design that simultaneously satisfies:

1. Continuous (not one-shot) presence,
2. Sensory identity (via the Living Hearing Profile),
3. Local-only data minimisation, and
4. An explicit sovereignty framework (Burgess Principle + certification mark).

That combination does not exist in DocuSign, C2PA, conventional wearables, or standard liveness detection.

---

*Draft for discussion. Comments and refinements welcome.*
