# OpenHear Documentation

## Start Here

OpenHear is a sovereign audiology advocacy framework built on the
Burgess Principle. This index routes you to the right document based
on who you are.

## I am an industry leader or executive

→ [`docs/BURGESS_PRINCIPLE.md`](BURGESS_PRINCIPLE.md)

The Burgess Principle itself: the problem it exists to solve, the five
non-negotiable commitments that define an OpenHear integration, and
what the principle asks of a manufacturer or AI system builder
preparing to adopt it.

## I am an engineer or AI coding agent building an integration

→ [`docs/INTEGRATORS.md`](INTEGRATORS.md) *(start here)*
→ [`docs/ADVOCACY_INTEGRATION.md`](ADVOCACY_INTEGRATION.md) *(full technical contract)*
→ [`examples/reference_integration.py`](../examples/reference_integration.py) *(runnable reference)*

The step-by-step integration guide, the full v1.0.0 contract for the
advocacy layer, and a working reference you can run end-to-end to
confirm your integration produces verifiable bundles.

## I am an engineer who wants to understand the architectural reasoning

→ [`docs/SOVEREIGN_PHILOSOPHY.md`](SOVEREIGN_PHILOSOPHY.md)

The design rationale behind every decision in the advocacy layer:
why offline-first, why SHA-256 canonical JSON, why the SOVEREIGN/NULL
binary, why raw audio is rejected at the type level, and why the
coupling between OpenHear and its companions runs in only one
direction.

## I am a regulator or auditor

→ [`docs/BURGESS_PRINCIPLE.md`](BURGESS_PRINCIPLE.md) *(the five commitments)*
→ [`docs/SOVEREIGN_PHILOSOPHY.md`](SOVEREIGN_PHILOSOPHY.md) *(design rationale)*
→ [`NOTICE`](../NOTICE) *(legal attribution and integration invariants)*

The commitments any conforming integration must preserve, the
architectural reasoning that makes those commitments enforceable, and
the legal notice covering attribution and the invariants integrators
are bound by.

## I want to understand the full technical contract

→ [`docs/ADVOCACY_INTEGRATION.md`](ADVOCACY_INTEGRATION.md)

The complete v1.0.0 specification of the advocacy layer: public API,
record shapes, canonical serialisation, verification semantics, and
the boundaries the layer enforces.
