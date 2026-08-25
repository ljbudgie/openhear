"""Tests for therapy/dermal_profiles.py — 30–100 Hz haptic exploration profiles."""

from __future__ import annotations

import pytest

from therapy.dermal_profiles import (
    DEFAULT_DUTY_CYCLE,
    MAX_AMPLITUDE,
    MAX_SESSION_S,
    DERMAL_PROFILES,
    DermalProfile,
    get_dermal_profile,
)
from therapy.protocol import (
    ContraindicationError,
    EvidenceGrade,
    TherapeuticProtocol,
)

# ── Registry smoke-tests ─────────────────────────────────────────────────────


def test_all_bundled_profiles_present():
    assert set(DERMAL_PROFILES) == {"gamma_low", "gamma_mid", "gamma_high"}


def test_get_dermal_profile_returns_correct_type():
    for key in DERMAL_PROFILES:
        profile = get_dermal_profile(key)
        assert isinstance(profile, DermalProfile)


def test_get_dermal_profile_unknown_key_raises():
    with pytest.raises(KeyError, match="unknown_key"):
        get_dermal_profile("unknown_key")


def test_get_dermal_profile_error_lists_available():
    with pytest.raises(KeyError, match="gamma_low"):
        get_dermal_profile("nonexistent")


# ── Evidence grade & frequency range ─────────────────────────────────────────


def test_all_profiles_are_anecdotal():
    for key, profile in DERMAL_PROFILES.items():
        assert profile.protocol.evidence_grade == EvidenceGrade.ANECDOTAL, (
            f"{key} should be ANECDOTAL"
        )


def test_all_frequencies_in_30_to_100_hz():
    for key, profile in DERMAL_PROFILES.items():
        for freq in profile.protocol.frequencies:
            assert 30.0 <= freq <= 100.0, (
                f"{key} frequency {freq} Hz out of 30–100 Hz range"
            )


def test_frequencies_ordered_ascending():
    freqs = [DERMAL_PROFILES[k].protocol.frequencies[0] for k in ["gamma_low", "gamma_mid", "gamma_high"]]
    assert freqs == sorted(freqs)


# ── Safety ceiling enforcement ────────────────────────────────────────────────


def test_all_sessions_within_max_duration():
    for key, profile in DERMAL_PROFILES.items():
        assert profile.protocol.session_length_s <= MAX_SESSION_S, (
            f"{key} session_length_s exceeds {MAX_SESSION_S} s"
        )


def test_all_amplitudes_within_ceiling():
    for key, profile in DERMAL_PROFILES.items():
        assert profile.recommended_amplitude <= MAX_AMPLITUDE, (
            f"{key} recommended_amplitude exceeds {MAX_AMPLITUDE}"
        )


def test_amplitude_must_not_exceed_max():
    with pytest.raises(ValueError, match="recommended_amplitude"):
        DermalProfile(
            protocol=TherapeuticProtocol(
                name="test",
                frequencies=(40.0,),
                session_length_s=600,
            ),
            receptor_context="test",
            recommended_amplitude=MAX_AMPLITUDE + 1,
        )


def test_session_over_ceiling_rejected():
    with pytest.raises(ValueError, match="20-minute safety ceiling"):
        DermalProfile(
            protocol=TherapeuticProtocol(
                name="test",
                frequencies=(40.0,),
                session_length_s=MAX_SESSION_S + 1,
            ),
            receptor_context="test",
            recommended_amplitude=80,
        )


# ── Contraindication gating ───────────────────────────────────────────────────


def test_open_wound_is_contraindicated():
    profile = get_dermal_profile("gamma_low")
    with pytest.raises(ContraindicationError):
        profile.gate({"open_wound"})


def test_peripheral_neuropathy_is_contraindicated():
    profile = get_dermal_profile("gamma_mid")
    with pytest.raises(ContraindicationError):
        profile.gate({"peripheral_neuropathy"})


def test_pregnancy_is_contraindicated():
    profile = get_dermal_profile("gamma_high")
    with pytest.raises(ContraindicationError):
        profile.gate({"pregnancy"})


def test_no_conditions_passes_gate():
    for key in DERMAL_PROFILES:
        # Should not raise.
        get_dermal_profile(key).gate(set())


def test_unrelated_condition_passes_gate():
    profile = get_dermal_profile("gamma_low")
    # A condition not in the contraindication set must not block the session.
    profile.gate({"hypertension"})


def test_case_insensitive_contraindication_check():
    profile = get_dermal_profile("gamma_mid")
    with pytest.raises(ContraindicationError):
        profile.gate({"OPEN_WOUND"})


# ── Protocol fields ───────────────────────────────────────────────────────────


def test_carrier_shape_is_sine():
    for profile in DERMAL_PROFILES.values():
        assert profile.protocol.carrier_shape == "sine"


def test_duty_cycle_matches_default():
    for profile in DERMAL_PROFILES.values():
        assert profile.protocol.duty_cycle == DEFAULT_DUTY_CYCLE


def test_washout_period_is_set():
    for profile in DERMAL_PROFILES.values():
        assert profile.protocol.washout_period_s > 0


def test_receptor_context_is_non_empty():
    for key, profile in DERMAL_PROFILES.items():
        assert profile.receptor_context.strip(), f"{key} has empty receptor_context"


def test_target_outcomes_declared():
    for key, profile in DERMAL_PROFILES.items():
        assert profile.protocol.target_outcomes, f"{key} has no target_outcomes"
