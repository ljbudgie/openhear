"""
explain.py – plain-English explanation of your own hearing-aid fitting.

:mod:`dsp.audiogram_profile` turns an audiogram into a
:class:`~dsp.audiogram_profile.Prescription` — per-band gains, compression
ratios, and knee points.  Those numbers are correct, but they are not an
*answer* to the question a person actually has:

    "What is this fitting doing to the sound I hear, and why?"

Commercial fitting software (Phonak Target, Signia Connexx, Starkey Pro
Fit) computes the same kind of prescription and then shows it only to the
clinician.  The wearer — whose ears these are — never sees the reasoning.

This module closes that gap.  It joins the prescription with the
audiogram *configuration* from :mod:`audiogram.analyse` and renders a
sovereign, plain-language account: where the fitting adds the most help,
why (tied to the shape of your loss), and how hard it is working to tame
loud sounds.  It is an explanation you own — not a diagnosis, and not a
substitute for professional verification.

Deterministic and pure: it reads an :class:`~audiogram.audiogram.Audiogram`
and returns dataclasses, so every sentence it can produce is unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass

from audiogram.analyse import analyse
from audiogram.audiogram import Audiogram
from dsp.audiogram_profile import Prescription, prescribe

#: A compression ratio at or above this is described as "actively taming"
#: loud sounds, versus gentle/near-linear amplification below it.
_ACTIVE_COMPRESSION_RATIO: float = 1.8

#: A band carrying at least this much gain is called out as a focus area.
_NOTABLE_GAIN_DB: float = 5.0


@dataclass
class EarFitting:
    """Plain-English-ready summary of one ear's fitting.

    Attributes:
        ear: ``"left"`` or ``"right"``.
        configuration: Audiometric shape from :mod:`audiogram.analyse`.
        peak_gain_freq: Frequency (Hz) receiving the most gain, or
            ``None`` when no band is prescribed (insufficient data).
        peak_gain_db: Gain at ``peak_gain_freq`` in dB.
        mean_gain_db: Mean prescribed gain across all bands, dB.
        max_ratio: Highest WDRC compression ratio across bands, or
            ``None`` when no band is prescribed.
    """

    ear: str
    configuration: str
    peak_gain_freq: int | None
    peak_gain_db: float
    mean_gain_db: float
    max_ratio: float | None


@dataclass
class FittingExplanation:
    """A bilateral, plain-English-ready explanation of a fitting."""

    left: EarFitting
    right: EarFitting
    method: str

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dict of this explanation."""
        return {
            "method": self.method,
            "left": vars(self.left),
            "right": vars(self.right),
        }


def _explain_ear(prescription: Prescription, configuration: str, ear: str) -> EarFitting:
    gains = prescription.gains_db(ear)
    ratios = prescription.ratios(ear)

    if not gains:
        return EarFitting(
            ear=ear,
            configuration=configuration,
            peak_gain_freq=None,
            peak_gain_db=0.0,
            mean_gain_db=0.0,
            max_ratio=None,
        )

    peak_freq = max(gains, key=lambda f: gains[f])
    return EarFitting(
        ear=ear,
        configuration=configuration,
        peak_gain_freq=peak_freq,
        peak_gain_db=round(gains[peak_freq], 1),
        mean_gain_db=round(sum(gains.values()) / len(gains), 1),
        max_ratio=round(max(ratios.values()), 2) if ratios else None,
    )


def explain(audiogram: Audiogram) -> FittingExplanation:
    """Explain the fitting OpenHear would prescribe for ``audiogram``.

    Args:
        audiogram: The bilateral audiogram to fit and explain.

    Returns:
        A :class:`FittingExplanation`.
    """
    prescription = prescribe(audiogram)
    shapes = analyse(audiogram)
    return FittingExplanation(
        left=_explain_ear(prescription, shapes.left.configuration, "left"),
        right=_explain_ear(prescription, shapes.right.configuration, "right"),
        method=prescription.method,
    )


# ── Plain-English rendering ─────────────────────────────────────────────────

_FREQ_LABEL: dict[int, str] = {
    250: "the low rumble (250 Hz)",
    500: "the low pitches (500 Hz)",
    1000: "the low-mids (1 kHz)",
    2000: "the mid pitches (2 kHz)",
    4000: "the high pitches (4 kHz)",
    6000: "the high detail (6 kHz)",
    8000: "the top end (8 kHz)",
}


def _freq_phrase(freq: int) -> str:
    return _FREQ_LABEL.get(freq, f"{freq} Hz")


def _ear_paragraph(fit: EarFitting) -> str:
    name = fit.ear.capitalize()
    if fit.peak_gain_freq is None:
        return (
            f"{name} ear: not enough frequencies were measured to prescribe a "
            "fitting yet."
        )
    if fit.peak_gain_db < _NOTABLE_GAIN_DB:
        lead = (
            f"{name} ear: your hearing is close enough to typical that the "
            "fitting adds little — only a touch of gain"
        )
    else:
        lead = (
            f"{name} ear: the fitting adds the most help at "
            f"{_freq_phrase(fit.peak_gain_freq)} (+{fit.peak_gain_db:.0f} dB), "
            f"averaging +{fit.mean_gain_db:.0f} dB across the range"
        )

    # Tie the focus back to the shape of the loss.
    if fit.configuration == "sloping":
        why = (
            ", because your loss slopes toward the high pitches where "
            "consonants and clarity live"
        )
    elif fit.configuration == "reverse-sloping":
        why = ", because your loss sits in the low pitches this time"
    elif fit.configuration == "notched":
        why = ", concentrated around the noise-related dip in your high pitches"
    elif fit.configuration == "cookie-bite":
        why = ", focused on the mid pitches where your loss is greatest"
    elif fit.configuration == "flat":
        why = ", spread fairly evenly because your loss is similar across pitches"
    else:
        why = ""

    if fit.max_ratio is not None and fit.max_ratio >= _ACTIVE_COMPRESSION_RATIO:
        comp = (
            f" Loud sounds are actively softened (compression up to "
            f"{fit.max_ratio:.1f}:1) so they stay comfortable while quiet "
            "speech is still lifted."
        )
    else:
        comp = " Amplification is gentle and near-linear (little compression)."

    return lead + why + "." + comp


def summarise(explanation: FittingExplanation) -> str:
    """Render ``explanation`` as a sovereign, plain-English report.

    Args:
        explanation: The result of :func:`explain`.

    Returns:
        A multi-line human-readable string.
    """
    lines = [
        "Your fitting, in plain English",
        "==============================",
        "",
        _ear_paragraph(explanation.right),
        "",
        _ear_paragraph(explanation.left),
        "",
        f"Method: {explanation.method}.",
        "This explains a fitting you own and can change. OpenHear is not a "
        "medical device; have a professional verify any fitting you wear.",
    ]
    return "\n".join(lines)
