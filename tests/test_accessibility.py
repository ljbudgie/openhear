"""Tests for the accessibility access-profile model and its adapters."""

from __future__ import annotations

import pytest

from accessibility import (
    ACCESS_PROFILES,
    AUTISM,
    CEREBRAL_PALSY,
    NEUTRAL,
    SENSORY_PROCESSING,
    SAFETY_INTENSITY_FLOOR,
    AccessProfile,
    InputGate,
    get_access_profile,
    policy_config_for,
    scale_intensity,
    voice_match_tolerance_db,
)
from accessibility.profiles import (
    HAPTIC_INTENSITY_SCALE_RANGE,
    HAPTIC_REFRACTORY_SCALE_RANGE,
)
from stream.haptic_policy import HapticPolicy, PolicyConfig


class _Detection:
    """Minimal stand-in for ClassifiedSound (sound_key + confidence)."""

    def __init__(self, sound_key: str, confidence: float) -> None:
        self.sound_key = sound_key
        self.confidence = confidence


# ── Profile model ───────────────────────────────────────────────────────────


def test_cerebral_palsy_profile_is_registered():
    assert "cerebral_palsy" in ACCESS_PROFILES
    assert get_access_profile("cerebral_palsy") is CEREBRAL_PALSY
    assert get_access_profile("Cerebral-Palsy") is CEREBRAL_PALSY


@pytest.mark.parametrize(
    ("key", "profile"),
    [
        ("autism", AUTISM),
        ("sensory_processing", SENSORY_PROCESSING),
    ],
)
def test_sensory_profiles_are_registered_opt_in_starting_points(key, profile):
    assert ACCESS_PROFILES[key] is profile
    assert get_access_profile(key.replace("_", "-")) is profile
    assert profile.haptic_intensity_scale < 1.0
    assert profile.haptic_ramp_ms > 0
    assert profile.haptic_refractory_scale > 1.0
    assert profile.min_confidence_delta > 0
    assert profile.input_hold_ms > 0
    assert profile.screening_prompts
    assert "starting point" in " ".join(profile.notes).lower()


def test_cerebral_palsy_defaults_are_conservative():
    assert CEREBRAL_PALSY.haptic_intensity_scale < 1.0
    assert CEREBRAL_PALSY.haptic_ramp_ms > 0
    assert CEREBRAL_PALSY.haptic_refractory_scale > 1.0
    assert CEREBRAL_PALSY.min_confidence_delta > 0
    assert CEREBRAL_PALSY.input_hold_ms > 0
    assert CEREBRAL_PALSY.voice_tolerance_scale > 1.0
    assert CEREBRAL_PALSY.screening_prompts


def test_neutral_profile_changes_nothing():
    assert NEUTRAL.haptic_intensity_scale == 1.0
    assert NEUTRAL.haptic_refractory_scale == 1.0
    assert NEUTRAL.min_confidence_delta == 0.0
    assert NEUTRAL.voice_tolerance_scale == 1.0
    assert get_access_profile(None) is NEUTRAL


def test_unknown_profile_key_lists_alternatives():
    with pytest.raises(KeyError) as exc:
        get_access_profile("nope")
    assert "cerebral_palsy" in str(exc.value)


def test_values_are_clipped_into_the_safe_envelope():
    reckless = AccessProfile(
        key="reckless",
        haptic_intensity_scale=99.0,
        haptic_refractory_scale=0.01,
        min_confidence_delta=5.0,
        input_hold_ms=-10.0,
        voice_tolerance_scale=100.0,
    )
    assert reckless.haptic_intensity_scale == HAPTIC_INTENSITY_SCALE_RANGE[1]
    assert reckless.haptic_refractory_scale == HAPTIC_REFRACTORY_SCALE_RANGE[0]
    assert reckless.min_confidence_delta == 0.2
    assert reckless.input_hold_ms == 0.0
    assert reckless.voice_tolerance_scale == 3.0


def test_muting_is_impossible_even_by_hand():
    silenced = AccessProfile(key="silenced", haptic_intensity_scale=0.0)
    assert silenced.haptic_intensity_scale == HAPTIC_INTENSITY_SCALE_RANGE[0]
    assert scale_intensity(200, silenced) > 0


def test_key_is_normalised_and_label_defaulted():
    profile = AccessProfile(key="  Mixed Key-Name ")
    assert profile.key == "mixed_key_name"
    assert profile.label == "Mixed key name"


def test_empty_key_is_rejected():
    with pytest.raises(ValueError):
        AccessProfile(key="   ")


def test_replace_reclips_overrides():
    tuned = CEREBRAL_PALSY.replace(haptic_intensity_scale=0.5, input_hold_ms=10_000.0)
    assert tuned.haptic_intensity_scale == 0.5
    assert tuned.input_hold_ms == 2000.0
    assert CEREBRAL_PALSY.haptic_intensity_scale == 0.7  # original untouched


def test_round_trips_through_dict():
    payload = CEREBRAL_PALSY.to_dict()
    assert AccessProfile.from_dict(payload) == CEREBRAL_PALSY


def test_from_dict_ignores_unknown_keys_and_needs_a_key():
    profile = AccessProfile.from_dict({"key": "future", "invented_later": 7})
    assert profile.key == "future"
    with pytest.raises(ValueError):
        AccessProfile.from_dict({"label": "no key"})


# ── Haptic policy adaptation ────────────────────────────────────────────────


def test_policy_config_raises_floor_and_spaces_alerts():
    base = PolicyConfig()
    adapted = policy_config_for(CEREBRAL_PALSY, base)

    assert adapted.min_confidence == pytest.approx(
        base.min_confidence + CEREBRAL_PALSY.min_confidence_delta
    )
    for key, value in base.refractory_ms.items():
        assert adapted.refractory_for(key) == pytest.approx(
            value * CEREBRAL_PALSY.haptic_refractory_scale
        )
    assert adapted.fallback_refractory_ms > base.fallback_refractory_ms
    # The base config must not be mutated.
    assert base.refractory_ms == PolicyConfig().refractory_ms


def test_policy_config_for_neutral_matches_base():
    base = PolicyConfig()
    adapted = policy_config_for(None, base)
    assert adapted.min_confidence == base.min_confidence
    assert adapted.refractory_ms == base.refractory_ms


def test_confidence_floor_stays_usable_under_extremes():
    lenient = policy_config_for(
        AccessProfile(key="lenient", min_confidence_delta=-1.0),
        PolicyConfig(min_confidence=0.15),
    )
    assert 0.1 <= lenient.min_confidence <= 0.95

    strict = policy_config_for(
        AccessProfile(key="strict", min_confidence_delta=1.0),
        PolicyConfig(min_confidence=0.9),
    )
    assert strict.min_confidence <= 0.95


def test_adapted_policy_suppresses_a_marginal_detection():
    policy = HapticPolicy(policy_config_for(CEREBRAL_PALSY))
    marginal = _Detection("doorbell", 0.65)  # above the stock 0.6 floor

    assert HapticPolicy().decide(marginal, 0.0).should_fire is True
    assert policy.decide(marginal, 0.0).should_fire is False


def test_adapted_policy_still_fires_and_then_spaces_repeats():
    policy = HapticPolicy(policy_config_for(CEREBRAL_PALSY))
    stock_refractory = PolicyConfig().refractory_for("doorbell")

    assert policy.decide(_Detection("doorbell", 0.95), 0.0).should_fire is True
    # Silent where the stock config would already have fired again...
    assert policy.decide(_Detection("doorbell", 0.95), stock_refractory + 1).should_fire is False
    # ...but not silent forever.
    later = stock_refractory * CEREBRAL_PALSY.haptic_refractory_scale + 1
    assert policy.decide(_Detection("doorbell", 0.95), later).should_fire is True


@pytest.mark.parametrize("profile", [AUTISM, SENSORY_PROCESSING])
def test_sensory_profiles_use_the_shared_policy_and_input_adapters(profile):
    base = PolicyConfig()
    adapted = policy_config_for(profile, base)
    assert adapted.min_confidence > base.min_confidence
    assert adapted.refractory_for("doorbell") > base.refractory_for("doorbell")

    gate = InputGate(profile)
    assert gate.update(pressed=True, now_ms=0.0) is False
    assert gate.update(pressed=True, now_ms=profile.input_hold_ms) is True


# ── Intensity damping ───────────────────────────────────────────────────────


def test_intensity_is_damped_for_comfort():
    assert scale_intensity(200, CEREBRAL_PALSY) == 140
    assert scale_intensity(200, NEUTRAL) == 200
    assert scale_intensity(200, None) == 200


def test_safety_alerts_are_never_damped_below_the_floor():
    assert scale_intensity(200, CEREBRAL_PALSY, sound_key="alarm") == SAFETY_INTENSITY_FLOOR
    assert scale_intensity(255, CEREBRAL_PALSY, sound_key="alarm") >= SAFETY_INTENSITY_FLOOR
    # Non-safety classes are damped all the way.
    assert scale_intensity(200, CEREBRAL_PALSY, sound_key="media") == 140


@pytest.mark.parametrize("profile", [AUTISM, SENSORY_PROCESSING])
def test_sensory_profiles_preserve_the_safety_alert_floor(profile):
    assert scale_intensity(200, profile, sound_key="alarm") == SAFETY_INTENSITY_FLOOR
    assert scale_intensity(40, profile, sound_key="alarm") <= 40


def test_a_quiet_alarm_command_is_never_amplified():
    assert scale_intensity(40, CEREBRAL_PALSY, sound_key="alarm") <= 40
    assert scale_intensity(0, CEREBRAL_PALSY, sound_key="alarm") == 0


def test_intensity_stays_in_byte_range():
    assert scale_intensity(999, NEUTRAL) == 255
    assert scale_intensity(-5, CEREBRAL_PALSY) == 0


# ── Voice tolerance ─────────────────────────────────────────────────────────


def test_voice_tolerance_widens_for_dysarthria():
    assert voice_match_tolerance_db(3.0, CEREBRAL_PALSY) == pytest.approx(6.0)
    assert voice_match_tolerance_db(3.0, NEUTRAL) == pytest.approx(3.0)
    assert voice_match_tolerance_db(3.0) == pytest.approx(3.0)


# ── Motor input gate ────────────────────────────────────────────────────────


def test_brief_contact_is_ignored():
    gate = InputGate(CEREBRAL_PALSY)
    assert gate.update(pressed=True, now_ms=0.0) is False
    assert gate.update(pressed=True, now_ms=100.0) is False
    assert gate.update(pressed=False, now_ms=150.0) is False


def test_deliberate_hold_is_accepted_once():
    gate = InputGate(CEREBRAL_PALSY)
    gate.update(pressed=True, now_ms=0.0)
    assert gate.update(pressed=True, now_ms=CEREBRAL_PALSY.input_hold_ms) is True
    # Holding on does not re-trigger.
    assert gate.update(pressed=True, now_ms=5000.0) is False


def test_release_restarts_the_hold_requirement():
    gate = InputGate(CEREBRAL_PALSY)
    gate.update(pressed=True, now_ms=0.0)
    gate.update(pressed=False, now_ms=200.0)
    assert gate.update(pressed=True, now_ms=CEREBRAL_PALSY.input_hold_ms) is False


def test_repeat_within_lockout_is_ignored():
    gate = InputGate(CEREBRAL_PALSY)
    gate.update(pressed=True, now_ms=0.0)
    assert gate.update(pressed=True, now_ms=400.0) is True

    gate.update(pressed=False, now_ms=450.0)
    gate.update(pressed=True, now_ms=500.0)
    assert gate.update(pressed=True, now_ms=900.0) is False  # still inside lockout

    gate.update(pressed=False, now_ms=1400.0)
    gate.update(pressed=True, now_ms=1500.0)
    assert gate.update(pressed=True, now_ms=1900.0) is True


def test_neutral_gate_accepts_immediately():
    gate = InputGate()
    assert gate.update(pressed=True, now_ms=0.0) is True
    assert gate.update(pressed=True, now_ms=1.0) is False
    gate.update(pressed=False, now_ms=2.0)
    assert gate.update(pressed=True, now_ms=3.0) is True


def test_reset_clears_history():
    gate = InputGate(CEREBRAL_PALSY)
    gate.update(pressed=True, now_ms=0.0)
    gate.update(pressed=True, now_ms=400.0)
    gate.reset()
    gate.update(pressed=True, now_ms=410.0)
    assert gate.update(pressed=True, now_ms=810.0) is True
