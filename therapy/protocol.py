"""
protocol.py – the evidence-graded, safety-gated therapeutic protocol model.

Implements the ``TherapeuticProtocol`` data model specified for Pillar 5 in
``docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md`` and the runtime
constraints around it: amplitudes stay below safety ceilings (enforced in
:mod:`therapy.binaural`), and **contraindication gates are explicit in the
protocol files** — enforced here.

Two principles shape this module:

* **Honesty about evidence.**  Brainwave-entrainment claims range from
  plausible to overstated; the literature is mixed.  Rather than launder
  that uncertainty, every protocol carries an explicit
  :class:`EvidenceGrade`, and the bundled presets are graded
  conservatively.  OpenHear is not a medical device and these are not
  treatments — they are inspectable parameters for evidence-led,
  user-owned self-experimentation.
* **Safety is a gate, not a footnote.**  Auditory/visual entrainment is
  contraindicated for people with seizure disorders; protocols declare
  their contraindications and :meth:`TherapeuticProtocol.gate` refuses to
  run when the user's declared conditions intersect them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class EvidenceGrade(IntEnum):
    """How well-supported a protocol's claimed effect is, low to high.

    Ordered so callers can compare (``grade >= EvidenceGrade.EMERGING``).
    Deliberately conservative: most consumer entrainment claims do not rise
    above :attr:`PRELIMINARY`.
    """

    ANECDOTAL = 0      # user reports / tradition only
    PRELIMINARY = 1    # small or mixed studies, not replicated
    EMERGING = 2       # replicated signal, active research, not settled
    ESTABLISHED = 3    # broad, consistent clinical evidence

    @property
    def label(self) -> str:
        return self.name.lower()


class ContraindicationError(RuntimeError):
    """Raised when a protocol is run against a contraindicated condition."""


#: Standard EEG band ranges in Hz (inclusive lower, exclusive upper),
#: provided as honest reference — not a promise that entraining a band
#: produces the lay association below it.
BRAINWAVE_BANDS: dict[str, tuple[float, float]] = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 100.0),
}


def band_for(frequency_hz: float) -> str | None:
    """Return the EEG band name containing *frequency_hz*, or ``None``."""
    for name, (lo, hi) in BRAINWAVE_BANDS.items():
        if lo <= frequency_hz < hi:
            return name
    return None


@dataclass(frozen=True)
class TherapeuticProtocol:
    """A frequency-delivery protocol with evidence and safety metadata.

    Mirrors the Pillar 5 data model.  ``frequencies`` are the entrainment
    (beat) frequencies in Hz — not the audio carrier, which is chosen at
    render time (and may be audiogram-personalised; see
    :func:`therapy.binaural.prescribe_binaural`).

    Attributes:
        name: Human-readable protocol name.
        frequencies: Entrainment frequencies in Hz (each > 0).
        carrier_shape: Waveform of the carrier (e.g. ``"sine"``).
        duty_cycle: Fraction of each cycle that is active, in ``(0, 1]``.
        session_length_s: Intended session length in seconds (> 0).
        evidence_grade: How well-supported the claimed effect is.
        contraindications: Conditions for which this must not be run.
        target_outcomes: What the protocol is *explored* for (not promised).
        washout_period_s: Recommended gap before re-running, seconds (>= 0).
        allowed_sleep_stages: Sleep stages during which delivery is allowed
            (empty means "no sleep-stage restriction declared").
    """

    name: str
    frequencies: tuple[float, ...]
    carrier_shape: str = "sine"
    duty_cycle: float = 1.0
    session_length_s: int = 600
    evidence_grade: EvidenceGrade = EvidenceGrade.ANECDOTAL
    contraindications: frozenset[str] = frozenset()
    target_outcomes: tuple[str, ...] = ()
    washout_period_s: int = 0
    allowed_sleep_stages: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.frequencies:
            raise ValueError("A protocol needs at least one frequency.")
        if any(f <= 0 for f in self.frequencies):
            raise ValueError("All frequencies must be positive.")
        if not 0.0 < self.duty_cycle <= 1.0:
            raise ValueError("duty_cycle must be in (0, 1].")
        if self.session_length_s <= 0:
            raise ValueError("session_length_s must be positive.")
        if self.washout_period_s < 0:
            raise ValueError("washout_period_s must be non-negative.")

    def is_contraindicated(self, conditions: frozenset[str] | set[str]) -> bool:
        """Whether any declared *conditions* intersect the contraindications."""
        normalised = {c.lower().strip() for c in conditions}
        return bool(normalised & {c.lower() for c in self.contraindications})

    def gate(self, conditions: frozenset[str] | set[str]) -> None:
        """Raise :class:`ContraindicationError` if *conditions* are barred.

        Call this before running a protocol for a user who has declared any
        health conditions.

        Raises:
            ContraindicationError: If a contraindicated condition is present.
        """
        normalised = {c.lower().strip() for c in conditions}
        hit = sorted(normalised & {c.lower() for c in self.contraindications})
        if hit:
            raise ContraindicationError(
                f"Protocol {self.name!r} is contraindicated for: "
                f"{', '.join(hit)}. It will not be run."
            )


# Entrainment (auditory/visual/haptic) is contraindicated for seizure
# disorders; that gate is non-negotiable on every bundled protocol.
_SEIZURE: frozenset[str] = frozenset({"epilepsy", "seizure_disorder", "photosensitive_epilepsy"})


#: A small registry of honestly-graded brainwave protocols. The lay
#: associations in ``target_outcomes`` are what each is *explored for*, not
#: claims — and the conservative evidence grades say so.
BRAINWAVE_PROTOCOLS: dict[str, TherapeuticProtocol] = {
    "delta_sleep": TherapeuticProtocol(
        name="Delta — deep-rest exploration",
        frequencies=(2.0,),
        session_length_s=1800,
        evidence_grade=EvidenceGrade.PRELIMINARY,
        contraindications=_SEIZURE,
        target_outcomes=("relaxation", "sleep-onset exploration"),
        washout_period_s=3600,
    ),
    "theta_meditation": TherapeuticProtocol(
        name="Theta — meditative-state exploration",
        frequencies=(6.0,),
        session_length_s=1200,
        evidence_grade=EvidenceGrade.PRELIMINARY,
        contraindications=_SEIZURE,
        target_outcomes=("relaxation", "meditation support"),
        washout_period_s=1800,
    ),
    "alpha_relax": TherapeuticProtocol(
        name="Alpha — calm-focus exploration",
        frequencies=(10.0,),
        session_length_s=900,
        evidence_grade=EvidenceGrade.EMERGING,
        contraindications=_SEIZURE,
        target_outcomes=("relaxation", "calm alertness"),
        washout_period_s=1800,
    ),
    "beta_focus": TherapeuticProtocol(
        name="Beta — alert-focus exploration",
        frequencies=(18.0,),
        session_length_s=900,
        evidence_grade=EvidenceGrade.PRELIMINARY,
        contraindications=_SEIZURE,
        target_outcomes=("focus exploration",),
        washout_period_s=1800,
    ),
    "gamma_40hz": TherapeuticProtocol(
        name="Gamma 40 Hz — research-grade entrainment",
        frequencies=(40.0,),
        session_length_s=3600,
        evidence_grade=EvidenceGrade.EMERGING,
        contraindications=_SEIZURE,
        target_outcomes=("40 Hz entrainment research",),
        washout_period_s=3600,
    ),
}


def get_protocol(key: str) -> TherapeuticProtocol:
    """Return a bundled protocol by key, with a helpful error otherwise."""
    try:
        return BRAINWAVE_PROTOCOLS[key]
    except KeyError as exc:
        raise KeyError(
            f"Unknown protocol {key!r}. Available: "
            f"{', '.join(sorted(BRAINWAVE_PROTOCOLS))}."
        ) from exc


# Keep field() importable for callers extending the registry.
__all__ = [
    "EvidenceGrade",
    "ContraindicationError",
    "TherapeuticProtocol",
    "BRAINWAVE_BANDS",
    "BRAINWAVE_PROTOCOLS",
    "band_for",
    "get_protocol",
]
