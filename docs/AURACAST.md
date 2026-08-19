# Auracast and OpenHear

**Status:** Design relationship (v1)  
**Date:** 2026-08-19  
**Scope:** How Bluetooth LE Audio Auracast broadcast fits with the Living Hearing Profile, context map, and haptic layer.

---

## What Auracast is

Auracast is the broadcast audio feature of Bluetooth LE Audio. A single transmitter can send a dedicated audio stream to an unlimited number of receivers with no pairing. Typical use cases:

- Airports and stations — gate and platform announcements
- Theatres, lecture halls, places of worship — performance or spoken word
- Gyms, bars, waiting rooms — specific TV or media channels
- Conferences and museums — language channels or tour groups

The user receives the **original clean feed** rather than trying to recover speech from room acoustics. Multiple programmes can exist in the same space; the user chooses which broadcast to join.

Auracast solves the *source access* problem in public spaces.

---

## What OpenHear already solves that Auracast does not

| Capability | Auracast | OpenHear |
|---|---|---|
| Clean source signal in venues | Yes | No (by design — complementary) |
| Personal audiogram → gain curve | No | Living Hearing Profile |
| Preference + context + fatigue awareness | No | Preference layer + context map |
| Haptic substitution when ears fail | No | Adaptive haptic layer |
| Accessibility profiles (autism / CP / sensory) | No | Live wristband path |
| Local-first sovereignty / Residual Witness | No | Core architecture |
| Scene intelligence (what is in the room) | Limited | YAMNet + sound-class policy |

OpenHear is not a replacement for Auracast. It is the layer that makes a clean feed (or residual hearing) *usable for this specific person*.

---

## Design relationship

### 1. Auracast stream as a preferred input

When an Auracast broadcast is available and the user joins it, the Living Hearing Profile should treat that stream as a **clean, high-priority speech/media input**:

- Apply the user’s preference-layer offsets and comfort ceiling to the stream.
- Prefer lower noise-reduction aggression (the source is already clean).
- Keep voice-clarity and mid-band preference behaviour that the user has already tuned.
- Do **not** assume the room microphone path is still primary.

The profile does not own the Auracast radio stack. It owns how the resulting audio is shaped for this person.

### 2. Context map entry: `auracast_venue`

A dedicated context captures the situation:

- Lower noise-reduction aggressiveness than `noisy_environment` or `transport`
- Beamforming less critical (source is already directional/clean)
- Voice-clarity gain still applied according to the user’s preference layer
- Haptic load reduced for continuous speech (the clean feed is carrying intelligibility); haptic remains available for discrete environmental events the broadcast does not cover (e.g. a nearby alarm, a person approaching)

### 3. Haptic behaviour around Auracast

- **Broadcast available / joined** — a short, low-urgency haptic cue so the user knows a clean assistive stream is present without needing to look at a phone.
- **Broadcast lost or left** — a distinct, still low-urgency cue so the user knows they have returned to acoustic-room listening.
- **While joined** — continuous speech from the stream should not generate continuous haptic “voice” pulses (that would be fatiguing). Haptic remains reserved for safety and discrete environmental classes that the broadcast does not replace.

This keeps the haptic layer complementary rather than competitive with the clean feed.

### 4. Sovereignty boundary

- Discovery and joining of Auracast broadcasts remain under the user’s control (phone assistant or hearing-device UI).
- OpenHear does not require cloud telemetry to use or personalise an Auracast stream.
- Any Living Hearing Profile adjustment applied to a broadcast is local, versioned, and user-owned in the same way as every other context.

---

## What this deliberately does *not* claim

- OpenHear does not implement the full LE Audio / BAP / BASS stack in this document.
- OpenHear does not replace hearing loops (telecoils) or claim Auracast will displace them in the near term. Both can coexist.
- OpenHear does not assume every user will have Auracast-capable aids. The acoustic + haptic path remains primary for people whose devices do not yet support LE Audio broadcast.

---

## Practical next steps for the repo

1. **Context map** — `auracast_venue` context added to the Living Hearing Profile (done in the accompanying profile update).
2. **Haptic policy** — document and, later, implement distinct short cues for “broadcast joined” / “broadcast left” without turning continuous stream speech into continuous haptic.
3. **DSP path** — when a clean digital stream is the active input, bias the pipeline toward preference-layer shaping and away from aggressive room-noise strategies.
4. **Clinician / user language** — keep explaining Auracast as “the clean feed in public places” and OpenHear as “how that feed (or your residual hearing) is made usable for you”.

---

## Summary

Auracast delivers the clean source.  
OpenHear delivers the personal, sovereign, context-aware, and haptic layer on top of whatever the person can hear — including a clean Auracast feed when one is available.

They are complementary. This document records that relationship so the architecture does not treat public assistive listening as an afterthought.
