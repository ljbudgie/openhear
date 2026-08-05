"""
interpreter.py – plain-English hearing experience interpreter for OpenHear.

Translates a :class:`~audiogram.living_profile.LivingHearingProfile` into
human-readable descriptions of what the acoustic world sounds (and feels
via haptics) like under that profile, without making any medical claims.

Usage::

    from audiogram.living_profile import LivingHearingProfile
    from audiogram.interpreter import interpret_profile

    profile = LivingHearingProfile.from_file("audiogram/data/burgess_living_profile.json")
    for line in interpret_profile(profile):
        print(line)

Or from the command line::

    python -m audiogram.interpreter audiogram/data/burgess_living_profile.json
"""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from audiogram.living_profile import LivingHearingProfile

from audiogram.loader import get_severity

# ── Frequency-band descriptions ───────────────────────────────────────────────

_BAND_LABELS: list[tuple[tuple[int, int], str, str]] = [
    # (freq_range_hz, short_label, plain-English sound examples)
    ((0, 300),    "sub-bass / bass",     "deep rumbles, distant thunder, heavy bass in music"),
    ((301, 800),  "low-mid",             "vowel sounds, male voice fundamental, footsteps"),
    ((801, 2000), "mid",                 "speech consonants, piano mid-notes, most conversation"),
    ((2001, 4000),"upper-mid",           "the 'crispness' of speech (s, f, t), doorbells, alarms"),
    ((4001, 8000),"treble / high",       "birdsong, keyboard clicks, music overtones, sibilance"),
]


def _band_for_freq(freq_hz: int) -> tuple[str, str]:
    """Return ``(short_label, examples)`` for a frequency."""
    for (lo, hi), label, examples in _BAND_LABELS:
        if lo <= freq_hz <= hi:
            return label, examples
    return "extended range", "very high-pitched sounds"


# ── Severity → experience description ─────────────────────────────────────────

_SEVERITY_EXPERIENCE: dict[str, str] = {
    "normal": "sounds at this frequency are fully audible without assistance",
    "mild": "soft sounds at this frequency may be missed; normal conversation is usually clear",
    "moderate": "speech at this frequency needs to be louder than average; background noise is tiring",
    "moderately-severe": "significant effort is needed to follow speech at this frequency; hearing aids help greatly",
    "severe": "only loud sounds at this frequency are detectable; speech is very difficult without amplification",
    "profound": "this frequency is largely inaudible; haptic substitution and visual cues become important",
}


# ── Public API ────────────────────────────────────────────────────────────────


def interpret_profile(profile: "LivingHearingProfile") -> list[str]:
    """Generate a plain-English interpretation of a Living Hearing Profile.

    Returns a list of text lines (no ANSI codes) that describe:

    1. Who the profile belongs to and its date.
    2. Per-frequency hearing experience for each ear.
    3. How preferences modify the experience.
    4. What the haptic layer substitutes.
    5. What the active listening context optimises for.

    Args:
        profile: A loaded :class:`~audiogram.living_profile.LivingHearingProfile`.

    Returns:
        List of plain-text lines.
    """
    lines: list[str] = []

    _section(lines, f"Hearing Experience — {profile.subject}")
    lines.append(
        f"  Clinical audiogram date: {profile.clinical_date}. "
        f"Last profile update: {profile.summary().get('last_updated', 'unknown')}."
    )
    lines.append("")

    # ── Per-ear frequency-by-frequency experience ─────────────────────────────
    for ear in ("right", "left"):
        _section(lines, f"{ear.capitalize()} Ear")
        thresholds = profile.get_thresholds(ear)
        pref_gains = dict(profile.get_gain_profile(ear, include_preference=True))
        clinical_gains = dict(profile.get_gain_profile(ear, include_preference=False))

        for freq, db in thresholds:
            sev = get_severity(db)
            band_label, examples = _band_for_freq(freq)
            exp = _SEVERITY_EXPERIENCE.get(sev, "unclear experience at this frequency")
            clinical_g = clinical_gains.get(freq, 0)
            pref_g = pref_gains.get(freq, 0)
            pref_note = ""
            if pref_g != clinical_g:
                diff = pref_g - clinical_g
                sign = "+" if diff >= 0 else ""
                pref_note = f" (preference offset: {sign}{diff} dB)"

            lines.append(
                f"  {freq} Hz  [{band_label}]"
            )
            lines.append(f"    Threshold: {db} dB HL — {sev}")
            lines.append(f"    Sounds like: {examples}")
            lines.append(f"    Experience: {exp}")
            lines.append(
                f"    DSP gain applied: +{clinical_g} dB clinical{pref_note}"
            )
            lines.append("")

        try:
            pta = profile.get_pta(ear)
            overall_sev = get_severity(int(pta))
            lines.append(
                f"  Overall ({ear}): PTA = {pta:.1f} dB HL — {overall_sev}"
            )
            lines.append(f"  {_pta_summary(pta)}")
        except ValueError:
            lines.append("  Overall: insufficient data for PTA.")
        lines.append("")

    # ── Haptic layer ──────────────────────────────────────────────────────────
    weights = profile.get_haptic_weights()
    if weights:
        _section(lines, "Haptic Substitution (Wristband)")
        lines.append(
            "  The wristband translates inaudible sounds into tactile vibrations."
        )
        lines.append(
            "  Weights reflect the severity of hearing loss at each sound's dominant frequency."
        )
        lines.append("")
        for cls_name, weight in sorted(weights.items(), key=lambda kv: -kv[1]):
            if cls_name == "silence":
                continue
            bar = _weight_bar(weight)
            lines.append(f"  {cls_name:<14} {bar}  {weight:.0%}")
        lines.append("")

    # ── Active context ────────────────────────────────────────────────────────
    ctx = profile.get_active_context()
    if ctx:
        _section(lines, f"Active Listening Context: {ctx.get('label', ctx.get('name', 'unknown'))}")
        lines.append(f"  Noise reduction: {_pct(ctx.get('noise_reduction_aggressiveness', 0))}")
        lines.append(
            f"  Beamforming (directional microphone): {'on' if ctx.get('beamforming_enabled') else 'off'}"
        )
        lines.append(f"  Voice clarity boost: ×{ctx.get('voice_clarity_gain', 1.0):.1f}")
        lines.append(f"  Compression ratio: {ctx.get('compression_ratio_override', 2.0):.1f}:1")
        lines.append("")

    # ── Preference summary ────────────────────────────────────────────────────
    pref = profile._data.get("preference_layer", {})  # noqa: SLF001
    ceiling = pref.get("comfort_ceiling_db_spl")
    if ceiling:
        lines.append(
            f"  Comfort ceiling: {ceiling} dB SPL — "
            "sounds above this level are compressed to protect comfort."
        )
    if pref.get("voice_enhancement_enabled"):
        lines.append("  Voice enhancement: on — speech frequencies are prioritised.")
    lines.append("")

    # ── Sovereignty notice ────────────────────────────────────────────────────
    notice = profile._data.get("sovereignty_notice", "")  # noqa: SLF001
    if notice:
        lines.append(f"  {notice}")
        lines.append("")

    return lines


def print_interpretation(profile: "LivingHearingProfile") -> None:
    """Print the plain-English interpretation to stdout.

    Args:
        profile: A loaded :class:`~audiogram.living_profile.LivingHearingProfile`.
    """
    for line in interpret_profile(profile):
        print(line)


# ── Private helpers ───────────────────────────────────────────────────────────


def _section(lines: list[str], title: str) -> None:
    lines.append(f"{'─' * 60}")
    lines.append(f"  {title}")
    lines.append(f"{'─' * 60}")
    lines.append("")


def _weight_bar(weight: float, width: int = 20) -> str:
    filled = round(weight * width)
    return "█" * filled + "░" * (width - filled)


def _pct(value: float) -> str:
    return f"{value:.0%}"


def _pta_summary(pta: float) -> str:
    """Return a one-line summary of what the PTA means in everyday terms."""
    if pta <= 25:
        return "Normal hearing range — most everyday sounds are fully audible."
    if pta <= 40:
        return "Mild loss — soft speech may be missed in background noise."
    if pta <= 55:
        return "Moderate loss — conversation at normal volume is effortful without aids."
    if pta <= 70:
        return "Moderately-severe — most speech is unclear; hearing aids are strongly beneficial."
    if pta <= 90:
        return "Severe — only loud sounds are audible; DSP gain and haptics are both active."
    return "Profound — most sound is inaudible acoustically; haptic substitution is primary."


# ── CLI entry point ───────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point: interpret a Living Hearing Profile."""
    parser = argparse.ArgumentParser(
        description=(
            "Print a plain-English description of what the world sounds "
            "and feels like under a Living Hearing Profile."
        )
    )
    parser.add_argument("input", nargs="?", help="Path to a living profile or audiogram JSON file.")
    parser.add_argument("--input", "-i", dest="input_flag", default=None)
    args = parser.parse_args()

    path = args.input or args.input_flag
    if not path:
        parser.error("Please provide a path to a profile JSON file.")
        sys.exit(1)

    from audiogram.living_profile import LivingHearingProfile

    profile = LivingHearingProfile.from_file(path)
    print_interpretation(profile)


if __name__ == "__main__":
    main()
