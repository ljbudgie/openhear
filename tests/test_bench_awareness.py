"""Tests for scripts/bench_awareness.py using synthetic scores (no model, no audio)."""

import gzip
import json

import numpy as np
import pytest

from scripts import bench_awareness as bench
from scripts import bench_datasets as datasets
from stream.sound_classifier import WINDOW_SECONDS

LABELS = ["Speech", "Dog", "Engine", "Vehicle horn, car horn, honking", "Knock", "Silence", "Rain"]
MAP_OLD = {
    "Speech": "voice",
    "Dog": "dog",
    "Engine": "traffic",
    "Vehicle horn, car horn, honking": "traffic",
    "Knock": "knock",
    "Silence": "silence",
}
MAP_NEW = {key: value for key, value in MAP_OLD.items() if key != "Engine"}
MAPS = {"v1.7.0": MAP_OLD, "v1.8.0": MAP_NEW}


def _spec(clip_id, category):
    return datasets.esc50_specs([{"filename": clip_id, "category": category}])[0]


def _scores(*rows):
    return np.array(rows, dtype=np.float32)


def test_wilson_interval_known_values():
    low, high = bench.wilson_interval(0, 40)
    assert low == 0.0 and 0.08 < high < 0.09
    low, high = bench.wilson_interval(40, 40)
    assert high == 1.0 and 0.91 < low < 0.92
    low, high = bench.wilson_interval(20, 40)
    assert low == pytest.approx(0.3520, abs=1e-3)
    assert high == pytest.approx(0.6480, abs=1e-3)
    assert bench.wilson_interval(0, 0) == (0.0, 0.0)


def test_split_windows_native_rate_drops_trailing_part_window_and_caps_length():
    rate = 44_100
    windows = bench.split_windows(np.zeros(rate * 5, dtype=np.float32), rate)
    assert len(windows) == 5
    assert all(len(w) == int(round(rate * WINDOW_SECONDS)) for w in windows)
    long_clip = np.zeros(16_000 * 120, dtype=np.float32)
    assert len(bench.split_windows(long_clip, 16_000)) == int(30 / WINDOW_SECONDS)


def test_split_windows_downmixes_stereo_and_keeps_short_clip():
    windows = bench.split_windows(np.ones((1000, 2), dtype=np.float32), 16_000)
    assert len(windows) == 1 and windows[0].ndim == 1


def test_score_clip_stacks_raw_scores_per_window():
    class _Stub:
        def __init__(self):
            self.calls = 0

        def score_window(self, samples, sample_rate):
            self.calls += 1
            return np.full(len(LABELS), self.calls / 10, dtype=np.float32)

    clip = np.zeros(int(16_000 * WINDOW_SECONDS * 3), dtype=np.float32)
    scores = bench.score_clip(_Stub(), clip, 16_000)
    assert scores.shape == (3, len(LABELS))
    assert scores[:, 0].tolist() == pytest.approx([0.1, 0.2, 0.3])


def test_decide_matches_classify_scores_rule():
    from stream.sound_classifier import classify_scores

    rng = np.random.default_rng(7)
    labels = bench.load_yamnet_labels()
    label_map = bench.current_label_map(labels)
    scores = rng.random((40, len(labels))).astype(np.float32) * 0.6
    decided = bench.decide(_spec("x.wav", "dog"), scores, labels, label_map)
    for row, key, score, label in zip(
        scores, decided.win_class, decided.win_score, decided.win_label, strict=True
    ):
        shipped = classify_scores(dict(zip(labels, map(float, row), strict=True)), min_confidence=0.0)
        assert (key, label) == (shipped.sound_key, shipped.source_label)
        assert score == pytest.approx(shipped.confidence)


def test_decide_unmapped_or_zero_scores_are_silence_and_top_label_is_raw():
    scores = _scores([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.9])
    decided = bench.decide(_spec("r.wav", "rain"), scores, LABELS, MAP_NEW)
    assert decided.win_class == ["silence"]
    assert decided.top_raw_label == "Rain"
    assert decided.fired(0.2) == {}


def test_silence_label_winning_the_window_fires_nothing():
    scores = _scores([0.3, 0.0, 0.0, 0.0, 0.0, 0.8, 0.0])
    decided = bench.decide(_spec("s.wav", "dog"), scores, LABELS, MAP_NEW)
    assert decided.win_class == ["silence"] and decided.fired(0.2) == {}


def _scored():
    #            Speech Dog  Engine Horn Knock Silence Rain
    return [
        (_spec("dog1.wav", "dog"), _scores([0.0, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0])),
        (_spec("dog2.wav", "dog"), _scores([0.6, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0])),  # missed as voice
        (_spec("horn1.wav", "car_horn"), _scores([0.0, 0.0, 0.7, 0.4, 0.0, 0.0, 0.0])),
        (_spec("horn2.wav", "car_horn"), _scores([0.0, 0.0, 0.7, 0.1, 0.0, 0.0, 0.0])),
        (_spec("eng1.wav", "engine"), _scores([0.0, 0.0, 0.8, 0.0, 0.0, 0.0, 0.0])),
        (_spec("eng2.wav", "engine"), _scores([0.0, 0.0, 0.8, 0.25, 0.0, 0.0, 0.0])),
        (_spec("rain1.wav", "rain"), _scores([0.0, 0.0, 0.3, 0.0, 0.0, 0.0, 0.9])),
        (_spec("rain2.wav", "rain"), _scores([0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.9])),
    ]


def _decided(scheme):
    return [bench.decide(spec, scores, LABELS, MAPS[scheme]) for spec, scores in _scored()]


def test_old_scheme_counts_engine_as_traffic_target():
    scored = bench.score_at_threshold(_decided("v1.7.0"), "v1.7.0", 0.20)
    traffic = scored["per_class"]["traffic"]["hit"]
    assert (traffic["count"], traffic["of"]) == (4, 4)  # 2 horn + 2 engine clips
    neg = scored["negatives"]["clips_with_false_alert"]
    assert (neg["count"], neg["of"]) == (1, 2)  # rain1 fired traffic via Engine
    assert scored["negatives"]["by_yamnet_label"] == {"Engine -> traffic": 1}


def test_new_scheme_engine_is_negative_and_horn_must_carry_the_hit():
    scored = bench.score_at_threshold(_decided("v1.8.0"), "v1.8.0", 0.20)
    traffic = scored["per_class"]["traffic"]
    assert (traffic["hit"]["count"], traffic["hit"]["of"]) == (1, 2)  # horn2 only scored 0.1
    assert traffic["missed_as"] == {"nothing": 1}
    assert traffic["missed_clips_top_yamnet_label"] == {"Engine": 1}
    neg = scored["negatives"]["clips_with_false_alert"]
    assert (neg["count"], neg["of"]) == (1, 4)  # eng2 fired traffic via a 0.25 horn score
    assert scored["negatives"]["by_yamnet_label"] == {"Vehicle horn, car horn, honking -> traffic": 1}
    groups = scored["groups"]
    assert groups["engine"] == {"clips": 2, "any_pattern_fired": 1, "fired_by_class": {"traffic": 1}}
    assert groups["rain"]["any_pattern_fired"] == 0
    dog = scored["per_class"]["dog"]
    assert dog["missed_as"] == {"voice": 1}


def test_precision_recall_counts_false_fires_against_the_class():
    curves = bench.precision_recall(_decided("v1.8.0"), "v1.8.0")
    at = {row["threshold"]: row for row in curves["traffic"]}
    assert (at[0.2]["fired"], at[0.2]["true_positive"]) == (2, 1)
    assert at[0.2]["precision"] == 0.5 and at[0.2]["recall"] == 0.5
    assert at[0.3]["precision"] == 1.0 and at[0.3]["recall"] == 0.5
    assert at[0.45]["precision"] is None and at[0.45]["recall"] == 0.0
    assert [row["threshold"] for row in curves["traffic"]][0] == 0.05
    assert len(curves["traffic"]) == 19


def test_score_distribution_explains_flat_threshold_steps():
    dist = bench.score_distribution(_decided("v1.8.0"), "v1.8.0")
    between = {(row["from"], row["to"]): row["deciding_scores_between"] for row in dist["deciding_scores_between_thresholds"]}
    assert between[(0.2, 0.25)] == 0  # nothing between: results identical at 0.20 and 0.25
    assert between[(0.25, 0.3)] == 1  # eng2's 0.25 horn score
    assert sum(dist["histogram_winning_window_scores"]) == dist["winning_window_scores"]
    assert dist["distinct_winning_scores"] >= 4


def test_report_is_signed_and_compares_both_schemes():
    report = bench.build_report("esc50", _scored(), LABELS, MAPS, {"git_sha": "test"})
    assert report["schema_version"] == 2
    assert report["report_sha256"] == bench.hash_report(report)
    tampered = json.loads(json.dumps(report))
    tampered["schemes"]["v1.8.0"]["at_shipped_threshold"]["targets_overall"]["count"] = 99
    assert bench.hash_report(tampered) != report["report_sha256"]
    assert report["schemes"]["v1.7.0"]["clips"] == {"targets": 6, "negatives": 2}
    assert report["schemes"]["v1.8.0"]["clips"] == {"targets": 4, "negatives": 4}
    assert report["schemes"]["v1.8.0"]["classes_tested"] == ["dog", "traffic"]
    assert "doorbell" in report["schemes"]["v1.8.0"]["classes_not_tested"]
    assert report["schemes"]["v1.7.0"]["label_map_sha256"] != report["schemes"]["v1.8.0"]["label_map_sha256"]
    assert report["clips"] == {"scored": 8, "windows": 8}


def test_render_markdown_uses_report_figures():
    report = bench.build_report(
        "esc50", _scored(), LABELS, MAPS, {"git_sha": "abc", "run_url": "https://example.test/run"}
    )
    text = bench.render_markdown(report)
    assert "#### Label map v1.7.0" in text and "#### Label map v1.8.0" in text
    assert "| traffic | 1/2 = 50.0%" in text
    assert "0.20 (shipped)" in text
    assert "Precision / recall by class and threshold" in text
    assert report["report_sha256"] in text


def test_write_raw_scores_round_trips(tmp_path):
    npz, top = tmp_path / "scores.npz", tmp_path / "scores.top10.jsonl.gz"
    bench.write_raw_scores(_scored(), LABELS, npz, top)
    data = np.load(npz)
    assert data["scores"].shape == (8, len(LABELS))
    assert data["windows_per_clip"].tolist() == [1] * 8
    with gzip.open(top, "rt", encoding="utf-8") as fh:
        first = json.loads(fh.readline())
    assert first["clip"] == "dog1.wav" and first["windows"][0][0] == ["Dog", 0.9]


def test_shipped_label_maps_differ_only_as_intended():
    labels = bench.load_yamnet_labels()
    maps = bench.load_label_maps(labels)
    old, new = maps["v1.7.0"], maps["v1.8.0"]
    removed = {label for label in old if old[label] == "traffic" and new.get(label) != "traffic"}
    added = {label: new[label] for label in new if old.get(label) != new[label]}
    assert len(removed) == 18
    assert added == {
        "Skidding": "traffic",
        "Tire squeal": "traffic",
        "Reversing beeps": "traffic",
        "Train horn": "traffic",
        "Emergency vehicle": "alarm",
    }
    unchanged = {label for label in old if old[label] != "traffic"}
    assert all(new[label] == old[label] for label in unchanged)
