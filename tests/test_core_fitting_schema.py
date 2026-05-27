"""Tests for ``core/fitting_schema.py``."""

from __future__ import annotations

from core.fitting_schema import (
    CompressionChannel,
    GainTable,
    PhonakFittingProfile,
    SigniaFittingProfile,
    phonak_profile_from_dict,
    signia_profile_from_dict,
)


class TestGainTable:
    def test_defaults(self):
        gt = GainTable()
        assert gt.frequencies_hz == [250, 500, 1000, 1500, 2000, 3000, 4000, 6000, 8000]
        assert gt.gains_db == [0.0] * 9

    def test_custom_values(self):
        gt = GainTable(frequencies_hz=[500, 1000], gains_db=[5.0, 10.0])
        assert gt.gains_db == [5.0, 10.0]

    def test_independent_instances(self):
        a, b = GainTable(), GainTable()
        a.gains_db.append(1.0)
        assert 1.0 not in b.gains_db


class TestCompressionChannel:
    def test_defaults(self):
        ch = CompressionChannel()
        assert ch.center_frequency_hz == 1000
        assert ch.compression_ratio == 2.0
        assert ch.knee_point_db == 50.0
        assert ch.attack_ms == 5.0
        assert ch.release_ms == 50.0
        assert ch.max_output_db == 110.0


class TestPhonakProfile:
    def test_defaults(self):
        p = PhonakFittingProfile()
        assert p.program_name == "AutoSense OS 4.0"
        assert p.noise_reduction_active is True
        assert p.bluetooth_enabled is True
        assert len(p.compression_channels) == 5

    def test_from_dict_full(self):
        data = {
            "device_serial": "SN1234",
            "program_name": "Speech in Noise",
            "treble_boost_db": 3.5,
            "noise_reduction_active": False,
            "directional_mode": "omni",
            "bluetooth_enabled": False,
            "gain_table": {
                "frequencies_hz": [500, 1000, 2000],
                "gains_db": [10.0, 15.0, 20.0],
            },
            "compression_channels": [
                {"center_frequency_hz": 500, "compression_ratio": 1.8},
                {"center_frequency_hz": 2000, "compression_ratio": 2.5},
            ],
        }
        p = phonak_profile_from_dict(data)
        assert p.device_serial == "SN1234"
        assert p.program_name == "Speech in Noise"
        assert p.treble_boost_db == 3.5
        assert p.noise_reduction_active is False
        assert p.bluetooth_enabled is False
        assert p.directional_mode == "omni"
        assert p.gain_table.frequencies_hz == [500, 1000, 2000]
        assert p.gain_table.gains_db == [10.0, 15.0, 20.0]
        assert len(p.compression_channels) == 2
        assert p.compression_channels[0].compression_ratio == 1.8

    def test_from_dict_empty_uses_defaults(self):
        p = phonak_profile_from_dict({})
        assert p.device_serial == ""
        assert p.program_name == "AutoSense OS 4.0"
        assert p.noise_reduction_active is True

    def test_from_dict_ignores_unknown_keys(self):
        p = phonak_profile_from_dict({"unknown_field": "ignore_me",
                                      "device_serial": "SN1"})
        assert p.device_serial == "SN1"

    def test_from_dict_partial_gain_table(self):
        # Only frequencies_hz provided; gains_db falls back to default.
        p = phonak_profile_from_dict({"gain_table": {"frequencies_hz": [500]}})
        assert p.gain_table.frequencies_hz == [500]
        assert p.gain_table.gains_db == [0.0] * 9


class TestSigniaProfile:
    def test_defaults(self):
        s = SigniaFittingProfile()
        assert s.program_name == "Universal"
        assert s.own_voice_processing is True
        assert s.noise_reduction_level == 2
        assert s.vent_type == "closed"

    def test_from_dict_full(self):
        data = {
            "device_serial": "AX-99",
            "program_name": "TV",
            "own_voice_processing": False,
            "noise_reduction_level": 3,
            "directional_mode": "super-narrow",
            "mfi_bluetooth_enabled": False,
            "vent_type": "open",
            "gain_table": {
                "frequencies_hz": [1000, 2000],
                "gains_db": [12.0, 18.0],
            },
            "compression_channels": [
                {"center_frequency_hz": 1000},
            ],
        }
        s = signia_profile_from_dict(data)
        assert s.device_serial == "AX-99"
        assert s.own_voice_processing is False
        assert s.noise_reduction_level == 3
        assert s.vent_type == "open"
        assert s.gain_table.gains_db == [12.0, 18.0]
        assert len(s.compression_channels) == 1

    def test_from_dict_empty_uses_defaults(self):
        s = signia_profile_from_dict({})
        assert s.program_name == "Universal"
        assert s.vent_type == "closed"
        assert s.mfi_bluetooth_enabled is True

    def test_noise_reduction_level_coerces_int(self):
        s = signia_profile_from_dict({"noise_reduction_level": "2"})
        assert s.noise_reduction_level == 2
        assert isinstance(s.noise_reduction_level, int)
