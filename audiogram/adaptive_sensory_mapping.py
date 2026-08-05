"""Profile-backed, local-first adaptive tactile encodings.

The mapping is deliberately data-driven: a Living Hearing Profile owns the
starting encoding and each bounded refinement.  This module never sends data
off-device and records only user-approved, aggregate observations -- never
raw audio or continuous sensor traces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from accessibility.adapt import scale_intensity
from accessibility.profiles import NEUTRAL, AccessProfile
from audiogram.living_profile import LivingHearingProfile
from stream.haptic_primitive import HapticPrimitive

_ENCODING_FIELDS = (
    "pulse_rate_hz",
    "intensity",
    "spatial_balance",
    "sharpness",
    "silence_ms",
)
_BOUNDS: dict[str, tuple[float, float]] = {
    "pulse_rate_hz": (0.1, 30.0),
    "intensity": (0.0, 255.0),
    "spatial_balance": (-1.0, 1.0),
    "sharpness": (0.0, 1.0),
    "silence_ms": (0.0, 5_000.0),
}


@dataclass(frozen=True)
class AcousticFeatures:
    """Important acoustic features supplied by the local classifier."""

    confidence: float = 1.0
    urgency: float = 0.0
    direction: float = 0.0
    intensity: float = 1.0


@dataclass(frozen=True)
class AdaptationObservation:
    """A local, inspectable summary of one experienced haptic cue.

    Scores range from 0.0 to 1.0.  ``perceptibility`` and ``usefulness`` may
    be derived from explicit user feedback or a local interaction flow;
    callers must not infer them from raw audio.
    """

    sound_class: str
    perceptibility: float
    usefulness: float
    comfort: float
    motor_stability: float = 1.0
    sensory_adaptation: float = 0.0
    user_preference: float = 0.5


@dataclass(frozen=True)
class RenderedSensoryMapping:
    """A multi-layer cue plus its intentional silence interval."""

    primitive: HapticPrimitive
    silence_ms: int
    acoustic_features: AcousticFeatures

    def legacy_command(self, sound_class_id: int, pattern_id: int) -> tuple[int, int, int]:
        """Collapse to the unchanged v1 command shape for existing wristbands."""
        return sound_class_id, self.primitive.intensity, pattern_id


class AdaptiveSensoryMapper:
    """Render and slowly refine the mapping stored in a Living Hearing Profile."""

    def __init__(
        self,
        profile: LivingHearingProfile,
        *,
        access_profile: AccessProfile | None = None,
    ) -> None:
        self.profile = profile
        self.access_profile = access_profile or NEUTRAL

    def render(
        self,
        sound_class: str,
        *,
        features: AcousticFeatures | None = None,
    ) -> RenderedSensoryMapping:
        """Render a profile-owned encoding without modifying the profile."""
        features = features or AcousticFeatures()
        encoding = self._encoding_for(sound_class)
        confidence = _clip(features.confidence, 0.0, 1.0)
        urgency = _clip(features.urgency, 0.0, 1.0)
        primitive = HapticPrimitive(
            pulse_rate_hz=_clip(
                _value(encoding, "pulse_rate_hz")
                + urgency * _value(encoding, "urgency_rate_delta_hz"),
                *_BOUNDS["pulse_rate_hz"],
            ),
            intensity=scale_intensity(
                round(
                    _clip(
                        _value(encoding, "intensity") * confidence * max(0.0, features.intensity)
                        + urgency * _value(encoding, "urgency_intensity_delta"),
                        *_BOUNDS["intensity"],
                    )
                ),
                self.access_profile,
                sound_key=sound_class,
            ),
            spatial_balance=_clip(
                _value(encoding, "spatial_balance") + _clip(features.direction, -1.0, 1.0),
                *_BOUNDS["spatial_balance"],
            ),
            sharpness=_clip(
                _value(encoding, "sharpness") + urgency * _value(encoding, "urgency_sharpness_delta"),
                *_BOUNDS["sharpness"],
            ),
        )
        return RenderedSensoryMapping(
            primitive=primitive,
            silence_ms=round(_clip(_value(encoding, "silence_ms"), *_BOUNDS["silence_ms"])),
            acoustic_features=features,
        )

    def observe(self, observation: AdaptationObservation) -> bool:
        """Append a local observation and make at most one bounded refinement.

        Returns ``True`` only when the mapping changed.  Every observation is
        retained, while refinements are committed through the profile's
        SHA-256 history.
        """
        mapping = self.profile.get_adaptive_sensory_mapping()
        if not mapping.get("enabled", False):
            return False
        encoding = self._encoding_for(observation.sound_class, mapping)
        scores = {
            name: _clip(float(getattr(observation, name)), 0.0, 1.0)
            for name in (
                "perceptibility",
                "usefulness",
                "comfort",
                "motor_stability",
                "sensory_adaptation",
                "user_preference",
            )
        }
        history = mapping.setdefault("adaptation_history", [])
        history.append({"sound_class": observation.sound_class, **scores})
        policy = mapping.get("adaptation_policy", {})
        minimum = max(1, int(policy.get("minimum_observations", 3)))
        if len([item for item in history if item["sound_class"] == observation.sound_class]) < minimum:
            self.profile.set_adaptive_sensory_mapping(mapping)
            return False

        learning_rate = _clip(float(policy.get("learning_rate", 0.05)), 0.0, 0.1)
        changed = False
        if scores["comfort"] < 0.5:
            changed = self._adjust(encoding, "intensity", -learning_rate * (0.5 - scores["comfort"]) * 255.0)
        elif min(scores["perceptibility"], scores["usefulness"]) < 0.5:
            missed = 1.0 - ((scores["perceptibility"] + scores["usefulness"]) / 2.0)
            changed = self._adjust(encoding, "intensity", learning_rate * missed * 255.0)
        if scores["sensory_adaptation"] > 0.5:
            changed = self._adjust(
                encoding, "silence_ms", learning_rate * scores["sensory_adaptation"] * 500.0
            ) or changed

        self.profile.set_adaptive_sensory_mapping(mapping)
        if changed:
            self.profile.commit(
                f"Refined tactile encoding for {observation.sound_class}.",
                change_type="adaptive_sensory_mapping_refined",
                layers_changed=["haptic_layer"],
            )
        return changed

    def _encoding_for(
        self, sound_class: str, mapping: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        mapping = mapping or self.profile.get_adaptive_sensory_mapping()
        try:
            raw = mapping["sound_classes"][sound_class]
        except KeyError as exc:
            raise KeyError(f"No adaptive sensory encoding for {sound_class!r}.") from exc
        if not isinstance(raw, dict):
            raise ValueError(f"Adaptive encoding for {sound_class!r} must be an object.")
        for field in _ENCODING_FIELDS:
            if field not in raw:
                raise ValueError(f"Adaptive encoding for {sound_class!r} is missing {field!r}.")
        return raw

    @staticmethod
    def _adjust(encoding: dict[str, Any], field: str, delta: float) -> bool:
        before = _value(encoding, field)
        encoding[field] = _clip(before + delta, *_BOUNDS[field])
        return encoding[field] != before


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _value(encoding: dict[str, Any], field: str) -> float:
    return float(encoding.get(field, 0.0))


__all__ = [
    "AcousticFeatures",
    "AdaptationObservation",
    "AdaptiveSensoryMapper",
    "RenderedSensoryMapping",
]
