"""Tests for ``hardware/safety/mpo_calculator.py``."""

from __future__ import annotations

import pytest

from hardware.safety.mpo_calculator import (
    _ABSOLUTE_MAX_MPO_DB,
    _MINIMUM_MPO_DB,
    _SERIES_RESISTOR_OHMS,
    _nearest_standard_zener,
    calculate_mpo,
)


class TestNearestStandardZener:
    def test_rounds_down(self):
        # Target between 5.1 and 5.6 should round down to 5.1 for safety.
        assert _nearest_standard_zener(5.4) == 5.1

    def test_exact_match(self):
        assert _nearest_standard_zener(5.1) == 5.1

    def test_too_low_returns_lowest_available(self):
        assert _nearest_standard_zener(0.01) == 0.47

    def test_above_highest_returns_highest(self):
        assert _nearest_standard_zener(1000.0) == 36.0


class TestCalculateMpo:
    def test_returns_expected_keys(self, burgess_audiogram_path):
        result = calculate_mpo(burgess_audiogram_path, ear="right")
        assert set(result.keys()) == {
            "ear", "safety_margin_db", "pta", "severity", "frequencies",
        }

    def test_per_frequency_keys(self, burgess_audiogram_path):
        result = calculate_mpo(burgess_audiogram_path, ear="right")
        assert len(result["frequencies"]) > 0
        freq_entry = result["frequencies"][0]
        expected_keys = {
            "freq_hz", "threshold_db", "estimated_ucl_db",
            "recommended_mpo_db", "zener_voltage",
            "series_resistor_ohms", "expected_clamping_spl",
        }
        assert set(freq_entry.keys()) == expected_keys

    def test_mpo_within_bounds(self, burgess_audiogram_path):
        result = calculate_mpo(burgess_audiogram_path, ear="right")
        for entry in result["frequencies"]:
            assert entry["recommended_mpo_db"] >= _MINIMUM_MPO_DB
            assert entry["recommended_mpo_db"] <= _ABSOLUTE_MAX_MPO_DB

    def test_series_resistor_constant(self, burgess_audiogram_path):
        result = calculate_mpo(burgess_audiogram_path, ear="right")
        for entry in result["frequencies"]:
            assert entry["series_resistor_ohms"] == _SERIES_RESISTOR_OHMS

    def test_ear_parameter_switches(self, burgess_audiogram_path):
        right = calculate_mpo(burgess_audiogram_path, ear="right")
        left = calculate_mpo(burgess_audiogram_path, ear="left")
        assert right["ear"] == "right"
        assert left["ear"] == "left"

    def test_safety_margin_applied(self, burgess_audiogram_path):
        base = calculate_mpo(burgess_audiogram_path, ear="right", safety_margin_db=5)
        tight = calculate_mpo(burgess_audiogram_path, ear="right", safety_margin_db=20)
        # A higher safety margin should produce equal or lower MPO values
        # (never negative because of the minimum floor).
        for b, t in zip(base["frequencies"], tight["frequencies"]):
            assert t["recommended_mpo_db"] <= b["recommended_mpo_db"]

    def test_zener_voltages_are_standard(self, burgess_audiogram_path):
        result = calculate_mpo(burgess_audiogram_path, ear="right")
        for entry in result["frequencies"]:
            assert entry["zener_voltage"] == _nearest_standard_zener(
                entry["zener_voltage"] + 1e-9
            )
