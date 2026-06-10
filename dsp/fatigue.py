"""
fatigue.py – fatigue-aware DSP bias (roadmap S3 → metric M6).

When the user's Whoop recovery score is low, the DSP chain should
*lighten the load* on cognition: softer compression, less aggressive
noise reduction, a touch less voice-band boost.  This module produces a
small, bounded :class:`~dsp.profile_delta.ProfileDelta` to express that
bias in a deterministic and explainable way.

Sovereignty & safety:
    * **No network I/O.**  Recovery is read from a single local JSON
      file (default ``~/.openhear/whoop_recovery.json``); the Whoop
      cloud is intentionally out of scope.  Cloud ingest is a separate,
      opt-in PR — see `SUPERIOR_HEARING_ROADMAP.md` §4.5.
    * **Deletion path.**  :func:`forget_recovery` removes the local
      file in one move; the ``python -m dsp.fatigue_cli clear`` command
      wraps it.
    * **Bounded bias.**  All deltas pass through
      :class:`~dsp.profile_delta.ProfileDelta`, which clips on
      construction.  The hardest fatigue bucket cannot push the DSP
      outside the safe envelope.
    * **Burgess Principle.**  The "red" bucket suggests a low-effort
      preset; it never silently rearms one.  The :class:`FatigueBias`
      object exposes a ``suggest_low_effort_preset`` flag for Iris or
      other surfaces to pick up.

Threshold scheme (pinned in §9 Q3 of the roadmap):

    green  : score >= 67  → no bias, training as scheduled
    yellow : 34..66       → mild bias, training as scheduled
    red    : score <= 33  → stronger bias, suggest low-effort preset
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from dsp.profile_delta import ProfileDelta

logger = logging.getLogger(__name__)

#: Canonical relative location of the local recovery file.
DEFAULT_RECOVERY_RELATIVE_PATH = Path(".openhear") / "whoop_recovery.json"

#: Environment variable that overrides the recovery file path.  Used as
#: the lowest-precedence override below the explicit ``path`` argument.
RECOVERY_FILE_ENV_VAR = "OPENHEAR_WHOOP_FILE"

#: Default §9 Q3 bucket boundaries.  Kept module-level so test code and
#: documentation can reference the same constants.
DEFAULT_GREEN_FLOOR: int = 67
DEFAULT_RED_CEILING: int = 33


def default_recovery_path() -> Path:
    """Return ``~/.openhear/whoop_recovery.json`` as a :class:`Path`."""
    return Path.home() / DEFAULT_RECOVERY_RELATIVE_PATH


def _resolve_path(path: str | Path | None) -> Path:
    if path is not None:
        return Path(os.path.expanduser(str(path)))
    env_override = os.environ.get(RECOVERY_FILE_ENV_VAR)
    if env_override:
        return Path(os.path.expanduser(env_override))
    return default_recovery_path()


# ── Buckets and dataclasses ────────────────────────────────────────────────


class RecoveryBucket(str, Enum):
    """Three-tier Whoop recovery bucket (see §9 Q3 of the roadmap).

    Inherits from ``str`` so values are JSON-serialisable and comparable
    by their lowercase name.
    """

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class WhoopRecovery:
    """A single recovery reading.

    Attributes:
        score: Whoop recovery score in the closed interval ``[0, 100]``.
        timestamp: ISO 8601 timestamp string of the reading, or empty.
        source: Free-text source tag (e.g. ``"whoop"``, ``"manual"``).
            Used only for human-readable logs; never sent off-device.
    """

    score: int
    timestamp: str = ""
    source: str = "whoop"


@dataclass(frozen=True)
class FatigueBias:
    """Resolved fatigue-aware bias ready to feed the pipeline.

    Attributes:
        bucket: The bucket the score fell into.
        delta: Bounded :class:`ProfileDelta` to add on top of the base
            DSP profile.  Identity for the "green" or "unknown" buckets.
        suggest_low_effort_preset: ``True`` only for the "red" bucket.
            Surfaces (Iris, CLI) should *suggest* a low-effort preset
            but never rearm it without explicit user confirmation —
            Burgess Principle.
        explanation: One-line human-readable summary.
    """

    bucket: RecoveryBucket
    delta: ProfileDelta
    suggest_low_effort_preset: bool
    explanation: str


# ── Public API ─────────────────────────────────────────────────────────────


def bucket(
    score: int | float | None,
    *,
    green_floor: int = DEFAULT_GREEN_FLOOR,
    red_ceiling: int = DEFAULT_RED_CEILING,
) -> RecoveryBucket:
    """Classify ``score`` into one of the three §9 Q3 buckets.

    Args:
        score: Whoop recovery score (``0``–``100``), or ``None`` for
            "unknown" (also returned for non-finite or out-of-range
            scores, with a warning logged).
        green_floor: Inclusive lower bound for the green bucket.
        red_ceiling: Inclusive upper bound for the red bucket.

    Returns:
        The matching :class:`RecoveryBucket`.

    Raises:
        ValueError: If ``red_ceiling >= green_floor`` (would leave the
            yellow band empty or inverted).
    """
    if red_ceiling >= green_floor:
        raise ValueError(f"red_ceiling ({red_ceiling}) must be < green_floor ({green_floor})")
    if score is None:
        return RecoveryBucket.UNKNOWN
    try:
        s = float(score)
    except (TypeError, ValueError):
        logger.warning("Non-numeric recovery score %r; treating as unknown.", score)
        return RecoveryBucket.UNKNOWN
    if not (0.0 <= s <= 100.0):
        logger.warning("Recovery score %s out of 0–100 range; treating as unknown.", s)
        return RecoveryBucket.UNKNOWN
    if s >= green_floor:
        return RecoveryBucket.GREEN
    if s <= red_ceiling:
        return RecoveryBucket.RED
    return RecoveryBucket.YELLOW


def fatigue_bias(
    b: RecoveryBucket,
    *,
    source_score: int | float | None = None,
) -> FatigueBias:
    """Return the :class:`FatigueBias` for a given bucket.

    The numeric values are intentionally conservative; they sit well
    inside the :mod:`dsp.profile_delta` clipping limits so future
    composition with per-contact deltas (and any other source) cannot
    blow past the safe envelope.

    Args:
        b: The bucket from :func:`bucket`.
        source_score: Optional original score, woven into the
            explanation string for the user.

    Returns:
        A :class:`FatigueBias`.  Green/unknown return the identity
        delta and do **not** suggest a low-effort preset.
    """
    score_str = f"{int(source_score)}" if source_score is not None else "?"
    if b is RecoveryBucket.GREEN:
        return FatigueBias(
            bucket=b,
            delta=ProfileDelta(),
            suggest_low_effort_preset=False,
            explanation=(f"Whoop recovery {score_str} = green; no fatigue bias applied."),
        )
    if b is RecoveryBucket.UNKNOWN:
        return FatigueBias(
            bucket=b,
            delta=ProfileDelta(),
            suggest_low_effort_preset=False,
            explanation=(
                "Whoop recovery unknown; no fatigue bias applied (Burgess Principle: "
                "no inference without data)."
            ),
        )
    if b is RecoveryBucket.YELLOW:
        # Mild bias: ease compression and NR a touch.
        delta = ProfileDelta(
            compression_ratio_delta=-0.1,
            compression_knee_delta_db=1.0,
            voice_gain_delta=-0.05,
            nr_aggressiveness_delta=-0.05,
            sources=("fatigue:yellow",),
            reason="mild fatigue bias",
        )
        return FatigueBias(
            bucket=b,
            delta=delta,
            suggest_low_effort_preset=False,
            explanation=(f"Whoop recovery {score_str} = yellow; applying mild fatigue bias."),
        )
    # RED
    delta = ProfileDelta(
        compression_ratio_delta=-0.25,
        compression_knee_delta_db=2.5,
        voice_gain_delta=-0.1,
        nr_aggressiveness_delta=-0.15,
        sources=("fatigue:red",),
        reason="stronger fatigue bias",
    )
    return FatigueBias(
        bucket=b,
        delta=delta,
        suggest_low_effort_preset=True,
        explanation=(
            f"Whoop recovery {score_str} = red; applying stronger fatigue bias "
            "and SUGGESTING a low-effort preset (user must confirm — Burgess Principle)."
        ),
    )


def read_recovery(path: str | Path | None = None) -> WhoopRecovery | None:
    """Read the local recovery file, returning ``None`` if absent.

    The file is expected to be a JSON object of the form::

        {"score": 64, "timestamp": "2026-06-10T07:00:00Z", "source": "whoop"}

    Args:
        path: Explicit override; otherwise the env var
            :data:`RECOVERY_FILE_ENV_VAR` and then
            :func:`default_recovery_path` are consulted in order.

    Returns:
        A :class:`WhoopRecovery`, or ``None`` if the file does not
        exist.  A malformed file raises :class:`ValueError` (so the
        user notices) — but a missing file is silent (the disabled
        default path).
    """
    target = _resolve_path(path)
    if not target.exists():
        logger.debug("No recovery file at %s.", target)
        return None
    text = target.read_text(encoding="utf-8")
    if not text.strip():
        return None
    data = json.loads(text)
    if not isinstance(data, Mapping):
        raise ValueError(
            f"{target}: recovery file root must be a JSON object, got {type(data).__name__}."
        )
    score = data.get("score")
    if score is None:
        raise ValueError(f"{target}: recovery file is missing required 'score' field.")
    try:
        score_int = int(score)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{target}: 'score' must be an integer 0–100.") from exc
    if not 0 <= score_int <= 100:
        raise ValueError(f"{target}: 'score' must be 0–100, got {score_int}.")
    return WhoopRecovery(
        score=score_int,
        timestamp=str(data.get("timestamp", "")),
        source=str(data.get("source", "whoop")),
    )


def write_recovery(
    recovery: WhoopRecovery,
    path: str | Path | None = None,
) -> Path:
    """Write a :class:`WhoopRecovery` atomically to disk.

    The parent directory is created with mode ``0o700`` and the file
    written with mode ``0o600`` where the OS supports it — this is
    sensitive health data per `SECURITY.md`.

    Args:
        recovery: The reading to persist.
        path: Explicit override; otherwise follows the same resolution
            order as :func:`read_recovery`.

    Returns:
        The resolved :class:`Path` written.
    """
    target = _resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload: dict[str, Any] = {
        "score": int(recovery.score),
        "timestamp": recovery.timestamp,
        "source": recovery.source,
    }
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        logger.debug("Could not chmod %s (non-POSIX filesystem?)", tmp)
    tmp.replace(target)
    return target


def forget_recovery(path: str | Path | None = None) -> bool:
    """Delete the local recovery file if it exists.

    Returns:
        ``True`` if a file was removed, ``False`` if there was nothing
        to remove.  Either outcome is safe to repeat.
    """
    target = _resolve_path(path)
    if not target.exists():
        return False
    target.unlink()
    logger.info("BGSP|fatigue-recovery-forgotten|%s", target)
    return True


def fatigue_delta_from_file(
    path: str | Path | None = None,
    *,
    green_floor: int = DEFAULT_GREEN_FLOOR,
    red_ceiling: int = DEFAULT_RED_CEILING,
) -> ProfileDelta:
    """Pipeline entry point: load recovery, classify, return the delta.

    This is what :mod:`dsp.pipeline` calls when ``--fatigue`` is set.
    A missing or malformed file results in the identity delta with a
    log warning (never an exception) — the pipeline must keep running.

    Args:
        path: Override for the recovery file location.
        green_floor / red_ceiling: Bucket boundaries.

    Returns:
        A bounded :class:`ProfileDelta`.  The identity delta is
        returned for green, unknown, missing, or malformed inputs.
    """
    try:
        recovery = read_recovery(path)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not read recovery file (%s); fatigue bias disabled.", exc)
        return ProfileDelta()
    if recovery is None:
        return ProfileDelta()
    b = bucket(recovery.score, green_floor=green_floor, red_ceiling=red_ceiling)
    bias = fatigue_bias(b, source_score=recovery.score)
    if bias.suggest_low_effort_preset:
        # Surface the suggestion; user/Iris decides whether to act.
        logger.warning("BGSP|fatigue-low-effort-suggested|%s", bias.explanation)
    if not bias.delta.is_identity():
        logger.info("BGSP|fatigue-bias-applied|%s", bias.delta.explain())
    return bias.delta
