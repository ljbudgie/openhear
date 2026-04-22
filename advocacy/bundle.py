"""
bundle.py – offline export bundle for sovereign advocacy records.

An export bundle is a plain Python dict (JSON‑serialisable) that a
caller may hand to a companion tool, save to disk, or show the user.
Bundles never contain sovereign facts — only the commitment, the
receipt (if any), the review tag, and the two hard‑coded advisory
disclaimers.

The disclaimers are written here, not by callers, so they cannot be
stripped by an over‑eager downstream formatter.
"""

from __future__ import annotations

from typing import Any

from advocacy.gate import PersonGate, Record

#: Mirrors the existing README experimental banner.  Hard‑coded so no
#: export can omit it.
MEDICAL_DISCLAIMER: str = (
    "OpenHear is experimental and is not a medical device. "
    "Nothing in this bundle has been reviewed or approved by any "
    "medical regulator. Do not treat any value here as a substitute "
    "for clinical audiological care."
)

#: Mirrors Iris's advisory banner.  Hard‑coded for the same reason.
ADVISORY_DISCLAIMER: str = (
    "This bundle is advisory only and is not legal advice. It is "
    "provided to help the sovereign individual demand human review of "
    "an automated or institutional decision (the Burgess Principle). "
    "It does not itself make any decision on the user's behalf."
)


def export_record(gate: PersonGate, record_id: str) -> dict[str, Any]:
    """Produce an offline‑only export bundle for ``record_id``.

    The returned dict is safe to share outside the device *only to
    the extent that the user chooses to share it*.  It carries:

    * the commitment (SHA‑256 digest, never the facts);
    * the receipt, if one has been received;
    * the review tag (``SOVEREIGN``, ``NULL``, or ``None`` if no
      receipt has been processed yet);
    * both advisory disclaimers;
    * verification instructions in plain English, so a tribunal can
      independently recompute the digest and confirm the binding.
    """

    record: Record = gate.get(record_id)
    bundle: dict[str, Any] = {
        "schema": "openhear-advocacy-bundle-v1",
        "commitment": record.commitment.to_dict(),
        "receipt": record.receipt.to_dict() if record.receipt else None,
        "tag": record.tag,
        "disclaimers": {
            "medical": MEDICAL_DISCLAIMER,
            "advisory": ADVISORY_DISCLAIMER,
        },
        "verification": {
            "algorithm": "sha256",
            "instructions": (
                "To verify this commitment, canonicalise the sovereign "
                "record as UTF-8 JSON with sorted keys and no whitespace "
                "(json.dumps(..., sort_keys=True, separators=(',', ':'))) "
                "and compute its SHA-256 hex digest. It must exactly "
                "equal the 'digest' field of the 'commitment' object."
            ),
        },
    }
    return bundle
