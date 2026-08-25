"""
dermal_profiles.py – Pillar 5 haptic profiles in the 30–100 Hz (gamma) range.

⚠️  EXPERIMENTAL — NOT A MEDICAL DEVICE.  These profiles are sovereign,
inspectable parameters for evidence-led self-experimentation.  They do
**not** diagnose, treat, or cure any condition.  The mechanoreceptor
references below are descriptive of the published biophysics literature, not
claims that using these frequencies will produce any particular biological
outcome in a given person.  Consult a medical professional before using any
frequency-delivery tool for a health purpose.

Background
----------
The 30–100 Hz range spans the gamma EEG band and coincides with the
sensitivity peaks of two well-characterised cutaneous mechanoreceptors:

* **Meissner's corpuscles** — concentrated in glabrous (hairless) skin,
  most sensitive around 20–50 Hz; respond to light touch and texture.
* **Pacinian corpuscles** — found in deeper dermis and subcutaneous tissue,
  most sensitive around 200–300 Hz but responsive from ~40 Hz upward;
  respond to vibration and rapid transients.

The profiles here are frequency bands within the wristband's haptic
capability, not tuned instruments for any specific receptor subtype.

Safety constraints (enforced here, not just documented)
--------------------------------------------------------
* ``MAX_SESSION_S = 1200`` — 20-minute hard ceiling.  Prolonged mechanical
  vibration on one skin site can cause numbness or adaptation; the ceiling
  prevents accidental over-exposure.
* ``MAX_AMPLITUDE`` — kept below the wristband firmware intensity ceiling
  (180 / 255) and below a conservative haptic-comfort threshold.
* Every profile carries ``EvidenceGrade.ANECDOTAL``; no bundled preset
  claims replicated clinical evidence for a dermal effect.
* Contraindications include open wounds / skin conditions at the contact
  site — the user must declare these so the gate can refuse to run.

All data stays local; this module has no network I/O.  The companion
``therapy/adapt.py`` JSONL logger can be used to record session outcomes
in ``~/.openhear/therapy/``.
"""

from __future__ import annotations

from dataclasses import dataclass

from therapy.protocol import (
    ContraindicationError,
    EvidenceGrade,
    TherapeuticProtocol,
)

# ── Safety constants ─────────────────────────────────────────────────────────

#: Hard maximum session length in seconds (20 minutes).
MAX_SESSION_S: int = 1200

#: Recommended amplitude for dermal profiles (0–255).
#: Kept well below the firmware ceiling of 180 to prioritise comfort over
#: intensity for long-contact sessions.
MAX_AMPLITUDE: int = 120

#: Default duty cycle for dermal profiles.  50 % gives a clear on/off rhythm
#: without continuous vibration on the skin site.
DEFAULT_DUTY_CYCLE: float = 0.5

# ── Contraindication sets ────────────────────────────────────────────────────

#: Conditions that are contraindicated for any haptic contact at the skin site.
_SKIN_CONTRAINDICATIONS: frozenset[str] = frozenset(
    {
        "open_wound",
        "open wound",
        "skin_infection",
        "skin infection",
        "dermatitis_at_contact_site",
        "dermatitis at contact site",
        "raynaud_syndrome",
        "raynaud syndrome",
        "peripheral_neuropathy",
        "peripheral neuropathy",
        "deep_vein_thrombosis",
        "deep vein thrombosis",
        "pregnancy",          # vibration over abdomen / extremity caution
    }
)


# ── DermalProfile wrapper ────────────────────────────────────────────────────


@dataclass(frozen=True)
class DermalProfile:
    """A haptic exploration profile for the 30–100 Hz range.

    Wraps a :class:`~therapy.protocol.TherapeuticProtocol` with
    dermal-specific metadata and enforces the 20-minute session ceiling.

    Attributes:
        protocol: The underlying delivery protocol.
        receptor_context: Human-readable note on which mechanoreceptor
            subtype is most sensitive in this frequency band, for reference
            only — **not a claim of therapeutic effect**.
        recommended_amplitude: Suggested wristband intensity byte (0–255).
            Always at or below :data:`MAX_AMPLITUDE`.
    """

    protocol: TherapeuticProtocol
    receptor_context: str
    recommended_amplitude: int

    def __post_init__(self) -> None:
        if self.protocol.session_length_s > MAX_SESSION_S:
            raise ValueError(
                f"Dermal profile '{self.protocol.name}' has "
                f"session_length_s={self.protocol.session_length_s} which exceeds "
                f"the 20-minute safety ceiling ({MAX_SESSION_S} s)."
            )
        if not 0 <= self.recommended_amplitude <= MAX_AMPLITUDE:
            raise ValueError(
                f"recommended_amplitude must be in [0, {MAX_AMPLITUDE}]; "
                f"got {self.recommended_amplitude}."
            )

    def gate(self, conditions: frozenset[str] | set[str]) -> None:
        """Refuse to run if any declared condition is contraindicated.

        Delegates to the underlying :meth:`~therapy.protocol.TherapeuticProtocol.gate`.

        Args:
            conditions: The user's declared health conditions.

        Raises:
            ContraindicationError: If a contraindicated condition is present.
        """
        self.protocol.gate(conditions)


# ── Bundled profiles ─────────────────────────────────────────────────────────

#: Registry of dermal haptic exploration profiles, keyed by short name.
#: All are graded :attr:`~therapy.protocol.EvidenceGrade.ANECDOTAL`.
#: ``target_outcomes`` describe what each is *explored for*, not what it does.
DERMAL_PROFILES: dict[str, DermalProfile] = {
    "gamma_low": DermalProfile(
        protocol=TherapeuticProtocol(
            name="Gamma low — 30 Hz haptic exploration",
            frequencies=(30.0,),
            carrier_shape="sine",
            duty_cycle=DEFAULT_DUTY_CYCLE,
            session_length_s=600,           # 10 minutes
            evidence_grade=EvidenceGrade.ANECDOTAL,
            contraindications=_SKIN_CONTRAINDICATIONS,
            target_outcomes=("superficial mechanoreceptor stimulation exploration",),
            washout_period_s=1800,
        ),
        receptor_context=(
            "30 Hz falls within the upper sensitivity range of Meissner's "
            "corpuscles (glabrous skin, ~20–50 Hz peak). Reference only — no "
            "therapeutic claim is made."
        ),
        recommended_amplitude=80,
    ),
    "gamma_mid": DermalProfile(
        protocol=TherapeuticProtocol(
            name="Gamma mid — 50 Hz haptic exploration",
            frequencies=(50.0,),
            carrier_shape="sine",
            duty_cycle=DEFAULT_DUTY_CYCLE,
            session_length_s=600,
            evidence_grade=EvidenceGrade.ANECDOTAL,
            contraindications=_SKIN_CONTRAINDICATIONS,
            target_outcomes=("mixed-receptor haptic exploration",),
            washout_period_s=1800,
        ),
        receptor_context=(
            "50 Hz sits at the crossover where Meissner sensitivity is "
            "declining and Pacinian corpuscle sensitivity (deep dermis, "
            "peak ~200–300 Hz) begins to contribute. Reference only — no "
            "therapeutic claim is made."
        ),
        recommended_amplitude=100,
    ),
    "gamma_high": DermalProfile(
        protocol=TherapeuticProtocol(
            name="Gamma high — 100 Hz haptic exploration",
            frequencies=(100.0,),
            carrier_shape="sine",
            duty_cycle=DEFAULT_DUTY_CYCLE,
            session_length_s=600,
            evidence_grade=EvidenceGrade.ANECDOTAL,
            contraindications=_SKIN_CONTRAINDICATIONS,
            target_outcomes=("deep mechanoreceptor haptic exploration",),
            washout_period_s=1800,
        ),
        receptor_context=(
            "100 Hz is within the rising slope of Pacinian corpuscle "
            "sensitivity (deep dermis / subcutaneous tissue). Reference "
            "only — no therapeutic claim is made."
        ),
        recommended_amplitude=120,
    ),
}


def get_dermal_profile(key: str) -> DermalProfile:
    """Return a bundled dermal profile by key, with a helpful error otherwise.

    Args:
        key: One of the keys in :data:`DERMAL_PROFILES`.

    Returns:
        The requested :class:`DermalProfile`.

    Raises:
        KeyError: If *key* is not in the registry.
    """
    try:
        return DERMAL_PROFILES[key]
    except KeyError as exc:
        raise KeyError(
            f"Unknown dermal profile {key!r}. Available: "
            f"{', '.join(sorted(DERMAL_PROFILES))}."
        ) from exc


__all__ = [
    "MAX_SESSION_S",
    "MAX_AMPLITUDE",
    "DEFAULT_DUTY_CYCLE",
    "DermalProfile",
    "DERMAL_PROFILES",
    "get_dermal_profile",
]
