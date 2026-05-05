"""Additional tests for ``stream/latency.py`` (CLI + edge cases)."""

from __future__ import annotations

import sys

import numpy as np
import pytest

from stream import latency
from stream.latency import (
    LatencyReport,
    detect_impulse_delay,
    format_report,
    main,
    measure_latency,
    synthesise_impulse,
)

# ---------------------------------------------------------------------------
# synthesise_impulse argument validation
# ---------------------------------------------------------------------------


def test_synthesise_impulse_rejects_zero_duration():
    with pytest.raises(ValueError):
        synthesise_impulse(0)


def test_synthesise_impulse_rejects_out_of_range_index():
    with pytest.raises(ValueError):
        synthesise_impulse(10, impulse_at=10)
    with pytest.raises(ValueError):
        synthesise_impulse(10, impulse_at=-1)


def test_synthesise_impulse_default_amplitude():
    out = synthesise_impulse(8, impulse_at=2)
    assert out.shape == (8,)
    assert out[2] == pytest.approx(0.9)
    # Other samples are zero.
    assert float(np.sum(np.abs(out))) == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# detect_impulse_delay edge cases
# ---------------------------------------------------------------------------


def test_detect_impulse_delay_empty_returns_minus_one():
    assert detect_impulse_delay(np.zeros(0, dtype=np.float32)) == -1


def test_detect_impulse_delay_silence_returns_minus_one():
    assert detect_impulse_delay(np.zeros(100, dtype=np.float32)) == -1


# ---------------------------------------------------------------------------
# measure_latency
# ---------------------------------------------------------------------------


def test_measure_latency_invalid_sample_rate():
    rec = np.zeros(10, dtype=np.float32)
    with pytest.raises(ValueError):
        measure_latency(rec, 0)


def test_measure_latency_within_target():
    sample_rate = 16_000
    rec = synthesise_impulse(1000, impulse_at=160)  # 10 ms
    report = measure_latency(rec, sample_rate, target_ms=20.0)
    assert report.impulse_index == 160
    assert report.latency_ms == pytest.approx(10.0)
    assert report.within_target is True
    assert report.verdict == "within target"


def test_measure_latency_above_target():
    sample_rate = 16_000
    rec = synthesise_impulse(1000, impulse_at=480)  # 30 ms
    report = measure_latency(rec, sample_rate, target_ms=20.0)
    assert report.within_target is False
    assert report.verdict == "above target"


def test_measure_latency_no_impulse_returns_nan():
    report = measure_latency(np.zeros(100, dtype=np.float32), 16_000)
    assert report.impulse_index == -1
    assert report.verdict == "no impulse detected"
    assert report.within_target is False
    # NaN check
    import math
    assert math.isnan(report.latency_ms)


# ---------------------------------------------------------------------------
# format_report
# ---------------------------------------------------------------------------


def test_format_report_no_impulse():
    report = LatencyReport(
        latency_ms=float("nan"), target_ms=20.0,
        sample_rate=16_000, impulse_index=-1,
    )
    text = format_report(report)
    assert "No impulse detected" in text


def test_format_report_with_values():
    report = LatencyReport(
        latency_ms=12.34, target_ms=20.0,
        sample_rate=16_000, impulse_index=200,
    )
    text = format_report(report)
    assert "latency=" in text
    assert "12.34" in text
    assert "target=20.0" in text
    assert "within target" in text


# ---------------------------------------------------------------------------
# CLI main()
# ---------------------------------------------------------------------------


def test_main_returns_2_when_pyaudio_missing(monkeypatch, caplog):
    """If ``import pyaudio`` raises in ``main``, return code 2."""
    real_pyaudio = sys.modules.pop("pyaudio", None)

    # Block re-import by adding a meta-path finder.
    class _Blocker:
        def find_module(self, name, path=None):
            if name == "pyaudio":
                return self
            return None

        def find_spec(self, name, path=None, target=None):
            if name == "pyaudio":
                raise ImportError("pyaudio not available")
            return None

        def load_module(self, name):
            raise ImportError("pyaudio not available")

    blocker = _Blocker()
    sys.meta_path.insert(0, blocker)
    try:
        rc = main(["--target", "20", "--sample-rate", "16000"])
        assert rc == 2
    finally:
        sys.meta_path.remove(blocker)
        if real_pyaudio is not None:
            sys.modules["pyaudio"] = real_pyaudio


def test_main_arg_parser_rejects_unknown_flag():
    with pytest.raises(SystemExit):
        main(["--no-such-flag"])


def test_main_measures_latency_with_fake_pyaudio(monkeypatch, capsys):
    sample_rate = 1000
    duration_ms = 50
    impulse_index = 5
    recording = np.zeros(int(sample_rate * duration_ms / 1000), dtype=np.int16)
    recording[impulse_index] = 32767

    class _FakeStream:
        def __init__(self, raw: bytes = b""):
            self.raw = raw
            self.stopped = False
            self.closed = False
            self.written = b""

        def read(self, frames, exception_on_overflow=False):
            if frames != recording.size:
                raise ValueError("latency CLI should read the full capture window")
            if exception_on_overflow:
                raise ValueError("latency CLI should disable overflow exceptions")
            return self.raw

        def write(self, data):
            self.written = data

        def stop_stream(self):
            self.stopped = True

        def close(self):
            self.closed = True

    class _FakePyAudioInstance:
        def __init__(self):
            self.input_stream = _FakeStream(recording.tobytes())
            self.output_stream = _FakeStream()
            self.terminated = False

        def open(self, **kwargs):
            assert kwargs["rate"] == sample_rate
            assert kwargs["format"] == _FakePyAudio.paInt16
            assert kwargs["frames_per_buffer"] == recording.size
            if kwargs.get("input"):
                return self.input_stream
            if kwargs.get("output"):
                return self.output_stream
            raise AssertionError("expected input or output stream")

        def terminate(self):
            self.terminated = True

    class _FakePyAudio:
        paInt16 = object()
        instance = _FakePyAudioInstance()

        @staticmethod
        def PyAudio():
            return _FakePyAudio.instance

    monkeypatch.setitem(sys.modules, "pyaudio", _FakePyAudio)

    rc = main(
        [
            "--sample-rate",
            str(sample_rate),
            "--duration-ms",
            str(duration_ms),
            "--target",
            "10",
        ]
    )

    assert rc == 0
    assert "latency=  5.00 ms" in capsys.readouterr().out
    assert _FakePyAudio.instance.input_stream.stopped is True
    assert _FakePyAudio.instance.output_stream.closed is True
    assert _FakePyAudio.instance.terminated is True
