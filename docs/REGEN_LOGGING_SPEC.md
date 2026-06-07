# Regeneration Support — Logging Schema & Advocacy Integration (Technical Spec)

> **Scope.** This spec defines the OpenHear-side data model and integration
> for capturing the *baselines, training events, and outcomes* needed to
> support a user before and after any biological hearing intervention.
> It is an **[OPENHEAR]** assistive specification. It does not regenerate
> biology, deliver therapy, or give clinical advice. See
> [`REGEN_VISION.md`](../REGEN_VISION.md) for the framing and evidence
> base; see [`BURGESS_PRINCIPLE.md`](BURGESS_PRINCIPLE.md) and
> [`ADVOCACY_INTEGRATION.md`](ADVOCACY_INTEGRATION.md) for the sovereignty
> contract this spec extends.

**Status:** Draft v0.1 · Target: §7 short-term milestone "Baseline/outcome
logging schema v1" in `REGEN_VISION.md`.

---

## 1. Goals and non-goals

**Goals.**

1. A single, versioned, append-only record type that captures the four
   regeneration-support signal families: **audiogram**, **speech-in-noise**,
   **haptic-perception**, **functional-log**.
2. Every record is **committable** through the existing advocacy gate
   (`advocacy/gate.py`) using the existing `commit(label, facts, tags)`
   primitive and verifiable offline by any holder of the bundle.
3. **Pre / during / post** intervention context is a first-class field, so
   a person can prove what their hearing looked like before and after a
   clinical event without surrendering the raw data to a vendor.
4. **No new schema family.** Records reuse the `openhear-advocacy-v1`
   schema family (`openhear-advocacy-commitment-v1`,
   `openhear-advocacy-receipt-v1`, `openhear-advocacy-bundle-v1`) per
   Burgess Principle commitment 5 (schema ownership is singular).

**Non-goals.**

1. Diagnostic interpretation. Records are *measurements*, not clinical
   judgements.
2. Recommending or scheduling biological therapy.
3. Cloud sync, fleet aggregation, or any network I/O beyond what the user
   explicitly initiates.
4. A new wire format. JSON over the existing canonical serialisation only.

---

## 2. Record families

All four families are plain JSON-serialisable mappings. None may contain
raw audio (`bytes`, `bytearray`, `memoryview`, `numpy.ndarray`); the
existing `RawAudioRejectedError` gate in `advocacy/adapters.py` is the
enforcement point.

### 2.1 `regen-audiogram-v1`

A versioned wrapper around the existing audiogram JSON shape used by the
`audiogram/` package. Adds:

- `record_id` — UUID, caller-supplied or generated.
- `recorded_at` — ISO-8601 UTC timestamp.
- `intervention_phase` — `"none" | "pre" | "post"` (default `"none"`).
- `intervention_ref` — optional opaque string identifying the clinical
  event the record relates to (e.g. a user-chosen label, never a vendor
  identifier).
- `audiogram` — the existing `openhear-audiogram-v1` dict, verbatim.
- `notes` — optional free-text, user-owned.

### 2.2 `regen-speech-in-noise-v1`

- `record_id`, `recorded_at`, `intervention_phase`, `intervention_ref` as
  above.
- `test` — short identifier of the test administered
  (e.g. `"matrix"`, `"hint"`, `"quicksin"`, `"custom"`); free-form
  string, user-owned.
- `snr_db` — the signal-to-noise ratio at which the score was measured.
- `score` — percent-correct (`0.0`–`100.0`) **or** SRT in dB; one of
  `score_percent` or `srt_db` must be present.
- `ear` — `"left" | "right" | "binaural"`.
- `conditions` — optional mapping for masker type, list length, etc.
- `notes`.

### 2.3 `regen-haptic-perception-v1`

Baseline and tracking for haptic substitution channels.

- `record_id`, `recorded_at`, `intervention_phase`, `intervention_ref`.
- `protocol` — identifier of the haptic test protocol (e.g. band count,
  encoding family); free-form string aligned with `wristband/` and
  `haptic_commander.py` capabilities.
- `metrics` — mapping of named scalar metrics (e.g.
  `discrimination_d_prime`, `phoneme_accuracy_pct`,
  `localisation_error_deg`). Values must be finite numbers; no arrays of
  raw signal.
- `notes`.

### 2.4 `regen-functional-log-v1`

Real-world participation and adherence — the signal most relevant to the
§3 critical-period discussion in `REGEN_VISION.md`.

- `record_id`, `recorded_at`, `intervention_phase`, `intervention_ref`.
- `category` — `"conversation" | "training" | "environment" | "adverse_event" | "other"`.
- `duration_seconds` — non-negative integer; `0` for instantaneous events.
- `context` — short structured mapping (e.g. `{"setting": "café",
  "people": 3, "background": "music"}`); strings and finite numbers only.
- `self_rating` — optional integer 1–5, user's subjective rating.
- `fatigue` — optional integer 0–10, user's reported fatigue at end of
  session (feeds the training-mode rest logic).
- `notes`.

### 2.5 Shared fields and rules

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `schema` | string | yes | One of the four `regen-*-v1` identifiers above |
| `record_id` | UUID string | yes | Caller-supplied or generated |
| `recorded_at` | ISO-8601 UTC string | yes | `Z`-suffixed, second precision |
| `intervention_phase` | enum | yes | `"none"` / `"pre"` / `"post"` |
| `intervention_ref` | string | no | User-chosen label only |
| `notes` | string | no | Free-text, user-owned |

Records are **append-only**. Corrections are new records that reference
the corrected `record_id` via `notes` or a future `supersedes` field
(introduced via a `-v2` schema, not by mutating `-v1`).

---

## 3. Advocacy integration

### 3.1 Commit path

A thin module `regen/commit.py` (to be added) exposes four adapter
functions that mirror the existing pattern in `advocacy/adapters.py`:

```
audiogram_record_commitment(record, tags=None)         -> Commitment
speech_in_noise_record_commitment(record, tags=None)   -> Commitment
haptic_perception_record_commitment(record, tags=None) -> Commitment
functional_log_record_commitment(record, tags=None)    -> Commitment
```

Each function:

1. Validates the record against §2 (type, required fields, enum values,
   finite numbers).
2. Calls the existing `_reject_raw_audio` walk to enforce commitment 4
   (no raw audio in facts).
3. Invokes the existing `commit(label, facts, tags)` from `advocacy.gate`
   with:
   - `label` — `"regen-audiogram"`, `"regen-speech-in-noise"`,
     `"regen-haptic-perception"`, `"regen-functional-log"`.
   - `facts` — the full record (deterministic ordering handled by the
     existing canonical serialisation).
   - `tags` — merged tuple of `("regen", <family>, "openhear-<family>-v1")`
     plus caller-supplied tags, deduplicated in order (reuse the
     `_merge_tags` helper).

No new schema family is introduced; the resulting commitment is an
`openhear-advocacy-commitment-v1` exactly as today.

### 3.2 Verify path

Verification is **unchanged**. Any holder of a bundle uses the existing
offline `verify` API in `advocacy.gate` to recompute the SHA-256 digest
over the canonical serialisation of the facts and compare it to the
commitment. No vendor involvement, no network, no new code path.

### 3.3 Export bundle

Existing `export_record(gate, record_id)` from `advocacy/bundle.py` is
sufficient. The returned `openhear-advocacy-bundle-v1` carries the
commitment, the receipt (if any), the review tag, and both hard-coded
disclaimers. A regen record exports identically to an audiogram or MPO
record today.

### 3.4 Receipts and the SOVEREIGN/NULL gate

A regen record presented to a clinician for review goes through the
existing `PersonGate` workflow:

- A real clinician personally reviewing the specific record and signing a
  receipt produces `SOVEREIGN`.
- Anything else (automation, blanket policy, invalid signature,
  unresolvable verification, refusal to engage) produces `NULL`.
- There is no third state.

This means **OpenHear cannot itself produce a SOVEREIGN tag** on regen
records — it produces commitments and bundles; sovereignty is a property
of human review, not of the software.

---

## 4. Storage and lifecycle

- **Local-first.** Records live in the user's existing OpenHear data
  directory. No cloud sync ships with this spec.
- **Append-only on disk.** One file per record (`<record_id>.json`) under
  a per-family subdirectory. Atomic write + rename.
- **Indexing.** A lightweight local index file maps `record_id` →
  `(family, recorded_at, intervention_phase)` for fast listing. The index
  is a derived artefact; deleting it must not lose data.
- **Export.** User-initiated only. Producing a bundle never modifies the
  source record. Bundles are written to a user-chosen path.
- **Deletion.** User-initiated only. Deletion removes the local file and
  the index entry; previously exported bundles remain valid for offline
  verification by the holder.

---

## 5. Validation, safety, and refusal rules

The adapter must refuse to commit, with a specific exception class, when:

1. `schema` is not one of the four `regen-*-v1` identifiers.
2. Any required field from §2.5 is missing or has the wrong type.
3. `intervention_phase` is outside the allowed enum.
4. Any number is `NaN` or infinite.
5. Any value in the record is detected as raw audio
   (`RawAudioRejectedError`, reused).
6. `recorded_at` is not a valid ISO-8601 UTC string.

Refusal is preferred over silent normalisation: commitment 3 (binary
SOVEREIGN/NULL) forbids ambiguous outcomes, and that discipline extends
to the data layer.

---

## 6. Claim-language discipline

Per `REGEN_VISION.md` §8.2:

- No code, comment, log message, UI string, or commit message produced
  by this subsystem may claim that OpenHear regenerates, repairs, cures,
  or restores biological hearing.
- Approved framing: *"OpenHear records sovereign baselines and outcomes
  so the user can take them to whoever provides their care."*
- The claim-lint check planned for `REGEN_VISION.md` §7 short-term
  applies to this subsystem's documentation and any user-facing strings.

---

## 7. Out of scope for v1

- Bulk migration of historical audiogram files (separate utility).
- A graphical timeline view (future `mobile/` work).
- Multi-user / family-shared records (handled by user-initiated bundle
  sharing only).
- Vendor-specific identifiers in `intervention_ref` (deliberately
  excluded — the field is for the user's own labelling).

---

## 8. Acceptance criteria

The v1 implementation is complete when:

1. The four adapter functions exist, are covered by unit tests, and
   reject every refusal case in §5.
2. A round-trip test for each family writes a record, commits it,
   exports a bundle, and verifies the bundle offline without network
   access.
3. `RawAudioRejectedError` is provably raised for `bytes`, `bytearray`,
   `memoryview`, and `numpy.ndarray` placed anywhere in a record.
4. `make ci` passes with no new lint or test regressions.
5. This spec, `REGEN_VISION.md`, and the docs index cross-link
   correctly.
