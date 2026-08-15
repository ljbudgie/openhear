"""End-to-end accessibility behaviour in the live wristband runtime."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from accessibility import (
    AUTISM,
    CEREBRAL_PALSY,
    NEUTRAL,
    SAFETY_INTENSITY_FLOOR,
    SENSORY_PROCESSING,
)
from stream.haptic_packet import ramp_config_packet
from stream.wristband_runtime import WristbandRuntime, _access_profile_from_args


class _Mapper:
    def build_command(self, sound_key: str, *, confidence: float) -> tuple[int, int, int]:
        return (3 if sound_key == "alarm" else 2, 200, 3 if sound_key == "alarm" else 2)


class _Client:
    def __init__(self) -> None:
        self.packets = []

    async def send_packet(self, packet) -> None:
        self.packets.append(packet)


def test_neutral_profile_leaves_live_packet_unchanged():
    runtime = WristbandRuntime(_Mapper(), _Client(), access_profile=NEUTRAL)

    assert runtime.packet_from_classification("doorbell", 1.0).intensity == 200


@pytest.mark.parametrize("profile", [AUTISM, CEREBRAL_PALSY])
def test_access_profiles_damp_non_safety_live_output(profile):
    runtime = WristbandRuntime(_Mapper(), _Client(), access_profile=profile)

    assert runtime.packet_from_classification("doorbell", 1.0).intensity < 200


@pytest.mark.parametrize("profile", [AUTISM, CEREBRAL_PALSY])
def test_access_profiles_keep_alarm_at_safety_floor(profile):
    runtime = WristbandRuntime(_Mapper(), _Client(), access_profile=profile)

    assert runtime.packet_from_classification("alarm", 1.0).intensity >= SAFETY_INTENSITY_FLOOR


def test_runtime_sends_session_only_ramp_configuration():
    client = _Client()
    runtime = WristbandRuntime(_Mapper(), client, access_profile=AUTISM)

    asyncio.run(runtime.configure_access_profile())

    assert client.packets == [ramp_config_packet(AUTISM.haptic_ramp_ms)]


def test_access_profile_policy_rejects_marginal_non_safety_detection(monkeypatch):
    client = _Client()
    runtime = WristbandRuntime(_Mapper(), client, access_profile=AUTISM)
    monkeypatch.setattr(
        "stream.wristband_runtime.classify_scores",
        lambda _scores: SimpleNamespace(
            sound_key="doorbell", confidence=0.65, source_label="Doorbell"
        ),
    )

    assert asyncio.run(runtime.send_scores({"Doorbell": 0.65})) is None
    assert client.packets == []


def test_sensory_processing_profile_is_accepted_by_runtime_configuration():
    profile = _access_profile_from_args(
        SimpleNamespace(
            access_profile="sensory_processing",
            access_intensity_scale=None,
            access_ramp_ms=None,
            access_refractory_scale=None,
            access_hold_ms=None,
        )
    )

    assert profile == SENSORY_PROCESSING
