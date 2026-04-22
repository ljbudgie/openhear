"""
compare.py – real-time voice comparison engine for OpenHear.

Accepts a live VoiceSnapshot and a ReferenceProfile, then computes
frequency-band energy differences, identifies underused formant regions,
and produces a similarity score.

The comparison is a training tool, not a judgement.  The reference is a
mirror — it shows the user where their vocal energy sits relative to a
target they chose.  The user decides what to do with that information.

Frequency bands:
  - Low:  80–300 Hz   (fundamental, chest resonance)
  - Mid:  300–2000 Hz (vowel formants F1/F2, vocal body)
  - High: 2000–8000 Hz (consonant articulation, sibilance, breathiness)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from voice import config
from voice.analyser import VoiceSnapshot
from voice.reference import ReferenceProfile

# ── Frequency band edges (Hz) ───────────────────────────────────────────────

BAND_LOW = (80.0, 300.0)
BAND_MID = (300.0, 2000.0)
BAND_HIGH = (2000.0, 8000.0)

BANDS: dict[str, tuple[float, float]] = {
    "low": BAND_LOW,
    "mid": BAND_MID,
    "high": BAND_HIGH,
}


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class VoiceComparison:
    """Result of comparing a VoiceSnapshot against a ReferenceProfile.

    Attributes:
        band_differences:   Energy difference (dB) per band, computed as
                            user_energy − reference_energy.  Negative values
                            mean the user is quieter than the reference in
                            that band.
        underused_formants: List of formant frequencies (Hz) from the
                            reference that the user is not producing or is
                            significantly weaker in.
        resonance_gap_hz:   List of frequency values (Hz) where the gap
                            between user and reference exceeds the gap
                            threshold.
        similarity_score:   Overall spectral similarity between 0.0 (no
                            match) and 1.0 (identical envelope shape).
    """
    band_differences: dict[str, float] = field(default_factory=dict)
    underused_formants: list[float] = field(default_factory=list)
    resonance_gap_hz: list[float] = field(default_factory=list)
    similarity_score: float = 0.0


# ── Internal helpers ─────────────────────────────────────────────────────────

def _band_energy(envelope_db: np.ndarray, freqs: np.ndarray,
                 low_hz: float, high_hz: float) -> float:
    """Return the mean energy (dB) within a frequency band."""
    mask = (freqs >= low_hz) & (freqs <= high_hz)
    if not np.any(mask):
        return -100.0
    return float(np.mean(envelope_db[mask]))


def _envelope_freqs(envelope: np.ndarray,
                    sample_rate: int = config.SAMPLE_RATE,
                    frame_size: int = config.FRAME_BUFFER) -> np.ndarray:
    """Return the frequency axis matching an envelope array."""
    n_bins = len(envelope)
    return np.fft.rfftfreq(frame_size, d=1.0 / sample_rate).astype(np.float32)[:n_bins]


# ── Public API ───────────────────────────────────────────────────────────────

def compare(snapshot: VoiceSnapshot,
            reference: ReferenceProfile,
            sample_rate: int = config.SAMPLE_RATE,
            frame_size: int = config.FRAME_BUFFER,
            match_tolerance_db: float = config.MATCH_TOLERANCE_DB,
            gap_threshold_db: float = config.GAP_THRESHOLD_DB) -> VoiceComparison:
    """Compare a live voice snapshot against a reference profile.

    Args:
        snapshot:          Current VoiceSnapshot from the analyser.
        reference:         Target ReferenceProfile to compare against.
        sample_rate:       Sample rate used during analysis.
        frame_size:        FFT frame size used during analysis.
        match_tolerance_db:
                           Energy difference (dB) within which a band is
                           considered "matched".
        gap_threshold_db:  Energy difference (dB) above which a gap is
                           flagged as significant.

    Returns:
        A populated VoiceComparison dataclass.
    """
    user_env = snapshot.spectral_envelope
    ref_env = reference.spectral_envelope

    # If either envelope is empty, return a zero comparison.
    if len(user_env) == 0 or len(ref_env) == 0:
        return VoiceComparison()

    # Align lengths — use the shorter of the two.
    n_bins = min(len(user_env), len(ref_env))
    user_env = user_env[:n_bins]
    ref_env = ref_env[:n_bins]
    freqs = _envelope_freqs(user_env, sample_rate, frame_size)[:n_bins]

    # ── Band energy differences ──────────────────────────────────────────
    band_diffs: dict[str, float] = {}
    for name, (lo, hi) in BANDS.items():
        user_e = _band_energy(user_env, freqs, lo, hi)
        ref_e = _band_energy(ref_env, freqs, lo, hi)
        band_diffs[name] = float(user_e - ref_e)

    # ── Underused formants ───────────────────────────────────────────────
    underused: list[float] = []
    for ref_formant in reference.avg_formants:
        # Find the nearest bin to this formant frequency.
        if len(freqs) == 0:
            continue
        idx = int(np.argmin(np.abs(freqs - ref_formant)))
        if idx < n_bins:
            diff = float(user_env[idx] - ref_env[idx])
            if diff < -match_tolerance_db:
                underused.append(ref_formant)

    # ── Resonance gaps ───────────────────────────────────────────────────
    diff_curve = user_env - ref_env
    gap_mask = diff_curve < -gap_threshold_db
    resonance_gaps = [float(f) for f in freqs[gap_mask]]

    # ── Similarity score ─────────────────────────────────────────────────
    # Normalised cross-correlation of the two envelopes, mapped to [0, 1].
    user_centered = user_env - np.mean(user_env)
    ref_centered = ref_env - np.mean(ref_env)

    user_norm = np.linalg.norm(user_centered)
    ref_norm = np.linalg.norm(ref_centered)

    if user_norm < 1e-10 or ref_norm < 1e-10:
        similarity = 0.0
    else:
        correlation = float(np.dot(user_centered, ref_centered) /
                            (user_norm * ref_norm))
        # Map from [-1, 1] correlation to [0, 1] similarity.
        similarity = float(np.clip((correlation + 1.0) / 2.0, 0.0, 1.0))

    return VoiceComparison(
        band_differences=band_diffs,
        underused_formants=underused,
        resonance_gap_hz=resonance_gaps,
        similarity_score=similarity,
    )
