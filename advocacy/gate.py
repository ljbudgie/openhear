"""
gate.py – PersonGate‑compatible commitment primitives.

Intentionally shaped to mirror Iris's ``@iris-gate/person`` API:

    commit(label, facts, tags=None)     → Commitment
    receive(record_id, receipt)         → Record (tagged SOVEREIGN or NULL)

A :class:`Commitment` is a SHA‑256 fingerprint over a canonical JSON
serialisation of the *facts*.  Only the commitment — never the raw
facts — is intended to leave the user's device.  A returning
:class:`Receipt` (for example, signed by a human assessor, caseworker,
or tribunal clerk) is then verified *against the commitment* to
establish whether a human judicial mind was applied.

The verification path is deliberately minimal: signature verification
is delegated to a caller‑supplied verifier, so OpenHear does not pick
a cryptographic library for downstream projects.  A plain
``hmac.compare_digest``‑based HMAC verifier is included for tests and
for the simplest sovereign‑vault‑on‑device case.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Literal, Mapping

# ── Tag vocabulary ─────────────────────────────────────────────────────────

#: Applied when a returning receipt proves a human personally reviewed
#: the specific facts of this specific case.
SOVEREIGN: Literal["SOVEREIGN"] = "SOVEREIGN"

#: Applied when no individual human review took place — pure
#: automation, a blanket policy, or a refusal to engage.
NULL: Literal["NULL"] = "NULL"

#: Type alias for the tag vocabulary.  Kept open to ``str`` so
#: downstream projects may add refinements (for example, ``NULL_AUTO``
#: vs. ``NULL_POLICY``) without breaking compatibility with OpenHear.
ReviewTag = str


# ── Public dataclasses ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class Commitment:
    """A SHA‑256 commitment over a sovereign record.

    The commitment is the only value that should be shared outside the
    user's device.  The ``facts`` stay on the device in whatever
    sovereign vault the caller has chosen (filesystem, encrypted blob
    store, a future OpenHear vault — this module takes no position).
    """

    record_id: str
    label: str
    digest: str                # hex‑encoded SHA‑256
    tags: tuple[str, ...]
    created_at: str            # ISO‑8601 UTC

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "label": self.label,
            "digest": self.digest,
            "tags": list(self.tags),
            "created_at": self.created_at,
            "algorithm": "sha256",
            "schema": "openhear-advocacy-commitment-v1",
        }


@dataclass(frozen=True)
class Receipt:
    """A signed response to a :class:`Commitment`.

    The semantics are: some external party (an assessor, caseworker,
    tribunal clerk, automated system) has been shown the commitment
    and has replied.  The receipt records *who*, *when*, and a
    signature over the commitment digest.  Whether the signature
    represents genuine human review is exactly what
    :meth:`PersonGate.receive` is asked to decide.
    """

    record_id: str
    digest: str
    signature: str             # opaque to this module; verified by caller
    reviewer: str              # free‑text identifier (name, role, or "automated")
    human_review_claimed: bool
    received_at: str           # ISO‑8601 UTC

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "digest": self.digest,
            "signature": self.signature,
            "reviewer": self.reviewer,
            "human_review_claimed": self.human_review_claimed,
            "received_at": self.received_at,
            "schema": "openhear-advocacy-receipt-v1",
        }


@dataclass
class Record:
    """A tagged record held in the local gate.

    Created when ``commit`` is called.  Gains a ``tag`` of
    :data:`SOVEREIGN` or :data:`NULL` only after a receipt is received
    and verified.
    """

    commitment: Commitment
    receipt: Receipt | None = None
    tag: ReviewTag | None = None
    # Facts stay on‑device.  Held by reference so callers that hold
    # the original object can update their own vault; the gate does
    # not mutate it.
    facts: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "commitment": self.commitment.to_dict(),
            "receipt": self.receipt.to_dict() if self.receipt else None,
            "tag": self.tag,
        }


# ── Verifier protocol ──────────────────────────────────────────────────────

#: Signature verifier.  Returns ``True`` iff the signature is valid for
#: ``digest`` under whatever keying material the verifier holds.
#: Deliberately left to callers so no crypto library is forced on
#: downstream projects.
Verifier = Callable[[str, str], bool]


def hmac_verifier(key: bytes) -> Verifier:
    """Return a :data:`Verifier` that accepts HMAC‑SHA‑256 signatures.

    Useful for local testing and for the simplest on‑device sovereign
    vault case.  Real advocacy flows will typically use an asymmetric
    verifier plugged in by the companion (e.g. Iris).
    """

    if not isinstance(key, (bytes, bytearray)):
        raise TypeError("hmac_verifier key must be bytes")
    key_bytes = bytes(key)

    def _verify(digest: str, signature: str) -> bool:
        expected = hmac.new(
            key_bytes, digest.encode("ascii"), hashlib.sha256
        ).hexdigest()
        # ``compare_digest`` defends against timing attacks even though
        # the signatures we compare here are already digests.
        return hmac.compare_digest(expected, signature)

    return _verify


# ── Canonical serialisation ────────────────────────────────────────────────

def _canonical_json(facts: Mapping[str, Any]) -> bytes:
    """Stable, sorted JSON bytes suitable for hashing.

    Using ``sort_keys=True`` and ``separators=(",", ":")`` means the
    same logical record always produces the same digest regardless of
    Python dict ordering.
    """

    return json.dumps(
        facts,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _utc_now_iso() -> str:
    # ``timespec='seconds'`` keeps the string compact and test‑friendly.
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── Module‑level convenience API ───────────────────────────────────────────

def commit(label: str, facts: Mapping[str, Any],
           tags: Iterable[str] | None = None) -> Commitment:
    """Produce a :class:`Commitment` over ``facts``.

    This is the primitive Iris's ``personGate.commit`` documents.
    OpenHear's adapters (audiogram, fitting, MPO) are thin wrappers
    around this function that also enforce the sovereign‑handling
    invariants specific to audio data.
    """

    if not isinstance(label, str) or not label:
        raise ValueError("label must be a non-empty string")
    if not isinstance(facts, Mapping):
        raise TypeError("facts must be a Mapping")

    payload = _canonical_json(facts)
    digest = _sha256_hex(payload)
    record_id = str(uuid.uuid4())
    tag_tuple: tuple[str, ...] = tuple(tags) if tags else ()
    return Commitment(
        record_id=record_id,
        label=label,
        digest=digest,
        tags=tag_tuple,
        created_at=_utc_now_iso(),
    )


def verify(commitment: Commitment, receipt: Receipt,
           verifier: Verifier) -> bool:
    """Return ``True`` iff ``receipt`` is a valid response to ``commitment``.

    A receipt is valid when (a) it references the same ``record_id``
    and ``digest`` and (b) the caller‑supplied :data:`Verifier`
    accepts the signature.  Whether the underlying review was *truly*
    human is a claim carried by the receipt (``human_review_claimed``)
    and ultimately the Burgess Principle question the user must
    answer; this function only establishes cryptographic integrity.
    """

    if receipt.record_id != commitment.record_id:
        return False
    if receipt.digest != commitment.digest:
        return False
    return bool(verifier(commitment.digest, receipt.signature))


# ── Stateful gate ──────────────────────────────────────────────────────────

class PersonGate:
    """In‑memory sovereign‑record store.

    The gate mirrors the surface area of Iris's ``@iris-gate/person``
    module that OpenHear records need to reach:

    * :meth:`commit` — create a record, return its commitment.
    * :meth:`receive` — attach a verified receipt and apply a
      :data:`SOVEREIGN` or :data:`NULL` tag.
    * :meth:`list_records` — iterate local records.
    * :meth:`challenges` — yield records tagged :data:`NULL`, the
      starting point for any Burgess‑Principle challenge.

    The gate deliberately does *not* persist to disk.  Persistence is
    the companion's job (Iris's vault, or whatever the user chooses),
    which keeps OpenHear free of vault‑format commitments for v1.
    """

    def __init__(self, verifier: Verifier | None = None) -> None:
        # Verifier is optional so a gate can be constructed first and
        # a verifier supplied later (e.g. once the companion loads a
        # key).  receive() will raise if no verifier has been set.
        self._verifier = verifier
        self._records: dict[str, Record] = {}

    # ---- mutation ---------------------------------------------------------

    def commit(self, label: str, facts: Mapping[str, Any],
               tags: Iterable[str] | None = None) -> Commitment:
        """Create a local record and return its commitment."""

        c = commit(label, facts, tags=tags)
        self._records[c.record_id] = Record(commitment=c, facts=facts)
        return c

    def receive(self, record_id: str, receipt: Receipt) -> Record:
        """Attach a verified receipt to a record and tag it.

        Raises :class:`KeyError` if the record is unknown, and
        :class:`ValueError` if no verifier has been configured.  The
        returned record carries either :data:`SOVEREIGN` or
        :data:`NULL` in ``record.tag`` depending on both the
        cryptographic integrity of the receipt *and* the
        ``human_review_claimed`` flag carried by the receipt.
        """

        if self._verifier is None:
            raise ValueError(
                "PersonGate has no verifier configured; cannot tag receipts"
            )
        if record_id not in self._records:
            raise KeyError(record_id)

        record = self._records[record_id]
        ok = verify(record.commitment, receipt, self._verifier)
        record.receipt = receipt
        if not ok:
            # A receipt that doesn't cryptographically bind to the
            # commitment cannot satisfy Burgess: treat as NULL.
            record.tag = NULL
            return record

        record.tag = SOVEREIGN if receipt.human_review_claimed else NULL
        return record

    # ---- queries ----------------------------------------------------------

    def list_records(self) -> list[Record]:
        return list(self._records.values())

    def get(self, record_id: str) -> Record:
        return self._records[record_id]

    def challenges(self) -> list[Record]:
        """Return records currently tagged :data:`NULL`.

        These are the records that failed the Burgess Principle test
        and are the starting list a companion like Iris would use to
        draft challenge language.
        """

        return [r for r in self._records.values() if r.tag == NULL]
