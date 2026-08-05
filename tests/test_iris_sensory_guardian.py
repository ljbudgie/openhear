"""Tests for local, permission-gated Iris sensory oversight."""

from __future__ import annotations

import pytest

from audiogram.adaptive_sensory_mapping import AdaptationObservation, AdaptiveSensoryMapper
from audiogram.iris_sensory_guardian import IrisSensoryGuardian, SensoryAccessContext
from audiogram.living_profile import LivingHearingProfile


def _guardian() -> IrisSensoryGuardian:
    profile = LivingHearingProfile.from_manual_entry(
        "Test",
        [(500, 40), (1000, 60), (2000, 70), (4000, 80)],
        [(500, 40), (1000, 60), (2000, 70), (4000, 80)],
    )
    profile.set_adaptive_sensory_mapping(
        {
            "version": 1,
            "enabled": True,
            "adaptation_policy": {"learning_rate": 0.05, "minimum_observations": 10},
            "sound_classes": {
                "alarm": {
                    "pulse_rate_hz": 8,
                    "intensity": 200,
                    "spatial_balance": 0,
                    "sharpness": 0.8,
                    "silence_ms": 100,
                }
            },
            "adaptation_history": [],
        }
    )
    return IrisSensoryGuardian(AdaptiveSensoryMapper(profile))


def test_guardian_proposes_local_protective_change_without_changing_mapping():
    guardian = _guardian()
    review = guardian.review(
        AdaptationObservation("alarm", 0.8, 0.8, 0.2, motor_stability=0.3),
        context=SensoryAccessContext(fatigue=0.8, tremor=0.8, cerebral_palsy=True),
    )

    assert review.proposal is not None
    assert review.proposal.burgess_status == "NULL"
    assert "comfort" in review.proposal.explanation
    mapping = guardian.mapper.profile.get_adaptive_sensory_mapping()
    assert mapping["sound_classes"]["alarm"]["intensity"] == 200
    assert mapping["iris_sensory_guardian"]["local_only"] is True


def test_guardian_requires_permission_and_preserves_tactile_identity():
    guardian = _guardian()
    proposal = guardian.review(
        AdaptationObservation("alarm", 0.8, 0.8, 0.2, motor_stability=0.3)
    ).proposal
    assert proposal is not None

    with pytest.raises(PermissionError):
        guardian.apply(proposal.proposal_id, user_permission=False)

    guardian.apply(proposal.proposal_id, user_permission=True)
    mapping = guardian.mapper.profile.get_adaptive_sensory_mapping()
    encoding = mapping["sound_classes"]["alarm"]
    assert encoding["intensity"] < 200
    assert encoding["pulse_rate_hz"] == 8
    assert encoding["spatial_balance"] == 0
    assert encoding["sharpness"] == 0.8
    assert mapping["iris_sensory_guardian"]["proposals"][0]["burgess_status"] == "SOVEREIGN"
    assert guardian.mapper.profile.get_history()[-1]["change_type"] == "iris_sensory_guardian_adjustment"
