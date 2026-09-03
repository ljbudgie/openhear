# Aids-out night safety and rear-approach awareness

**Status:** Design note from RNID Research Panel lived experience  
**Date:** 2026-09-03  
**Purpose:** Record two safety gaps that a booth audiogram and a daytime hearing-aid fitting do not cover.

---

## 1. Aids-out night / sleep safety

Many people remove hearing aids before sleep as recovery, not as non-compliance. Once the aids are out:

- Building and hotel fire alarms in neighbouring or downstairs premises can be inaudible in the bedroom.
- A bedroom smoke alarm may also be missed.
- Statutory tactile substitutes (local-authority pillow shakers, buzzing doorbells) fail in the field and then become impossible to get repaired.

**Design implication for OpenHear**

The wristband must remain a first-class alerting path when aids are out. Alarm and doorbell classes stay at maximum priority during an explicit `aids_out` / night quiet period. The band is not optional decoration in this mode; it is the remaining sensory channel. Do not treat aid-out as “off”.

A watch-reachable **kill switch / comfort clamp** is a separate daytime need (drilling, sirens, recruitment). Night alerting and daytime overload control must not cancel each other.

## 2. People approaching from behind

Listeners often do not hear a person coming up behind them and therefore do not move. This is a courtesy and safety problem on pavements, in corridors, and in shops. It is related to, but not the same as, traffic localisation under single-sided deafness.

**Design implication**

Reserve a short, distinct haptic class for *human approach from rear / unheard side* — not the same pulse as speech-in-front or as vehicle traffic. Low duty cycle. Opt-in. The aim is a chance to step aside, not a continuous presence buzz.

## 3. Related product gaps named in the same accounts (not yet separate modules)

- Shared listening: one Bluetooth stream to the aids leaves a partner unable to join the same Zoom or phone call.
- Venue loop systems that exist on paper but are off or staffed as a performance.
- Assistive headphones that work only if the aids come out, with nowhere discreet to store them at an interval.
- Android Bluetooth dropouts mid-conversation when the phone takes a photo, shows a map, or posts a notification.
- Rechargeable aids that fade before the end of the day.

These are manufacturer and venue failures. OpenHear should not pretend to replace every one of them. It should keep them listed so the Living Hearing Profile and study questionnaires keep asking the right questions.

## Sovereignty note

This note contains no personal identifiers. It is derived from consented panel correspondence used as architecture, not as published case narrative.
