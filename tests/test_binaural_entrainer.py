"""Tests for :mod:`dsp.stages.binaural_entrainer`."""

from __future__ import annotations

import logging

import numpy as np
import pytest

from dsp.audiogram_profile import BandPrescription, Prescription
from dsp.stages.binaural_entrainer import BinauralEntrainer


def _render(stage: BinauralEntrainer, seconds: float, sample_rate: int = 16_000) -> np.ndarray:
    block = 256
    total = int(seconds * sample_rate)
    out = []
    pos = 0
    while pos < total:
        n = min(block, total - pos)
        out.append(stage.process(np.zeros(n, dtype=np.float32)))
        pos += n
    return np.vstack(out)


def _peak_frequency(samples: np.ndarray, sample_rate: int) -> float:
    windowed = samples * np.hanning(samples.shape[0])
    spectrum = np.fft.rfft(windowed)
    freqs = np.fft.rfftfreq(samples.shape[0], d=1.0 / sample_rate)
    return float(freqs[int(np.argmax(np.abs(spectrum)))])


def _rx(left_gain: float, right_gain: float) -> Prescription:
    left = [
        BandPrescription(
            freq_hz=250,
            threshold_db_hl=60.0,
            gain_db=left_gain,
            ratio=2.0,
            knee_dbfs=-40.0,
        ),
        BandPrescription(
            freq_hz=500,
            threshold_db_hl=60.0,
            gain_db=left_gain,
            ratio=2.0,
            knee_dbfs=-40.0,
        ),
    ]
    right = [
        BandPrescription(
            freq_hz=250,
            threshold_db_hl=20.0,
            gain_db=right_gain,
            ratio=1.0,
            knee_dbfs=-30.0,
        ),
        BandPrescription(
            freq_hz=500,
            threshold_db_hl=20.0,
            gain_db=right_gain,
            ratio=1.0,
            knee_dbfs=-30.0,
        ),
    ]
    return Prescription(right=right, left=left)


def test_beat_frequency_accuracy_in_output(caplog):
    stage = BinauralEntrainer(
        sample_rate=16_000,
        beat_hz=6.0,
        carrier_hz=300.0,
        ramp_ms=0.0,
        mask_type="none",
    )

    with caplog.at_level(logging.WARNING, logger="dsp.stages.binaural_entrainer"):
        out = _render(stage, seconds=1.0)

    left_peak = _peak_frequency(out[:, 0], 16_000)
    right_peak = _peak_frequency(out[:, 1], 16_000)
    assert right_peak - left_peak == pytest.approx(6.0, abs=0.25)
    assert any("Experimental feature" in record.message for record in caplog.records)


def test_hard_limiter_never_exceeds_point_seven():
    stage = BinauralEntrainer(ramp_ms=0.0, mask_type="none")
    loud = np.ones(512, dtype=np.float32) * 2.0
    out = stage.process(loud)
    assert out.shape == (512, 2)
    assert float(np.max(np.abs(out))) <= 0.7 + 1e-6


def test_audiogram_compensation_scales_per_ear_output():
    stage = BinauralEntrainer(
        sample_rate=16_000,
        beat_hz=6.0,
        carrier_hz=300.0,
        ramp_ms=0.0,
        mask_type="none",
        prescription=_rx(left_gain=12.0, right_gain=0.0),
    )
    out = _render(stage, seconds=0.5)
    left_rms = float(np.sqrt(np.mean(out[:, 0] ** 2)))
    right_rms = float(np.sqrt(np.mean(out[:, 1] ** 2)))
    assert left_rms > right_rms * 2.0


def test_rejects_out_of_range_session_parameters():
    with pytest.raises(ValueError, match="beat_hz"):
        BinauralEntrainer(beat_hz=2.0)
    with pytest.raises(ValueError, match="carrier_hz"):
        BinauralEntrainer(carrier_hz=900.0)
    with pytest.raises(ValueError, match="mask_type"):
        BinauralEntrainer(mask_type="cloud")


def test_own_voice_bypass_disables_generation_but_keeps_safety_limit():
    stage = BinauralEntrainer(ramp_ms=0.0, mask_type="none", own_voice_bypass=True)
    out = stage.process(np.zeros(256, dtype=np.float32))
    assert out.shape == (256, 2)
    np.testing.assert_allclose(out, 0.0)
