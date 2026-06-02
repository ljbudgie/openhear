"""
adapt.py – closed-loop, n-of-1 personalisation of entrainment protocols.

This is the honest version of "an AI tunes the beats". It is **not** an
opaque model that generates tones; generating a sine pair is trivial. The
hard, valuable part is figuring out which entrainment frequency and session
length actually work *for one specific person* — a sample size of one — and
converging on it transparently.

So this is a deterministic, bounded, explainable controller in the same
spirit as :mod:`learn.engine`: after each session the user leaves a rating
(thumbs down/neutral/up as ``-1..+1``); the controller records it and
suggests the next session by **averaging toward the settings that person
rated well**, with an **exploration nudge** when nothing has landed yet.

Two guard-rails make it trustworthy rather than mystical:

* **Stays in band.** Personalising an *alpha* protocol only ever uses and
  suggests alpha-band frequencies — it will not wander into delta.
* **Stays bounded.** Session length is clamped to a safe range; suggestions
  are reproducible from the history, so a user can see exactly why a setting
  was chosen.

Outcomes persist as JSONL (one rating per line), matching
:mod:`learn.preferences`, so phone and desktop can append without rewrites.
OpenHear is not a medical device; this learns a preference, not a treatment.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from therapy.protocol import BRAINWAVE_BANDS, TherapeuticProtocol, band_for

#: Session length is clamped to this range (seconds): 5 to 60 minutes.
MIN_SESSION_S: int = 300
MAX_SESSION_S: int = 3600

#: Default step (Hz) used when exploring for a person's sweet spot.
DEFAULT_STEP_HZ: float = 1.0

__all__ = [
    "SessionOutcome",
    "Suggestion",
    "record_outcome",
    "load_outcomes",
    "personalise",
    "MIN_SESSION_S",
    "MAX_SESSION_S",
]


@dataclass
class SessionOutcome:
    """One rated entrainment session.

    Attributes:
        beat_hz: The entrainment frequency used.
        session_length_s: How long the session ran, seconds.
        rating: The listener's response in ``[-1.0, 1.0]`` (down/neutral/up).
        goal: Optional free tag for what it was for (e.g. ``"sleep"``).
        timestamp: ISO-8601 UTC timestamp.
        notes: Free-form user notes.
    """

    beat_hz: float
    session_length_s: int
    rating: float
    goal: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )
    notes: str = ""

    def __post_init__(self) -> None:
        if self.beat_hz <= 0:
            raise ValueError("beat_hz must be positive.")
        if self.session_length_s <= 0:
            raise ValueError("session_length_s must be positive.")
        if not -1.0 <= self.rating <= 1.0:
            raise ValueError("rating must be in [-1.0, 1.0].")


@dataclass(frozen=True)
class Suggestion:
    """The controller's next-session recommendation.

    Attributes:
        beat_hz: Suggested entrainment frequency.
        session_length_s: Suggested session length, seconds.
        rationale: Plain-English reason, derived from the history.
        basis: How many in-band rated sessions informed this.
        explored: Whether this is an exploration step (vs. exploiting a
            known-good setting).
    """

    beat_hz: float
    session_length_s: int
    rationale: str
    basis: int
    explored: bool


def record_outcome(outcome: SessionOutcome, *, store_path: Path) -> None:
    """Append *outcome* to the JSONL log at *store_path*."""
    store_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(asdict(outcome), sort_keys=True, separators=(",", ":"))
    with store_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def load_outcomes(store_path: Path) -> list[SessionOutcome]:
    """Load all :class:`SessionOutcome` records from *store_path*.

    Raises:
        ValueError: If a non-blank JSONL line is malformed.
    """
    if not store_path.exists():
        return []
    outcomes: list[SessionOutcome] = []
    for line_no, line in enumerate(
        store_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                raise TypeError(f"expected object, got {type(data).__name__}")
            outcomes.append(SessionOutcome(**data))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"Invalid session outcome at {store_path}:{line_no}: {exc}"
            ) from exc
    return outcomes


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def personalise(
    protocol: TherapeuticProtocol,
    history: list[SessionOutcome],
    *,
    step_hz: float = DEFAULT_STEP_HZ,
) -> Suggestion:
    """Suggest the next session for *protocol* from a person's *history*.

    Only sessions whose ``beat_hz`` falls in the protocol's EEG band inform
    the suggestion, so personalisation never leaves the band. When the user
    has rated at least one in-band setting positively, the controller
    averages toward those settings (exploit); otherwise it nudges to a
    neighbouring frequency to keep searching (explore).

    Args:
        protocol: The protocol being personalised (gives the band and the
            cold-start defaults).
        history: All recorded outcomes (any band; filtered here).
        step_hz: Exploration step size in Hz.

    Returns:
        A :class:`Suggestion` reproducible from the history.
    """
    base_beat = protocol.frequencies[0]
    base_len = protocol.session_length_s
    band = band_for(base_beat)
    if band is None:
        # Protocol frequency outside known bands — no band to stay within.
        return Suggestion(base_beat, base_len, "Protocol frequency is outside the "
                          "standard EEG bands; leaving it unchanged.", 0, False)

    lo, hi = BRAINWAVE_BANDS[band]
    relevant = [o for o in history if lo <= o.beat_hz < hi]
    n = len(relevant)

    if n == 0:
        return Suggestion(
            base_beat,
            base_len,
            f"No personal history in the {band} band yet — starting from the "
            "protocol default.",
            0,
            False,
        )

    liked = [o for o in relevant if o.rating > 0]
    weight = sum(o.rating for o in liked)

    if weight > 0:
        beat = _clamp(sum(o.beat_hz * o.rating for o in liked) / weight, lo, hi)
        length = _clamp(
            sum(o.session_length_s * o.rating for o in liked) / weight,
            MIN_SESSION_S,
            MAX_SESSION_S,
        )
        return Suggestion(
            round(beat, 2),
            int(round(length)),
            f"Converging on {beat:.1f} Hz — the {band}-band setting your "
            f"ratings favour ({len(liked)} positive of {n}).",
            n,
            False,
        )

    # Nothing has landed yet: explore a neighbouring in-band frequency,
    # stepping away from the most recent (likely unhelpful) setting.
    last = relevant[-1].beat_hz
    candidate = last + step_hz if last + step_hz < hi else last - step_hz
    beat = _clamp(candidate, lo, hi)
    length = _clamp(float(relevant[-1].session_length_s), MIN_SESSION_S, MAX_SESSION_S)
    return Suggestion(
        round(beat, 2),
        int(round(length)),
        f"No setting has landed in {n} {band}-band session(s); exploring "
        f"{beat:.1f} Hz next.",
        n,
        True,
    )
