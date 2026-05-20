"""Shared stage interface for optional DSP modules."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class BaseStage(ABC):
    """Minimal interface implemented by DSP processing stages."""

    @abstractmethod
    def process(self, samples: np.ndarray) -> np.ndarray:
        """Return processed samples for the next pipeline stage."""
