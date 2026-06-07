"""
crowd_arousal.py – continuous crowd-energy estimation for haptic rendering.

The v1 wristband can say "media is playing" or "there is crowd noise", but
both reduce to a single category and a single buzz.  A sports venue, concert,
or public space is a *dynamic* acoustic environment — the crowd is tense, then
euphoric, then on the edge of its seat; two moments of crowd noise can feel
completely different.  None of that survives a seven-way classifier.

This module estimates that continuous state from a rolling audio frame,
producing three dimensions that between them capture most of what a hearing
person perceives as "the energy in the room":

    arousal         — overall energy/excitement, 0.0 (silent/calm) to 1.0 (frenetic)
    tension         — rate of change / spectral flux, 0.0 (steady) to 1.0 (volatile)
    onset_rate_hz   — detected acoustic events per second in recent history

Those dimensions map cleanly to the haptic primitive axes in
:mod:`stream.haptic_primitive`:

    arousal  → intensity        (louder/more excited crowd → stronger buzz)
    tension  → pulse_rate_hz    (volatile audio → faster rhythm)
    tension  → sharpness        (tense crowd → sharper haptic onset)
    spatial_balance is always 0.0 — crowd energy is omnidirectional

Algorithm:

1. **RMS energy → arousal.**  Mapped on a log scale that puts a typical
   quiet crowd at ~0.3, a cheering crowd at ~0.8, and silence at 0.0.
2. **Spectral flux → tension.**  Half-wave rectified difference between
   successive magnitude spectra, normalised by mean spectrum amplitude so
   it is scale-invariant.  Zero for a steady tone, high for fast-changing
   textured noise.
3. **Onset detection → onset_rate_hz.**  An onset is flagged when RMS rises
   by more than :data:`_ONSET_THRESHOLD` relative to the previous frame.
   The rate is computed over a rolling :data:`_ONSET_HISTORY_S` window.

Limitations (honest):
    - The onset detector over-fires on heavily compressed signals (hard-limited
      audio) because every frame has similar RMS.  Use unprocessed microphone
      input where possible.
    - Valence (positive/negative emotional content) is omitted intentionally —
      it requires a trained model and we do not have one.  Arousal + tension
      are measurable from first principles; valence is not.
    - Spectral flux normalisation can saturate near-silence frames.  The
      :attr:`_SILENCE_FLOOR` guard prevents division-by-zero but onset
      sensitivity drops at very low levels.

Usage::

    estimator = CrowdArousalEstimator(sample_rate=44_100, frame_size=2048)
    for frame in audio_frames:
        estimate = estimator.update(frame)
        primitive = estimator.to_primitive(estimate)
        events = primitive.to_events(duration_s=1.0)
        send_to_wristband(events)
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from stream.haptic_primitive import HapticPrimitive

# ── Constants ─────────────────────────────────────────────────────────────────

#: Rolling window over which onset rate is computed, in seconds.
_ONSET_HISTORY_S: float = 2.0

#: Intensity at which the wristband buzz is barely perceptible above the
#: motor's own noise floor (practical minimum for meaningful feedback).
_MIN_INTENSITY: int = 40

#: Intensity ceiling for the crowd-arousal channel.  Kept below 255 so
#: safety-critical alert signals can always override with a stronger signal.
_MAX_INTENSITY: int = 160

#: Slowest haptic rate used for crowd texture — very calm, barely-there throb.
_MIN_RATE_HZ: float = 0.5

#: Fastest haptic rate for crowd texture.  Above ~15 Hz the wrist feels a
#: continuous buzz rather than discrete pulses; 12 Hz is the perceptual
#: threshold for "fast and frenetic" without losing rhythmicity.
_MAX_RATE_HZ: float = 12.0

#: RMS floor below which a frame is treated as silence.  Guards log(0) and
#: division by near-zero in flux normalisation.
_SILENCE_FLOOR: float = 1e-6

#: Relative RMS rise required to count as an onset (15%).  Tighten for
#: very dynamic sources; loosen for compressed broadcast audio.
_ONSET_THRESHOLD: float = 0.15

# Log scale calibration: maps RMS 0.001 → arousal ~0.33,
# RMS 0.01 → ~0.67, RMS 0.1 → ~1.0 for audio in the ±1 float range.
_AROUSAL_LOG_LO: float = -4.0   # log10 of the "silence" anchor
_AROUSAL_LOG_SPAN: float = 3.0  # log10(0.1) − log10(0.001) = 2, +1 headroom


# ── Output type ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ArousalEstimate:
    """One instantaneous crowd-state reading.

    Attributes:
        arousal:       Energy/excitement level, 0.0 (calm) to 1.0 (frenetic).
        tension:       Rate of change, 0.0 (steady) to 1.0 (volatile).
        onset_rate_hz: Acoustic events per second in the recent history window.
    """

    arousal: float
    tension: float
    onset_rate_hz: float


# ── Estimator ─────────────────────────────────────────────────────────────────


class CrowdArousalEstimator:
    """Stateful, frame-by-frame crowd-energy estimator.

    Instantiate once per listening session; call :meth:`update` for each
    incoming audio frame.

    Args:
        sample_rate: Audio sample rate in Hz (default 44 100).
        frame_size:  Expected samples per :meth:`update` call (default 2048).
                     Values between 512 and 8192 work well at 44.1 kHz.
    """

    def __init__(self, *, sample_rate: int = 44_100, frame_size: int = 2048) -> None:
        if sample_rate <= 0:
            raise ValueError(f"sample_rate must be positive, got {sample_rate}.")
        if frame_size <= 0:
            raise ValueError(f"frame_size must be positive, got {frame_size}.")
        self._sample_rate = sample_rate
        self._frame_size = frame_size
        self._frame_duration_s: float = frame_size / sample_rate
        # Rolling magnitude spectrum for spectral-flux computation
        self._prev_spectrum: "np.ndarray | None" = None
        # RMS of previous frame for onset detection
        self._prev_rms: float = 0.0
        # Queue of onset timestamps (in seconds) for rolling rate estimate
        _max_frames = int(_ONSET_HISTORY_S / self._frame_duration_s) + 2
        self._onset_times: deque[float] = deque(maxlen=_max_frames)
        self._frame_index: int = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, audio_frame: "np.ndarray") -> ArousalEstimate:
        """Process one audio frame and return the current crowd state.

        Args:
            audio_frame: 1-D float32 or float64 array of exactly
                         ``frame_size`` samples.  Values should be in the
                         ±1 float range (standard normalised audio).

        Returns:
            :class:`ArousalEstimate` for this frame.

        Raises:
            ValueError: If *audio_frame* is not 1-D.
        """
        frame = np.asarray(audio_frame, dtype=np.float64)
        if frame.ndim != 1:
            raise ValueError(f"audio_frame must be 1-D, got shape {frame.shape}.")

        # ── 1. RMS energy → arousal ──────────────────────────────────────────
        rms = float(np.sqrt(np.mean(frame**2)))
        arousal = float(np.clip(_rms_to_arousal(rms), 0.0, 1.0))

        # ── 2. Spectral flux → tension ───────────────────────────────────────
        spectrum = np.abs(np.fft.rfft(frame))
        if self._prev_spectrum is not None and len(spectrum) == len(self._prev_spectrum):
            # Half-wave rectified flux: only energy *increases* matter
            # (we care about new content appearing, not disappearing)
            diff = spectrum - self._prev_spectrum
            flux = float(np.mean(np.maximum(diff, 0.0)))
            mean_energy = float(np.mean(np.abs(spectrum))) + _SILENCE_FLOOR
            tension = float(np.clip(flux / mean_energy, 0.0, 1.0))
        else:
            tension = 0.0
        self._prev_spectrum = spectrum

        # ── 3. Onset detection → onset_rate_hz ───────────────────────────────
        if rms > _SILENCE_FLOOR and self._prev_rms > _SILENCE_FLOOR:
            relative_rise = (rms - self._prev_rms) / self._prev_rms
            if relative_rise > _ONSET_THRESHOLD:
                now_s = self._frame_index * self._frame_duration_s
                self._onset_times.append(now_s)
        self._prev_rms = rms

        now_s = self._frame_index * self._frame_duration_s
        window_start = now_s - _ONSET_HISTORY_S
        recent = [t for t in self._onset_times if t >= window_start]
        onset_rate_hz = len(recent) / _ONSET_HISTORY_S

        self._frame_index += 1
        return ArousalEstimate(
            arousal=round(arousal, 4),
            tension=round(tension, 4),
            onset_rate_hz=round(onset_rate_hz, 4),
        )

    def to_primitive(self, estimate: ArousalEstimate) -> HapticPrimitive:
        """Map a crowd-state estimate to a :class:`~stream.haptic_primitive.HapticPrimitive`.

        Mapping (all linear):

        * ``arousal``  → ``intensity``        (:data:`_MIN_INTENSITY` – :data:`_MAX_INTENSITY`)
        * ``tension``  → ``pulse_rate_hz``    (:data:`_MIN_RATE_HZ` – :data:`_MAX_RATE_HZ`)
        * ``tension``  → ``sharpness``        (0.0 – 1.0)
        * ``spatial_balance`` = 0.0            (crowd is omnidirectional)
        """
        intensity = int(round(_lerp(_MIN_INTENSITY, _MAX_INTENSITY, estimate.arousal)))
        rate_hz = _lerp(_MIN_RATE_HZ, _MAX_RATE_HZ, estimate.tension)
        return HapticPrimitive(
            pulse_rate_hz=round(rate_hz, 3),
            intensity=intensity,
            spatial_balance=0.0,
            sharpness=round(float(np.clip(estimate.tension, 0.0, 1.0)), 3),
        )

    def reset(self) -> None:
        """Clear all internal state.  Call between songs or listening sessions."""
        self._prev_spectrum = None
        self._prev_rms = 0.0
        self._onset_times.clear()
        self._frame_index = 0


# ── Private helpers ───────────────────────────────────────────────────────────


def _rms_to_arousal(rms: float) -> float:
    """Map RMS amplitude [0, ∞) to arousal [0, 1] on a log scale.

    The log scale approximates how human loudness perception works (roughly
    logarithmic with level).  Calibration anchors:

    * rms ≈ 0.001 (very quiet)  → arousal ≈ 0.33
    * rms ≈ 0.010 (moderate)    → arousal ≈ 0.67
    * rms ≈ 0.100 (loud)        → arousal ≈ 1.00
    """
    if rms < _SILENCE_FLOOR:
        return 0.0
    log_rms = float(np.log10(rms + _SILENCE_FLOOR))
    return (log_rms - _AROUSAL_LOG_LO) / _AROUSAL_LOG_SPAN


def _lerp(lo: float, hi: float, t: float) -> float:
    """Linear interpolation from *lo* to *hi* at fraction *t*."""
    return lo + (hi - lo) * float(t)
