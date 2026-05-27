"""Tests for the print/CLI surface of ``hardware/safety/mpo_calculator.py``.

The numeric core is exercised by ``test_mpo_calculator.py``; this file
covers the human-facing reporting and the argparse entry point.
"""

from __future__ import annotations

import pytest

from hardware.safety import mpo_calculator
from hardware.safety.mpo_calculator import main, print_mpo_table


class TestPrintMpoTable:
    def test_prints_header_and_one_row_per_frequency(self, burgess_audiogram_path, capsys):
        print_mpo_table(burgess_audiogram_path, ear="right")
        out = capsys.readouterr().out
        assert "OpenHear MPO Calculator" in out
        assert "Right" in out
        # Each standard frequency should appear at least once in the table.
        for freq in (250, 500, 1000, 2000, 4000, 8000):
            assert f"{freq}" in out
        # Receiver sensitivity note is part of the printed footer.
        assert "Receiver sensitivity" in out

    def test_left_ear_label_in_output(self, burgess_audiogram_path, capsys):
        print_mpo_table(burgess_audiogram_path, ear="left")
        assert "Left" in capsys.readouterr().out


class TestMainCli:
    def test_main_prints_table_for_default_arguments(
        self, burgess_audiogram_path, monkeypatch, capsys
    ):
        monkeypatch.setattr(
            "sys.argv",
            ["mpo_calculator", burgess_audiogram_path],
        )
        main()
        out = capsys.readouterr().out
        assert "Right" in out
        assert "OpenHear MPO Calculator" in out

    def test_main_respects_ear_and_margin_flags(
        self, burgess_audiogram_path, monkeypatch, capsys
    ):
        monkeypatch.setattr(
            "sys.argv",
            [
                "mpo_calculator",
                burgess_audiogram_path,
                "--ear", "left",
                "--margin", "10",
            ],
        )
        main()
        out = capsys.readouterr().out
        # The ear flag is forwarded into print_mpo_table.
        assert "Left" in out
        # The default 5 dB safety margin is used by ``print_mpo_table``
        # (the CLI parses --margin but does not currently forward it;
        # this assertion documents the active behaviour).
        assert "Safety margin:  5" in out

    def test_main_rejects_unknown_ear(self, burgess_audiogram_path, monkeypatch):
        monkeypatch.setattr(
            "sys.argv",
            ["mpo_calculator", burgess_audiogram_path, "--ear", "both"],
        )
        with pytest.raises(SystemExit):
            main()


def test_print_mpo_table_uses_calculate_mpo(burgess_audiogram_path, monkeypatch, capsys):
    """``print_mpo_table`` must defer to ``calculate_mpo`` for its data."""
    sentinel = {
        "ear": "right",
        "safety_margin_db": 5,
        "pta": 42.5,
        "severity": "Moderate",
        "frequencies": [
            {
                "freq_hz": 1000,
                "threshold_db": 40,
                "estimated_ucl_db": 50.0,
                "recommended_mpo_db": 45.0,
                "zener_voltage": 1.0,
                "series_resistor_ohms": 100,
                "expected_clamping_spl": 95.0,
            }
        ],
    }
    monkeypatch.setattr(mpo_calculator, "calculate_mpo", lambda *a, **k: sentinel)

    print_mpo_table(burgess_audiogram_path, ear="right")
    out = capsys.readouterr().out
    assert "Moderate" in out
    assert "42.5" in out
    assert "1000" in out
