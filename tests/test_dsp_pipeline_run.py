"""Additional tests for ``dsp/pipeline.py``: ``run_pipeline`` & arg-parser."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pytest


def _ensure_pipeline_imported():
    if "dsp.pipeline" in sys.modules:
        return
    if "pyaudio" not in sys.modules:
        mod = types.ModuleType("pyaudio")
        mod.paInt16 = 8

        class _DummyPyAudio:
            def open(self, *args, **kwargs):
                raise RuntimeError("not used in tests")

            def terminate(self):
                pass

        mod.PyAudio = _DummyPyAudio
        sys.modules["pyaudio"] = mod
    import dsp.pipeline  # noqa: F401


_ensure_pipeline_imported()

from dsp import config, pipeline  # noqa: E402


# ---------------------------------------------------------------------------
# generate_test_tone
# ---------------------------------------------------------------------------


class TestGenerateTestTone:
    def test_returns_correct_length(self):
        samples, _ = pipeline.generate_test_tone(256, 16_000)
        assert samples.shape == (256,)
        assert samples.dtype == np.float32

    def test_phase_continuity(self):
        # Continuous phase across two consecutive blocks.
        block1, phase = pipeline.generate_test_tone(
            128, 16_000, frequency_hz=1000.0, phase=0.0,
        )
        block2, _ = pipeline.generate_test_tone(
            128, 16_000, frequency_hz=1000.0, phase=phase,
        )
        # The boundary should be smooth — no large jump.
        boundary_jump = abs(float(block2[0]) - float(block1[-1]))
        # For a 1 kHz tone @ 16 kHz, samples step ~0.382 max in absolute terms.
        assert boundary_jump < 0.25

    def test_amplitude_respected(self):
        samples, _ = pipeline.generate_test_tone(
            512, 16_000, amplitude=0.1, frequency_hz=2000.0,
        )
        assert float(np.max(np.abs(samples))) <= 0.1 + 1e-6


# ---------------------------------------------------------------------------
# _build_arg_parser
# ---------------------------------------------------------------------------


class TestBuildArgParser:
    def test_default_values(self):
        ns = pipeline._build_arg_parser().parse_args([])
        assert ns.bypass is False
        assert ns.test_tone is False
        assert ns.latency is False
        assert ns.metrics_csv is None

    def test_all_flags_set(self):
        ns = pipeline._build_arg_parser().parse_args([
            "--bypass", "--test-tone", "--latency", "--metrics-csv", "/tmp/m.csv",
        ])
        assert ns.bypass is True
        assert ns.test_tone is True
        assert ns.latency is True
        assert ns.metrics_csv == "/tmp/m.csv"

    def test_unknown_flag_rejected(self):
        with pytest.raises(SystemExit):
            pipeline._build_arg_parser().parse_args(["--no-such"])


# ---------------------------------------------------------------------------
# run_pipeline (with mocked PyAudio + KeyboardInterrupt)
# ---------------------------------------------------------------------------


class _FakeStream:
    def __init__(self, sample_count):
        self.writes: list[bytes] = []
        self.stopped = False
        self.closed = False
        # Provide silent input frames.
        self._frame_bytes = b"\x00\x00" * sample_count

    def read(self, n, exception_on_overflow=False):
        return b"\x00\x00" * n

    def write(self, payload):
        self.writes.append(payload)

    def stop_stream(self):
        self.stopped = True

    def close(self):
        self.closed = True


class _FakePyAudio:
    def __init__(self):
        self.opens: list[dict] = []
        self.streams: list[_FakeStream] = []
        self.terminated = False

    def open(self, **kwargs):
        self.opens.append(kwargs)
        s = _FakeStream(config.FRAMES_PER_BUFFER)
        self.streams.append(s)
        return s

    def terminate(self):
        self.terminated = True


def _patch_pyaudio(monkeypatch, fake_factory=None):
    fake = (fake_factory or _FakePyAudio)()
    fake_module = types.SimpleNamespace(
        PyAudio=lambda: fake,
        paInt16=8,
    )
    monkeypatch.setattr(pipeline, "pyaudio", fake_module)
    return fake


def _stop_after_n_blocks(n):
    """Build a side-effect that raises KeyboardInterrupt after *n* calls."""
    state = {"calls": 0}

    def _se(*args, **kwargs):  # noqa: ARG001
        state["calls"] += 1
        if state["calls"] > n:
            raise KeyboardInterrupt()
        return state["calls"]

    return _se


class TestRunPipeline:
    def test_open_failure_exits_with_code_1(self, monkeypatch):
        class _BrokenPyAudio:
            def open(self, **kwargs):
                raise OSError("no audio device")

            def terminate(self):
                self._terminated = True

        monkeypatch.setattr(
            pipeline, "pyaudio",
            types.SimpleNamespace(PyAudio=_BrokenPyAudio, paInt16=8),
        )
        with pytest.raises(SystemExit) as excinfo:
            pipeline.run_pipeline(test_tone=False)
        assert excinfo.value.code == 1

    def test_test_tone_mode_writes_blocks_until_interrupt(self, monkeypatch):
        fake = _patch_pyaudio(monkeypatch)

        # Stop after the second perf_counter() call.
        monkeypatch.setattr(pipeline.time, "perf_counter", _stop_after_n_blocks(2))

        pipeline.run_pipeline(bypass=True, test_tone=True)

        # Only the output stream is opened in test-tone mode.
        assert len(fake.streams) == 1
        # At least one block should have been written.
        assert len(fake.streams[0].writes) >= 1
        assert fake.streams[0].stopped is True
        assert fake.streams[0].closed is True
        assert fake.terminated is True

    def test_microphone_path_uses_input_stream(self, monkeypatch):
        fake = _patch_pyaudio(monkeypatch)
        monkeypatch.setattr(pipeline.time, "perf_counter", _stop_after_n_blocks(1))

        pipeline.run_pipeline(bypass=True, test_tone=False)

        # input + output streams.
        assert len(fake.streams) == 2

    def test_latency_logging_path(self, monkeypatch, caplog):
        fake = _patch_pyaudio(monkeypatch)
        monkeypatch.setattr(pipeline.time, "perf_counter", _stop_after_n_blocks(2))
        # Force the "1 second elapsed" branch by advancing monotonic.
        ticks = iter([0.0, 100.0, 100.0, 100.0])
        monkeypatch.setattr(
            pipeline.time, "monotonic", lambda: next(ticks, 100.0),
        )

        import logging
        with caplog.at_level(logging.INFO, logger=pipeline.logger.name):
            pipeline.run_pipeline(bypass=True, test_tone=True, measure_latency=True)
        assert any("latency=" in r.message for r in caplog.records)

    def test_metrics_csv_creates_file(self, monkeypatch, tmp_path: Path):
        fake = _patch_pyaudio(monkeypatch)
        monkeypatch.setattr(pipeline.time, "perf_counter", _stop_after_n_blocks(2))

        metrics_path = tmp_path / "metrics.csv"
        pipeline.run_pipeline(
            bypass=True, test_tone=True, metrics_path=str(metrics_path),
        )
        assert metrics_path.exists()
        # File should have a header + at least one data row.
        text = metrics_path.read_text()
        assert text.strip() != ""
