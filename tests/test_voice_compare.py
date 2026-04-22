"""Tests for ``voice/compare.py``."""

from __future__ import annotations

import numpy as np

from voice.analyser import VoiceSnapshot
from voice.compare import BANDS, VoiceComparison, compare
from voice.reference import ReferenceProfile

SR = 44_100
FRAME = 1024


def _make_snapshot(envelope: np.ndarray) -> VoiceSnapshot:
    return VoiceSnapshot(spectral_envelope=envelope.astype(np.float32))


def _make_reference(envelope: np.ndarray, formants: list[float] | None = None
                    ) -> ReferenceProfile:
    return ReferenceProfile(
        artist_name="test",
        avg_formants=formants or [],
        spectral_envelope=envelope.astype(np.float32),
    )


class TestCompare:
    def test_empty_envelopes_return_zero_comparison(self):
        snap = VoiceSnapshot()
        ref = ReferenceProfile()
        result = compare(snap, ref)
        assert isinstance(result, VoiceComparison)
        assert result.similarity_score == 0.0

    def test_identical_envelopes(self):
        env = np.linspace(-60, -20, FRAME // 2 + 1, dtype=np.float32)
        snap = _make_snapshot(env)
        ref = _make_reference(env)
        result = compare(snap, ref, sample_rate=SR, frame_size=FRAME)
        # With identical envelopes, every band diff is 0, similarity is 1.0.
        for name in BANDS:
            assert abs(result.band_differences[name]) < 1e-5
        assert result.similarity_score > 0.99
        assert result.underused_formants == []
        assert result.resonance_gap_hz == []

    def test_user_below_reference_flags_underused_formants(self):
        n_bins = FRAME // 2 + 1
        user_env = np.full(n_bins, -60.0, dtype=np.float32)
        ref_env = np.full(n_bins, -30.0, dtype=np.float32)
        snap = _make_snapshot(user_env)
        ref = _make_reference(ref_env, formants=[500.0, 1500.0])
        result = compare(snap, ref, sample_rate=SR, frame_size=FRAME,
                         match_tolerance_db=3.0, gap_threshold_db=6.0)
        # Both formants should be flagged underused.
        assert 500.0 in result.underused_formants
        assert 1500.0 in result.underused_formants
        # Every bin falls below the gap threshold.
        assert len(result.resonance_gap_hz) > 0

    def test_similarity_score_in_range(self):
        n_bins = FRAME // 2 + 1
        rng = np.random.default_rng(0)
        user_env = rng.standard_normal(n_bins).astype(np.float32) * 10 - 30
        ref_env = rng.standard_normal(n_bins).astype(np.float32) * 10 - 30
        snap = _make_snapshot(user_env)
        ref = _make_reference(ref_env)
        result = compare(snap, ref, sample_rate=SR, frame_size=FRAME)
        assert 0.0 <= result.similarity_score <= 1.0

    def test_flat_envelopes_give_zero_similarity(self):
        n_bins = FRAME // 2 + 1
        user_env = np.full(n_bins, -50.0, dtype=np.float32)
        ref_env = np.full(n_bins, -50.0, dtype=np.float32)
        snap = _make_snapshot(user_env)
        ref = _make_reference(ref_env)
        result = compare(snap, ref, sample_rate=SR, frame_size=FRAME)
        # Constant envelopes have zero variation → similarity falls through
        # to 0.0 (norm < 1e-10).
        assert result.similarity_score == 0.0

    def test_unequal_lengths_truncate(self):
        n = FRAME // 2 + 1
        user_env = np.linspace(-60, -20, n, dtype=np.float32)
        ref_env = np.linspace(-60, -20, n + 50, dtype=np.float32)
        snap = _make_snapshot(user_env)
        ref = _make_reference(ref_env)
        result = compare(snap, ref, sample_rate=SR, frame_size=FRAME)
        # Does not raise — truncates to shorter length.
        assert isinstance(result, VoiceComparison)
