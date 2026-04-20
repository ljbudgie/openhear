# Sovereign Philosophy — The Architecture of Trust

This is the deeper companion to
[`BURGESS_PRINCIPLE.md`](BURGESS_PRINCIPLE.md). Where the Principle
document states *what* OpenHear's advocacy layer commits to, this
document explains *why* each architectural decision was made the way it
was. It is written for senior engineers at hearing manufacturers, FDA
digital health reviewers, and medical AI ethics researchers — readers
who need to evaluate whether the design holds up under clinical and
regulatory scrutiny, not just whether the code runs.

## Why Offline-First

The advocacy layer performs no network I/O, emits no telemetry, and
persists nothing to disk. This is not a limitation imposed by scope; it
is the guarantee the layer exists to provide. A commitment that
requires a server to verify is not a sovereign commitment — it is a
service, and a service can be paywalled, deprecated, breached, or
withdrawn the moment its commercial logic shifts.

The clinical context makes this concrete. Devices fail. Clinic networks
go down. Manufacturers get acquired and their cloud endpoints are
retired with thirty days' notice. A hearing aid fitted in 2026 may
still be in use in 2036, and the patient or their clinician may need to
verify what was committed to long after the originating vendor's
infrastructure has been decommissioned. The bundle must be verifiable
in a room with no internet, ten years from now, by a party with no
relationship to the original system. Offline-first is the only
architecture that satisfies that requirement, so it is the architecture
the advocacy layer enforces.

## Why SHA-256 Canonical JSON

The commitment is a SHA-256 digest taken over a *canonical* JSON
serialisation of the facts: deterministic key ordering, fixed
separators, no insignificant whitespace. The exact recipe is given in
[`docs/ADVOCACY_INTEGRATION.md`](ADVOCACY_INTEGRATION.md#canonical-serialisation)
and is not restated here on purpose — there must be one canonical
description of the canonical form.

Canonicalisation matters because the same facts must always produce the
same digest, regardless of insertion order, the serialisation library
in use, the platform performing the serialisation, or the year in
which the verification is being done. Without canonicalisation the
commitment is fragile: a downstream verifier on a different runtime
can compute a different digest from the same logical facts and arrive
at a false `NULL`. With canonicalisation the commitment is portable
across languages, runtimes, and decades. The choice of SHA-256 follows
the same logic — it is widely available, well understood, and not
under realistic dispute as a fingerprinting primitive in the timeframe
this layer is meant to operate over.

## Why SOVEREIGN / NULL and Nothing Else

The tag vocabulary is binary. `SOVEREIGN` means a real human
personally reviewed the specific facts of this specific case and
signed a receipt that verifies against the commitment. `NULL` means
anything else: pure automation, blanket policy, an invalid or absent
signature, tampering, or a refusal to engage. There is no `PENDING`,
no `UNVERIFIED`, no `PARTIAL`, no `PROVISIONAL`.

The binary is a feature, not a simplification. Clinical systems built
on ambiguous trust states produce ambiguous clinical outcomes; a
"partially verified" record invites every downstream reader to
interpret the partiality in whichever direction suits them. A
clinician sees confirmation; a manufacturer sees a disclaimer; a
patient sees authority. The binary forces the question to be answered
honestly at the moment of verification: a human stood behind this
specific case, or no human did. Everything that is not `SOVEREIGN` is
`NULL`, and `NULL` is not a slur on the record — it is an accurate
description of what is and is not known about the human review behind
it.

## Why RawAudioRejectedError is a Type Boundary

Raw audio is rejected at the type level. The adapter inspects the
facts payload for `bytes`, `bytearray`, `memoryview`, and NumPy
`ndarray`, and raises `RawAudioRejectedError` before any commitment
is produced. The check is on the *type*, not on the values, the
field names, or any documented convention.

This decision is deliberate. Documentation is ignored — every engineer
under deadline pressure has shipped code that contradicted the README.
Runtime value checks are bypassable — a base64 string of PCM passes
any "looks like audio" heuristic and any naming check. Naming
conventions drift — a field called `audio_features` today becomes a
field called `payload` after the next refactor. A type boundary does
not drift: if the value is byte-like, the commitment is refused, and
no comment, rename, or refactor changes that.

The clinical consequence is what makes this worth enforcing so
strictly. Committing to a raw audio signal instead of an interpreted
clinical fact produces a meaningless commitment that nevertheless
looks valid: the digest is well-formed, the bundle verifies, and a
downstream reader has no way to tell that the underlying facts were
never reduced to anything a clinician can reason about. A commitment
that looks valid but is meaningless is the worst possible failure mode
for a trust layer, because it produces confident, unverifiable error.
The type boundary exists to make that failure unreachable.

## Why One-Way Coupling

OpenHear exposes the schema. Companions — including Iris — import
that schema. OpenHear never imports a companion. The coupling is
deliberately one-way.

This keeps the trust layer stable and independent. If OpenHear
imported Iris, a change in Iris could change the behaviour of the
commitment primitive, and a change in the commitment primitive
invalidates every existing commitment by changing what they actually
commit to. The advocacy layer's value rests on the fact that a bundle
produced by version 1.0.0 in 2026 is still verifiable by version
1.0.0's verifier in 2036 — and that property cannot survive a
dependency on a higher-level system that is permitted to evolve. The
coupling direction is therefore a clinical safety decision, not a
software-engineering preference about layering.

## Why Schema Ownership is Singular

Integrators cannot fork or independently version
`openhear-advocacy-v1`. The schema family
(`openhear-advocacy-commitment-v1`, `openhear-advocacy-receipt-v1`,
`openhear-advocacy-bundle-v1`) is owned by this repository, and
evolution happens here, in coordination with the author.

The reasoning is the same reasoning that makes the type boundary
necessary. A forked schema is an incompatible schema. Incompatible
schemas produce bundles that cannot be verified by the reference
implementation, and a bundle that cannot be verified by the reference
implementation is a bundle no independent party can stand behind. In
a clinical context, an unverifiable bundle is worse than no bundle —
it creates false confidence in a record that has no anchor outside
the system that produced it. Schema evolution belongs to the
framework because that is the only place it can happen without
breaking the property the framework exists to provide.

## On Iris and Future Tooling

Iris is a companion, not a dependency. It is an AI companion built
within the Burgess Principle that will provide a higher-level
advocacy workflow — tribunal-ready bundles, draft challenge language,
receipt verification UI, shared vault formats — on top of the
primitives this repository defines.

The Sovereign Philosophy requires that the foundational layer —
OpenHear — remain stable, auditable, and independent of any AI
companion. Iris will use OpenHear. OpenHear will not use Iris. This
is permanent architectural policy, not a temporary decision pending
v2.0.0. An integrator who wants to support Iris does so by
integrating correctly against the current advocacy layer; nothing
else is required, and nothing else will be required.
