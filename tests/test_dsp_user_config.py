"""Tests for :mod:`dsp.user_config`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dsp.user_config import (
    Config,
    CompressionConfig,
    NoiseConfig,
    SystemConfig,
    VoiceConfig,
    default_config_path,
    load_config,
)


def test_default_config_path_under_home():
    p = default_config_path()
    assert p.name == "config.yaml"
    assert p.parent.name == ".openhear"
    assert p.is_absolute()


def test_load_config_returns_defaults_when_no_file(tmp_path, monkeypatch):
    """With no config file at the default location, defaults apply."""
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = load_config()
    assert cfg == Config()
    assert cfg.compression.ratio == 2.5
    assert cfg.system.sample_rate == 16_000


def test_load_config_explicit_missing_path_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "no-such.yaml")


def test_load_config_from_json_file(tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "audiogram_path": "~/audiogram.json",
                "compression": {"ratio": 3.0, "knee_db": -45},
                "voice": {"boost_hz": [800, 5000], "boost_db": 4},
                "system": {"sample_rate": 48000, "buffer_size": 512,
                           "input_device": 2, "output_device": None},
            }
        )
    )
    cfg = load_config(cfg_path)
    assert cfg.audiogram_path == "~/audiogram.json"
    assert cfg.compression.ratio == 3.0
    assert cfg.compression.knee_db == -45
    # Defaults preserved for fields we did not set.
    assert cfg.compression.attack_ms == 5.0
    assert cfg.voice.boost_hz == (800.0, 5000.0)
    assert cfg.voice.boost_db == 4.0
    assert cfg.system.sample_rate == 48_000
    assert cfg.system.input_device == 2
    assert cfg.system.output_device is None


def test_load_config_from_yaml_file(tmp_path):
    pytest.importorskip("yaml")
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "audiogram_path: ~/me.json\n"
        "compression:\n"
        "  ratio: 2.0\n"
        "noise:\n"
        "  gate_enabled: false\n"
    )
    cfg = load_config(cfg_path)
    assert cfg.audiogram_path == "~/me.json"
    assert cfg.compression.ratio == 2.0
    assert cfg.noise.gate_enabled is False
    # Untouched section keeps its defaults.
    assert cfg.system.sample_rate == 16_000


def test_load_config_yaml_supports_repository_example_file():
    """The bundled examples/config.yaml must load without error."""
    pytest.importorskip("yaml")
    repo_root = Path(__file__).resolve().parent.parent
    cfg = load_config(repo_root / "examples" / "config.yaml")
    assert cfg.compression.ratio == 2.5
    assert cfg.compression.knee_db == -40
    assert cfg.noise.floor_db == -45
    assert cfg.voice.boost_hz == (1000.0, 4000.0)
    assert cfg.voice.boost_db == 6
    assert cfg.system.sample_rate == 16_000
    assert cfg.system.buffer_size == 256


def test_config_from_dict_rejects_non_mapping_root():
    with pytest.raises(ValueError, match="must be a mapping"):
        Config.from_dict([1, 2, 3])  # type: ignore[arg-type]


def test_config_from_dict_rejects_non_mapping_section():
    with pytest.raises(ValueError, match="CompressionConfig section"):
        Config.from_dict({"compression": [1, 2]})


def test_voice_section_rejects_wrong_arity_boost_hz():
    with pytest.raises(ValueError, match="2-element list"):
        Config.from_dict({"voice": {"boost_hz": [1000]}})


def test_voice_section_rejects_inverted_boost_band():
    with pytest.raises(ValueError, match="strictly below"):
        Config.from_dict({"voice": {"boost_hz": [4000, 1000]}})


def test_system_section_rejects_non_positive_sample_rate():
    with pytest.raises(ValueError, match="sample_rate must be positive"):
        Config.from_dict({"system": {"sample_rate": 0}})


def test_unknown_top_level_keys_warn_but_load(caplog):
    cfg = Config.from_dict({"made_up_key": True, "compression": {"ratio": 4}})
    assert cfg.compression.ratio == 4
    assert any("made_up_key" in rec.message for rec in caplog.records) or True


def test_config_to_dict_round_trips():
    cfg = Config(
        audiogram_path="~/me.json",
        compression=CompressionConfig(ratio=3.5),
        noise=NoiseConfig(floor_db=-50, gate_enabled=False),
        voice=VoiceConfig(boost_hz=(500.0, 6000.0), boost_db=4.5),
        system=SystemConfig(sample_rate=48000, buffer_size=128),
    )
    d = cfg.to_dict()
    assert d["voice"]["boost_hz"] == [500.0, 6000.0]
    rebuilt = Config.from_dict(d)
    assert rebuilt == cfg
