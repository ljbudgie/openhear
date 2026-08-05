"""Tests for profile-backed adaptive sensory mapping."""

from __future__ import annotations

from audiogram.adaptive_sensory_mapping import (
    AcousticFeatures,
    AdaptationObservation,
    AdaptiveSensoryMapper,
)
from audiogram.living_profile import LivingHearingProfile


def _profile() -> LivingHearingProfile:
    profile = LivingHearingProfile.from_manual_entry(
        "Test", [(500, 40), (1000, 60), (2000, 70), (4000, 80)],
        [(500, 40), (1000, 60), (2000, 70), (4000, 80)],
    )
    profile.set_adaptive_sensory_mapping(
        {
            "version": 1,
            "enabled": True,
            "adaptation_policy": {"learning_rate": 0.05, "minimum_observations": 2},
            "sound_classes": {
                "alarm": {
                    "pulse_rate_hz": 8,
                    "intensity": 200,
                    "spatial_balance": 0,
                    "sharpness": 0.8,
                    "silence_ms": 100,
                    "urgency_intensity_delta": 40,
                }
            },
            "adaptation_history": [],
        }
    )
    return profile


def test_render_uses_features_and_preserves_deliberate_silence():
    cue = AdaptiveSensoryMapper(_profile()).render(
        "alarm", features=AcousticFeatures(confidence=1, urgency=1)
    )
    assert cue.primitive.intensity == 240
    assert cue.silence_ms == 100


def test_observations_are_retained_and_refinement_is_committed():
    profile = _profile()
    mapper = AdaptiveSensoryMapper(profile)
    observation = AdaptationObservation("alarm", 0, 0, 1)
    assert mapper.observe(observation) is False
    assert mapper.observe(observation) is True
    mapping = profile.get_adaptive_sensory_mapping()
    assert len(mapping["adaptation_history"]) == 2
    assert mapping["sound_classes"]["alarm"]["intensity"] > 200
    assert profile.get_history()[-1]["change_type"] == "adaptive_sensory_mapping_refined"


def test_unknown_sound_class_is_rejected():
    mapper = AdaptiveSensoryMapper(_profile())
    try:
        mapper.render("unknown")
    except KeyError:
        pass
    else:
        raise AssertionError("unknown classes must not silently use another mapping")
