# OpenHear Wristband — v0 Haptic Encoding Specification

> **Status:** frozen baseline (v0). Reference implementation:
> [`wristband/encoding/v0.py`](v0.py). Test suite:
> [`tests/test_wristband_encoding_v0.py`](../../tests/test_wristband_encoding_v0.py).
>
> **⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE.** This encoding is a research
> baseline for psychoacoustic falsification. It has not been clinically
> validated. Do not rely on it as a substitute for an audiologist-fitted
> hearing aid.

## 1. Purpose

The v0 encoder defines an unambiguous, deterministic mapping from a
mono audio frame to an array of motor drive values for the OpenHear
wristband. It exists so that:

1. The aspirational claim in the README ("the wristband IS the
   hearing system") can be tested rather than asserted.
2. Every psychoacoustic experiment in this repository (and any
   independent replication) targets the *same* algorithm bit-for-bit.
3. Future encoders (v1, v2, ...) have a **falsifiable baseline** to
   beat. A new encoder is only promoted if it improves at least one
   pre-registered metric on the standard battery (see
   [`docs/HAPTIC_PRIOR_ART.md`](../../docs/HAPTIC_PRIOR_ART.md) for
   the list of candidate metrics).

This document specifies *what* v0 does. The reference implementation
specifies *how*. If the two disagree, the reference implementation is
authoritative and this document is a bug.

## 2. Scope and non-goals

**In scope.** A frame-by-frame mapping
`(audio_frame_float32) → (motor_drive_float32[N_BANDS])` suitable for
driving a 4-motor LRA array around the wrist.

**Out of scope.**

* Spatial sound-source localisation. v0 conveys spectral content, not
  direction. Direction-of-arrival encodings will be defined in a
  separate v1+ specification.
* Speech intelligibility. v0 is not expected to deliver speech
  intelligibility on its own; conveying broadband envelope structure
  is sufficient for the v0 success criteria.
* Firmware-level safety limiting, PWM ramping, motor self-test, or
  battery management. These belong to the wristband firmware layer
  (`wristband/openhear_firmware.py`).
* Adaptation to an individual audiogram. v0 is audiogram-agnostic;
  audiogram-driven re-mapping is reserved for v1+.

## 3. Algorithm

Given a mono frame `x[n]` of `frame_length` real-valued samples in
`[-1.0, 1.0]` at `sample_rate` Hz:

1. **Spectrum.** Compute `X = rfft(x)`.
2. **Band split.** Partition the frequency axis into `N_BANDS = 4`
   contiguous bands using crossover frequencies
   `c = (500, 1000, 2000)` Hz:

   | Band | Lower edge (Hz) | Upper edge (Hz) | Notes |
   |------|----------------:|----------------:|-------|
   | 0    | 0   | 500  | low / fundamentals |
   | 1    | 500 | 1000 | low-mid / vowel formants |
   | 2    | 1000 | 2000 | speech intelligibility cues |
   | 3    | 2000 | Nyquist | high / consonants, sibilance |

   For each band, build a binary FFT-bin mask: bin `k` is in-band iff
   `low_edge ≤ freqs[k] < upper_edge` (the final band is inclusive of
   Nyquist so no energy is silently discarded).
3. **Per-band envelope.** For each band `i`, reconstruct the
   band-passed signal `b_i = irfft(X · mask_i, n=frame_length)`, then
   compute its RMS: `r_i = sqrt(mean(b_i**2))`.
4. **dBFS conversion.** For each band, `db_i = 20 · log10(r_i)`,
   defining `r_i = 0` as `db_i = -∞` (handled by deterministic clamp
   to drive 0).
5. **Drive mapping.** Linearly interpolate `db_i` from the published
   dynamic window `[DB_FLOOR, DB_CEILING] = [-60 dBFS, -10 dBFS]` to
   `[0.0, 1.0]`, clipping outside this range:

       drive_i = clip( (db_i − DB_FLOOR) / (DB_CEILING − DB_FLOOR), 0, 1 )

6. **Output.** Return `drive` as a `float32` array of length 4. Motor
   ordering is fixed: motor 0 is the lowest band and is mounted on the
   anatomical *ulnar* (pinky-side) face of the wrist; motor 3 is the
   highest band and is mounted on the *radial* (thumb-side) face.

## 4. Frozen constants

These constants define v0. Changing any of them produces a
non-conformant encoder which **must** be reported as such in any
published result.

| Constant      | Value          | Meaning |
|---------------|---------------:|---------|
| `N_BANDS`     | 4              | Number of bands and motors. |
| `crossovers_hz` | (500, 1000, 2000) | Inter-band crossover frequencies. |
| `DB_FLOOR`    | −60 dBFS       | RMS level mapped to drive 0.0. |
| `DB_CEILING`  | −10 dBFS       | RMS level mapped to drive 1.0. |
| `frame_length` (default) | 1024 samples | Analysis window size. |
| `sample_rate` (default)  | 16 000 Hz    | Matches the DSP pipeline. |

Permitted (and reported) overrides without breaking v0 conformance:

* `sample_rate` may be any positive integer ≥ 8 kHz, provided the top
  crossover stays below Nyquist.
* `frame_length` may be any power of two ≥ 64 samples. Frame length
  trades temporal resolution against spectral resolution; both must
  be reported.

## 5. Determinism and reproducibility

* The encoder is **stateless** across frames. Two identical input
  frames always yield identical output drives.
* The implementation depends only on numpy. Floating-point output is
  reproducible bit-for-bit on a fixed numpy + CPU vendor pairing; minor
  trailing-LSB differences across BLAS vendors are tolerated and
  exercised by the test suite.
* A canonical test vector and expected output array are committed
  under `tests/golden/` so that any port (C++, Rust, embedded firmware)
  can be parity-checked against this reference.

## 6. Success criteria for v0

v0 itself is the **null model**. It succeeds if:

1. The reference implementation passes its unit tests
   (`tests/test_wristband_encoding_v0.py`).
2. It can be run end-to-end on a 30-second audio clip in real time on
   a Raspberry Pi 5 (≥ 30 frames/s at the default frame length).
3. A pre-registered psychoacoustic battery (n=10 normal-hearing
   participants, see `experiments/haptic_battery/` once implemented)
   produces a measurable accuracy distribution — *positive, null, or
   negative* — with confidence intervals. v0 is **not** required to
   exceed chance performance to be useful; it is required to be the
   honest baseline against which v1+ are measured.

## 7. What v1 must improve

Concrete avenues for v1, none of which are claimed by v0:

* Audiogram-aware band weighting (per-user calibration).
* Cochlea-style logarithmic ERB band spacing instead of octave bands.
* Temporal envelope smoothing (e.g. Hilbert envelope + low-pass) to
  reduce flicker and improve perceptual stability.
* Phase-locked spatial encoding for sound-source direction (would
  require an additional input: a stereo or microphone-array stream).
* Adaptive AGC across bands so that quiet but informationally rich
  bands (e.g. consonants) are not masked by loud low-band rumble.

Each of these represents one falsifiable hypothesis and is an
explicit invitation for contributors and academic partners to
propose, implement, and test against v0.
