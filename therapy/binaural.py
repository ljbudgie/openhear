"""
binaural.py – sovereign, audiogram-aware binaural-beat generation.

A binaural beat is the rhythmic percept the brain creates when each ear
hears a slightly different pure tone: 200 Hz in the left ear and 210 Hz in
the right produces a perceived 10 Hz "beat".  Generating that is simple
trigonometry.  What no consumer binaural-beats app does — and what is
genuinely unexplored for OpenHear's actual users — is account for the fact
that **the listener may have hearing loss**.

The beat percept depends on the brain receiving *both* tones at usable,
roughly balanced loudness.  If one ear's carrier sits in a frequency region
where that ear has a 50 dB loss, the tone is faint or absent and the beat
collapses.  So this module can read the user's own audiogram and:

* pick a **carrier frequency** where *both* ears hear as well as possible, and
* set **per-ear gains** that rebalance an asymmetric loss,

while never exceeding a conservative amplitude ceiling.

Everything here is deterministic NumPy maths over an explicit sample rate —
no audio devices, no I/O — so the generated signal, its per-ear
frequencies, and the safety bounds are all unit-testable.  OpenHear is not a
medical device; this is sovereign tooling for evidence-led
self-experimentation (see :mod:`therapy.protocol`).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from audiogram.audiogram import Audiogram

#: Default output sample rate in Hz.
DEFAULT_SAMPLE_RATE: int = 44_100

#: Peak per-channel amplitude we will never exceed (headroom + comfort).
#: Binaural beats want to be gentle; this also leaves room for per-ear gain.
SAFE_PEAK_AMPLITUDE: float = 0.32

#: Sensible carrier window (Hz) for the audiogram-aware prescriber.  Low
#: carriers give a stronger beat percept; we stay in a comfortable,
#: well-tested band and inside typical audiometric frequencies.
DEFAULT_CARRIER_RANGE: tuple[float, float] = (250.0, 1000.0)

#: Cap how much per-ear boost asymmetry compensation may request (dB), so a
#: severe single-ear loss cannot demand an absurd gain.
_MAX_BALANCE_DB: float = 30.0


def generate_binaural(
    carrier_hz: float,
    beat_hz: float,
    duration_s: float,
    *,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    amplitude: float = 0.2,
    left_gain: float = 1.0,
    right_gain: float = 1.0,
    fade_s: float = 0.05,
) -> np.ndarray:
    """Generate a stereo binaural beat as a ``(N, 2)`` float32 array.

    The left ear gets ``carrier - beat/2`` and the right ``carrier + beat/2``,
    so the perceived beat is ``beat_hz`` and the two ears stay symmetric
    about the carrier.

    Args:
        carrier_hz: Centre carrier frequency in Hz.
        beat_hz: Desired beat (difference) frequency in Hz.
        duration_s: Length of the signal in seconds.
        sample_rate: Output sample rate in Hz.
        amplitude: Base peak amplitude before per-ear gain, in ``(0, 1]``.
        left_gain: Linear gain applied to the left channel.
        right_gain: Linear gain applied to the right channel.
        fade_s: Linear fade-in/out length (seconds) to avoid onset clicks.

    Returns:
        A ``(N, 2)`` ``float32`` array, column 0 left, column 1 right, with
        samples in ``[-1, 1]``.

    Raises:
        ValueError: On non-positive durations/frequencies, a left carrier
            that would be <= 0, a carrier above the Nyquist limit, or a
            gained peak exceeding 1.0 (refused rather than clipped).
    """
    if duration_s <= 0:
        raise ValueError("duration_s must be positive.")
    if carrier_hz <= 0 or beat_hz <= 0:
        raise ValueError("carrier_hz and beat_hz must be positive.")
    if not 0.0 < amplitude <= 1.0:
        raise ValueError("amplitude must be in (0, 1].")
    if left_gain <= 0 or right_gain <= 0:
        raise ValueError("gains must be positive.")

    left_freq = carrier_hz - beat_hz / 2.0
    right_freq = carrier_hz + beat_hz / 2.0
    if left_freq <= 0:
        raise ValueError("carrier_hz must exceed beat_hz / 2.")
    if right_freq >= sample_rate / 2.0:
        raise ValueError("carrier exceeds the Nyquist limit for this sample_rate.")

    peak = amplitude * max(left_gain, right_gain)
    if peak > 1.0:
        raise ValueError(
            f"amplitude x gain peak {peak:.3f} exceeds 1.0; lower amplitude or gain."
        )

    n = int(round(duration_s * sample_rate))
    t = np.arange(n, dtype=np.float64) / sample_rate
    left = amplitude * left_gain * np.sin(2.0 * np.pi * left_freq * t)
    right = amplitude * right_gain * np.sin(2.0 * np.pi * right_freq * t)

    envelope = _fade_envelope(n, sample_rate, fade_s)
    left *= envelope
    right *= envelope

    return np.column_stack((left, right)).astype(np.float32)


def _fade_envelope(n: int, sample_rate: int, fade_s: float) -> np.ndarray:
    """Return a 1-D linear fade-in/out envelope of length *n*."""
    env = np.ones(n, dtype=np.float64)
    fade = min(int(fade_s * sample_rate), n // 2)
    if fade > 0:
        ramp = np.linspace(0.0, 1.0, fade, endpoint=False)
        env[:fade] = ramp
        env[-fade:] = ramp[::-1]
    return env


def dominant_frequencies(stereo: np.ndarray, sample_rate: int) -> tuple[float, float]:
    """Return the (left, right) dominant frequencies of a stereo signal.

    Uses an FFT magnitude peak per channel.  Useful for verifying generated
    output and for tests.

    Args:
        stereo: A ``(N, 2)`` array.
        sample_rate: Sample rate in Hz.

    Returns:
        ``(left_hz, right_hz)`` to the FFT bin resolution.
    """
    if stereo.ndim != 2 or stereo.shape[1] != 2:
        raise ValueError("stereo must be an (N, 2) array.")
    n = stereo.shape[0]
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    out = []
    for channel in range(2):
        spectrum = np.abs(np.fft.rfft(stereo[:, channel]))
        out.append(float(freqs[int(np.argmax(spectrum))]))
    return out[0], out[1]


@dataclass(frozen=True)
class BinauralPrescription:
    """An audiogram-tailored binaural-beat recipe.

    Attributes:
        carrier_hz: Carrier frequency chosen for mutual audibility.
        beat_hz: Requested beat (entrainment) frequency.
        left_gain: Linear gain for the left channel.
        right_gain: Linear gain for the right channel.
        amplitude: Base amplitude the gains are applied to.
        sample_rate: Sample rate the recipe renders at.
        rationale: Plain-English explanation of the choices.
    """

    carrier_hz: float
    beat_hz: float
    left_gain: float
    right_gain: float
    amplitude: float
    sample_rate: int
    rationale: str

    def render(self, duration_s: float, *, fade_s: float = 0.05) -> np.ndarray:
        """Render this prescription to a ``(N, 2)`` float32 signal."""
        return generate_binaural(
            self.carrier_hz,
            self.beat_hz,
            duration_s,
            sample_rate=self.sample_rate,
            amplitude=self.amplitude,
            left_gain=self.left_gain,
            right_gain=self.right_gain,
            fade_s=fade_s,
        )

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dict of this prescription."""
        return {
            "carrier_hz": self.carrier_hz,
            "beat_hz": self.beat_hz,
            "left_gain": self.left_gain,
            "right_gain": self.right_gain,
            "amplitude": self.amplitude,
            "sample_rate": self.sample_rate,
            "rationale": self.rationale,
        }


def _best_mutual_carrier(
    audiogram: Audiogram, carrier_range: tuple[float, float]
) -> int | None:
    """Pick the in-range frequency where *both* ears hear best.

    Returns the frequency (Hz) minimising the worse ear's threshold, or
    ``None`` when no frequency is measured in both ears within the range.
    """
    lo, hi = carrier_range
    left = audiogram.thresholds("left")
    right = audiogram.thresholds("right")
    shared = sorted(f for f in (set(left) & set(right)) if lo <= f <= hi)
    if not shared:
        return None
    # Lowest worse-ear threshold wins; ties break toward the lower carrier.
    return min(shared, key=lambda f: (max(left[f], right[f]), f))


def prescribe_binaural(
    audiogram: Audiogram,
    beat_hz: float,
    *,
    amplitude: float = 0.2,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    carrier_range: tuple[float, float] = DEFAULT_CARRIER_RANGE,
) -> BinauralPrescription:
    """Tailor a binaural beat to ``audiogram`` so both ears actually hear it.

    The carrier is placed where both ears hear best; per-ear gains rebalance
    an asymmetric loss (the worse ear is boosted by the threshold difference,
    capped at :data:`_MAX_BALANCE_DB`).  If that pushes the peak past the
    :data:`SAFE_PEAK_AMPLITUDE` ceiling, both channels are scaled down
    together so the *balance* is preserved under the safety limit.

    Args:
        audiogram: The listener's audiogram.
        beat_hz: Desired beat (entrainment) frequency in Hz.
        amplitude: Base amplitude before per-ear gain.
        sample_rate: Output sample rate.
        carrier_range: Allowed carrier window in Hz.

    Returns:
        A :class:`BinauralPrescription`.
    """
    if beat_hz <= 0:
        raise ValueError("beat_hz must be positive.")

    carrier = _best_mutual_carrier(audiogram, carrier_range)
    if carrier is None:
        # Not enough overlapping data — fall back to a neutral, balanced tone.
        return BinauralPrescription(
            carrier_hz=float(int((carrier_range[0] + carrier_range[1]) / 2)),
            beat_hz=beat_hz,
            left_gain=1.0,
            right_gain=1.0,
            amplitude=amplitude,
            sample_rate=sample_rate,
            rationale=(
                "Not enough overlapping audiogram data in the carrier range, so "
                "a neutral mid-range carrier with balanced ears was used. Add "
                "thresholds in both ears to personalise this."
            ),
        )

    left_thr = audiogram.thresholds("left")[carrier]
    right_thr = audiogram.thresholds("right")[carrier]

    # Boost the worse (higher-threshold) ear by the capped difference.
    delta_db = min(abs(left_thr - right_thr), _MAX_BALANCE_DB)
    boost = 10.0 ** (delta_db / 20.0)
    if left_thr >= right_thr:
        left_gain, right_gain = boost, 1.0
        worse = "left"
    else:
        left_gain, right_gain = 1.0, boost
        worse = "right"

    # Respect the safety ceiling while preserving the left/right balance.
    peak = amplitude * max(left_gain, right_gain)
    if peak > SAFE_PEAK_AMPLITUDE:
        scale = SAFE_PEAK_AMPLITUDE / peak
        left_gain *= scale
        right_gain *= scale

    if delta_db < 0.5:
        rationale = (
            f"Carrier {carrier} Hz sits where both ears hear best "
            f"({left_thr:.0f}/{right_thr:.0f} dB HL); your ears are well "
            "balanced here, so both channels play at equal level."
        )
    else:
        rationale = (
            f"Carrier {carrier} Hz sits where both ears hear best. Your "
            f"{worse} ear is ~{delta_db:.0f} dB weaker here, so it is boosted "
            "to keep the beat balanced — kept under the safety ceiling."
        )

    return BinauralPrescription(
        carrier_hz=float(carrier),
        beat_hz=beat_hz,
        left_gain=round(left_gain, 4),
        right_gain=round(right_gain, 4),
        amplitude=amplitude,
        sample_rate=sample_rate,
        rationale=rationale,
    )
