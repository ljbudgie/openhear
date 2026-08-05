"""
Tests for audiogram.interpreter — plain-English hearing experience interpreter.
"""

from __future__ import annotations

import os

import pytest

from audiogram.interpreter import interpret_profile
from audiogram.living_profile import LivingHearingProfile

_PROFILE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "audiogram", "data", "burgess_living_profile.json"
)
_V1_PATH = os.path.join(
    os.path.dirname(__file__), "..", "audiogram", "data", "burgess_2021.json"
)


@pytest.fixture
def profile():
    return LivingHearingProfile.from_file(_PROFILE_PATH)


@pytest.fixture
def v1_profile():
    """A profile created by wrapping a v1 audiogram."""
    return LivingHearingProfile.from_file(_V1_PATH)


class TestInterpretProfile:
    def test_returns_list_of_strings(self, profile):
        lines = interpret_profile(profile)
        assert isinstance(lines, list)
        assert all(isinstance(line, str) for line in lines)

    def test_contains_subject_name(self, profile):
        text = "\n".join(interpret_profile(profile))
        assert "Lewis Burgess" in text

    def test_contains_frequency_descriptions(self, profile):
        text = "\n".join(interpret_profile(profile))
        assert "Hz" in text

    def test_contains_haptic_section(self, profile):
        text = "\n".join(interpret_profile(profile))
        assert "Haptic" in text

    def test_contains_context_section(self, profile):
        text = "\n".join(interpret_profile(profile))
        assert "Context" in text or "context" in text

    def test_works_with_wrapped_v1(self, v1_profile):
        lines = interpret_profile(v1_profile)
        text = "\n".join(lines)
        assert "Lewis Burgess" in text
        assert "Hz" in text

    def test_severe_pta_described(self, profile):
        text = "\n".join(interpret_profile(profile))
        # PTA ~72 dB HL — should mention severe or DSP
        assert "severe" in text.lower() or "DSP" in text

    def test_sovereignty_notice_present(self, profile):
        text = "\n".join(interpret_profile(profile))
        assert "sovereign" in text.lower() or "Apache" in text
