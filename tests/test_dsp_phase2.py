"""Tests for :mod:`dsp.beamforming` and :mod:`dsp.metrics` and :mod:`dsp.noise`."""

from __future__ import annotations

import csv

import numpy as np
import pytest

from dsp.beamforming import (
    DelaySumBeamformer,
    MicrophoneArray,
    MvdrBeamformer,
    mono_passthrough,
)
from dsp.metrics import MetricsLogger, format_dashboard_line
from dsp.noise import SpectralSubtractor, VoiceActivityDetector


# ── beamforming ────────────────────────────────────────────────────────────


def test_mono_passthrough_returns_same_data():
    x = np.array([0.1, 0.2, -0.3, 0.4], dtype=np.float32)
    out = mono_passthrough(x)
    np.testing.assert_array_equal(out, x)


def test_mono_passthrough_handles_single_row_2d():
    x = np.array([[0.1, 0.2, 0.3]], dtype=np.float32)
    out = mono_passthrough(x)
    np.testing.assert_array_equal(out, x[0])


def test_mono_passthrough_rejects_multi_channel():
    x = np.zeros((2, 4), dtype=np.float32)
    with pytest.raises(ValueError):
        mono_passthrough(x)


def test_delay_sum_passthrough_for_mono_input():
    array = MicrophoneArray(positions_m=(0.0, 0.014), sample_rate=16_000)
    bf = DelaySumBeamformer(array)
    x = np.random.randn(1024).astype(np.float32)
    out = bf.process(x)
    np.testing.assert_array_equal(out, x)


def test_delay_sum_with_two_channels_averages_aligned_signal():
    """When both channels carry the same signal aligned with the array
    front, delay-and-sum reproduces the source attenuated by 0 dB
    (perfect coherent sum / number of channels)."""
    array = MicrophoneArray(positions_m=(0.0, 0.014), sample_rate=16_000)
    bf = DelaySumBeamformer(array, direction_deg=90.0)  # broadside
    x = np.sin(2 * np.pi * 1000 * np.arange(2048) / 16_000).astype(np.float32)
    channels = np.vstack([x, x])
    out = bf.process(channels)
    # Same length, similar amplitude (averaging two identical channels = same).
    assert out.shape == x.shape
    np.testing.assert_allclose(np.abs(out).mean(), np.abs(x).mean(), rtol=0.1)


def test_delay_sum_rejects_wrong_channel_count():
    array = MicrophoneArray(positions_m=(0.0, 0.014), sample_rate=16_000)
    bf = DelaySumBeamformer(array)
    bad = np.zeros((3, 1024), dtype=np.float32)
    with pytest.raises(ValueError, match="rows but array has"):
        bf.process(bad)


def test_mvdr_falls_back_to_delay_sum_with_warning(caplog):
    import logging
    array = MicrophoneArray(positions_m=(0.0, 0.014), sample_rate=16_000)
    bf = MvdrBeamformer(array)
    x = np.zeros(64, dtype=np.float32)
    with caplog.at_level(logging.WARNING, logger="dsp.beamforming"):
        bf.process(x)
    assert any("stub" in rec.message for rec in caplog.records)


# ── metrics ────────────────────────────────────────────────────────────────


def test_metrics_logger_writes_csv_with_header(tmp_path):
    out = tmp_path / "metrics.csv"
    block = np.full(256, 0.1, dtype=np.float32)
    with MetricsLogger(path=out, keep_in_memory=True) as ml:
        for _ in range(3):
            ml.log_block(
                block_samples=256, sample_rate=16_000,
                process_seconds=0.005, samples=block,
            )
    rows = list(csv.reader(out.open("r")))
    assert rows[0] == list(MetricsLogger.HEADER)
    assert len(rows) == 1 + 3
    assert all(len(r) == 6 for r in rows[1:])


def test_metrics_logger_computes_latency_and_rms(tmp_path):
    out = tmp_path / "m.csv"
    block = np.full(256, 0.5, dtype=np.float32)  # ≈ -6 dBFS RMS
    with MetricsLogger(path=out, keep_in_memory=True) as ml:
        row = ml.log_block(
            block_samples=256, sample_rate=16_000,
            process_seconds=0.008, samples=block,
        )
    # latency = 256/16000 s = 16 ms.
    assert row.latency_ms == pytest.approx(16.0, abs=0.1)
    # cpu = 8 ms / 16 ms = 0.5
    assert row.cpu_percent == pytest.approx(0.5, abs=0.001)
    assert row.rms_dbfs == pytest.approx(-6.0, abs=0.5)


def test_metrics_logger_log_block_before_open_raises(tmp_path):
    ml = MetricsLogger(path=tmp_path / "m.csv")
    with pytest.raises(RuntimeError, match="before open"):
        ml.log_block(
            block_samples=128, sample_rate=16_000,
            process_seconds=0.001, samples=np.zeros(128, dtype=np.float32),
        )


def test_metrics_logger_validates_inputs(tmp_path):
    ml = MetricsLogger(path=tmp_path / "m.csv").open()
    try:
        with pytest.raises(ValueError, match="sample_rate must be positive"):
            ml.log_block(
                block_samples=128, sample_rate=0,
                process_seconds=0.001, samples=np.zeros(128, dtype=np.float32),
            )
        with pytest.raises(ValueError, match="block_samples must be positive"):
            ml.log_block(
                block_samples=0, sample_rate=16_000,
                process_seconds=0.001, samples=np.zeros(128, dtype=np.float32),
            )
    finally:
        ml.close()


def test_format_dashboard_line_includes_key_fields(tmp_path):
    block = np.full(256, 0.1, dtype=np.float32)
    with MetricsLogger(path=tmp_path / "m.csv", keep_in_memory=True) as ml:
        row = ml.log_block(
            block_samples=256, sample_rate=16_000,
            process_seconds=0.004, samples=block,
        )
    line = format_dashboard_line(row)
    assert "latency=" in line
    assert "CPU=" in line
    assert "level=" in line


# ── noise / VAD ────────────────────────────────────────────────────────────


def test_noise_module_re_exports_spectral_subtractor():
    """Backwards-compat: the canonical module name still exposes the class."""
    from dsp import noise_reduction
    assert SpectralSubtractor is noise_reduction.SpectralSubtractor


def test_vad_detects_loud_speech_after_quiet_warmup():
    vad = VoiceActivityDetector(sample_rate=16_000, threshold_db=9.0)
    quiet = np.random.randn(4096).astype(np.float32) * 0.001
    # Adapt floor over several quiet blocks.
    for _ in range(20):
        assert not vad.is_speech(quiet)
    # A loud sine block should be flagged as speech.
    loud_sine = np.sin(2 * np.pi * 500 * np.arange(4096) / 16_000).astype(np.float32) * 0.2
    assert vad.is_speech(loud_sine)


def test_vad_rejects_high_zcr_wideband_noise():
    vad = VoiceActivityDetector(sample_rate=16_000, threshold_db=3.0, max_zcr=0.3)
    quiet = np.random.randn(4096).astype(np.float32) * 0.001
    for _ in range(20):
        vad.is_speech(quiet)
    # White noise has very high ZCR even when loud → rejected.
    rng = np.random.default_rng(0)
    loud_noise = rng.standard_normal(4096).astype(np.float32) * 0.3
    assert not vad.is_speech(loud_noise)


def test_vad_validates_constructor_args():
    with pytest.raises(ValueError, match="sample_rate"):
        VoiceActivityDetector(sample_rate=0)
    with pytest.raises(ValueError, match="adapt_seconds"):
        VoiceActivityDetector(sample_rate=16_000, adapt_seconds=0)
