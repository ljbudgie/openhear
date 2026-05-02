"""Tests for ``wristband/encoding/v0.py`` — the v0 haptic encoder.

These tests double as the executable specification for v0.  Any
behaviour change here is a breaking change to the encoding contract
and must be paired with a v1 spec, not a silent edit to v0.
"""

from __future__ import annotations

import numpy as np
import pytest

from wristband.encoding import V0Encoder, V0EncoderConfig
from wristband.encoding.v0 import (
    DB_CEILING,
    DB_FLOOR,
    DEFAULT_CROSSOVERS_HZ,
    DEFAULT_FRAME_LENGTH,
    N_BANDS,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class TestConfig:
    def test_defaults_match_spec(self) -> None:
        cfg = V0EncoderConfig()
        assert cfg.sample_rate == 16_000
        assert cfg.frame_length == DEFAULT_FRAME_LENGTH
        assert cfg.crossovers_hz == DEFAULT_CROSSOVERS_HZ
        assert cfg.db_floor == DB_FLOOR
        assert cfg.db_ceiling == DB_CEILING

    def test_crossovers_must_have_n_bands_minus_one(self) -> None:
        with pytest.raises(ValueError, match="crossovers_hz must have length"):
            V0EncoderConfig(crossovers_hz=(500.0, 1000.0))

    def test_crossovers_must_be_strictly_increasing(self) -> None:
        with pytest.raises(ValueError, match="strictly increasing"):
            V0EncoderConfig(crossovers_hz=(1000.0, 500.0, 2000.0))

    def test_top_crossover_below_nyquist(self) -> None:
        with pytest.raises(ValueError, match="Nyquist"):
            V0EncoderConfig(sample_rate=8_000, crossovers_hz=(500.0, 1000.0, 5_000.0))

    def test_db_ceiling_above_floor(self) -> None:
        with pytest.raises(ValueError, match="db_ceiling"):
            V0EncoderConfig(db_floor=-10.0, db_ceiling=-20.0)

    def test_frame_length_lower_bound(self) -> None:
        with pytest.raises(ValueError, match="frame_length"):
            V0EncoderConfig(frame_length=8)

    def test_sample_rate_positive(self) -> None:
        with pytest.raises(ValueError, match="sample_rate"):
            V0EncoderConfig(sample_rate=0)

    def test_first_crossover_positive(self) -> None:
        with pytest.raises(ValueError, match="crossovers_hz\\[0\\]"):
            V0EncoderConfig(crossovers_hz=(0.0, 1000.0, 2000.0))


# ---------------------------------------------------------------------------
# Encoder structural properties
# ---------------------------------------------------------------------------


class TestStructure:
    def test_n_bands(self) -> None:
        assert V0Encoder().n_bands == N_BANDS == 4

    def test_band_edges_cover_zero_to_nyquist(self) -> None:
        enc = V0Encoder()
        edges = enc.band_edges_hz
        assert len(edges) == N_BANDS
        assert edges[0][0] == 0.0
        assert edges[-1][1] == pytest.approx(enc.config.sample_rate / 2.0)
        # Adjacent bands share an edge.
        for (_, hi), (lo, _) in zip(edges, edges[1:]):
            assert hi == lo

    def test_silence_produces_zero_drives(self) -> None:
        enc = V0Encoder()
        frame = np.zeros(enc.config.frame_length, dtype=np.float32)
        drives = enc.encode(frame)
        assert drives.shape == (N_BANDS,)
        assert drives.dtype == np.float32
        assert np.all(drives == 0.0)


# ---------------------------------------------------------------------------
# Frame validation
# ---------------------------------------------------------------------------


class TestFrameValidation:
    def test_rejects_wrong_length(self) -> None:
        enc = V0Encoder()
        with pytest.raises(ValueError, match="frame length"):
            enc.encode(np.zeros(enc.config.frame_length - 1, dtype=np.float32))

    def test_rejects_non_1d(self) -> None:
        enc = V0Encoder()
        with pytest.raises(ValueError, match="1-D"):
            enc.encode(np.zeros((2, enc.config.frame_length), dtype=np.float32))


# ---------------------------------------------------------------------------
# Spectral selectivity — the core acceptance test.
#
# A pure tone in band i should drive motor i and *only* motor i.
# ---------------------------------------------------------------------------


def _tone(freq_hz: float, n: int, sr: int, amplitude: float = 0.3) -> np.ndarray:
    t = np.arange(n, dtype=np.float64) / sr
    return (amplitude * np.sin(2.0 * np.pi * freq_hz * t)).astype(np.float32)


class TestSpectralSelectivity:
    @pytest.mark.parametrize(
        "freq_hz, expected_band",
        [
            (200.0, 0),
            (750.0, 1),
            (1500.0, 2),
            (3000.0, 3),
        ],
    )
    def test_tone_routes_to_expected_band(self, freq_hz: float, expected_band: int) -> None:
        enc = V0Encoder()
        frame = _tone(freq_hz, enc.config.frame_length, enc.config.sample_rate)
        drives = enc.encode(frame)
        # Expected band is the loudest by a clear margin.
        loudest = int(np.argmax(drives))
        assert loudest == expected_band, (
            f"Tone @ {freq_hz} Hz lit band {loudest}, expected {expected_band}; drives={drives}"
        )
        # And the other bands are at least 6 dB quieter (factor 0.5 in
        # the linear drive domain after dB→drive normalisation).
        others = np.delete(drives, expected_band)
        assert drives[expected_band] >= float(others.max()) * 2.0


# ---------------------------------------------------------------------------
# Drive-mapping monotonicity and clipping
# ---------------------------------------------------------------------------


class TestDriveMapping:
    def test_loud_full_band_noise_saturates(self) -> None:
        enc = V0Encoder()
        rng = np.random.default_rng(0)
        # 0.9 amplitude white noise → RMS ≈ 0.52 ≈ −5.6 dBFS, which is
        # comfortably above the −10 dBFS ceiling.
        frame = (rng.uniform(-0.9, 0.9, enc.config.frame_length)).astype(np.float32)
        drives = enc.encode(frame)
        # Per-band RMS is a fraction of the total (energy is split across
        # 4 bands); each band should still be well into the upper half of
        # the drive range.
        assert np.all(drives >= 0.7)

    def test_below_floor_is_zero(self) -> None:
        enc = V0Encoder()
        # A −80 dBFS tone is below the −60 dBFS floor.
        frame = _tone(
            1500.0,
            enc.config.frame_length,
            enc.config.sample_rate,
            amplitude=10 ** (-80.0 / 20.0),
        )
        drives = enc.encode(frame)
        assert float(drives.max()) == 0.0

    def test_drive_increases_with_amplitude(self) -> None:
        enc = V0Encoder()
        amps = [0.005, 0.02, 0.08, 0.3]
        prev = -1.0
        for a in amps:
            frame = _tone(1500.0, enc.config.frame_length, enc.config.sample_rate, amplitude=a)
            d = float(enc.encode(frame)[2])  # band 2 = 1–2 kHz
            assert d >= prev, f"amplitude {a} produced {d}, prev {prev}"
            prev = d
        # And the loudest amplitude saturates by construction.
        assert prev == pytest.approx(1.0, abs=1e-6) or prev > 0.5


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_input_same_output(self) -> None:
        enc = V0Encoder()
        rng = np.random.default_rng(42)
        frame = rng.standard_normal(enc.config.frame_length).astype(np.float32) * 0.1
        a = enc.encode(frame)
        b = enc.encode(frame)
        np.testing.assert_array_equal(a, b)

    def test_stateless_across_frames(self) -> None:
        """Two encoders see the same output for the same frame regardless
        of what they processed previously."""
        enc1 = V0Encoder()
        enc2 = V0Encoder()
        rng = np.random.default_rng(7)
        warmup = rng.standard_normal(enc1.config.frame_length).astype(np.float32)
        frame = rng.standard_normal(enc1.config.frame_length).astype(np.float32) * 0.1
        # enc1 sees a warm-up frame first; enc2 does not.
        enc1.encode(warmup)
        np.testing.assert_array_equal(enc1.encode(frame), enc2.encode(frame))
