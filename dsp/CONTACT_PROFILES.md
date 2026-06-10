# Per-contact DSP profiles (roadmap S1)

> **Status:** v0 scaffold — local storage, CLI, and pipeline plumbing.
> Voice-print fingerprinting is intentionally **not** included; that
> work lives behind §8 Q5 of `SUPERIOR_HEARING_ROADMAP.md` and will
> arrive in a later, consent-gated phase.
>
> **Sovereignty:** every profile is stored in a single local JSON file
> (default `~/.openhear/contacts.json`). Deleting that file revokes
> every stored contact profile in one move. No network call is ever
> made by this subsystem.

## What it does

When you tell the pipeline "I'm about to talk with Alex", a small,
bounded `ProfileDelta` (`dsp/profile_delta.py`) is layered on top of
the generic audiogram-derived DSP profile. The delta can soften or
tighten the compressor, nudge the speech-band gain, and ease off or
sharpen noise reduction — within the safe envelope enforced by
`dsp.profile_delta`.

This is the scaffold that unblocks roadmap experiment **SH-S-001**
(per-contact intelligibility, n ≥ 20 utterances × top-3 contacts) and
its associated metric **M2**.

## Storage layout

`~/.openhear/contacts.json`:

```json
{
  "version": 1,
  "profiles": [
    {
      "contact_id": "partner",
      "label": "Partner",
      "compression_ratio_delta": -0.1,
      "compression_knee_delta_db": -2.0,
      "voice_gain_delta": 0.1,
      "nr_aggressiveness_delta": -0.05,
      "consent": true,
      "enabled": true,
      "eq_delta_db": {},
      "fingerprint": null,
      "notes": ""
    }
  ]
}
```

All deltas are **clipped** to the safe limits defined in
`dsp/profile_delta.py` on load. A malformed file can never push the
DSP outside the envelope.

## CLI

```bash
# Save (or update) a contact.
python -m dsp.contact_cli set partner \
    --label "Partner" \
    --voice-gain-delta 0.1 \
    --comp-ratio-delta -0.1 \
    --consent

# Inspect.
python -m dsp.contact_cli list
python -m dsp.contact_cli show partner
python -m dsp.contact_cli where      # print the resolved file path

# Withdraw consent without losing the tuning.
python -m dsp.contact_cli set partner --no-consent

# Disable temporarily (BSEP switch).
python -m dsp.contact_cli set partner --disable

# Delete one contact.
python -m dsp.contact_cli clear partner

# Nuke everything (one-shot consent revocation).
python -m dsp.contact_cli clear '*' --yes
```

Use `--path FILE` on any command to point at a contacts file outside
the default location (e.g. on an encrypted volume).

## Pipeline integration

`python -m dsp.pipeline --contact partner` looks up `partner` in the
local bank and, **only if** that profile has `consent=true` and
`enabled=true`, applies its `ProfileDelta` on top of the audiogram-
derived parameters. Otherwise the generic profile is used and the
pipeline logs the reason.

The applied delta is emitted as a `BGSP|contact-profile-applied|…`
line in the standard logger so the receipt is recoverable later (no
new logger added).

## Burgess Principle guarantees

* `set` defaults to `consent=False`. A profile is never applied to the
  DSP chain until the user explicitly passes `--consent`.
* `--no-consent` keeps the on-disk tuning but blocks application —
  consent is revocable.
* `--disable` is a BSEP-style master switch per contact.
* Deltas are clipped on load and on combination; no escape from the
  safe envelope.
* Voice-print fingerprints are rejected by the loader in v0; storing
  one requires an explicit later upgrade.

## What is *not* in v0

* Voice-print matching — caller (CLI / future Iris sub-agent) must set
  the active contact explicitly.
* Per-band EQ application — the `eq_delta_db` field is accepted by the
  loader for forward compatibility but not yet applied by the DSP
  chain.
* Automatic contact switching from calendar or location.

See `SUPERIOR_HEARING_ROADMAP.md` §4.1 and §8 Q5 for the planned
trajectory.
