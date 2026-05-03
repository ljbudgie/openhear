"""
occlusion_reduction.py – high-pass filter for ITE shell occlusion relief.

When an in-the-ear (ITE) hearing aid or shell seals the ear canal, the
wearer's own voice and body sounds create a low-frequency resonance in
the blocked cavity — the "occlusion effect".  Attenuating frequencies
below ~300 Hz reduces this boomy buildup without affecting speech
intelligibility (which lives mostly above 500 Hz).

This stage applies a Butterworth high-pass filter at the configured
corner frequency.  Filter order is derived from the desired roll-off
slope in dB/octave:

    order = max(1, round(slope_db_oct / 6))

So 6 dB/octave → 1st-order, 12 dB/octave → 2nd-order (default), etc.

Disabled by default — only relevant for ITE/CIC shell wearers.
Enable and tune in dsp/config.py:

    OCCLUSION_REDUCTION_ENABLED = True
    OCCLUSION_REDUCTION_CORNER_HZ = 300.0   # Hz
    OCCLUSION_REDUCTION_SLOPE_DB_OCT = 12.0  # dB/octave
"""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi


class OcclusionReducer:
    """Stateful Butterworth high-pass filter for occlusion effect relief.

    Args:
        sample_rate:    Audio sample rate in Hz.
        corner_hz:      High-pass corner frequency in Hz (–3 dB point).
        slope_db_oct:   Roll-off slope below the corner in dB/octave.
                        6 dB/oct = 1st-order, 12 dB/oct = 2nd-order, etc.
    """

    def __init__(
        self,
        sample_rate: int,
        corner_hz: float = 300.0,
        slope_db_oct: float = 12.0,
    ) -> None:
        nyquist = sample_rate / 2.0
        if not (0 < corner_hz < nyquist):
            raise ValueError(
                f"corner_hz must be in (0, {nyquist}), got {corner_hz}."
            )
        if slope_db_oct <= 0:
            raise ValueError(f"slope_db_oct must be positive, got {slope_db_oct}.")

        order = max(1, round(slope_db_oct / 6.0))
        self._sos = butter(order, corner_hz / nyquist, btype="high", output="sos")
        # Initial conditions sized to the filter (n_sections × 2).
        self._zi_proto = sosfilt_zi(self._sos)
        self._zi = np.zeros_like(self._zi_proto)

    def process(self, samples: np.ndarray) -> np.ndarray:
        """Apply the high-pass filter to *samples*, preserving state.

        Args:
            samples: 1-D float32 PCM array normalised to [-1.0, 1.0].

        Returns:
            Filtered float32 array of the same shape.
        """
        x = np.asarray(samples, dtype=np.float64)
        y, self._zi = sosfilt(self._sos, x, zi=self._zi)
        return y.astype(np.float32)

    def reset(self) -> None:
        """Reset filter state to silence."""
        self._zi = np.zeros_like(self._zi_proto)
