"""Adaptive-tuning / listener-learning package.

Phase 6 of the OpenHear roadmap.  Everything in this package is
currently scaffolding with documented ``NotImplementedError`` stubs:
the data-model shape is deliberately shared between modules so that,
once the machine-learning side lands, it can be swapped in under a
stable API.

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
