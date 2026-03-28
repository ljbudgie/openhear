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
"""
