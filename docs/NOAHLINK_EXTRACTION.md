# Noahlink extraction — schema, safety, and the mock Phonak adapter

> **⚠️ NOT A MEDICAL DEVICE.** Nothing in this document or in the
> `core.noahlink.*` modules has been clinically validated. Read the
> repository [`README`](../README.md) and [`SECURITY.md`](../SECURITY.md)
> before connecting any of this code to real hearing aids.

This document covers the Phase A work added in May 2026:

* a versioned, on-disk extraction schema (`openhear-extraction-v1`)
  that supersedes the ad-hoc shape previously produced by
  `core/read_fitting.py`,
* a configurable safety evaluator (`core.safety`) that flags
  dangerously high gain, missing limiters, and implausible compression
  parameters,
* a refactored `core.noahlink` package with a `vendors/` subpackage,
* a **read-only, feature-flagged, mock-backed** Phonak adapter for
  development without hardware in the loop,
* the new `openhear-noahlink` subcommands `extract`, `backup`, and
  `validate`.

What is **not** in this PR:

* A real Phonak (or Signia, ReSound, Oticon, Widex) protocol
  implementation.  Those protocols are proprietary; OpenHear will not
  ship code that pretends to read or write them without hardware
  verification.
* An embedded C++/Zephyr port of the DSP pipeline — Phase B.
* An OpenEarable firmware overlay or LE-Audio support — Phase C.
* A wizard composing backup → build → flash — Phase D.
* PyPI publish, Web-Assembly demo, NAL-NL2, real Phonak write paths —
  Phase E.

## Why a new schema?

`core.fitting_data.FittingSession` already carries gain tables,
compression profiles, MPO profiles, programmes and an audiogram.  But
several things a clinical extraction needs are missing:

* **Bone-conduction (BC) thresholds** alongside air-conduction (AC),
  so the audiometric picture is complete.
* **RECD** (Real-Ear-to-Coupler Difference) per ear, so coupler
  measurements can be translated to in-ear SPL.
* **Provenance** — which adapter produced the document, whether that
  adapter has been verified against real hardware, and how confident
  it is in the parsed values.
* **Safety flags** carried *in* the document so a backup remembers the
  warnings it shipped with.
* A **deterministic SHA-256 commitment** so a user can later prove
  their backup has not been tampered with.

`core.schema.extraction_v1.ExtractedFitting` is that document.  It
re-uses the existing `DeviceInfo`, `GainTable`, `CompressionProfile`,
`MPOProfile`, `ProgrammeSlot` and `Audiogram` dataclasses unchanged
and adds `BoneConductionAudiogram`, `RECDProfile`, and
`ExtractionSafetyFlag` for the new fields.

The schema version constant `openhear-extraction-v1` is the only
version this PR understands; bumping it means adding
`extraction_v2.py`, never editing v1 in place.

### Why dataclasses, not Pydantic v2?

The original plan called for Pydantic v2.  Every existing typed
schema in this repo (`Audiogram`, `FittingSession`, etc.) is a
dataclass with manual `__post_init__` validation and explicit
`to_dict`/`from_dict`/`to_json`/`from_json` methods.  Adding Pydantic
just for this module would be inconsistent and would pull a new
runtime dependency for marginal gain; the dataclass implementation
gets the same validation guarantees with the same shape as the rest
of the codebase.  This choice can be revisited when other modules
migrate.

## SHA-256 commitment

`ExtractedFitting.canonical_json()` returns a deterministic JSON
encoding (`sort_keys=True`, compact separators).
`sha256_commitment()` hashes that.  Because it is deterministic, the
same document always produces the same digest on every platform — so
a manifest written today can be verified against the file on disk
years later.

The `backup` CLI writes that commitment into
`manifest.json` under `extraction_commitment_sha256`, *alongside* the
file-level SHA-256 (`extraction_sha256`).  The file-level hash
catches tampering with the JSON text (including reformatting); the
commitment hash catches tampering with the parsed content even if
the JSON text was re-serialised.

## Safety evaluation

`core.safety.evaluate_session` and `core.safety.evaluate_extraction`
return a `SafetyReport`:

| Flag code                  | Level      | Default trigger                              |
|----------------------------|------------|----------------------------------------------|
| `gain_exceeds_ceiling`     | critical   | insertion gain > 60 dB                       |
| `negative_gain`            | warning    | insertion gain < 0 dB                        |
| `compression_ratio_high`   | warning    | ratio > 8.0:1                                |
| `compression_ratio_low`    | warning    | ratio < 1.0:1 (expander)                     |
| `mpo_missing`              | critical   | MPO profile absent and `require_mpo=True`    |
| `mpo_exceeds_ceiling`      | critical   | MPO > 130 dB SPL                             |
| `adapter_unverified`       | warning    | `is_verified=False` (extractions only)       |
| `low_confidence`           | info       | `confidence < 0.5` (extractions only)        |

Defaults are tunable through `SafetyThresholds`.  A report `passed`
only when no `critical` flags were raised; `warning` and `info` do
not block, but the CLI surfaces them so callers can decide.

## The Phonak adapter is a mock

`core.noahlink.vendors.phonak.PhonakMockAdapter` is **read-only**,
**mock-backed**, and **feature-flagged**:

* `WRITE_SUPPORTED` is `False` at the module level.
  `raise_if_write_disabled()` is provided so callers can fail loud
  before constructing a write request.
* `read()` raises `RuntimeError` unless
  `OPENHEAR_ENABLE_PHONAK_MOCK=1` is set in the environment.  This
  forces an explicit opt-in so the mock cannot be used in production
  by accident.
* Every emitted document has `vendor_adapter="phonak.mock"`,
  `is_verified=False`, `confidence=0.0`, and carries a
  `mock_data` safety flag in `safety_flags`.
* Every CLI command that exposes mock output prints
  `*** UNVERIFIED MOCK DATA — DO NOT WRITE TO A REAL HEARING AID ***`
  to stderr.

Until a real Phonak Marvel/Lumity/Infinio extraction has been
validated end-to-end against hardware, no other adapter will ship.

## CLI reference

```text
openhear-noahlink extract  --aid <vendor> [--json] [--output FILE] [--device-serial SN]
openhear-noahlink backup   --aid <vendor>  --output DIR        [--device-serial SN] [--list-adapters]
openhear-noahlink validate PATH
openhear-noahlink enumerate                                    # hardware path
openhear-noahlink sniff   [--duration SEC] [--log PATH]        # hardware path
```

`extract` runs the named vendor adapter and prints / writes an
`openhear-extraction-v1` JSON document.

`backup` writes a timestamped directory containing
`extraction.json` (the document), `raw.bin` (the raw HID payload, or
empty for mock adapters), and `manifest.json` (SHA-256 manifest +
commitment).

`validate` parses an extraction JSON, applies the safety evaluator,
and exits `0` on pass, `1` on a critical safety finding, `2` on a
schema error.  Use it in CI to gate any change that touches an
extraction document.

`enumerate` and `sniff` are unchanged from before; they require a
plugged-in Noahlink Wireless 2 dongle.

## Adding a new vendor adapter

1. Create `core/noahlink/vendors/<vendor>.py` exposing
   `read_extraction()` and a `<Vendor>MockAdapter` class.
2. Add `WRITE_SUPPORTED = False` at module level and a
   `raise_if_write_disabled()` helper if writes are out of scope.
3. Register the adapter in `core/noahlink/vendors/__init__.py`'s
   `available_adapters()` mapping.
4. Add the dispatch branch to `_run_vendor_adapter` in
   `core/noahlink/__init__.py`.
5. Ship tests in `tests/test_phase_a_extraction.py` (or a sibling file)
   covering the feature flag, the safety report, and round-trip
   serialisation.

Until the adapter has been validated against real hardware of the
named model/platform, `is_verified` MUST remain `False`.

## Open issues / next steps

* Real Phonak Marvel/Lumity/Infinio adapter (requires hardware).
* Signia AX, ReSound, Oticon, Widex adapters (each needs its own
  hardware verification).
* Embedded-side schema bindings (Phase B).
* Hook `validate` into a pre-commit / CI check that any committed
  example fitting passes the safety evaluator.
