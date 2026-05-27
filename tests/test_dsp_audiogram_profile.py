"""Tests for :mod:`dsp.audiogram_profile`."""

from __future__ import annotations

import pytest

from audiogram.audiogram import Audiogram
from dsp.audiogram_profile import (
    PRESCRIPTION_FREQUENCIES_HZ,
    Prescription,
    prescribe,
)


def _build_ag(threshold_db_hl: float = 40.0) -> Audiogram:
    """Construct a flat audiogram at *threshold_db_hl* across both ears."""
    thresholds = {f: threshold_db_hl for f in (250, 500, 1000, 2000, 4000, 8000)}
    return Audiogram(
        right_ear=dict(thresholds), left_ear=dict(thresholds),
        date_measured="2024-11-15", source="synthetic",
    )


def test_prescribe_returns_one_band_per_prescription_frequency():
    rx = prescribe(_build_ag(40))
    assert isinstance(rx, Prescription)
    assert {b.freq_hz for b in rx.right} == set(PRESCRIPTION_FREQUENCIES_HZ)
    assert {b.freq_hz for b in rx.left} == set(PRESCRIPTION_FREQUENCIES_HZ)


def test_normal_hearing_yields_zero_or_low_gain_and_linear_ratio():
    rx = prescribe(_build_ag(15))  # all thresholds in normal-hearing range
    for band in rx.right:
        assert band.gain_db >= 0
        assert band.gain_db < 10  # near-zero
        assert band.ratio == 1.0  # linear


def test_severe_hearing_loss_yields_meaningful_gain_and_compression():
    rx = prescribe(_build_ag(75))
    for band in rx.right:
        # 75 dB HL → > 1.5 ratio per the table
        assert band.ratio >= 2.5
        # Gain should be meaningfully positive in the speech band.
        if 1000 <= band.freq_hz <= 4000:
            assert band.gain_db > 15.0


def test_per_ear_gains_dict_round_trips():
    rx = prescribe(_build_ag(40))
    gains_right = rx.gains_db("right")
    assert set(gains_right.keys()) == set(PRESCRIPTION_FREQUENCIES_HZ)
    assert all(isinstance(v, float) for v in gains_right.values())


def test_invalid_ear_label_raises():
    rx = prescribe(_build_ag(40))
    with pytest.raises(ValueError, match="ear must be"):
        rx.gains_db("centre")


def test_asymmetric_audiogram_yields_different_per_ear_prescriptions():
    ag = Audiogram(
        right_ear={f: 25 for f in (250, 500, 1000, 2000, 4000, 8000)},
        left_ear={f: 75 for f in (250, 500, 1000, 2000, 4000, 8000)},
    )
    rx = prescribe(ag)
    # Left ear has worse hearing → more gain than right at every frequency.
    for r_band, l_band in zip(rx.right, rx.left):
        assert l_band.gain_db > r_band.gain_db
        assert l_band.ratio >= r_band.ratio


def test_missing_frequencies_are_interpolated():
    """Audiogram without 6000 Hz still gets a 6000 Hz prescription via
    interpolation between 4000 and 8000."""
    ag = Audiogram(
        right_ear={500: 30, 1000: 40, 2000: 50, 4000: 60, 8000: 70},
        left_ear={500: 30, 1000: 40, 2000: 50, 4000: 60, 8000: 70},
    )
    rx = prescribe(ag)
    band_6k = next(b for b in rx.right if b.freq_hz == 6000)
    # Log-frequency interpolation between 4 kHz/60 dB and 8 kHz/70 dB
    # at 6 kHz lands ≈ 65.85 dB HL (log2(6/4)/log2(8/4) ≈ 0.585).
    assert band_6k.threshold_db_hl == pytest.approx(65.85, abs=0.5)


def test_band_gain_is_clipped_to_safety_ceiling():
    """Profound losses cap gain at the documented ceiling."""
    rx = prescribe(_build_ag(120))
    for band in rx.right:
        assert band.gain_db <= 35.0


def test_empty_ear_yields_no_bands():
    """An audiogram with one ear empty produces no prescription for that ear."""
    ag = Audiogram(
        right_ear={500: 30, 1000: 40, 2000: 50, 4000: 60},
        left_ear={},
    )
    rx = prescribe(ag)
    assert rx.right  # populated
    assert rx.left == []
