"""
metrics.py – runtime metrics logging for the OpenHear DSP pipeline.

Continuously records per-block statistics (latency, CPU usage, signal
level) to a CSV file so users can verify that the pipeline meets its
20 ms latency budget and stays within CPU headroom on their hardware.

The logger is intentionally minimal: it just appends rows to a
configurable CSV path.  An optional in-process buffer lets tests inspect
captured rows without touching the filesystem.

The companion :func:`format_dashboard_line` helper formats a single
row as a one-line terminal status string (used by ``dsp.pipeline``
when ``--metrics-dashboard`` is enabled).
"""

from __future__ import annotations

import csv
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MetricsRow:
    """One sampled metric row.

    Attributes:
        timestamp: Wall-clock UNIX time the block finished processing.
        block_seconds: Duration of audio represented by the block.
        process_seconds: Wall-clock seconds the DSP chain spent on the block.
        latency_ms: Estimated end-to-end latency in milliseconds.
        cpu_percent: Fraction (0.0–1.0+) of real-time consumed by the
            DSP chain on this block.  Above 1.0 means the pipeline is
            slower than real time.
        rms_dbfs: Block RMS in dBFS (``-120`` for silence).
    """

    timestamp: float
    block_seconds: float
    process_seconds: float
    latency_ms: float
    cpu_percent: float
    rms_dbfs: float


@dataclass
class MetricsLogger:
    """Append per-block metrics to a CSV file (and optionally to memory).

    Args:
        path: Output CSV path.  Parent directories are created on open.
        keep_in_memory: If ``True``, every row is also retained on
            ``self.rows`` for tests/inspection.
    """

    path: Path
    keep_in_memory: bool = False
    rows: list[MetricsRow] = field(default_factory=list)
    _file: IO | None = field(default=None, init=False, repr=False)
    _writer: csv.writer | None = field(default=None, init=False, repr=False)

    HEADER: tuple[str, ...] = (
        "timestamp", "block_seconds", "process_seconds",
        "latency_ms", "cpu_percent", "rms_dbfs",
    )

    def __post_init__(self) -> None:
        self.path = Path(self.path)

    def open(self) -> "MetricsLogger":
        """Open the CSV file and write the header row."""
        if self._file is not None:
            return self
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.path, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(self.HEADER)
        self._file.flush()
        return self

    def close(self) -> None:
        """Flush and close the underlying file (idempotent)."""
        if self._file is not None:
            self._file.flush()
            self._file.close()
            self._file = None
            self._writer = None

    def __enter__(self) -> "MetricsLogger":
        return self.open()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def log_block(
        self,
        *,
        block_samples: int,
        sample_rate: int,
        process_seconds: float,
        samples: np.ndarray,
        extra_latency_ms: float = 0.0,
        timestamp: float | None = None,
    ) -> MetricsRow:
        """Compute and write one metrics row for a freshly processed block.

        Args:
            block_samples: Number of samples in the block.
            sample_rate: Sample rate in Hz.
            process_seconds: Wall-clock seconds the DSP chain consumed.
            samples: The processed block (used to compute RMS).
            extra_latency_ms: Additional latency on top of the block size
                that should be reported (e.g. hardware buffer overhead).
            timestamp: Override the wall-clock timestamp (for tests).

        Returns:
            The :class:`MetricsRow` that was written.
        """
        if sample_rate <= 0:
            raise ValueError(f"sample_rate must be positive, got {sample_rate}.")
        if block_samples <= 0:
            raise ValueError(
                f"block_samples must be positive, got {block_samples}."
            )

        block_seconds = block_samples / sample_rate
        latency_ms = block_seconds * 1000.0 + extra_latency_ms
        cpu_percent = process_seconds / block_seconds if block_seconds > 0 else 0.0

        x = np.asarray(samples, dtype=np.float32)
        rms = float(np.sqrt(np.mean(x * x) + 1e-12))
        rms_dbfs = 20.0 * np.log10(max(rms, 1e-9))

        row = MetricsRow(
            timestamp=time.time() if timestamp is None else float(timestamp),
            block_seconds=block_seconds,
            process_seconds=process_seconds,
            latency_ms=latency_ms,
            cpu_percent=cpu_percent,
            rms_dbfs=rms_dbfs,
        )

        if self._writer is None:
            raise RuntimeError(
                "MetricsLogger.log_block() called before open().  "
                "Use the context manager or call .open() first."
            )
        self._writer.writerow([
            f"{row.timestamp:.6f}",
            f"{row.block_seconds:.6f}",
            f"{row.process_seconds:.6f}",
            f"{row.latency_ms:.3f}",
            f"{row.cpu_percent:.4f}",
            f"{row.rms_dbfs:.2f}",
        ])
        if self.keep_in_memory:
            self.rows.append(row)
        return row


def format_dashboard_line(row: MetricsRow) -> str:
    """Format *row* as a one-line terminal status string.

    Useful for ``dsp.pipeline --metrics-dashboard`` mode.
    """
    cpu_pct = row.cpu_percent * 100.0
    return (
        f"latency={row.latency_ms:6.2f} ms  "
        f"CPU={cpu_pct:5.1f}%  "
        f"level={row.rms_dbfs:6.1f} dBFS"
    )
