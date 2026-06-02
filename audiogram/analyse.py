"""
analyse.py – plain-English interpretation of your own audiogram.

The rest of the :mod:`audiogram` package can *store*, *validate*,
*compare*, and *prescribe gain* from threshold data.  This module
answers the question a person actually asks when a clinician hands them
a chart and little else:

    "What does my audiogram mean?"

It derives, for each ear:

* the pure-tone average (PTA) and its severity band,
* the audiometric *configuration* — the shape of the loss across
  frequency (flat, high-frequency sloping, low-frequency rising,
  mid-frequency "cookie-bite", or a noise-style notch), and

and across both ears:

* the inter-ear asymmetry, and
* a small set of plain-language *flags* — never diagnoses, only
  "this is worth understanding / worth a professional's eyes" pointers.

Design principles (the OpenHear way):

* **Sovereign, not clinical.** Everything here is a guide you own, not a
  verdict handed down to you.  Output is framed to inform, never to
  shame or alarm.  OpenHear is **not a medical device** and this module
  does not diagnose; where a pattern is worth a professional's eyes it
  says so plainly and explains *why*.
* **Honest about uncertainty.** With too few measured frequencies the
  configuration is reported as ``"indeterminate"`` rather than guessed.
* **Deterministic.** Pure functions over an :class:`~audiogram.audiogram.Audiogram`;
  no I/O, no hidden state, fully unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from audiogram.audiogram import Audiogram, severity

# ── Tuning constants ────────────────────────────────────────────────────────
#
# These thresholds are *guides* drawn from common audiological practice,
# not bright lines.  They exist to turn numbers into words; they are not a
# substitute for a professional reading of your audiogram.

#: Frequencies (Hz) treated as the "low" region when judging slope.
_LOW_FREQS: tuple[int, ...] = (250, 500)
#: Frequencies (Hz) treated as the "high" region when judging slope.
_HIGH_FREQS: tuple[int, ...] = (4000, 6000, 8000)
#: Frequencies (Hz) treated as the "mid" region.
_MID_FREQS: tuple[int, ...] = (1000, 2000)
#: Candidate noise-notch frequencies (Hz).  A noise-induced loss dips
#: here and partially recovers by 8 kHz.
_NOTCH_FREQS: tuple[int, ...] = (3000, 4000, 6000)

#: dB difference (high minus low region) above which a loss is "sloping"
#: and below the negation of which it is "reverse-sloping".
_SLOPE_DB: float = 15.0
#: dB by which a notch / cookie-bite must stand out from its neighbours.
_PROMINENCE_DB: float = 20.0
#: Inter-ear PTA gap (dB) at or above which asymmetry is worth flagging.
_ASYMMETRY_DB: float = 15.0
#: dB HL at or above which device output safety (MPO) deserves a note.
_PROFOUND_DB: float = 90.0


# ── Result types ────────────────────────────────────────────────────────────


@dataclass
class EarAnalysis:
    """Interpretation of a single ear.

    Attributes:
        ear: ``"left"`` or ``"right"``.
        pta: Pure-tone average in dB HL, or ``None`` if it cannot be
            computed (the four PTA frequencies are not all present).
        severity: Severity band for the PTA, or ``"unknown"`` when
            ``pta`` is ``None``.
        configuration: Shape of the loss across frequency — one of
            ``"flat"``, ``"sloping"`` (high-frequency), ``"reverse-sloping"``
            (low-frequency), ``"cookie-bite"`` (mid-frequency),
            ``"notched"`` (noise-style), or ``"indeterminate"`` when too
            few frequencies are present to judge.
        measured_frequencies: Count of frequencies recorded for this ear.
    """

    ear: str
    pta: float | None
    severity: str
    configuration: str
    measured_frequencies: int


@dataclass
class AudiogramAnalysis:
    """Full interpretation of a bilateral audiogram.

    Attributes:
        left: Per-ear analysis for the left ear.
        right: Per-ear analysis for the right ear.
        asymmetry_db: Absolute difference between the two ears' PTAs in
            dB, or ``None`` if either PTA is unavailable.
        flags: Plain-language, non-diagnostic pointers worth the user's
            attention (asymmetry, possible noise damage, output-safety).
    """

    left: EarAnalysis
    right: EarAnalysis
    asymmetry_db: float | None
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dict of this analysis."""
        return {
            "left": vars(self.left),
            "right": vars(self.right),
            "asymmetry_db": self.asymmetry_db,
            "flags": list(self.flags),
        }


# ── Core analysis ───────────────────────────────────────────────────────────


def _region_average(thresholds: dict[int, float], freqs: tuple[int, ...]) -> float | None:
    """Mean threshold over the measured members of ``freqs``, or ``None``."""
    present = [thresholds[f] for f in freqs if f in thresholds]
    if not present:
        return None
    return sum(present) / len(present)


def _classify_configuration(thresholds: dict[int, float]) -> str:
    """Classify the audiometric shape of one ear.

    Returns one of ``"flat"``, ``"sloping"``, ``"reverse-sloping"``,
    ``"cookie-bite"``, ``"notched"`` or ``"indeterminate"``.  At least
    three measured frequencies are required to commit to a shape.
    """
    if len(thresholds) < 3:
        return "indeterminate"

    low = _region_average(thresholds, _LOW_FREQS)
    mid = _region_average(thresholds, _MID_FREQS)
    high = _region_average(thresholds, _HIGH_FREQS)

    if low is None or high is None:
        return "indeterminate"

    # Noise-style notch first: a dip at 3/4/6 kHz that stands out from the
    # 1-2 kHz region *and* recovers by 8 kHz.  The recovery condition is
    # what distinguishes a notch from a plain sloping loss (which keeps
    # worsening through 8 kHz), so it must be tested before slope.
    notch_vals = [thresholds[f] for f in _NOTCH_FREQS if f in thresholds]
    recovery = thresholds.get(8000)
    if notch_vals and mid is not None and recovery is not None:
        worst_notch = max(notch_vals)
        if worst_notch - mid >= _PROMINENCE_DB and worst_notch - recovery >= _PROMINENCE_DB:
            return "notched"

    slope = high - low
    if slope >= _SLOPE_DB:
        return "sloping"
    if slope <= -_SLOPE_DB:
        return "reverse-sloping"

    # Roughly level across low and high — look for a mid-frequency dip.
    flank_avg = (low + high) / 2
    if mid is not None and mid - flank_avg >= _PROMINENCE_DB:
        return "cookie-bite"

    return "flat"


def _analyse_ear(audiogram: Audiogram, ear: str) -> EarAnalysis:
    thresholds = audiogram.thresholds(ear)
    try:
        pta: float | None = audiogram.pure_tone_average(ear)
    except ValueError:
        pta = None
    return EarAnalysis(
        ear=ear,
        pta=pta,
        severity=severity(pta) if pta is not None else "unknown",
        configuration=_classify_configuration(thresholds),
        measured_frequencies=len(thresholds),
    )


def analyse(audiogram: Audiogram) -> AudiogramAnalysis:
    """Interpret ``audiogram`` and return a structured analysis.

    This is the single entry point used by the CLI and by any caller that
    wants a plain-English read on a measured audiogram.

    Args:
        audiogram: The bilateral audiogram to interpret.

    Returns:
        An :class:`AudiogramAnalysis`.
    """
    left = _analyse_ear(audiogram, "left")
    right = _analyse_ear(audiogram, "right")

    asymmetry: float | None = None
    if left.pta is not None and right.pta is not None:
        asymmetry = round(abs(left.pta - right.pta), 1)

    flags: list[str] = []

    if asymmetry is not None and asymmetry >= _ASYMMETRY_DB:
        flags.append(
            f"Your ears differ by {asymmetry:.0f} dB on average. Asymmetry "
            "usually has a benign explanation, but it is the one pattern "
            "worth a professional's eyes to rule things out — not a cause "
            "for alarm, just worth doing once."
        )

    if "notched" in (left.configuration, right.configuration):
        flags.append(
            "The shape in at least one ear looks like a noise-related notch. "
            "If you are around loud sound, protecting your hearing now is the "
            "highest-leverage thing you can do for it."
        )

    for ear in (left, right):
        if ear.pta is not None and ear.pta >= _PROFOUND_DB:
            flags.append(
                f"The {ear.ear} ear is in the profound range. Make sure any "
                "device you build respects a safe maximum output (MPO) — see "
                "hardware/safety/mpo_calculator.py — so amplification never "
                "trades hearing access for more damage."
            )

    return AudiogramAnalysis(left=left, right=right, asymmetry_db=asymmetry, flags=flags)


# ── Plain-English rendering ─────────────────────────────────────────────────

_CONFIG_PHRASES: dict[str, str] = {
    "flat": "fairly even across pitches",
    "sloping": "better in the low pitches, falling away in the highs "
    "(the most common pattern — high-pitched sounds and consonants fade first)",
    "reverse-sloping": "weaker in the low pitches and stronger in the highs "
    "(a rarer, rising pattern)",
    "cookie-bite": "dipped in the mid pitches with better low and high ends",
    "notched": "a localised dip around 3–6 kHz, the classic fingerprint of "
    "noise exposure",
    "indeterminate": "not classifiable from the frequencies measured",
}


def _ear_sentence(a: EarAnalysis) -> str:
    name = a.ear.capitalize()
    if a.pta is None:
        return (
            f"{name} ear: not enough of the standard frequencies were measured "
            "to summarise (need 500, 1000, 2000 and 4000 Hz for a pure-tone "
            "average)."
        )
    shape = _CONFIG_PHRASES.get(a.configuration, a.configuration)
    return (
        f"{name} ear: average {a.pta:.0f} dB HL — {a.severity} range; "
        f"shape is {shape}."
    )


def summarise(analysis: AudiogramAnalysis) -> str:
    """Render ``analysis`` as a sovereign, plain-English report.

    Args:
        analysis: The result of :func:`analyse`.

    Returns:
        A multi-line human-readable string.  This is information you own
        about your own body — not a diagnosis.
    """
    lines = [
        "Your audiogram, in plain English",
        "================================",
        "",
        _ear_sentence(analysis.right),
        _ear_sentence(analysis.left),
    ]
    if analysis.asymmetry_db is not None:
        lines += ["", f"Difference between ears: {analysis.asymmetry_db:.0f} dB."]
    if analysis.flags:
        lines += ["", "Worth knowing:"]
        lines += [f"  • {flag}" for flag in analysis.flags]
    lines += [
        "",
        "This is a guide you own, not a diagnosis. OpenHear is not a medical "
        "device. A professional can read nuance a summary cannot.",
    ]
    return "\n".join(lines)
