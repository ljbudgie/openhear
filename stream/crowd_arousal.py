"""
crowd_arousal.py – continuous crowd-energy estimation for haptic rendering.

This is an acoustic texture estimator, not a crowd classifier or emotion
detector.  Public field names are retained for compatibility:

    arousal         — log recorded RMS level, 0.0 to 1.0
    tension         — smoothed spectral-shape change, 0.0 to 1.0
    onset_rate_hz   — rising-envelope detections per second over the last 2 s

Level drives intensity; spectral change drives pulse rate and sharpness.
Balance is centred by design, not because every crowd is omnidirectional.
Zero arousal means motors off, not a minimum-strength background buzz.

Algorithm:

1. **RMS → arousal.**  Log-level mapping with a configurable silence gate.
2. **Spectral shape → tension.**  Hann-windowed magnitudes are pooled into
   up to 32 bands and normalised to unit sum before temporal smoothing.
   Positive departure from the recent smoothed shape is itself smoothed.  Changing only
   gain does not change the shape; stationary noise still has a residual.
3. **Envelope rises → onset_rate_hz.**  A >15% RMS rise, including emergence
   from observed silence, starts a detection.  A latch, 150 ms refractory
   interval and 100 ms of <=5% rises re-arm it, avoiding repeated counts
   during sustained steep ramps.  The first frame only primes the detector.

Limitations (honest):
    - Gain, distance and compression affect recorded level.  Compression can
      hide onsets; gain pumping can create them.  Detections are not a count
      of distinct real-world events.
    - No emotional tension, excitement or valence is inferred.
    - Silence gating trades sensitivity for stability.  Calibrate it for the
      microphone; the default 1e-4 RMS is not a sound-pressure threshold.
    - Band pooling and smoothing reduce jitter but lose fine/fast changes.
      These are engineering defaults, not validated perceptual thresholds.
      See HARDWARE.md for the outstanding bench and wearer calibration.

Usage::

    estimator = CrowdArousalEstimator(sample_rate=44_100, frame_size=2048)
    playback = HapticPlayback()  # from stream.haptic_playback
    # In the audio callback (using the same monotonic clock as playback):
    estimate = estimator.update(frame)
    playback.set_texture(estimator.to_primitive(estimate), now_ms=now_ms)
    # In a separate, frequent, serialised playback loop:
    for event in playback.poll(now_ms):
        send_packet(event.packet)

All texture and alert output must share that playback instance.  Polling only
once per audio frame can miss short pulses; do not queue a new one-second
``to_events`` schedule on each update.  The caller owns transport timing and
must send ``playback.stop(now_ms)`` events on shutdown.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from numbers import Integral

import numpy as np

from stream.haptic_primitive import HapticPrimitive

# ── Constants ─────────────────────────────────────────────────────────────────

#: Rolling window over which onset rate is computed, in seconds.
_ONSET_HISTORY_S: float = 2.0

#: Provisional minimum for active texture; silence uses zero.
_MIN_INTENSITY: int = 40

#: Provisional ceiling.  Alert priority is enforced by playback, not amplitude.
_MAX_INTENSITY: int = 160

#: Provisional slowest texture rate; requires hardware/wearer calibration.
_MIN_RATE_HZ: float = 0.5

#: Provisional fastest texture rate, not a universal perceptual threshold.
_MAX_RATE_HZ: float = 12.0

#: Numerical floor for the logarithm, separate from the microphone silence gate.
_SILENCE_FLOOR: float = 1e-6
_DEFAULT_SILENCE_RMS: float = 1e-4
_SPECTRUM_SMOOTHING_S: float = 0.15
_TENSION_SMOOTHING_S: float = 0.10
_ONSET_REFRACTORY_S: float = 0.15
_ONSET_REARM_S: float = 0.10
_ONSET_REARM_THRESHOLD: float = 0.05

#: Relative RMS rise required to start an envelope-rise detection (15%).
_ONSET_THRESHOLD: float = 0.15

# Log scale calibration: maps RMS 0.001 → arousal ~0.33,
# RMS 0.01 → ~0.67, RMS 0.1 → ~1.0 for audio in the ±1 float range.
_AROUSAL_LOG_LO: float = -4.0  # log10 of the "silence" anchor
_AROUSAL_LOG_SPAN: float = 3.0  # log10(0.1) − log10(0.0001)


# ── Output type ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ArousalEstimate:
    """One acoustic-proxy reading, not an emotion estimate.

    Attributes:
        arousal:       Log recorded level, 0.0 (muted) to 1.0 (saturated).
        tension:       Smoothed spectral-shape change, 0.0 to 1.0.
        onset_rate_hz: Envelope-rise detections per second over a fixed 2 s
                       denominator, including during startup; diagnostic only.
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
        silence_rms: Frames at or below this RMS are immediately muted.
                     Finite and in [1e-6, 1.0]; default 1e-4.
    """

    def __init__(
        self,
        *,
        sample_rate: int = 44_100,
        frame_size: int = 2048,
        silence_rms: float = _DEFAULT_SILENCE_RMS,
    ) -> None:
        for name, value in (("sample_rate", sample_rate), ("frame_size", frame_size)):
            if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
                raise ValueError(f"{name} must be a positive integer, got {value}.")
        if not np.isfinite(silence_rms) or not _SILENCE_FLOOR <= silence_rms <= 1.0:
            raise ValueError("silence_rms must be finite and in [1e-6, 1.0].")
        self._sample_rate = sample_rate
        self._frame_size = frame_size
        self._silence_rms = silence_rms
        self._frame_duration_s: float = frame_size / sample_rate
        # Tiny frames still have a nonzero window.
        self._window = np.hanning(frame_size) if frame_size > 2 else np.ones(frame_size)
        self._band_starts = np.linspace(
            0,
            frame_size // 2 + 1,
            min(32, frame_size // 2 + 1),
            endpoint=False,
            dtype=int,
        )
        self._spectrum_alpha = -np.expm1(-self._frame_duration_s / _SPECTRUM_SMOOTHING_S)
        self._tension_alpha = -np.expm1(-self._frame_duration_s / _TENSION_SMOOTHING_S)
        # Rolling magnitude spectrum for spectral-flux computation
        self._prev_spectrum: "np.ndarray | None" = None
        self._tension: float = 0.0
        # RMS of previous frame for onset detection
        self._prev_rms: float = 0.0
        # Queue of onset timestamps (in seconds) for rolling rate estimate
        _max_frames = int(_ONSET_HISTORY_S / self._frame_duration_s) + 2
        self._onset_times: deque[float] = deque(maxlen=_max_frames)
        self._frame_index: int = 0
        self._onset_armed = True
        self._settled_s = 0.0
        self._last_onset_s = float("-inf")

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
            ValueError: If the frame is not real, finite, 1-D, or exactly
                        ``frame_size`` samples.  Rejected frames do not change state.
        """
        if np.iscomplexobj(audio_frame):
            raise ValueError("audio_frame must contain real samples.")
        frame = np.asarray(audio_frame, dtype=np.float64)
        if frame.ndim != 1:
            raise ValueError(f"audio_frame must be 1-D, got shape {frame.shape}.")
        if len(frame) != self._frame_size:
            raise ValueError(f"audio_frame must contain {self._frame_size} samples.")
        if not np.all(np.isfinite(frame)):
            raise ValueError("audio_frame must contain finite samples.")

        # ── 1. RMS energy → arousal ──────────────────────────────────────────
        peak = float(np.max(np.abs(frame)))
        scaled = frame / peak if peak else frame
        rms = peak * float(np.sqrt(np.mean(scaled**2)))
        silent = rms <= self._silence_rms
        arousal = 0.0 if silent else float(np.clip(_rms_to_arousal(rms), 0.0, 1.0))

        # ── 2. Spectral flux → tension ───────────────────────────────────────
        spectrum = np.add.reduceat(np.abs(np.fft.rfft(scaled * self._window)), self._band_starts)
        total = float(spectrum.sum())
        if silent or total == 0.0:
            self._prev_spectrum = None
            self._tension = 0.0
        else:
            spectrum /= total
            if self._prev_spectrum is None:
                self._tension = 0.0
            else:
                flux = float(np.maximum(spectrum - self._prev_spectrum, 0.0).sum())
                spectrum = self._prev_spectrum + self._spectrum_alpha * (
                    spectrum - self._prev_spectrum
                )
                self._tension += self._tension_alpha * (flux - self._tension)
            self._prev_spectrum = spectrum

        # ── 3. Onset detection → onset_rate_hz ───────────────────────────────
        now_s = self._frame_index * self._frame_duration_s
        relative_rise = (rms - self._prev_rms) / max(self._prev_rms, self._silence_rms)
        if silent:
            self._onset_armed = True
            self._settled_s = 0.0
        elif self._frame_index > 0:
            rising = self._prev_rms <= self._silence_rms or relative_rise > _ONSET_THRESHOLD
            if rising and self._onset_armed and now_s - self._last_onset_s >= _ONSET_REFRACTORY_S:
                self._onset_times.append(now_s)
                self._last_onset_s = now_s
                self._onset_armed = False
            if relative_rise <= _ONSET_REARM_THRESHOLD:
                self._settled_s += self._frame_duration_s
                if self._settled_s >= _ONSET_REARM_S:
                    self._onset_armed = True
            else:
                self._settled_s = 0.0
        self._prev_rms = rms

        window_start = now_s - _ONSET_HISTORY_S
        while self._onset_times and self._onset_times[0] <= window_start:
            self._onset_times.popleft()
        onset_rate_hz = len(self._onset_times) / _ONSET_HISTORY_S

        self._frame_index += 1
        return ArousalEstimate(
            arousal=round(arousal, 4),
            tension=round(float(np.clip(self._tension, 0.0, 1.0)), 4),
            onset_rate_hz=round(onset_rate_hz, 4),
        )

    def to_primitive(self, estimate: ArousalEstimate) -> HapticPrimitive:
        """Map a crowd-state estimate to a :class:`~stream.haptic_primitive.HapticPrimitive`.

        Mapping (linear for active texture; zero arousal is muted):

        * ``arousal``  → ``intensity``        (:data:`_MIN_INTENSITY` – :data:`_MAX_INTENSITY`)
        * ``tension``  → ``pulse_rate_hz``    (:data:`_MIN_RATE_HZ` – :data:`_MAX_RATE_HZ`)
        * ``tension``  → ``sharpness``        (0.0 – 1.0)
        * ``spatial_balance`` = 0.0            (deliberately non-directional)
        * ``onset_rate_hz`` remains diagnostic; it does not drive a motor.
        """
        for name in ("arousal", "tension"):
            value = getattr(estimate, name)
            if not np.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1].")
        intensity = (
            int(round(_lerp(_MIN_INTENSITY, _MAX_INTENSITY, estimate.arousal)))
            if estimate.arousal > 0.0
            else 0
        )
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
        self._tension = 0.0
        self._prev_rms = 0.0
        self._onset_times.clear()
        self._frame_index = 0
        self._onset_armed = True
        self._settled_s = 0.0
        self._last_onset_s = float("-inf")


# ── Private helpers ───────────────────────────────────────────────────────────


def _rms_to_arousal(rms: float) -> float:
    """Map RMS amplitude [0, ∞) to arousal [0, 1] on a log scale.

    Digital-level anchors (not calibrated sound-pressure or perceived loudness):

    * rms ≈ 0.001 → arousal ≈ 0.33
    * rms ≈ 0.010 → arousal ≈ 0.67
    * rms ≈ 0.100 → arousal ≈ 1.00
    """
    if rms < _SILENCE_FLOOR:
        return 0.0
    log_rms = float(np.log10(rms + _SILENCE_FLOOR))
    return (log_rms - _AROUSAL_LOG_LO) / _AROUSAL_LOG_SPAN


def _lerp(lo: float, hi: float, t: float) -> float:
    """Linear interpolation from *lo* to *hi* at fraction *t*."""
    return lo + (hi - lo) * float(t)
