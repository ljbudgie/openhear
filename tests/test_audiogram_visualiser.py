"""Tests for ``audiogram/visualiser.py``."""

from __future__ import annotations

from audiogram.visualiser import _db_to_row, _freq_to_col, _severity_colour, print_audiogram


class TestDbToRow:
    def test_zero_db_is_top(self):
        assert _db_to_row(0) == 0

    def test_max_is_bottom(self):
        # _CHART_HEIGHT = 24 → last row = 23.
        assert _db_to_row(120) == 23

    def test_clamping(self):
        assert _db_to_row(-50) == 0
        assert _db_to_row(200) == 23


class TestFreqToCol:
    def test_low_freq_is_left(self):
        assert _freq_to_col(125) == 0

    def test_high_freq_is_right(self):
        # _CHART_WIDTH = 72 → last col = 71.
        assert _freq_to_col(8000) == 71

    def test_frequency_out_of_range_clamps(self):
        assert _freq_to_col(50) == 0
        assert _freq_to_col(20_000) == 71


class TestSeverityColour:
    def test_normal_green(self):
        assert "92" in _severity_colour("Normal")

    def test_mild_yellow(self):
        assert "93" in _severity_colour("Mild")

    def test_severe_red(self):
        assert "91" in _severity_colour("Severe")


class TestPrintAudiogram:
    def test_smoke(self, burgess_audiogram_path, capsys):
        # Just check the function runs end-to-end without raising.
        print_audiogram(burgess_audiogram_path)
        captured = capsys.readouterr()
        assert "Lewis Burgess" in captured.out
        assert "Right Ear" in captured.out
        assert "Left Ear" in captured.out
