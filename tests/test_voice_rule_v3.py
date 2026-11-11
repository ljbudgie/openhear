"""Rule V3 (voice minimum 0.30): off by default, one flag, and the only change when on."""

import csv
import json

import numpy as np
import pytest

from scripts import bench_awareness as bench
from scripts import bench_datasets as datasets
from scripts import bench_rules as rules
from stream import sound_classifier
from stream.sound_classifier import classify_scores

LABELS = bench.load_yamnet_labels()
ENV = sound_classifier.VOICE_RULE_V3_ENV


@pytest.fixture(autouse=True)
def _flag_off(monkeypatch):
    monkeypatch.delenv(ENV, raising=False)


def test_flag_is_off_by_default_and_shipped_behaviour_is_unchanged():
    assert not sound_classifier.voice_rule_v3_enabled()
    assert sound_classifier.default_voice_minimum() == 0.0
    assert classify_scores({"Speech": 0.25}).sound_key == "voice"


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", " 1 "])
def test_flag_turns_rule_on(monkeypatch, value):
    monkeypatch.setenv(ENV, value)
    assert sound_classifier.voice_rule_v3_enabled()
    assert sound_classifier.default_voice_minimum() == 0.30
    assert classify_scores({"Speech": 0.25}).sound_key == "silence"
    assert classify_scores({"Speech": 0.33}).sound_key == "voice"


@pytest.mark.parametrize("value", ["", "0", "false", "no", "off", "0.5", "v3"])
def test_other_values_leave_rule_off(monkeypatch, value):
    monkeypatch.setenv(ENV, value)
    assert not sound_classifier.voice_rule_v3_enabled()
    assert classify_scores({"Speech": 0.25}).sound_key == "voice"


def test_explicit_argument_overrides_the_flag(monkeypatch):
    assert classify_scores({"Speech": 0.25}, voice_minimum=0.30).sound_key == "silence"
    monkeypatch.setenv(ENV, "1")
    assert classify_scores({"Speech": 0.25}, voice_minimum=0.0).sound_key == "voice"


def test_held_back_voice_does_not_pass_to_the_next_class(monkeypatch):
    monkeypatch.setenv(ENV, "1")
    result = classify_scores({"Speech": 0.25, "Dog": 0.22})
    assert result.sound_key == "silence"


def test_other_classes_are_never_affected(monkeypatch):
    monkeypatch.setenv(ENV, "1")
    for label, key in [
        ("Dog", "dog"),
        ("Siren", "alarm"),
        ("Knock", "knock"),
        ("Doorbell", "doorbell"),
        ("Music", "media"),
        ("Vehicle horn, car horn, honking", "traffic"),
        ("Baby cry, infant cry", "baby_cry"),
        ("Ringtone", "phone"),
    ]:
        assert classify_scores({label: 0.21}).sound_key == key


def test_v3_is_the_only_behavioural_change_when_enabled(monkeypatch):
    """Over many random windows, on and off differ only for voice wins scoring 0.20 to 0.30."""
    rng = np.random.default_rng(11)
    changed = 0
    for _ in range(250):
        scores = dict(zip(LABELS, map(float, rng.random(len(LABELS)) ** 4 * 0.15), strict=True))
        if rng.random() < 0.7:
            scores["Speech"] = float(rng.random() * 0.5)
        monkeypatch.delenv(ENV, raising=False)
        off = classify_scores(scores)
        monkeypatch.setenv(ENV, "1")
        on = classify_scores(scores)
        if off == on:
            continue
        changed += 1
        assert off.sound_key == "voice" and 0.20 <= off.confidence < 0.30
        assert on.sound_key == "silence"
    assert changed >= 10


def test_bench_decision_with_v3_matches_the_shipped_classifier(monkeypatch):
    rng = np.random.default_rng(5)
    label_map = bench.current_label_map(LABELS)
    scores = (rng.random((200, len(LABELS))) ** 4 * 0.15).astype(np.float32)
    scores[:, 0] = rng.random(200) * 0.5
    spec = datasets.esc50_specs([{"filename": "x.wav", "category": "rain"}])[0]
    decided = bench.decide(spec, scores, LABELS, label_map, sound_classifier.VOICE_RULE_V3_MINIMUM)
    monkeypatch.setenv(ENV, "1")
    for row, key, label in zip(scores, decided.win_class, decided.win_label, strict=True):
        shipped = classify_scores(dict(zip(LABELS, map(float, row), strict=True)), min_confidence=0.0)
        assert key == shipped.sound_key
        if key != "silence":
            assert label == shipped.source_label
    held_back = bench.decide(spec, scores, LABELS, label_map).win_class.count("voice") - decided.win_class.count("voice")
    assert held_back >= 10  # the rule did something in this sample


def _scored():
    def clip(name, category, *windows):
        spec = datasets.esc50_specs([{"filename": name, "category": category}])[0]
        rows = []
        for window in windows:
            row = np.zeros(len(LABELS), dtype=np.float32)
            for label, value in window.items():
                row[LABELS.index(label)] = value
            rows.append(row)
        return spec, np.stack(rows)

    return [
        clip("cough.wav", "coughing", {"Speech": 0.26}),
        clip("laugh.wav", "laughing", {"Speech": 0.9}),
        clip("dog.wav", "dog", {"Dog": 0.8}, {"Speech": 0.26}),
        clip("siren.wav", "siren", {"Siren": 0.7}),
        clip("rain.wav", "rain", {"Rain": 0.9}),
    ]


def test_v3_report_scores_current_map_with_rule_off_and_on():
    report = bench.build_report(
        "esc50", _scored(), LABELS, bench.load_label_maps(LABELS), {"git_sha": "t"}, voice_rule_v3=True
    )
    assert list(report["schemes"]) == ["v1.8.0", bench.V3_SCHEME]
    assert report["method"]["schemes_in_this_report"] == ["v1.8.0", "v1.8.0+V3"]
    off, on = report["schemes"]["v1.8.0"], report["schemes"]["v1.8.0+V3"]
    assert (off["voice_minimum"], on["voice_minimum"]) == (0.0, 0.30)
    assert off["label_map_sha256"] == on["label_map_sha256"]
    count = lambda s: s["at_shipped_threshold"]["negatives"]["clips_with_false_alert"]["count"]  # noqa: E731
    assert (count(off), count(on)) == (2, 1)
    hits = lambda s: {k: v["hit"]["count"] for k, v in s["at_shipped_threshold"]["per_class"].items()}  # noqa: E731
    assert hits(off) == hits(on) == {"alarm": 1, "dog": 1}
    assert report["report_sha256"] == bench.hash_report(report)
    assert "#### Label map v1.8.0+V3" in bench.render_markdown(report)


def test_default_report_is_unchanged_two_label_maps():
    report = bench.build_report(
        "esc50", _scored(), LABELS, bench.load_label_maps(LABELS), {"git_sha": "t"}
    )
    assert list(report["schemes"]) == ["v1.7.0", "v1.8.0"]


def test_v3_report_agrees_with_the_rules_report():
    scored = _scored()
    v3 = bench.build_report(
        "esc50", scored, LABELS, bench.load_label_maps(LABELS), {"git_sha": "t"}, voice_rule_v3=True
    )["schemes"][bench.V3_SCHEME]["at_shipped_threshold"]
    ruled = rules.build_report("esc50", scored, LABELS, {"git_sha": "t"})["results"]["V3"]
    assert v3["negatives"]["clips_with_false_alert"]["count"] == ruled["false_alert_clips"]
    assert {k: r["hit"]["count"] for k, r in v3["per_class"].items()} == {
        k: r["hits"] for k, r in ruled["hits"].items()
    }


def test_cli_scores_stored_scores_without_a_model(tmp_path, capsys):
    scored = _scored()
    npz = tmp_path / "s.npz"
    bench.write_raw_scores(scored, LABELS, npz, tmp_path / "s.top10.jsonl.gz")
    (tmp_path / "meta").mkdir()
    with open(tmp_path / "meta" / "esc50.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["filename", "category"])
        writer.writerows([spec.clip_id, spec.labels[0]] for spec, _ in scored)
    out = tmp_path / "r.json"
    code = bench.main(
        ["--dataset", "esc50", "--data", str(tmp_path), "--stored-scores", str(npz),
         "--scores-run", "123", "--voice-rule-v3", "--out", str(out)]
    )
    capsys.readouterr()
    report = json.loads(out.read_text(encoding="utf-8"))
    assert code == 0 and report["report_sha256"] == bench.hash_report(report)
    assert report["provenance"]["model_was_run"] is False
    assert report["provenance"]["stored_scores_from_run"] == "123"
    assert report["provenance"]["raw_scores_sha256"] == bench._sha256_file(npz)
    assert list(report["schemes"]) == ["v1.8.0", "v1.8.0+V3"]
    with pytest.raises(SystemExit):
        bench.main(["--dataset", "esc50", "--data", str(tmp_path)])
    capsys.readouterr()
