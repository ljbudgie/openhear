"""
filters.py – biquad filter bank for the OpenHear DSP pipeline.

Hearing-aid signal processing relies heavily on second-order IIR
("biquad") filters because they are cheap, stable, and combine to
form arbitrary frequency responses suitable for prescription gain,
notching anti-feedback bands, and emphasising the speech band.

This module implements a stateful :class:`Biquad` plus convenience
constructors for the most common audiology-relevant filter types:

* peaking EQ (``peaking_eq``)
* low-shelf (``low_shelf``)
* high-shelf (``high_shelf``)
* notch (``notch``)
* bandpass (``bandpass``)

Coefficients follow Robert Bristow-Johnson's *Audio EQ Cookbook*
formulas, the de-facto standard for parametric audio EQ.  The
implementation is pure-numpy so it works without ``scipy`` and is
trivial to vectorise across blocks.

References:
    * Bristow-Johnson, R. *Cookbook formulae for audio equalizer
      biquad filter coefficients*, 2005.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import numpy as np


def _validate_freq(freq_hz: float, sample_rate: float) -> float:
    """Return the angular centre frequency, raising if it is invalid."""
    if sample_rate <= 0:
        raise ValueError(f"sample_rate must be positive, got {sample_rate}.")
    if not (0 < freq_hz < sample_rate / 2):
        raise ValueError(
            f"freq_hz must be in (0, Nyquist={sample_rate / 2}), got {freq_hz}."
        )
    return 2.0 * math.pi * freq_hz / sample_rate


@dataclass
class BiquadCoeffs:
    """Direct-form-I biquad coefficients (b0, b1, b2, a0, a1, a2).

    All coefficients are normalised by ``a0`` on construction so that the
    actual difference equation is::

        y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2]
    """

    b0: float
    b1: float
    b2: float
    a1: float
    a2: float

    @classmethod
    def from_unnormalised(
        cls,
        b0: float, b1: float, b2: float,
        a0: float, a1: float, a2: float,
    ) -> "BiquadCoeffs":
        """Normalise raw cookbook coefficients by ``a0``."""
        if a0 == 0:
            raise ValueError("a0 must be non-zero.")
        return cls(b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0)


# ── Cookbook coefficient constructors ───────────────────────────────────────


def peaking_eq(freq_hz: float, gain_db: float, q: float, sample_rate: float) -> BiquadCoeffs:
    """Parametric peaking-EQ biquad coefficients.

    Args:
        freq_hz: Centre frequency in Hz.
        gain_db: Peak/dip gain in dB (positive = boost, negative = cut).
        q: Quality factor (sharpness).  Typical: 0.5–6.0.
        sample_rate: Sample rate in Hz.

    Returns:
        Normalised :class:`BiquadCoeffs`.

    Raises:
        ValueError: For invalid frequency, sample rate, or non-positive Q.
    """
    if q <= 0:
        raise ValueError(f"Q must be positive, got {q}.")
    w0 = _validate_freq(freq_hz, sample_rate)
    A = 10.0 ** (gain_db / 40.0)
    alpha = math.sin(w0) / (2.0 * q)
    cos_w0 = math.cos(w0)

    b0 = 1 + alpha * A
    b1 = -2 * cos_w0
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * cos_w0
    a2 = 1 - alpha / A
    return BiquadCoeffs.from_unnormalised(b0, b1, b2, a0, a1, a2)


def low_shelf(freq_hz: float, gain_db: float, slope: float, sample_rate: float) -> BiquadCoeffs:
    """Low-shelf biquad coefficients.

    ``slope=1.0`` reproduces the classic Butterworth-style shelf.
    """
    if slope <= 0:
        raise ValueError(f"slope must be positive, got {slope}.")
    w0 = _validate_freq(freq_hz, sample_rate)
    A = 10.0 ** (gain_db / 40.0)
    cos_w0 = math.cos(w0)
    sin_w0 = math.sin(w0)
    alpha = sin_w0 / 2.0 * math.sqrt((A + 1.0 / A) * (1.0 / slope - 1.0) + 2.0)

    b0 = A * ((A + 1) - (A - 1) * cos_w0 + 2 * math.sqrt(A) * alpha)
    b1 = 2 * A * ((A - 1) - (A + 1) * cos_w0)
    b2 = A * ((A + 1) - (A - 1) * cos_w0 - 2 * math.sqrt(A) * alpha)
    a0 = (A + 1) + (A - 1) * cos_w0 + 2 * math.sqrt(A) * alpha
    a1 = -2 * ((A - 1) + (A + 1) * cos_w0)
    a2 = (A + 1) + (A - 1) * cos_w0 - 2 * math.sqrt(A) * alpha
    return BiquadCoeffs.from_unnormalised(b0, b1, b2, a0, a1, a2)


def high_shelf(freq_hz: float, gain_db: float, slope: float, sample_rate: float) -> BiquadCoeffs:
    """High-shelf biquad coefficients.  See :func:`low_shelf` for ``slope``."""
    if slope <= 0:
        raise ValueError(f"slope must be positive, got {slope}.")
    w0 = _validate_freq(freq_hz, sample_rate)
    A = 10.0 ** (gain_db / 40.0)
    cos_w0 = math.cos(w0)
    sin_w0 = math.sin(w0)
    alpha = sin_w0 / 2.0 * math.sqrt((A + 1.0 / A) * (1.0 / slope - 1.0) + 2.0)

    b0 = A * ((A + 1) + (A - 1) * cos_w0 + 2 * math.sqrt(A) * alpha)
    b1 = -2 * A * ((A - 1) + (A + 1) * cos_w0)
    b2 = A * ((A + 1) + (A - 1) * cos_w0 - 2 * math.sqrt(A) * alpha)
    a0 = (A + 1) - (A - 1) * cos_w0 + 2 * math.sqrt(A) * alpha
    a1 = 2 * ((A - 1) - (A + 1) * cos_w0)
    a2 = (A + 1) - (A - 1) * cos_w0 - 2 * math.sqrt(A) * alpha
    return BiquadCoeffs.from_unnormalised(b0, b1, b2, a0, a1, a2)


def notch(freq_hz: float, q: float, sample_rate: float) -> BiquadCoeffs:
    """Bandstop (notch) biquad — useful for anti-feedback at known peaks."""
    if q <= 0:
        raise ValueError(f"Q must be positive, got {q}.")
    w0 = _validate_freq(freq_hz, sample_rate)
    cos_w0 = math.cos(w0)
    alpha = math.sin(w0) / (2.0 * q)

    b0 = 1.0
    b1 = -2 * cos_w0
    b2 = 1.0
    a0 = 1 + alpha
    a1 = -2 * cos_w0
    a2 = 1 - alpha
    return BiquadCoeffs.from_unnormalised(b0, b1, b2, a0, a1, a2)


def bandpass(freq_hz: float, q: float, sample_rate: float) -> BiquadCoeffs:
    """Constant-skirt-gain bandpass biquad — the speech-band emphasis filter."""
    if q <= 0:
        raise ValueError(f"Q must be positive, got {q}.")
    w0 = _validate_freq(freq_hz, sample_rate)
    cos_w0 = math.cos(w0)
    alpha = math.sin(w0) / (2.0 * q)

    b0 = q * alpha
    b1 = 0.0
    b2 = -q * alpha
    a0 = 1 + alpha
    a1 = -2 * cos_w0
    a2 = 1 - alpha
    return BiquadCoeffs.from_unnormalised(b0, b1, b2, a0, a1, a2)


# ── Stateful processor ──────────────────────────────────────────────────────


class Biquad:
    """Direct-form-I biquad filter that preserves state across blocks.

    Use :func:`peaking_eq`, :func:`low_shelf`, etc. to build coefficients,
    then construct a :class:`Biquad` to actually filter samples.

    Example::

        coeffs = peaking_eq(2000.0, 6.0, 1.5, 16_000)
        eq = Biquad(coeffs)
        block_out = eq.process(block_in)
    """

    def __init__(self, coeffs: BiquadCoeffs) -> None:
        self.coeffs = coeffs
        self._x1: float = 0.0
        self._x2: float = 0.0
        self._y1: float = 0.0
        self._y2: float = 0.0

    def process(self, samples: np.ndarray) -> np.ndarray:
        """Filter *samples* and return the result.

        Args:
            samples: 1-D float array.

        Returns:
            New 1-D float32 array of the same shape, filtered with state
            preserved between calls.
        """
        x = np.asarray(samples, dtype=np.float64)
        y = np.empty_like(x)
        b0, b1, b2, a1, a2 = (
            self.coeffs.b0, self.coeffs.b1, self.coeffs.b2,
            self.coeffs.a1, self.coeffs.a2,
        )
        x1, x2, y1, y2 = self._x1, self._x2, self._y1, self._y2
        for i, xi in enumerate(x):
            yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            y[i] = yi
            x2 = x1
            x1 = xi
            y2 = y1
            y1 = yi
        self._x1, self._x2, self._y1, self._y2 = x1, x2, y1, y2
        return y.astype(np.float32)

    def reset(self) -> None:
        """Reset filter state to zero (silence)."""
        self._x1 = self._x2 = self._y1 = self._y2 = 0.0


class FilterBank:
    """Cascade of :class:`Biquad` filters applied left-to-right.

    Use this to combine, e.g., a bass cut, a presence boost, and an
    anti-feedback notch into a single processing stage.
    """

    def __init__(self, filters: Iterable[Biquad]) -> None:
        self.filters: list[Biquad] = list(filters)

    def process(self, samples: np.ndarray) -> np.ndarray:
        out = samples
        for f in self.filters:
            out = f.process(out)
        return out

    def reset(self) -> None:
        for f in self.filters:
            f.reset()


# ── Convenience factories matching the master prompt ──────────────────────


def voice_bandpass(sample_rate: float, low_hz: float = 1000.0, high_hz: float = 4000.0) -> Biquad:
    """Speech-band emphasis bandpass centred between *low_hz* and *high_hz*.

    Args:
        sample_rate: Sample rate in Hz.
        low_hz: Low edge of the speech band (default 1000 Hz).
        high_hz: High edge of the speech band (default 4000 Hz).

    Returns:
        A configured :class:`Biquad`.
    """
    if not (0 < low_hz < high_hz):
        raise ValueError(f"Need 0 < low_hz < high_hz, got {low_hz}/{high_hz}.")
    centre = math.sqrt(low_hz * high_hz)  # geometric mean
    bw_octaves = math.log2(high_hz / low_hz)
    # Convert bandwidth in octaves to Q (cookbook).
    q = 1.0 / (2.0 * math.sinh(math.log(2) / 2.0 * bw_octaves)) if bw_octaves > 0 else 1.0
    return Biquad(bandpass(centre, q, sample_rate))


def anti_feedback_notch(freq_hz: float, sample_rate: float, q: float = 30.0) -> Biquad:
    """Sharp notch at a known feedback frequency.

    A high Q (default 30) keeps the notch narrow so the surrounding
    response is left almost unchanged.
    """
    return Biquad(notch(freq_hz, q, sample_rate))
