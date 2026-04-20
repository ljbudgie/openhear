# Advocacy Integration — the Burgess Principle extension point

> **Advisory only. Not legal advice. Not a medical device.**
> OpenHear is experimental. This document describes an optional,
> offline extension point; nothing here makes a decision on your
> behalf.

OpenHear's eighth pillar — *Sovereign Philosophy Enforced at Every
Layer* — explicitly adopts the **Burgess Principle** as a binary test
applied to every feature:

> Was a human judicial mind applied to the specific facts of this
> specific case?

The `advocacy/` package is the minimal, dependency‑free extension
point that lets a sovereign‑advocacy companion — for example
[Iris](https://github.com/ljbudgie/Iris), the reference Burgess
Principle implementation — answer that question against OpenHear
records (audiograms, fitting profiles, MPO safety calculations)
without OpenHear ever importing the companion, depending on it, or
phoning home to it.

This document describes the v1.0.0 contract. It is deliberately
small. The full advocacy workflow (tribunal‑ready bundles, draft
challenge language, receipt verification UI, shared vault formats)
lives in the companion, not here.

## What the adapter does

1. Takes a sovereign OpenHear record (e.g. an audiogram in the
   `openhear-audiogram-v1` JSON shape).
2. Produces a **SHA‑256 commitment** over a canonical serialisation
   of that record. The commitment is the only value intended to
   leave the device.
3. Accepts a returning **receipt**, verifies it against the
   commitment, and tags the record:
   - `SOVEREIGN` — a real human personally reviewed the specific
     facts of this case.
   - `NULL` — no individual human review (pure automation, blanket
     policy, or invalid receipt).
4. Emits an **export bundle** carrying the commitment, the receipt
   (if any), the tag, dual advisory disclaimers, and plain‑English
   verification instructions. The bundle never contains the
   sovereign facts themselves.

## What the adapter does *not* do

- It does not talk to the network.
- It does not pick a cryptographic library for you. Signature
  verification is delegated to a caller‑supplied `Verifier`. An
  `hmac_verifier(key)` is included for testing and the simplest
  on‑device sovereign‑vault case.
- It does not persist anything to disk. Persistence is the
  companion's job.
- It does not emit raw environmental audio. Attempting to commit a
  `bytes`, `bytearray`, `memoryview`, or NumPy `ndarray` anywhere
  inside the facts raises `RawAudioRejectedError`. The wristband's
  edge‑AI classifier produces classifications and fingerprints, not
  PCM, and the adapter enforces that invariant at the type boundary.

## Public API

```python
from advocacy import (
    # Primitives
    PersonGate, Commitment, Receipt, Record,
    SOVEREIGN, NULL,
    commit, verify, hmac_verifier,
    # Adapters
    audiogram_commitment, fitting_commitment, mpo_commitment,
    RawAudioRejectedError,
    # Export bundle
    export_record,
    MEDICAL_DISCLAIMER, ADVISORY_DISCLAIMER,
)
```

## Shape of the record types

### `Commitment`

```
record_id:   UUID (str)
label:       "audiogram" | "fitting" | "mpo" | <caller-defined>
digest:      SHA-256 hex over canonical JSON of the facts
tags:        tuple of strings (domain tags prepended by the adapter)
created_at:  ISO-8601 UTC timestamp
```

Serialises via `commitment.to_dict()`. Schema string:
`openhear-advocacy-commitment-v1`.

### `Receipt`

```
record_id:             must match the commitment
digest:                must match the commitment
signature:             opaque, verified by the caller-supplied Verifier
reviewer:              free-text identifier ("Dr Smith", "automated", …)
human_review_claimed:  bool — claim that a human reviewed the facts
received_at:           ISO-8601 UTC timestamp
```

Schema string: `openhear-advocacy-receipt-v1`.

### Export bundle

Schema string: `openhear-advocacy-bundle-v1`. A JSON‑serialisable
dict. Fields:

- `commitment` — see above.
- `receipt` — see above, or `null`.
- `tag` — `"SOVEREIGN"`, `"NULL"`, or `null`.
- `disclaimers.medical` — hard‑coded; see `MEDICAL_DISCLAIMER`.
- `disclaimers.advisory` — hard‑coded; see `ADVISORY_DISCLAIMER`.
- `verification.algorithm` — `"sha256"`.
- `verification.instructions` — plain‑English recipe a tribunal can
  follow to independently recompute the digest from the original
  facts and confirm the binding.

## Canonical serialisation

The digest is computed over

```python
json.dumps(facts, sort_keys=True, separators=(",", ":"),
           ensure_ascii=False).encode("utf-8")
```

Choosing sorted keys and no whitespace means the same logical record
always produces the same digest regardless of Python dict ordering,
which is what makes tribunal‑side verification practical.

## Example — audiogram round‑trip

```python
from advocacy import PersonGate, hmac_verifier, audiogram_commitment, export_record

audiogram = load_audiogram("audiogram/data/burgess_2021.json")  # or any openhear-audiogram-v1 dict

gate = PersonGate(verifier=hmac_verifier(my_local_key))
commitment = gate.commit("audiogram", audiogram,
                         tags=("audiogram", "workplace-adjustment"))

# Share only `commitment.to_dict()` with the external party.
# When they reply, wrap the reply as a Receipt and call:
record = gate.receive(commitment.record_id, receipt)

if record.tag == "SOVEREIGN":
    ...  # human review confirmed
else:
    bundle = export_record(gate, commitment.record_id)
    # Hand `bundle` to the advocacy companion to draft a challenge.
```

## Integration invariants (what a companion may rely on)

1. The package is pure‑Python and depends only on the standard
   library.
2. It performs no I/O beyond what the caller passes in.
3. Commitment digests are stable across Python versions and dict
   orderings.
4. Both disclaimers are always present in every export bundle and
   cannot be suppressed by callers.
5. Raw audio is rejected before any commitment is produced.

## Post‑v1.0.0 roadmap

- Receipt signature verification with an asymmetric verifier
  contributed by the companion.
- A shared vault format negotiated with Iris.
- A combined bundle that links an OpenHear record to a case file
  held in the companion (links only — never facts).
