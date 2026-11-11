"""
bench_awareness.py – bench test of the OpenHear sound classifier on recorded clips.

What this measures
------------------
Whether the classifier (YAMNet + the OpenHear label map in
``stream.sound_classifier``) fires the right wristband pattern for recorded
clips of everyday sounds, and how often it fires a pattern for a sound that
has no OpenHear class.

What this does not measure
--------------------------
No wearers, no microphone, no wristband and no real rooms. It says nothing
about whether a person can feel or name a pattern. It is not a clinical
result. See ``docs/INTENDED_PURPOSE.md`` and ``docs/EVALUATION.md``.

Method
------
Each clip is cut into consecutive 0.975 s windows at its native sample rate
(clips longer than 30 s are cut off there) and each window goes through
``YamnetClassifier.score_window``, the same model call the wristband runtime
makes. The raw score for every YAMNet class is kept for every window.

The decision rule is then applied to the stored scores, exactly as
``classify_scores`` applies it: the highest-scoring mapped label wins the
window, and its pattern fires if the score reaches the threshold. Because the
scores are stored, two label maps ("schemes") are scored on identical model
output: the map shipped in v1.7.0 and the map in this release.

* A *target* clip is a hit when its OpenHear class fires in at least one window.
* A *negative* clip is a false alert when any pattern fires in at least one window.

No audio and no model file is committed to this repository.

Usage::

    python -m scripts.bench_awareness --dataset esc50 --data /path/to/ESC-50 \\
        --model /path/to/yamnet.tflite --out report.json --markdown report.md
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import platform
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from scripts import bench_datasets as datasets
from stream.haptic_mapper import SOUND_PROFILES
from stream.sound_classifier import (
    DEFAULT_MIN_CONFIDENCE,
    VOICE_RULE_V3_MINIMUM,
    WINDOW_SECONDS,
    map_label_to_sound_key,
)

SCHEMA_VERSION = 2
V3_SCHEME = "v1.8.0+V3"
REPO_ROOT = Path(__file__).resolve().parent.parent
LABELS_CSV = REPO_ROOT / "stream" / "data" / "yamnet_class_map.csv"
LABEL_MAP_V17 = REPO_ROOT / "docs" / "bench" / "label_map_v1.7.0.json"

THRESHOLDS: tuple[float, ...] = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50)
PR_THRESHOLDS: tuple[float, ...] = tuple(round(0.05 * step, 2) for step in range(1, 20))
TOP_K = 10
_EPS = 1e-9


# ---------------------------------------------------------------------------
# Small statistics helpers
# ---------------------------------------------------------------------------


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion. Returns (low, high)."""
    if n <= 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _rate(successes: int, n: int) -> dict:
    low, high = wilson_interval(successes, n)
    return {
        "count": int(successes),
        "of": int(n),
        "rate": round(successes / n, 4) if n else None,
        "wilson95": [round(low, 4), round(high, 4)],
    }


# ---------------------------------------------------------------------------
# Label maps
# ---------------------------------------------------------------------------


def load_yamnet_labels(path: Path = LABELS_CSV) -> list[str]:
    with open(path, newline="", encoding="utf-8") as fh:
        return [row["display_name"] for row in csv.DictReader(fh)]


def current_label_map(labels: list[str]) -> dict[str, str]:
    """The label map the code ships today: YAMNet label -> OpenHear class."""
    return {label: key for label in labels if (key := map_label_to_sound_key(label))}


def load_label_maps(labels: list[str]) -> dict[str, dict[str, str]]:
    """Both schemes' label maps, keyed by scheme name."""
    with open(LABEL_MAP_V17, encoding="utf-8") as fh:
        v17 = json.load(fh)
    return {"v1.7.0": v17, "v1.8.0": current_label_map(labels)}


def label_map_sha256(label_map: dict[str, str]) -> str:
    blob = json.dumps(label_map, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


# ---------------------------------------------------------------------------
# Scoring one clip
# ---------------------------------------------------------------------------


def split_windows(
    samples: np.ndarray, sample_rate: int, max_seconds: float = datasets.MAX_CLIP_SECONDS
) -> list[np.ndarray]:
    """Cut a clip into consecutive full classifier windows at its native rate."""
    mono = np.asarray(samples, dtype=np.float32)
    if mono.ndim > 1:
        mono = mono.mean(axis=1)
    mono = mono[: int(round(sample_rate * max_seconds))]
    size = int(round(sample_rate * WINDOW_SECONDS))
    if size <= 0 or len(mono) < size:
        return [mono] if len(mono) else []
    return [mono[i : i + size] for i in range(0, len(mono) - size + 1, size)]


def score_clip(classifier, samples: np.ndarray, sample_rate: int) -> np.ndarray:
    """Raw YAMNet scores for each window of a clip: shape (windows, classes)."""
    rows = [
        np.asarray(classifier.score_window(window, sample_rate), dtype=np.float32)
        for window in split_windows(samples, sample_rate)
    ]
    if not rows:
        return np.zeros((0, 0), dtype=np.float32)
    return np.stack(rows)


@dataclass
class Decided:
    """One clip after a label map has been applied to its stored scores."""

    spec: datasets.ClipSpec
    win_class: list[str]  # winning class per window ("silence" if none mapped)
    win_score: list[float]  # its score
    win_label: list[str]  # the YAMNet label that carried it
    top_raw_label: str  # highest-scoring YAMNet label anywhere in the clip, mapped or not

    def class_max(self) -> dict[str, tuple[float, str]]:
        """For each class that won a window: its best winning score and label."""
        best: dict[str, tuple[float, str]] = {}
        for key, score, label in zip(self.win_class, self.win_score, self.win_label, strict=True):
            if key == "silence":
                continue
            if key not in best or score > best[key][0]:
                best[key] = (score, label)
        return best

    def fired(self, threshold: float) -> dict[str, tuple[float, str]]:
        """Classes that fire a pattern somewhere in the clip at *threshold*."""
        return {
            key: value for key, value in self.class_max().items() if value[0] >= threshold - _EPS
        }

    def windows_fired(self, threshold: float) -> int:
        return sum(
            1
            for key, score in zip(self.win_class, self.win_score, strict=True)
            if key != "silence" and score >= threshold - _EPS
        )


def decide(
    spec: datasets.ClipSpec,
    scores: np.ndarray,
    labels: list[str],
    label_map: dict[str, str],
    voice_minimum: float = 0.0,
) -> Decided:
    """Apply a label map to one clip's stored scores, as ``classify_scores`` does.

    The highest-scoring mapped label wins each window. Ties go to the lower
    class index, and a score of zero never wins, matching the shipped loop.
    ``voice_minimum`` applies rule V3 as the shipped classifier does: a window
    won by voice below that score fires nothing.
    """
    win_class: list[str] = []
    win_score: list[float] = []
    win_label: list[str] = []
    top_raw = "none"
    if scores.size:
        mapped = [index for index, label in enumerate(labels[: scores.shape[1]]) if label in label_map]
        sub = scores[:, mapped] if mapped else np.zeros((scores.shape[0], 0), dtype=np.float32)
        for row in sub:
            if row.size == 0 or float(row.max()) <= 0.0:
                win_class.append("silence")
                win_score.append(0.0)
                win_label.append("silence")
                continue
            position = int(np.argmax(row))
            label = labels[mapped[position]]
            if label_map[label] == "voice" and float(row[position]) < voice_minimum:
                win_class.append("silence")
                win_score.append(0.0)
                win_label.append("silence")
                continue
            win_class.append(label_map[label])
            win_score.append(float(row[position]))
            win_label.append(label)
        top_raw = labels[int(np.argmax(scores.max(axis=0)))]
    return Decided(spec, win_class, win_score, win_label, top_raw)


# ---------------------------------------------------------------------------
# Scoring a scheme
# ---------------------------------------------------------------------------


def _in_scope(clip: Decided, scheme: str) -> bool:
    return bool(clip.spec.targets.get(scheme)) or bool(clip.spec.negative.get(scheme))


def score_at_threshold(clips: list[Decided], scheme: str, threshold: float) -> dict:
    """Hits, misses and false alerts for one scheme at one threshold."""
    per_class: dict[str, dict] = {}
    groups: dict[str, dict] = {}
    neg_clips = neg_fired = neg_windows = neg_windows_fired = 0
    neg_by_pattern: Counter[str] = Counter()
    neg_by_label: Counter[str] = Counter()

    for clip in clips:
        fired = clip.fired(threshold)
        targets = clip.spec.targets.get(scheme, frozenset())
        for group in clip.spec.groups:
            row = groups.setdefault(group, {"clips": 0, "any": 0, "by_class": Counter()})
            row["clips"] += 1
            row["any"] += 1 if fired else 0
            row["by_class"].update(fired.keys())
        for target in sorted(targets):
            row = per_class.setdefault(
                target,
                {
                    "clips": 0,
                    "hits": 0,
                    "hits_with_other_pattern": 0,
                    "missed_as": Counter(),
                    "missed_top_label": Counter(),
                },
            )
            row["clips"] += 1
            others = {key: value for key, value in fired.items() if key not in targets}
            if target in fired:
                row["hits"] += 1
                row["hits_with_other_pattern"] += 1 if others else 0
            else:
                wrong = max(others.items(), key=lambda item: item[1][0])[0] if others else "nothing"
                row["missed_as"][wrong] += 1
                row["missed_top_label"][clip.top_raw_label] += 1
        if clip.spec.negative.get(scheme):
            neg_clips += 1
            neg_windows += len(clip.win_class)
            neg_windows_fired += clip.windows_fired(threshold)
            if fired:
                neg_fired += 1
                key, (_, label) = max(fired.items(), key=lambda item: item[1][0])
                neg_by_pattern[key] += 1
                neg_by_label[f"{label} -> {key}"] += 1

    hits = sum(row["hits"] for row in per_class.values())
    target_clips = sum(row["clips"] for row in per_class.values())
    return {
        "threshold": threshold,
        "targets_overall": _rate(hits, target_clips),
        "per_class": {
            key: {
                "hit": _rate(row["hits"], row["clips"]),
                "hits_with_other_pattern": row["hits_with_other_pattern"],
                "missed_as": dict(row["missed_as"].most_common()),
                "missed_clips_top_yamnet_label": dict(row["missed_top_label"].most_common(8)),
            }
            for key, row in sorted(per_class.items())
        },
        "negatives": {
            "clips_with_false_alert": _rate(neg_fired, neg_clips),
            "windows_with_false_alert": _rate(neg_windows_fired, neg_windows),
            "by_pattern": dict(neg_by_pattern.most_common()),
            "by_yamnet_label": dict(neg_by_label.most_common(25)),
        },
        "groups": {
            group: {
                "clips": row["clips"],
                "any_pattern_fired": row["any"],
                "fired_by_class": dict(row["by_class"].most_common()),
            }
            for group, row in sorted(groups.items())
        },
    }


def precision_recall(clips: list[Decided], scheme: str) -> dict:
    """Per-class precision and recall at each PR threshold.

    Precision for a class is: clips where it fired and was a target, out of
    all in-scope clips where it fired. Recall is its hit rate.
    """
    in_scope = [clip for clip in clips if _in_scope(clip, scheme)]
    classes = sorted({key for clip in in_scope for key in clip.spec.targets.get(scheme, ())})
    maxima = [clip.class_max() for clip in in_scope]
    out: dict[str, list[dict]] = {}
    for key in classes:
        target_flags = [key in clip.spec.targets.get(scheme, ()) for clip in in_scope]
        total_targets = sum(target_flags)
        rows = []
        for threshold in PR_THRESHOLDS:
            fired = [key in best and best[key][0] >= threshold - _EPS for best in maxima]
            true_pos = sum(1 for f, t in zip(fired, target_flags, strict=True) if f and t)
            fired_n = sum(fired)
            rows.append(
                {
                    "threshold": threshold,
                    "fired": fired_n,
                    "true_positive": true_pos,
                    "precision": round(true_pos / fired_n, 4) if fired_n else None,
                    "recall": round(true_pos / total_targets, 4) if total_targets else None,
                }
            )
        out[key] = rows
    return out


def score_distribution(clips: list[Decided], scheme: str) -> dict:
    """Describe the scores that decide results, so plateaus can be explained.

    A clip's result at a threshold depends only on each class's best winning
    score in that clip. If no such score falls between two thresholds, the
    results at those thresholds are identical.
    """
    in_scope = [clip for clip in clips if _in_scope(clip, scheme)]
    deciding = [score for clip in in_scope for score, _ in clip.class_max().values()]
    window_scores = [
        score
        for clip in in_scope
        for key, score in zip(clip.win_class, clip.win_score, strict=True)
        if key != "silence"
    ]
    histogram = [0] * 100
    for score in window_scores:
        histogram[min(99, int(score * 100 + _EPS))] += 1
    between = []
    for low, high in zip(THRESHOLDS, THRESHOLDS[1:], strict=False):
        between.append(
            {
                "from": low,
                "to": high,
                "deciding_scores_between": sum(1 for s in deciding if low - _EPS <= s < high - _EPS),
            }
        )
    distinct = sorted({round(score, 6) for score in window_scores})
    gaps = [round(b - a, 6) for a, b in zip(distinct, distinct[1:], strict=False)]
    return {
        "winning_window_scores": len(window_scores),
        "distinct_winning_scores": len(distinct),
        "smallest_gap_between_distinct_scores": min(gaps) if gaps else None,
        "median_gap_between_distinct_scores": float(np.median(gaps)) if gaps else None,
        "distinct_scores_from_0.15_to_0.45": [s for s in distinct if 0.15 <= s <= 0.45][:80],
        "histogram_bin_width": 0.01,
        "histogram_winning_window_scores": histogram,
        "deciding_scores_between_thresholds": between,
    }


def score_scheme(clips: list[Decided], scheme: str) -> dict:
    shipped = score_at_threshold(clips, scheme, DEFAULT_MIN_CONFIDENCE)
    sweep = []
    for threshold in THRESHOLDS:
        scored = score_at_threshold(clips, scheme, threshold)
        sweep.append(
            {
                "threshold": threshold,
                "target_hit_rate": scored["targets_overall"]["rate"],
                "false_alert_clip_rate": scored["negatives"]["clips_with_false_alert"]["rate"],
                "per_class_hit_rate": {
                    key: row["hit"]["rate"] for key, row in scored["per_class"].items()
                },
            }
        )
    return {
        "clips": {
            "targets": sum(1 for clip in clips if clip.spec.targets.get(scheme)),
            "negatives": sum(1 for clip in clips if clip.spec.negative.get(scheme)),
        },
        "at_shipped_threshold": shipped,
        "threshold_sweep": sweep,
        "precision_recall": precision_recall(clips, scheme),
        "score_distribution": score_distribution(clips, scheme),
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def hash_report(report: dict) -> str:
    """SHA-256 of the report body with ``report_sha256`` nulled (as scripts.benchmark)."""
    body = dict(report)
    body["report_sha256"] = None
    blob = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def tested_classes(specs: list[datasets.ClipSpec], scheme: str) -> list[str]:
    return sorted({key for spec in specs for key in spec.targets.get(scheme, ())})


def build_report(
    dataset: str,
    scored: list[tuple[datasets.ClipSpec, np.ndarray]],
    labels: list[str],
    label_maps: dict[str, dict[str, str]],
    provenance: dict,
    dataset_notes: dict | None = None,
    voice_rule_v3: bool = False,
) -> dict:
    """Assemble the signed report from stored scores.

    By default the v1.7.0 and v1.8.0 label maps are compared. With
    ``voice_rule_v3`` the current label map is scored with rule V3 off and on.
    """
    if voice_rule_v3:
        current = datasets.SCHEMES[-1]
        plan = [(current, current, 0.0), (V3_SCHEME, current, VOICE_RULE_V3_MINIMUM)]
    else:
        plan = [(scheme, scheme, 0.0) for scheme in datasets.SCHEMES]
    schemes = {}
    for name, scheme, voice_minimum in plan:
        decided = [
            decide(spec, scores, labels, label_maps[scheme], voice_minimum) for spec, scores in scored
        ]
        result = score_scheme(decided, scheme)
        specs = [spec for spec, _ in scored]
        every = [key for key in SOUND_PROFILES if key != "silence"]
        tested = tested_classes(specs, scheme)
        result["classes_tested"] = tested
        result["classes_not_tested"] = [key for key in every if key not in tested]
        result["label_map_sha256"] = label_map_sha256(label_maps[scheme])
        result["voice_minimum"] = voice_minimum
        schemes[name] = result
    report = {
        "schema_version": SCHEMA_VERSION,
        "kind": "openhear-awareness-bench",
        "dataset": dataset,
        "scope": (
            "Classifier only, on recorded clips. No wearers, no microphone, "
            "no wristband, no real rooms. Not a clinical result."
        ),
        "provenance": provenance,
        "dataset_notes": dataset_notes or {},
        "method": {
            "window_seconds": WINDOW_SECONDS,
            "max_clip_seconds": datasets.MAX_CLIP_SECONDS,
            "windowing": (
                "Consecutive non-overlapping windows at the clip's native sample rate; "
                "trailing part-window dropped; clips cut off at max_clip_seconds."
            ),
            "decision_rule": (
                "Highest-scoring mapped YAMNet label wins the window; its pattern fires "
                "if the score reaches the threshold. Applied to stored raw scores."
            ),
            "hit_rule": "Target class fires in at least one window of the clip.",
            "false_alert_rule": "Any pattern fires in at least one window of a negative clip.",
            "precision_rule": (
                "Clips where the class fired and was a target, out of all in-scope clips "
                "where it fired."
            ),
            "shipped_threshold": DEFAULT_MIN_CONFIDENCE,
            "schemes": {
                "v1.7.0": "Label map shipped in v1.7.0 (any engine fired traffic).",
                "v1.8.0": "Current label map (traffic is an allowlist of vehicle warnings).",
                V3_SCHEME: (
                    "Current label map with rule V3 on: a window won by voice fires only "
                    f"if its score is at least {VOICE_RULE_V3_MINIMUM:.2f}."
                ),
            },
            "schemes_in_this_report": list(schemes),
        },
        "clips": {"scored": len(scored), "windows": int(sum(len(s) for _, s in scored))},
        "schemes": schemes,
        "report_sha256": None,
    }
    report["report_sha256"] = hash_report(report)
    return report


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------


def _pct(rate: dict) -> str:
    if rate["rate"] is None:
        return "n/a"
    low, high = rate["wilson95"]
    return (
        f"{rate['count']}/{rate['of']} = {rate['rate'] * 100:.1f}% "
        f"(95% CI {low * 100:.1f} to {high * 100:.1f}%)"
    )


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.0f}%"


def render_markdown(report: dict) -> str:
    """Render one dataset's results section from a signed report."""
    prov = report["provenance"]
    lines: list[str] = []
    for scheme, result in report["schemes"].items():
        shipped = result["at_shipped_threshold"]
        neg = shipped["negatives"]
        lines += [
            f"#### Label map {scheme}",
            "",
            f"Threshold {report['method']['shipped_threshold']:.2f}. "
            f"Clips: {result['clips']['targets']} target, {result['clips']['negatives']} negative. "
            f"Not tested on this dataset: {', '.join(result['classes_not_tested']) or 'none'}.",
            "",
            "| Class | Hit rate | Hits where another pattern also fired | Misses classified as |",
            "|---|---|---|---|",
        ]
        for key, row in shipped["per_class"].items():
            missed = ", ".join(f"{k} {v}" for k, v in row["missed_as"].items()) or "none"
            lines.append(
                f"| {key} | {_pct(row['hit'])} | {row['hits_with_other_pattern']} | {missed} |"
            )
        lines += [
            f"| **All target clips** | {_pct(shipped['targets_overall'])} | | |",
            "",
            f"False alerts: any pattern fired on {_pct(neg['clips_with_false_alert'])} of negative "
            f"clips, and on {_pct(neg['windows_with_false_alert'])} of their windows.",
            "",
        ]
        if neg["by_pattern"]:
            lines.append(
                "By pattern: " + ", ".join(f"{k} {v}" for k, v in neg["by_pattern"].items()) + "."
            )
            lines.append("")
        if neg["by_yamnet_label"]:
            lines += [
                "| YAMNet label that fired on a negative clip | Clips |",
                "|---|---|",
            ]
            lines += [f"| {k} | {v} |" for k, v in list(neg["by_yamnet_label"].items())[:12]]
            lines.append("")
        if shipped["groups"]:
            lines += [
                "| Group | Clips | Any pattern fired | Patterns fired |",
                "|---|---|---|---|",
            ]
            for group, row in shipped["groups"].items():
                fired = ", ".join(f"{k} {v}" for k, v in row["fired_by_class"].items()) or "none"
                lines.append(f"| {group} | {row['clips']} | {row['any_pattern_fired']} | {fired} |")
            lines.append("")
        lines += [
            "Threshold sweep:",
            "",
            "| Threshold | Target hit rate | False-alert clip rate |",
            "|---|---|---|",
        ]
        for row in result["threshold_sweep"]:
            mark = " (shipped)" if abs(row["threshold"] - DEFAULT_MIN_CONFIDENCE) < 1e-9 else ""
            lines.append(
                f"| {row['threshold']:.2f}{mark} | {_fmt(row['target_hit_rate'])} "
                f"| {_fmt(row['false_alert_clip_rate'])} |"
            )
        lines.append("")
        curves = result["precision_recall"]
        if curves:
            picks = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70]
            lines += [
                "Precision / recall by class and threshold:",
                "",
                "| Class | " + " | ".join(f"{t:.2f}" for t in picks) + " |",
                "|---|" + "---|" * len(picks),
            ]
            for key, rows in curves.items():
                by_threshold = {row["threshold"]: row for row in rows}
                cells = [
                    f"{_fmt(by_threshold[t]['precision'])} / {_fmt(by_threshold[t]['recall'])}"
                    for t in picks
                ]
                lines.append(f"| {key} | " + " | ".join(cells) + " |")
            lines.append("")
        dist = result["score_distribution"]
        flat = [
            f"{row['from']:.2f} to {row['to']:.2f}"
            for row in dist["deciding_scores_between_thresholds"]
            if row["deciding_scores_between"] == 0
        ]
        lines += [
            f"Score distribution: {dist['winning_window_scores']} winning window scores took "
            f"{dist['distinct_winning_scores']} distinct values "
            f"(smallest gap {dist['smallest_gap_between_distinct_scores']}). "
            + (
                "No deciding score fell in: " + "; ".join(flat) + "."
                if flat
                else "Every threshold step had deciding scores in it."
            ),
            "",
        ]
    lines += [
        "Provenance:",
        "",
        f"- OpenHear commit: `{prov.get('git_sha')}`",
        f"- Model SHA-256: `{prov.get('model_sha256')}`",
        f"- Dataset: {prov.get('dataset_source')} ({prov.get('dataset_licence')})",
        f"- Workflow run: {prov.get('run_url')}",
        f"- Raw scores SHA-256: `{prov.get('raw_scores_sha256')}`",
        f"- Report SHA-256: `{report['report_sha256']}`",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------


def _git(args: list[str], cwd: Path | None = None) -> str:
    try:
        out = subprocess.check_output(["git", *args], cwd=cwd, stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_raw_scores(
    scored: list[tuple[datasets.ClipSpec, np.ndarray]], labels: list[str], npz_path: Path, top_path: Path
) -> None:
    """Write every raw score (npz) and a readable per-window top-10 (gzipped JSON lines)."""
    filled = [scores for _, scores in scored if scores.size]
    matrix = np.concatenate(filled) if filled else np.zeros((0, 0), dtype=np.float32)
    np.savez_compressed(
        npz_path,
        scores=matrix.astype(np.float32),
        clip_ids=np.array([spec.clip_id for spec, _ in scored]),
        windows_per_clip=np.array([len(scores) for _, scores in scored], dtype=np.int32),
        labels=np.array(labels),
    )
    with gzip.open(top_path, "wt", encoding="utf-8") as fh:
        for spec, scores in scored:
            windows = []
            for row in scores:
                order = np.argsort(row)[::-1][:TOP_K]
                windows.append([[labels[int(i)], round(float(row[int(i)]), 4)] for i in order])
            fh.write(
                json.dumps({"clip": spec.clip_id, "labels": list(spec.labels), "windows": windows})
                + "\n"
            )


def load_stored_scores(path: Path) -> tuple[dict[str, np.ndarray], list[str], np.ndarray]:
    """Read a ``*_scores.npz`` written by ``write_raw_scores``.

    Returns (scores by clip id, YAMNet labels, the full matrix).
    """
    data = np.load(path, allow_pickle=False)
    matrix = data["scores"]
    by_clip: dict[str, np.ndarray] = {}
    start = 0
    for clip_id, count in zip(data["clip_ids"], data["windows_per_clip"], strict=True):
        by_clip[str(clip_id)] = matrix[start : start + int(count)]
        start += int(count)
    return by_clip, [str(label) for label in data["labels"]], matrix


def load_specs(dataset: str, root: Path) -> tuple[list[datasets.ClipSpec], dict, str, str]:
    """Return (specs, notes, source, licence) for a dataset rooted at *root*."""
    if dataset == "esc50":
        return (
            datasets.load_esc50(root),
            {},
            "ESC-50 (github.com/karolpiczak/ESC-50)",
            datasets.ESC50_LICENCE,
        )
    if dataset == "fsd50k":
        specs, notes = datasets.load_fsd50k(root)
        return specs, notes, "FSD50K eval split (zenodo.org/records/4060432)", datasets.FSD50K_LICENCE
    if dataset == "sonyc":
        specs, notes = datasets.load_sonyc(root)
        return specs, notes, "SONYC-UST v2.3.0 (zenodo.org/records/3966543)", datasets.SONYC_LICENCE
    raise ValueError(f"unknown dataset: {dataset}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dataset", required=True, choices=("esc50", "fsd50k", "sonyc"))
    parser.add_argument("--data", required=True, help="Dataset root (metadata)")
    parser.add_argument("--audio-dir", help="Directory holding the audio (default: dataset root)")
    parser.add_argument("--audio-zip", help="Read audio straight from this zip archive")
    parser.add_argument("--model", help="Path to the YAMNet .tflite model")
    parser.add_argument(
        "--stored-scores",
        help="Score a stored *_scores.npz from an earlier run instead of running the model",
    )
    parser.add_argument("--scores-run", default=None, help="Workflow run the stored scores came from")
    parser.add_argument(
        "--voice-rule-v3",
        action="store_true",
        help="Score the current label map with rule V3 (voice minimum 0.30) off and on",
    )
    parser.add_argument("--model-source", default="unknown")
    parser.add_argument("--dataset-version", default="unknown")
    parser.add_argument("--run-url", default="local run")
    parser.add_argument("--out", help="Write the signed JSON report here")
    parser.add_argument("--markdown", help="Write the Markdown results section here")
    parser.add_argument("--scores-out", help="Write raw scores here (.npz); a .top10.jsonl.gz is written beside it")
    parser.add_argument("--limit", type=int, help="Only the first N clips (smoke test)")
    args = parser.parse_args(argv)

    if bool(args.model) == bool(args.stored_scores):
        parser.error("give exactly one of --model (run the model) or --stored-scores (re-score)")

    root = Path(args.data)
    labels = load_yamnet_labels()
    specs, notes, source, licence = load_specs(args.dataset, root)
    if args.limit:
        specs = specs[: args.limit]
    notes = dict(notes)
    notes["clips_listed"] = len(specs)

    scored: list[tuple[datasets.ClipSpec, np.ndarray]] = []
    raw_sha = top_sha = None
    if args.stored_scores:
        by_clip, stored_labels, _ = load_stored_scores(Path(args.stored_scores))
        if stored_labels != labels:
            raise SystemExit("stored scores were made with a different YAMNet label list")
        scored = [(spec, by_clip[spec.clip_id]) for spec in specs if spec.clip_id in by_clip]
        notes["clips_with_stored_scores"] = len(scored)
        raw_sha = _sha256_file(Path(args.stored_scores))
    else:
        from stream.sound_classifier import YamnetClassifier

        classifier = YamnetClassifier(args.model, str(LABELS_CSV))
        audio = datasets.iter_audio(
            specs,
            audio_dir=Path(args.audio_dir) if args.audio_dir else root,
            audio_zip=Path(args.audio_zip) if args.audio_zip else None,
        )
        for index, (spec, samples, rate) in enumerate(audio, start=1):
            scored.append((spec, score_clip(classifier, samples, rate)))
            if index % 250 == 0:
                print(f"scored {index}/{len(specs)} clips", file=sys.stderr, flush=True)
        notes["clips_with_audio_found"] = len(scored)

    if args.scores_out and not args.stored_scores:
        npz_path = Path(args.scores_out)
        top_path = npz_path.with_suffix(".top10.jsonl.gz")
        write_raw_scores(scored, labels, npz_path, top_path)
        raw_sha, top_sha = _sha256_file(npz_path), _sha256_file(top_path)

    provenance = {
        "git_sha": _git(["rev-parse", "HEAD"]),
        "model_was_run": not args.stored_scores,
        "model_sha256": _sha256_file(Path(args.model)) if args.model else None,
        "model_source": args.model_source,
        "stored_scores_from_run": args.scores_run,
        "dataset_source": source,
        "dataset_version": args.dataset_version,
        "dataset_licence": licence,
        "run_url": args.run_url,
        "raw_scores_sha256": raw_sha,
        "top10_per_window_sha256": top_sha,
        "host": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": np.__version__,
        },
        "limit": args.limit,
    }
    report = build_report(
        args.dataset,
        scored,
        labels,
        load_label_maps(labels),
        provenance,
        notes,
        voice_rule_v3=args.voice_rule_v3,
    )
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    if args.markdown:
        Path(args.markdown).write_text(render_markdown(report), encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
