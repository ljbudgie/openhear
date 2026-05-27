"""Tests for the Phase 5 sovereign-device bundle pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hardware.sovereign_device.pipeline import (
    COMPONENT_DATABASE_SCHEMA,
    DEFAULT_COST_TARGET_GBP,
    MANIFEST_SCHEMA,
    estimate_binaural_cost,
    generate_phase5_device_bundle,
    list_components,
    load_component_database,
    main,
)


def test_component_database_is_sovereign_and_under_target():
    data = load_component_database()
    components = list_components()
    roles = {component.role for component in components}

    assert data["schema_version"] == COMPONENT_DATABASE_SCHEMA
    assert estimate_binaural_cost() <= DEFAULT_COST_TARGET_GBP
    assert {"shell", "receiver", "microphone", "processor", "power", "safety_limiter"} <= roles
    assert all(component.is_sovereign for component in components)
    assert all(component.supplier_count > 0 for component in components)


def test_component_database_rejects_proprietary_dependency(tmp_path: Path):
    path = tmp_path / "components.json"
    data = load_component_database()
    data["components"][0]["proprietary"] = True
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="proprietary"):
        load_component_database(path)


def test_generate_phase5_bundle_writes_firmware_and_manifest(audiogram_path: str, tmp_path: Path):
    manifest = generate_phase5_device_bundle(audiogram_path, tmp_path)
    manifest_path = tmp_path / "manifest.json"
    firmware_path = tmp_path / manifest.firmware_file

    assert manifest.schema_version == MANIFEST_SCHEMA
    assert manifest.mode == "binaural"
    assert manifest.ear is None
    assert manifest.cost_target_met is True
    assert firmware_path.exists()
    assert manifest_path.exists()
    assert "{{" not in firmware_path.read_text(encoding="utf-8")

    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert saved["audiogram_sha256"] == manifest.audiogram_sha256
    assert "right_ear" not in json.dumps(saved)
    assert "left_ear" not in json.dumps(saved)
    assert "Passive hardware MPO limiter" in " ".join(saved["safety_requirements"])
    assert "No cloud service" in " ".join(saved["sovereignty_guarantees"])


def test_generate_single_ear_bundle_records_ear(audiogram_path: str, tmp_path: Path):
    manifest = generate_phase5_device_bundle(
        audiogram_path,
        tmp_path,
        ear="left",
        binaural=False,
    )

    assert manifest.mode == "single-ear"
    assert manifest.ear == "left"
    assert manifest.firmware_file == "openhear_phase5_left.ino"


def test_generate_phase5_bundle_rejects_unknown_ear(audiogram_path: str, tmp_path: Path):
    with pytest.raises(ValueError, match="ear must be"):
        generate_phase5_device_bundle(audiogram_path, tmp_path, ear="both", binaural=False)


def test_phase5_cli_generates_bundle(monkeypatch, audiogram_path: str, tmp_path: Path, capsys):
    monkeypatch.setattr(
        "sys.argv",
        ["phase5", audiogram_path, str(tmp_path), "--single-ear", "--ear", "right"],
    )

    main()

    captured = capsys.readouterr()
    assert "Phase 5 bundle written" in captured.out
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "openhear_phase5_right.ino").exists()
