"""
therapy package – Pillar 5, therapeutic frequency delivery for OpenHear.

This package is the first code for the therapeutic-delivery pillar described
in ``docs/HUMAN_SENSORY_SOVEREIGNTY_ARCHITECTURE.md``: programmable
frequency delivery with a *strong bias toward evidence-led protocols and
user-owned outcomes*.

It starts with binaural-beat generation, but with the angle that is actually
novel for OpenHear's users and absent from every consumer binaural-beats
app: **the listener may have hearing loss**.  A conventional binaural beat
silently fails when its two carrier tones are not equally audible in each
ear — so this package can prescribe the carrier frequency and per-ear levels
from the user's own audiogram, keeping the beat perceivable and balanced.

Honesty is a first-class feature here, not an afterthought: every protocol
carries an :class:`~therapy.protocol.EvidenceGrade`, and entrainment
protocols ship with explicit contraindication gates (e.g. seizure
disorders).  OpenHear is **not a medical device**; this is sovereign,
inspectable tooling for evidence-led self-experimentation, not treatment.
"""

from therapy.adapt import (  # noqa: F401
    SessionOutcome,
    Suggestion,
    load_outcomes,
    personalise,
    record_outcome,
)
from therapy.binaural import (  # noqa: F401
    BinauralPrescription,
    dominant_frequencies,
    generate_binaural,
    prescribe_binaural,
)
from therapy.entrainment import (  # noqa: F401
    EntrainmentEvent,
    Pulse,
    events_for_protocol,
    haptic_events,
    pulse_schedule,
)
from therapy.protocol import (  # noqa: F401
    BRAINWAVE_BANDS,
    BRAINWAVE_PROTOCOLS,
    ContraindicationError,
    EvidenceGrade,
    TherapeuticProtocol,
)

__all__ = [
    "EvidenceGrade",
    "TherapeuticProtocol",
    "ContraindicationError",
    "BRAINWAVE_BANDS",
    "BRAINWAVE_PROTOCOLS",
    "generate_binaural",
    "dominant_frequencies",
    "prescribe_binaural",
    "BinauralPrescription",
    "pulse_schedule",
    "haptic_events",
    "events_for_protocol",
    "Pulse",
    "EntrainmentEvent",
    "SessionOutcome",
    "Suggestion",
    "record_outcome",
    "load_outcomes",
    "personalise",
]
