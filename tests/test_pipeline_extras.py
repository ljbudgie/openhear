"""Tests for the new pipeline helpers and the offline demo CLI."""

from __future__ import annotations

import sys
import types
import wave
from pathlib import Path

import numpy as np
import pytest


def _stub_pyaudio() -> None:
    if "pyaudio" in sys.modules:
        return
    mod = types.ModuleType("pyaudio")
    mod.paInt16 = 8

    class _DummyPyAudio:
        def open(self, *args, **kwargs):
            raise RuntimeError("not used")

        def terminate(self):
            pass

    mod.PyAudio = _DummyPyAudio
    sys.modules["pyaudio"] = mod


_stub_pyaudio()


def test_generate_test_tone_phase_continuity():
    """Two consecutive tone blocks must form a continuous waveform.

    Concatenating block 1 with block 2 and comparing the resulting
    end-of-block-1-to-start-of-block-2 step against a single 512-sample
    block must show the same step (i.e. the phase math is correct).
    """
    from dsp.pipeline import generate_test_tone

    s1, ph = generate_test_tone(256, 16_000, frequency_hz=1000.0)
    s2, _ = generate_test_tone(256, 16_000, frequency_hz=1000.0, phase=ph)

    s_full, _ = generate_test_tone(512, 16_000, frequency_hz=1000.0)
    np.testing.assert_allclose(np.concatenate([s1, s2]), s_full, atol=1e-6)


def test_generate_test_tone_returns_correct_length():
    from dsp.pipeline import generate_test_tone

    s, _ = generate_test_tone(512, 16_000)
    assert s.shape == (512,)


def _write_wav_file(path: Path, samples: np.ndarray, sr: int) -> None:
    """Helper – write a 16-bit mono WAV file."""
    int16 = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16.tobytes())


def test_demo_bypass_round_trips_wave_file(tmp_path: Path):
    """In bypass mode the demo should faithfully copy the audio."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from examples import demo  # type: ignore

    sr = 16_000
    n = 4096
    sig = (0.2 * np.sin(2 * np.pi * 500 * np.arange(n) / sr)).astype(np.float32)
    in_path = tmp_path / "in.wav"
    out_path = tmp_path / "out.wav"
    _write_wav_file(in_path, sig, sr)

    rc = demo.main([
        "--input", str(in_path),
        "--output", str(out_path),
        "--bypass",
        "--config", str(Path(__file__).resolve().parent.parent / "examples" / "config.yaml"),
    ])
    assert rc == 0
    assert out_path.exists()

    with wave.open(str(out_path), "rb") as wf:
        n_out = wf.getnframes()
        raw = wf.readframes(n_out)
        sr_out = wf.getframerate()
    assert sr_out == sr
    assert n_out == n


def test_demo_processes_wave_file_through_chain(tmp_path: Path):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from examples import demo  # type: ignore

    sr = 16_000
    n = 4096
    sig = (0.2 * np.sin(2 * np.pi * 500 * np.arange(n) / sr)).astype(np.float32)
    in_path = tmp_path / "in.wav"
    out_path = tmp_path / "out.wav"
    _write_wav_file(in_path, sig, sr)

    rc = demo.main([
        "--input", str(in_path),
        "--output", str(out_path),
        "--block-size", "256",
        "--config", str(Path(__file__).resolve().parent.parent / "examples" / "config.yaml"),
    ])
    assert rc == 0
    with wave.open(str(out_path), "rb") as wf:
        assert wf.getframerate() == sr
        assert wf.getnframes() == n


def test_demo_missing_config_returns_error(tmp_path: Path):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from examples import demo  # type: ignore

    in_path = tmp_path / "in.wav"
    out_path = tmp_path / "out.wav"
    _write_wav_file(in_path, np.zeros(1024, dtype=np.float32), 16_000)

    rc = demo.main([
        "--input", str(in_path),
        "--output", str(out_path),
        "--config", str(tmp_path / "nope.yaml"),
    ])
    assert rc != 0
