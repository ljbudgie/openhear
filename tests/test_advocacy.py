"""Tests for the advocacy extension point.

These cover the v1.0.0 contract:

* A sovereign OpenHear record (an audiogram in the
  ``openhear-audiogram-v1`` shape) can be committed to a PersonGate
  and a receipt round‑tripped to produce a ``SOVEREIGN`` tag.
* A valid receipt whose ``human_review_claimed`` flag is ``False``
  produces a ``NULL`` tag (the Burgess challenge list).
* A tampered receipt (wrong signature or wrong digest) also produces
  ``NULL``.
* Raw audio payloads are refused by the adapters.
* The export bundle carries both disclaimers and never contains
  sovereign facts.
* Two commits over the same audiogram produce the same digest
  regardless of dict ordering (canonical serialisation).
"""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest

from advocacy import (
    ADVISORY_DISCLAIMER,
    MEDICAL_DISCLAIMER,
    NULL,
    PersonGate,
    RawAudioRejectedError,
    Receipt,
    SOVEREIGN,
    audiogram_commitment,
    commit,
    export_record,
    fitting_commitment,
    hmac_verifier,
    mpo_commitment,
    verify,
)


# ---- helpers ----------------------------------------------------------------

_KEY = b"test-key-not-a-real-secret"


def _sign(digest: str) -> str:
    return hmac.new(_KEY, digest.encode("ascii"), hashlib.sha256).hexdigest()


def _make_receipt(commitment, *, human: bool, sig: str | None = None,
                  digest_override: str | None = None) -> Receipt:
    digest = digest_override if digest_override is not None else commitment.digest
    return Receipt(
        record_id=commitment.record_id,
        digest=digest,
        signature=sig if sig is not None else _sign(digest),
        reviewer="Test Assessor" if human else "automated",
        human_review_claimed=human,
        received_at="2026-01-01T00:00:00+00:00",
    )


# ---- round‑trip -------------------------------------------------------------

def test_audiogram_roundtrip_to_sovereign(sample_audiogram_dict):
    gate = PersonGate(verifier=hmac_verifier(_KEY))
    commitment = audiogram_commitment(sample_audiogram_dict, tags=("gp-triage",))

    # Domain tags are preserved and extra tags appended.
    assert commitment.tags[:2] == ("audiogram", "openhear-audiogram-v1")
    assert "gp-triage" in commitment.tags

    # Commit in the gate so we can receive against it.
    record_id = gate.commit(
        "audiogram", sample_audiogram_dict,
        tags=commitment.tags,
    ).record_id

    receipt = _make_receipt(gate.get(record_id).commitment, human=True)
    record = gate.receive(record_id, receipt)
    assert record.tag == SOVEREIGN


def test_valid_receipt_without_human_review_is_null(sample_audiogram_dict):
    gate = PersonGate(verifier=hmac_verifier(_KEY))
    c = gate.commit("audiogram", sample_audiogram_dict)
    record = gate.receive(c.record_id, _make_receipt(c, human=False))
    assert record.tag == NULL
    assert gate.challenges() == [record]


def test_tampered_signature_is_null(sample_audiogram_dict):
    gate = PersonGate(verifier=hmac_verifier(_KEY))
    c = gate.commit("audiogram", sample_audiogram_dict)
    bad = _make_receipt(c, human=True, sig="00" * 32)
    record = gate.receive(c.record_id, bad)
    assert record.tag == NULL


def test_tampered_digest_is_null(sample_audiogram_dict):
    gate = PersonGate(verifier=hmac_verifier(_KEY))
    c = gate.commit("audiogram", sample_audiogram_dict)
    forged_digest = "f" * 64
    bad = _make_receipt(c, human=True, digest_override=forged_digest,
                        sig=_sign(forged_digest))
    record = gate.receive(c.record_id, bad)
    assert record.tag == NULL


# ---- sovereign handling -----------------------------------------------------

def test_adapter_rejects_raw_pcm_bytes():
    with pytest.raises(RawAudioRejectedError):
        audiogram_commitment({"subject": "x", "sample": b"\x00\x01\x02"})


def test_adapter_rejects_raw_pcm_in_nested_list():
    with pytest.raises(RawAudioRejectedError):
        fitting_commitment({"programs": [{"clip": bytearray(b"\x00\x01"),
                                           "name": "quiet"}]})


def test_adapter_rejects_numpy_array():
    np = pytest.importorskip("numpy")
    with pytest.raises(RawAudioRejectedError):
        mpo_commitment({"headroom_db": 12, "samples": np.zeros(4)})


def test_adapter_rejects_non_mapping():
    with pytest.raises(TypeError):
        audiogram_commitment([("subject", "x")])  # type: ignore[arg-type]


# ---- determinism ------------------------------------------------------------

def test_canonical_digest_is_order_independent(sample_audiogram_dict):
    # Build a reordered copy — same content, different dict order.
    reordered = dict(reversed(list(sample_audiogram_dict.items())))
    assert list(sample_audiogram_dict) != list(reordered)
    a = audiogram_commitment(sample_audiogram_dict)
    b = audiogram_commitment(reordered)
    assert a.digest == b.digest


# ---- export bundle ----------------------------------------------------------

def test_export_bundle_has_disclaimers_and_no_facts(sample_audiogram_dict):
    gate = PersonGate(verifier=hmac_verifier(_KEY))
    c = gate.commit("audiogram", sample_audiogram_dict,
                    tags=("audiogram", "openhear-audiogram-v1"))
    receipt = _make_receipt(c, human=True)
    gate.receive(c.record_id, receipt)

    bundle = export_record(gate, c.record_id)

    assert bundle["schema"] == "openhear-advocacy-bundle-v1"
    assert bundle["tag"] == SOVEREIGN
    assert bundle["disclaimers"]["medical"] == MEDICAL_DISCLAIMER
    assert bundle["disclaimers"]["advisory"] == ADVISORY_DISCLAIMER
    assert bundle["verification"]["algorithm"] == "sha256"

    # The subject name and thresholds must NOT appear in the bundle.
    as_json = json.dumps(bundle)
    assert sample_audiogram_dict["subject"] not in as_json
    for ear in ("right_ear", "left_ear"):
        for threshold in sample_audiogram_dict[ear]["thresholds"]:
            assert f'"db_hl": {threshold["db_hl"]}' not in as_json


def test_export_bundle_digest_matches_recomputed_digest(sample_audiogram_dict):
    gate = PersonGate(verifier=hmac_verifier(_KEY))
    c = gate.commit("audiogram", sample_audiogram_dict)
    bundle = export_record(gate, c.record_id)

    # Independently recompute the canonical digest using the documented
    # instructions.  This is the path a tribunal would follow.
    payload = json.dumps(
        sample_audiogram_dict,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    recomputed = hashlib.sha256(payload).hexdigest()
    assert bundle["commitment"]["digest"] == recomputed


# ---- gate guardrails --------------------------------------------------------

def test_receive_without_verifier_raises(sample_audiogram_dict):
    gate = PersonGate()  # no verifier
    c = gate.commit("audiogram", sample_audiogram_dict)
    with pytest.raises(ValueError):
        gate.receive(c.record_id, _make_receipt(c, human=True))


def test_receive_unknown_record_raises():
    gate = PersonGate(verifier=hmac_verifier(_KEY))
    fake = Receipt(
        record_id="nope", digest="0" * 64, signature="x",
        reviewer="x", human_review_claimed=True,
        received_at="2026-01-01T00:00:00+00:00",
    )
    with pytest.raises(KeyError):
        gate.receive("nope", fake)


def test_module_level_commit_and_verify_roundtrip():
    c = commit("note", {"k": "v"}, tags=("misc",))
    good = Receipt(
        record_id=c.record_id, digest=c.digest, signature=_sign(c.digest),
        reviewer="x", human_review_claimed=True,
        received_at="2026-01-01T00:00:00+00:00",
    )
    assert verify(c, good, hmac_verifier(_KEY)) is True

    wrong = Receipt(
        record_id=c.record_id, digest=c.digest, signature="deadbeef",
        reviewer="x", human_review_claimed=True,
        received_at="2026-01-01T00:00:00+00:00",
    )
    assert verify(c, wrong, hmac_verifier(_KEY)) is False
