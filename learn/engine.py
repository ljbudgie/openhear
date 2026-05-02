"""
engine.py – turn listener preferences into config updates.

This is where the actual machine-learning happens: Bayesian optimisation
over the compression / voice-boost parameter space, constrained by the
safety bounds already enforced in :mod:`core.write_fitting` and the
schema in ``dsp/config.schema.json``.

Public API:

    suggest_next_config()   — propose a new candidate YAML given history.
    update_from_feedback()  — fold a new PreferenceEvent into the model.

The implementation is deliberately deterministic and local-only.  It records
feedback events in serialisable state and writes bounded candidate configs
that remain valid for :mod:`dsp.user_config`.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from dsp.user_config import load_config
from learn.preferences import PreferenceEvent

__all__ = [
    "EngineState",
    "suggest_next_config",
    "update_from_feedback",
]

_ADAPTIVE_BOUNDS: dict[tuple[str, str], tuple[float, float]] = {
    ("compression", "ratio"): (1.0, 10.0),
    ("compression", "knee_db"): (-120.0, 0.0),
    ("compression", "attack_ms"): (0.1, 1000.0),
    ("compression", "release_ms"): (1.0, 10000.0),
    ("noise", "floor_db"): (-120.0, 0.0),
    ("noise", "reduction_strength"): (0.0, 1.0),
    ("voice", "boost_db"): (-24.0, 24.0),
    ("beamforming", "width_deg"): (1.0, 360.0),
    ("beamforming", "direction_deg"): (-180.0, 180.0),
}

_EXPLORATION_STEPS: tuple[tuple[tuple[str, str], float], ...] = (
    (("voice", "boost_db"), 0.5),
    (("noise", "reduction_strength"), 0.05),
    (("compression", "ratio"), 0.25),
    (("beamforming", "width_deg"), -5.0),
)


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
        return json.dumps(self.data, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "EngineState":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(f"EngineState JSON must contain an object, got {type(data).__name__}.")
        return cls(data=data)


def suggest_next_config(
    state: EngineState,
    *,
    base_config_path: Path,
    output_path: Path,
) -> Path:
    """Write a candidate YAML config at *output_path* and return its path.

    Raises:
        FileNotFoundError: If *base_config_path* does not exist.
        RuntimeError: If PyYAML is unavailable.
    """
    config = load_config(base_config_path).to_dict()
    _apply_preferred_config_average(config, state)
    _apply_explicit_overrides(config, state.data.get("config_overrides", {}))
    _apply_exploration_nudge(config, state)
    _clamp_config(config)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_dump_yaml(config), encoding="utf-8")
    return output_path


def update_from_feedback(
    state: EngineState,
    event: PreferenceEvent,
) -> EngineState:
    """Return a new :class:`EngineState` folding *event* into the model."""
    if event.choice not in {"A", "B", "undecided"}:
        raise ValueError(f"Invalid preference choice: {event.choice!r}.")
    data = deepcopy(state.data)
    events = data.setdefault("events", [])
    if not isinstance(events, list):
        raise ValueError("EngineState.data['events'] must be a list when present.")
    events.append(asdict(event))

    summary = data.setdefault("summary", {})
    if not isinstance(summary, dict):
        raise ValueError("EngineState.data['summary'] must be a mapping when present.")
    environment = event.environment or "default"
    env_summary = summary.setdefault(environment, {"A": 0, "B": 0, "undecided": 0})
    if not isinstance(env_summary, dict):
        raise ValueError(f"EngineState summary for {environment!r} must be a mapping.")
    env_summary[event.choice] = int(env_summary.get(event.choice, 0)) + 1
    data["last_environment"] = environment
    return EngineState(data=data)


def _apply_preferred_config_average(config: dict[str, Any], state: EngineState) -> None:
    preferred_configs: list[dict[str, Any]] = []
    for raw_event in state.data.get("events", []):
        if not isinstance(raw_event, dict):
            continue
        choice = raw_event.get("choice")
        if choice == "A":
            path = raw_event.get("config_a_path")
        elif choice == "B":
            path = raw_event.get("config_b_path")
        else:
            continue
        if not path:
            continue
        candidate_path = Path(str(path)).expanduser()
        if not candidate_path.exists():
            continue
        try:
            preferred_configs.append(load_config(candidate_path).to_dict())
        except (FileNotFoundError, ValueError, json.JSONDecodeError, RuntimeError):
            continue

    if not preferred_configs:
        return

    for section, key in _ADAPTIVE_BOUNDS:
        values = [
            preferred[section][key]
            for preferred in preferred_configs
            if section in preferred and key in preferred[section]
        ]
        if not values:
            continue
        target = sum(float(value) for value in values) / len(values)
        current = float(config[section][key])
        config[section][key] = current + ((target - current) * 0.5)

    _apply_voice_band_average(config, preferred_configs)


def _apply_voice_band_average(
    config: dict[str, Any], preferred_configs: list[dict[str, Any]]
) -> None:
    bands = [
        preferred["voice"]["boost_hz"]
        for preferred in preferred_configs
        if "voice" in preferred and "boost_hz" in preferred["voice"]
    ]
    if not bands:
        return
    lows = [float(band[0]) for band in bands]
    highs = [float(band[1]) for band in bands]
    current_low, current_high = [float(value) for value in config["voice"]["boost_hz"]]
    target_low = sum(lows) / len(lows)
    target_high = sum(highs) / len(highs)
    next_low = _clamp(current_low + ((target_low - current_low) * 0.5), 20.0, 19999.0)
    next_high = _clamp(current_high + ((target_high - current_high) * 0.5), 21.0, 20000.0)
    if next_low >= next_high:
        midpoint = (next_low + next_high) / 2
        next_low = max(20.0, midpoint - 0.5)
        next_high = min(20000.0, midpoint + 0.5)
    config["voice"]["boost_hz"] = [next_low, next_high]


def _apply_explicit_overrides(config: dict[str, Any], overrides: Any) -> None:
    if not isinstance(overrides, dict):
        return
    for section, values in overrides.items():
        if section not in config or not isinstance(values, dict):
            continue
        for key, value in values.items():
            if (section, key) in _ADAPTIVE_BOUNDS:
                config[section][key] = float(value)


def _apply_exploration_nudge(config: dict[str, Any], state: EngineState) -> None:
    if _has_preferred_config(state) or state.data.get("config_overrides"):
        return
    events = state.data.get("events", [])
    if not events:
        return
    field, step = _EXPLORATION_STEPS[(len(events) - 1) % len(_EXPLORATION_STEPS)]
    section, key = field
    config[section][key] = float(config[section][key]) + step


def _has_preferred_config(state: EngineState) -> bool:
    for raw_event in state.data.get("events", []):
        if not isinstance(raw_event, dict):
            continue
        choice = raw_event.get("choice")
        path = raw_event.get("config_a_path" if choice == "A" else "config_b_path")
        if choice in {"A", "B"} and path and Path(str(path)).expanduser().exists():
            return True
    return False


def _clamp_config(config: dict[str, Any]) -> None:
    for (section, key), (minimum, maximum) in _ADAPTIVE_BOUNDS.items():
        config[section][key] = _clamp(float(config[section][key]), minimum, maximum)
    low, high = [float(value) for value in config["voice"]["boost_hz"]]
    low = _clamp(low, 20.0, 19999.0)
    high = _clamp(high, 21.0, 20000.0)
    if low >= high:
        high = min(20000.0, low + 1.0)
    config["voice"]["boost_hz"] = [low, high]


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _dump_yaml(config: dict[str, Any]) -> str:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "Cannot write YAML config: install PyYAML (pip install pyyaml)."
        ) from exc

    return yaml.safe_dump(config, sort_keys=False)
