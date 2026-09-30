"""Bone-conduction output pathway for OpenHear.

Takes an existing air-conduction :class:`~dsp.audiogram_profile.Prescription`
and retargets it for a contact transducer on bone.  This module does **not**
implement an intra-oral or tooth-mounted appliance.  See
``docs/FTO_SONITUS.md`` and ``docs/BONE_CONDUCTION_PATHWAY.md``.

Design:
    * Prefer measured bone-conduction thresholds when the caller supplies
      them.  Otherwise keep the air-conduction thresholds and mark the
      source.
    * Apply a *generic* transducer compensation table.  The numbers are an
      OpenHear heuristic (BC pads typically under-deliver below 500 Hz and
      peak in the mid band).  They are not a copied manufacturer curve.
    * Optional contralateral (SSD / CROS-style) routing is a label on the
      result, not a second DSP graph.
    * Extra safety attenuation sits on top of ``dsp.output_safety``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping

from dsp.audiogram_profile import (
    PRESCRIPTION_FREQUENCIES_HZ,
    BandPrescription,
    Prescription,
    prescribe,
)
from audiogram.audiogram import Audiogram

Coupler = Literal["mastoid", "forehead", "abutment", "unspecified"]
SsdRoute = Literal["none", "contralateral"]
Ear = Literal["left", "right"]

# Generic BC pad compensation in dB, keyed by Hz.
# Positive = add gain to offset a weak transducer region.
# This is an OpenHear starting table, not a lab calibration and not a
# SoundBite response.  Replace with a measured coupler curve when one exists.
BC_COMPENSATION_DB: dict[int, float] = {
    250: 6.0,
    500: 4.0,
    1000: 0.0,
    2000: -2.0,
    4000: -1.0,
    6000: 1.0,
    8000: 3.0,
}

# Conservative extra ceiling until a measured acceleration limit exists.
BC_SAFETY_ATTENUATION_DB: float = 3.0

_MAX_BAND_GAIN_DB: float = 32.0
_MIN_BAND_GAIN_DB: float = 0.0


@dataclass
class BoneConductionPrescription:
    """AC prescription retargeted for a bone-conduction coupler."""

    air: Prescription
    right: list[BandPrescription]
    left: list[BandPrescription]
    coupler: Coupler
    threshold_source: Literal["bone", "air_fallback"]
    ssd_route: SsdRoute = "none"
    dead_side: Ear | None = None
    safety_attenuation_db: float = BC_SAFETY_ATTENUATION_DB
    method: str = "OpenHear BC pathway v1"
    notes: list[str] = field(default_factory=list)

    def gains_db(self, ear: str) -> dict[int, float]:
        bands = self.right if ear == "right" else self.left
        return {b.freq_hz: b.gain_db for b in bands}


def _comp(freq: int) -> float:
    if freq in BC_COMPENSATION_DB:
        return BC_COMPENSATION_DB[freq]
    below = [f for f in BC_COMPENSATION_DB if f <= freq]
    above = [f for f in BC_COMPENSATION_DB if f >= freq]
    if not below:
        return BC_COMPENSATION_DB[min(BC_COMPENSATION_DB)]
    if not above:
        return BC_COMPENSATION_DB[max(BC_COMPENSATION_DB)]
    lo, hi = max(below), min(above)
    if lo == hi:
        return BC_COMPENSATION_DB[lo]
    w = (freq - lo) / (hi - lo)
    return (1.0 - w) * BC_COMPENSATION_DB[lo] + w * BC_COMPENSATION_DB[hi]


def _retarget_band(band: BandPrescription) -> BandPrescription:
    gain = band.gain_db + _comp(band.freq_hz) - BC_SAFETY_ATTENUATION_DB
    gain = max(_MIN_BAND_GAIN_DB, min(_MAX_BAND_GAIN_DB, round(gain, 1)))
    return BandPrescription(
        freq_hz=band.freq_hz,
        threshold_db_hl=band.threshold_db_hl,
        gain_db=gain,
        ratio=band.ratio,
        knee_dbfs=band.knee_dbfs,
    )


def _audiogram_from_bc(
    ac: Audiogram,
    bc_left: Mapping[int, float] | None,
    bc_right: Mapping[int, float] | None,
) -> tuple[Audiogram, Literal["bone", "air_fallback"]]:
    if not bc_left and not bc_right:
        return ac, "air_fallback"
    left = dict(bc_left) if bc_left else dict(ac.left_ear)
    right = dict(bc_right) if bc_right else dict(ac.right_ear)
    return Audiogram(
        left_ear=left,
        right_ear=right,
        date_measured=ac.date_measured,
        source=ac.source,
        subject=ac.subject,
        notes=(ac.notes + " | BC thresholds used as cochlear target").strip(" |"),
    ), "bone"


def prescribe_bc(
    audiogram: Audiogram,
    *,
    coupler: Coupler = "unspecified",
    bc_left: Mapping[int, float] | None = None,
    bc_right: Mapping[int, float] | None = None,
    ssd_route: SsdRoute = "none",
    dead_side: Ear | None = None,
) -> BoneConductionPrescription:
    """Build a bone-conduction prescription from an air-conduction audiogram.

    Args:
        audiogram: Canonical AC audiogram.
        coupler: Where vibration is expected to meet bone.  ``oral`` is not
            a legal value.
        bc_left / bc_right: Optional bone-conduction thresholds (dB HL).
        ssd_route: ``contralateral`` labels CROS-style routing.
        dead_side: Required when ``ssd_route='contralateral'``.
    """
    if coupler not in ("mastoid", "forehead", "abutment", "unspecified"):
        raise ValueError(
            f"coupler {coupler!r} is not published. "
            "Oral / tooth couplers are reserved pending FTO (docs/FTO_SONITUS.md)."
        )
    if ssd_route == "contralateral" and dead_side not in ("left", "right"):
        raise ValueError("contralateral routing requires dead_side='left' or 'right'")

    target, source = _audiogram_from_bc(audiogram, bc_left, bc_right)
    air = prescribe(target)
    notes = [
        f"coupler={coupler}",
        f"threshold_source={source}",
        f"safety_attenuation_db={BC_SAFETY_ATTENUATION_DB}",
    ]
    if ssd_route == "contralateral":
        notes.append(f"ssd_route=contralateral dead_side={dead_side}")

    return BoneConductionPrescription(
        air=air,
        right=[_retarget_band(b) for b in air.right],
        left=[_retarget_band(b) for b in air.left],
        coupler=coupler,
        threshold_source=source,
        ssd_route=ssd_route,
        dead_side=dead_side,
        notes=notes,
    )


__all__ = [
    "BC_COMPENSATION_DB",
    "BC_SAFETY_ATTENUATION_DB",
    "BoneConductionPrescription",
    "PRESCRIPTION_FREQUENCIES_HZ",
    "prescribe_bc",
]
