"""
advocacy package – Burgess Principle extension point for OpenHear.

OpenHear is a human sensory sovereignty platform.  Users of the
platform — deaf and hard‑of‑hearing people, in particular — routinely
face institutional decisions (workplace adjustments, GP triage,
education access, benefits assessments, travel boarding) that touch
their sovereign data: audiograms, fittings, MPO safety calculations.

The Burgess Principle, already adopted throughout the OpenHear README
("does this feature treat the user as a sovereign individual … or as a
unit inside someone else's system"), asks one binary question of every
such institutional decision:

    Was a human judicial mind applied to the specific facts of this
    specific case?

This package is the minimal, offline, dependency‑free extension point
that lets a companion advocacy tool (for example Iris, from the
Burgess Principle project) answer that question against OpenHear
records without OpenHear ever importing, depending on, or phoning home
to the companion.

Design guarantees (enforced in code, not just docs):

* **One‑way coupling.**  OpenHear exposes a stable record schema and a
  commitment helper.  No network calls.  No third‑party imports.
* **Sovereign handling.**  Only cryptographic commitments
  (SHA‑256 fingerprints) of sovereign records are intended to leave
  the device.  Raw audiogram thresholds, fitting parameters, and —
  critically — raw environmental audio samples from the wristband
  must never be serialised into an advocacy bundle.  The adapter
  rejects the latter at the type boundary.
* **Dual advisory disclaimers.**  Every export bundle carries both
  the OpenHear "experimental, not a medical device" disclaimer and an
  advocacy "advisory‑only, not legal advice" disclaimer.  They are
  written by the adapter, not by callers.
* **No telemetry.**  This module performs no I/O beyond what the
  caller explicitly passes to :func:`export_record`.

This module is deliberately small.  The full advocacy workflow
(tribunal‑ready bundles combining case facts, draft challenge
language, receipt verification UI) lives in Iris, not here.
"""

from __future__ import annotations

from advocacy.gate import (
    PersonGate,
    Commitment,
    Receipt,
    Record,
    ReviewTag,
    SOVEREIGN,
    NULL,
    commit,
    verify,
    hmac_verifier,
)
from advocacy.adapters import (
    RawAudioRejectedError,
    audiogram_commitment,
    fitting_commitment,
    mpo_commitment,
)
from advocacy.bundle import (
    MEDICAL_DISCLAIMER,
    ADVISORY_DISCLAIMER,
    export_record,
)

__all__ = [
    # Gate primitives
    "PersonGate",
    "Commitment",
    "Receipt",
    "Record",
    "ReviewTag",
    "SOVEREIGN",
    "NULL",
    "commit",
    "verify",
    "hmac_verifier",
    # Adapters
    "RawAudioRejectedError",
    "audiogram_commitment",
    "fitting_commitment",
    "mpo_commitment",
    # Export bundle
    "MEDICAL_DISCLAIMER",
    "ADVISORY_DISCLAIMER",
    "export_record",
]
