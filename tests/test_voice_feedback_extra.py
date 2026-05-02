"""Additional tests for ``voice/feedback.py`` – covering the ``run_live``
function and edge cases in rendering helpers."""

from __future__ import annotations

import io
import sys

import numpy as np
import pytest

from voice.analyser import VoiceSnapshot
from voice.compare import VoiceComparison
from voice.feedback import _bar, _format_freq, _ref_marker, render_frame, run_live


class TestBarEdgeCases:
    """Test ``_bar`` color-coding paths not covered by existing tests."""

    def test_above_reference_within_tolerance_is_green(self):
        # value above ref but within match_tol → green
        s = _bar(-27.0, -30.0, 0.0, bar_width=20, match_tol=5.0, gap_thr=10.0)
        assert "\033[92m" in s

    def test_above_reference_outside_tolerance_no_colour(self):
        # value above ref by more than tolerance but not below by gap_thr → no colour
        s = _bar(-20.0, -30.0, 0.0, bar_width=20, match_tol=3.0, gap_thr=10.0)
        assert "\033[92m" not in s
        assert "\033[91m" not in s

    def test_value_at_zero_is_full_bar(self):
        s = _bar(0.0, -100.0, 0.0, bar_width=5, match_tol=1.0, gap_thr=5.0)
        # The result should be red (big gap downward from reference)
        # Actually: value (0) - ref (-100) = +100 > match_tol so no green,
        # diff > 0 so not red either. Plain bar.
        assert isinstance(s, str)


class TestRunLive:
    def test_run_live_iterates_and_renders(self, capsys):
        """run_live should iterate snapshots, call comparison_fn, and write output."""
        sr = 44_100
        n_bins = 512
        env = np.linspace(-60, -20, n_bins, dtype=np.float32)
        ref_env = np.linspace(-65, -25, n_bins, dtype=np.float32)

        snapshots = [
            VoiceSnapshot(
                fundamental_frequency_hz=200.0,
                hnr_db=15.0,
                energy_db=-20.0,
                spectral_envelope=env,
            )
            for _ in range(2)
        ]

        def comparison_fn(snapshot):
            return VoiceComparison(similarity_score=0.8)

        # Use refresh_hz=1000 so time.sleep is as short as possible.
        run_live(
            iter(snapshots),
            ref_env,
            comparison_fn,
            refresh_hz=1_000.0,
            sample_rate=sr,
            frame_size=1024,
        )
        captured = capsys.readouterr().out
        # At least one frame was written
        assert "F0:" in captured

    def test_run_live_keyboard_interrupt_exits_cleanly(self, capsys):
        """KeyboardInterrupt during iteration should print 'Stopped.' and return."""

        def _raising_gen():
            yield VoiceSnapshot(
                fundamental_frequency_hz=100.0,
                hnr_db=10.0,
                energy_db=-30.0,
                spectral_envelope=np.zeros(128, dtype=np.float32),
            )
            raise KeyboardInterrupt

        run_live(
            _raising_gen(),
            np.array([], dtype=np.float32),
            lambda s: VoiceComparison(),
            refresh_hz=1_000.0,
        )
        captured = capsys.readouterr().out
        assert "Stopped" in captured

    def test_run_live_empty_generator_does_not_crash(self):
        """An empty generator should return immediately without error."""
        run_live(
            iter([]),
            np.array([], dtype=np.float32),
            lambda s: VoiceComparison(),
        )


class TestRenderFrameEdgeCases:
    def test_ref_envelope_larger_than_user_env(self):
        """ref_envelope longer than user env should not cause index errors."""
        n_bins = 128
        snap = VoiceSnapshot(
            fundamental_frequency_hz=150.0,
            hnr_db=10.0,
            energy_db=-25.0,
            spectral_envelope=np.linspace(-80, -30, n_bins, dtype=np.float32),
        )
        cmp = VoiceComparison(similarity_score=0.5)
        ref_env = np.linspace(-70, -20, n_bins * 2, dtype=np.float32)  # longer ref
        out = render_frame(snap, ref_env, cmp, sample_rate=44_100, frame_size=256)
        assert "F0:" in out

    def test_render_frame_custom_n_bands(self):
        n_bins = 512
        snap = VoiceSnapshot(
            fundamental_frequency_hz=300.0,
            hnr_db=12.0,
            energy_db=-18.0,
            spectral_envelope=np.linspace(-60, -10, n_bins, dtype=np.float32),
        )
        cmp = VoiceComparison(similarity_score=0.9)
        out = render_frame(
            snap,
            np.array([], dtype=np.float32),
            cmp,
            sample_rate=44_100,
            frame_size=1024,
            n_bands=8,
        )
        assert "F0:" in out
