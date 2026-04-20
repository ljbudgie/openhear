"""
engine.py – turn listener preferences into config updates (Phase 6 stub).

This is where the actual machine-learning happens: Bayesian optimisation
over the compression / voice-boost parameter space, constrained by the
safety bounds already enforced in :mod:`core.write_fitting` and the
schema in ``dsp/config.schema.json``.

Public API (all stubs):

    suggest_next_config()   — propose a new candidate YAML given history.
    update_from_feedback()  — fold a new PreferenceEvent into the model.

Until a real implementation lands, the signatures here let mobile and
desktop UIs be built against a stable contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from learn.preferences import PreferenceEvent

__all__ = [
    "EngineState",
    "suggest_next_config",
    "update_from_feedback",
]


@dataclass
class EngineState:
    """Opaque handle representing the current learning state.

    The concrete contents are deliberately unspecified so the
    implementation is free to use scikit-learn, pure NumPy, an on-device
    TFLite model, or anything else.  Callers only need to know that:

    * ``EngineState`` is serialisable to JSON (:meth:`to_json` / :meth:`from_json`).
    * ``EngineState`` is durable — the same bytes produce the same suggestions.
    """

    data: dict[str, Any]

    def to_json(self) -> str:
        raise NotImplementedError(
            "learn.engine.EngineState.to_json is a Phase 6 scaffold."
        )

    @classmethod
    def from_json(cls, text: str) -> "EngineState":
        _ = text
        raise NotImplementedError(
            "learn.engine.EngineState.from_json is a Phase 6 scaffold."
        )


def suggest_next_config(
    state: EngineState,
    *,
    base_config_path: Path,
    output_path: Path,
) -> Path:
    """Write a candidate YAML config at *output_path* and return its path.

    Raises:
        NotImplementedError: Always — implementation pending.
    """
    _ = state, base_config_path, output_path
    raise NotImplementedError(
        "learn.engine.suggest_next_config is a Phase 6 scaffold.  "
        "The suggestion algorithm must respect dsp/config.schema.json "
        "bounds and core.write_fitting.ALLOWED_PARAMETERS."
    )


def update_from_feedback(
    state: EngineState,
    event: PreferenceEvent,
) -> EngineState:
    """Return a new :class:`EngineState` folding *event* into the model.

    Raises:
        NotImplementedError: Always — implementation pending.
    """
    _ = state, event
    raise NotImplementedError(
        "learn.engine.update_from_feedback is a Phase 6 scaffold."
    )
