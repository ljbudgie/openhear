"""reference_integration.py — end-to-end demonstration of the OpenHear
Sovereign Advocacy Layer for hearing-industry integrators.

This file is the executable companion to ``docs/INTEGRATORS.md`` and
implements the integration contract described there literally. It is
deliberately self-contained:

* Imports only from ``advocacy`` (the OpenHear Sovereign Advocacy
  Layer) and the Python standard library.
* Defines a fictional ``FittingSystem`` — the kind of class a
  manufacturer (Phonak, Widex, Starkey, Signia, Whoopee) would
  already have — and demonstrates how to plug commitment in alongside
  it without changing the existing data flow.
* Walks the three flows every integrator must understand:
    1. The happy path — commit an audiogram, receive a human-signed
       receipt, export a SOVEREIGN-tagged bundle, print it as JSON,
       and print the plain-English verification instructions a
       tribunal would follow.
    2. The tamper detection path — modify a single dB threshold
       after commitment and show that the bundle's digest no longer
       matches the modified record, that a forged receipt over the
       tampered facts is tagged NULL by the gate, and what that
       means clinically.
    3. The hard boundary — attempt to pass raw PCM bytes into the
       audiogram adapter and show the ``RawAudioRejectedError`` that
       protects the commitment layer from sovereign audio leakage.

Background:

The Burgess Principle — *"Was a human judicial mind applied to the
specific facts of this specific case?"* — is the ethical philosophy
that governs OpenHear. The advocacy layer is its enforcement surface
in code. SOVEREIGN means the answer was yes. NULL means the answer
was no. There is no third tag and no in-between. See
``docs/INTEGRATORS.md`` for the full contract and
``docs/ADVOCACY_INTEGRATION.md`` for the design rationale.

Run it with:

    python examples/reference_integration.py

No flags. No configuration. No network. No persistence.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from advocacy import (
    NULL,
    SOVEREIGN,
    PersonGate,
    RawAudioRejectedError,
    Receipt,
    audiogram_commitment,
    export_record,
    hmac_verifier,
)

# ── Fictional fitting system ───────────────────────────────────────────────
#
# The kind of class a hearing-aid manufacturer would already have in
# their fitting application. It owns the patient identity, the
# audiometric measurements, and the fitting parameters. OpenHear sits
# alongside it and produces a commitment over the clinical facts; it
# does not replace the system.

@dataclass
class FittingSystem:
    """A minimal, fictional manufacturer-side fitting system.

    Realistic dB HL values across the standard audiometric
    frequencies. Bilateral, sloping high-frequency loss — the most
    common adult presentation in the clinic.
    """

    subject: str = "patient-0001"
    source: str = "ACME Fitting Suite v4.2"
    measurement_date: str = "2026-04-15"
    notes: str = (
        "Bilateral sensorineural hearing loss, sloping high-frequency "
        "configuration. Synthetic example for the OpenHear reference "
        "integration; not a real patient."
    )

    # Standard audiometric frequencies (Hz) → threshold (dB HL).
    right_thresholds: dict[int, int] = field(default_factory=lambda: {
        250: 20, 500: 25, 1000: 35, 2000: 50, 4000: 65, 8000: 75,
    })
    left_thresholds: dict[int, int] = field(default_factory=lambda: {
        250: 25, 500: 30, 1000: 40, 2000: 55, 4000: 70, 8000: 80,
    })

    def export_audiogram_facts(self) -> dict[str, Any]:
        """Return the audiogram in the ``openhear-audiogram-v1`` shape.

        This is the exact dict the OpenHear adapter expects. The
        manufacturer system reduces its internal representation to
        clinical facts here — never raw audio, never PCM, never
        device-internal blobs.
        """

        def _ear(symbol: str, thresholds: Mapping[int, int]) -> dict[str, Any]:
            return {
                "symbol": symbol,
                "thresholds": [
                    {"freq_hz": freq, "db_hl": db}
                    for freq, db in sorted(thresholds.items())
                ],
            }

        return {
            "subject": self.subject,
            "source": self.source,
            "date": self.measurement_date,
            "format_version": "openhear-audiogram-v1",
            "notes": self.notes,
            "right_ear": _ear("O", self.right_thresholds),
            "left_ear": _ear("X", self.left_thresholds),
            "classification": {
                "type": "sensorineural",
                "pattern": "moderate_to_severe_sloping",
            },
        }


# ── Helpers for the reviewer side ──────────────────────────────────────────
#
# In a real deployment the verifier would be asymmetric and the
# signing key would belong to the reviewing audiologist's identity
# system. For this offline demonstration we use the HMAC verifier
# that ships with the layer for tests and on-device sovereign vaults.

_REVIEWER_KEY = b"reference-integration-demo-key-not-a-real-secret"


def _sign(digest: str) -> str:
    return hmac.new(_REVIEWER_KEY, digest.encode("ascii"), hashlib.sha256).hexdigest()


def _build_receipt(commitment, *, reviewer: str, human_review: bool,
                   digest_override: str | None = None,
                   signature_override: str | None = None) -> Receipt:
    """Build a Receipt the way a reviewer's identity system would.

    ``digest_override`` and ``signature_override`` exist only so the
    tamper-detection demonstration can construct a forged receipt.
    """

    digest = digest_override if digest_override is not None else commitment.digest
    signature = signature_override if signature_override is not None else _sign(digest)
    return Receipt(
        record_id=commitment.record_id,
        digest=digest,
        signature=signature,
        reviewer=reviewer,
        human_review_claimed=human_review,
        received_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def _section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# ── 1. Happy path — SOVEREIGN bundle ───────────────────────────────────────

def demo_happy_path() -> dict[str, Any]:
    _section("1. HAPPY PATH — commit, receive, export a SOVEREIGN bundle")

    # Step 1: build facts from the manufacturer system.
    fitting = FittingSystem()
    facts = fitting.export_audiogram_facts()

    # Step 2: bind the facts into a stateful gate so a receipt can be
    # processed against the commitment.
    gate = PersonGate(verifier=hmac_verifier(_REVIEWER_KEY))
    commitment = gate.commit(
        "audiogram", facts,
        tags=("audiogram", "openhear-audiogram-v1", "pre-fitting"),
    )

    # (The audiogram_commitment adapter is also available; it computes
    # the same digest and is the right entry point when you do not
    # need a stateful gate. Shown here for completeness:)
    standalone = audiogram_commitment(facts, tags=("pre-fitting",))
    assert standalone.digest == commitment.digest, "adapters must agree"

    # Step 3: a real human reviewer (the audiologist) inspects the
    # specific facts of this specific case and signs a receipt that
    # cryptographically binds to the commitment digest.
    receipt = _build_receipt(
        commitment,
        reviewer="Dr A. Audiologist (HCPC #00000)",
        human_review=True,
    )

    # Step 4: the gate verifies the receipt and tags the record.
    record = gate.receive(commitment.record_id, receipt)
    assert record.tag == SOVEREIGN, "valid human receipt must produce SOVEREIGN"

    # Step 5: export the offline bundle. This is the only artefact
    # that should ever leave the device.
    bundle = export_record(gate, commitment.record_id)

    print("Bundle (JSON-formatted, safe to share):")
    print(json.dumps(bundle, indent=2))

    print()
    print("Plain-English verification instructions from the bundle:")
    print(f"  algorithm:    {bundle['verification']['algorithm']}")
    print(f"  instructions: {bundle['verification']['instructions']}")
    print()
    print(f"Tag: {bundle['tag']}  →  a human judicial mind was applied to "
          "the specific facts of this specific case.")

    return {"facts": facts, "commitment": commitment, "gate": gate,
            "bundle": bundle}


# ── 2. Tamper detection path — NULL bundle ─────────────────────────────────

def demo_tamper_detection(prior: dict[str, Any]) -> None:
    _section("2. TAMPER DETECTION — modify one dB threshold, observe NULL")

    original_facts: dict[str, Any] = prior["facts"]
    original_bundle: dict[str, Any] = prior["bundle"]
    original_digest: str = original_bundle["commitment"]["digest"]

    # Take the committed facts and modify a single value. We deepen
    # the structure just enough to mutate one dB threshold without
    # mutating the original (the gate holds it by reference).
    tampered_facts = json.loads(json.dumps(original_facts))
    target = next(
        t for t in tampered_facts["right_ear"]["thresholds"]
        if t["freq_hz"] == 2000
    )
    print(f"Original right ear @ {target['freq_hz']} Hz: {target['db_hl']} dB HL")
    target["db_hl"] = target["db_hl"] - 25                   # falsify a 25 dB improvement
    print(f"Tampered right ear @ {target['freq_hz']} Hz: {target['db_hl']} dB HL")

    # Independent verifier path: recompute the digest from the
    # tampered facts using the bundle's plain-English instructions
    # and show it no longer matches.
    payload = json.dumps(
        tampered_facts, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    recomputed = hashlib.sha256(payload).hexdigest()

    print()
    print(f"Bundle digest:           {original_digest}")
    print(f"Recomputed (tampered):   {recomputed}")
    print(f"Match: {recomputed == original_digest}")

    # Now show what the gate does when a receipt is presented over
    # the tampered facts. This is the same path an attacker would
    # take to try to pass off a falsified audiogram as reviewed.
    gate: PersonGate = prior["gate"]
    commitment = prior["commitment"]
    forged_receipt = _build_receipt(
        commitment,
        reviewer="Dr A. Audiologist (HCPC #00000)",
        human_review=True,
        digest_override=recomputed,
        signature_override=_sign(recomputed),
    )
    record = gate.receive(commitment.record_id, forged_receipt)
    assert record.tag == NULL, "tampered receipt must produce NULL"
    print(f"Gate tag for the forged receipt: {record.tag}")

    print()
    print("Why this matters clinically:")
    print(
        "  A 25 dB shift at 2 kHz would understate a moderate "
        "high-frequency loss as a near-normal threshold. A fitting "
        "produced from the tampered audiogram would under-amplify "
        "speech consonants and could pass an employer-side check that "
        "the original record would correctly fail. The Sovereign "
        "Advocacy Layer makes that substitution detectable: any third "
        "party with the original facts and the bundle can reproduce "
        "the SHA-256 in ten lines of stdlib Python and see that the "
        "presented record does not match the committed one."
    )


# ── 3. Hard boundary — RawAudioRejectedError ───────────────────────────────

def demo_raw_audio_boundary() -> None:
    _section("3. HARD BOUNDARY — RawAudioRejectedError on raw audio")

    # A manufacturer system might be tempted to attach a short PCM
    # snippet to the audiogram facts ("for diagnostic context"). The
    # adapter refuses, by design, before any commitment is produced.
    pcm_snippet = b"\x00\x01\x02\x03\x04\x05\x06\x07"   # 8 bytes of pretend PCM
    facts_with_audio = {
        "subject": "patient-0001",
        "format_version": "openhear-audiogram-v1",
        "right_ear": {"symbol": "O", "thresholds": []},
        "left_ear": {"symbol": "X", "thresholds": []},
        "diagnostic_clip": pcm_snippet,                 # ← the violation
    }

    try:
        audiogram_commitment(facts_with_audio)
    except RawAudioRejectedError as exc:
        print("RawAudioRejectedError raised, as required:")
        print(f"  {exc}")
    else:
        raise AssertionError(
            "audiogram_commitment must reject raw audio payloads"
        )

    print()
    print("Why this boundary exists:")
    print(
        "  Raw environmental audio is sovereign data. If a PCM "
        "buffer can reach the commitment layer, it can reach the "
        "export bundle, and the bundle is the artefact that leaves "
        "the device. The adapter walks the entire facts payload "
        "(including nested mappings and lists) and refuses bytes, "
        "bytearray, memoryview, and NumPy ndarray on sight. If a "
        "byte string is genuinely needed in the record, the caller "
        "must hex- or base64-encode it first — a deliberate moment "
        "of consent rather than an accidental leak."
    )


# ── Entry point ────────────────────────────────────────────────────────────

def main() -> None:
    happy = demo_happy_path()
    demo_tamper_detection(happy)
    demo_raw_audio_boundary()
    print()
    print("Reference integration complete. See docs/INTEGRATORS.md for the "
          "full contract.")


if __name__ == "__main__":
    main()
