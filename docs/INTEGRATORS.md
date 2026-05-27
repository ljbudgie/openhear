# OpenHear Integration Guide
## For Hearing Industry Engineers and AI Coding Agents

> **Advisory only. Not legal advice. Not a medical device.**
> OpenHear is experimental. This guide describes how to integrate the
> Sovereign Advocacy Layer into manufacturer software, audiology
> platforms, and AI clinical systems. Nothing in this document or in
> the software it describes makes a clinical or legal decision on
> anyone's behalf.

---

### 1. Permission First

This guide is written for engineering teams — and AI coding agents
acting on behalf of those teams — who have received **written
permission from the author** to deploy the OpenHear Sovereign Advocacy
Layer in a production clinical environment.

Cloning the repository, reading the source, running the tests, and
experimenting locally is welcome and unrestricted. You do not need
permission to learn how the layer works, build a prototype, or
evaluate it against your own systems.

Permission is required before the layer is shipped inside a product
that touches real patient data in a real clinic.

To request permission, contact:

> **[CONTACT — author to complete]**

(See the repository `NOTICE` file. The contact placeholder is
intentional — the author completes it on a per-deployment basis.)

---

### 2. What You Are Integrating

OpenHear's Sovereign Advocacy Layer (`advocacy/`) is a tamper-evident,
cryptographic commitment layer for sovereign clinical records —
audiograms, fitting profiles, and MPO (maximum power output) safety
calculations. It produces a SHA-256 commitment over a canonical JSON
serialisation of the record, accepts a returning receipt from a
reviewing party, tags the record `SOVEREIGN` or `NULL` according to
whether a human judicial mind was actually applied, and emits an
offline export bundle that any third party can independently verify
with a few lines of stdlib Python. The layer runs entirely offline,
has zero runtime dependencies beyond the Python standard library, and
performs no I/O of its own.

It does **not** store data. It does **not** transmit data. It does
**not** make clinical decisions. It does **not** replace your existing
fitting software, your patient management system, your audiogram
viewer, your cloud, or your DSP pipeline. It is a trust layer that
sits *alongside* your system and produces verifiable evidence that a
specific clinical record was bound to a specific human reviewer at a
specific point in time. Your system continues to own the data, the
workflow, and the user interface; OpenHear adds the commitment and
the audit trail.

---

### 3. The Architecture Contract

These six rules are non-negotiable. An integration that breaks any of
them is not a valid OpenHear integration and may not be described as
one.

1. **One-way coupling.** Your system imports OpenHear. OpenHear never
   imports your system. There is no callback API, no plugin registry,
   no inversion of control. The dependency arrow points one way only.

2. **No network I/O, persistence, or telemetry may be added to the
   advocacy layer.** The layer is offline by construction. Do not
   patch in a logger that posts elsewhere, a cache that writes to
   disk, or a metric that phones home. Persistence is your system's
   job; the gate is in-memory by design.

3. **SOVEREIGN = human-verified commitment. NULL = automation,
   tampered, or unverifiable.** These two tags are the entire
   vocabulary. SOVEREIGN means a real human personally reviewed the
   specific facts of the specific case and signed a receipt that
   cryptographically binds to the commitment. NULL means anything
   else: the receipt was produced by automation
   (`human_review_claimed=False`), the signature failed verification,
   the digest does not match, or the receipt references a different
   record. Do not introduce a third tag, an "unknown" state, or a
   "SOVEREIGN-ish" intermediate. Downstream projects may *refine*
   NULL (for example `NULL_AUTO` vs `NULL_POLICY`), but the binary
   distinction at this layer must be preserved.

4. **`RawAudioRejectedError` is a hard type boundary.** If your
   system handles audio — and a hearing-industry system almost
   certainly does — extract the clinical facts from the audio
   on-device first. Never pass `bytes`, `bytearray`, `memoryview`, or
   a NumPy `ndarray` into `audiogram_commitment()`,
   `fitting_commitment()`, or `mpo_commitment()`. The adapter walks
   the facts payload (including nested mappings and lists) and
   raises `RawAudioRejectedError` if it finds any of those four
   types. Do not catch and silence this exception. If you genuinely
   need a byte string in the record, hex- or base64-encode it
   yourself first; that is a deliberate moment of consent.

5. **The bundle from `export_record()` is the only shareable
   artefact.** Sovereign facts (the audiogram thresholds, the fitting
   parameters, the MPO inputs) are never transmitted. The bundle
   contains the commitment digest, the receipt, the tag, the two
   advisory disclaimers, and plain-English verification instructions
   — nothing else. Do not extend the bundle with the source facts
   "for convenience".

6. **Do not version the `openhear-advocacy-v1` schema independently.**
   The three schema identifiers
   (`openhear-advocacy-commitment-v1`, `openhear-advocacy-receipt-v1`,
   `openhear-advocacy-bundle-v1`) are owned by this repository. If
   you need a change, request it upstream. Forking the schema breaks
   verifiability across the ecosystem.

---

### 4. Installation

The advocacy layer ships as part of the `openhear` distribution.

**From PyPI (when published):**

```
pip install openhear
```

**From source, for development:**

```
git clone https://github.com/ljbudgie/openhear.git
cd openhear
pip install -e .
```

**Runtime dependencies of the advocacy layer:** none beyond the
Python standard library. The layer uses only `hashlib`, `hmac`,
`json`, `uuid`, `dataclasses`, `datetime`, and `typing`. Other
OpenHear subsystems (DSP, wristband, audiogram visualiser) declare
NumPy, SciPy, PyYAML, and `hid`, but the advocacy layer itself does
not import them. You can use the advocacy layer in a stripped
installation with no scientific Python stack present.

**Minimum Python version:** 3.10 (matches `pyproject.toml`).

To run the advocacy test suite:

```
pip install -e .[dev]
pytest tests/test_advocacy.py
```

---

### 5. Choosing Your Adapter

Three adapters are exposed from the `advocacy` package. Each is a
thin wrapper around `commit()` that adds domain tags and enforces the
no-raw-audio invariant. Pick the adapter whose label matches the
clinical artefact you are committing.

| Adapter                  | Use case                                                                                              | What facts it expects                                                                                                                  | What it rejects                                                                                                                                          |
|--------------------------|-------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `audiogram_commitment`   | Commit an audiogram (thresholds for one or both ears, with subject, source, date metadata).           | A `Mapping` matching the `openhear-audiogram-v1` shape used by the `audiogram/` package — typically keys such as `subject`, `source`, `date`, `format_version`, `notes`, `right_ear`, `left_ear`, `classification`. The whole record is hashed. | Anything that is not a `Mapping` raises `TypeError`. Any `bytes`/`bytearray`/`memoryview`/NumPy `ndarray` anywhere in the structure raises `RawAudioRejectedError`. |
| `fitting_commitment`     | Commit a fitting profile (the structured DSP parameters applied to a user's aids).                    | A `Mapping` of DSP parameters — gain curves, compression ratios, own-voice bypass flags, program memory, etc. The schema is intentionally open: whatever you pass is hashed verbatim. | Same: non-`Mapping` → `TypeError`; any raw audio payload → `RawAudioRejectedError`. Domain tags `fitting`, `dsp-parameters` are added automatically. |
| `mpo_commitment`         | Commit a maximum power output safety calculation (the record that matters in headset/employer disputes). | A `Mapping` of MPO calculator output — typically the inputs and the calculated safe ceiling.                                          | Same: non-`Mapping` → `TypeError`; any raw audio payload → `RawAudioRejectedError`. Domain tags `mpo`, `safety-ceiling` are added automatically. |

All three adapters accept an optional `tags` iterable, which is
appended to the adapter's domain tags (deduplicated, domain tags
first). Use this to attach context such as `"gp-triage"`,
`"pre-fitting"`, `"post-adjustment"`, or your own institutional
identifiers.

The exact source of truth for these adapters is `advocacy/adapters.py`.
Read it before integrating; it is short.

---

### 6. Step-by-Step Integration

The following sequence is the integration. An AI coding agent can
follow it literally.

1. **Import the adapter for your data type, the gate, and the export
   helper.** From the `advocacy` package, import the adapter
   (`audiogram_commitment`, `fitting_commitment`, or `mpo_commitment`),
   the `PersonGate` class, the `Receipt` dataclass, the `hmac_verifier`
   helper (or your own `Verifier`), the `SOVEREIGN`/`NULL` tag
   constants, and `export_record`. Import `RawAudioRejectedError` so
   you can let it propagate or, if you must, log it before re-raising.

2. **Build the facts dict.** The dict is the canonical clinical
   record. The exact keys differ per adapter:
   - `audiogram_commitment` expects the `openhear-audiogram-v1`
     shape: `subject`, `source`, `date`, `format_version`, `notes`,
     `right_ear` and `left_ear` (each with `symbol` and a
     `thresholds` list of `{"freq_hz": int, "db_hl": int}` entries),
     and an optional `classification`. See
     `examples/sample_audiogram.json` for a fully populated example.
   - `fitting_commitment` expects whatever your fitting format
     contains. Use stable keys; the digest depends on them.
   - `mpo_commitment` expects whatever your MPO calculator emits.
   In all three cases the dict must contain no raw audio.

3. **Call the adapter to obtain a `Commitment`.** The adapter
   delegates to `commit()` in `advocacy/gate.py`. The signature of
   `commit` is:
   ```
   commit(label: str,
          facts: Mapping[str, Any],
          tags: Iterable[str] | None = None) -> Commitment
   ```
   You will normally not call `commit` directly; the adapters set the
   correct `label` and pre-populate the domain tags for you. To bind
   the commitment into a stateful gate (so a receipt can be
   processed against it), call `gate.commit(label, facts, tags=...)`
   on a `PersonGate` instance. `PersonGate.commit` returns the same
   `Commitment` and stores the record internally.

4. **Receive the commitment and inspect it.** A `Commitment` is a
   frozen dataclass with five fields: `record_id` (UUID4 string),
   `label` (e.g. `"audiogram"`), `digest` (hex-encoded SHA-256),
   `tags` (tuple of strings), and `created_at` (ISO-8601 UTC). Its
   `to_dict()` method emits the dict shape carrying the
   `openhear-advocacy-commitment-v1` schema identifier and the
   algorithm marker `"sha256"`. The digest is the only value you
   should hand to a reviewing party.

5. **Process the returning receipt.** A `Receipt` is a frozen
   dataclass with six fields: `record_id`, `digest`, `signature`
   (opaque to the gate; verified by the caller-supplied `Verifier`),
   `reviewer` (free-text identifier such as a name, role, or
   `"automated"`), `human_review_claimed` (boolean — the reviewer's
   claim that a human personally reviewed this case), and
   `received_at` (ISO-8601 UTC). Construct a `PersonGate` with a
   `Verifier`, then call `gate.receive(record_id, receipt)`. The
   gate verifies the receipt cryptographically and tags the record
   `SOVEREIGN` (valid signature *and* `human_review_claimed=True`)
   or `NULL` (anything else).

6. **Call `export_record()` to obtain the shareable bundle.** The
   signature is:
   ```
   export_record(gate: PersonGate, record_id: str) -> dict[str, Any]
   ```
   The returned dict is the bundle. Its top-level shape is:
   ```
   {
     "schema": "openhear-advocacy-bundle-v1",
     "commitment": { ... openhear-advocacy-commitment-v1 ... },
     "receipt":    { ... openhear-advocacy-receipt-v1 ... } | null,
     "tag":        "SOVEREIGN" | "NULL" | null,
     "disclaimers": {
       "medical":  "...experimental, not a medical device...",
       "advisory": "...advisory only, not legal advice..."
     },
     "verification": {
       "algorithm":    "sha256",
       "instructions": "...plain-English SHA-256 instructions..."
     }
   }
   ```
   The bundle is JSON-serialisable with `json.dumps`. It contains no
   sovereign facts.

7. **Verify the bundle independently.** The `verification.instructions`
   string in the bundle tells any third party — a tribunal, an
   auditor, a journalist, a patient — exactly how to recompute the
   digest from the original record:

   > Canonicalise the sovereign record as UTF-8 JSON with sorted keys
   > and no whitespace
   > (`json.dumps(..., sort_keys=True, separators=(',', ':'))`)
   > and compute its SHA-256 hex digest. It must exactly equal the
   > `'digest'` field of the `'commitment'` object.

   Recomputation requires only Python's stdlib (`json`, `hashlib`).
   No OpenHear install is needed to verify a bundle. This is
   deliberate.

---

### 7. What SOVEREIGN vs NULL Means for Your System

The two tags are the operational output of the layer. Your system
should treat them differently — and visibly so.

A record is tagged `SOVEREIGN` when, and only when, both conditions
hold inside `PersonGate.receive`:

1. The receipt cryptographically binds to the commitment — its
   `record_id` and `digest` match the stored commitment, and the
   caller-supplied `Verifier` accepts its signature.
2. The receipt's `human_review_claimed` flag is `True`.

Your system should **log SOVEREIGN records as evidence** that a human
judicial mind was applied. They are the records you want available
when a patient, an employer, an insurer, or a regulator asks "who
decided this, and on what basis?". Surface them in the patient's
record as a verifiable audit entry, not as a transient log line.

A record is tagged `NULL` in any of these situations, all of which
are produced by the same `PersonGate.receive` logic:

- The receipt's `human_review_claimed` flag is `False` — for example,
  an automated triage system signed the receipt itself, or a blanket
  policy was applied without individual review.
- The receipt's signature fails the `Verifier` (tampered, wrong key,
  forged).
- The receipt's `digest` does not match the commitment's `digest`
  (the underlying facts were modified after commitment).
- The receipt's `record_id` does not match the commitment's
  `record_id` (the receipt is for a different case).

Your system should **surface NULL records as challenges**. They are
exactly the cases where the Burgess Principle test failed: the
institutional decision was not bound to a human review of the
specific facts of the specific case. The companion advocacy tool
(Iris, post-v1.0.0) consumes the `gate.challenges()` list as its
starting point for drafting challenge language. Your system should
do the equivalent: route NULL records into a review queue, prompt
the user, or flag the decision for re-examination — never silently
treat NULL the same as SOVEREIGN.

---

### 8. Testing Your Integration

The advocacy layer ships with a 14-test contract suite at
`tests/test_advocacy.py`. Run it before and after your integration to
confirm the contract still holds. The 14 tests cover:

1. `test_audiogram_roundtrip_to_sovereign` — committing an audiogram
   and round-tripping a valid receipt produces a `SOVEREIGN` tag,
   and domain tags are preserved with extra tags appended.
2. `test_valid_receipt_without_human_review_is_null` — a
   cryptographically valid receipt with `human_review_claimed=False`
   produces `NULL` and appears in `gate.challenges()`.
3. `test_tampered_signature_is_null` — a receipt with a forged
   signature produces `NULL`.
4. `test_tampered_digest_is_null` — a receipt whose digest does not
   match the commitment's digest produces `NULL`.
5. `test_adapter_rejects_raw_pcm_bytes` — `bytes` in the audiogram
   facts raises `RawAudioRejectedError`.
6. `test_adapter_rejects_raw_pcm_in_nested_list` — `bytearray`
   nested inside a list inside a fitting profile raises
   `RawAudioRejectedError`.
7. `test_adapter_rejects_numpy_array` — a NumPy `ndarray` in MPO
   facts raises `RawAudioRejectedError` (without OpenHear importing
   NumPy at module load).
8. `test_adapter_rejects_non_mapping` — a non-`Mapping` argument
   (e.g. a list of tuples) raises `TypeError`.
9. `test_canonical_digest_is_order_independent` — committing the
   same audiogram in two different dict orderings produces the
   same digest (canonical serialisation).
10. `test_export_bundle_has_disclaimers_and_no_facts` — the export
    bundle carries both the medical and advisory disclaimers, the
    `SOVEREIGN` tag, and contains neither the subject name nor any
    threshold value from the source audiogram.
11. `test_export_bundle_digest_matches_recomputed_digest` — the
    digest in the bundle exactly equals the SHA-256 recomputed from
    the canonical JSON of the source record (the path a tribunal
    would follow).
12. `test_receive_without_verifier_raises` — calling `receive` on a
    `PersonGate` constructed without a verifier raises `ValueError`.
13. `test_receive_unknown_record_raises` — calling `receive` with a
    `record_id` the gate has not seen raises `KeyError`.
14. `test_module_level_commit_and_verify_roundtrip` — the
    module-level `commit` and `verify` functions round-trip
    correctly and reject a bad signature.

These tests cover the layer's contract. They do **not** cover your
domain logic: the correctness of your audiogram extraction, your
fitting parameter validation, your MPO calculator, your reviewer
identity flow, or your storage. Add tests for those in your own
suite. A reasonable shape is:

- A round-trip test through your adapter end-to-end (build facts →
  commit → receive a real receipt from your reviewer system →
  expect `SOVEREIGN`).
- A negative test that an automated reviewer in your system
  produces `NULL`.
- A property test that any record your system can produce passes
  the no-raw-audio check.

---

### 9. About Iris and the Burgess Principle

The Burgess Principle — *"Was a human judicial mind applied to the
specific facts of this specific case?"* — is the ethical and clinical
philosophy that governs this software. It is not a feature, a
component, or a marketing line; it is the question every layer of
OpenHear is built to answer honestly. Iris is an AI companion
agent being built within that same framework. Neither the Burgess
Principle nor Iris is a runtime dependency of this release. The
advocacy layer ships complete on its own.

Post-v1.0.0, Iris will provide a higher-level advocacy workflow —
tribunal-ready bundles combining case facts and draft challenge
language, receipt verification UI, shared vault formats — on top of
this layer. When Iris ships, it will import OpenHear, never the
reverse. Integrators who build correctly against this layer today
(one-way coupling, preserved tag semantics, no schema fork) will be
compatible with Iris automatically. There is no need to wait, and
no benefit to deferring integration in anticipation of Iris.

---

### 10. Post-v1.0.0 Roadmap

The following items are deferred to post-v1.0.0 work. They are
**additions**, not fixes. The current layer is stable and complete
for its stated scope.

- **Iris as a (consuming) dependency.** Iris will import OpenHear and
  layer the full advocacy workflow on top.
- **Asymmetric signature verifier.** The current `hmac_verifier` is
  sufficient for on-device sovereign vaults and tests; an asymmetric
  verifier will be contributed by the companion for tribunal-grade
  use.
- **Shared vault format.** A negotiated on-disk format for the
  sovereign facts, shared between OpenHear and Iris.
- **Combined case-file bundles.** A bundle that links an OpenHear
  record to a case file held in the companion — links only, never
  facts.

These items are tracked in `docs/ADVOCACY_INTEGRATION.md`. They do
not change the v1.0.0 contract described above.
