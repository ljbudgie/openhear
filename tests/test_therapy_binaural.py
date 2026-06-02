"""Tests for the therapy package: protocol model + binaural generation."""

from __future__ import annotations

import wave

import numpy as np
import pytest
from click.testing import CliRunner

from audiogram.audiogram import Audiogram
from therapy.binaural import (
    SAFE_PEAK_AMPLITUDE,
    BinauralPrescription,
    dominant_frequencies,
    generate_binaural,
    prescribe_binaural,
)
from therapy.binaural_cli import main
from therapy.protocol import (
    BRAINWAVE_PROTOCOLS,
    ContraindicationError,
    EvidenceGrade,
    TherapeuticProtocol,
    band_for,
    get_protocol,
)

# ── Protocol model ──────────────────────────────────────────────────────────


def test_protocol_validates_fields():
    with pytest.raises(ValueError):
        TherapeuticProtocol(name="x", frequencies=())
    with pytest.raises(ValueError):
        TherapeuticProtocol(name="x", frequencies=(-1.0,))
    with pytest.raises(ValueError):
        TherapeuticProtocol(name="x", frequencies=(10.0,), duty_cycle=0.0)
    with pytest.raises(ValueError):
        TherapeuticProtocol(name="x", frequencies=(10.0,), session_length_s=0)


def test_evidence_grade_is_ordered_and_conservative():
    assert EvidenceGrade.ANECDOTAL < EvidenceGrade.EMERGING < EvidenceGrade.ESTABLISHED
    # No bundled protocol overclaims as "established".
    assert all(p.evidence_grade < EvidenceGrade.ESTABLISHED for p in BRAINWAVE_PROTOCOLS.values())


def test_band_classification():
    assert band_for(2.0) == "delta"
    assert band_for(10.0) == "alpha"
    assert band_for(40.0) == "gamma"
    assert band_for(0.1) is None


def test_seizure_contraindication_is_gated_on_every_preset():
    for proto in BRAINWAVE_PROTOCOLS.values():
        assert proto.is_contraindicated({"epilepsy"})
        with pytest.raises(ContraindicationError):
            proto.gate({"Epilepsy"})  # case-insensitive


def test_gate_allows_unrelated_conditions():
    get_protocol("alpha_relax").gate({"flat_feet", "myopia"})  # no raise


def test_get_protocol_unknown_key():
    with pytest.raises(KeyError):
        get_protocol("nope")


# ── Binaural generation ─────────────────────────────────────────────────────


def test_generates_correct_shape_and_length():
    sr = 44_100
    sig = generate_binaural(300.0, 10.0, 1.0, sample_rate=sr)
    assert sig.shape == (sr, 2)
    assert sig.dtype == np.float32
    assert np.abs(sig).max() <= 1.0


def test_beat_is_difference_of_ear_frequencies():
    sr = 44_100
    # 2-second window for fine FFT resolution; no fade so peaks are clean.
    sig = generate_binaural(300.0, 10.0, 2.0, sample_rate=sr, fade_s=0.0)
    left_hz, right_hz = dominant_frequencies(sig, sr)
    assert left_hz == pytest.approx(295.0, abs=1.0)
    assert right_hz == pytest.approx(305.0, abs=1.0)
    assert right_hz - left_hz == pytest.approx(10.0, abs=1.0)


def test_rejects_carrier_below_half_beat():
    with pytest.raises(ValueError):
        generate_binaural(4.0, 10.0, 1.0)


def test_rejects_carrier_above_nyquist():
    with pytest.raises(ValueError):
        generate_binaural(30_000.0, 10.0, 1.0, sample_rate=44_100)


def test_refuses_gain_that_would_clip():
    with pytest.raises(ValueError, match="exceeds 1.0"):
        generate_binaural(300.0, 10.0, 0.1, amplitude=0.9, left_gain=2.0)


# ── Audiogram-aware prescription ────────────────────────────────────────────


def _ag(left: dict, right: dict) -> Audiogram:
    return Audiogram(left_ear=left, right_ear=right)


def test_carrier_lands_where_both_ears_hear_best():
    # Best mutual hearing at 500 Hz; worse at the edges.
    left = {250: 40, 500: 10, 1000: 45}
    right = {250: 45, 500: 15, 1000: 40}
    rx = prescribe_binaural(_ag(left, right), 8.0)
    assert rx.carrier_hz == 500.0


def test_symmetric_ears_get_equal_gain():
    sym = {250: 20, 500: 20, 1000: 20}
    rx = prescribe_binaural(_ag(sym, sym), 10.0)
    assert rx.left_gain == rx.right_gain


def test_worse_ear_is_boosted():
    # At the chosen carrier the left ear is much weaker → louder left.
    left = {500: 60}
    right = {500: 20}
    rx = prescribe_binaural(_ag(left, right), 10.0)
    assert rx.left_gain > rx.right_gain


def test_prescription_respects_safety_ceiling():
    left = {500: 90}
    right = {500: 10}
    rx = prescribe_binaural(_ag(left, right), 10.0, amplitude=0.25)
    peak = rx.amplitude * max(rx.left_gain, rx.right_gain)
    assert peak <= SAFE_PEAK_AMPLITUDE + 1e-6


def test_falls_back_when_no_shared_data_in_range():
    rx = prescribe_binaural(_ag({250: 20}, {8000: 30}), 10.0)
    assert rx.left_gain == rx.right_gain == 1.0
    assert "neutral" in rx.rationale.lower()


def test_hearing_aids_mode_keeps_channels_balanced():
    # Asymmetric loss that would boost one ear on headphones...
    left = {500: 60}
    right = {500: 20}
    headphones = prescribe_binaural(_ag(left, right), 10.0, delivery="headphones")
    aids = prescribe_binaural(_ag(left, right), 10.0, delivery="hearing_aids")
    # Headphones rebalance; hearing aids stay equal (the aids correct each ear).
    assert headphones.left_gain != headphones.right_gain
    assert aids.left_gain == aids.right_gain == 1.0
    # Same carrier region either way.
    assert aids.carrier_hz == headphones.carrier_hz
    assert "double-compensation" in aids.rationale.lower()


def test_invalid_delivery_mode_rejected():
    with pytest.raises(ValueError, match="delivery must be"):
        prescribe_binaural(_ag({500: 20}, {500: 20}), 10.0, delivery="telepathy")


def test_prescription_renders_and_round_trips_dict():
    rx = prescribe_binaural(_ag({500: 20}, {500: 20}), 10.0)
    sig = rx.render(0.5)
    assert sig.shape[1] == 2
    assert isinstance(rx, BinauralPrescription)
    assert rx.to_dict()["beat_hz"] == 10.0


# ── CLI ─────────────────────────────────────────────────────────────────────


def test_cli_writes_valid_wav(tmp_path):
    out = tmp_path / "beats.wav"
    result = CliRunner().invoke(
        main, ["--beat", "10", "--carrier", "300", "--duration", "0.2", "--out", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    with wave.open(str(out), "rb") as wav:
        assert wav.getnchannels() == 2
        assert wav.getsampwidth() == 2
        assert wav.getnframes() > 0


def test_cli_audiogram_mode_personalises(tmp_path):
    ag = tmp_path / "ag.json"
    ag.write_text(Audiogram(left_ear={500: 20}, right_ear={500: 20}).to_json(), encoding="utf-8")
    out = tmp_path / "beats.wav"
    result = CliRunner().invoke(
        main, ["--beat", "10", "--audiogram", str(ag), "--duration", "0.2", "--out", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert "carrier" in result.output.lower()
    assert out.exists()


def test_cli_reports_bad_parameters(tmp_path):
    out = tmp_path / "beats.wav"
    result = CliRunner().invoke(
        main, ["--beat", "10", "--carrier", "2", "--duration", "0.2", "--out", str(out)]
    )
    assert result.exit_code == 1
    assert "Could not generate" in result.output
