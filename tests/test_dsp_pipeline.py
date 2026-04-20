"""Tests for ``dsp/pipeline.py`` (pure helpers only — no mic I/O)."""

from __future__ import annotations

import sys
import types

import numpy as np
import pytest


def _stub_pyaudio() -> None:
    """Install a minimal pyaudio stub so ``dsp.pipeline`` can be imported.

    The test environment does not have PyAudio installed (and we do not
    exercise real audio I/O in unit tests).  This stub provides just
    enough of the module surface for the ``import pyaudio`` statement
    at the top of ``dsp.pipeline`` to succeed; no actual device access
    is enabled.
    """
    if "pyaudio" in sys.modules:
        return
    mod = types.ModuleType("pyaudio")
    mod.paInt16 = 8  # Matches real PyAudio value.

    class _DummyPyAudio:
        def open(self, *args, **kwargs):
            raise RuntimeError("not used in tests")

        def terminate(self):
            pass

    mod.PyAudio = _DummyPyAudio
    sys.modules["pyaudio"] = mod


_stub_pyaudio()

from dsp import config, pipeline  # noqa: E402


class TestBytesToFloat32:
    def test_round_trip_zero(self):
        raw = np.zeros(128, dtype=np.int16).tobytes()
        out = pipeline._bytes_to_float32(raw)
        assert out.shape == (128,)
        np.testing.assert_array_equal(out, 0.0)

    def test_range_mapping(self):
        raw = np.array([32767, -32768, 0], dtype=np.int16).tobytes()
        out = pipeline._bytes_to_float32(raw)
        assert out.dtype == np.float32
        # 32767 / 32768 ≈ 0.99997
        assert abs(out[0] - (32767 / 32768.0)) < 1e-6
        assert out[1] == -1.0
        assert out[2] == 0.0


class TestFloat32ToBytes:
    def test_round_trip(self):
        x = np.array([0.0, 0.5, -0.5], dtype=np.float32)
        raw = pipeline._float32_to_bytes(x, channels=1)
        recovered = np.frombuffer(raw, dtype=np.int16)
        assert recovered[0] == 0
        assert recovered[1] == int(0.5 * 32767)
        assert recovered[2] == int(-0.5 * 32767)

    def test_clips_out_of_range(self):
        x = np.array([1.5, -2.0], dtype=np.float32)
        raw = pipeline._float32_to_bytes(x, channels=1)
        recovered = np.frombuffer(raw, dtype=np.int16)
        assert recovered[0] == 32767
        assert recovered[1] == -32767

    def test_duplicates_for_stereo(self):
        x = np.array([0.1, -0.1], dtype=np.float32)
        raw = pipeline._float32_to_bytes(x, channels=2)
        recovered = np.frombuffer(raw, dtype=np.int16)
        # Two source samples × 2 channels = 4 int16s.
        assert len(recovered) == 4
        assert recovered[0] == recovered[1]  # Duplicated left/right.
        assert recovered[2] == recovered[3]


class TestBuildDspChain:
    def test_all_stages_enabled(self, monkeypatch):
        monkeypatch.setattr(config, "NOISE_REDUCTION_ENABLED", True)
        monkeypatch.setattr(config, "COMPRESSION_ENABLED", True)
        monkeypatch.setattr(config, "VOICE_CLARITY_ENABLED", True)
        monkeypatch.setattr(config, "FEEDBACK_CANCELLATION_ENABLED", True)
        monkeypatch.setattr(config, "OWN_VOICE_BYPASS_ENABLED", True)

        chain = pipeline.build_dsp_chain()
        assert len(chain) == 5

        from dsp.compression import WDRCompressor
        from dsp.feedback_canceller import FeedbackCanceller
        from dsp.noise_reduction import SpectralSubtractor
        from dsp.own_voice_bypass import OwnVoiceBypass
        from dsp.voice_clarity import VoiceClarityEnhancer

        assert isinstance(chain[0], SpectralSubtractor)
        assert isinstance(chain[1], WDRCompressor)
        assert isinstance(chain[2], VoiceClarityEnhancer)
        assert isinstance(chain[3], FeedbackCanceller)
        assert isinstance(chain[4], OwnVoiceBypass)

    def test_all_stages_disabled(self, monkeypatch, caplog):
        monkeypatch.setattr(config, "NOISE_REDUCTION_ENABLED", False)
        monkeypatch.setattr(config, "COMPRESSION_ENABLED", False)
        monkeypatch.setattr(config, "VOICE_CLARITY_ENABLED", False)
        monkeypatch.setattr(config, "FEEDBACK_CANCELLATION_ENABLED", False)
        monkeypatch.setattr(config, "OWN_VOICE_BYPASS_ENABLED", False)

        import logging
        with caplog.at_level(logging.WARNING):
            chain = pipeline.build_dsp_chain()
        assert chain == []
        assert any("disabled" in r.message for r in caplog.records)

    def test_partial_enable(self, monkeypatch):
        monkeypatch.setattr(config, "NOISE_REDUCTION_ENABLED", False)
        monkeypatch.setattr(config, "COMPRESSION_ENABLED", True)
        monkeypatch.setattr(config, "VOICE_CLARITY_ENABLED", False)
        monkeypatch.setattr(config, "FEEDBACK_CANCELLATION_ENABLED", False)
        monkeypatch.setattr(config, "OWN_VOICE_BYPASS_ENABLED", False)

        chain = pipeline.build_dsp_chain()
        assert len(chain) == 1

    def test_chain_processes_samples(self, monkeypatch):
        monkeypatch.setattr(config, "NOISE_REDUCTION_ENABLED", True)
        monkeypatch.setattr(config, "COMPRESSION_ENABLED", True)
        monkeypatch.setattr(config, "VOICE_CLARITY_ENABLED", True)
        monkeypatch.setattr(config, "FEEDBACK_CANCELLATION_ENABLED", True)
        monkeypatch.setattr(config, "OWN_VOICE_BYPASS_ENABLED", True)

        chain = pipeline.build_dsp_chain()
        samples = np.zeros(config.FRAMES_PER_BUFFER, dtype=np.float32)
        for stage in chain:
            samples = stage.process(samples)
        assert samples.shape == (config.FRAMES_PER_BUFFER,)
        assert samples.dtype == np.float32
