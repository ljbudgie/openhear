# OpenHear — Accessibility profiles

> **Cerebral palsy is in scope. So is anyone else whose body — not just
> their ears — changes what a good fit looks like.**

Every other tuning path in this repo starts from an audiogram: what you
hear. That is only half the fit. If your muscle tone shifts through the
day, if vibration can trigger a spasm or a startle, if an involuntary
movement can press a button you never meant to press, or if your speech
varies widely between repetitions, then the "correct" audiogram-derived
settings can still be the wrong settings for you.

This package holds that second half of the fit.

## What an access profile is

An `AccessProfile` (`accessibility/profiles.py`) is a small set of
**bounded** numbers describing motor and sensory access needs:

| Field | What it changes |
| --- | --- |
| `haptic_intensity_scale` | Multiplier on the wristband intensity byte — comfort damping. |
| `haptic_ramp_ms` | Minimum onset ramp instead of a hard step, so a buzz does not startle or provoke a spasm. |
| `haptic_refractory_scale` | Multiplier on the per-class alert spacing in `stream/haptic_policy.py`. |
| `min_confidence_delta` | Added to the policy confidence floor — fewer false buzzes. |
| `input_hold_ms` | How long a control must be held before it counts (hold-to-confirm). |
| `input_lockout_ms` | Quiet window after an accepted input, so one press is not read as several. |
| `voice_tolerance_scale` | Multiplier on the voice module's match tolerance (dysarthria). |
| `screening_prompts` | Questions a UI should ask — never answers. |

Every value is **clipped into a safe range on construction**, so a
hand-edited or malformed profile can never push the wristband outside the
envelope. Damping in particular is floored: `haptic_intensity_scale`
cannot reach zero, and `accessibility.adapt.scale_intensity` refuses to
take a safety-critical alert (an alarm) below a perceptible level.

## Bundled starting profiles

`CEREBRAL_PALSY`, `AUTISM`, and `SENSORY_PROCESSING` are optional starting
points, not diagnoses or predictions. Select one only when the user chooses
it, personalise every value, or start from `NEUTRAL`. Nothing in OpenHear
infers a condition or sensory need from behaviour, audio, or device use.

`CEREBRAL_PALSY` is a conservative starting point for users who choose it:

- **damped, ramped haptics** — spasticity and dyskinesia mean an abrupt,
  hard buzz on a limb with fluctuating tone can provoke an involuntary
  movement;
- **a raised confidence floor** — every false alert costs effort, and a
  startle response makes it cost more;
- **wider alert spacing** — orienting to an alert and acting on it can
  take longer;
- **hold-to-confirm input with a repeat lockout** — a brush or a tremor
  should not toggle a setting, and one intended press should register
  once;
- **dysarthria-tolerant voice scoring** — ordinary variability between
  repetitions is not failure.

`AUTISM` and `SENSORY_PROCESSING` start with gentler, ramped haptics, fewer
low-confidence alerts, wider alert spacing, and hold-to-confirm input. They
are deliberately separate: autism does not imply a particular sensory profile,
and sensory needs do not require a diagnosis.

**Every profile is a starting point, not a prescription.** No two people with
the same diagnosis or sensory preference need the same numbers. Override
anything:

```python
from accessibility import CEREBRAL_PALSY

mine = CEREBRAL_PALSY.replace(haptic_intensity_scale=0.5, input_hold_ms=650)
```

Overrides are re-clipped, so personalising can never escape the envelope.

## Using it

```python
from accessibility import (
    CEREBRAL_PALSY,
    InputGate,
    policy_config_for,
    scale_intensity,
    voice_match_tolerance_db,
)
from stream.haptic_policy import HapticPolicy

# 1. Alerting: raised confidence floor + wider refractory windows.
policy = HapticPolicy(policy_config_for(CEREBRAL_PALSY))

# 2. Drive strength: comfort damping that never mutes an alarm.
raw = mapper.get_intensity("alarm")
intensity = scale_intensity(raw, CEREBRAL_PALSY, sound_key="alarm")

# 3. Controls: hold-to-confirm over a monotonic ms clock.
gate = InputGate(CEREBRAL_PALSY)
if gate.update(pressed=button_is_down, now_ms=now):
    toggle_something()

# 4. Voice: widen the match window for dysarthric speech.
tolerance_db = voice_match_tolerance_db(MATCH_TOLERANCE_DB, CEREBRAL_PALSY)
```

`accessibility/adapt.py` is the **only** place a profile becomes
behaviour, so every adaptation rule is auditable in one file.

## Therapy protocols

No profile implies epilepsy or any other condition. `screening_prompts` asks
the user before gated therapy is considered; it never supplies an answer.
Whatever the user consents to declare is what you pass to
`TherapeuticProtocol.gate()`:

```python
from therapy import BRAINWAVE_PROTOCOLS

BRAINWAVE_PROTOCOLS["alpha_relax"].gate(declared_conditions)  # user's answer
```

The gate raises `ContraindicationError` and refuses to run. Nothing in
this package weakens it.

## Sovereignty

Nothing here is inferred, stored, or transmitted. An access profile exists
only because the user declared it, in memory, for that session. Obtain the
user's consent before selecting, personalising, or retaining a profile.
There is no detection of disability anywhere in this package and there will
not be one.

## Adding a profile

Cerebral palsy is the first bundled profile, not the last. To add
another, construct an `AccessProfile` and register it in
`ACCESS_PROFILES` — no other subsystem needs to change, because the
adapters read fields, not condition names. Please open an issue first if
you live with the condition or work with people who do; these defaults
should come from experience, not guesswork.
