"""Tests for :mod:`dsp.filters`."""

from __future__ import annotations

import math

import numpy as np
import pytest

from dsp.filters import (
    Biquad,
    BiquadCoeffs,
    FilterBank,
    anti_feedback_notch,
    bandpass,
    high_shelf,
    low_shelf,
    notch,
    peaking_eq,
    voice_bandpass,
)

SR = 16_000


def _sine(freq_hz: float, n: int = 4096, sr: int = SR, amp: float = 0.5) -> np.ndarray:
    t = np.arange(n) / sr
    return (amp * np.sin(2 * math.pi * freq_hz * t)).astype(np.float32)


def _rms_db(samples: np.ndarray) -> float:
    rms = math.sqrt(float(np.mean(samples * samples)) + 1e-20)
    return 20.0 * math.log10(rms)


def test_peaking_eq_boosts_at_centre_frequency():
    coeffs = peaking_eq(2_000.0, gain_db=12.0, q=2.0, sample_rate=SR)
    eq = Biquad(coeffs)
    x = _sine(2_000.0)
    eq.process(x[:512])  # warm up
    eq.reset()
    y = eq.process(x)
    delta = _rms_db(y) - _rms_db(x)
    # 12 dB target ± 1 dB tolerance.
    assert 11.0 < delta < 13.0


def test_peaking_eq_cuts_at_centre_frequency():
    coeffs = peaking_eq(2_000.0, gain_db=-12.0, q=2.0, sample_rate=SR)
    eq = Biquad(coeffs)
    x = _sine(2_000.0)
    y = eq.process(x)
    delta = _rms_db(y) - _rms_db(x)
    assert -13.5 < delta < -10.5


def test_peaking_eq_leaves_far_frequencies_alone():
    coeffs = peaking_eq(2_000.0, gain_db=12.0, q=4.0, sample_rate=SR)
    eq = Biquad(coeffs)
    x = _sine(200.0)  # well below centre
    y = eq.process(x)
    delta = _rms_db(y) - _rms_db(x)
    assert abs(delta) < 1.0


def test_low_shelf_boost_low_frequency():
    coeffs = low_shelf(500.0, gain_db=10.0, slope=1.0, sample_rate=SR)
    sh = Biquad(coeffs)
    x = _sine(100.0)
    y = sh.process(x)
    assert _rms_db(y) - _rms_db(x) > 7.0


def test_high_shelf_boost_high_frequency():
    coeffs = high_shelf(2_000.0, gain_db=10.0, slope=1.0, sample_rate=SR)
    sh = Biquad(coeffs)
    x = _sine(6_000.0)
    y = sh.process(x)
    assert _rms_db(y) - _rms_db(x) > 7.0


def test_notch_attenuates_at_centre():
    coeffs = notch(1_000.0, q=20.0, sample_rate=SR)
    f = Biquad(coeffs)
    x = _sine(1_000.0)
    f.process(x[:1024])  # warm up
    f.reset()
    y = f.process(x)
    assert _rms_db(y) - _rms_db(x) < -10.0


def test_bandpass_passes_centre_attenuates_edges():
    bp = Biquad(bandpass(2_000.0, q=2.0, sample_rate=SR))
    centre = bp.process(_sine(2_000.0))
    bp.reset()
    edge = bp.process(_sine(200.0))
    assert _rms_db(centre) > _rms_db(edge) + 6.0


def test_voice_bandpass_centred_in_speech_band():
    f = voice_bandpass(SR, low_hz=1_000.0, high_hz=4_000.0)
    speech = f.process(_sine(2_000.0))
    f.reset()
    bass = f.process(_sine(200.0))
    assert _rms_db(speech) > _rms_db(bass)


def test_anti_feedback_notch_attenuates_target_freq():
    f = anti_feedback_notch(3_500.0, sample_rate=SR, q=30.0)
    on_target = f.process(_sine(3_500.0))
    f.reset()
    off_target = f.process(_sine(500.0))
    assert _rms_db(on_target) < _rms_db(off_target) - 5.0


def test_filter_bank_applies_filters_in_order():
    f1 = Biquad(peaking_eq(1_000.0, 6.0, 2.0, SR))
    f2 = Biquad(peaking_eq(1_000.0, 6.0, 2.0, SR))
    bank = FilterBank([f1, f2])
    x = _sine(1_000.0)
    y = bank.process(x)
    # Two cascaded +6 dB peaks ≈ +12 dB at the centre.
    delta = _rms_db(y) - _rms_db(x)
    assert 9.0 < delta < 14.0


def test_filter_bank_reset_clears_state():
    f = Biquad(peaking_eq(1_000.0, 6.0, 2.0, SR))
    bank = FilterBank([f])
    bank.process(_sine(1_000.0))
    bank.reset()
    # After reset, state vars should be back to zero.
    assert f._x1 == 0.0
    assert f._y1 == 0.0


def test_invalid_q_rejected():
    with pytest.raises(ValueError, match="Q must be positive"):
        peaking_eq(1_000.0, 0.0, q=-1.0, sample_rate=SR)
    with pytest.raises(ValueError, match="Q must be positive"):
        notch(1_000.0, q=0.0, sample_rate=SR)


def test_invalid_freq_rejected():
    with pytest.raises(ValueError, match="freq_hz"):
        peaking_eq(SR, 0.0, 1.0, sample_rate=SR)  # at Nyquist


def test_invalid_sample_rate_rejected():
    with pytest.raises(ValueError, match="sample_rate"):
        peaking_eq(1_000.0, 0.0, 1.0, sample_rate=0)


def test_biquad_coeffs_normalised_by_a0():
    c = BiquadCoeffs.from_unnormalised(2.0, 0.0, 0.0, 4.0, 0.0, 0.0)
    assert c.b0 == 0.5  # 2.0 / 4.0


def test_biquad_coeffs_a0_zero_rejected():
    with pytest.raises(ValueError, match="a0 must be non-zero"):
        BiquadCoeffs.from_unnormalised(1, 1, 1, 0, 1, 1)


def test_biquad_state_persists_across_blocks():
    """Splitting a sine into two halves should produce the same output as
    processing it whole, modulo numeric noise."""
    f1 = Biquad(peaking_eq(1_000.0, 6.0, 2.0, SR))
    x = _sine(1_000.0, n=2048)
    full = f1.process(x)

    f2 = Biquad(peaking_eq(1_000.0, 6.0, 2.0, SR))
    halves = np.concatenate([f2.process(x[:1024]), f2.process(x[1024:])])

    np.testing.assert_allclose(full, halves, atol=1e-5)
