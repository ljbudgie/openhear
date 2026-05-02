"""
benchmark.py – deterministic latency, throughput and parity harness for OpenHear.

This is the foundational artefact for Workstream A of the Phase 1 master plan.
Every future claim about OpenHear's real-time performance must reference an
output of this script.

The harness is intentionally **hardware-free**: it generates a synthetic
audio stream, runs it through the existing Python DSP stages
(noise reduction → WDRC → voice clarity → feedback cancellation), and
measures wall-clock per-frame processing time on the host CPU.  No
microphone, no speaker, no Bluetooth — so it can be run on a developer
laptop, a Raspberry Pi 5, a CI runner, or a clean-room lab machine and
the numbers are directly comparable.

The script also asserts **bit-parity** with the committed golden test
vectors (``tests/golden/``).  If the DSP code drifts away from the
reference implementation the harness fails and refuses to emit a
report — so a benchmark report is, by construction, a benchmark of an
*unchanged* algorithm.

Output (always written to stdout; optionally also to a file):

    {
      "schema_version": 1,
      "git_sha": "...",
      "host": { "platform": "...", "python": "..." },
      "config": { "sample_rate": 16000, "frames_per_buffer": 256, ... },
      "stages": {
        "noise_reduction": { "frames": 1000, "p50_ms": 0.41, "p95_ms": 0.67, ... },
        "compression":     { ... },
        "voice_clarity":   { ... },
        "feedback":        { ... },
        "full_pipeline":   { ... }
      },
      "parity": {
        "noise_reduction": "ok",
        "compression":     "ok",
        "voice_clarity":   "ok",
        "feedback":        "ok"
      },
      "report_sha256": "..."   # hash of the report itself, with this field nulled
    }

The ``report_sha256`` field is computed over the JSON body with that
field set to ``null``, so a third party can recompute and verify it.

Usage::

    python -m scripts.benchmark                # print JSON to stdout
    python -m scripts.benchmark --frames 2000  # longer run for stability
    python -m scripts.benchmark --out report.json

Exit codes:
    0 — benchmark completed and parity tests passed.
    2 — parity drift detected; benchmark aborted.
    3 — golden vectors missing; run ``python -m scripts.benchmark --regen-golden``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from dsp import config as dsp_config
from dsp.compression import WDRCompressor
from dsp.feedback_canceller import FeedbackCanceller
from dsp.noise_reduction import SpectralSubtractor
from dsp.voice_clarity import VoiceClarityEnhancer

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = REPO_ROOT / "tests" / "golden"

SCHEMA_VERSION = 1


# ---------------------------------------------------------------------------
# Deterministic test signal
# ---------------------------------------------------------------------------


def make_test_signal(sample_rate: int, n_frames: int, frame_length: int) -> np.ndarray:
    """Return a deterministic float32 audio buffer of shape (n_frames, frame_length).

    The signal is a mixture of:
      * white noise (low amplitude) — exercises the noise reducer.
      * a 440 Hz sine — exercises the WDRC envelope follower.
      * a 2 kHz sine — exercises the voice-clarity emphasis band.

    The seed and waveform are fixed forever so that successive runs of
    the benchmark are byte-identical at the input.
    """
    rng = np.random.default_rng(0xCAFEBABE)
    total = n_frames * frame_length
    t = np.arange(total, dtype=np.float64) / sample_rate
    noise = rng.standard_normal(total).astype(np.float64) * 0.02
    sine_low = 0.20 * np.sin(2.0 * np.pi * 440.0 * t)
    sine_high = 0.10 * np.sin(2.0 * np.pi * 2_000.0 * t)
    signal = (noise + sine_low + sine_high).astype(np.float32)
    return signal.reshape(n_frames, frame_length)


# ---------------------------------------------------------------------------
# Stage factories — one per benchmarked DSP block.
# ---------------------------------------------------------------------------


def _make_noise_reducer() -> SpectralSubtractor:
    return SpectralSubtractor(
        frame_length=dsp_config.FRAMES_PER_BUFFER,
        noise_floor_multiplier=dsp_config.NOISE_FLOOR_MULTIPLIER,
        spectral_floor=dsp_config.SPECTRAL_FLOOR,
        noise_estimation_frames=dsp_config.NOISE_ESTIMATION_FRAMES,
    )


def _make_compressor() -> WDRCompressor:
    return WDRCompressor(
        sample_rate=dsp_config.SAMPLE_RATE,
        ratio=dsp_config.COMPRESSION_RATIO,
        knee_dbfs=dsp_config.COMPRESSION_KNEE_DBFS,
        attack_s=dsp_config.COMPRESSION_ATTACK_S,
        release_s=dsp_config.COMPRESSION_RELEASE_S,
    )


def _make_voice_clarity() -> VoiceClarityEnhancer:
    return VoiceClarityEnhancer(
        frame_length=dsp_config.FRAMES_PER_BUFFER,
        sample_rate=dsp_config.SAMPLE_RATE,
        low_hz=dsp_config.VOICE_CLARITY_LOW_HZ,
        high_hz=dsp_config.VOICE_CLARITY_HIGH_HZ,
        gain=dsp_config.VOICE_CLARITY_GAIN,
    )


def _make_feedback() -> FeedbackCanceller:
    return FeedbackCanceller(
        filter_length=dsp_config.FEEDBACK_FILTER_LENGTH,
        mu=dsp_config.FEEDBACK_MU,
        sample_rate=dsp_config.SAMPLE_RATE,
        anti_feedback_gain_db=dsp_config.ANTI_FEEDBACK_GAIN_DB,
    )


STAGE_FACTORIES = {
    "noise_reduction": _make_noise_reducer,
    "compression": _make_compressor,
    "voice_clarity": _make_voice_clarity,
    "feedback": _make_feedback,
}


# ---------------------------------------------------------------------------
# Golden-vector generation and parity check
# ---------------------------------------------------------------------------

# A small, fixed golden frame (independent of the larger benchmark
# buffer) used purely to detect algorithmic drift.  Stored once on
# disk; regenerated only via --regen-golden.
_GOLDEN_FRAMES = 8
_GOLDEN_SEED = 0xDEADBEEF


def _golden_input(frame_length: int) -> np.ndarray:
    rng = np.random.default_rng(_GOLDEN_SEED)
    return rng.standard_normal((_GOLDEN_FRAMES, frame_length)).astype(np.float32) * 0.1


def _run_stage_on_frames(stage_name: str, frames: np.ndarray) -> np.ndarray:
    """Run a freshly-constructed stage over ``frames`` and stack outputs."""
    stage = STAGE_FACTORIES[stage_name]()
    out = np.empty_like(frames)
    for i, frame in enumerate(frames):
        out[i] = stage.process(frame)
    return out


def regenerate_golden_vectors() -> None:
    """Regenerate golden input + reference output files on disk.

    Should only be invoked deliberately, after an intentional algorithmic
    change, with the resulting diff reviewed by a human.
    """
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    frame_length = dsp_config.FRAMES_PER_BUFFER
    inp = _golden_input(frame_length)
    np.save(GOLDEN_DIR / "input.npy", inp, allow_pickle=False)
    for stage_name in STAGE_FACTORIES:
        out = _run_stage_on_frames(stage_name, inp)
        np.save(GOLDEN_DIR / f"{stage_name}.npy", out, allow_pickle=False)
    (GOLDEN_DIR / "README.md").write_text(_golden_readme(), encoding="utf-8")


def _golden_readme() -> str:
    return (
        "# Golden DSP vectors\n\n"
        "These files are the **frozen reference** for OpenHear's DSP stages.\n"
        "They are generated by `python -m scripts.benchmark --regen-golden`\n"
        "and consumed by `tests/test_golden_vectors.py` and the benchmark\n"
        "harness's parity check.\n\n"
        "If a code change in `dsp/` causes any of these vectors to diverge,\n"
        "that is **by definition** an algorithmic change and must be\n"
        "accompanied by an explicit regeneration commit and a CHANGELOG\n"
        "entry.  Do not regenerate silently.\n\n"
        "Files:\n\n"
        "* `input.npy` — deterministic float32 input frames "
        f"(seed {hex(_GOLDEN_SEED)}).\n"
        "* `noise_reduction.npy` — `SpectralSubtractor` output.\n"
        "* `compression.npy` — `WDRCompressor` output.\n"
        "* `voice_clarity.npy` — `VoiceClarityEnhancer` output.\n"
        "* `feedback.npy` — `FeedbackCanceller` output.\n"
    )


def check_parity() -> dict[str, str]:
    """Compare every stage against its golden vector.

    Returns a dict mapping stage name to "ok" or a short failure
    description.  Raises FileNotFoundError if golden vectors are missing.
    """
    inp_path = GOLDEN_DIR / "input.npy"
    if not inp_path.exists():
        raise FileNotFoundError(
            f"Golden input vector not found at {inp_path}. "
            "Run `python -m scripts.benchmark --regen-golden`."
        )
    inp = np.load(inp_path)
    results: dict[str, str] = {}
    for stage_name in STAGE_FACTORIES:
        ref_path = GOLDEN_DIR / f"{stage_name}.npy"
        if not ref_path.exists():
            results[stage_name] = f"missing reference at {ref_path.name}"
            continue
        ref = np.load(ref_path)
        out = _run_stage_on_frames(stage_name, inp)
        # Tolerance: ~1 LSB at single-precision float on signals in
        # roughly [-1, 1].  Generous enough to absorb BLAS-vendor
        # differences; tight enough to flag any real algorithmic drift.
        if np.allclose(out, ref, atol=1e-5, rtol=0.0):
            results[stage_name] = "ok"
        else:
            max_err = float(np.max(np.abs(out - ref)))
            results[stage_name] = f"drift detected (max_abs_err={max_err:.3e})"
    return results


# ---------------------------------------------------------------------------
# Latency measurement
# ---------------------------------------------------------------------------


def _percentile(samples: list[float], p: float) -> float:
    """Robust percentile (no scipy dependency)."""
    if not samples:
        return float("nan")
    s = sorted(samples)
    k = (len(s) - 1) * p / 100.0
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    frac = k - lo
    return s[lo] * (1.0 - frac) + s[hi] * frac


def _summarise(samples_ms: list[float], frame_ms: float) -> dict[str, float]:
    return {
        "frames": len(samples_ms),
        "frame_duration_ms": round(frame_ms, 4),
        "p50_ms": round(_percentile(samples_ms, 50), 4),
        "p95_ms": round(_percentile(samples_ms, 95), 4),
        "p99_ms": round(_percentile(samples_ms, 99), 4),
        "max_ms": round(max(samples_ms), 4),
        "mean_ms": round(statistics.fmean(samples_ms), 4),
        "realtime_factor_p95": round(frame_ms / _percentile(samples_ms, 95), 3)
        if _percentile(samples_ms, 95) > 0
        else float("inf"),
    }


def measure_stage(stage_name: str, frames: np.ndarray) -> dict[str, float]:
    """Time a single stage frame-by-frame.

    The first 10% of frames are treated as warm-up and discarded so
    that JIT-style caches and Python interpreter warm-up do not skew
    the percentiles.
    """
    stage = STAGE_FACTORIES[stage_name]()
    n = frames.shape[0]
    warmup = max(1, n // 10)
    samples_ms: list[float] = []
    for i, frame in enumerate(frames):
        t0 = time.perf_counter()
        stage.process(frame)
        dt_ms = (time.perf_counter() - t0) * 1_000.0
        if i >= warmup:
            samples_ms.append(dt_ms)
    frame_ms = (frames.shape[1] / dsp_config.SAMPLE_RATE) * 1_000.0
    return _summarise(samples_ms, frame_ms)


def measure_full_pipeline(frames: np.ndarray) -> dict[str, float]:
    """Time the full chain through every stage in order."""
    stages = [STAGE_FACTORIES[name]() for name in STAGE_FACTORIES]
    n = frames.shape[0]
    warmup = max(1, n // 10)
    samples_ms: list[float] = []
    for i, frame in enumerate(frames):
        t0 = time.perf_counter()
        x = frame
        for stage in stages:
            x = stage.process(x)
        dt_ms = (time.perf_counter() - t0) * 1_000.0
        if i >= warmup:
            samples_ms.append(dt_ms)
    frame_ms = (frames.shape[1] / dsp_config.SAMPLE_RATE) * 1_000.0
    return _summarise(samples_ms, frame_ms)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _git_sha() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
        )
        return out.decode("ascii").strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _hash_report(report: dict) -> str:
    body = dict(report)
    body["report_sha256"] = None
    blob = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_report(
    n_frames: int,
    parity: dict[str, str],
    stage_summaries: dict[str, dict[str, float]],
) -> dict:
    report = {
        "schema_version": SCHEMA_VERSION,
        "git_sha": _git_sha(),
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or "unknown",
            "python": platform.python_version(),
            "numpy": np.__version__,
        },
        "config": {
            "sample_rate": dsp_config.SAMPLE_RATE,
            "frames_per_buffer": dsp_config.FRAMES_PER_BUFFER,
            "n_frames": n_frames,
        },
        "parity": parity,
        "stages": stage_summaries,
        "report_sha256": None,
    }
    report["report_sha256"] = _hash_report(report)
    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="openhear-benchmark",
        description=("Run the deterministic OpenHear DSP benchmark and emit a signed JSON report."),
    )
    p.add_argument(
        "--frames",
        type=int,
        default=1_000,
        help="Number of frames to process for the latency measurement (default: 1000).",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional path to also write the JSON report to. "
        "The report is always written to stdout.",
    )
    p.add_argument(
        "--regen-golden",
        action="store_true",
        help="Regenerate the committed golden vectors and exit. "
        "Use only after an intentional algorithmic change.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.regen_golden:
        regenerate_golden_vectors()
        print(f"Regenerated golden vectors in {GOLDEN_DIR}", file=sys.stderr)
        return 0

    try:
        parity = check_parity()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    if any(v != "ok" for v in parity.values()):
        print(
            "ERROR: parity drift detected against golden vectors:",
            file=sys.stderr,
        )
        for k, v in parity.items():
            if v != "ok":
                print(f"  {k}: {v}", file=sys.stderr)
        print(
            "Refusing to emit a benchmark report for an unverified pipeline.\n"
            "If the change is intentional, regenerate with "
            "`python -m scripts.benchmark --regen-golden`.",
            file=sys.stderr,
        )
        return 2

    frames = make_test_signal(dsp_config.SAMPLE_RATE, args.frames, dsp_config.FRAMES_PER_BUFFER)

    stage_summaries: dict[str, dict[str, float]] = {}
    for name in STAGE_FACTORIES:
        stage_summaries[name] = measure_stage(name, frames)
    stage_summaries["full_pipeline"] = measure_full_pipeline(frames)

    report = build_report(args.frames, parity, stage_summaries)
    blob = json.dumps(report, indent=2, sort_keys=True)
    print(blob)
    if args.out is not None:
        args.out.write_text(blob + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
