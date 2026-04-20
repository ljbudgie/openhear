"""
adapters.py – bridge OpenHear sovereign records into commitments.

These adapters are the one‑way boundary between OpenHear's domain
types (audiogram, fitting profile, MPO result) and the PersonGate
commitment primitive in :mod:`advocacy.gate`.

The adapters enforce the *sovereign‑handling invariants* that apply
specifically to audio data:

* **No raw PCM ever.**  The wristband's edge‑AI classifier processes
  environmental audio on‑device.  That audio must never appear in an
  advocacy bundle.  :func:`_reject_raw_audio` walks the facts payload
  and raises :class:`RawAudioRejectedError` if it finds ``bytes``,
  ``bytearray``, ``memoryview``, or a NumPy ``ndarray`` — the four
  ways raw audio could realistically slip in.
* **Domain tagging.**  Each adapter pre‑populates Burgess‑relevant
  tags (``audiogram``, ``fitting``, ``mpo``) so downstream companions
  can categorise NULL challenges without reparsing the commitment.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from advocacy.gate import Commitment, commit


class RawAudioRejectedError(ValueError):
    """Raised when a raw audio payload is detected in advocacy facts.

    Advocacy bundles are meant to leave the device; raw environmental
    audio captured by the wristband is sovereign data that must never
    do so.  This exception is the adapter's last line of defence.
    """


def _is_raw_audio(value: Any) -> bool:
    """Return ``True`` if ``value`` looks like a raw audio payload.

    The check is conservative: anything byte‑like and anything that
    looks like a NumPy array is treated as raw audio regardless of
    actual content.  False positives here are strictly safer than
    false negatives — a user can always convert a genuinely needed
    byte string to hex or base64 themselves if they really want it in
    the record, which is itself a deliberate moment of consent.
    """

    if isinstance(value, (bytes, bytearray, memoryview)):
        return True
    # Detect NumPy arrays without importing NumPy at module load time.
    cls = type(value)
    module = getattr(cls, "__module__", "") or ""
    name = getattr(cls, "__name__", "") or ""
    if module.split(".", 1)[0] == "numpy" and name == "ndarray":
        return True
    return False


def _reject_raw_audio(facts: Mapping[str, Any], _path: str = "") -> None:
    """Walk ``facts`` and raise if any raw audio payload is present."""

    for key, value in facts.items():
        here = f"{_path}.{key}" if _path else str(key)
        if _is_raw_audio(value):
            raise RawAudioRejectedError(
                f"raw audio payload at '{here}' cannot be committed to an "
                "advocacy bundle; hash, classify, or summarise it on-device first"
            )
        if isinstance(value, Mapping):
            _reject_raw_audio(value, here)
        elif isinstance(value, (list, tuple)):
            for i, item in enumerate(value):
                sub_path = f"{here}[{i}]"
                if _is_raw_audio(item):
                    raise RawAudioRejectedError(
                        f"raw audio payload at '{sub_path}' cannot be "
                        "committed to an advocacy bundle; hash, classify, "
                        "or summarise it on-device first"
                    )
                if isinstance(item, Mapping):
                    _reject_raw_audio(item, sub_path)


def _merge_tags(base: Iterable[str], extra: Iterable[str] | None) -> tuple[str, ...]:
    """Return ``base`` tags followed by ``extra`` tags, deduplicated
    while preserving order so domain tags always appear first."""

    seen: set[str] = set()
    merged: list[str] = []
    for tag in list(base) + list(extra or ()):
        if tag not in seen:
            seen.add(tag)
            merged.append(tag)
    return tuple(merged)


# ── Audiogram ──────────────────────────────────────────────────────────────

def audiogram_commitment(audiogram: Mapping[str, Any],
                         tags: Iterable[str] | None = None) -> Commitment:
    """Produce a :class:`Commitment` over an ``openhear-audiogram-v1`` dict.

    ``audiogram`` is the on‑disk JSON shape used throughout the
    :mod:`audiogram` package (see ``audiogram/loader.py``).  The whole
    record is hashed — subject, source, date, format version, notes,
    and both ears' thresholds — so the commitment uniquely binds to
    the exact audiogram presented to the reviewing party.
    """

    if not isinstance(audiogram, Mapping):
        raise TypeError("audiogram must be a Mapping (openhear-audiogram-v1 dict)")
    _reject_raw_audio(audiogram)
    return commit(
        label="audiogram",
        facts=audiogram,
        tags=_merge_tags(("audiogram", "openhear-audiogram-v1"), tags),
    )


# ── Fitting profile ────────────────────────────────────────────────────────

def fitting_commitment(fitting: Mapping[str, Any],
                       tags: Iterable[str] | None = None) -> Commitment:
    """Produce a :class:`Commitment` over a fitting profile dict.

    The "fitting profile" is any structured description of the DSP
    parameters applied to a user's aids (gain curves, compression
    ratios, own‑voice bypass flags, program memory).  OpenHear does
    not fix a single schema here — the commitment is computed over
    whatever the caller passes, so fitting formats can evolve without
    breaking advocacy compatibility.
    """

    if not isinstance(fitting, Mapping):
        raise TypeError("fitting must be a Mapping of DSP parameters")
    _reject_raw_audio(fitting)
    return commit(
        label="fitting",
        facts=fitting,
        tags=_merge_tags(("fitting", "dsp-parameters"), tags),
    )


# ── MPO safety calculation ─────────────────────────────────────────────────

def mpo_commitment(mpo: Mapping[str, Any],
                   tags: Iterable[str] | None = None) -> Commitment:
    """Produce a :class:`Commitment` over an MPO safety calculation.

    MPO (maximum power output) calculations are the sovereign record
    most likely to matter in a safety‑adjacent institutional dispute
    — for example, an employer insisting on a headset whose output
    exceeds the user's calculated safe ceiling.  Committing the
    calculation produces verifiable evidence without leaking the
    calculation inputs until the user chooses to reveal them.
    """

    if not isinstance(mpo, Mapping):
        raise TypeError("mpo must be a Mapping of MPO calculator output")
    _reject_raw_audio(mpo)
    return commit(
        label="mpo",
        facts=mpo,
        tags=_merge_tags(("mpo", "safety-ceiling"), tags),
    )
