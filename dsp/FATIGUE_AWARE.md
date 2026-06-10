# Fatigue-aware DSP hooks (roadmap S3)

> **Status:** v0 scaffold — local-file Whoop adapter, bounded bias, CLI,
> pipeline plumbing. **No network call is ever made.** Cloud ingest is
> a separate, opt-in PR (see `SUPERIOR_HEARING_ROADMAP.md` §4.5).
>
> **Sovereignty:** the local recovery file holds sensitive health data.
> It lives in your home directory (default
> `~/.openhear/whoop_recovery.json`), is written with mode `0o600` on
> POSIX, and can be deleted in one command at any time.

## What it does

When the user's Whoop recovery score is low, the DSP chain *lightens
the load* on cognition: softer compression, less aggressive noise
reduction, a touch less voice-band boost. The bias is expressed as a
small, bounded `ProfileDelta` (`dsp/profile_delta.py`) layered on top
of the audiogram-derived profile.

This unblocks roadmap metric **M6** (subjective fatigue Δ vs Whoop
strain / recovery): ≤ baseline subjective fatigue on ≥ 70 % of
low-recovery days.

## Recovery buckets (§9 Q3 thresholds, pinned in the roadmap)

| Bucket | Score | DSP behaviour | Suggestion |
|---|---|---|---|
| **green** | ≥ 67 | no bias | none |
| **yellow** | 34 – 66 | mild bias (softer compression, gentler NR) | none |
| **red** | ≤ 33 | stronger bias (within the safe envelope) | "low-effort preset" — **suggestion only**, user/Iris must confirm |
| **unknown** | n/a | no bias | none — Burgess Principle: no inference without data |

## Storage layout

`~/.openhear/whoop_recovery.json`:

```json
{
  "score": 64,
  "timestamp": "2026-06-10T07:00:00Z",
  "source": "whoop"
}
```

`source` is a free-text tag (`"whoop"`, `"manual"`, …) used only in
local logs. The file is never sent off-device.

Override the location with `--path` on the CLI or the
`OPENHEAR_WHOOP_FILE` environment variable.

## CLI

```bash
# Manually set today's recovery (useful while the cloud ingest is out of scope).
python -m dsp.fatigue_cli set --score 64

# Inspect the current reading and the bias it produces.
python -m dsp.fatigue_cli show

# Classify a hypothetical score without writing anything.
python -m dsp.fatigue_cli classify --score 30

# Print the resolved file path.
python -m dsp.fatigue_cli where

# Delete the local recovery file (full deletion path).
python -m dsp.fatigue_cli clear
```

## Pipeline integration

```bash
python -m dsp.pipeline --fatigue                # uses default file
python -m dsp.pipeline --fatigue --fatigue-recovery-file /path/to/r.json
python -m dsp.pipeline --contact partner --fatigue   # both compose
```

When `--fatigue` is set the pipeline calls `fatigue_delta_from_file()`,
which:

1. Returns the **identity delta** if the file is missing, empty, or
   malformed (the pipeline keeps running; a warning is logged).
2. Reads the score, classifies it into a bucket, and returns the
   matching bounded `ProfileDelta`.
3. Emits a `BGSP|fatigue-bias-applied|…` log line when a non-identity
   bias is applied.
4. Emits a `BGSP|fatigue-low-effort-suggested|…` log line for the red
   bucket — the suggestion is **never** acted on automatically.

If a `ContactProfile` is also active (`--contact …`), the two deltas
are composed via `ProfileDelta.compose([contact, fatigue])`. Per-contact
tuning is therefore applied *first*; fatigue bias is layered on top.
The combined delta is re-clipped to the safe envelope by
`dsp.profile_delta`, so no composition can leave the bounded region.

## Burgess Principle guarantees

* `enabled: false` by default in `user_config.FatigueConfig`.
* Red bucket *suggests* a low-effort preset; the pipeline never silently
  arms one. The CLI surfaces the suggestion in `show` output.
* All deltas pass through `ProfileDelta` clipping on construction *and*
  on combination.
* `forget_recovery()` / `python -m dsp.fatigue_cli clear` removes the
  local file in one move.

## What is *not* in v0

* No HTTP / Whoop API ingest — recovery must be written locally
  (manually or by an out-of-band script the user controls).
* No automatic preset arming — the red bucket only emits a suggestion.
* No persistence of past readings — one current score, one file.
  Trend logging belongs to a later BGSP experiment record.

See `SUPERIOR_HEARING_ROADMAP.md` §4.5, §9 Q3 (rows 329–341 and 422–425)
for the planned trajectory.
