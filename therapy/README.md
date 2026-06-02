# OpenHear — Therapy (Pillar 5)

> **⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE**
> This is sovereign, inspectable tooling for *evidence-led self-experimentation*,
> not treatment. Nothing here diagnoses, treats, or cures anything. Talk to a
> professional before using frequency delivery for any health purpose.

First code for the therapeutic-frequency-delivery pillar in
[`docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md`](../docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md).
It begins with **binaural beats**, but with the angle that is genuinely
unexplored for OpenHear's users and missing from every consumer app.

## Why this is different

A binaural beat is the rhythm your brain perceives when each ear hears a
slightly different tone (e.g. 295 Hz left, 305 Hz right → a 10 Hz beat).
Generating that is trivial. The catch nobody addresses: **the percept needs
both tones to arrive at usable, balanced loudness.** For someone with hearing
loss — OpenHear's whole audience — a fixed carrier can land in a dead zone in
one ear and the beat simply collapses.

So `prescribe_binaural()` reads *your* audiogram and:

- places the **carrier** where both ears hear best, and
- sets **per-ear gains** that rebalance an asymmetric loss,

never exceeding a conservative amplitude ceiling. That is the part no
binaural-beats product does.

## Honesty about evidence

The science of brainwave entrainment is mixed, and most consumer claims are
overstated. Rather than hide that, every protocol carries an explicit
[`EvidenceGrade`](protocol.py) (`anecdotal → preliminary → emerging →
established`), and the bundled presets are graded conservatively — none
claims to be `established`. `target_outcomes` describe what a protocol is
*explored for*, not what it does.

## Safety

Auditory entrainment is contraindicated for seizure disorders. Every bundled
protocol declares that contraindication and `TherapeuticProtocol.gate()`
refuses to run when a user's declared conditions match. Amplitudes are capped
in `therapy/binaural.py`.

## Usage

```bash
# A plain 10 Hz (alpha) beat on a 300 Hz carrier:
python -m therapy.binaural_cli --beat 10 --carrier 300 --duration 60 --out beats.wav

# Personalised to your own audiogram (carrier + per-ear levels):
python -m therapy.binaural_cli --beat 10 --audiogram AG.json --out beats.wav
```

```python
from audiogram.audiogram import Audiogram
from therapy import prescribe_binaural, BRAINWAVE_PROTOCOLS

proto = BRAINWAVE_PROTOCOLS["alpha_relax"]
proto.gate(user_conditions={"epilepsy"})        # raises ContraindicationError
rx = prescribe_binaural(Audiogram.from_path("AG.json"), proto.frequencies[0])
signal = rx.render(duration_s=60)               # (N, 2) float32, ready to play
```

## Roadmap (Pillar 5, still open)

- Cross-modal entrainment via the wristband for profound loss where acoustic
  binaural beats can't work at all (isochronic/haptic rhythm over the
  existing 3-byte haptic packet).
- `carrier_shape` / `duty_cycle` rendering beyond pure sine.
- n-of-1 outcome logging and an evidence registry, per the architecture doc.
