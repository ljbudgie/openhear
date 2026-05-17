"""
phonak.py – mock-only Phonak adapter.

This adapter is **read-only** and does **not** talk to real Phonak
hardware.  It exists so the rest of the OpenHear toolchain — CLI,
schema, safety evaluation, backup format — can be developed and tested
without a Noahlink dongle plus a real Phonak Naída M70-SP / Lumity /
Infinio aid in the loop.

Why a mock rather than a "best-effort" Phonak protocol implementation?

Phonak's wireless fitting protocol (the Marvel/Lumity/Infinio stack
running over Noahlink Wireless 2) is proprietary, undocumented, and
shares no published intermediate representation with Noah.  Any
"real-looking" extractor written without a verified device would
silently produce wrong values — exactly the failure mode the project's
safety principles forbid (raw audio never stored, hard safety
limiters, *user trust must not be misplaced*).  Until a real device is
available for verification, the only honest thing this module can
return is a clearly-labelled mock.

The adapter therefore:

* Returns an :class:`ExtractedFitting` whose ``vendor_adapter`` is
  ``"phonak.mock"``, ``is_verified`` is ``False``, and ``confidence``
  is ``0.0``.  Downstream safety evaluation flags these (see
  :mod:`core.safety`).
* Refuses to do anything resembling a *write*.  The
  :data:`WRITE_SUPPORTED` flag is ``False`` and
  :func:`raise_if_write_disabled` is called from any code path that
  might mutate device state.
* Gates all execution behind the ``OPENHEAR_ENABLE_PHONAK_MOCK``
  environment variable so a careless ``openhear noahlink extract --aid
  phonak`` in production cannot mistake a mock fitting for a real one.
  (Tests set this automatically via :func:`enable_for_testing`.)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

from audiogram.audiogram import Audiogram
from core.fitting_data import (
    CompressionProfile,
    DeviceInfo,
    GainTable,
    MPOProfile,
    ProgrammeSlot,
)
from core.schema.extraction_v1 import (
    BoneConductionAudiogram,
    ExtractedFitting,
    ExtractionSafetyFlag,
    RECDProfile,
)

__all__ = [
    "FEATURE_FLAG_ENV",
    "WRITE_SUPPORTED",
    "PhonakMockAdapter",
    "enable_for_testing",
    "is_enabled",
    "raise_if_write_disabled",
    "read_extraction",
]

#: Environment variable that must be set to "1" before the mock adapter
#: will produce any output.  Forces an opt-in so users never receive
#: placeholder data they could mistake for a real fitting.
FEATURE_FLAG_ENV: str = "OPENHEAR_ENABLE_PHONAK_MOCK"

#: This adapter never writes to hardware.  Kept as a module-level
#: constant so callers can check before constructing a write request.
WRITE_SUPPORTED: bool = False

#: Conservative defaults used by the mock so the resulting document
#: looks plausible to humans yet trips no safety thresholds.
_DEFAULT_FREQUENCIES_HZ: list[int] = [250, 500, 1000, 2000, 3000, 4000, 6000, 8000]


def is_enabled() -> bool:
    """Return ``True`` if the feature flag environment variable is set."""
    return os.environ.get(FEATURE_FLAG_ENV, "") == "1"


def enable_for_testing(monkeypatch=None) -> None:
    """Enable the mock for the duration of a test.

    When given a pytest ``monkeypatch`` fixture, the flag is unset at
    test teardown automatically.  Without it the caller is responsible
    for cleanup.
    """
    if monkeypatch is not None:
        monkeypatch.setenv(FEATURE_FLAG_ENV, "1")
    else:  # pragma: no cover - convenience path
        os.environ[FEATURE_FLAG_ENV] = "1"


def raise_if_write_disabled() -> None:
    """Raise ``RuntimeError`` — the mock has no write path, ever.

    Provided so write-path callers can do an explicit ``assert``-style
    check without importing constants.
    """
    raise RuntimeError(
        "Phonak adapter is mock-only and read-only.  Writing fitting "
        "parameters to a real Phonak hearing aid via OpenHear is NOT "
        "supported and would risk damaging the device or your hearing."
    )


@dataclass
class PhonakMockAdapter:
    """Read-only mock adapter for Phonak Marvel/Lumity/Infinio aids.

    Construct with an optional serial number for the device-info block.
    Call :meth:`read` to obtain an :class:`ExtractedFitting`.
    """

    device_serial: str = "MOCK-PHONAK-000000"
    model: str = "Naida M70-SP (mock)"
    platform: str = "Marvel (mock)"

    def read(self) -> ExtractedFitting:
        """Produce a placeholder extraction.

        Raises:
            RuntimeError: If the feature flag environment variable is
                not set.  Forcing an opt-in stops the mock from being
                used by accident in production code.
        """
        if not is_enabled():
            raise RuntimeError(
                f"Phonak mock adapter is disabled.  Set the "
                f"{FEATURE_FLAG_ENV}=1 environment variable to opt in "
                "to placeholder data, and read the warnings in the "
                "module docstring before doing so."
            )

        device = DeviceInfo(
            manufacturer="Phonak",
            model=self.model,
            platform=self.platform,
            serial=self.device_serial,
            firmware="unknown",
        )

        # A mild, symmetric moderate sensorineural loss — plausible but
        # not a real measurement.  Values chosen to sit comfortably
        # inside every default safety threshold.
        air_left = {
            f: db for f, db in zip(_DEFAULT_FREQUENCIES_HZ, [20, 25, 30, 40, 45, 50, 55, 55])
        }
        air_right = dict(air_left)
        ac = Audiogram(
            left_ear=air_left,
            right_ear=air_right,
            date_measured="unknown",
            source="synthetic",
            notes="Mock data — produced by core.noahlink.vendors.phonak.",
        )
        bc = BoneConductionAudiogram(
            left_ear={f: max(0, v - 5) for f, v in air_left.items()},
            right_ear={f: max(0, v - 5) for f, v in air_right.items()},
        )

        recd = RECDProfile(
            frequencies_hz=list(_DEFAULT_FREQUENCIES_HZ),
            left_db=[2.0, 3.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0],
            right_db=[2.0, 3.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0],
        )

        # Conservative half-gain prescription as a starting point;
        # documented as such — this is NOT NAL-NL2.
        gains_db = [round(v * 0.5, 1) for v in [20, 25, 30, 40, 45, 50, 55, 55]]
        gain = GainTable(frequencies_hz=list(_DEFAULT_FREQUENCIES_HZ), gains_db=gains_db)

        n_bands = len(_DEFAULT_FREQUENCIES_HZ)
        compression = CompressionProfile(
            centre_frequencies_hz=list(_DEFAULT_FREQUENCIES_HZ),
            ratios=[2.0] * n_bands,
            knee_db=[50.0] * n_bands,
            attack_ms=[5.0] * n_bands,
            release_ms=[50.0] * n_bands,
        )
        mpo = MPOProfile(
            centre_frequencies_hz=list(_DEFAULT_FREQUENCIES_HZ),
            max_db_spl=[110.0] * n_bands,
        )

        programmes = [
            ProgrammeSlot(slot_index=0, name="AutoSense (mock)"),
            ProgrammeSlot(slot_index=1, name="Speech in Noise (mock)"),
        ]

        flags = [
            ExtractionSafetyFlag(
                level="warning",
                code="mock_data",
                message=(
                    "This document was produced by the Phonak MOCK adapter. "
                    "It contains placeholder values and MUST NOT be used to "
                    "program a real hearing aid."
                ),
                location="vendor_adapter",
            )
        ]

        return ExtractedFitting(
            captured_at=_utc_now_iso(),
            vendor_adapter="phonak.mock",
            is_verified=False,
            confidence=0.0,
            device=device,
            air_conduction=ac,
            bone_conduction=bc,
            recd=recd,
            right_gain=gain,
            left_gain=gain,
            right_compression=compression,
            left_compression=compression,
            right_mpo=mpo,
            left_mpo=mpo,
            programmes=programmes,
            safety_flags=flags,
            raw_payload_hex="",
        )


def read_extraction(*, device_serial: str = "MOCK-PHONAK-000000") -> ExtractedFitting:
    """Module-level convenience wrapper around :class:`PhonakMockAdapter`."""
    return PhonakMockAdapter(device_serial=device_serial).read()


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
