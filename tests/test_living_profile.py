"""
Tests for audiogram.living_profile — LivingHearingProfile core.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile

import pytest

from audiogram.living_profile import (
    FORMAT_VERSION,
    LivingHearingProfile,
    load_living_profile,
)

# Path to the reference Living Hearing Profile for the founder.
_PROFILE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "audiogram", "data", "burgess_living_profile.json"
)
_V1_PATH = os.path.join(
    os.path.dirname(__file__), "..", "audiogram", "data", "burgess_2021.json"
)


# ── Loading ────────────────────────────────────────────────────────────────────


class TestLoading:
    def test_load_living_profile_file(self):
        profile = LivingHearingProfile.from_file(_PROFILE_PATH)
        assert profile.subject == "Lewis Burgess"

    def test_load_v1_audiogram_wraps_automatically(self):
        """A plain v1 audiogram is wrapped into a living profile on load."""
        profile = LivingHearingProfile.from_file(_V1_PATH)
        assert profile.subject == "Lewis Burgess"
        assert profile.clinical_date == "2021-10-20"

    def test_load_living_profile_convenience(self):
        profile = load_living_profile(_PROFILE_PATH)
        assert isinstance(profile, LivingHearingProfile)

    def test_load_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            LivingHearingProfile.from_file("/nonexistent/profile.json")

    def test_load_wrong_version_raises(self):
        bad = {"format_version": "unknown-v99", "subject": "X"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fh:
            json.dump(bad, fh)
            path = fh.name
        try:
            with pytest.raises(ValueError, match="Unsupported format version"):
                LivingHearingProfile.from_file(path)
        finally:
            os.unlink(path)


# ── Clinical core ──────────────────────────────────────────────────────────────


class TestClinicalCore:
    def setup_method(self):
        self.profile = LivingHearingProfile.from_file(_PROFILE_PATH)

    def test_get_thresholds_right(self):
        thresholds = self.profile.get_thresholds("right")
        freqs = [t[0] for t in thresholds]
        assert 1000 in freqs

    def test_get_thresholds_left(self):
        thresholds = self.profile.get_thresholds("left")
        assert thresholds[0][0] == 125  # sorted by frequency

    def test_get_pta_right(self):
        pta = self.profile.get_pta("right")
        # Manually: (50+75+80+85)/4 = 72.5
        assert pta == pytest.approx(72.5, abs=0.1)

    def test_get_pta_left(self):
        pta = self.profile.get_pta("left")
        assert isinstance(pta, float)

    def test_invalid_ear_raises(self):
        with pytest.raises(ValueError, match="ear must be"):
            self.profile.get_thresholds("center")


# ── Gain profile ───────────────────────────────────────────────────────────────


class TestGainProfile:
    def setup_method(self):
        self.profile = LivingHearingProfile.from_file(_PROFILE_PATH)

    def test_clinical_gain_right_at_1000hz(self):
        # threshold 75 dB HL → gain = 75-20 = 55 dB
        gains = dict(self.profile.get_gain_profile("right", include_preference=False))
        assert gains[1000] == 55

    def test_preference_offset_applied(self):
        # The profile has a +3 dB preference offset at 1000 Hz
        clinical = dict(self.profile.get_gain_profile("right", include_preference=False))
        with_pref = dict(self.profile.get_gain_profile("right", include_preference=True))
        diff = with_pref[1000] - clinical[1000]
        assert diff == 3  # matches the offset in the reference file

    def test_gain_never_negative(self):
        for ear in ("right", "left"):
            for _, gain in self.profile.get_gain_profile(ear, include_preference=True):
                assert gain >= 0


# ── Preference layer ───────────────────────────────────────────────────────────


class TestPreferenceLayer:
    def setup_method(self):
        self.profile = LivingHearingProfile.from_manual_entry(
            subject="Test User",
            right_thresholds=[(500, 50), (1000, 70), (2000, 80), (4000, 85)],
            left_thresholds=[(500, 55), (1000, 75), (2000, 80), (4000, 85)],
        )

    def test_set_loudness_offset_adds_entry(self):
        self.profile.set_loudness_offset("right", 1000, offset_db=5)
        gains_pref = dict(self.profile.get_gain_profile("right", include_preference=True))
        gains_clinical = dict(self.profile.get_gain_profile("right", include_preference=False))
        assert gains_pref[1000] == gains_clinical[1000] + 5

    def test_set_loudness_offset_updates_existing(self):
        self.profile.set_loudness_offset("right", 1000, offset_db=3)
        self.profile.set_loudness_offset("right", 1000, offset_db=7)
        gains = dict(self.profile.get_gain_profile("right", include_preference=True))
        gains_clin = dict(self.profile.get_gain_profile("right", include_preference=False))
        assert gains[1000] == gains_clin[1000] + 7

    def test_set_comfort_ceiling(self):
        self.profile.set_comfort_ceiling(90)
        assert self.profile._data["preference_layer"]["comfort_ceiling_db_spl"] == 90


# ── Context map ────────────────────────────────────────────────────────────────


class TestContextMap:
    def setup_method(self):
        self.profile = LivingHearingProfile.from_file(_PROFILE_PATH)

    def test_list_contexts(self):
        contexts = self.profile.list_contexts()
        assert "quiet_conversation" in contexts
        assert "noisy_environment" in contexts

    def test_get_active_context(self):
        ctx = self.profile.get_active_context()
        assert ctx.get("name") == "quiet_conversation"

    def test_set_active_context(self):
        self.profile.set_active_context("music")
        ctx = self.profile.get_active_context()
        assert ctx.get("name") == "music"

    def test_set_invalid_context_raises(self):
        with pytest.raises(KeyError, match="not found"):
            self.profile.set_active_context("underwater_nightclub")


# ── Haptic layer ───────────────────────────────────────────────────────────────


class TestHapticLayer:
    def setup_method(self):
        self.profile = LivingHearingProfile.from_file(_PROFILE_PATH)

    def test_get_haptic_weights_returns_dict(self):
        weights = self.profile.get_haptic_weights()
        assert isinstance(weights, dict)
        assert "alarm" in weights

    def test_alarm_weight_is_max(self):
        weights = self.profile.get_haptic_weights()
        assert weights["alarm"] == 1.0

    def test_set_haptic_weight_clamps(self):
        self.profile.set_haptic_weight("alarm", 1.5)
        assert self.profile.get_haptic_weights()["alarm"] == 1.0

    def test_set_haptic_weight_unknown_class_raises(self):
        with pytest.raises(KeyError):
            self.profile.set_haptic_weight("foghorn", 0.5)


# ── History / commitment ───────────────────────────────────────────────────────


class TestHistory:
    def setup_method(self):
        self.profile = LivingHearingProfile.from_manual_entry(
            subject="Alice",
            right_thresholds=[(500, 40), (1000, 60), (2000, 70), (4000, 75)],
            left_thresholds=[(500, 45), (1000, 65), (2000, 75), (4000, 80)],
        )

    def test_commit_returns_sha256(self):
        sha = self.profile.commit("Initial commit")
        assert len(sha) == 64  # SHA-256 hex digest

    def test_commit_appends_history(self):
        before = len(self.profile.get_history())
        self.profile.commit("A change")
        after = len(self.profile.get_history())
        assert after == before + 1

    def test_commit_sha256_is_reproducible(self):
        """Two profiles with identical state should produce the same hash."""
        p1 = LivingHearingProfile.from_manual_entry(
            "Bob", [(500, 30), (1000, 40), (2000, 50), (4000, 55)],
            [(500, 35), (1000, 45), (2000, 55), (4000, 60)]
        )
        p2 = LivingHearingProfile.from_manual_entry(
            "Bob", [(500, 30), (1000, 40), (2000, 50), (4000, 55)],
            [(500, 35), (1000, 45), (2000, 55), (4000, 60)]
        )
        sha1 = p1.commit("same change")
        sha2 = p2.commit("same change")
        # Both computed over identical states
        assert sha1 == sha2

    def test_commit_description_stored(self):
        self.profile.commit("Updated comfort preference", change_type="preference_update")
        last = self.profile.get_history()[-1]
        assert last["description"] == "Updated comfort preference"
        assert last["change_type"] == "preference_update"


# ── Persistence ────────────────────────────────────────────────────────────────


class TestPersistence:
    def test_save_and_reload(self):
        profile = LivingHearingProfile.from_file(_PROFILE_PATH)
        profile.set_loudness_offset("right", 1000, offset_db=6)
        profile.commit("Updated preference")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fh:
            path = fh.name

        try:
            profile.save(path)
            reloaded = LivingHearingProfile.from_file(path)
            gains = dict(reloaded.get_gain_profile("right", include_preference=True))
            assert gains[1000] == dict(profile.get_gain_profile("right", include_preference=True))[1000]
        finally:
            os.unlink(path)


# ── Summary ────────────────────────────────────────────────────────────────────


class TestSummary:
    def test_summary_keys(self):
        profile = LivingHearingProfile.from_file(_PROFILE_PATH)
        summ = profile.summary()
        for key in ("subject", "clinical_date", "last_updated", "right_pta", "left_pta",
                    "right_severity", "left_severity", "active_context", "history_entries"):
            assert key in summ

    def test_summary_severity_severe(self):
        profile = LivingHearingProfile.from_file(_PROFILE_PATH)
        summ = profile.summary()
        # PTA ~72.5 dB HL → severe
        assert summ["right_severity"] == "severe"
