"""
audiogram.py – canonical :class:`Audiogram` dataclass for OpenHear.

This module provides a single, well-typed representation of a hearing
audiogram that the rest of the codebase can build on.  It coexists with
the dict-based helpers in :mod:`audiogram.loader` and
:mod:`audiogram.export`: those modules continue to operate on the
``openhear-audiogram-v1`` JSON shape used by the wristband and Noahlink
prototypes, while :class:`Audiogram` provides a structured object for
new code (DSP gain prescription, manual entry, comparison tooling).

The ``openhear-audiogram-v1`` JSON shape is the canonical on-disk
format.  An :class:`Audiogram` instance can be constructed from that
shape (``Audiogram.from_json``) and serialised back to it
(``Audiogram.to_json``), so both representations remain interchangeable.

Standard frequencies follow ISO 8253-1: 250, 500, 750, 1000, 1500,
2000, 3000, 4000, 6000, 8000 Hz.  Thresholds are stored in dB HL
(decibels Hearing Level).

Why a dataclass *and* a dict-based loader?
    The dict shape is what we receive from existing exports and what we
    write to disk.  A dataclass gives downstream consumers (DSP profile
    prescription, comparison reports, manual entry) static fields and
    methods that catch bugs early.  Both views exist because each is the
    right tool for a different job.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from datetime import date as date_type
from pathlib import Path
from typing import Iterable, Mapping

# ── Public constants ────────────────────────────────────────────────────────

#: Standard audiometric test frequencies in Hz (ISO 8253-1).
STANDARD_FREQUENCIES_HZ: tuple[int, ...] = (
    250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000,
)

#: Permitted dB HL range for a clinical audiogram (per ISO 8253-1).
MIN_THRESHOLD_DB_HL: int = -10
MAX_THRESHOLD_DB_HL: int = 120

#: Source labels recognised by :class:`Audiogram`.
KNOWN_SOURCES: frozenset[str] = frozenset({
    "manual_entry",
    "imported_from_device",
    "imported_from_pdf",
    "synthetic",
    "unknown",
})

# Standard severity classification (BSA / WHO).  Each tuple is
# (upper_bound_inclusive_db_hl, label).
_SEVERITY_BANDS: tuple[tuple[int, str], ...] = (
    (25, "normal"),
    (40, "mild"),
    (55, "moderate"),
    (70, "moderately-severe"),
    (90, "severe"),
    (120, "profound"),
)


# ── Validation helpers ──────────────────────────────────────────────────────


def _coerce_thresholds(values: Mapping[int | str, float | int]) -> dict[int, float]:
    """Coerce a threshold mapping to ``{int Hz: float dB HL}`` and validate.

    Args:
        values: Mapping of frequency (Hz, int or str) to threshold (dB HL).

    Returns:
        Dict mapping each frequency in Hz (int) to a threshold in dB HL
        (float), with frequencies sorted in ascending order on iteration.

    Raises:
        ValueError: If any threshold falls outside the
            :data:`MIN_THRESHOLD_DB_HL` to :data:`MAX_THRESHOLD_DB_HL`
            range, or any frequency cannot be parsed as an integer.
    """
    out: dict[int, float] = {}
    for freq_raw, db_raw in values.items():
        try:
            freq = int(freq_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Audiogram frequency must be integer-like, got {freq_raw!r}."
            ) from exc
        try:
            db = float(db_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Audiogram threshold for {freq} Hz must be numeric, got {db_raw!r}."
            ) from exc
        if not (MIN_THRESHOLD_DB_HL <= db <= MAX_THRESHOLD_DB_HL):
            raise ValueError(
                f"Threshold for {freq} Hz is {db} dB HL, outside the valid "
                f"range [{MIN_THRESHOLD_DB_HL}, {MAX_THRESHOLD_DB_HL}]."
            )
        out[freq] = db
    return dict(sorted(out.items()))


def severity(db_hl: float) -> str:
    """Return the clinical severity label for a single dB HL value.

    The classification follows the British Society of Audiology / WHO
    bands used in :mod:`audiogram.loader` so the two APIs agree.

    Args:
        db_hl: Threshold or pure-tone-average in dB HL.

    Returns:
        One of ``"normal"``, ``"mild"``, ``"moderate"``,
        ``"moderately-severe"``, ``"severe"``, ``"profound"``.
    """
    for upper, label in _SEVERITY_BANDS:
        if db_hl <= upper:
            return label
    return "profound"


# ── Audiogram dataclass ─────────────────────────────────────────────────────


@dataclass
class Audiogram:
    """A bilateral hearing audiogram in dB HL.

    Attributes:
        left_ear: Mapping of frequency (Hz) to threshold (dB HL) for the
            left ear.  Frequencies should be drawn from
            :data:`STANDARD_FREQUENCIES_HZ` but any subset is accepted.
        right_ear: Mapping of frequency (Hz) to threshold (dB HL) for the
            right ear.
        date_measured: ISO-8601 date string (``YYYY-MM-DD``) when the
            audiogram was taken, or ``"unknown"``.
        source: Origin of the data.  Free-form string but values in
            :data:`KNOWN_SOURCES` are preferred so downstream tooling
            can filter on them.
        subject: Optional subject identifier.  Not personally
            identifying by default.
        notes: Optional free-form notes.
    """

    left_ear: dict[int, float] = field(default_factory=dict)
    right_ear: dict[int, float] = field(default_factory=dict)
    date_measured: str = "unknown"
    source: str = "unknown"
    subject: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        self.left_ear = _coerce_thresholds(self.left_ear)
        self.right_ear = _coerce_thresholds(self.right_ear)
        if self.date_measured and self.date_measured != "unknown":
            # Validate date format if provided.
            try:
                date_type.fromisoformat(self.date_measured)
            except ValueError as exc:
                raise ValueError(
                    f"date_measured must be ISO-8601 (YYYY-MM-DD) or 'unknown', "
                    f"got {self.date_measured!r}."
                ) from exc

    # ── Per-frequency / per-ear queries ────────────────────────────────────

    def thresholds(self, ear: str) -> dict[int, float]:
        """Return the threshold mapping for ``ear`` (``"left"``/``"right"``)."""
        return self._ear(ear)

    def severity(self, freq_hz: int, ear: str = "right") -> str:
        """Severity classification at a given frequency for one ear.

        Args:
            freq_hz: Frequency in Hz.  Must be present in the chosen ear.
            ear: ``"left"`` or ``"right"``.

        Returns:
            The severity label from :func:`severity`.

        Raises:
            KeyError: If the frequency is not present in that ear.
        """
        thresholds = self._ear(ear)
        if freq_hz not in thresholds:
            raise KeyError(
                f"No threshold recorded at {freq_hz} Hz in the {ear} ear."
            )
        return severity(thresholds[freq_hz])

    def pure_tone_average(self, ear: str) -> float:
        """Pure-tone average across 500/1000/2000/4000 Hz for ``ear``.

        Returns:
            The mean threshold in dB HL, rounded to one decimal place.

        Raises:
            ValueError: If any of the four PTA frequencies is missing.
        """
        thresholds = self._ear(ear)
        pta_freqs = (500, 1000, 2000, 4000)
        missing = [f for f in pta_freqs if f not in thresholds]
        if missing:
            raise ValueError(
                f"Cannot compute PTA: missing thresholds at "
                f"{', '.join(str(f) for f in missing)} Hz in the {ear} ear."
            )
        return round(sum(thresholds[f] for f in pta_freqs) / len(pta_freqs), 1)

    # ── JSON I/O ──────────────────────────────────────────────────────────

    def to_json(self, indent: int | None = 2) -> str:
        """Serialise this audiogram to ``openhear-audiogram-v1`` JSON.

        The output is the same shape consumed by
        :func:`audiogram.loader.load_audiogram`, so the two APIs are
        round-trip compatible.

        Args:
            indent: ``json.dumps`` indent level, or ``None`` for compact.

        Returns:
            A JSON-encoded string.
        """
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False)

    def to_dict(self) -> dict:
        """Return the ``openhear-audiogram-v1`` dict for this audiogram."""
        return {
            "subject": self.subject or "anonymous",
            "source": self.source,
            "date": self.date_measured,
            "format_version": "openhear-audiogram-v1",
            "notes": self.notes,
            "right_ear": {
                "symbol": "O",
                "thresholds": [
                    {"freq_hz": f, "db_hl": _to_int_if_whole(db)}
                    for f, db in self.right_ear.items()
                ],
            },
            "left_ear": {
                "symbol": "X",
                "thresholds": [
                    {"freq_hz": f, "db_hl": _to_int_if_whole(db)}
                    for f, db in self.left_ear.items()
                ],
            },
        }

    @classmethod
    def from_json(cls, text: str) -> "Audiogram":
        """Construct an audiogram from a JSON string.

        Accepts both the canonical ``openhear-audiogram-v1`` shape and
        the simplified ``{"left_ear": {...}, "right_ear": {...}}`` shape
        used in the master prompt's example data.
        """
        return cls.from_dict(json.loads(text))

    @classmethod
    def from_dict(cls, data: Mapping) -> "Audiogram":
        """Construct an audiogram from a parsed dict.

        Two input shapes are accepted:

        1. The canonical ``openhear-audiogram-v1`` shape with
           ``right_ear``/``left_ear`` containing a ``thresholds`` list of
           ``{"freq_hz": ..., "db_hl": ...}`` entries.
        2. The simplified shape used in the master prompt example, where
           ``right_ear``/``left_ear`` are direct ``{freq: db}`` maps and
           the file optionally carries ``date``/``source`` keys.

        Args:
            data: Parsed JSON dict.

        Returns:
            A new :class:`Audiogram`.

        Raises:
            ValueError: If neither shape can be parsed or thresholds are
                outside the permitted dB HL range.
        """
        if "right_ear" not in data or "left_ear" not in data:
            raise ValueError(
                "Audiogram dict must contain 'right_ear' and 'left_ear' keys."
            )

        right = _extract_threshold_map(data["right_ear"])
        left = _extract_threshold_map(data["left_ear"])

        return cls(
            left_ear=left,
            right_ear=right,
            date_measured=str(data.get("date", "unknown")),
            source=str(data.get("source", "unknown")),
            subject=str(data.get("subject", "")),
            notes=str(data.get("notes", "")),
        )

    @classmethod
    def from_path(cls, path: str | Path) -> "Audiogram":
        """Load an audiogram from a JSON file on disk."""
        text = Path(path).read_text(encoding="utf-8")
        return cls.from_json(text)

    # ── CSV export ────────────────────────────────────────────────────────

    def to_csv(self) -> str:
        """Return the audiogram as a CSV string.

        Columns: ``ear, freq_hz, db_hl``.  One row per (ear, frequency).
        Frequencies are emitted in ascending order, right ear first.
        """
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["ear", "freq_hz", "db_hl"])
        for freq, db in self.right_ear.items():
            writer.writerow(["right", freq, _to_int_if_whole(db)])
        for freq, db in self.left_ear.items():
            writer.writerow(["left", freq, _to_int_if_whole(db)])
        return buf.getvalue()

    # ── Internal helpers ──────────────────────────────────────────────────

    def _ear(self, ear: str) -> dict[int, float]:
        ear_lc = ear.lower().strip()
        if ear_lc == "left":
            return self.left_ear
        if ear_lc == "right":
            return self.right_ear
        raise ValueError(f"ear must be 'left' or 'right', got {ear!r}")


# ── Internal helpers (module-private) ───────────────────────────────────────


def _extract_threshold_map(ear_data: object) -> dict[int, float]:
    """Pull a ``{freq: db}`` mapping from either supported input shape."""
    # Shape 1: openhear-audiogram-v1 — {"thresholds": [{"freq_hz": ..., "db_hl": ...}]}
    if isinstance(ear_data, Mapping) and "thresholds" in ear_data:
        thresholds_list = ear_data["thresholds"]
        if not isinstance(thresholds_list, Iterable):
            raise ValueError("'thresholds' must be a list of {freq_hz, db_hl} entries.")
        result: dict[int, float] = {}
        for entry in thresholds_list:
            if not isinstance(entry, Mapping) or "freq_hz" not in entry or "db_hl" not in entry:
                raise ValueError(
                    "Each thresholds entry must be a dict with 'freq_hz' and 'db_hl'."
                )
            result[int(entry["freq_hz"])] = float(entry["db_hl"])
        return result

    # Shape 2: prompt-style — {"250": 35, "500": 40, ...}
    if isinstance(ear_data, Mapping):
        return {int(k): float(v) for k, v in ear_data.items()}

    raise ValueError(
        f"Unsupported ear data shape: expected dict, got {type(ear_data).__name__}."
    )


def _to_int_if_whole(value: float) -> int | float:
    """Render whole-number thresholds as ints in JSON/CSV for readability."""
    if float(value).is_integer():
        return int(value)
    return float(value)
