# OpenHear — DSP Benchmark Methodology

> **Status.** v1, May 2026. Foundational artefact for Workstream A of
> the Phase 1 90-Day Master Plan.
>
> **Why this document exists.** Every quantitative claim OpenHear
> makes about latency, throughput or real-time headroom must be
> reproducible by an independent third party from a clean checkout
> with one command. This page specifies how.

## 1. Run it

```bash
make install-dev      # one-off
make benchmark        # prints a signed JSON report on stdout
```

Or, equivalently:

```bash
python -m scripts.benchmark --frames 1000 --out benchmark_report.json
```

The harness needs no microphone, no speaker, no Bluetooth, and no
audiogram. It can be run on a developer laptop, a Raspberry Pi 5, a
CI runner or a clean-room lab machine — the resulting numbers are
directly comparable because the input signal, the DSP code and the
algorithm parameters are all pinned.

## 2. What it measures

For each of the four core Python DSP stages —
[`SpectralSubtractor`](../dsp/noise_reduction.py),
[`WDRCompressor`](../dsp/compression.py),
[`VoiceClarityEnhancer`](../dsp/voice_clarity.py),
[`FeedbackCanceller`](../dsp/feedback_canceller.py) — and for the full
chain stitched together in pipeline order, the harness reports:

| Field                  | Meaning |
|------------------------|---------|
| `frames`               | Number of frames timed (after warm-up). |
| `frame_duration_ms`    | Real-time audio duration of one frame at the configured sample rate. |
| `p50_ms` / `p95_ms` / `p99_ms` / `max_ms` | Wall-clock processing time percentiles per frame. |
| `mean_ms`              | Mean processing time per frame. |
| `realtime_factor_p95`  | `frame_duration_ms / p95_ms`. Values > 1 indicate the stage is real-time at the 95th percentile; values < 1 indicate it is *not* real-time. |

The first 10 % of frames are discarded as warm-up so that interpreter
JIT, BLAS first-call costs and cache effects do not dominate the
percentiles.

## 3. Why the numbers can be trusted

1. **Deterministic input.** The audio buffer is generated from a
   fixed seed (`0xCAFEBABE`) as a mixture of low-amplitude white
   noise plus 440 Hz and 2 kHz sinusoids. The same buffer is fed to
   every stage on every run.
2. **Bit-parity guard.** Before timing, the harness re-runs every
   stage on a separate fixed golden frame (`tests/golden/`) and
   refuses to emit a report unless the output matches the committed
   reference within ~1 LSB at single precision. This means a
   benchmark report is, by construction, a benchmark of an
   *unchanged* algorithm. CI enforces the same parity check via
   [`tests/test_golden_vectors.py`](../tests/test_golden_vectors.py).
3. **Self-signed report.** The JSON report contains a
   `report_sha256` field whose value is the SHA-256 of the report
   body with that field nulled out. A reader can recompute and
   verify it independently — no external trust required, in keeping
   with the [Burgess Principle](BURGESS_PRINCIPLE.md).
4. **Provenance fields.** Every report carries `git_sha`, host
   platform, machine type, Python version and numpy version so that
   apparent regressions can be diagnosed without extra metadata.

## 4. Interpreting a report

A typical developer-laptop run on the current Python pipeline
(numbers will differ on your hardware; this is illustrative, **not** a
performance claim):

```
config: { "sample_rate": 16000, "frames_per_buffer": 256 }
=> frame_duration_ms = 16.0

stages:
  noise_reduction.p95_ms ≈ 0.04  (realtime_factor ≈ 400×)
  voice_clarity.p95_ms   ≈ 0.02  (realtime_factor ≈ 800×)
  compression.p95_ms     ≈ 0.50  (realtime_factor ≈ 30×)
  feedback.p95_ms        ≈ 3.20  (realtime_factor ≈ 5×)
  full_pipeline.p95_ms   ≈ 3.85  (realtime_factor ≈ 4×)
```

Key reading guidance:

* `full_pipeline.p95_ms` is the only number that should be quoted in
  external communications. Single-stage numbers are diagnostic, not
  promotional.
* `realtime_factor_p95 > ~3` is the working threshold for "real-time
  capable on this CPU". Below ~1.5, the pipeline is at risk of
  buffer underrun under load.
* The benchmark measures **DSP cost only**. Real end-to-end
  microphone-to-output latency adds the audio I/O round-trip, which
  is platform-specific and tracked separately by
  [`stream/latency.py`](../stream/latency.py) once a real device is
  attached.

## 5. Honest limitations (read this before quoting numbers)

The current harness measures what it can measure honestly. The
following are **explicit gaps** that Workstream A will close in
days 31–90 and beyond; until then, do not paper over them.

* **No audio I/O included.** Microphone capture, output buffering and
  Bluetooth transport latency are not measured here. Sub-5 ms claims
  cannot be made from this report alone.
* **No power measurement.** Wall-clock time is not energy. A separate
  campaign on a USB power meter is required for the
  `<50 mW` Phase 3 target.
* **CPython, not the future native core.** The Phase 1 plan calls for
  a C++/Rust port (Day 31–60). When that lands, the same harness
  will time both implementations and emit them as parallel sections,
  so absolute numbers can be compared like-for-like.
* **No Raspberry Pi 5 numbers committed yet.** The repository does
  not yet include a benchmark report from a Pi 5. The harness will
  produce one as soon as a unit is on a contributor's bench;
  contributions of `benchmark_report.json` files for diverse hosts
  are explicitly invited (see §7).

## 6. Regenerating golden vectors (rare, deliberate)

Golden vectors freeze the *current* DSP behaviour. You only
regenerate them after an intentional algorithmic change — for
example, a bug fix, a new compression algorithm, or an upstream
numpy change that legitimately alters numerical output.

```bash
python -m scripts.benchmark --regen-golden
git diff tests/golden/   # review the diff carefully
git add tests/golden/
# add a CHANGELOG entry explaining *why* the algorithm changed.
```

If the parity check ever fails unexpectedly in CI, that is the
desired behaviour: a silent change to a DSP coefficient is exactly
what this guard exists to catch.

## 7. Contributing a report

Run the benchmark on your hardware and open a PR adding the JSON to
`docs/benchmarks/<short-host-id>.json`. We particularly want runs
from:

* Raspberry Pi 5 (4 GB and 8 GB).
* Jetson Orin Nano.
* Apple Silicon (M1/M2/M3).
* Older x86 laptops, to bound the lower end.

A directory full of these reports is the cheapest credible answer to
the question "does OpenHear actually run in real time?" — and it is
the kind of artefact a grant reviewer or journal editor can verify in
60 seconds.
