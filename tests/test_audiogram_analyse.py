"""Tests for ``audiogram/analyse.py`` and its Click CLI front-end."""

from __future__ import annotations

import json

from click.testing import CliRunner

from audiogram.analyse import analyse, summarise
from audiogram.analyse_cli import main
from audiogram.audiogram import Audiogram

# ── Fixtures: characteristic audiogram shapes ───────────────────────────────

# Standard frequencies used throughout: 250, 500, 1000, 2000, 3000, 4000, 6000, 8000.

_FLAT = {250: 30, 500: 30, 1000: 35, 2000: 30, 4000: 35, 6000: 30, 8000: 35}
_SLOPING = {250: 10, 500: 10, 1000: 20, 2000: 40, 3000: 55, 4000: 65, 6000: 70, 8000: 75}
_REVERSE = {250: 65, 500: 60, 1000: 45, 2000: 30, 4000: 15, 6000: 15, 8000: 10}
# Notch: quiet 1-2 kHz, dip at 4 kHz, recovery at 8 kHz.
_NOTCHED = {250: 10, 500: 10, 1000: 10, 2000: 15, 3000: 35, 4000: 45, 6000: 30, 8000: 15}
# Cookie-bite: good low and high, worse mid.
_COOKIE = {250: 15, 500: 15, 1000: 45, 2000: 50, 4000: 20, 6000: 15, 8000: 15}


def _ag(right: dict, left: dict | None = None) -> Audiogram:
    return Audiogram(right_ear=right, left_ear=left if left is not None else right)


# ── Configuration classification ────────────────────────────────────────────


def test_flat_configuration():
    assert analyse(_ag(_FLAT)).right.configuration == "flat"


def test_sloping_configuration():
    assert analyse(_ag(_SLOPING)).right.configuration == "sloping"


def test_reverse_sloping_configuration():
    assert analyse(_ag(_REVERSE)).right.configuration == "reverse-sloping"


def test_notched_configuration():
    assert analyse(_ag(_NOTCHED)).right.configuration == "notched"


def test_cookie_bite_configuration():
    assert analyse(_ag(_COOKIE)).right.configuration == "cookie-bite"


def test_indeterminate_when_too_few_frequencies():
    a = analyse(_ag({500: 30, 4000: 40}))
    assert a.right.configuration == "indeterminate"


def test_indeterminate_when_region_missing():
    # Three points but no high-frequency region — cannot judge slope.
    a = analyse(_ag({250: 20, 500: 25, 1000: 30}))
    assert a.right.configuration == "indeterminate"


# ── PTA / severity ──────────────────────────────────────────────────────────


def test_pta_and_severity_populated():
    a = analyse(_ag(_SLOPING)).right
    # PTA = mean(500,1000,2000,4000) = mean(10,20,40,65) = 33.75
    assert a.pta == 33.8
    assert a.severity == "mild"


def test_pta_none_when_frequencies_missing():
    a = analyse(_ag({250: 20, 8000: 30})).right
    assert a.pta is None
    assert a.severity == "unknown"
    assert a.measured_frequencies == 2


# ── Asymmetry + flags ───────────────────────────────────────────────────────


def test_symmetric_has_no_asymmetry_flag():
    a = analyse(_ag(_FLAT, _FLAT))
    assert a.asymmetry_db == 0.0
    assert not any("differ by" in f for f in a.flags)


def test_asymmetric_ears_flagged():
    worse_left = {f: v + 30 for f, v in _FLAT.items()}
    a = analyse(_ag(_FLAT, worse_left))
    assert a.asymmetry_db == 30.0
    assert any("differ by" in f for f in a.flags)


def test_asymmetry_none_when_pta_unavailable():
    a = analyse(_ag(_FLAT, {250: 20, 8000: 30}))
    assert a.asymmetry_db is None


def test_notch_raises_noise_flag():
    a = analyse(_ag(_NOTCHED, _NOTCHED))
    assert any("noise" in f.lower() for f in a.flags)


def test_profound_loss_flags_output_safety():
    profound = {f: 95 for f in (250, 500, 1000, 2000, 4000, 6000, 8000)}
    a = analyse(_ag(profound, profound))
    assert any("profound" in f.lower() and "MPO" in f for f in a.flags)


# ── Plain-English summary ───────────────────────────────────────────────────


def test_summary_is_non_diagnostic_and_mentions_both_ears():
    text = summarise(analyse(_ag(_SLOPING, _FLAT)))
    assert "Right ear" in text and "Left ear" in text
    assert "not a diagnosis" in text.lower()
    assert "not a medical device" in text.lower()


def test_summary_handles_unmeasurable_ear():
    text = summarise(analyse(_ag({250: 20, 8000: 30})))
    assert "not enough" in text.lower()


# ── to_dict round-trips through JSON ────────────────────────────────────────


def test_to_dict_is_json_serialisable():
    d = analyse(_ag(_SLOPING)).to_dict()
    restored = json.loads(json.dumps(d))
    assert restored["right"]["configuration"] == "sloping"
    assert "flags" in restored


# ── CLI ─────────────────────────────────────────────────────────────────────


def _write(tmp_path, data):
    p = tmp_path / "ag.json"
    p.write_text(_ag(data).to_json(), encoding="utf-8")
    return p


def test_cli_plain_output(tmp_path):
    result = CliRunner().invoke(main, [str(_write(tmp_path, _SLOPING))])
    assert result.exit_code == 0
    assert "plain English" in result.output


def test_cli_json_output(tmp_path):
    result = CliRunner().invoke(main, [str(_write(tmp_path, _SLOPING)), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["right"]["configuration"] == "sloping"


def test_cli_rejects_unreadable_file(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    result = CliRunner().invoke(main, [str(bad)])
    assert result.exit_code == 1
    assert "Could not read" in result.output
