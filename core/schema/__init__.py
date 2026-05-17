"""Versioned, on-disk schemas for OpenHear extraction documents.

Each module under :mod:`core.schema` exposes a single, stable version of a
schema with explicit ``SCHEMA_VERSION`` constants.  Bumping a schema means
adding a new module (``foo_v2.py``); the old module is kept so historical
files keep loading.
"""

from __future__ import annotations

from core.schema.extraction_v1 import (
    SCHEMA_VERSION as EXTRACTION_V1_VERSION,
)
from core.schema.extraction_v1 import (
    BoneConductionAudiogram,
    ExtractedFitting,
    ExtractionSafetyFlag,
    RECDProfile,
)

__all__ = [
    "EXTRACTION_V1_VERSION",
    "BoneConductionAudiogram",
    "ExtractedFitting",
    "ExtractionSafetyFlag",
    "RECDProfile",
]
