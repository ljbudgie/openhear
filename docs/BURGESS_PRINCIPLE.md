# The Burgess Principle

## What This Is

The Burgess Principle is a framework authored by Lewis James Burgess for
sovereign, ethical handling of clinical audiology data. It defines how
hearing data — audiograms, fittings, MPO calculations — should be
committed, verified, and transmitted without surrendering control to any
vendor, platform, or intermediary. It is the ethical, clinical, and
architectural root from which OpenHear grows; the advocacy layer in this
repository is the reference implementation of that principle, and any
future tooling — including the Iris companion — is built on top of it
rather than around it.

## The Problem It Exists to Solve

Fitting data lives inside proprietary manufacturer silos. An audiogram is
a measurement of a person's body, yet that person rarely holds an
independent, verifiable copy of what was measured, what was prescribed,
or what was finally programmed into their device. Audiologists cannot
independently audit records once they leave the clinic's fitting
software. Regulators cannot inspect a fitting decision without the
cooperation of the vendor whose decision is under inspection. The party
with the most at stake — the patient — is the party with the least
access to the ground truth about their own care.

When AI enters that system without a sovereignty layer, the gap widens.
AI-assisted fittings, automated adjustments, and remote programming all
produce clinical decisions, and those decisions are currently
unverifiable, untraceable, and unaccountable at the data level. A
manufacturer's cloud may log that an adjustment occurred, but the
patient cannot prove what was applied to them, the clinician cannot
independently reconstruct the reasoning, and the regulator cannot
distinguish a human clinical judgement from an automated policy
applied at scale.

The result is a structural gap in clinical accountability. A patient who
receives a suboptimal fitting has no cryptographic record of what was
applied. A clinician disputing a manufacturer's AI recommendation has no
independent ground truth to point to. A regulator investigating a
pattern of harm has no tamper-evident audit trail that exists outside
the system under investigation. The Burgess Principle exists to close
that gap — not by replacing the manufacturers, the clinicians, or the
regulators, but by giving each of them an independent, verifiable,
offline record of what was committed to and by whom.

## The Five Commitments

These are the invariants of the Burgess Principle. They are derived from
what is already enforced in `advocacy/gate.py`, `advocacy/adapters.py`,
and the `NOTICE` file. Any system that violates one is not operating
within the principle, regardless of what it claims.

1. **Sovereign facts belong to the person they describe.**
   The audiogram, the fitting profile, and the MPO calculation are facts
   about a human body and must never be transmitted, bundled, or shared
   without explicit, informed consent from that person. In clinical
   terms, the patient is the data controller of their own physiology;
   any architecture that treats the patient as a downstream consumer of
   their own measurements has already failed the duty of care that the
   measurement was performed under.

2. **Every clinical commitment is cryptographically verifiable by any
   party holding the bundle, independently, offline, with no vendor
   involvement.**
   A SHA-256 commitment over a canonical serialisation of the facts is
   the only value intended to leave the device, and any downstream
   verifier can reconstruct that digest from the original facts without
   contacting the originating system. In clinical terms, a record whose
   integrity depends on a vendor's continued cooperation is not a
   clinical record — it is a vendor service, and clinical accountability
   cannot rest on a service that can be revoked, paywalled, or
   discontinued.

3. **Human verification produces SOVEREIGN status. Automation,
   tampering, or unresolvable verification produces NULL. There is no
   third state.**
   `SOVEREIGN` means a real human personally reviewed the specific
   facts of this specific case and signed a receipt against the
   commitment; `NULL` covers every other outcome — pure automation,
   blanket policy, an invalid signature, or a refusal to engage. In
   clinical terms, ambiguous trust states produce ambiguous clinical
   outcomes; a "partially verified" fitting decision invites the
   misreading that a human stood behind it when no human did.

4. **Raw audio is not a clinical fact.**
   The boundary between signal and interpretation is enforced at the
   type level: any attempt to commit `bytes`, `bytearray`,
   `memoryview`, or a NumPy `ndarray` anywhere in the facts payload
   raises `RawAudioRejectedError` before a commitment is produced. In
   clinical terms, environmental audio is sovereign data of the highest
   sensitivity and must never become part of a record intended for
   transmission; a commitment over raw audio is a meaningless
   commitment that nevertheless looks valid, and that combination is
   precisely the failure mode the principle exists to prevent.

5. **Schema ownership is singular.**
   The `openhear-advocacy-v1` schema family
   (`openhear-advocacy-commitment-v1`, `openhear-advocacy-receipt-v1`,
   `openhear-advocacy-bundle-v1`) is owned by this repository.
   Integrators must not fork, independently version, or extend it.
   In clinical terms, a forked schema is an incompatible schema, and an
   incompatible schema produces bundles that cannot be verified by the
   reference implementation; an unverifiable bundle is worse than no
   bundle, because it creates false confidence in a record that no
   independent party can stand behind.

## What This Asks of Integrators

You — a hearing device manufacturer, an audiology software vendor, or an
AI system builder — must preserve the five commitments above. They are
not configuration options, opt-in features, or recommended defaults.
They are the contract. An integration that bypasses any of them is not
an OpenHear integration, regardless of the surface it presents to its
users; it is a separate product that happens to share some of our type
names.

In return, what you gain is structural rather than cosmetic.
Tamper-evident clinical records that survive your own corporate
lifecycle. A verifiable audit trail your customers — patients,
clinicians, regulators — can hold independently of you, which converts
disputes from your-word-against-theirs into something that can be
resolved by inspection. A foundation that will be compatible with Iris
and future Burgess Principle tooling without modification, because the
contract you integrated against is the same contract those tools will
build on.

What comes next is Iris — an AI companion built within the Burgess
Principle — which will provide a higher-level advocacy workflow
post-v1.0.0. Iris will import OpenHear; OpenHear will not import Iris.
That direction is permanent. If you have integrated correctly against
the current advocacy layer, you will be compatible with Iris
automatically, and you do not need to wait for it before shipping.

## About the Author

Lewis James Burgess is the author of the Burgess Principle and the
creator of OpenHear. Contact: [CONTACT — author to complete]

## Implementation

For the technical and operational detail, read these documents in order:

1. [`docs/ADVOCACY_INTEGRATION.md`](ADVOCACY_INTEGRATION.md) — the
   technical contract for the advocacy layer.
2. [`docs/INTEGRATORS.md`](INTEGRATORS.md) — the step-by-step
   integration guide.
3. [`examples/reference_integration.py`](../examples/reference_integration.py)
   — the runnable reference integration.

Start with `INTEGRATORS.md` if you are an engineer or AI coding agent
building an integration.
