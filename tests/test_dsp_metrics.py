"""Tests for ``dsp/metrics.py``."""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import pytest

from dsp.metrics import MetricsLogger, MetricsRow, format_dashboard_line

SR = 16_000
BLOCK = 256


def _make_logger(tmp_path: Path, **kwargs) -> MetricsLogger:
    return MetricsLogger(path=tmp_path / "metrics.csv", **kwargs)


class TestMetricsLoggerOpen:
    def test_open_returns_self(self, tmp_path):
        ml = _make_logger(tmp_path)
        result = ml.open()
        try:
            assert result is ml
        finally:
            ml.close()

    def test_open_creates_file_with_header(self, tmp_path):
        ml = _make_logger(tmp_path)
        with ml:
            pass
        content = ml.path.read_text()
        assert content.startswith("timestamp")

    def test_open_idempotent(self, tmp_path):
        ml = _make_logger(tmp_path)
        ml.open()
        try:
            ml.open()  # second call must not raise
        finally:
            ml.close()

    def test_close_idempotent(self, tmp_path):
        ml = _make_logger(tmp_path)
        ml.open()
        ml.close()
        ml.close()  # second close must not raise


class TestMetricsLoggerLogBlock:
    def test_log_block_returns_row(self, tmp_path):
        with _make_logger(tmp_path) as ml:
            row = ml.log_block(
                block_samples=BLOCK,
                sample_rate=SR,
                process_seconds=0.005,
                samples=np.zeros(BLOCK, dtype=np.float32),
                timestamp=1000.0,
            )
        assert isinstance(row, MetricsRow)
        assert row.timestamp == pytest.approx(1000.0)

    def test_latency_is_block_duration_ms(self, tmp_path):
        with _make_logger(tmp_path) as ml:
            row = ml.log_block(
                block_samples=BLOCK,
                sample_rate=SR,
                process_seconds=0.001,
                samples=np.zeros(BLOCK, dtype=np.float32),
                timestamp=0.0,
            )
        expected_ms = (BLOCK / SR) * 1000.0
        assert row.latency_ms == pytest.approx(expected_ms)

    def test_extra_latency_added(self, tmp_path):
        with _make_logger(tmp_path) as ml:
            row = ml.log_block(
                block_samples=BLOCK,
                sample_rate=SR,
                process_seconds=0.001,
                samples=np.zeros(BLOCK, dtype=np.float32),
                extra_latency_ms=5.0,
                timestamp=0.0,
            )
        expected_ms = (BLOCK / SR) * 1000.0 + 5.0
        assert row.latency_ms == pytest.approx(expected_ms)

    def test_cpu_percent_computed(self, tmp_path):
        with _make_logger(tmp_path) as ml:
            row = ml.log_block(
                block_samples=BLOCK,
                sample_rate=SR,
                process_seconds=0.008,
                samples=np.zeros(BLOCK, dtype=np.float32),
                timestamp=0.0,
            )
        block_secs = BLOCK / SR
        assert row.cpu_percent == pytest.approx(0.008 / block_secs, rel=1e-5)

    def test_rms_dbfs_silence(self, tmp_path):
        with _make_logger(tmp_path) as ml:
            row = ml.log_block(
                block_samples=BLOCK,
                sample_rate=SR,
                process_seconds=0.001,
                samples=np.zeros(BLOCK, dtype=np.float32),
                timestamp=0.0,
            )
        # Near-silence gives very negative dBFS (dominated by epsilon)
        assert row.rms_dbfs < -100.0

    def test_rms_dbfs_full_scale(self, tmp_path):
        with _make_logger(tmp_path) as ml:
            row = ml.log_block(
                block_samples=BLOCK,
                sample_rate=SR,
                process_seconds=0.001,
                samples=np.ones(BLOCK, dtype=np.float32),
                timestamp=0.0,
            )
        assert row.rms_dbfs == pytest.approx(0.0, abs=0.01)

    def test_csv_row_written(self, tmp_path):
        with _make_logger(tmp_path) as ml:
            ml.log_block(
                block_samples=BLOCK,
                sample_rate=SR,
                process_seconds=0.001,
                samples=np.zeros(BLOCK, dtype=np.float32),
                timestamp=42.0,
            )
        content = ml.path.read_text()
        assert "42.000000" in content

    def test_keep_in_memory(self, tmp_path):
        ml = MetricsLogger(path=tmp_path / "m.csv", keep_in_memory=True)
        with ml:
            ml.log_block(
                block_samples=BLOCK,
                sample_rate=SR,
                process_seconds=0.001,
                samples=np.zeros(BLOCK, dtype=np.float32),
                timestamp=1.0,
            )
            ml.log_block(
                block_samples=BLOCK,
                sample_rate=SR,
                process_seconds=0.001,
                samples=np.zeros(BLOCK, dtype=np.float32),
                timestamp=2.0,
            )
        assert len(ml.rows) == 2
        assert ml.rows[0].timestamp == pytest.approx(1.0)
        assert ml.rows[1].timestamp == pytest.approx(2.0)

    def test_log_before_open_raises(self, tmp_path):
        ml = _make_logger(tmp_path)
        with pytest.raises(RuntimeError, match="open"):
            ml.log_block(
                block_samples=BLOCK,
                sample_rate=SR,
                process_seconds=0.001,
                samples=np.zeros(BLOCK, dtype=np.float32),
            )

    def test_invalid_sample_rate_raises(self, tmp_path):
        with _make_logger(tmp_path) as ml:
            with pytest.raises(ValueError, match="sample_rate"):
                ml.log_block(
                    block_samples=BLOCK,
                    sample_rate=0,
                    process_seconds=0.001,
                    samples=np.zeros(BLOCK, dtype=np.float32),
                )

    def test_invalid_block_samples_raises(self, tmp_path):
        with _make_logger(tmp_path) as ml:
            with pytest.raises(ValueError, match="block_samples"):
                ml.log_block(
                    block_samples=0,
                    sample_rate=SR,
                    process_seconds=0.001,
                    samples=np.zeros(BLOCK, dtype=np.float32),
                )

    def test_parents_created_automatically(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c" / "metrics.csv"
        ml = MetricsLogger(path=nested)
        with ml:
            ml.log_block(
                block_samples=BLOCK,
                sample_rate=SR,
                process_seconds=0.001,
                samples=np.zeros(BLOCK, dtype=np.float32),
                timestamp=0.0,
            )
        assert nested.exists()

    def test_timestamp_uses_time_if_not_provided(self, tmp_path):
        import time

        before = time.time()
        with _make_logger(tmp_path) as ml:
            row = ml.log_block(
                block_samples=BLOCK,
                sample_rate=SR,
                process_seconds=0.001,
                samples=np.zeros(BLOCK, dtype=np.float32),
            )
        after = time.time()
        assert before <= row.timestamp <= after


class TestFormatDashboardLine:
    def test_contains_expected_fields(self):
        row = MetricsRow(
            timestamp=0.0,
            block_seconds=0.016,
            process_seconds=0.005,
            latency_ms=16.0,
            cpu_percent=0.3125,
            rms_dbfs=-20.0,
        )
        line = format_dashboard_line(row)
        assert "latency=" in line
        assert "16.00" in line
        assert "CPU=" in line
        assert "31.2" in line
        assert "level=" in line
        assert "-20" in line
