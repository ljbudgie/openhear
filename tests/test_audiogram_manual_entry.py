"""Tests for the manual-entry CLI in :mod:`audiogram.manual_entry`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from audiogram.manual_entry import collect_audiogram, main


def _ten_thresholds(start: int) -> list[str]:
    """Ten dB-HL strings for one ear at the standard frequencies."""
    return [str(start + 5 * i) for i in range(10)]


def test_collect_audiogram_with_full_answer_set():
    answers = _ten_thresholds(30) + _ten_thresholds(35)  # right then left
    ag = collect_audiogram(
        subject="anon",
        date_measured="2024-11-15",
        answers=answers,
    )
    # Right ear was the first ten answers (30, 35, 40, ..., 75).
    assert ag.right_ear[250] == 30.0
    assert ag.right_ear[8000] == 75.0
    # Left ear came after.
    assert ag.left_ear[250] == 35.0
    assert ag.left_ear[8000] == 80.0
    assert ag.source == "manual_entry"
    assert ag.subject == "anon"
    assert ag.date_measured == "2024-11-15"


def test_collect_audiogram_skips_blank_answers():
    answers = ["skip"] * 20  # all skipped
    ag = collect_audiogram(answers=answers)
    assert ag.right_ear == {}
    assert ag.left_ear == {}


def test_collect_audiogram_rejects_out_of_range_value():
    answers = ["999"]  # very first prompt
    with pytest.raises(Exception):  # click.BadParameter or ValueError
        collect_audiogram(answers=answers)


def test_cli_writes_json_file(tmp_path: Path):
    runner = CliRunner()
    out = tmp_path / "ag.json"
    # Provide 20 frequency answers via stdin (right ear, then left).
    answers = "\n".join(_ten_thresholds(30) + _ten_thresholds(35)) + "\n"
    result = runner.invoke(
        main,
        ["--output", str(out), "--subject", "anon",
         "--date", "2024-11-15"],
        input=answers,
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["format_version"] == "openhear-audiogram-v1"
    assert data["source"] == "manual_entry"
    right_thresholds = {
        e["freq_hz"]: e["db_hl"] for e in data["right_ear"]["thresholds"]
    }
    assert right_thresholds[250] == 30
    assert right_thresholds[8000] == 75


def test_cli_refuses_to_overwrite_without_force(tmp_path: Path):
    out = tmp_path / "ag.json"
    out.write_text("{}")
    runner = CliRunner()
    result = runner.invoke(main, ["--output", str(out)])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_cli_overwrites_with_force(tmp_path: Path):
    out = tmp_path / "ag.json"
    out.write_text("{}")
    runner = CliRunner()
    answers = "\n".join(["skip"] * 20) + "\n"
    result = runner.invoke(
        main,
        ["--output", str(out), "--force"],
        input=answers,
    )
    assert result.exit_code == 0, result.output
    data = json.loads(out.read_text())
    assert data["right_ear"]["thresholds"] == []
