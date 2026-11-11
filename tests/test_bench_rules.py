"""Tests for scripts/bench_rules.py on synthetic scores (no model, no audio)."""

import json

import numpy as np
import pytest

from scripts import bench_awareness as bench
from scripts import bench_datasets as datasets
from scripts import bench_rules as rules

LABELS = bench.load_yamnet_labels()
INDEX = {label: i for i, label in enumerate(LABELS)}
LABEL_MAP = bench.current_label_map(LABELS)
HORN = "Vehicle horn, car horn, honking"


def _named(pairs):
    row = np.zeros(len(LABELS), dtype=np.float32)
    for label, value in pairs.items():
        row[INDEX[label]] = value
    return row


def _clip(category, *windows, clip_id="c.wav"):
    spec = datasets.esc50_specs([{"filename": clip_id, "category": category}])[0]
    return rules.build_clip(spec, np.stack([_named(w) for w in windows]), LABELS, LABEL_MAP)


def _fired(rule, clip):
    return set(rules.apply_rule(rule, clip, LABEL_MAP).fired(rules.THRESHOLD))


def test_baseline_is_the_shipped_decision():
    clip = _clip("dog", {"Speech": 0.6, "Dog": 0.3})
    assert rules.apply_rule("baseline", clip, LABEL_MAP) is clip.base
    assert _fired("baseline", clip) == {"voice"}


def test_v1_speech_dominance_holds_back_voice_when_another_label_is_top():
    cough = _clip("coughing", {"Cough": 0.9, "Speech": 0.4})
    assert _fired("baseline", cough) == {"voice"}
    assert _fired("V1", cough) == set()
    talk = _clip("rain", {"Speech": 0.9, "Cough": 0.2})
    assert _fired("V1", talk) == {"voice"}


def test_v2_persistence_needs_a_neighbouring_voice_window():
    lone = _clip("coughing", {"Speech": 0.5}, {"Rain": 0.9}, {"Speech": 0.5})
    assert _fired("V2", lone) == set()
    pair = _clip("rain", {"Rain": 0.9}, {"Speech": 0.5}, {"Speech": 0.3})
    assert _fired("V2", pair) == {"voice"}
    weak_neighbour = _clip("rain", {"Speech": 0.5}, {"Speech": 0.1})
    assert _fired("V2", weak_neighbour) == set()
    single_window = _clip("rain", {"Speech": 0.9})
    assert _fired("V2", single_window) == set()


def test_v3_and_v4_voice_minimum_scores():
    clip = _clip("rain", {"Speech": 0.33})
    assert _fired("V3", clip) == {"voice"} and _fired("V4", clip) == set()
    low = _clip("rain", {"Speech": 0.26})
    assert _fired("baseline", low) == {"voice"} and _fired("V3", low) == set()


def test_voice_rules_do_not_touch_other_classes_or_pass_the_window_on():
    clip = _clip("dog", {"Cough": 0.9, "Speech": 0.4, "Dog": 0.3})
    assert _fired("V1", clip) == set()  # held-back voice does not fall through to dog
    dog = _clip("dog", {"Dog": 0.8})
    for rule in rules.VOICE_RULES:
        assert _fired(rule, dog) == {"dog"}


def test_h1_alarm_and_traffic_outrank_voice_and_media_only():
    masked = _clip("car_horn", {"Speech": 0.6, HORN: 0.3})
    assert _fired("baseline", masked) == {"voice"}
    assert _fired("H1", masked) == {"traffic"}
    music = _clip("siren", {"Music": 0.7, "Siren": 0.25})
    assert _fired("H1", music) == {"alarm"}
    under_dog = _clip("car_horn", {"Dog": 0.6, HORN: 0.3})
    assert _fired("H1", under_dog) == {"dog"}
    assert _fired("H2", under_dog) == {"traffic"}


def test_horn_rules_need_0_20_and_prefer_the_higher_of_alarm_and_traffic():
    weak = _clip("car_horn", {"Speech": 0.6, HORN: 0.19})
    assert _fired("H1", weak) == {"voice"} and _fired("H2", weak) == {"voice"}
    both = _clip("car_horn", {"Speech": 0.6, HORN: 0.3, "Siren": 0.4})
    assert _fired("H1", both) == {"alarm"}
    tie = _clip("car_horn", {"Speech": 0.6, HORN: 0.3, "Siren": 0.3})
    assert _fired("H1", tie) == {"alarm"}
    decided = rules.apply_rule("H1", masked := _clip("car_horn", {"Speech": 0.6, HORN: 0.3}), LABEL_MAP)
    assert decided.win_label == [HORN] and decided.win_score == [pytest.approx(0.3)]
    assert masked.base.win_class == ["voice"]  # the baseline is not mutated


def test_c1_applies_h1_first_then_v1():
    clip = _clip(
        "car_horn",
        {"Speech": 0.6, HORN: 0.3},  # H1 gives this window to traffic
        {"Cough": 0.9, "Speech": 0.4},  # V1 holds this voice window back
        {"Speech": 0.9},  # genuine speech survives
    )
    assert _fired("C1", clip) == {"traffic", "voice"}
    assert rules.apply_rule("C1", clip, LABEL_MAP).win_class == ["traffic", "silence", "voice"]


def test_unknown_rule_raises():
    with pytest.raises(ValueError):
        rules.apply_rule("Z9", _clip("dog", {"Dog": 0.5}), LABEL_MAP)


def _scored():
    def spec(name, category):
        return datasets.esc50_specs([{"filename": name, "category": category}])[0]

    def mat(*windows):
        return np.stack([_named(w) for w in windows])

    return [
        (spec("horn_hit.wav", "car_horn"), mat({HORN: 0.5})),
        (spec("horn_masked.wav", "car_horn"), mat({"Speech": 0.6, HORN: 0.3})),
        (spec("horn_low.wav", "car_horn"), mat({HORN: 0.1})),
        (spec("horn_weak.wav", "car_horn"), mat({"Speech": 0.6, HORN: 0.1})),
        (spec("horn_vehicle.wav", "car_horn"), mat({"Vehicle": 0.8})),
        (spec("horn_none.wav", "car_horn"), mat({"Rain": 0.8})),
        (spec("siren.wav", "siren"), mat({"Siren": 0.9}, {"Speech": 0.5, "Siren": 0.25})),
        (spec("cough.wav", "coughing"), mat({"Cough": 0.9, "Speech": 0.4})),
        (spec("laugh.wav", "laughing"), mat({"Speech": 0.9}, {"Speech": 0.9})),
        (spec("bells.wav", "church_bells"), mat({"Music": 0.7, "Siren": 0.3})),
        (spec("rain.wav", "rain"), mat({"Rain": 0.9})),
    ]


def test_horn_breakdown_sorts_misses_by_cause():
    report = rules.build_report("esc50", _scored(), LABELS, {"git_sha": "t"})
    horn = report["diagnostics"]["horn"]
    assert horn["horn_target_clips"] == 6 and horn["hits_at_0.20"] == 1 and horn["hits_at_0.05"] == 2
    causes = horn["missed_by_cause"]
    assert sum(causes.values()) == 5 == horn["missed_at_0.20"]
    assert causes["masked: horn scored 0.20 or more but another class scored higher"] == 1
    assert causes["threshold: horn won a window but scored 0.05 to 0.20"] == 1
    assert causes["weak and outscored: horn scored 0.05 to 0.20 and another class won"] == 1
    assert causes["index mapping: top label is a vehicle or engine label outside the allowlist"] == 1
    assert causes["not detected: no horn label reached 0.05"] == 1
    assert horn["masked_by_class"] == {"voice": 1}
    assert horn["hits_by_clip_length"] == {"1 window": {"hits": 1, "of": 6}}
    assert horn["alarm_target_clips"] == 1 and horn["alarm_target_clips_where_traffic_fired"] == 0


def test_report_results_and_facts_against_baseline():
    report = rules.build_report("esc50", _scored(), LABELS, {"git_sha": "t"})
    assert report["report_sha256"] == bench.hash_report(report)
    base = report["results"]["baseline"]
    assert base["hits"]["traffic"] == {"hits": 1, "of": 6}
    assert base["hits"]["alarm"] == {"hits": 1, "of": 1}
    assert (base["false_alert_clips"], base["negative_clips"]) == (3, 4)
    assert base["wrong_fires"] == {"alarm": 0, "traffic": 0}

    h1 = report["against_baseline"]["H1"]
    assert h1["traffic_hits_change"] == 1  # the masked horn is recovered
    assert h1["wrong_alarm_or_traffic_clips_added"] == 1  # church bells now fire alarm
    assert h1["gate_no_alarm_hit_lost"] and h1["false_alert_clips_change"] == 0
    assert h1["selected_if_esc50"]  # one wrong clip added for one horn gained

    v1 = report["against_baseline"]["V1"]
    assert v1["false_alert_clips_change"] == -1  # the cough no longer fires voice
    assert v1["selected_if_esc50"] and v1["confirmed_if_held_out"]
    assert v1["missed_speech"] is None  # ESC-50 has no voice targets

    voice = report["diagnostics"]["voice_false_alerts"]
    assert voice == {"negative_clips_where_voice_fired": 2, "by_yamnet_index": {"0 Speech": 2}}
    assert report["results"]["V1"]["false_alerts_by_pattern"].get("voice", 0) == 1
    assert set(report["results"]) == {"baseline", *rules.RULES}
    assert len(rules.RULES) == 7


def test_a_rule_that_costs_an_alarm_hit_fails_the_gate():
    base = {"hits": {"alarm": {"hits": 10, "of": 12}, "traffic": {"hits": 5, "of": 9}},
            "false_alert_clips": 20, "wrong_fires": {"alarm": 1, "traffic": 1}}
    worse = {"hits": {"alarm": {"hits": 9, "of": 12}, "traffic": {"hits": 8, "of": 9}},
             "false_alert_clips": 10, "wrong_fires": {"alarm": 1, "traffic": 1}}
    for rule in ("V1", "H1", "C1"):
        facts = rules.compare(rule, base, worse)
        assert not facts["gate_no_alarm_hit_lost"] and facts["alarm_hits_lost"] == 1
        assert not facts["selected_if_esc50"] and not facts["confirmed_if_held_out"]


def test_horn_rule_conditions_on_wrong_fires_and_other_classes():
    base = {"hits": {"alarm": {"hits": 10, "of": 12}, "traffic": {"hits": 5, "of": 9},
                     "voice": {"hits": 50, "of": 60}},
            "false_alert_clips": 20, "wrong_fires": {"alarm": 1, "traffic": 1}}
    good = {"hits": {"alarm": {"hits": 10, "of": 12}, "traffic": {"hits": 7, "of": 9},
                     "voice": {"hits": 49, "of": 60}},
            "false_alert_clips": 20, "wrong_fires": {"alarm": 2, "traffic": 2}}
    facts = rules.compare("H1", base, good)
    assert facts["confirmed_if_held_out"]  # +2 hits, +2 wrong, 1 voice hit lost
    assert not facts["selected_if_esc50"]  # selection allows no class to lose hits
    assert facts["missed_speech"] == 1
    too_many_wrong = json.loads(json.dumps(good))
    too_many_wrong["wrong_fires"] = {"alarm": 3, "traffic": 2}
    assert not rules.compare("H1", base, too_many_wrong)["confirmed_if_held_out"]
    no_gain = json.loads(json.dumps(base))
    assert rules.compare("H1", base, no_gain)["confirmed_if_held_out"]
    assert not rules.compare("H1", base, no_gain)["selected_if_esc50"]


def _fake_report(dataset, **flags):
    facts = {}
    for rule in rules.RULES:
        facts[rule] = {
            "selected_if_esc50": flags.get(f"{rule}_selected", False),
            "confirmed_if_held_out": flags.get(f"{rule}_confirmed", False),
            "gate_no_alarm_hit_lost": flags.get(f"{rule}_gate", True),
            "missed_speech": flags.get(f"{rule}_missed", 0),
        }
    return {"dataset": dataset, "against_baseline": facts, "report_sha256": dataset}


def test_verdict_needs_selection_on_esc50_and_confirmation_on_both_held_out_sets():
    reports = {
        "esc50": _fake_report("esc50", H1_selected=True, H2_selected=True, V1_selected=True),
        "fsd50k": _fake_report("fsd50k", H1_confirmed=True, H2_confirmed=True, V1_confirmed=True, V1_missed=42),
        "sonyc": _fake_report("sonyc", H1_confirmed=True, V1_confirmed=True),
    }
    verdict = rules.build_verdict(reports)
    assert verdict["rules"]["H1"]["passes_protocol"] and verdict["rules"]["H1"]["may_be_enabled"]
    assert not verdict["rules"]["H2"]["passes_protocol"]  # not confirmed on SONYC-UST
    assert verdict["rules"]["V1"]["passes_protocol"] and not verdict["rules"]["V1"]["may_be_enabled"]
    assert verdict["rules"]["V1"]["missed_speech_on_fsd50k"] == 42
    assert verdict["rule_that_may_be_enabled"] == "H1" and verdict["voice_rules_stay_off"]
    assert verdict["report_sha256"] == bench.hash_report(verdict)
    assert "| H1:" in rules.render_verdict_markdown(verdict)


def test_verdict_held_out_sets_cannot_rescue_a_rule_esc50_did_not_select():
    reports = {
        "esc50": _fake_report("esc50"),
        "fsd50k": _fake_report("fsd50k", H1_confirmed=True),
        "sonyc": _fake_report("sonyc", H1_confirmed=True),
    }
    verdict = rules.build_verdict(reports)
    assert not verdict["rules"]["H1"]["passes_protocol"]
    assert verdict["rule_that_may_be_enabled"] is None


def test_verdict_prefers_h1_and_fails_on_a_gate_break_anywhere():
    both = {
        "esc50": _fake_report("esc50", H1_selected=True, H2_selected=True),
        "fsd50k": _fake_report("fsd50k", H1_confirmed=True, H2_confirmed=True),
        "sonyc": _fake_report("sonyc", H1_confirmed=True, H2_confirmed=True),
    }
    assert rules.build_verdict(both)["rule_that_may_be_enabled"] == "H1"
    both["sonyc"] = _fake_report("sonyc", H1_confirmed=True, H2_confirmed=True, H1_gate=False)
    verdict = rules.build_verdict(both)
    assert not verdict["rules"]["H1"]["passes_protocol"]
    assert verdict["rule_that_may_be_enabled"] == "H2"


def test_stored_scores_round_trip_and_grid(tmp_path):
    scored = _scored()
    npz = tmp_path / "s.npz"
    bench.write_raw_scores(scored, LABELS, npz, tmp_path / "s.top10.jsonl.gz")
    by_clip, labels, matrix = rules.load_stored_scores(npz)
    assert labels == LABELS and set(by_clip) == {spec.clip_id for spec, _ in scored}
    assert by_clip["siren.wav"].shape == (2, len(LABELS))
    assert np.array_equal(by_clip["laugh.wav"], scored[8][1])
    grid = rules.score_grid(np.array([[0.0, 51 / 256, 67 / 256]], dtype=np.float32))
    assert grid["distinct_values"] == 3 and grid["all_multiples_of_1_over_256"]
    assert grid["values_from_0.15_to_0.55"] == [round(51 / 256, 6), round(67 / 256, 6)]
    assert not rules.score_grid(np.array([[0.1234567]], dtype=np.float32))["all_multiples_of_1_over_256"]


def test_markdown_and_distributions():
    report = rules.build_report("esc50", _scored(), LABELS, {"git_sha": "t"})
    text = rules.render_markdown(report)
    assert "| baseline |" in text and "| H1 |" in text and "| C1 |" in text
    assert "Why a horn clip was missed at 0.20" in text
    dist = report["diagnostics"]["score_distributions"]
    assert dist["traffic"]["target_clips"]["none"] == 4
    assert dist["voice"]["negative_clips"] == {"0.4000": 1, "0.9000": 1}
