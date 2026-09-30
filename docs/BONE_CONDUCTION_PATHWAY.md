# Bone-conduction pathway

OpenHear already prescribes air-conduction insertion gain from an audiogram
(`dsp/audiogram_profile.py`). This note adds a **second output pathway**:
the same Living Hearing Profile, rendered as vibration into bone rather than
into the ear canal.

It is not SoundBite. It is not a tooth. Coupling hardware is an optional
module and the oral variant is unpublished — see `docs/FTO_SONITUS.md`.

## Why a separate pathway

Air-conduction aids fail three groups the panel keeps naming:

- Conductive or mixed loss, where the outer/middle ear is the problem and
  the cochlea still has reserve (the air–bone gap).
- Single-sided deafness, where one cochlea is gone and the other is fine —
  volume in the dead ear does nothing.
- Aids-out hours, when a canal device is not worn and a mastoid or forehead
  transducer can still carry an alarm or a name.

Bone conduction is old (tuning forks, BAHA abutments, consumer BC headsets).
What OpenHear owns is the **user-held audiogram → gain table** and the rule
that the person can see the table.

## Signal path

```
Living Hearing Profile (AC thresholds, optional BC thresholds)
        |
        v
dsp.audiogram_profile.prescribe()     # existing NAL-style AC start
        |
        v
dsp.bone_conduction.prescribe_bc()    # retarget + transducer compensation
        |
        v
output_safety limiter                 # still last; BC has its own ceiling
        |
        v
transducer driver (mastoid / forehead / abutment / unspecified)
```

Code: `dsp/bone_conduction.py`.

## Prescription rules (ours)

1. **Target the cochlea, not the canal.** If bone-conduction thresholds exist
   for an ear, use those as the hearing-loss input. If they do not, fall back
   to air-conduction thresholds and say so on the profile. Do not invent an
   air–bone gap.
2. **Do not copy a manufacturer EQ.** Compensation for a generic BC transducer
   (weak lows, a mid-band peak) lives in a labelled table in
   `dsp/bone_conduction.py`. Swap the table when a real coupler measurement
   exists. Never paste a SoundBite response curve.
3. **SSD is a route, not a device.** `route="contralateral"` sends the dead-side
   microphone into the better-cochlea BC output. That is CROS logic. It does
   not require a tooth.
4. **Safety is vibration, not only dBFS.** The AC limiter still runs. BC adds
   a conservative extra attenuation (`BC_SAFETY_ATTENUATION_DB`) until a
   measured acceleration limit exists for the chosen coupler. Over-driving a
   mastoid pad is still a harm.
5. **Aids-out is a context flag**, not a new product. The same profile can
   ask for BC output when `aids_in == false` (see
   `docs/AIDS_OUT_AND_REAR_APPROACH.md`).

## What this is not

- Not a claim that BC restores the turbine hall or replaces an implant.
- Not a CE/UKCA bone-conduction medical device. Mode 1 remains a phone filter
  plus optional contact transducer under the same sovereignty rules.
- Not an intra-oral appliance. That folder is a hold.

## Living Profile fields

```
output_pathways: [air_conduction, bone_conduction, haptic]
bone_conduction:
  coupler: mastoid | forehead | abutment | unspecified
  use_bc_thresholds: true | false
  ssd_route: none | contralateral
  dead_side: left | right | none
```

Oral / tooth is not a legal value in the public schema.
