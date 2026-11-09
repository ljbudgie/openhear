"""
bench_awareness.py – bench test of the OpenHear sound classifier on ESC-50.

What this measures
------------------
Whether the shipped classifier (YAMNet + the OpenHear label map in
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
ESC-50 has 2,000 five-second clips in 50 categories (40 clips each). Each
clip is cut into consecutive 0.975 s windows at its native sample rate and
each window goes through ``YamnetClassifier.classify_window``, the same call
the wristband runtime makes. The trailing part-window is dropped.

* A *target* clip is a hit when its OpenHear class fires in at least one
  window.
* A *negative* clip (an ESC-50 category with no OpenHear class) is a false
  alert when any pattern fires in at least one window.

Scores are read before thresholding, so one pass gives results at the
shipped threshold and across a threshold sweep.

Neither the audio (CC BY-NC) nor the model is committed to this repository.

Usage::

    python -m scripts.bench_awareness --esc50 /path/to/ESC-50 \\
        --model /path/to/yamnet.tflite --out report.json --markdown report.md
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from stream.haptic_mapper import SOUND_PROFILES
from stream.sound_classifier import DEFAULT_MIN_CONFIDENCE, WINDOW_SECONDS

SCHEMA_VERSION = 1

# ESC-50 category -> OpenHear class. Every other ESC-50 category is a negative.
TARGET_MAP: dict[str, str] = {
    "dog": "dog",
    "siren": "alarm",
    "clock_alarm": "alarm",
    "car_horn": "traffic",
    "engine": "traffic",
    "door_wood_knock": "knock",
    "crying_baby": "baby_cry",
}

# OpenHear classes that ESC-50 has no clips for. No figure is reported for these.
UNTESTED_CLASSES: tuple[str, ...] = ("voice", "doorbell", "media", "phone")

THRESHOLDS: tuple[float, ...] = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50)


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion. Returns (low, high)."""
    if n <= 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def split_windows(samples: np.ndarray, sample_rate: int) -> list[np.ndarray]:
    """Cut a clip into consecutive full classifier windows at its native rate."""
    mono = np.asarray(samples, dtype=np.float32)
    if mono.ndim > 1:
        mono = mono.mean(axis=1)
    size = int(round(sample_rate * WINDOW_SECONDS))
    if size <= 0 or len(mono) < size:
        return [mono] if len(mono) else []
    return [mono[i : i + size] for i in range(0, len(mono) - size + 1, size)]


def classify_clip(classifier, samples: np.ndarray, sample_rate: int) -> list[tuple[str, float]]:
    """Return (class, score) for each window, read before thresholding."""
    results = []
    for window in split_windows(samples, sample_rate):
        sound = classifier.classify_window(window, sample_rate, min_confidence=0.0)
        results.append((sound.sound_key, float(sound.confidence)))
    return results


def fired_classes(windows: list[tuple[str, float]], threshold: float) -> list[str]:
    """Classes that would fire a pattern in each window at *threshold*."""
    return [key for key, score in windows if key != "silence" and score >= threshold]


def _rate(successes: int, n: int) -> dict:
    low, high = wilson_interval(successes, n)
    return {
        "count": successes,
        "of": n,
        "rate": round(successes / n, 4) if n else None,
        "wilson95": [round(low, 4), round(high, 4)],
    }


def score_at_threshold(clips: list[dict], threshold: float) -> dict:
    """Score all clips at one threshold.

    Each clip dict has ``category`` (ESC-50 category) and ``windows``
    (list of (class, score) pairs).
    """
    per_class: dict[str, dict] = {}
    per_category: dict[str, dict] = {}
    neg_clips = neg_fired = neg_windows = neg_windows_fired = 0
    neg_by_pattern: Counter[str] = Counter()
    neg_by_category: dict[str, list[int]] = {}

    for clip in clips:
        category = clip["category"]
        fired = fired_classes(clip["windows"], threshold)
        target = TARGET_MAP.get(category)
        if target is not None:
            hit = target in fired
            others = [key for key in fired if key != target]
            for bucket, key in ((per_class, target), (per_category, category)):
                row = bucket.setdefault(
                    key,
                    {"clips": 0, "hits": 0, "hits_with_other_pattern": 0, "missed_as": Counter()},
                )
                row["clips"] += 1
                if hit:
                    row["hits"] += 1
                    if others:
                        row["hits_with_other_pattern"] += 1
                else:
                    wrong = Counter(others).most_common(1)
                    row["missed_as"][wrong[0][0] if wrong else "nothing"] += 1
        else:
            neg_clips += 1
            neg_windows += len(clip["windows"])
            neg_windows_fired += len(fired)
            tally = neg_by_category.setdefault(category, [0, 0])
            tally[1] += 1
            if fired:
                neg_fired += 1
                tally[0] += 1
                neg_by_pattern[Counter(fired).most_common(1)[0][0]] += 1

    def _finish(bucket: dict) -> dict:
        out = {}
        for key in sorted(bucket):
            row = bucket[key]
            out[key] = {
                "hit": _rate(row["hits"], row["clips"]),
                "hits_with_other_pattern": row["hits_with_other_pattern"],
                "missed_as": dict(row["missed_as"].most_common()),
            }
        return out

    total_hits = sum(row["hits"] for row in per_class.values())
    total_targets = sum(row["clips"] for row in per_class.values())
    return {
        "threshold": threshold,
        "targets_overall": _rate(total_hits, total_targets),
        "per_class": _finish(per_class),
        "per_esc50_category": _finish(per_category),
        "negatives": {
            "clips_with_false_alert": _rate(neg_fired, neg_clips),
            "windows_with_false_alert": _rate(neg_windows_fired, neg_windows),
            "by_pattern": dict(neg_by_pattern.most_common()),
            "by_esc50_category": {
                category: {"false_alert_clips": tally[0], "clips": tally[1]}
                for category, tally in sorted(
                    neg_by_category.items(), key=lambda item: (-item[1][0], item[0])
                )
            },
        },
    }


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


def hash_report(report: dict) -> str:
    """SHA-256 of the report body with ``report_sha256`` nulled (as scripts.benchmark)."""
    body = dict(report)
    body["report_sha256"] = None
    blob = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_report(clips: list[dict], provenance: dict) -> dict:
    """Assemble the signed report from classified clips."""
    shipped = score_at_threshold(clips, DEFAULT_MIN_CONFIDENCE)
    sweep = []
    for threshold in THRESHOLDS:
        scored = score_at_threshold(clips, threshold)
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
    report = {
        "schema_version": SCHEMA_VERSION,
        "kind": "openhear-awareness-bench",
        "scope": (
            "Classifier only, on recorded ESC-50 clips. No wearers, no microphone, "
            "no wristband, no real rooms. Not a clinical result."
        ),
        "provenance": provenance,
        "method": {
            "window_seconds": WINDOW_SECONDS,
            "windowing": (
                "Consecutive non-overlapping windows at the clip's native sample rate; "
                "trailing part-window dropped."
            ),
            "hit_rule": "Target class fires in at least one window of the clip.",
            "false_alert_rule": "Any pattern fires in at least one window of a negative clip.",
            "shipped_threshold": DEFAULT_MIN_CONFIDENCE,
            "target_map": TARGET_MAP,
            "openhear_classes": [key for key in SOUND_PROFILES if key != "silence"],
            "classes_not_tested": list(UNTESTED_CLASSES),
            "classes_not_tested_reason": "ESC-50 has no clips for these classes.",
        },
        "clips": {
            "total": len(clips),
            "targets": sum(1 for clip in clips if clip["category"] in TARGET_MAP),
            "negatives": sum(1 for clip in clips if clip["category"] not in TARGET_MAP),
        },
        "at_shipped_threshold": shipped,
        "threshold_sweep": sweep,
        "report_sha256": None,
    }
    report["report_sha256"] = hash_report(report)
    return report


def _pct(rate: dict) -> str:
    if rate["rate"] is None:
        return "n/a"
    low, high = rate["wilson95"]
    return (
        f"{rate['count']}/{rate['of']} = {rate['rate'] * 100:.1f}% "
        f"(95% CI {low * 100:.1f} to {high * 100:.1f}%)"
    )


def render_markdown(report: dict) -> str:
    """Render the results section for docs/BENCH_RESULTS.md from a report."""
    shipped = report["at_shipped_threshold"]
    prov = report["provenance"]
    lines = [
        f"Shipped threshold: {report['method']['shipped_threshold']:.2f}. "
        f"Clips: {report['clips']['targets']} target, {report['clips']['negatives']} negative.",
        "",
        "### Hit rate by OpenHear class",
        "",
        "| Class | Hit rate | Hits where another pattern also fired | Misses classified as |",
        "|---|---|---|---|",
    ]
    for key, row in shipped["per_class"].items():
        missed = ", ".join(f"{k} {v}" for k, v in row["missed_as"].items()) or "none"
        lines.append(f"| {key} | {_pct(row['hit'])} | {row['hits_with_other_pattern']} | {missed} |")
    lines += [
        f"| **All target clips** | {_pct(shipped['targets_overall'])} | | |",
        "",
        "### Hit rate by ESC-50 category",
        "",
        "| ESC-50 category | OpenHear class | Hit rate |",
        "|---|---|---|",
    ]
    for category, row in shipped["per_esc50_category"].items():
        lines.append(f"| {category} | {TARGET_MAP[category]} | {_pct(row['hit'])} |")
    neg = shipped["negatives"]
    lines += [
        "",
        "### False alerts on sounds with no OpenHear class",
        "",
        f"- Clips where any pattern fired: {_pct(neg['clips_with_false_alert'])}",
        f"- Windows where any pattern fired: {_pct(neg['windows_with_false_alert'])}",
        "- Pattern fired (by clip): "
        + (", ".join(f"{k} {v}" for k, v in neg["by_pattern"].items()) or "none"),
        "",
        "| ESC-50 category | Clips with a false alert |",
        "|---|---|",
    ]
    for category, tally in neg["by_esc50_category"].items():
        if tally["false_alert_clips"]:
            lines.append(f"| {category} | {tally['false_alert_clips']}/{tally['clips']} |")
    lines += [
        "",
        "### Threshold sweep",
        "",
        "| Threshold | Target hit rate | False-alert clip rate |",
        "|---|---|---|",
    ]
    for row in report["threshold_sweep"]:
        mark = " (shipped)" if abs(row["threshold"] - report["method"]["shipped_threshold"]) < 1e-9 else ""
        lines.append(
            f"| {row['threshold']:.2f}{mark} | {row['target_hit_rate'] * 100:.1f}% "
            f"| {row['false_alert_clip_rate'] * 100:.1f}% |"
        )
    lines += [
        "",
        "### Provenance",
        "",
        f"- OpenHear commit: `{prov.get('git_sha')}`",
        f"- Model SHA-256: `{prov.get('model_sha256')}`",
        f"- Model source: {prov.get('model_source')}",
        f"- ESC-50 commit: `{prov.get('esc50_commit')}`",
        f"- Workflow run: {prov.get('run_url')}",
        f"- Report SHA-256: `{report['report_sha256']}`",
        "",
    ]
    return "\n".join(lines)


def load_clips(esc50_dir: Path, classifier, limit: int | None = None) -> list[dict]:
    """Classify ESC-50 clips. Imports soundfile lazily so tests do not need it."""
    import soundfile as sf

    with open(esc50_dir / "meta" / "esc50.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    rows.sort(key=lambda row: row["filename"])
    if limit:
        rows = rows[:limit]
    clips = []
    for index, row in enumerate(rows, start=1):
        samples, sample_rate = sf.read(str(esc50_dir / "audio" / row["filename"]), dtype="float32")
        clips.append(
            {
                "filename": row["filename"],
                "category": row["category"],
                "windows": classify_clip(classifier, samples, sample_rate),
            }
        )
        if index % 200 == 0:
            print(f"classified {index}/{len(rows)} clips", file=sys.stderr)
    return clips


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--esc50", required=True, help="Path to a checkout of karolpiczak/ESC-50")
    parser.add_argument("--model", required=True, help="Path to the YAMNet .tflite model")
    parser.add_argument("--model-source", default="unknown", help="URL the model came from")
    parser.add_argument("--run-url", default="local run", help="CI run URL for provenance")
    parser.add_argument("--out", help="Write the signed JSON report here")
    parser.add_argument("--markdown", help="Write the Markdown results section here")
    parser.add_argument("--limit", type=int, help="Only the first N clips (smoke test)")
    args = parser.parse_args(argv)

    from stream.sound_classifier import YamnetClassifier
    from yamnet_classifier import bundled_labels_path

    esc50_dir = Path(args.esc50)
    classifier = YamnetClassifier(args.model, bundled_labels_path())
    clips = load_clips(esc50_dir, classifier, args.limit)
    provenance = {
        "git_sha": _git(["rev-parse", "HEAD"]),
        "model_sha256": _sha256_file(Path(args.model)),
        "model_source": args.model_source,
        "esc50_commit": _git(["rev-parse", "HEAD"], cwd=esc50_dir),
        "esc50_licence": "CC BY-NC 3.0 (audio not redistributed)",
        "run_url": args.run_url,
        "host": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": np.__version__,
        },
        "limit": args.limit,
    }
    report = build_report(clips, provenance)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    if args.markdown:
        Path(args.markdown).write_text(render_markdown(report), encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
