"""Tests for ``stream/crowd_arousal.py`` — continuous crowd-energy estimation."""

from __future__ import annotations

import numpy as np
import pytest

from stream.crowd_arousal import (
    _ONSET_HISTORY_S,
    _ONSET_THRESHOLD,
    ArousalEstimate,
    CrowdArousalEstimator,
)
from stream.haptic_primitive import HapticPrimitive

# ── ArousalEstimate ──────────────────────────────────────────────────────────


def test_arousal_estimate_is_dataclass():
    est = ArousalEstimate(arousal=0.5, tension=0.3, onset_rate_hz=2.0)
    assert est.arousal == 0.5
    assert est.tension == 0.3
    assert est.onset_rate_hz == 2.0


def test_arousal_estimate_is_frozen():
    est = ArousalEstimate(arousal=0.5, tension=0.3, onset_rate_hz=2.0)
    with pytest.raises((AttributeError, TypeError)):
        est.arousal = 0.9  # type: ignore[misc]


# ── CrowdArousalEstimator construction ───────────────────────────────────────


def test_invalid_sample_rate_raises():
    with pytest.raises(ValueError, match="sample_rate"):
        CrowdArousalEstimator(sample_rate=0)


def test_invalid_frame_size_raises():
    with pytest.raises(ValueError, match="frame_size"):
        CrowdArousalEstimator(frame_size=-1)


# ── update: shape validation ──────────────────────────────────────────────────


def test_2d_frame_raises():
    est = CrowdArousalEstimator()
    with pytest.raises(ValueError, match="1-D"):
        est.update(np.zeros((2, 2048)))


# ── update: arousal dimension ─────────────────────────────────────────────────


def test_silence_gives_zero_arousal():
    est = CrowdArousalEstimator(frame_size=2048)
    frame = np.zeros(2048, dtype=np.float32)
    result = est.update(frame)
    assert result.arousal == pytest.approx(0.0)


def test_loud_frame_gives_positive_arousal():
    est = CrowdArousalEstimator(frame_size=2048)
    frame = np.random.default_rng(42).uniform(-0.5, 0.5, 2048).astype(np.float64)
    result = est.update(frame)
    assert result.arousal > 0.0


def test_loud_frame_has_higher_arousal_than_quiet_frame():
    est_loud = CrowdArousalEstimator(frame_size=2048)
    est_quiet = CrowdArousalEstimator(frame_size=2048)
    rng = np.random.default_rng(0)
    loud = rng.uniform(-0.5, 0.5, 2048).astype(np.float64)
    quiet = rng.uniform(-0.01, 0.01, 2048).astype(np.float64)
    arousal_loud = est_loud.update(loud).arousal
    arousal_quiet = est_quiet.update(quiet).arousal
    assert arousal_loud > arousal_quiet


def test_arousal_in_unit_range():
    est = CrowdArousalEstimator(frame_size=2048)
    for amplitude in [0.0, 0.001, 0.01, 0.1, 1.0]:
        frame = np.full(2048, amplitude, dtype=np.float64)
        result = est.update(frame)
        assert 0.0 <= result.arousal <= 1.0, f"arousal out of range for amplitude {amplitude}"
        est.reset()


# ── update: tension dimension ─────────────────────────────────────────────────


def test_first_frame_tension_is_zero():
    """First frame has no previous spectrum to compare against."""
    est = CrowdArousalEstimator(frame_size=2048)
    frame = np.ones(2048, dtype=np.float64)
    result = est.update(frame)
    assert result.tension == pytest.approx(0.0)


def test_identical_frames_give_low_tension():
    """Unchanging audio → no spectral flux → near-zero tension."""
    est = CrowdArousalEstimator(frame_size=2048)
    frame = np.ones(2048, dtype=np.float64) * 0.1
    est.update(frame)  # prime prev_spectrum
    result = est.update(frame)  # identical — no positive flux
    assert result.tension == pytest.approx(0.0)


def test_different_frames_give_nonzero_tension():
    """Very different consecutive frames → high spectral flux → higher tension."""
    est = CrowdArousalEstimator(frame_size=2048)
    rng = np.random.default_rng(7)
    frame_a = rng.uniform(-1.0, 1.0, 2048).astype(np.float64)
    frame_b = rng.uniform(-1.0, 1.0, 2048).astype(np.float64)
    est.update(frame_a)
    result = est.update(frame_b)
    assert result.tension > 0.0


def test_tension_in_unit_range():
    est = CrowdArousalEstimator(frame_size=2048)
    rng = np.random.default_rng(13)
    for _ in range(10):
        frame = rng.uniform(-1.0, 1.0, 2048).astype(np.float64)
        result = est.update(frame)
        assert 0.0 <= result.tension <= 1.0


# ── update: onset detection ───────────────────────────────────────────────────


def test_steady_tone_gives_zero_onset_rate():
    """A steady signal with no amplitude rise should have no onsets."""
    est = CrowdArousalEstimator(frame_size=2048, sample_rate=44_100)
    frame = np.ones(2048, dtype=np.float64) * 0.05
    for _ in range(20):
        est.update(frame)
    result = est.update(frame)
    assert result.onset_rate_hz == pytest.approx(0.0)


def test_amplitude_spike_increases_onset_count():
    """A sudden RMS jump should register as an onset."""
    est = CrowdArousalEstimator(frame_size=2048, sample_rate=44_100)
    quiet = np.ones(2048, dtype=np.float64) * 0.01
    loud = np.ones(2048, dtype=np.float64) * 0.3  # ~30× rise, well above threshold

    est.update(quiet)   # prime prev_rms
    result = est.update(loud)   # onset should fire here
    # onset_rate_hz is over a 2 s window; 1 onset in 2 s = 0.5 Hz
    assert result.onset_rate_hz > 0.0


# ── reset ─────────────────────────────────────────────────────────────────────


def test_reset_clears_tension():
    """After reset, the next frame should behave as if it is the first."""
    est = CrowdArousalEstimator(frame_size=2048)
    rng = np.random.default_rng(99)
    frame_a = rng.uniform(-1.0, 1.0, 2048).astype(np.float64)
    frame_b = rng.uniform(-1.0, 1.0, 2048).astype(np.float64)
    est.update(frame_a)
    est.reset()
    result = est.update(frame_b)
    # After reset, no prev_spectrum — tension must be 0
    assert result.tension == pytest.approx(0.0)


def test_reset_clears_onset_history():
    est = CrowdArousalEstimator(frame_size=2048, sample_rate=44_100)
    quiet = np.ones(2048, dtype=np.float64) * 0.01
    loud = np.ones(2048, dtype=np.float64) * 0.3
    est.update(quiet)
    est.update(loud)  # registers an onset
    est.reset()
    # After reset, onset queue is cleared
    result = est.update(quiet)
    assert result.onset_rate_hz == pytest.approx(0.0)


# ── to_primitive ──────────────────────────────────────────────────────────────


def test_to_primitive_returns_haptic_primitive():
    est = CrowdArousalEstimator()
    e = ArousalEstimate(arousal=0.5, tension=0.5, onset_rate_hz=2.0)
    p = est.to_primitive(e)
    assert isinstance(p, HapticPrimitive)


def test_to_primitive_spatial_balance_is_zero():
    """Crowd energy is omnidirectional — primitive must be centred."""
    est = CrowdArousalEstimator()
    e = ArousalEstimate(arousal=0.5, tension=0.5, onset_rate_hz=2.0)
    p = est.to_primitive(e)
    assert p.spatial_balance == pytest.approx(0.0)


def test_to_primitive_high_arousal_stronger_than_low():
    est = CrowdArousalEstimator()
    low = ArousalEstimate(arousal=0.0, tension=0.5, onset_rate_hz=0.0)
    high = ArousalEstimate(arousal=1.0, tension=0.5, onset_rate_hz=0.0)
    assert est.to_primitive(high).intensity > est.to_primitive(low).intensity


def test_to_primitive_high_tension_faster_than_low():
    est = CrowdArousalEstimator()
    low = ArousalEstimate(arousal=0.5, tension=0.0, onset_rate_hz=0.0)
    high = ArousalEstimate(arousal=0.5, tension=1.0, onset_rate_hz=0.0)
    assert est.to_primitive(high).pulse_rate_hz > est.to_primitive(low).pulse_rate_hz


def test_to_primitive_all_extreme_estimates_produce_valid_primitives():
    """Boundary estimates must produce valid HapticPrimitive without raising."""
    est = CrowdArousalEstimator()
    for arousal in [0.0, 1.0]:
        for tension in [0.0, 1.0]:
            e = ArousalEstimate(arousal=arousal, tension=tension, onset_rate_hz=0.0)
            p = est.to_primitive(e)
            assert isinstance(p, HapticPrimitive)  # __post_init__ validates


def test_to_primitive_intensity_within_configured_range():
    from stream.crowd_arousal import _MAX_INTENSITY, _MIN_INTENSITY

    est = CrowdArousalEstimator()
    for arousal in [0.0, 0.25, 0.5, 0.75, 1.0]:
        e = ArousalEstimate(arousal=arousal, tension=0.5, onset_rate_hz=0.0)
        p = est.to_primitive(e)
        assert _MIN_INTENSITY <= p.intensity <= _MAX_INTENSITY


# ── Integration: update → to_primitive ───────────────────────────────────────


def test_full_pipeline_loud_crowd_maps_to_strong_fast_primitive():
    """Loud, rapidly-changing audio should produce high-intensity, fast primitive."""
    est = CrowdArousalEstimator(frame_size=2048, sample_rate=44_100)
    rng = np.random.default_rng(2024)
    # Feed several frames of loud varied noise (simulate cheering crowd)
    prev = rng.uniform(-1.0, 1.0, 2048).astype(np.float64)
    for _ in range(5):
        curr = rng.uniform(-1.0, 1.0, 2048).astype(np.float64)
        est.update(prev)
        prev = curr
    result = est.update(prev)
    p = est.to_primitive(result)
    # Loud crowd → arousal > 0.5 → intensity well above minimum
    assert p.intensity > 80
    # Rapidly-changing → tension > 0 → rate above minimum
    assert p.pulse_rate_hz > 1.0


def test_full_pipeline_silence_maps_to_minimum_intensity():
    """Silence should map to the minimum configured intensity."""
    from stream.crowd_arousal import _MIN_INTENSITY

    est = CrowdArousalEstimator(frame_size=2048, sample_rate=44_100)
    frame = np.zeros(2048, dtype=np.float64)
    result = est.update(frame)
    p = est.to_primitive(result)
    assert p.intensity == _MIN_INTENSITY
