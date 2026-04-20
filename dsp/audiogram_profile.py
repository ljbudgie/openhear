"""
audiogram_profile.py – audiogram-driven gain prescription for OpenHear.

Implements an open approximation of NAL-NL2 (the National Acoustic
Laboratories' nonlinear prescription, version 2) that converts a
:class:`audiogram.audiogram.Audiogram` into per-band insertion gains
and compression ratios for the live DSP pipeline.

Why "approximation":
    NAL-NL2 itself is described in published papers (Keidser et al.,
    *Audiology Today*, 2011) but the current proprietary fitting
    software bundles polynomial coefficients that are not redistributable.
    This module implements the *spirit* of NAL-NL2 — frequency-shaped
    insertion gain that scales sub-linearly with hearing loss, with
    higher compression ratios for greater loss — using publicly
    documented heuristics rather than the proprietary fitting formula.

The output is intentionally conservative.  Users with significant
hearing loss should still seek an audiologist's prescription; this
module exists so the OpenHear pipeline has a sensible starting point
without requiring a clinical visit.

References:
    * Keidser, G., Dillon, H., Flax, M., Ching, T. & Brewer, S. (2011).
      The NAL-NL2 prescription procedure. *Audiology Research*, 1(e24).
    * Byrne, D. & Dillon, H. (1986). The National Acoustic Laboratories'
      (NAL) new procedure for selecting the gain and frequency response
      of a hearing aid. *Ear & Hearing*, 7(4).
"""

from __future__ import annotations

from dataclasses import dataclass

from audiogram.audiogram import Audiogram


# Frequencies prescribed by this module.  Aligned with the four-band
# WDRC layout and standard audiometric points.
PRESCRIPTION_FREQUENCIES_HZ: tuple[int, ...] = (
    250, 500, 1000, 2000, 4000, 6000, 8000,
)

# Heuristic constant from Byrne/Dillon NAL-R: roughly 0.31 of the
# threshold contributes to insertion gain at the same frequency.
# NAL-NL2 reduces this for compressive prescriptions; we use the same
# scaling since this module emits explicit ratios separately.
_NAL_GAIN_SLOPE: float = 0.31

# Clip individual band gains to avoid prescribing more gain than the
# downstream amplifier can safely deliver without feedback.
_MAX_BAND_GAIN_DB: float = 35.0
_MIN_BAND_GAIN_DB: float = 0.0


@dataclass
class BandPrescription:
    """A single-band prescription derived from an :class:`Audiogram`.

    Attributes:
        freq_hz: Centre frequency of the band.
        threshold_db_hl: Measured threshold at this frequency.
        gain_db: Insertion gain to apply (dB).
        ratio: WDRC compression ratio (>= 1.0).
        knee_dbfs: Compression knee point in dBFS.
    """

    freq_hz: int
    threshold_db_hl: float
    gain_db: float
    ratio: float
    knee_dbfs: float


@dataclass
class Prescription:
    """A bilateral prescription with one :class:`BandPrescription` per ear/freq.

    Attributes:
        right: Per-frequency prescription for the right ear.
        left: Per-frequency prescription for the left ear.
        method: Human-readable label of the prescription method used.
    """

    right: list[BandPrescription]
    left: list[BandPrescription]
    method: str = "OpenHear NAL-NL2 approximation v1"

    def gains_db(self, ear: str) -> dict[int, float]:
        """Return ``{freq_hz: gain_db}`` for the requested ear."""
        bands = self._select(ear)
        return {b.freq_hz: b.gain_db for b in bands}

    def ratios(self, ear: str) -> dict[int, float]:
        """Return ``{freq_hz: ratio}`` for the requested ear."""
        bands = self._select(ear)
        return {b.freq_hz: b.ratio for b in bands}

    def knees_dbfs(self, ear: str) -> dict[int, float]:
        """Return ``{freq_hz: knee_dbfs}`` for the requested ear."""
        bands = self._select(ear)
        return {b.freq_hz: b.knee_dbfs for b in bands}

    def _select(self, ear: str) -> list[BandPrescription]:
        if ear == "right":
            return self.right
        if ear == "left":
            return self.left
        raise ValueError(f"ear must be 'right' or 'left', got {ear!r}")


# ── Internal helpers ────────────────────────────────────────────────────────


def _interpolate_threshold(
    thresholds: dict[int, float],
    freq: int,
) -> float | None:
    """Return the threshold at *freq* using nearest/linear interpolation.

    Returns ``None`` if *thresholds* is empty.
    """
    if not thresholds:
        return None
    if freq in thresholds:
        return thresholds[freq]
    sorted_freqs = sorted(thresholds.keys())
    if freq <= sorted_freqs[0]:
        return thresholds[sorted_freqs[0]]
    if freq >= sorted_freqs[-1]:
        return thresholds[sorted_freqs[-1]]
    # Linear interpolation in log-frequency.
    import math
    lower = max(f for f in sorted_freqs if f <= freq)
    upper = min(f for f in sorted_freqs if f >= freq)
    if lower == upper:
        return thresholds[lower]
    log_freq = math.log2(freq)
    log_lo = math.log2(lower)
    log_hi = math.log2(upper)
    weight = (log_freq - log_lo) / (log_hi - log_lo)
    return (1.0 - weight) * thresholds[lower] + weight * thresholds[upper]


def _band_gain(freq: int, threshold_db_hl: float, pta_db: float) -> float:
    """Compute a single-band insertion gain (dB) using the NAL-NL2-style rule.

    The formula is a documented public approximation::

        gain = 0.31 * threshold + 0.05 * PTA  - frequency_correction

    Frequency correction reduces the prescribed gain at very low (<500 Hz)
    and very high (>4000 Hz) frequencies where insertion gain causes
    occlusion or feedback respectively.
    """
    base = _NAL_GAIN_SLOPE * threshold_db_hl + 0.05 * pta_db

    if freq < 500:
        base -= 4.0  # bass cut for occlusion control
    elif freq > 4000:
        base -= 3.0  # treble roll-off for feedback safety

    return max(_MIN_BAND_GAIN_DB, min(_MAX_BAND_GAIN_DB, round(base, 1)))


def _ratio_for(threshold_db_hl: float) -> float:
    """Pick a WDRC ratio appropriate for the threshold magnitude."""
    if threshold_db_hl <= 25:
        return 1.0  # linear — no compression needed
    if threshold_db_hl <= 40:
        return 1.5
    if threshold_db_hl <= 55:
        return 2.0
    if threshold_db_hl <= 70:
        return 2.5
    if threshold_db_hl <= 90:
        return 3.0
    return 3.5


def _knee_for(pta_db: float) -> float:
    """Pick a compression knee (dBFS) appropriate for the PTA magnitude."""
    if pta_db <= 25:
        return -30.0
    if pta_db <= 40:
        return -35.0
    if pta_db <= 55:
        return -40.0
    if pta_db <= 70:
        return -45.0
    return -50.0


def _safe_pta(thresholds: dict[int, float]) -> float:
    """PTA across 500/1000/2000/4000 Hz, falling back to mean if missing."""
    pta_freqs = (500, 1000, 2000, 4000)
    available = [thresholds[f] for f in pta_freqs if f in thresholds]
    if available:
        return sum(available) / len(available)
    if thresholds:
        return sum(thresholds.values()) / len(thresholds)
    return 0.0


def _prescribe_ear(thresholds: dict[int, float]) -> list[BandPrescription]:
    pta = _safe_pta(thresholds)
    knee = _knee_for(pta)
    bands: list[BandPrescription] = []
    for freq in PRESCRIPTION_FREQUENCIES_HZ:
        thr = _interpolate_threshold(thresholds, freq)
        if thr is None:
            continue
        bands.append(BandPrescription(
            freq_hz=freq,
            threshold_db_hl=float(thr),
            gain_db=_band_gain(freq, thr, pta),
            ratio=_ratio_for(thr),
            knee_dbfs=knee,
        ))
    return bands


# ── Public API ──────────────────────────────────────────────────────────────


def prescribe(audiogram: Audiogram) -> Prescription:
    """Build a :class:`Prescription` from an :class:`Audiogram`.

    Args:
        audiogram: A canonical :class:`audiogram.audiogram.Audiogram`.

    Returns:
        A :class:`Prescription` containing per-frequency gains and
        compression parameters for both ears.
    """
    return Prescription(
        right=_prescribe_ear(audiogram.right_ear),
        left=_prescribe_ear(audiogram.left_ear),
    )
