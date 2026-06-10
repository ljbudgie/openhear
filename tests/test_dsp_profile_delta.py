"""Tests for :mod:`dsp.profile_delta`."""

from __future__ import annotations

import pytest

from dsp.profile_delta import (
    MAX_COMPRESSION_KNEE_DELTA_DB,
    MAX_COMPRESSION_RATIO_DELTA,
    MAX_NR_AGGRESSIVENESS_DELTA,
    MAX_VOICE_GAIN_DELTA,
    ProfileDelta,
)


class TestClipping:
    def test_identity_default(self):
        d = ProfileDelta()
        assert d.is_identity()
        assert d.compression_ratio_delta == 0.0
        assert d.sources == ()
        assert d.reason == ""

    def test_ratio_clipped_high(self):
        d = ProfileDelta(compression_ratio_delta=99.0)
        assert d.compression_ratio_delta == MAX_COMPRESSION_RATIO_DELTA

    def test_ratio_clipped_low(self):
        d = ProfileDelta(compression_ratio_delta=-99.0)
        assert d.compression_ratio_delta == -MAX_COMPRESSION_RATIO_DELTA

    def test_knee_clipped(self):
        assert ProfileDelta(compression_knee_delta_db=50).compression_knee_delta_db == (
            MAX_COMPRESSION_KNEE_DELTA_DB
        )
        assert ProfileDelta(compression_knee_delta_db=-50).compression_knee_delta_db == (
            -MAX_COMPRESSION_KNEE_DELTA_DB
        )

    def test_voice_gain_clipped(self):
        assert ProfileDelta(voice_gain_delta=10).voice_gain_delta == MAX_VOICE_GAIN_DELTA

    def test_nr_alpha_clipped(self):
        assert (
            ProfileDelta(nr_aggressiveness_delta=5).nr_aggressiveness_delta
            == MAX_NR_AGGRESSIVENESS_DELTA
        )

    def test_within_bounds_preserved(self):
        d = ProfileDelta(
            compression_ratio_delta=0.2,
            compression_knee_delta_db=-3.0,
            voice_gain_delta=0.1,
            nr_aggressiveness_delta=-0.1,
        )
        assert d.compression_ratio_delta == pytest.approx(0.2)
        assert d.compression_knee_delta_db == pytest.approx(-3.0)
        assert d.voice_gain_delta == pytest.approx(0.1)
        assert d.nr_aggressiveness_delta == pytest.approx(-0.1)


class TestCombine:
    def test_combine_sums_fields(self):
        a = ProfileDelta(compression_ratio_delta=0.2, sources=("a",), reason="A")
        b = ProfileDelta(compression_ratio_delta=0.2, sources=("b",), reason="B")
        c = a.combine(b)
        assert c.compression_ratio_delta == pytest.approx(0.4)
        assert c.sources == ("a", "b")
        assert c.reason == "A + B"

    def test_combine_re_clips(self):
        a = ProfileDelta(compression_ratio_delta=MAX_COMPRESSION_RATIO_DELTA)
        b = ProfileDelta(compression_ratio_delta=MAX_COMPRESSION_RATIO_DELTA)
        c = a.combine(b)
        # Both at the limit — sum would exceed; result must clip back.
        assert c.compression_ratio_delta == MAX_COMPRESSION_RATIO_DELTA

    def test_compose_empty_is_identity(self):
        assert ProfileDelta.compose([]).is_identity()

    def test_compose_preserves_order(self):
        deltas = [
            ProfileDelta(sources=("x",)),
            ProfileDelta(sources=("y",)),
            ProfileDelta(sources=("z",)),
        ]
        assert ProfileDelta.compose(deltas).sources == ("x", "y", "z")


class TestApply:
    def test_apply_to_compression_floors_at_one(self):
        d = ProfileDelta(compression_ratio_delta=-MAX_COMPRESSION_RATIO_DELTA)
        ratio, knee = d.apply_to_compression(ratio=1.0, knee_dbfs=-40.0)
        assert ratio == 1.0  # floored
        assert knee == -40.0

    def test_apply_to_compression_changes_both(self):
        d = ProfileDelta(compression_ratio_delta=0.3, compression_knee_delta_db=-2)
        ratio, knee = d.apply_to_compression(ratio=2.0, knee_dbfs=-40.0)
        assert ratio == pytest.approx(2.3)
        assert knee == pytest.approx(-42.0)

    def test_apply_to_voice_gain_floors_at_zero(self):
        d = ProfileDelta(voice_gain_delta=-MAX_VOICE_GAIN_DELTA)
        assert d.apply_to_voice_gain(0.1) == 0.0
        assert d.apply_to_voice_gain(1.0) == pytest.approx(1.0 - MAX_VOICE_GAIN_DELTA)

    def test_apply_to_nr_alpha_floors_at_one(self):
        d = ProfileDelta(nr_aggressiveness_delta=-MAX_NR_AGGRESSIVENESS_DELTA)
        # Even with a low alpha, the result is floored at 1.0.
        assert d.apply_to_nr_alpha(1.1) == 1.0
        assert d.apply_to_nr_alpha(1.5) == pytest.approx(
            1.5 - MAX_NR_AGGRESSIVENESS_DELTA
        )


class TestExplain:
    def test_identity_explain(self):
        assert ProfileDelta().explain() == "no DSP delta applied"

    def test_explain_includes_sources_and_reason(self):
        d = ProfileDelta(
            compression_ratio_delta=-0.2,
            voice_gain_delta=0.1,
            sources=("contact:partner",),
            reason="partner voice tuning",
        )
        text = d.explain()
        assert "comp ratio -0.20" in text
        assert "voice gain +0.10" in text
        assert "contact:partner" in text
        assert "partner voice tuning" in text

    def test_with_source_appends(self):
        d = ProfileDelta(sources=("a",)).with_source("b")
        assert d.sources == ("a", "b")

    def test_frozen(self):
        d = ProfileDelta()
        with pytest.raises((AttributeError, Exception)):
            d.compression_ratio_delta = 0.1  # type: ignore[misc]


class TestNegativeLimit:
    def test_negative_limit_rejected(self):
        from dsp.profile_delta import _clip

        with pytest.raises(ValueError):
            _clip(0.0, -1.0)
