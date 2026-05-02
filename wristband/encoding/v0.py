"""
v0.py – reference implementation of the OpenHear wristband **v0** haptic encoder.

This module is the executable counterpart to ``v0_spec.md``.  Where the
specification states the algorithm in prose, this file provides the
canonical numerical implementation that all psychoacoustic experiments,
replication studies and future encoder revisions must compare against.

Design summary (see ``v0_spec.md`` for full detail):

    * Mono float32 audio (``[-1.0, 1.0]``) at any sample rate is split
      into ``N_BANDS`` (default 4) octave-spaced bands using zero-phase
      FFT bin masking.
    * Each band envelope is computed as the per-frame RMS of the
      band-passed signal.
    * Envelopes are converted to dBFS, clipped to a published dynamic
      window (``DB_FLOOR`` ... ``DB_CEILING``), and linearly mapped to
      ``[0.0, 1.0]`` motor drive values.
    * Motor positions are arranged around the wrist in ascending
      frequency order: motor 0 = lowest band (anatomical *ulnar /
      pinky side*), motor N-1 = highest band (anatomical *radial /
      thumb side*).  This ordering is fixed and part of the spec.

The encoder is intentionally simple, deterministic, and dependency-free
(numpy only).  It is the **falsifiable baseline**: future encoders must
beat v0 on the published psychoacoustic battery to be promoted.

Safety: the encoder produces normalised drive values in ``[0, 1]`` only.
Conversion to physical motor PWM is the responsibility of the firmware
layer and must be clamped per the actuator's safe-operating envelope.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# ---------------------------------------------------------------------------
# Spec constants — frozen for v0.  Do NOT change these in place; create v1.
# ---------------------------------------------------------------------------

#: Number of frequency bands / motors in the v0 encoder.
N_BANDS: int = 4

#: Default crossover frequencies (Hz) between adjacent bands.
#: 4 bands → 3 crossovers.  Roughly octave-spaced, covering the speech
#: intelligibility range (250 Hz – 4 kHz) plus low-rumble headroom below.
DEFAULT_CROSSOVERS_HZ: tuple[float, ...] = (500.0, 1000.0, 2000.0)

#: Lower bound of the encoder's dynamic window in dBFS.
#: Envelopes below this level produce zero motor drive.
DB_FLOOR: float = -60.0

#: Upper bound of the encoder's dynamic window in dBFS.
#: Envelopes at or above this level produce full motor drive.
DB_CEILING: float = -10.0

#: Default analysis frame length in samples.
#: 1024 samples @ 16 kHz ≈ 64 ms — the minimum interval at which a
#: typical wrist LRA can render a perceptibly distinct intensity step.
DEFAULT_FRAME_LENGTH: int = 1024


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class V0EncoderConfig:
    """Frozen configuration for the v0 wristband encoder.

    All fields have spec-mandated defaults; overriding them produces a
    *non-conformant* encoder that must be reported as such in any
    psychoacoustic results.

    Attributes:
        sample_rate:    Input audio sample rate in Hz.
        frame_length:   Number of samples consumed per :meth:`encode` call.
        crossovers_hz:  Inter-band crossover frequencies in Hz, strictly
            increasing, length ``N_BANDS - 1``.
        db_floor:       dBFS level mapped to motor drive 0.0.
        db_ceiling:     dBFS level mapped to motor drive 1.0.
    """

    sample_rate: int = 16_000
    frame_length: int = DEFAULT_FRAME_LENGTH
    crossovers_hz: tuple[float, ...] = field(default=DEFAULT_CROSSOVERS_HZ)
    db_floor: float = DB_FLOOR
    db_ceiling: float = DB_CEILING

    def __post_init__(self) -> None:  # pragma: no cover - exercised in tests
        if self.sample_rate <= 0:
            raise ValueError(f"sample_rate must be > 0, got {self.sample_rate}")
        if self.frame_length < 16:
            raise ValueError(f"frame_length must be >= 16 samples, got {self.frame_length}")
        if len(self.crossovers_hz) != N_BANDS - 1:
            raise ValueError(
                f"crossovers_hz must have length {N_BANDS - 1}, got {len(self.crossovers_hz)}"
            )
        if any(b <= a for a, b in zip(self.crossovers_hz, self.crossovers_hz[1:])):
            raise ValueError(f"crossovers_hz must be strictly increasing, got {self.crossovers_hz}")
        if self.crossovers_hz[0] <= 0.0:
            raise ValueError(f"crossovers_hz[0] must be > 0, got {self.crossovers_hz[0]}")
        nyquist = self.sample_rate / 2.0
        if self.crossovers_hz[-1] >= nyquist:
            raise ValueError(
                f"highest crossover {self.crossovers_hz[-1]} must be < Nyquist {nyquist}"
            )
        if self.db_ceiling <= self.db_floor:
            raise ValueError(f"db_ceiling ({self.db_ceiling}) must be > db_floor ({self.db_floor})")


# ---------------------------------------------------------------------------
# Encoder
# ---------------------------------------------------------------------------


class V0Encoder:
    """Reference implementation of the v0 wrist-haptic encoder.

    The encoder is **stateless across frames**: each call to
    :meth:`encode` operates independently on a single frame of audio.
    This is a deliberate choice to keep the v0 baseline trivially
    parallelisable and exactly reproducible from a fixed input vector.

    Example:

        >>> import numpy as np
        >>> enc = V0Encoder()
        >>> frame = np.zeros(1024, dtype=np.float32)
        >>> drives = enc.encode(frame)
        >>> drives.shape
        (4,)
        >>> bool(np.all(drives == 0.0))
        True
    """

    def __init__(self, config: V0EncoderConfig | None = None) -> None:
        self.config = config if config is not None else V0EncoderConfig()
        self._band_masks = self._build_band_masks(self.config)

    # ------------------------------------------------------------------
    # Public API

    @property
    def n_bands(self) -> int:
        """Number of motors driven by this encoder (always :data:`N_BANDS`)."""
        return N_BANDS

    @property
    def band_edges_hz(self) -> tuple[tuple[float, float], ...]:
        """Inclusive frequency edges of each band, low → high.

        Edge 0 of band 0 is 0 Hz; the upper edge of the final band is
        the Nyquist frequency.  These are the bands used by
        :meth:`encode`.
        """
        edges: list[tuple[float, float]] = []
        prev = 0.0
        for f in self.config.crossovers_hz:
            edges.append((prev, f))
            prev = f
        edges.append((prev, self.config.sample_rate / 2.0))
        return tuple(edges)

    def encode(self, frame: np.ndarray) -> np.ndarray:
        """Encode a single audio frame into per-motor drive values.

        Args:
            frame:  1-D numeric array of normalised PCM samples in
                ``[-1.0, 1.0]``.  Length must equal
                ``self.config.frame_length``.

        Returns:
            1-D ``float32`` array of length :data:`N_BANDS`, one drive
            value per motor in ``[0.0, 1.0]``.  Motor ordering is fixed
            (low → high frequency, ulnar → radial around the wrist).
        """
        frame = np.asarray(frame, dtype=np.float32)
        if frame.ndim != 1:
            raise ValueError(f"frame must be 1-D, got shape {frame.shape}")
        if frame.shape[0] != self.config.frame_length:
            raise ValueError(
                f"frame length {frame.shape[0]} != configured "
                f"frame_length {self.config.frame_length}"
            )

        # Real FFT once; reuse spectrum across all bands.
        spectrum = np.fft.rfft(frame)

        drives = np.empty(N_BANDS, dtype=np.float32)
        for i, mask in enumerate(self._band_masks):
            band_spectrum = spectrum * mask
            band_signal = np.fft.irfft(band_spectrum, n=self.config.frame_length)
            rms = float(np.sqrt(np.mean(band_signal.astype(np.float64) ** 2)))
            drives[i] = self._rms_to_drive(rms)

        return drives

    # ------------------------------------------------------------------
    # Internals

    @staticmethod
    def _build_band_masks(config: V0EncoderConfig) -> list[np.ndarray]:
        """Pre-compute one rfft-domain band-pass mask per band."""
        n_bins = config.frame_length // 2 + 1
        freqs = np.fft.rfftfreq(config.frame_length, d=1.0 / config.sample_rate)

        edges_low: list[float] = [0.0, *list(config.crossovers_hz)]
        edges_high: list[float] = [*list(config.crossovers_hz), config.sample_rate / 2.0]

        masks: list[np.ndarray] = []
        for low, high in zip(edges_low, edges_high):
            mask = np.zeros(n_bins, dtype=np.float32)
            # Left edge inclusive, right edge exclusive — except the
            # final band which includes Nyquist so that no energy is
            # silently discarded.
            if high >= config.sample_rate / 2.0:
                in_band = (freqs >= low) & (freqs <= high)
            else:
                in_band = (freqs >= low) & (freqs < high)
            mask[in_band] = 1.0
            masks.append(mask)
        return masks

    def _rms_to_drive(self, rms: float) -> float:
        """Map a linear RMS magnitude to a normalised motor drive value.

        The mapping is a clipped linear interpolation from
        ``db_floor``→0 to ``db_ceiling``→1 in the dBFS domain.  Silence
        (``rms == 0``) maps deterministically to 0.0 without taking
        ``log10(0)``.
        """
        if rms <= 0.0:
            return 0.0
        db = 20.0 * np.log10(rms)
        if db <= self.config.db_floor:
            return 0.0
        if db >= self.config.db_ceiling:
            return 1.0
        span = self.config.db_ceiling - self.config.db_floor
        return float((db - self.config.db_floor) / span)
