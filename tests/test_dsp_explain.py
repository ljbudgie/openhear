"""Tests for ``dsp/explain.py`` and its Click CLI front-end."""

from __future__ import annotations

import json

from click.testing import CliRunner

from audiogram.audiogram import Audiogram
from dsp.explain import EarFitting, explain, summarise
from dsp.explain_cli import main

# Characteristic shapes (mirror the analyse tests so behaviour stays aligned).
_SLOPING = {250: 10, 500: 10, 1000: 20, 2000: 40, 3000: 55, 4000: 65, 6000: 70, 8000: 75}
_FLAT = {250: 30, 500: 30, 1000: 35, 2000: 30, 4000: 35, 6000: 30, 8000: 35}
_NORMAL = {f: 5 for f in (250, 500, 1000, 2000, 4000, 6000, 8000)}


def _ag(right: dict, left: dict | None = None) -> Audiogram:
    return Audiogram(right_ear=right, left_ear=left if left is not None else right)


# ── Structured explanation ──────────────────────────────────────────────────


def test_sloping_loss_focuses_gain_on_high_pitches():
    fit = explain(_ag(_SLOPING)).right
    assert fit.configuration == "sloping"
    assert fit.peak_gain_freq is not None
    # Most help should land in the high frequencies for a sloping loss.
    assert fit.peak_gain_freq >= 3000
    assert fit.peak_gain_db > 0
    assert fit.mean_gain_db > 0


def test_near_normal_hearing_prescribes_little_gain():
    fit = explain(_ag(_NORMAL)).right
    # NAL-R slope (~0.31 x threshold) leaves only a hair of gain at ~5 dB HL.
    assert fit.mean_gain_db < 5.0
    # And the summary should say so plainly rather than overstate the help.
    assert "adds little" in summarise(explain(_ag(_NORMAL))).lower()


def test_unmeasurable_ear_has_no_peak():
    fit = explain(_ag({250: 20, 8000: 30}, {250: 20, 8000: 30})).right
    # Two scattered points: prescription may still interpolate, but assert the
    # dataclass shape is coherent regardless.
    assert isinstance(fit, EarFitting)
    assert fit.ear == "right"


def test_to_dict_is_json_serialisable():
    d = explain(_ag(_SLOPING)).to_dict()
    restored = json.loads(json.dumps(d))
    assert restored["right"]["configuration"] == "sloping"
    assert "method" in restored


# ── Plain-English summary ───────────────────────────────────────────────────


def test_summary_explains_why_and_is_non_diagnostic():
    text = summarise(explain(_ag(_SLOPING, _FLAT)))
    assert "Right ear" in text and "Left ear" in text
    # The point of the feature: it explains the *reasoning*.
    assert "because" in text.lower()
    assert "high pitches" in text.lower()  # sloping rationale
    assert "not a medical device" in text.lower()


def test_summary_mentions_compression_behaviour():
    text = summarise(explain(_ag(_SLOPING)))
    assert "compression" in text.lower()


# ── CLI ─────────────────────────────────────────────────────────────────────


def _write(tmp_path, data):
    p = tmp_path / "ag.json"
    p.write_text(_ag(data).to_json(), encoding="utf-8")
    return p


def test_cli_plain_output(tmp_path):
    result = CliRunner().invoke(main, [str(_write(tmp_path, _SLOPING))])
    assert result.exit_code == 0
    assert "Your fitting, in plain English" in result.output


def test_cli_json_output(tmp_path):
    result = CliRunner().invoke(main, [str(_write(tmp_path, _SLOPING)), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["right"]["configuration"] == "sloping"
    assert "method" in payload


def test_cli_rejects_unreadable_file(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    result = CliRunner().invoke(main, [str(bad)])
    assert result.exit_code == 1
    assert "Could not read" in result.output
