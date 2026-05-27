"""Minimal sanity checks for the Phase 5 pyproject.toml.

The build is exercised in CI (`pip install -e .`); here we confirm the
file parses and its declared metadata is consistent so regressions like
a missing entry-point or mistyped classifier are caught even without
a Python build backend installed.
"""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib as toml_lib
else:  # pragma: no cover - only reached on 3.10
    import tomli as toml_lib  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"


def _load() -> dict:
    with open(PYPROJECT, "rb") as fh:
        return toml_lib.load(fh)


def test_pyproject_exists():
    assert PYPROJECT.exists(), (
        "pyproject.toml must exist to enable `pip install -e .`"
    )


def test_project_metadata_is_complete():
    data = _load()
    project = data["project"]
    assert project["name"] == "openhear"
    assert project["version"]
    assert project["description"]
    assert project["requires-python"].startswith(">=3.10")


def test_core_dependencies_declared():
    data = _load()
    deps = " ".join(data["project"]["dependencies"]).lower()
    for required in ("numpy", "scipy", "hid", "pyyaml"):
        assert required in deps, f"{required!r} missing from dependencies"


def test_pyaudio_is_optional_extra():
    """PyAudio needs native portaudio — it must not be a hard dep,
    otherwise CI and plain `pip install` break on clean machines."""
    data = _load()
    deps = " ".join(data["project"]["dependencies"]).lower()
    assert "pyaudio" not in deps
    assert "audio" in data["project"]["optional-dependencies"]
    audio_extra = " ".join(data["project"]["optional-dependencies"]["audio"]).lower()
    assert "pyaudio" in audio_extra


def test_console_scripts_target_real_modules():
    """Every console_scripts target must resolve to an existing module."""
    data = _load()
    scripts = data["project"]["scripts"]
    for name, target in scripts.items():
        module_path, _, attr = target.partition(":")
        module_file = ROOT / Path(*module_path.split(".")).with_suffix(".py")
        assert module_file.exists(), (
            f"Script {name!r} points at {target!r} but "
            f"{module_file.relative_to(ROOT)} does not exist."
        )
        text = module_file.read_text(encoding="utf-8")
        assert f"def {attr}" in text, (
            f"Script {name!r} references {target!r} but "
            f"{module_file.relative_to(ROOT)} does not define {attr}()."
        )


def test_ci_workflow_exists():
    """Phase 5 adds GitHub Actions CI for Python 3.10–3.12."""
    workflow = ROOT / ".github" / "workflows" / "ci.yml"
    assert workflow.exists()
    text = workflow.read_text(encoding="utf-8")
    assert "pytest" in text
    # All supported Python versions covered.
    for version in ("3.10", "3.11", "3.12"):
        assert version in text, f"CI matrix missing Python {version}"


def test_phase5_docs_present():
    for name in ("ARCHITECTURE.md", "TUNING_GUIDE.md", "CONTRIBUTING.md",
                 "PROTOCOL_NOTES.md"):
        assert (ROOT / "docs" / name).exists(), f"docs/{name} is missing"
