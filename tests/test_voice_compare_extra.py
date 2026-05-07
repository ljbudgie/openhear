"""Additional tests for ``voice/compare.py`` covering edge cases not reached
by the main test suite."""

from __future__ import annotations

import numpy as np

from voice.analyser import VoiceSnapshot
from voice.compare import _band_energy, compare
from voice.reference import ReferenceProfile

SR = 44_100
FRAME = 1024


def _make_snapshot(envelope: np.ndarray) -> VoiceSnapshot:
    return VoiceSnapshot(spectral_envelope=envelope.astype(np.float32))


def _make_reference(envelope: np.ndarray, formants: list[float] | None = None) -> ReferenceProfile:
    return ReferenceProfile(
        artist_name="test",
        avg_formants=formants or [],
        spectral_envelope=envelope.astype(np.float32),
    )


class TestBandEnergy:
    def test_no_bins_in_band_returns_minus_100(self):
        """When no frequency bins fall in the band, return -100 dB."""
        envelope = np.full(10, -30.0, dtype=np.float32)
        # Frequencies well above the query band: 10 bins of 5000 Hz each
        freqs = np.linspace(5000.0, 10000.0, 10, dtype=np.float32)
        result = _band_energy(envelope, freqs, 80.0, 300.0)
        assert result == -100.0

    def test_bins_in_band_returns_mean(self):
        """Bins inside the band should be averaged."""
        envelope = np.array([-30.0, -20.0, -30.0], dtype=np.float32)
        freqs = np.array([100.0, 200.0, 5000.0], dtype=np.float32)
        result = _band_energy(envelope, freqs, 80.0, 300.0)
        # Only first two bins (100 Hz, 200 Hz) are in the band.
        assert result == -25.0


class TestCompareEdgeCases:
    def test_user_empty_returns_zero_comparison(self):
        snap = _make_snapshot(np.array([], dtype=np.float32))
        ref = _make_reference(np.linspace(-60, -20, 512, dtype=np.float32))
        result = compare(snap, ref, sample_rate=SR, frame_size=FRAME)
        assert result.similarity_score == 0.0
        assert result.band_differences == {}

    def test_ref_empty_returns_zero_comparison(self):
        snap = _make_snapshot(np.linspace(-60, -20, 512, dtype=np.float32))
        ref = _make_reference(np.array([], dtype=np.float32))
        result = compare(snap, ref, sample_rate=SR, frame_size=FRAME)
        assert result.similarity_score == 0.0
