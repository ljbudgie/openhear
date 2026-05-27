# OpenHear Tuning Guide

A quick reference for the knobs that matter in
`~/.openhear/config.yaml` and the live `dsp/config.py` defaults.

## Who should read this?

Anyone who has loaded their audiogram, is hearing processed audio in
their aids, and now wants to refine the sound.  The goal is *your*
ears — not a clinic standard.

## The big four

| Knob | What it does | Start here | Symptoms if too high | Symptoms if too low |
|------|--------------|-----------|----------------------|---------------------|
| `compression.ratio` | Slope of the WDRC curve. | 2.0–2.5 | Loud consonants sound squashed; music loses punch. | Whispers vanish; loud voices blast. |
| `compression.knee_db` | Level above which compression kicks in (dBFS). | -30 to -35 | Room noise gets amplified. | Quiet speech isn't lifted. |
| `voice.boost_db` | Extra gain in the 1–4 kHz voice band. | +4 to +8 dB | Sibilance, whistling. | Speech sounds muffled or thin. |
| `voice.boost_hz` | Low/high edges of the voice boost band. | `[1000, 4000]` | Too narrow → boomy bass. | Too wide → sharp highs hurt. |

## Quick diagnosis

**"Speech is clear but too sharp at the top."**
  Lower `voice.boost_db` by 2 dB, or pull the high edge of
  `voice.boost_hz` from 4000 down to 3500.

**"Noise gets boosted as much as speech."**
  Reduce `compression.ratio` towards 1.8, or raise
  `compression.knee_db` from -35 towards -28.

**"My own voice booms."**
  Ensure the own-voice bypass is enabled in `dsp/config.py`
  (`OWN_VOICE_BYPASS_ENABLED`) and consider raising the
  `OWN_VOICE_ENERGY_THRESHOLD_DBFS` so it engages more eagerly.

**"Whistling / feedback."**
  Drop `ANTI_FEEDBACK_GAIN_DB` by 2 dB at a time.  If it persists, run
  `python -m dsp.pipeline --test-tone` and watch the
  `dsp.feedback_canceller` log output.

## Measuring before you change

Before adjusting anything, capture a baseline:

```
python -m stream.recorder --raw raw.wav --processed proc.wav --duration 30
python -m stream.latency  --target 20
python -m dsp.pipeline     --metrics-csv metrics.csv &
```

Keep the WAVs and the CSV — if a later change sounds worse, A/B them
against the baseline.

## Offline evaluation

Use `examples/demo.py` to run a candidate config against a known WAV
file without any real-time pressure:

```
python examples/demo.py -i speech.wav -o processed.wav \
        --config my-candidate.yaml
```

Compare `speech.wav` and `processed.wav` in any DAW or in Audacity.

## Staying safe

* Keep `dsp/config.py` read-only after your first tuning session — put
  all personal overrides in `~/.openhear/config.yaml` instead.
* Before writing any fitting change back to the aids, confirm
  `core.backup.write_backup` has written a recent archive under
  `output/backups/` (`core.write_fitting.write_safe_parameters` does
  this automatically — check the log line it emits).
* If any new setting makes things sound drastically different, revert
  with `python -m core.read_fitting --session -o last.json` and
  compare.
