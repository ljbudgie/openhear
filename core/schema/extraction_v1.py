"""
extraction_v1.py – the ``openhear-extraction-v1`` schema.

This is the canonical, on-disk shape produced by ``openhear noahlink
extract`` / ``backup``.  It is a *superset* of the existing
:class:`core.fitting_data.FittingSession` schema:

* It adds bone-conduction (BC) thresholds alongside air-conduction (AC)
  so a full audiometric picture is preserved.
* It adds an optional Real-Ear-to-Coupler Difference (RECD) profile,
  which clinical fittings rely on to map 2-cc coupler measurements to
  in-ear sound pressure level.
* It carries provenance metadata: which vendor adapter produced the
  document, whether the read path is verified against real hardware,
  and a confidence score in ``[0, 1]``.
* It carries a list of :class:`ExtractionSafetyFlag` entries so the
  output of :mod:`core.safety` round-trips with the document.
* It exposes a deterministic SHA-256 commitment over its canonical JSON
  serialisation, so a user can later prove a backup has not been
  tampered with.

The schema uses :mod:`dataclasses` to match the rest of the codebase
(no new runtime dependencies).  All fields are typed and validated in
``__post_init__``.

The on-disk format is JSON; ``ExtractedFitting.to_dict()`` returns a
plain ``dict`` ready for ``json.dumps`` and ``from_dict()`` accepts the
same shape (unknown keys are silently ignored so newer firmware
payloads do not break older builds).

This module is **not** a medical device.  See the project README for
the full disclaimer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from audiogram.audiogram import (
    MAX_THRESHOLD_DB_HL,
    MIN_THRESHOLD_DB_HL,
    Audiogram,
)
from core.fitting_data import (
    CompressionProfile,
    DeviceInfo,
    GainTable,
    MPOProfile,
    ProgrammeSlot,
)

__all__ = [
    "SCHEMA_VERSION",
    "BoneConductionAudiogram",
    "ExtractedFitting",
    "ExtractionSafetyFlag",
    "RECDProfile",
]

#: Canonical schema-version string written into every document.
SCHEMA_VERSION: str = "openhear-extraction-v1"

#: Severity levels recognised on :class:`ExtractionSafetyFlag`.
SAFETY_LEVELS: frozenset[str] = frozenset({"info", "warning", "critical"})


# ── Bone-conduction audiogram -----------------------------------------------


@dataclass
class BoneConductionAudiogram:
    """Bone-conduction (BC) thresholds, in dB HL, per ear.

    The dict shape matches :class:`audiogram.audiogram.Audiogram` so the
    same loaders/visualisers can be reused.  Validation enforces the
    ISO 8253-1 valid range.
    """

    left_ear: dict[int, float] = field(default_factory=dict)
    right_ear: dict[int, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.left_ear = _coerce_db_hl_mapping(self.left_ear)
        self.right_ear = _coerce_db_hl_mapping(self.right_ear)

    def to_dict(self) -> dict[str, Any]:
        return {
            "left_ear": {str(f): v for f, v in self.left_ear.items()},
            "right_ear": {str(f): v for f, v in self.right_ear.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BoneConductionAudiogram":
        return cls(
            left_ear=_mapping_from_jsonish(data.get("left_ear", {})),
            right_ear=_mapping_from_jsonish(data.get("right_ear", {})),
        )


# ── RECD --------------------------------------------------------------------


@dataclass
class RECDProfile:
    """Real-Ear-to-Coupler Difference values, in dB, per ear.

    RECD is the per-frequency offset between SPL measured in a 2-cc
    coupler and SPL at the eardrum.  Clinical software uses it to
    convert coupler-measured gain into in-ear gain — values typically
    range from a few dB at low frequencies to >15 dB at high
    frequencies in small ear canals.

    Attributes:
        frequencies_hz: Centre frequencies (Hz) shared across both ears.
        left_db: Left-ear offsets (dB), same length as
            ``frequencies_hz``.
        right_db: Right-ear offsets (dB), same length as
            ``frequencies_hz``.
    """

    frequencies_hz: list[int] = field(default_factory=list)
    left_db: list[float] = field(default_factory=list)
    right_db: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        n = len(self.frequencies_hz)
        for name, lst in (("left_db", self.left_db), ("right_db", self.right_db)):
            if len(lst) != n:
                raise ValueError(
                    f"RECDProfile.{name} length {len(lst)} != frequencies_hz length {n}."
                )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RECDProfile":
        return cls(
            frequencies_hz=[int(f) for f in data.get("frequencies_hz", [])],
            left_db=[float(v) for v in data.get("left_db", [])],
            right_db=[float(v) for v in data.get("right_db", [])],
        )


# ── Safety flag carrier -----------------------------------------------------


@dataclass
class ExtractionSafetyFlag:
    """A single safety-relevant finding attached to an extraction document.

    The shape is intentionally compatible with the flags emitted by
    :class:`core.safety.SafetyReport` so a report can round-trip into,
    and out of, the on-disk document.

    Attributes:
        level: One of ``"info"``, ``"warning"``, ``"critical"``.
        code: Short machine-readable identifier (e.g.
            ``"gain_exceeds_ceiling"``).
        message: Human-readable description.
        location: Optional dotted path into the document
            (e.g. ``"right_gain[3]"``) that points at the offending
            value.
    """

    level: str
    code: str
    message: str
    location: str = ""

    def __post_init__(self) -> None:
        if self.level not in SAFETY_LEVELS:
            raise ValueError(
                f"ExtractionSafetyFlag.level must be one of "
                f"{sorted(SAFETY_LEVELS)}, got {self.level!r}."
            )
        if not self.code:
            raise ValueError("ExtractionSafetyFlag.code must be a non-empty string.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExtractionSafetyFlag":
        return cls(
            level=str(data.get("level", "info")),
            code=str(data.get("code", "")),
            message=str(data.get("message", "")),
            location=str(data.get("location", "")),
        )


# ── ExtractedFitting --------------------------------------------------------


@dataclass
class ExtractedFitting:
    """Top-level ``openhear-extraction-v1`` document.

    See module docstring for the rationale.  Every field is optional so
    partial reads (e.g. when only an audiogram could be recovered) can
    still be persisted and round-tripped.

    Provenance fields:
        vendor_adapter: Identifier of the adapter that produced this
            document (e.g. ``"phonak.mock"``, ``"generic.read_session"``).
        is_verified: ``True`` only when the adapter has been validated
            against real hardware of the named model/platform.  Mock
            and reverse-engineered adapters MUST leave this at
            ``False``; the CLI surfaces it prominently.
        confidence: Adapter's self-reported confidence in the parsed
            data, in ``[0, 1]``.  Mock adapters typically report
            ``0.0`` to make it impossible to mistake their output for
            real fittings.
        safety_flags: Results of :mod:`core.safety` evaluation, carried
            in the document so consumers do not have to re-run the
            evaluation to know whether the fitting is plausible.
    """

    schema_version: str = SCHEMA_VERSION
    captured_at: str = ""  # ISO-8601 UTC.
    vendor_adapter: str = "unknown"
    is_verified: bool = False
    confidence: float = 0.0
    device: DeviceInfo = field(default_factory=DeviceInfo)
    air_conduction: Audiogram | None = None
    bone_conduction: BoneConductionAudiogram | None = None
    recd: RECDProfile | None = None
    right_gain: GainTable = field(default_factory=GainTable)
    left_gain: GainTable = field(default_factory=GainTable)
    right_compression: CompressionProfile = field(default_factory=CompressionProfile)
    left_compression: CompressionProfile = field(default_factory=CompressionProfile)
    right_mpo: MPOProfile = field(default_factory=MPOProfile)
    left_mpo: MPOProfile = field(default_factory=MPOProfile)
    programmes: list[ProgrammeSlot] = field(default_factory=list)
    safety_flags: list[ExtractionSafetyFlag] = field(default_factory=list)
    raw_payload_hex: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"ExtractedFitting requires schema_version={SCHEMA_VERSION!r}, "
                f"got {self.schema_version!r}."
            )
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"ExtractedFitting.confidence must be in [0, 1], got {self.confidence}."
            )

    # -- serialisation ------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "captured_at": self.captured_at,
            "vendor_adapter": self.vendor_adapter,
            "is_verified": self.is_verified,
            "confidence": self.confidence,
            "device": self.device.to_dict(),
            "air_conduction": (self.air_conduction.to_dict() if self.air_conduction else None),
            "bone_conduction": (self.bone_conduction.to_dict() if self.bone_conduction else None),
            "recd": self.recd.to_dict() if self.recd else None,
            "right_gain": self.right_gain.to_dict(),
            "left_gain": self.left_gain.to_dict(),
            "right_compression": self.right_compression.to_dict(),
            "left_compression": self.left_compression.to_dict(),
            "right_mpo": self.right_mpo.to_dict(),
            "left_mpo": self.left_mpo.to_dict(),
            "programmes": [p.to_dict() for p in self.programmes],
            "safety_flags": [f.to_dict() for f in self.safety_flags],
            "raw_payload_hex": self.raw_payload_hex,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExtractedFitting":
        ac = data.get("air_conduction")
        bc = data.get("bone_conduction")
        recd = data.get("recd")
        return cls(
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
            captured_at=str(data.get("captured_at", "")),
            vendor_adapter=str(data.get("vendor_adapter", "unknown")),
            is_verified=bool(data.get("is_verified", False)),
            confidence=float(data.get("confidence", 0.0)),
            device=DeviceInfo.from_dict(data.get("device", {})),
            air_conduction=Audiogram.from_dict(ac) if ac else None,
            bone_conduction=BoneConductionAudiogram.from_dict(bc) if bc else None,
            recd=RECDProfile.from_dict(recd) if recd else None,
            right_gain=GainTable.from_dict(data.get("right_gain", {})),
            left_gain=GainTable.from_dict(data.get("left_gain", {})),
            right_compression=CompressionProfile.from_dict(data.get("right_compression", {})),
            left_compression=CompressionProfile.from_dict(data.get("left_compression", {})),
            right_mpo=MPOProfile.from_dict(data.get("right_mpo", {})),
            left_mpo=MPOProfile.from_dict(data.get("left_mpo", {})),
            programmes=[ProgrammeSlot.from_dict(p) for p in data.get("programmes", [])],
            safety_flags=[ExtractionSafetyFlag.from_dict(f) for f in data.get("safety_flags", [])],
            raw_payload_hex=str(data.get("raw_payload_hex", "")),
        )

    def to_json(self, *, indent: int | None = 2) -> str:
        """Pretty JSON for humans.  Uses key order from :meth:`to_dict`."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False)

    @classmethod
    def from_json(cls, text: str) -> "ExtractedFitting":
        return cls.from_dict(json.loads(text))

    # -- SHA-256 commitment -------------------------------------------------

    def canonical_json(self) -> str:
        """Return a deterministic JSON encoding for hashing.

        ``sort_keys=True`` and compact separators guarantee the same
        document yields the same bytes (and therefore the same
        SHA-256) on every machine and Python version.  The
        ``safety_flags`` and ``raw_payload_hex`` fields are *included*
        — the user is committing to the entire document.
        """
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def sha256_commitment(self) -> str:
        """Hex-encoded SHA-256 of :meth:`canonical_json`."""
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


# ── Helpers -----------------------------------------------------------------


def _coerce_db_hl_mapping(values: Iterable) -> dict[int, float]:
    """Coerce a mapping or list of pairs into ``{Hz int: dB HL float}``.

    Mirrors the validation in :func:`audiogram.audiogram._coerce_thresholds`
    so AC and BC use the same rules.
    """
    if hasattr(values, "items"):
        items = list(values.items())  # type: ignore[union-attr]
    else:
        items = list(values)
    out: dict[int, float] = {}
    for freq_raw, db_raw in items:
        try:
            freq = int(freq_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"BC audiogram frequency must be integer-like, got {freq_raw!r}."
            ) from exc
        try:
            db = float(db_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"BC threshold for {freq} Hz must be numeric, got {db_raw!r}."
            ) from exc
        if not (MIN_THRESHOLD_DB_HL <= db <= MAX_THRESHOLD_DB_HL):
            raise ValueError(
                f"BC threshold for {freq} Hz is {db} dB HL, outside the valid "
                f"range [{MIN_THRESHOLD_DB_HL}, {MAX_THRESHOLD_DB_HL}]."
            )
        out[freq] = db
    return dict(sorted(out.items()))


def _mapping_from_jsonish(data: Any) -> dict[int, float]:
    """Accept either a dict (``{"500": 30}``) or a list of pairs."""
    if isinstance(data, dict):
        return {int(k): float(v) for k, v in data.items()}
    return {int(k): float(v) for k, v in data}
