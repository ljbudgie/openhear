"""Tests for ``audiogram/compare.py`` (Click CLI front-end)."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from audiogram.compare import _format_diff_line, main


def _write_audiogram(path: Path, *, right_offset: int = 0, left_offset: int = 0) -> None:
    payload = {
        "subject": "T",
        "source": "Test",
        "date": "2024-01-01",
        "format_version": "openhear-audiogram-v1",
        "right_ear": {
            "symbol": "O",
            "thresholds": [
                {"freq_hz": 500, "db_hl": 20 + right_offset},
                {"freq_hz": 1000, "db_hl": 30 + right_offset},
                {"freq_hz": 2000, "db_hl": 40 + right_offset},
                {"freq_hz": 4000, "db_hl": 50 + right_offset},
            ],
        },
        "left_ear": {
            "symbol": "X",
            "thresholds": [
                {"freq_hz": 500, "db_hl": 25 + left_offset},
                {"freq_hz": 1000, "db_hl": 35 + left_offset},
                {"freq_hz": 2000, "db_hl": 45 + left_offset},
                {"freq_hz": 4000, "db_hl": 55 + left_offset},
            ],
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class TestFormatDiffLine:
    def test_worse_diff_marked_red_with_suffix(self):
        line = _format_diff_line(1000, 5)
        assert "1000 Hz" in line
        assert "+" in line and "5" in line
        assert "(worse)" in line

    def test_better_diff_marked_green_with_suffix(self):
        line = _format_diff_line(1000, -5)
        assert "-5" in line
        assert "(better)" in line

    def test_zero_diff_no_suffix(self):
        line = _format_diff_line(1000, 0)
        assert "1000 Hz" in line
        assert "(worse)" not in line
        assert "(better)" not in line


class TestCompareCli:
    def test_human_readable_output(self, tmp_path: Path):
        old = tmp_path / "old.json"
        new = tmp_path / "new.json"
        _write_audiogram(old)
        _write_audiogram(new, right_offset=10, left_offset=-5)

        runner = CliRunner()
        result = runner.invoke(main, [str(old), str(new)])
        assert result.exit_code == 0, result.output
        # Header
        assert "Comparing:" in result.output
        # Section headings for both ears
        assert "Right ear" in result.output
        assert "Left ear" in result.output
        # PTA delta lines (positive for right, negative for left)
        assert "PTA delta:" in result.output

    def test_json_output(self, tmp_path: Path):
        old = tmp_path / "old.json"
        new = tmp_path / "new.json"
        _write_audiogram(old)
        _write_audiogram(new, right_offset=10)

        runner = CliRunner()
        result = runner.invoke(main, [str(old), str(new), "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "right" in data and "left" in data
        # All right-ear deltas should be +10
        for _freq, diff in data["right"]:
            assert diff == 10
        assert data["right_pta_diff"] == 10.0
        assert data["left_pta_diff"] == 0.0

    def test_handles_no_overlapping_frequencies(self, tmp_path: Path):
        # Build two audiograms with disjoint frequency sets.
        old = tmp_path / "old.json"
        new = tmp_path / "new.json"
        common = {
            "subject": "T",
            "source": "Test",
            "date": "2024-01-01",
            "format_version": "openhear-audiogram-v1",
        }
        old.write_text(
            json.dumps(
                {
                    **common,
                    "right_ear": {"symbol": "O", "thresholds": [{"freq_hz": 250, "db_hl": 10}]},
                    "left_ear": {"symbol": "X", "thresholds": [{"freq_hz": 250, "db_hl": 15}]},
                }
            ),
            encoding="utf-8",
        )
        new.write_text(
            json.dumps(
                {
                    **common,
                    "right_ear": {"symbol": "O", "thresholds": [{"freq_hz": 8000, "db_hl": 50}]},
                    "left_ear": {"symbol": "X", "thresholds": [{"freq_hz": 8000, "db_hl": 55}]},
                }
            ),
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(main, [str(old), str(new)])
        assert result.exit_code == 0, result.output
        assert "(no overlapping frequencies)" in result.output
        assert "insufficient data" in result.output

    def test_missing_old_file_errors(self, tmp_path: Path):
        new = tmp_path / "new.json"
        _write_audiogram(new)
        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_path / "missing.json"), str(new)])
        assert result.exit_code != 0
