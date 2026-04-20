"""
fitting_data.py – canonical fitting-session dataclasses for OpenHear.

These dataclasses are the bridge between the existing platform-specific
:mod:`core.fitting_schema` (Phonak / Signia profiles) and the rest of
the pipeline.  Where ``fitting_schema`` is brand-aware, the structures
here are *brand neutral*: they describe what every modern hearing aid
exposes, regardless of vendor.

Data model:

    DeviceInfo        – manufacturer, model, firmware, serial.
    Audiogram         – per-ear thresholds (delegates to
                        :class:`audiogram.audiogram.Audiogram`).
    GainTable         – one frequency-band-indexed list of gains.
    CompressionProfile – per-band WDRC parameters.
    MPOProfile        – Maximum Power Output limits per band (safety).
    ProgrammeSlot     – one user-selectable programme.
    FittingSession    – the full snapshot at the moment of read.

All classes provide ``to_json``/``from_json`` for lossless round-tripping
to JSON files written by :mod:`core.read_fitting`.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from audiogram.audiogram import Audiogram
from core.fitting_schema import GainTable as _LegacyGainTable
from core.fitting_schema import PhonakFittingProfile, SigniaFittingProfile

__all__ = [
    "DeviceInfo",
    "GainTable",
    "CompressionProfile",
    "MPOProfile",
    "ProgrammeSlot",
    "FittingSession",
    "from_phonak",
    "from_signia",
]


@dataclass
class DeviceInfo:
    """Identifying details about the hearing aid hardware.

    Attributes:
        manufacturer: e.g. "Phonak".
        model: e.g. "Naida M70-SP".
        platform: e.g. "Marvel".
        serial: Device serial number as reported over HID.
        firmware: Firmware version string.
    """

    manufacturer: str = ""
    model: str = ""
    platform: str = ""
    serial: str = ""
    firmware: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceInfo":
        return cls(
            manufacturer=str(data.get("manufacturer", "")),
            model=str(data.get("model", "")),
            platform=str(data.get("platform", "")),
            serial=str(data.get("serial", "")),
            firmware=str(data.get("firmware", "")),
        )


@dataclass
class GainTable:
    """Per-frequency insertion gain in dB.

    Attributes:
        frequencies_hz: Centre frequencies of each band.
        gains_db: Insertion gain at each band (same length as
            *frequencies_hz*).
    """

    frequencies_hz: list[int] = field(default_factory=lambda: [
        250, 500, 1000, 1500, 2000, 3000, 4000, 6000, 8000,
    ])
    gains_db: list[float] = field(default_factory=lambda: [0.0] * 9)

    def __post_init__(self) -> None:
        if len(self.frequencies_hz) != len(self.gains_db):
            raise ValueError(
                "frequencies_hz and gains_db must have the same length "
                f"(got {len(self.frequencies_hz)} vs {len(self.gains_db)})."
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GainTable":
        return cls(
            frequencies_hz=list(data.get("frequencies_hz", [])),
            gains_db=[float(g) for g in data.get("gains_db", [])],
        )

    @classmethod
    def from_legacy(cls, gt: _LegacyGainTable) -> "GainTable":
        """Convert a :class:`core.fitting_schema.GainTable` to the new shape."""
        return cls(
            frequencies_hz=list(gt.frequencies_hz),
            gains_db=[float(g) for g in gt.gains_db],
        )


@dataclass
class CompressionProfile:
    """Per-band WDRC parameters.

    Each list is the same length, indexed by band.
    """

    centre_frequencies_hz: list[int] = field(default_factory=list)
    ratios: list[float] = field(default_factory=list)
    knee_db: list[float] = field(default_factory=list)
    attack_ms: list[float] = field(default_factory=list)
    release_ms: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        n = len(self.centre_frequencies_hz)
        for name, lst in (
            ("ratios", self.ratios),
            ("knee_db", self.knee_db),
            ("attack_ms", self.attack_ms),
            ("release_ms", self.release_ms),
        ):
            if len(lst) != n:
                raise ValueError(
                    f"{name} length {len(lst)} != centre_frequencies_hz length {n}."
                )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CompressionProfile":
        return cls(
            centre_frequencies_hz=list(data.get("centre_frequencies_hz", [])),
            ratios=[float(x) for x in data.get("ratios", [])],
            knee_db=[float(x) for x in data.get("knee_db", [])],
            attack_ms=[float(x) for x in data.get("attack_ms", [])],
            release_ms=[float(x) for x in data.get("release_ms", [])],
        )


@dataclass
class MPOProfile:
    """Maximum Power Output safety limits per band, in dB SPL."""

    centre_frequencies_hz: list[int] = field(default_factory=list)
    max_db_spl: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.centre_frequencies_hz) != len(self.max_db_spl):
            raise ValueError(
                "centre_frequencies_hz and max_db_spl must have equal length."
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MPOProfile":
        return cls(
            centre_frequencies_hz=list(data.get("centre_frequencies_hz", [])),
            max_db_spl=[float(x) for x in data.get("max_db_spl", [])],
        )


@dataclass
class ProgrammeSlot:
    """One user-selectable programme on the aid (e.g. ‘Quiet’, ‘Noisy’)."""

    slot_index: int = 0
    name: str = ""
    description: str = ""
    streaming_preference: str = "automatic"  # automatic | priority | off
    volume_offset_db: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProgrammeSlot":
        return cls(
            slot_index=int(data.get("slot_index", 0)),
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            streaming_preference=str(data.get("streaming_preference", "automatic")),
            volume_offset_db=float(data.get("volume_offset_db", 0.0)),
        )


@dataclass
class FittingSession:
    """A complete snapshot of a fitting at a moment in time.

    This is what :mod:`core.read_fitting` writes out and
    :mod:`core.write_fitting` reads back.  Every field is optional so a
    partial read can still be persisted.
    """

    schema_version: str = "openhear-fitting-v1"
    captured_at: str = ""  # ISO-8601 UTC timestamp.
    device: DeviceInfo = field(default_factory=DeviceInfo)
    audiogram: Audiogram | None = None
    right_gain: GainTable = field(default_factory=GainTable)
    left_gain: GainTable = field(default_factory=GainTable)
    right_compression: CompressionProfile = field(default_factory=CompressionProfile)
    left_compression: CompressionProfile = field(default_factory=CompressionProfile)
    right_mpo: MPOProfile = field(default_factory=MPOProfile)
    left_mpo: MPOProfile = field(default_factory=MPOProfile)
    programmes: list[ProgrammeSlot] = field(default_factory=list)
    raw_payload_hex: str = ""  # full HID dump for round-tripping.

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "schema_version": self.schema_version,
            "captured_at": self.captured_at,
            "device": self.device.to_dict(),
            "audiogram": self.audiogram.to_dict() if self.audiogram else None,
            "right_gain": self.right_gain.to_dict(),
            "left_gain": self.left_gain.to_dict(),
            "right_compression": self.right_compression.to_dict(),
            "left_compression": self.left_compression.to_dict(),
            "right_mpo": self.right_mpo.to_dict(),
            "left_mpo": self.left_mpo.to_dict(),
            "programmes": [p.to_dict() for p in self.programmes],
            "raw_payload_hex": self.raw_payload_hex,
        }
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FittingSession":
        ag = data.get("audiogram")
        return cls(
            schema_version=str(data.get("schema_version", "openhear-fitting-v1")),
            captured_at=str(data.get("captured_at", "")),
            device=DeviceInfo.from_dict(data.get("device", {})),
            audiogram=Audiogram.from_dict(ag) if ag else None,
            right_gain=GainTable.from_dict(data.get("right_gain", {})),
            left_gain=GainTable.from_dict(data.get("left_gain", {})),
            right_compression=CompressionProfile.from_dict(
                data.get("right_compression", {}),
            ),
            left_compression=CompressionProfile.from_dict(
                data.get("left_compression", {}),
            ),
            right_mpo=MPOProfile.from_dict(data.get("right_mpo", {})),
            left_mpo=MPOProfile.from_dict(data.get("left_mpo", {})),
            programmes=[ProgrammeSlot.from_dict(p) for p in data.get("programmes", [])],
            raw_payload_hex=str(data.get("raw_payload_hex", "")),
        )

    def to_json(self, **kwargs: Any) -> str:
        """Serialise to a JSON string (kwargs forwarded to ``json.dumps``)."""
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def from_json(cls, text: str) -> "FittingSession":
        return cls.from_dict(json.loads(text))


# ── Bridge to legacy fitting_schema -----------------------------------------


def from_phonak(profile: PhonakFittingProfile) -> FittingSession:
    """Build a :class:`FittingSession` from a legacy Phonak profile."""
    session = FittingSession()
    session.device = DeviceInfo(
        manufacturer="Phonak",
        model="Naida (legacy profile)",
        platform="Marvel",
        serial=profile.device_serial,
    )
    session.right_gain = GainTable.from_legacy(profile.gain_table)
    session.left_gain = GainTable.from_legacy(profile.gain_table)
    session.right_compression = CompressionProfile(
        centre_frequencies_hz=[ch.center_frequency_hz for ch in profile.compression_channels],
        ratios=[ch.compression_ratio for ch in profile.compression_channels],
        knee_db=[ch.knee_point_db for ch in profile.compression_channels],
        attack_ms=[ch.attack_ms for ch in profile.compression_channels],
        release_ms=[ch.release_ms for ch in profile.compression_channels],
    )
    session.left_compression = CompressionProfile(
        centre_frequencies_hz=[ch.center_frequency_hz for ch in profile.compression_channels],
        ratios=[ch.compression_ratio for ch in profile.compression_channels],
        knee_db=[ch.knee_point_db for ch in profile.compression_channels],
        attack_ms=[ch.attack_ms for ch in profile.compression_channels],
        release_ms=[ch.release_ms for ch in profile.compression_channels],
    )
    session.programmes = [ProgrammeSlot(slot_index=0, name=profile.program_name)]
    return session


def from_signia(profile: SigniaFittingProfile) -> FittingSession:
    """Build a :class:`FittingSession` from a legacy Signia profile."""
    session = FittingSession()
    session.device = DeviceInfo(
        manufacturer="Signia",
        model="Insio (legacy profile)",
        platform="AX",
        serial=profile.device_serial,
    )
    session.right_gain = GainTable.from_legacy(profile.gain_table)
    session.left_gain = GainTable.from_legacy(profile.gain_table)
    session.right_compression = CompressionProfile(
        centre_frequencies_hz=[ch.center_frequency_hz for ch in profile.compression_channels],
        ratios=[ch.compression_ratio for ch in profile.compression_channels],
        knee_db=[ch.knee_point_db for ch in profile.compression_channels],
        attack_ms=[ch.attack_ms for ch in profile.compression_channels],
        release_ms=[ch.release_ms for ch in profile.compression_channels],
    )
    session.left_compression = CompressionProfile(
        centre_frequencies_hz=[ch.center_frequency_hz for ch in profile.compression_channels],
        ratios=[ch.compression_ratio for ch in profile.compression_channels],
        knee_db=[ch.knee_point_db for ch in profile.compression_channels],
        attack_ms=[ch.attack_ms for ch in profile.compression_channels],
        release_ms=[ch.release_ms for ch in profile.compression_channels],
    )
    session.programmes = [ProgrammeSlot(slot_index=0, name=profile.program_name)]
    return session
