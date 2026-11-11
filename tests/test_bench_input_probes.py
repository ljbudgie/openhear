"""Tests for the input probes in scripts/bench_awareness.py (no model, no audio files)."""

import numpy as np
import pytest

from scripts import bench_awareness as bench
from scripts import bench_datasets as datasets
from stream.sound_classifier import WINDOW_SECONDS

LABELS = bench.load_yamnet_labels()
HORN = LABELS.index("Vehicle horn, car horn, honking")
SPEECH = LABELS.index("Speech")


def _spec(name, category):
    return datasets.esc50_specs([{"filename": name, "category": category}])[0]


def _scores(*windows):
    rows = np.zeros((len(windows), len(LABELS)), dtype=np.float32)
    for i, window in enumerate(windows):
        for index, value in window.items():
            rows[i, index] = value
    return rows


def test_shift_half_window_drops_half_a_window_and_downmixes():
    rate = 44_100
    clip = np.arange(rate * 2, dtype=np.float32)
    shifted = bench.shift_half_window(clip, rate)
    half = int(round(rate * WINDOW_SECONDS / 2))
    assert len(shifted) == len(clip) - half and shifted[0] == clip[half]
    stereo = np.ones((rate, 2), dtype=np.float32)
    assert bench.shift_half_window(stereo, rate).ndim == 1


def test_bandlimited_resampling_removes_content_above_8khz_that_linear_folds_back():
    pytest.importorskip("scipy")
    from stream.sound_classifier import prepare_audio_window

    rate = 44_100
    t = np.arange(rate, dtype=np.float64) / rate
    tone = np.sin(2 * np.pi * 12_000 * t).astype(np.float32)  # above the 8 kHz limit of 16 kHz audio
    filtered = bench.bandlimited_16k(tone, rate)
    assert len(filtered) == 16_000
    linear = prepare_audio_window(tone, rate)
    assert float(np.sqrt(np.mean(filtered**2))) < 0.05  # the filter removes it
    assert float(np.sqrt(np.mean(linear**2))) > 0.3  # linear interpolation folds it into the band


def test_bandlimited_resampling_keeps_in_band_content_and_passes_16k_through():
    pytest.importorskip("scipy")
    rate = 48_000
    t = np.arange(rate, dtype=np.float64) / rate
    tone = np.sin(2 * np.pi * 1_000 * t).astype(np.float32)
    out = bench.bandlimited_16k(tone, rate)
    assert len(out) == 16_000
    assert float(np.sqrt(np.mean(out[1000:-1000] ** 2))) == pytest.approx(0.7071, abs=0.02)
    already = np.ones(100, dtype=np.float32)
    assert bench.bandlimited_16k(already, 16_000) is not None and len(bench.bandlimited_16k(already, 16_000)) == 100


def _probe_inputs():
    horn_a, horn_b, horn_c, rain = (
        _spec("a.wav", "car_horn"),
        _spec("b.wav", "car_horn"),
        _spec("c.wav", "car_horn"),
        _spec("r.wav", "rain"),
    )
    shipped = [
        (horn_a, _scores({HORN: 0.5})),
        (horn_b, _scores({HORN: 0.1})),
        (horn_c, _scores({HORN: 0.4})),
        (rain, _scores({SPEECH: 0.1})),
    ]
    probes = {
        "shifted": [
            (horn_a, _scores({HORN: 0.5})),
            (horn_b, _scores({HORN: 0.3})),  # recovered by shifting
            (horn_c, _scores({HORN: 0.1})),  # lost by shifting
            (rain, _scores({SPEECH: 0.1})),
        ],
        "bandlimited": [
            (horn_a, _scores({HORN: 0.5})),
            (horn_b, _scores({HORN: 0.1})),
            (horn_c, _scores({HORN: 0.4})),
            (rain, _scores({SPEECH: 0.6})),  # a new false alert under this input
        ],
    }
    return shipped, probes


def test_probe_report_scores_each_input_and_tracks_horn_changes():
    shipped, probes = _probe_inputs()
    report = bench.build_report(
        "esc50", shipped, LABELS, bench.load_label_maps(LABELS), {"git_sha": "t"}, input_probes=probes
    )
    assert list(report["schemes"]) == ["v1.8.0", "v1.8.0+shifted", "v1.8.0+bandlimited"]
    hit = lambda name: report["schemes"][name]["at_shipped_threshold"]["per_class"]["traffic"]["hit"]["count"]  # noqa: E731
    assert (hit("v1.8.0"), hit("v1.8.0+shifted"), hit("v1.8.0+bandlimited")) == (2, 2, 2)
    alerts = lambda name: report["schemes"][name]["at_shipped_threshold"]["negatives"]["clips_with_false_alert"]["count"]  # noqa: E731
    assert (alerts("v1.8.0"), alerts("v1.8.0+bandlimited")) == (0, 1)
    probe = report["input_probes"]["all"]
    assert probe["clips"] == 3 and probe["fired_under_any_input"] == 3
    assert probe["against_shipped"]["v1.8.0+shifted"] == {"gained": 1, "lost": 1}
    assert probe["against_shipped"]["v1.8.0+bandlimited"] == {"gained": 0, "lost": 0}
    assert probe["fired_under_shipped_or_shifted"] == 3
    assert report["input_probes"]["by_group"]["car_horn"]["clips"] == 3
    assert report["report_sha256"] == bench.hash_report(report)
    text = bench.render_markdown(report)
    assert "Input probes on traffic target clips" in text and "#### Label map v1.8.0+bandlimited" in text


def test_reports_without_probes_are_unchanged():
    shipped, _ = _probe_inputs()
    report = bench.build_report("esc50", shipped, LABELS, bench.load_label_maps(LABELS), {"git_sha": "t"})
    assert report["input_probes"] is None and list(report["schemes"]) == ["v1.7.0", "v1.8.0"]
