"""
safety.py – plausibility checks for fitting / extraction documents.

A hearing-aid fitting can be written with values that are technically
valid (right types, in-range) but dangerous in practice: insertion gain
above what the residual hearing can safely receive, MPO above 130 dB
SPL, compression ratios that flatten dynamic range to nothing.  Real
fitting software refuses such values.  This module gives OpenHear the
same backstop.

Two entry points, both pure functions, both side-effect-free:

* :func:`evaluate_session` – run thresholds against a
  :class:`core.fitting_data.FittingSession`.
* :func:`evaluate_extraction` – same, but for the richer
  :class:`core.schema.extraction_v1.ExtractedFitting` document.

Both return a :class:`SafetyReport` with a list of :class:`SafetyFlag`
entries.  Each flag carries a severity level so callers can decide
how to act (``"critical"`` should block writes; ``"warning"`` should
prompt user confirmation; ``"info"`` is logged).

Default thresholds are conservative and tunable through
:class:`SafetyThresholds`.  This module is **not** a substitute for
clinical judgement and OpenHear is not a medical device — see project
README.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from core.fitting_data import (
    CompressionProfile,
    FittingSession,
    GainTable,
    MPOProfile,
)

__all__ = [
    "DEFAULT_THRESHOLDS",
    "SafetyFlag",
    "SafetyReport",
    "SafetyThresholds",
    "evaluate_extraction",
    "evaluate_session",
]


# ── Configurable thresholds -------------------------------------------------


@dataclass(frozen=True)
class SafetyThresholds:
    """Tunable ceilings for safety evaluation.

    Defaults come from widely cited audiology guidance (e.g. Dillon,
    *Hearing Aids* 3rd ed.) and are deliberately conservative:

    * ``max_insertion_gain_db = 60`` — above this, real-ear measured
      output starts to risk further damage even for severe-profound
      losses.
    * ``max_mpo_db_spl = 130`` — the upper bound used by the IEC
      60118-0 measurement standard; output above this is unsafe for
      any user.
    * ``max_compression_ratio = 8.0`` — beyond this, dynamic range is
      effectively eliminated.
    * ``min_compression_ratio = 1.0`` — anything below 1:1 is an
      expander (signal-dependent gain), almost never wanted.
    * ``require_mpo`` — when ``True``, a missing MPO profile is flagged
      because it means the implicit limiter is unspecified.
    """

    max_insertion_gain_db: float = 60.0
    max_mpo_db_spl: float = 130.0
    max_compression_ratio: float = 8.0
    min_compression_ratio: float = 1.0
    require_mpo: bool = True


#: The default ceilings; pass a different :class:`SafetyThresholds` to override.
DEFAULT_THRESHOLDS: SafetyThresholds = SafetyThresholds()


# ── Result types ------------------------------------------------------------


@dataclass
class SafetyFlag:
    """A single safety-relevant finding.

    Attributes:
        level: ``"info"``, ``"warning"``, or ``"critical"``.  Only
            ``"critical"`` flags cause :attr:`SafetyReport.passed` to be
            ``False``.
        code: Short machine-readable identifier (e.g.
            ``"gain_exceeds_ceiling"``) so callers can branch on it
            without parsing :attr:`message`.
        message: Human-readable description, suitable for display.
        location: Dotted path into the source document
            (e.g. ``"right_gain[2]"``) so a UI can highlight the value.
    """

    level: str
    code: str
    message: str
    location: str = ""


@dataclass
class SafetyReport:
    """Result of a safety evaluation.

    Attributes:
        flags: All findings, in evaluation order.
        thresholds: The thresholds that were applied.
        passed: ``False`` if any flag is ``"critical"``.  Use this as a
            single-bit gate; if you need finer control inspect
            :attr:`flags` directly.
    """

    flags: list[SafetyFlag] = field(default_factory=list)
    thresholds: SafetyThresholds = field(default_factory=SafetyThresholds)

    @property
    def passed(self) -> bool:
        return not any(f.level == "critical" for f in self.flags)

    def critical(self) -> list[SafetyFlag]:
        return [f for f in self.flags if f.level == "critical"]

    def warnings(self) -> list[SafetyFlag]:
        return [f for f in self.flags if f.level == "warning"]

    def summary(self) -> str:
        """One-line summary suitable for CLI output."""
        return (
            f"{'PASS' if self.passed else 'FAIL'}: "
            f"{len(self.critical())} critical, "
            f"{len(self.warnings())} warnings, "
            f"{len(self.flags)} total."
        )


# ── Public API --------------------------------------------------------------


def evaluate_session(
    session: FittingSession,
    thresholds: SafetyThresholds = DEFAULT_THRESHOLDS,
) -> SafetyReport:
    """Evaluate a :class:`FittingSession` against *thresholds*."""
    flags: list[SafetyFlag] = []
    _check_gain(session.right_gain, "right_gain", thresholds, flags)
    _check_gain(session.left_gain, "left_gain", thresholds, flags)
    _check_compression(session.right_compression, "right_compression", thresholds, flags)
    _check_compression(session.left_compression, "left_compression", thresholds, flags)
    _check_mpo(session.right_mpo, "right_mpo", thresholds, flags)
    _check_mpo(session.left_mpo, "left_mpo", thresholds, flags)
    return SafetyReport(flags=flags, thresholds=thresholds)


def evaluate_extraction(
    extraction, thresholds: SafetyThresholds = DEFAULT_THRESHOLDS
) -> SafetyReport:
    """Evaluate an :class:`core.schema.extraction_v1.ExtractedFitting`.

    Accepts the document type directly rather than via a typed import
    to avoid a circular dependency (the schema module imports
    :mod:`core.fitting_data` which this module also uses).
    """
    # Re-use the session evaluator on the overlapping fields, then add
    # extraction-specific checks (e.g. unverified vendor adapter).
    flags: list[SafetyFlag] = []
    _check_gain(extraction.right_gain, "right_gain", thresholds, flags)
    _check_gain(extraction.left_gain, "left_gain", thresholds, flags)
    _check_compression(extraction.right_compression, "right_compression", thresholds, flags)
    _check_compression(extraction.left_compression, "left_compression", thresholds, flags)
    _check_mpo(extraction.right_mpo, "right_mpo", thresholds, flags)
    _check_mpo(extraction.left_mpo, "left_mpo", thresholds, flags)

    if not extraction.is_verified:
        flags.append(
            SafetyFlag(
                level="warning",
                code="adapter_unverified",
                message=(
                    f"Extraction was produced by vendor adapter "
                    f"{extraction.vendor_adapter!r} which has not been "
                    "verified against real hardware.  Values may be "
                    "placeholders; do not write to a device based on this "
                    "document."
                ),
                location="vendor_adapter",
            )
        )

    if extraction.confidence < 0.5:
        flags.append(
            SafetyFlag(
                level="info",
                code="low_confidence",
                message=(
                    f"Adapter reported low confidence "
                    f"({extraction.confidence:.2f}); review fields manually."
                ),
                location="confidence",
            )
        )

    return SafetyReport(flags=flags, thresholds=thresholds)


# ── Internal checks ---------------------------------------------------------


def _check_gain(
    table: GainTable,
    location: str,
    thresholds: SafetyThresholds,
    flags: list[SafetyFlag],
) -> None:
    for i, db in enumerate(table.gains_db):
        if db > thresholds.max_insertion_gain_db:
            flags.append(
                SafetyFlag(
                    level="critical",
                    code="gain_exceeds_ceiling",
                    message=(
                        f"Insertion gain {db:.1f} dB at "
                        f"{table.frequencies_hz[i]} Hz exceeds the "
                        f"{thresholds.max_insertion_gain_db:.1f} dB ceiling."
                    ),
                    location=f"{location}[{i}]",
                )
            )
        elif db < 0:
            flags.append(
                SafetyFlag(
                    level="warning",
                    code="negative_gain",
                    message=(
                        f"Insertion gain {db:.1f} dB at "
                        f"{table.frequencies_hz[i]} Hz is negative "
                        "(attenuation); confirm this is intentional."
                    ),
                    location=f"{location}[{i}]",
                )
            )


def _check_compression(
    profile: CompressionProfile,
    location: str,
    thresholds: SafetyThresholds,
    flags: list[SafetyFlag],
) -> None:
    for i, ratio in enumerate(profile.ratios):
        if ratio > thresholds.max_compression_ratio:
            flags.append(
                SafetyFlag(
                    level="warning",
                    code="compression_ratio_high",
                    message=(
                        f"Compression ratio {ratio:.1f}:1 in band "
                        f"{_band_label(profile.centre_frequencies_hz, i)} "
                        f"exceeds the {thresholds.max_compression_ratio:.1f}:1 "
                        "soft ceiling."
                    ),
                    location=f"{location}.ratios[{i}]",
                )
            )
        elif ratio < thresholds.min_compression_ratio:
            flags.append(
                SafetyFlag(
                    level="warning",
                    code="compression_ratio_low",
                    message=(
                        f"Compression ratio {ratio:.2f}:1 in band "
                        f"{_band_label(profile.centre_frequencies_hz, i)} "
                        "is below 1:1 (expander) — almost certainly an error."
                    ),
                    location=f"{location}.ratios[{i}]",
                )
            )


def _check_mpo(
    profile: MPOProfile,
    location: str,
    thresholds: SafetyThresholds,
    flags: list[SafetyFlag],
) -> None:
    if not profile.max_db_spl:
        if thresholds.require_mpo:
            flags.append(
                SafetyFlag(
                    level="critical",
                    code="mpo_missing",
                    message=(
                        f"{location} has no Maximum Power Output entries; "
                        "the implicit output limiter is unspecified."
                    ),
                    location=location,
                )
            )
        return
    for i, db in enumerate(profile.max_db_spl):
        if db > thresholds.max_mpo_db_spl:
            flags.append(
                SafetyFlag(
                    level="critical",
                    code="mpo_exceeds_ceiling",
                    message=(
                        f"MPO {db:.1f} dB SPL in band "
                        f"{_band_label(profile.centre_frequencies_hz, i)} "
                        f"exceeds the {thresholds.max_mpo_db_spl:.1f} "
                        "dB SPL ceiling."
                    ),
                    location=f"{location}.max_db_spl[{i}]",
                )
            )


def _band_label(centres: Sequence[int], index: int) -> str:
    """Return a human-friendly band identifier for an index."""
    if 0 <= index < len(centres):
        return f"{centres[index]} Hz"
    return f"#{index}"
