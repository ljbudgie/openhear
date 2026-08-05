"""Local, person-first oversight for adaptive tactile encodings.

The guardian composes an :class:`AdaptiveSensoryMapper`; it never changes the
existing rendering path or sends observations outside the Living Hearing
Profile.  It records only aggregate feedback and functional context, then
requires an explicit person-level approval before applying a proposal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from audiogram.adaptive_sensory_mapping import AdaptationObservation, AdaptiveSensoryMapper

_GUARDIAN_KEY = "iris_sensory_guardian"
_PROTECTIVE_FIELDS = {"intensity", "silence_ms"}
_BOUNDS = {"intensity": (0.0, 255.0), "silence_ms": (0.0, 5_000.0)}


@dataclass(frozen=True)
class SensoryAccessContext:
    """Local functional context that must constrain tactile adaptation."""

    fatigue: float = 0.0
    tremor: float = 0.0
    cerebral_palsy: bool = False


@dataclass(frozen=True)
class ProtectiveProposal:
    """An inspectable, unapplied or user-approved protective adjustment."""

    proposal_id: str
    sound_class: str
    adjustments: dict[str, float]
    explanation: str
    burgess_status: str
    status: str


@dataclass(frozen=True)
class GuardianReview:
    """Result of one mapper observation and its protective review."""

    mapper_refined: bool
    proposal: ProtectiveProposal | None


class IrisSensoryGuardian:
    """Person-first, local oversight process above an adaptive sensory mapper.

    The guardian preserves a class's tactile identity by limiting its own
    adjustments to intensity and intentional silence. Pulse rate, sharpness,
    spatial position, sound-class membership, and urgency semantics remain
    owned by the mapper's established language.
    """

    def __init__(self, mapper: AdaptiveSensoryMapper) -> None:
        self.mapper = mapper

    def observe(
        self,
        observation: AdaptationObservation,
        *,
        context: SensoryAccessContext | None = None,
    ) -> GuardianReview:
        """Run the existing adaptation, then inspect it for person-level drift."""
        refined = self.mapper.observe(observation)
        return self.review(observation, context=context, mapper_refined=refined)

    def review(
        self,
        observation: AdaptationObservation,
        *,
        context: SensoryAccessContext | None = None,
        mapper_refined: bool = False,
    ) -> GuardianReview:
        """Record a local review and propose a protective adjustment if needed."""
        context = context or SensoryAccessContext()
        mapping = self.mapper.profile.get_adaptive_sensory_mapping()
        guardian = _guardian_state(mapping)
        scores = _scores(observation)
        context_values = _context_values(context)
        adjustments, reasons = _protective_adjustments(
            mapping, observation.sound_class, scores, context_values
        )
        proposal = None
        if adjustments and not _has_matching_pending_proposal(
            guardian["proposals"], observation.sound_class, adjustments
        ):
            proposal_data = {
                "proposal_id": f"iris-{uuid4()}",
                "sound_class": observation.sound_class,
                "adjustments": adjustments,
                "explanation": _explanation(observation.sound_class, reasons),
                "burgess_status": "NULL",
                "status": "proposed",
            }
            guardian["proposals"].append(proposal_data)
            proposal = _proposal(proposal_data)
        guardian["memory"].append(
            {
                "event": "review",
                "timestamp": _now(),
                "sound_class": observation.sound_class,
                "scores": scores,
                "access_context": context_values,
                "mapper_refined": mapper_refined,
                "proposal_id": proposal.proposal_id if proposal else None,
                "local_only": True,
            }
        )
        self.mapper.profile.set_adaptive_sensory_mapping(mapping)
        return GuardianReview(mapper_refined=mapper_refined, proposal=proposal)

    def pending_proposals(self) -> list[ProtectiveProposal]:
        """Return locally stored proposals that still require user approval."""
        mapping = self.mapper.profile.get_adaptive_sensory_mapping()
        guardian = _guardian_state(mapping)
        return [_proposal(item) for item in guardian["proposals"] if item["status"] == "proposed"]

    def apply(self, proposal_id: str, *, user_permission: bool) -> str:
        """Apply one proposal only after an explicit user-level permission."""
        if not user_permission:
            raise PermissionError(
                "Iris will not apply a sensory adjustment without user permission."
            )
        mapping = self.mapper.profile.get_adaptive_sensory_mapping()
        guardian = _guardian_state(mapping)
        proposal = next(
            (item for item in guardian["proposals"] if item["proposal_id"] == proposal_id),
            None,
        )
        if proposal is None:
            raise KeyError(f"Unknown Iris sensory proposal {proposal_id!r}.")
        if proposal["status"] != "proposed":
            raise ValueError(
                f"Iris sensory proposal {proposal_id!r} is already {proposal['status']!r}."
            )
        encoding = mapping.get("sound_classes", {}).get(proposal["sound_class"])
        if not isinstance(encoding, dict):
            raise KeyError(f"No adaptive sensory encoding for {proposal['sound_class']!r}.")
        for field, value in proposal["adjustments"].items():
            if field not in _PROTECTIVE_FIELDS:
                raise ValueError(f"Iris cannot change tactile identity field {field!r}.")
            encoding[field] = _clip(value, *_BOUNDS[field])
        proposal["status"] = "applied"
        proposal["burgess_status"] = "SOVEREIGN"
        proposal["approved_at"] = _now()
        guardian["memory"].append(
            {
                "event": "applied",
                "timestamp": proposal["approved_at"],
                "proposal_id": proposal_id,
                "sound_class": proposal["sound_class"],
                "burgess_status": "SOVEREIGN",
                "local_only": True,
            }
        )
        self.mapper.profile.set_adaptive_sensory_mapping(mapping)
        return self.mapper.profile.commit(
            f"Iris applied a user-approved protective adjustment for {proposal['sound_class']}: "
            f"{proposal['explanation']}",
            author="Iris Sensory Guardian (user-approved)",
            change_type="iris_sensory_guardian_adjustment",
            layers_changed=["haptic_layer"],
        )


def _guardian_state(mapping: dict[str, Any]) -> dict[str, Any]:
    state = mapping.setdefault(
        _GUARDIAN_KEY,
        {"version": 1, "local_only": True, "memory": [], "proposals": []},
    )
    if not isinstance(state, dict) or state.get("local_only") is not True:
        raise ValueError("Iris Sensory Guardian state must be a local-only object.")
    state.setdefault("memory", [])
    state.setdefault("proposals", [])
    return state


def _protective_adjustments(
    mapping: dict[str, Any],
    sound_class: str,
    scores: dict[str, float],
    context: dict[str, float | bool],
) -> tuple[dict[str, float], list[str]]:
    encoding = mapping.get("sound_classes", {}).get(sound_class)
    if not isinstance(encoding, dict):
        raise KeyError(f"No adaptive sensory encoding for {sound_class!r}.")
    intensity = float(encoding["intensity"])
    silence_ms = float(encoding["silence_ms"])
    reasons: list[str] = []
    if scores["comfort"] < 0.5:
        intensity -= 25.0
        reasons.append("comfort fell below the safe threshold")
    if scores["motor_stability"] < 0.5 or context["tremor"] > 0.5:
        intensity -= 20.0
        silence_ms += 150.0
        reasons.append("motor stability or tremor made the cue harder to use")
    if context["fatigue"] > 0.5:
        intensity -= 15.0
        silence_ms += 150.0
        reasons.append("fatigue indicated a lower-effort cue")
    if context["cerebral_palsy"] and scores["motor_stability"] < 0.75:
        silence_ms += 100.0
        reasons.append("cerebral palsy context called for additional motor recovery time")
    if scores["sensory_adaptation"] > 0.5:
        silence_ms += 150.0
        reasons.append("sensory adaptation reduced the cue's distinction")
    if scores["perceptibility"] < 0.35 and scores["comfort"] >= 0.5:
        intensity += 15.0
        reasons.append("perceptibility fell below the protective threshold")
    adjustments = {
        "intensity": _clip(intensity, *_BOUNDS["intensity"]),
        "silence_ms": _clip(silence_ms, *_BOUNDS["silence_ms"]),
    }
    return (
        {field: value for field, value in adjustments.items() if value != float(encoding[field])},
        reasons,
    )


def _scores(observation: AdaptationObservation) -> dict[str, float]:
    return {
        field: _clip(float(getattr(observation, field)), 0.0, 1.0)
        for field in (
            "perceptibility",
            "usefulness",
            "comfort",
            "motor_stability",
            "sensory_adaptation",
        )
    }


def _context_values(context: SensoryAccessContext) -> dict[str, float | bool]:
    return {
        "fatigue": _clip(context.fatigue, 0.0, 1.0),
        "tremor": _clip(context.tremor, 0.0, 1.0),
        "cerebral_palsy": bool(context.cerebral_palsy),
    }


def _has_matching_pending_proposal(
    proposals: list[dict[str, Any]], sound_class: str, adjustments: dict[str, float]
) -> bool:
    return any(
        item["status"] == "proposed"
        and item["sound_class"] == sound_class
        and item["adjustments"] == adjustments
        for item in proposals
    )


def _proposal(item: dict[str, Any]) -> ProtectiveProposal:
    return ProtectiveProposal(
        proposal_id=str(item["proposal_id"]),
        sound_class=str(item["sound_class"]),
        adjustments=dict(item["adjustments"]),
        explanation=str(item["explanation"]),
        burgess_status=str(item["burgess_status"]),
        status=str(item["status"]),
    )


def _explanation(sound_class: str, reasons: list[str]) -> str:
    return (
        f"{sound_class.replace('_', ' ').capitalize()} changed because " + "; ".join(reasons) + "."
    )


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "GuardianReview",
    "IrisSensoryGuardian",
    "ProtectiveProposal",
    "SensoryAccessContext",
]
