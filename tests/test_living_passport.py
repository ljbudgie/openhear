"""
Tests for audiogram.passport — Hearing Passport exporter.
"""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from audiogram.living_profile import LivingHearingProfile
from audiogram.passport import (
    build_passport_bundle,
    build_passport_markdown,
    export_passport,
)

_PROFILE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "audiogram", "data", "burgess_living_profile.json"
)


@pytest.fixture
def profile():
    return LivingHearingProfile.from_file(_PROFILE_PATH)


class TestPassportMarkdown:
    def test_contains_subject(self, profile):
        md = build_passport_markdown(profile)
        assert "Lewis Burgess" in md

    def test_contains_clinical_section(self, profile):
        md = build_passport_markdown(profile)
        assert "Clinical Core" in md

    def test_contains_gain_profile(self, profile):
        md = build_passport_markdown(profile)
        assert "Gain Profile" in md

    def test_contains_haptic_weights(self, profile):
        md = build_passport_markdown(profile)
        assert "Haptic" in md

    def test_contains_history_when_requested(self, profile):
        md = build_passport_markdown(profile, include_history=True)
        assert "Change History" in md

    def test_omits_history_when_not_requested(self, profile):
        md = build_passport_markdown(profile, include_history=False)
        assert "Change History" not in md

    def test_sovereignty_notice_present(self, profile):
        md = build_passport_markdown(profile)
        assert "sovereign" in md.lower() or "Sovereign" in md


class TestPassportBundle:
    def test_bundle_keys(self, profile):
        bundle = build_passport_bundle(profile)
        for key in ("format", "subject", "clinical_thresholds", "gain_profile_clinical",
                    "haptic_weights", "sovereignty_notice"):
            assert key in bundle

    def test_bundle_format_string(self, profile):
        bundle = build_passport_bundle(profile)
        assert bundle["format"] == "openhear-hearing-passport-v1"

    def test_bundle_includes_history_by_default(self, profile):
        bundle = build_passport_bundle(profile)
        assert "history" in bundle
        assert isinstance(bundle["history"], list)

    def test_bundle_omits_history_when_disabled(self, profile):
        bundle = build_passport_bundle(profile, include_history=False)
        assert "history" not in bundle

    def test_clinical_thresholds_present(self, profile):
        bundle = build_passport_bundle(profile)
        right = bundle["clinical_thresholds"]["right"]
        assert any(freq == 1000 for freq, _ in right)


class TestExportPassport:
    def test_writes_md_file(self, profile):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "passport.md")
            export_passport(profile, out, include_json_bundle=False)
            assert os.path.exists(out)
            with open(out, encoding="utf-8") as fh:
                content = fh.read()
            assert "Lewis Burgess" in content

    def test_writes_json_bundle(self, profile):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "passport.md")
            export_passport(profile, out, include_json_bundle=True)
            json_path = os.path.join(tmpdir, "passport.json")
            assert os.path.exists(json_path)
            with open(json_path, encoding="utf-8") as fh:
                bundle = json.load(fh)
            assert bundle["subject"] == "Lewis Burgess"

    def test_adds_md_extension_if_missing(self, profile):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "passport_no_ext")
            export_passport(profile, out, include_json_bundle=False)
            assert os.path.exists(out + ".md")
