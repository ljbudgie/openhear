"""
audiogram package – sovereign audiogram data for OpenHear.

Reads, stores, visualises, and exports audiometric threshold data in the
open openhear-audiogram-v1 JSON format.  Your audiogram is a measurement
of your body — this module treats it as sovereign data that you own and
control.

Key components:
  - loader.py      Load, validate, and analyse audiogram JSON files.
  - visualiser.py  Render an audiogram in the terminal (Unicode + ANSI).
  - export.py      Export to CSV, Markdown, or DSP configuration.
  - reader.py      Read threshold data from Noahlink Wireless 2 hardware.
  - data/          Audiogram data files in openhear-audiogram-v1 format.
  - audiogram.py   Canonical :class:`Audiogram` dataclass.
  - manual_entry.py CLI for entering thresholds at the keyboard.
  - compare.py     CLI front-end for longitudinal audiogram comparison.
"""

from audiogram.audiogram import (  # noqa: E402,F401
    Audiogram,
    STANDARD_FREQUENCIES_HZ,
    MIN_THRESHOLD_DB_HL,
    MAX_THRESHOLD_DB_HL,
    severity,
)

__all__ = [
    "Audiogram",
    "STANDARD_FREQUENCIES_HZ",
    "MIN_THRESHOLD_DB_HL",
    "MAX_THRESHOLD_DB_HL",
    "severity",
]
