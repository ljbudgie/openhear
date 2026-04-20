"""Tests for the Phase 3 streaming helpers (no real hardware)."""

from __future__ import annotations

import wave
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest


# ── bluetooth_output ───────────────────────────────────────────────────────


def test_is_likely_bluetooth_device_matches_known_brands():
    from stream.bluetooth_output import is_likely_bluetooth_device
    assert is_likely_bluetooth_device("Phonak Naida M70")
    assert is_likely_bluetooth_device("Bluetooth Headphones")
    assert is_likely_bluetooth_device("Signia Insio AX")
    assert is_likely_bluetooth_device("Audeo M-R")  # marvel hint via 'audeo'


def test_is_likely_bluetooth_device_misses_random_devices():
    from stream.bluetooth_output import is_likely_bluetooth_device
    assert not is_likely_bluetooth_device("Realtek Speakers")
    assert not is_likely_bluetooth_device("USB Microphone")


def test_resample_to_no_op_on_matching_rate():
    from stream.bluetooth_output import resample_to
    x = np.array([0.1, -0.2, 0.3], dtype=np.float32)
    out = resample_to(x, 16_000, 16_000)
    np.testing.assert_array_equal(out, x)


def test_resample_to_doubles_length_when_doubling_rate():
    from stream.bluetooth_output import resample_to
    x = np.array([0.0, 1.0, 0.0, -1.0], dtype=np.float32)
    out = resample_to(x, 16_000, 32_000)
    assert out.size == 8


def test_resample_to_halves_length_when_halving_rate():
    from stream.bluetooth_output import resample_to
    x = np.arange(8, dtype=np.float32)
    out = resample_to(x, 32_000, 16_000)
    assert out.size == 4


def test_resample_to_preserves_sine_amplitude():
    """A pure tone resampled to a higher rate keeps its peak amplitude."""
    from stream.bluetooth_output import resample_to
    sr = 16_000
    n = 1024
    x = (0.5 * np.sin(2 * np.pi * 1000 * np.arange(n) / sr)).astype(np.float32)
    out = resample_to(x, sr, 48_000)
    assert abs(np.max(out) - 0.5) < 0.05


def test_resample_to_rejects_non_positive_rates():
    from stream.bluetooth_output import resample_to
    with pytest.raises(ValueError):
        resample_to(np.zeros(8, dtype=np.float32), 0, 16_000)
    with pytest.raises(ValueError):
        resample_to(np.zeros(8, dtype=np.float32), 16_000, -1)


def test_list_output_devices_uses_provided_pyaudio_instance():
    from stream.bluetooth_output import list_output_devices

    fake = MagicMock()
    fake.get_device_count.return_value = 3
    fake.get_device_info_by_index.side_effect = [
        {"name": "Speakers (Realtek)", "maxOutputChannels": 2,
         "defaultSampleRate": 48_000.0},
        {"name": "Phonak Audeo M",     "maxOutputChannels": 2,
         "defaultSampleRate": 16_000.0},
        {"name": "USB Microphone",     "maxOutputChannels": 0,
         "defaultSampleRate": 48_000.0},  # input-only, should be skipped
    ]
    devices = list_output_devices(fake)
    assert len(devices) == 2
    names = [d["name"] for d in devices]
    assert "Speakers (Realtek)" in names
    assert "Phonak Audeo M" in names
    assert any(d["likely_bluetooth"] for d in devices if d["name"] == "Phonak Audeo M")
    fake.terminate.assert_not_called()  # caller-owned PA must not be terminated


# ── virtual_cable ──────────────────────────────────────────────────────────


def _fake_pa(devices):
    """Build a MagicMock PyAudio with the given device list."""
    fake = MagicMock()
    fake.get_device_count.return_value = len(devices)
    fake.get_device_info_by_index.side_effect = devices
    return fake


def test_detect_virtual_cables_finds_vb_cable():
    from stream.virtual_cable import detect_virtual_cables

    pa = _fake_pa([
        {"name": "Speakers", "maxOutputChannels": 2, "maxInputChannels": 0,
         "defaultSampleRate": 48_000.0},
        {"name": "VB-Audio Virtual Cable", "maxOutputChannels": 2,
         "maxInputChannels": 0, "defaultSampleRate": 48_000.0},
        {"name": "VB-Audio Virtual Cable", "maxOutputChannels": 0,
         "maxInputChannels": 2, "defaultSampleRate": 48_000.0},
    ])
    cables = detect_virtual_cables(pa)
    directions = sorted(c.direction for c in cables)
    assert directions == ["input", "output"]


def test_detect_virtual_cables_returns_empty_when_none():
    from stream.virtual_cable import detect_virtual_cables

    pa = _fake_pa([
        {"name": "Speakers", "maxOutputChannels": 2, "maxInputChannels": 0,
         "defaultSampleRate": 48_000.0},
    ])
    assert detect_virtual_cables(pa) == []


def test_best_virtual_cable_prefers_vb_cable():
    from stream.virtual_cable import VirtualCable, best_virtual_cable

    cables = [
        VirtualCable(0, "PulseAudio sink.monitor", "input", 48_000.0),
        VirtualCable(1, "VB-Audio Virtual Cable", "input", 48_000.0),
        VirtualCable(2, "BlackHole 2ch", "input", 48_000.0),
    ]
    pick = best_virtual_cable("input", cables)
    assert pick is not None and pick.index == 1


def test_best_virtual_cable_returns_none_for_missing_direction():
    from stream.virtual_cable import VirtualCable, best_virtual_cable

    cables = [VirtualCable(0, "VB-Cable", "output", 48_000.0)]
    assert best_virtual_cable("input", cables) is None


def test_best_virtual_cable_validates_direction():
    from stream.virtual_cable import best_virtual_cable
    with pytest.raises(ValueError, match="direction must be"):
        best_virtual_cable("middle", [])


# ── latency ────────────────────────────────────────────────────────────────


def test_synthesise_impulse_basic():
    from stream.latency import synthesise_impulse
    s = synthesise_impulse(8, impulse_at=3, amplitude=0.5)
    assert s.shape == (8,)
    assert s[3] == 0.5
    assert (s[np.arange(8) != 3] == 0).all()


def test_synthesise_impulse_validates_args():
    from stream.latency import synthesise_impulse
    with pytest.raises(ValueError):
        synthesise_impulse(0)
    with pytest.raises(ValueError):
        synthesise_impulse(8, impulse_at=8)


def test_detect_impulse_delay_finds_known_offset():
    from stream.latency import detect_impulse_delay
    rec = np.zeros(160, dtype=np.float32)
    rec[40] = 0.8
    assert detect_impulse_delay(rec) == 40


def test_detect_impulse_delay_handles_silence():
    from stream.latency import detect_impulse_delay
    assert detect_impulse_delay(np.zeros(100, dtype=np.float32)) == -1
    assert detect_impulse_delay(np.array([], dtype=np.float32)) == -1


def test_measure_latency_round_trips_known_offset():
    from stream.latency import measure_latency
    sr = 16_000
    rec = np.zeros(int(sr * 0.05), dtype=np.float32)
    rec[160] = 0.9  # 10 ms in
    report = measure_latency(rec, sr, target_ms=20.0)
    assert report.impulse_index == 160
    assert report.latency_ms == pytest.approx(10.0, abs=0.05)
    assert report.within_target
    assert report.verdict == "within target"


def test_measure_latency_above_target():
    from stream.latency import measure_latency
    sr = 16_000
    rec = np.zeros(int(sr * 0.05), dtype=np.float32)
    rec[480] = 0.9  # 30 ms
    report = measure_latency(rec, sr, target_ms=20.0)
    assert not report.within_target
    assert report.verdict == "above target"


def test_measure_latency_no_impulse():
    from stream.latency import measure_latency, format_report
    sr = 16_000
    report = measure_latency(np.zeros(160, dtype=np.float32), sr)
    assert report.impulse_index == -1
    assert report.verdict == "no impulse detected"
    assert "No impulse detected" in format_report(report)


def test_measure_latency_validates_sample_rate():
    from stream.latency import measure_latency
    with pytest.raises(ValueError, match="sample_rate must be positive"):
        measure_latency(np.zeros(160, dtype=np.float32), 0)


# ── recorder ───────────────────────────────────────────────────────────────


def test_recorder_writes_concatenated_wav(tmp_path: Path):
    from stream.recorder import Recorder

    rec = Recorder(path=tmp_path / "out.wav", sample_rate=16_000)
    rec.feed(np.full(128, 0.1, dtype=np.float32))
    rec.feed(np.full(128, -0.2, dtype=np.float32))
    out = rec.save()

    with wave.open(str(out), "rb") as wf:
        assert wf.getframerate() == 16_000
        assert wf.getnframes() == 256
        raw = wf.readframes(256)
    samples = np.frombuffer(raw, dtype=np.int16)
    assert samples.size == 256


def test_recorder_respects_max_samples(tmp_path: Path):
    from stream.recorder import Recorder

    rec = Recorder(path=tmp_path / "cap.wav", sample_rate=16_000, max_samples=200)
    rec.feed(np.zeros(150, dtype=np.float32))
    rec.feed(np.zeros(150, dtype=np.float32))  # only 50 of these accepted
    rec.feed(np.zeros(50, dtype=np.float32))   # all dropped
    assert rec.length_samples == 200


def test_recorder_save_with_no_data_raises(tmp_path: Path):
    from stream.recorder import Recorder

    rec = Recorder(path=tmp_path / "x.wav", sample_rate=16_000)
    with pytest.raises(RuntimeError, match="before any samples"):
        rec.save()


def test_write_wav_validates_inputs(tmp_path: Path):
    from stream.recorder import write_wav
    with pytest.raises(ValueError, match="sample_rate"):
        write_wav(tmp_path / "x.wav", np.zeros(8, dtype=np.float32), 0)
    with pytest.raises(ValueError, match="empty WAV"):
        write_wav(tmp_path / "y.wav", np.zeros(0, dtype=np.float32), 16_000)
