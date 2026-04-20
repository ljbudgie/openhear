"""Shared pytest fixtures for the OpenHear test suite."""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

# Make repository root importable when pytest is invoked from the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# Provide a minimal stub for the optional `hid` USB library so modules that
# import it at module load time (core.read_fitting, audiogram.reader) can be
# imported and unit-tested in environments without the native hidapi library.
def _install_hid_stub() -> None:
    try:
        import hid as _real_hid  # noqa: F401
        if hasattr(_real_hid, "device"):
            return
    except Exception:  # pragma: no cover - defensive: covers ImportError + load failures
        pass

    stub = types.ModuleType("hid")

    class _StubDevice:  # pragma: no cover - replaced by tests as needed
        def open(self, vendor_id, product_id):
            raise OSError("stub hid.device cannot open real hardware")

        def set_nonblocking(self, value):
            pass

        def write(self, data):
            return len(data)

        def read(self, length, timeout_ms=0):
            return []

        def close(self):
            pass

    stub.device = _StubDevice
    sys.modules["hid"] = stub


_install_hid_stub()


@pytest.fixture
def sample_audiogram_dict() -> dict:
    """Return a valid openhear-audiogram-v1 dict with data on both ears."""
    return {
        "subject": "Test Subject",
        "source": "Unit Test Clinic",
        "date": "2024-01-15",
        "format_version": "openhear-audiogram-v1",
        "notes": "Synthetic audiogram for tests.",
        "right_ear": {
            "symbol": "O",
            "thresholds": [
                {"freq_hz": 250, "db_hl": 20},
                {"freq_hz": 500, "db_hl": 30},
                {"freq_hz": 1000, "db_hl": 40},
                {"freq_hz": 2000, "db_hl": 50},
                {"freq_hz": 4000, "db_hl": 60},
                {"freq_hz": 8000, "db_hl": 70},
            ],
        },
        "left_ear": {
            "symbol": "X",
            "thresholds": [
                {"freq_hz": 250, "db_hl": 25},
                {"freq_hz": 500, "db_hl": 35},
                {"freq_hz": 1000, "db_hl": 45},
                {"freq_hz": 2000, "db_hl": 55},
                {"freq_hz": 4000, "db_hl": 65},
                {"freq_hz": 8000, "db_hl": 75},
            ],
        },
    }


@pytest.fixture
def audiogram_path(tmp_path: Path, sample_audiogram_dict: dict) -> str:
    """Write ``sample_audiogram_dict`` to a JSON file and return its path."""
    p = tmp_path / "audiogram.json"
    p.write_text(json.dumps(sample_audiogram_dict), encoding="utf-8")
    return str(p)


@pytest.fixture
def burgess_audiogram_path() -> str:
    """Return the path to the bundled burgess_2021 audiogram sample."""
    return str(_REPO_ROOT / "audiogram" / "data" / "burgess_2021.json")
