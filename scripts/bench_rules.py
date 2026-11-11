"""
bench_rules.py – re-analyse stored bench scores under candidate decision rules.

This script never runs the model. It reads the raw YAMNet scores that
``scripts/bench_awareness.py`` stored for every window of every clip, applies
the shipped decision (the *baseline*) and seven candidate rules to them, and
reports what each rule would change.

The rules, the measures and the pass conditions were fixed in
``docs/BENCH_PLAN_v1.9.md`` before any rule was run. The pass conditions are
checked by the code here, not by eye.

Scope is the same as the bench it builds on: classifier only, recorded clips,
no wearers, no real rooms, not a clinical result.

Usage::

    python -m scripts.bench_rules analyse --dataset esc50 --data /path/to/metadata \\
        --scores bench_esc50_scores.npz --out rules_esc50.json --markdown rules_esc50.md
    python -m scripts.bench_rules verdict --reports rules_esc50.json rules_fsd50k.json \\
        rules_sonyc.json --out rules_verdict.json --markdown rules_verdict.md
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from scripts import bench_awareness as bench
from scripts import bench_datasets as datasets
from stream.sound_classifier import DEFAULT_MIN_CONFIDENCE

SCHEMA_VERSION = 1
SCHEME = "v1.8.0"  # the label map and targets the baseline uses
THRESHOLD = DEFAULT_MIN_CONFIDENCE
LOW_THRESHOLD = 0.05
_EPS = bench._EPS

VOICE_RULES: tuple[str, ...] = ("V1", "V2", "V3", "V4")
HORN_RULES: tuple[str, ...] = ("H1", "H2")
COMBINED_RULES: tuple[str, ...] = ("C1",)
RULES: dict[str, str] = {
    "V1": "Speech dominance: voice fires only if the top label of all 521 is a voice label",
    "V2": "Persistence: voice fires only if a neighbouring window was also won by voice",
    "V3": "Voice minimum 0.30",
    "V4": "Voice minimum 0.50",
    "H1": "Alarm and traffic outrank voice and media",
    "H2": "Alarm and traffic outrank everything",
    "C1": "H1 with V1 (H1 applied first)",
}
VOICE_MINIMUM: dict[str, float] = {"V3": 0.30, "V4": 0.50}
ALARM_FAMILY: tuple[str, ...] = ("alarm", "traffic")


def rule_family(rule: str) -> str:
    if rule in VOICE_RULES:
        return "voice"
    if rule in HORN_RULES:
        return "horn"
    return "combined"


# ---------------------------------------------------------------------------
# One clip's scores, viewed per OpenHear class
# ---------------------------------------------------------------------------


@dataclass
class ClipScores:
    """Stored scores for one clip plus the per-class view the rules need."""

    spec: datasets.ClipSpec
    scores: np.ndarray  # (windows, 521)
    base: bench.Decided  # the shipped decision
    class_score: dict[str, np.ndarray]  # class -> best score per window
    class_label: dict[str, list[str]]  # class -> label carrying that score
    top_label: list[str]  # highest-scoring of all labels, per window


def build_clip(
    spec: datasets.ClipSpec, scores: np.ndarray, labels: list[str], label_map: dict[str, str]
) -> ClipScores:
    base = bench.decide(spec, scores, labels, label_map)
    class_score: dict[str, np.ndarray] = {}
    class_label: dict[str, list[str]] = {}
    top_label: list[str] = []
    if scores.size:
        columns: dict[str, list[int]] = {}
        for index, label in enumerate(labels[: scores.shape[1]]):
            key = label_map.get(label)
            if key and key != "silence":
                columns.setdefault(key, []).append(index)
        for key, cols in columns.items():
            sub = scores[:, cols]
            position = sub.argmax(axis=1)
            class_score[key] = sub.max(axis=1)
            class_label[key] = [labels[cols[int(p)]] for p in position]
        top_label = [labels[int(i)] for i in scores.argmax(axis=1)]
    return ClipScores(spec, scores, base, class_score, class_label, top_label)


# ---------------------------------------------------------------------------
# The rules
# ---------------------------------------------------------------------------


def _copy(decided: bench.Decided) -> bench.Decided:
    return bench.Decided(
        decided.spec,
        list(decided.win_class),
        list(decided.win_score),
        list(decided.win_label),
        decided.top_raw_label,
    )


def _silence(decided: bench.Decided, window: int) -> None:
    decided.win_class[window] = "silence"
    decided.win_score[window] = 0.0
    decided.win_label[window] = "silence"


def _apply_voice_rule(rule: str, clip: ClipScores, current: bench.Decided, label_map: dict) -> bench.Decided:
    out = _copy(current)
    fires = [
        key == "voice" and score >= THRESHOLD - _EPS
        for key, score in zip(current.win_class, current.win_score, strict=True)
    ]
    for window, key in enumerate(current.win_class):
        if key != "voice":
            continue
        if rule == "V1":
            keep = label_map.get(clip.top_label[window]) == "voice"
        elif rule == "V2":
            before = window > 0 and fires[window - 1]
            after = window + 1 < len(fires) and fires[window + 1]
            keep = before or after
        else:
            keep = current.win_score[window] >= VOICE_MINIMUM[rule] - _EPS
        if not keep:
            _silence(out, window)
    return out


def _apply_horn_rule(rule: str, clip: ClipScores, current: bench.Decided) -> bench.Decided:
    out = _copy(current)
    alarm = clip.class_score.get("alarm")
    traffic = clip.class_score.get("traffic")
    for window, winner in enumerate(current.win_class):
        if winner in ALARM_FAMILY:
            continue
        if rule == "H1" and winner not in ("voice", "media"):
            continue
        a = float(alarm[window]) if alarm is not None else 0.0
        t = float(traffic[window]) if traffic is not None else 0.0
        if max(a, t) < THRESHOLD - _EPS:
            continue
        key = "alarm" if a >= t else "traffic"
        out.win_class[window] = key
        out.win_score[window] = max(a, t)
        out.win_label[window] = clip.class_label[key][window]
    return out


def apply_rule(rule: str, clip: ClipScores, label_map: dict[str, str]) -> bench.Decided:
    """Return the clip's decision under *rule* ("baseline" returns the shipped decision)."""
    if rule == "baseline":
        return clip.base
    if rule in VOICE_RULES:
        return _apply_voice_rule(rule, clip, clip.base, label_map)
    if rule in HORN_RULES:
        return _apply_horn_rule(rule, clip, clip.base)
    if rule == "C1":
        after_h1 = _apply_horn_rule("H1", clip, clip.base)
        return _apply_voice_rule("V1", clip, after_h1, label_map)
    raise ValueError(f"unknown rule: {rule}")


# ---------------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------------


def _in_scope(spec: datasets.ClipSpec) -> bool:
    return bool(spec.targets.get(SCHEME)) or bool(spec.negative.get(SCHEME))


def summarise(decided: list[bench.Decided]) -> dict:
    """Hits per class, false alerts and wrong alarm/traffic fires at the shipped threshold."""
    scored = bench.score_at_threshold(decided, SCHEME, THRESHOLD)
    wrong = dict.fromkeys(ALARM_FAMILY, 0)
    for clip in decided:
        if not _in_scope(clip.spec):
            continue
        fired = clip.fired(THRESHOLD)
        targets = clip.spec.targets.get(SCHEME, frozenset())
        for key in ALARM_FAMILY:
            if key in fired and key not in targets:
                wrong[key] += 1
    return {
        "hits": {
            key: {"hits": row["hit"]["count"], "of": row["hit"]["of"]}
            for key, row in scored["per_class"].items()
        },
        "false_alert_clips": scored["negatives"]["clips_with_false_alert"]["count"],
        "negative_clips": scored["negatives"]["clips_with_false_alert"]["of"],
        "false_alerts_by_pattern": scored["negatives"]["by_pattern"],
        "wrong_fires": wrong,
        "groups": scored["groups"],
    }


def compare(rule: str, base: dict, result: dict) -> dict:
    """The facts the pass conditions need, for one rule on one dataset."""
    classes = sorted(set(base["hits"]) | set(result["hits"]))
    delta = {
        key: result["hits"].get(key, {}).get("hits", 0) - base["hits"].get(key, {}).get("hits", 0)
        for key in classes
    }
    alarm_tested = "alarm" in base["hits"]
    traffic_tested = "traffic" in base["hits"]
    gained = sum(max(0, delta.get(key, 0)) for key in ALARM_FAMILY)
    added_wrong = sum(result["wrong_fires"][k] - base["wrong_fires"][k] for k in ALARM_FAMILY)
    lost_other = sum(max(0, -value) for key, value in delta.items() if key not in ALARM_FAMILY)
    facts = {
        "hit_change_by_class": delta,
        "alarm_tested": alarm_tested,
        "alarm_hits_lost": max(0, -delta.get("alarm", 0)),
        "gate_no_alarm_hit_lost": delta.get("alarm", 0) >= 0,
        "false_alert_clips_change": result["false_alert_clips"] - base["false_alert_clips"],
        "traffic_tested": traffic_tested,
        "traffic_hits_change": delta.get("traffic", 0),
        "alarm_and_traffic_hits_gained": gained,
        "wrong_alarm_or_traffic_clips_added": added_wrong,
        "hits_lost_by_other_classes": lost_other,
        "any_class_lost_hits": any(value < 0 for value in delta.values()),
        "missed_speech": max(0, -delta.get("voice", 0)) if "voice" in base["hits"] else None,
    }
    voice_selected = (
        facts["gate_no_alarm_hit_lost"]
        and facts["false_alert_clips_change"] < 0
        and not facts["any_class_lost_hits"]
    )
    horn_selected = (
        facts["gate_no_alarm_hit_lost"]
        and facts["traffic_hits_change"] > 0
        and added_wrong <= max(0, facts["traffic_hits_change"])
        and not facts["any_class_lost_hits"]
    )
    voice_confirmed = facts["gate_no_alarm_hit_lost"] and facts["false_alert_clips_change"] <= 0
    horn_confirmed = (
        facts["gate_no_alarm_hit_lost"]
        and facts["traffic_hits_change"] >= 0
        and added_wrong <= gained
        and lost_other <= gained
    )
    family = rule_family(rule)
    if family == "voice":
        facts["selected_if_esc50"], facts["confirmed_if_held_out"] = voice_selected, voice_confirmed
    elif family == "horn":
        facts["selected_if_esc50"], facts["confirmed_if_held_out"] = horn_selected, horn_confirmed
    else:
        facts["selected_if_esc50"] = voice_selected and horn_selected
        facts["confirmed_if_held_out"] = voice_confirmed and horn_confirmed
    return facts


# ---------------------------------------------------------------------------
# Diagnostics on the baseline
# ---------------------------------------------------------------------------


def _bucket(windows: int) -> str:
    if windows <= 1:
        return "1 window"
    if windows <= 5:
        return "2 to 5 windows"
    if windows <= 10:
        return "6 to 10 windows"
    return "11 or more windows"


def voice_false_alerts_by_index(clips: list[ClipScores], labels: list[str]) -> dict:
    """Which YAMNet index carried each voice false alert on negative clips."""
    index_of = {label: index for index, label in enumerate(labels)}
    counts: Counter[str] = Counter()
    total = 0
    for clip in clips:
        if not clip.spec.negative.get(SCHEME):
            continue
        fired = clip.base.fired(THRESHOLD)
        if "voice" not in fired:
            continue
        total += 1
        label = fired["voice"][1]
        counts[f"{index_of.get(label, -1)} {label}"] += 1
    return {"negative_clips_where_voice_fired": total, "by_yamnet_index": dict(counts.most_common())}


def horn_breakdown(clips: list[ClipScores], v17_traffic_labels: set[str]) -> dict:
    """Why horn (traffic) target clips are missed at the shipped threshold."""
    targets = [clip for clip in clips if "traffic" in clip.spec.targets.get(SCHEME, ())]
    causes: Counter[str] = Counter()
    masked_by: Counter[str] = Counter()
    missed_top: Counter[str] = Counter()
    by_length: dict[str, list[int]] = {}
    hits = hits_low = alarm_on_horn = alarm_on_missed = 0
    for clip in targets:
        fired = clip.base.fired(THRESHOLD)
        hit = "traffic" in fired
        hits += hit
        hits_low += "traffic" in clip.base.fired(LOW_THRESHOLD)
        alarm_on_horn += "alarm" in fired
        tally = by_length.setdefault(_bucket(len(clip.base.win_class)), [0, 0])
        tally[0] += hit
        tally[1] += 1
        if hit:
            continue
        alarm_on_missed += "alarm" in fired
        missed_top[clip.base.top_raw_label] += 1
        traffic = clip.class_score.get("traffic")
        best = float(traffic.max()) if traffic is not None and traffic.size else 0.0
        strong_windows = (
            [w for w, value in enumerate(traffic) if value >= THRESHOLD - _EPS] if traffic is not None else []
        )
        won_low = any(
            key == "traffic" and LOW_THRESHOLD - _EPS <= score < THRESHOLD - _EPS
            for key, score in zip(clip.base.win_class, clip.base.win_score, strict=True)
        )
        if strong_windows:
            causes["masked: horn scored 0.20 or more but another class scored higher"] += 1
            winners = Counter(clip.base.win_class[w] for w in strong_windows)
            masked_by[winners.most_common(1)[0][0]] += 1
        elif won_low:
            causes["threshold: horn won a window but scored 0.05 to 0.20"] += 1
        elif best >= LOW_THRESHOLD - _EPS:
            causes["weak and outscored: horn scored 0.05 to 0.20 and another class won"] += 1
        elif clip.base.top_raw_label == "Vehicle" or clip.base.top_raw_label in v17_traffic_labels:
            causes["index mapping: top label is a vehicle or engine label outside the allowlist"] += 1
        else:
            causes["not detected: no horn label reached 0.05"] += 1
    wrong_low = 0
    traffic_on_alarm = alarm_targets = 0
    for clip in clips:
        targets_here = clip.spec.targets.get(SCHEME, frozenset())
        if _in_scope(clip.spec) and "traffic" not in targets_here:
            wrong_low += "traffic" in clip.base.fired(LOW_THRESHOLD)
        if "alarm" in targets_here:
            alarm_targets += 1
            traffic_on_alarm += "traffic" in clip.base.fired(THRESHOLD)
    return {
        "horn_target_clips": len(targets),
        "hits_at_0.20": hits,
        "hits_at_0.05": hits_low,
        "non_target_clips_where_traffic_fires_at_0.05": wrong_low,
        "missed_at_0.20": len(targets) - hits,
        "missed_by_cause": dict(causes.most_common()),
        "masked_by_class": dict(masked_by.most_common()),
        "missed_clips_top_yamnet_label": dict(missed_top.most_common(10)),
        "hits_by_clip_length": {
            key: {"hits": value[0], "of": value[1]} for key, value in sorted(by_length.items())
        },
        "horn_clips_where_alarm_fired": alarm_on_horn,
        "missed_horn_clips_where_alarm_fired": alarm_on_missed,
        "alarm_target_clips": alarm_targets,
        "alarm_target_clips_where_traffic_fired": traffic_on_alarm,
    }


def score_distributions(clips: list[ClipScores]) -> dict:
    """For every class: how its best winning score is distributed over target and negative clips."""
    out: dict[str, dict[str, Counter]] = {}
    for clip in clips:
        best = clip.base.class_max()
        targets = clip.spec.targets.get(SCHEME, frozenset())
        negative = bool(clip.spec.negative.get(SCHEME))
        for key in set(best) | set(targets):
            value = f"{best[key][0]:.4f}" if key in best else "none"
            row = out.setdefault(key, {"target_clips": Counter(), "negative_clips": Counter()})
            if key in targets:
                row["target_clips"][value] += 1
            elif negative:
                row["negative_clips"][value] += 1
    return {
        key: {kind: dict(sorted(counter.items())) for kind, counter in row.items()}
        for key, row in sorted(out.items())
    }


def score_grid(matrix: np.ndarray) -> dict:
    """Describe the set of values the stored scores take."""
    if not matrix.size:
        return {"distinct_values": 0}
    values = np.unique(matrix)
    scaled = values.astype(np.float64) * 256.0
    on_grid = bool(np.all(np.abs(scaled - np.round(scaled)) < 1e-3))
    steps = sorted({int(round(v)) for v in scaled})
    return {
        "distinct_values": int(values.size),
        "all_multiples_of_1_over_256": on_grid,
        "smallest_nonzero_value": float(values[values > 0].min()) if np.any(values > 0) else None,
        "largest_value": float(values.max()),
        "values_from_0.15_to_0.55": [
            round(step / 256.0, 6) for step in steps if 0.15 <= step / 256.0 <= 0.55
        ],
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

KEY_GROUPS: dict[str, tuple[str, ...]] = {
    "esc50": ("car_horn", "siren", "clock_alarm", "engine", "laughing", "coughing", "church_bells"),
    "fsd50k": ("Vehicle_horn_and_car_horn_and_honking", "Siren", "Speech", "Doorbell", "Ringtone", "Knock"),
    "sonyc": ("car_horn", "reverse_beeper", "siren", "engine_only"),
}


load_stored_scores = bench.load_stored_scores


def build_report(
    dataset: str,
    scored: list[tuple[datasets.ClipSpec, np.ndarray]],
    labels: list[str],
    provenance: dict,
    matrix: np.ndarray | None = None,
    v18_report: dict | None = None,
) -> dict:
    label_maps = bench.load_label_maps(labels)
    label_map = label_maps[SCHEME]
    v17_traffic = {label for label, key in label_maps["v1.7.0"].items() if key == "traffic"}
    clips = [build_clip(spec, scores, labels, label_map) for spec, scores in scored]

    summaries = {"baseline": summarise([clip.base for clip in clips])}
    for rule in RULES:
        summaries[rule] = summarise([apply_rule(rule, clip, label_map) for clip in clips])
    base = summaries["baseline"]
    keep = KEY_GROUPS.get(dataset, ())
    for summary in summaries.values():
        summary["groups"] = {g: row for g, row in summary["groups"].items() if g in keep}

    baseline_check = None
    if v18_report is not None:
        shipped = v18_report["schemes"][SCHEME]["at_shipped_threshold"]
        baseline_check = {
            "hits_match": all(
                base["hits"].get(key, {}).get("hits") == row["hit"]["count"]
                for key, row in shipped["per_class"].items()
            ),
            "false_alerts_match": base["false_alert_clips"]
            == shipped["negatives"]["clips_with_false_alert"]["count"],
            "raw_scores_sha256_match": provenance.get("raw_scores_sha256")
            == v18_report["provenance"].get("raw_scores_sha256"),
        }

    report = {
        "schema_version": SCHEMA_VERSION,
        "kind": "openhear-awareness-bench-rules",
        "dataset": dataset,
        "scope": (
            "Re-analysis of stored model scores. Classifier only, on recorded clips. "
            "No wearers, no microphone, no wristband, no real rooms. Not a clinical result."
        ),
        "plan": "docs/BENCH_PLAN_v1.9.md",
        "provenance": provenance,
        "baseline": {
            "label_map": SCHEME,
            "label_map_sha256": bench.label_map_sha256(label_map),
            "threshold": THRESHOLD,
            "matches_v1.8.0_report": baseline_check,
        },
        "rules": RULES,
        "clips": {"scored": len(clips), "windows": int(sum(len(c.base.win_class) for c in clips))},
        "results": summaries,
        "against_baseline": {rule: compare(rule, base, summaries[rule]) for rule in RULES},
        "diagnostics": {
            "voice_false_alerts": voice_false_alerts_by_index(clips, labels),
            "horn": horn_breakdown(clips, v17_traffic),
            "score_distributions": score_distributions(clips),
            "score_grid": score_grid(matrix) if matrix is not None else None,
        },
        "report_sha256": None,
    }
    report["report_sha256"] = bench.hash_report(report)
    return report


def build_verdict(reports: dict[str, dict]) -> dict:
    """Combine the three datasets' facts into pass or fail for each rule, per the plan."""
    held_out = [name for name in ("fsd50k", "sonyc") if name in reports]
    rules: dict[str, dict] = {}
    for rule in RULES:
        selected = bool(reports["esc50"]["against_baseline"][rule]["selected_if_esc50"])
        confirmed = {
            name: bool(reports[name]["against_baseline"][rule]["confirmed_if_held_out"])
            for name in held_out
        }
        gate = {
            name: bool(report["against_baseline"][rule]["gate_no_alarm_hit_lost"])
            for name, report in reports.items()
        }
        passes = selected and len(held_out) == 2 and all(confirmed.values()) and all(gate.values())
        family = rule_family(rule)
        rules[rule] = {
            "name": RULES[rule],
            "family": family,
            "gate_no_alarm_hit_lost": gate,
            "selected_on_esc50": selected,
            "confirmed_on": confirmed,
            "passes_protocol": passes,
            "may_be_enabled": passes and family == "horn",
        }
        if "fsd50k" in reports:
            rules[rule]["missed_speech_on_fsd50k"] = reports["fsd50k"]["against_baseline"][rule][
                "missed_speech"
            ]
    eligible = [rule for rule in HORN_RULES if rules[rule]["may_be_enabled"]]
    verdict = {
        "schema_version": SCHEMA_VERSION,
        "kind": "openhear-awareness-bench-rules-verdict",
        "plan": "docs/BENCH_PLAN_v1.9.md",
        "report_sha256_by_dataset": {name: report["report_sha256"] for name, report in reports.items()},
        "rules": rules,
        "voice_rules_stay_off": True,
        "rule_that_may_be_enabled": eligible[0] if eligible else None,
        "report_sha256": None,
    }
    verdict["report_sha256"] = bench.hash_report(verdict)
    return verdict


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------


def _signed(value: int) -> str:
    return f"+{value}" if value > 0 else str(value)


def render_markdown(report: dict) -> str:
    results = report["results"]
    base = results["baseline"]
    classes = sorted(base["hits"])
    lines = [
        f"Clips: {report['clips']['scored']}, windows: {report['clips']['windows']}. "
        f"Baseline: label map {report['baseline']['label_map']} at threshold "
        f"{report['baseline']['threshold']:.2f}.",
        "",
        "Hits per class (change against the baseline in brackets):",
        "",
        "| Rule | " + " | ".join(f"{key} (of {base['hits'][key]['of']})" for key in classes) + " |",
        "|---|" + "---|" * len(classes),
    ]
    for rule, summary in results.items():
        cells = []
        for key in classes:
            hits = summary["hits"].get(key, {}).get("hits", 0)
            change = hits - base["hits"][key]["hits"]
            cells.append(str(hits) if rule == "baseline" else f"{hits} ({_signed(change)})")
        lines.append(f"| {rule} | " + " | ".join(cells) + " |")
    lines += [
        "",
        f"False alerts and wrong fires (negative clips: {base['negative_clips']}):",
        "",
        "| Rule | False-alert clips | Led by voice | Wrong alarm clips | Wrong traffic clips |",
        "|---|---|---|---|---|",
    ]
    for rule, summary in results.items():
        change = summary["false_alert_clips"] - base["false_alert_clips"]
        shown = (
            str(summary["false_alert_clips"])
            if rule == "baseline"
            else f"{summary['false_alert_clips']} ({_signed(change)})"
        )
        lines.append(
            f"| {rule} | {shown} | {summary['false_alerts_by_pattern'].get('voice', 0)} "
            f"| {summary['wrong_fires']['alarm']} | {summary['wrong_fires']['traffic']} |"
        )
    lines += ["", "Rules: " + "; ".join(f"{key} = {name}" for key, name in report["rules"].items()) + ".", ""]
    horn = report["diagnostics"]["horn"]
    if horn["horn_target_clips"]:
        lines += [
            f"Horn clips at the baseline: {horn['hits_at_0.20']} of {horn['horn_target_clips']} hit at 0.20, "
            f"{horn['hits_at_0.05']} at 0.05 (where traffic also fires on "
            f"{horn['non_target_clips_where_traffic_fires_at_0.05']} non-target clips).",
            "",
            "| Why a horn clip was missed at 0.20 | Clips |",
            "|---|---|",
        ]
        lines += [f"| {cause} | {count} |" for cause, count in horn["missed_by_cause"].items()]
        lines.append("")
        if horn["masked_by_class"]:
            lines.append(
                "Masked by: " + ", ".join(f"{k} {v}" for k, v in horn["masked_by_class"].items()) + "."
            )
        lines.append(
            "Hits by clip length: "
            + ", ".join(f"{k} {v['hits']}/{v['of']}" for k, v in horn["hits_by_clip_length"].items())
            + "."
        )
        lines.append(
            f"Horn and alarm: alarm fired on {horn['horn_clips_where_alarm_fired']} horn clips "
            f"({horn['missed_horn_clips_where_alarm_fired']} of them missed horns); traffic fired on "
            f"{horn['alarm_target_clips_where_traffic_fired']} of {horn['alarm_target_clips']} alarm clips."
        )
        lines.append("")
    voice = report["diagnostics"]["voice_false_alerts"]
    lines += [
        f"Voice false alerts at the baseline: {voice['negative_clips_where_voice_fired']} negative clips, "
        "by YAMNet index: " + (", ".join(f"{k}: {v}" for k, v in voice["by_yamnet_index"].items()) or "none") + ".",
        "",
        f"Report SHA-256: `{report['report_sha256']}`",
        "",
    ]
    return "\n".join(lines)


def render_verdict_markdown(verdict: dict) -> str:
    lines = [
        "| Rule | No alarm hit lost | Selected on ESC-50 | Confirmed on FSD50K | Confirmed on SONYC-UST | Passes | Missed speech on FSD50K |",
        "|---|---|---|---|---|---|---|",
    ]

    def yn(value: bool | None) -> str:
        return "n/a" if value is None else ("yes" if value else "no")

    for rule, row in verdict["rules"].items():
        missed = row.get("missed_speech_on_fsd50k")
        lines.append(
            f"| {rule}: {row['name']} | {yn(all(row['gate_no_alarm_hit_lost'].values()))} "
            f"| {yn(row['selected_on_esc50'])} | {yn(row['confirmed_on'].get('fsd50k'))} "
            f"| {yn(row['confirmed_on'].get('sonyc'))} | {yn(row['passes_protocol'])} "
            f"| {'n/a' if missed is None else missed} |"
        )
    enabled = verdict["rule_that_may_be_enabled"]
    lines += [
        "",
        f"Rule that may be enabled under the plan: {enabled or 'none'}. Voice rules stay switched off.",
        "",
        f"Verdict SHA-256: `{verdict['report_sha256']}`",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------


def _analyse(args: argparse.Namespace) -> int:
    specs, notes, source, licence = bench.load_specs(args.dataset, Path(args.data))
    by_clip, labels, matrix = load_stored_scores(Path(args.scores))
    scored = [(spec, by_clip[spec.clip_id]) for spec in specs if spec.clip_id in by_clip]
    v18_path = bench.REPO_ROOT / "docs" / "bench" / f"awareness_bench_v1.8.0_{args.dataset}.json"
    v18_report = json.loads(v18_path.read_text(encoding="utf-8")) if v18_path.exists() else None
    provenance = {
        "git_sha": bench._git(["rev-parse", "HEAD"]),
        "dataset_source": source,
        "dataset_licence": licence,
        "dataset_notes": notes,
        "stored_scores_from_run": args.scores_run,
        "raw_scores_sha256": bench._sha256_file(Path(args.scores)),
        "model_was_run": False,
        "clips_listed": len(specs),
        "clips_with_stored_scores": len(scored),
        "run_url": args.run_url,
        "host": {"platform": platform.platform(), "python": platform.python_version(), "numpy": np.__version__},
    }
    report = build_report(args.dataset, scored, labels, provenance, matrix, v18_report)
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown:
        Path(args.markdown).write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["against_baseline"], indent=2, sort_keys=True), file=sys.stderr)
    return 0


def _verdict(args: argparse.Namespace) -> int:
    reports = {}
    for path in args.reports:
        report = json.loads(Path(path).read_text(encoding="utf-8"))
        if bench.hash_report(report) != report["report_sha256"]:
            raise SystemExit(f"signature check failed for {path}")
        reports[report["dataset"]] = report
    if "esc50" not in reports:
        raise SystemExit("the verdict needs the ESC-50 report: ESC-50 is the dataset that chooses")
    verdict = build_verdict(reports)
    if args.out:
        Path(args.out).write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown:
        Path(args.markdown).write_text(render_verdict_markdown(verdict), encoding="utf-8")
    print(render_verdict_markdown(verdict))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    analyse = sub.add_parser("analyse", help="apply the rules to one dataset's stored scores")
    analyse.add_argument("--dataset", required=True, choices=("esc50", "fsd50k", "sonyc"))
    analyse.add_argument("--data", required=True, help="Dataset metadata root")
    analyse.add_argument("--scores", required=True, help="Stored *_scores.npz from bench_awareness")
    analyse.add_argument("--scores-run", default="unknown", help="Workflow run the scores came from")
    analyse.add_argument("--run-url", default="local run")
    analyse.add_argument("--out")
    analyse.add_argument("--markdown")
    analyse.set_defaults(func=_analyse)
    verdict = sub.add_parser("verdict", help="combine dataset reports into pass or fail per rule")
    verdict.add_argument("--reports", nargs="+", required=True)
    verdict.add_argument("--out")
    verdict.add_argument("--markdown")
    verdict.set_defaults(func=_verdict)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
