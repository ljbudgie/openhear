"""Tests for ``stream/haptic_policy.py`` — the sound→haptic decision layer."""

from __future__ import annotations

from dataclasses import dataclass

from stream.haptic_packet import encode_packet
from stream.haptic_policy import (
    PRIORITY,
    SAFETY_PRIORITY,
    HapticPolicy,
    PolicyConfig,
    packet_for,
    priority_of,
)


@dataclass
class _Sound:
    """Minimal duck-typed stand-in for ClassifiedSound."""

    sound_key: str
    confidence: float


def _policy(**kw) -> HapticPolicy:
    return HapticPolicy(PolicyConfig(**kw))


# ── Actionability ───────────────────────────────────────────────────────────


def test_silence_never_fires():
    d = _policy().decide(_Sound("silence", 1.0), now_ms=0)
    assert d.should_fire is False
    assert d.reason == "not_actionable"


def test_unknown_class_never_fires():
    d = _policy().decide(_Sound("spaceship", 1.0), now_ms=0)
    assert d.should_fire is False
    assert d.reason == "not_actionable"


# ── Confidence gate ─────────────────────────────────────────────────────────


def test_low_confidence_is_suppressed():
    d = _policy(min_confidence=0.6).decide(_Sound("alarm", 0.4), now_ms=0)
    assert d.should_fire is False
    assert d.reason == "low_confidence"


def test_confident_detection_fires():
    d = _policy().decide(_Sound("alarm", 0.9), now_ms=0)
    assert d.should_fire is True
    assert d.reason == "fire"


# ── Per-class refractory / debounce ─────────────────────────────────────────


def test_same_class_is_debounced_within_refractory():
    p = _policy()
    assert p.decide(_Sound("doorbell", 0.9), now_ms=0).should_fire is True
    # doorbell refractory is 1200 ms; 500 ms later must be suppressed.
    again = p.decide(_Sound("doorbell", 0.9), now_ms=500)
    assert again.should_fire is False
    assert again.reason == "refractory"
    # After the window it fires again.
    assert p.decide(_Sound("doorbell", 0.9), now_ms=1300).should_fire is True


def test_different_classes_are_independent():
    p = _policy()
    assert p.decide(_Sound("alarm", 0.9), now_ms=0).should_fire is True
    # A doorbell right after is a different class with its own window.
    assert p.decide(_Sound("doorbell", 0.9), now_ms=50).should_fire is True


def test_reset_clears_refractory_history():
    p = _policy()
    assert p.decide(_Sound("alarm", 0.9), now_ms=0).should_fire is True
    p.reset()
    assert p.decide(_Sound("alarm", 0.9), now_ms=100).should_fire is True


# ── Priority ────────────────────────────────────────────────────────────────


def test_priority_ordering_is_safety_first():
    assert priority_of("alarm") > priority_of("doorbell") > priority_of("media")
    assert priority_of("silence") == 0
    assert priority_of("unknown") == 0


def test_safety_flag():
    p = _policy()
    assert p.decide(_Sound("alarm", 0.9), now_ms=0).is_safety is True
    assert p.decide(_Sound("media", 0.9), now_ms=0).is_safety is False
    assert PRIORITY["alarm"] == SAFETY_PRIORITY


# ── packet_for bridge (policy → mapper → wire codec) ────────────────────────


def test_packet_for_encodes_firing_decision():
    p = _policy()
    decision = p.decide(_Sound("alarm", 0.9), now_ms=0)
    calls: list[tuple] = []

    def fake_build_command(sound_key, *, confidence):
        calls.append((sound_key, confidence))
        return (3, 200, 3)  # sound_class_id, intensity, pattern_id

    packet = packet_for(decision, fake_build_command)
    assert packet == encode_packet(3, 200, 3) == b"\x03\xc8\x03"
    # Confidence is threaded through to the mapper.
    assert calls == [("alarm", 0.9)]


def test_packet_for_returns_none_when_not_firing():
    p = _policy()
    p.decide(_Sound("doorbell", 0.9), now_ms=0)  # prime refractory
    decision = p.decide(_Sound("doorbell", 0.9), now_ms=100)  # suppressed
    assert decision.should_fire is False
    assert packet_for(decision, lambda *a, **k: (0, 0, 0)) is None
