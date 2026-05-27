"""Adaptive-tuning / listener-learning package.

Phase 6 of the OpenHear roadmap.  This package provides local listener
preference capture, deterministic adaptive config suggestions, and saved
per-environment profiles.

Public modules:

* :mod:`learn.preferences` — capture listener A/B choices.
* :mod:`learn.engine` — convert preferences into config updates.
* :mod:`learn.profiles` — store/load per-environment profiles.
"""

from __future__ import annotations

__all__ = [
    "preferences",
    "engine",
    "profiles",
]
