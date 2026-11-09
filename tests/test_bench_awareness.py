"""Tests for scripts/bench_awareness.py using a stub classifier (no model, no audio)."""

import json

import numpy as np
import pytest

from scripts import bench_awareness as bench
from stream.sound_classifier import WINDOW_SECONDS, ClassifiedSound


class _StubClassifier:
    """Returns a scripted (class, score) per window, in order."""

    def __init__(self, script):
        self._script = list(script)
        self.calls = []

    def classify_window(self, samples, sample_rate, *, min_confidence):
        self.calls.append((len(samples), sample_rate, min_confidence))
        key, score = self._script.pop(0)
        return ClassifiedSound(key, score, key)


def test_wilson_interval_known_values():
    low, high = bench.wilson_interval(0, 40)
    assert low == 0.0 and 0.08 < high < 0.09
    low, high = bench.wilson_interval(40, 40)
    assert high == 1.0 and 0.91 < low < 0.92
    low, high = bench.wilson_interval(20, 40)
    assert low == pytest.approx(0.3520, abs=1e-3)
    assert high == pytest.approx(0.6480, abs=1e-3)
    assert bench.wilson_interval(0, 0) == (0.0, 0.0)


def test_split_windows_native_rate_drops_trailing_part_window():
    sample_rate = 44_100
    clip = np.zeros(sample_rate * 5, dtype=np.float32)
    windows = bench.split_windows(clip, sample_rate)
    assert len(windows) == 5
    assert all(len(w) == int(round(sample_rate * WINDOW_SECONDS)) for w in windows)


def test_split_windows_downmixes_stereo_and_keeps_short_clip():
    stereo = np.ones((1000, 2), dtype=np.float32)
    windows = bench.split_windows(stereo, 16_000)
    assert len(windows) == 1 and windows[0].ndim == 1


def test_classify_clip_reads_scores_before_thresholding():
    stub = _StubClassifier([("dog", 0.05), ("silence", 0.0)])
    clip = np.zeros(int(16_000 * WINDOW_SECONDS * 2), dtype=np.float32)
    assert bench.classify_clip(stub, clip, 16_000) == [("dog", 0.05), ("silence", 0.0)]
    assert all(call[2] == 0.0 for call in stub.calls)


def test_fired_classes_applies_threshold_and_ignores_silence():
    windows = [("dog", 0.19), ("dog", 0.20), ("silence", 0.9), ("alarm", 0.5)]
    assert bench.fired_classes(windows, 0.20) == ["dog", "alarm"]


def _clips():
    return [
        # dog: one clean hit, one hit with another pattern, one miss as media, one miss as nothing
        {"category": "dog", "windows": [("dog", 0.9), ("silence", 0.0)]},
        {"category": "dog", "windows": [("dog", 0.4), ("media", 0.6)]},
        {"category": "dog", "windows": [("media", 0.7), ("dog", 0.1)]},
        {"category": "dog", "windows": [("silence", 0.0)]},
        # two ESC-50 categories share the alarm class
        {"category": "siren", "windows": [("alarm", 0.8)]},
        {"category": "clock_alarm", "windows": [("phone", 0.8)]},
        # negatives: one false alert, one quiet
        {"category": "rain", "windows": [("traffic", 0.3), ("traffic", 0.1)]},
        {"category": "wind", "windows": [("traffic", 0.19), ("silence", 0.0)]},
    ]


def test_score_at_threshold_counts_hits_misses_and_false_alerts():
    scored = bench.score_at_threshold(_clips(), 0.20)
    dog = scored["per_class"]["dog"]
    assert (dog["hit"]["count"], dog["hit"]["of"]) == (2, 4)
    assert dog["hits_with_other_pattern"] == 1
    assert dog["missed_as"] == {"media": 1, "nothing": 1}
    alarm = scored["per_class"]["alarm"]
    assert (alarm["hit"]["count"], alarm["hit"]["of"]) == (1, 2)
    assert alarm["missed_as"] == {"phone": 1}
    assert scored["per_esc50_category"]["siren"]["hit"]["rate"] == 1.0
    assert scored["per_esc50_category"]["clock_alarm"]["hit"]["rate"] == 0.0
    assert scored["targets_overall"]["count"] == 3 and scored["targets_overall"]["of"] == 6
    neg = scored["negatives"]
    assert (neg["clips_with_false_alert"]["count"], neg["clips_with_false_alert"]["of"]) == (1, 2)
    assert (neg["windows_with_false_alert"]["count"], neg["windows_with_false_alert"]["of"]) == (1, 4)
    assert neg["by_pattern"] == {"traffic": 1}
    assert neg["by_esc50_category"]["rain"] == {"false_alert_clips": 1, "clips": 1}


def test_lower_threshold_raises_hits_and_false_alerts():
    low = bench.score_at_threshold(_clips(), 0.10)
    assert low["per_class"]["dog"]["hit"]["count"] == 3
    assert low["negatives"]["clips_with_false_alert"]["count"] == 2


def test_report_is_signed_and_states_untested_classes():
    report = bench.build_report(_clips(), {"git_sha": "test"})
    assert report["report_sha256"] == bench.hash_report(report)
    tampered = json.loads(json.dumps(report))
    tampered["at_shipped_threshold"]["targets_overall"]["count"] = 99
    assert bench.hash_report(tampered) != report["report_sha256"]
    assert report["method"]["classes_not_tested"] == ["voice", "doorbell", "media", "phone"]
    assert [row["threshold"] for row in report["threshold_sweep"]] == list(bench.THRESHOLDS)
    assert report["clips"] == {"total": 8, "targets": 6, "negatives": 2}


def test_target_map_and_untested_classes_cover_every_openhear_class():
    from stream.haptic_mapper import SOUND_PROFILES

    covered = set(bench.TARGET_MAP.values()) | set(bench.UNTESTED_CLASSES) | {"silence"}
    assert covered == set(SOUND_PROFILES)


def test_render_markdown_contains_numbers_from_report_only():
    report = bench.build_report(_clips(), {"git_sha": "abc", "run_url": "https://example.test/run"})
    text = bench.render_markdown(report)
    assert "| dog | 2/4 = 50.0%" in text
    assert "0.20 (shipped)" in text
    assert report["report_sha256"] in text
    assert "https://example.test/run" in text
