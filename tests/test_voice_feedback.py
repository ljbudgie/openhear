"""Tests for ``voice/feedback.py`` rendering helpers."""

from __future__ import annotations

import numpy as np

from voice.analyser import VoiceSnapshot
from voice.compare import VoiceComparison
from voice.feedback import _bar, _format_freq, _ref_marker, render_frame


class TestBar:
    def test_bar_contains_ansi(self):
        s = _bar(-30.0, -30.0, 0.0, bar_width=20, match_tol=3.0, gap_thr=6.0)
        # Matched → green colour.
        assert "\033[92m" in s
        assert "\033[0m" in s

    def test_gap_is_red(self):
        s = _bar(-60.0, -30.0, 0.0, bar_width=20, match_tol=3.0, gap_thr=6.0)
        assert "\033[91m" in s

    def test_near_match_no_colour(self):
        # Halfway between match tolerance and gap threshold → no colour wrap.
        s = _bar(-35.0, -30.0, 0.0, bar_width=20, match_tol=3.0, gap_thr=10.0)
        assert "\033[92m" not in s
        assert "\033[91m" not in s

    def test_bar_width_preserved(self):
        s = _bar(0.0, 0.0, 0.0, bar_width=30, match_tol=3.0, gap_thr=6.0)
        # Strip ANSI codes and count visible characters.
        import re
        plain = re.sub(r"\033\[[0-9;]*m", "", s)
        # Approx bar_width, possibly off by one for fractional block.
        assert len(plain) >= 30


class TestRefMarker:
    def test_below_range_clamps_to_zero(self):
        assert _ref_marker(-200.0, 0.0, 40) == 0

    def test_at_max(self):
        assert _ref_marker(0.0, 0.0, 40) == 40


class TestFormatFreq:
    def test_below_1khz(self):
        assert _format_freq(500.0) == "500"

    def test_at_or_above_1khz(self):
        assert _format_freq(1000.0) == "1.0k"
        assert _format_freq(2500.0) == "2.5k"


class TestRenderFrame:
    def _snapshot(self, n_bins: int = 512) -> VoiceSnapshot:
        env = np.linspace(-60, -20, n_bins, dtype=np.float32)
        return VoiceSnapshot(
            fundamental_frequency_hz=200.0,
            hnr_db=18.5,
            energy_db=-15.0,
            spectral_envelope=env,
        )

    def test_renders_multi_line_output(self):
        snap = self._snapshot()
        cmp = VoiceComparison(similarity_score=0.75)
        ref_env = np.linspace(-60, -20, 512, dtype=np.float32)
        out = render_frame(snap, ref_env, cmp, sample_rate=44_100, frame_size=1024)
        assert "F0:" in out
        assert "HNR:" in out
        assert "Similarity:" in out
        assert "reference target" in out

    def test_no_signal(self):
        snap = VoiceSnapshot()
        cmp = VoiceComparison()
        out = render_frame(snap, np.array([], dtype=np.float32), cmp)
        assert "(no signal)" in out

    def test_f0_zero_shows_dash(self):
        snap = self._snapshot()
        snap.fundamental_frequency_hz = 0.0
        cmp = VoiceComparison()
        out = render_frame(snap, np.array([], dtype=np.float32), cmp,
                           sample_rate=44_100, frame_size=1024)
        assert "F0:" in out
        assert "—" in out

    def test_empty_reference_envelope(self):
        snap = self._snapshot()
        cmp = VoiceComparison(similarity_score=0.0)
        out = render_frame(snap, np.array([], dtype=np.float32), cmp,
                           sample_rate=44_100, frame_size=1024)
        # With no reference, the reference target marker line is blank.
        assert "F0:" in out
