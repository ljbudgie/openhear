"""
profiles.py – per-environment saved profiles.

A *profile* is a named config + metadata bundle the user can recall
with one tap: "Restaurant", "Quiet home", "Wind outdoors".

    save_profile(config_path, name, metadata) → Path
    load_profile(name) → dict   # parsed YAML + metadata
    list_profiles() → list[str]
    delete_profile(name) → None

Profiles use this on-disk layout:

    ~/.openhear/profiles/<slug>/
        config.yaml
        metadata.json    {name, created_at, environment, notes}
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dsp.user_config import load_config

__all__ = [
    "PROFILES_ROOT",
    "save_profile",
    "load_profile",
    "list_profiles",
    "delete_profile",
]


#: Default root under which profiles are stored.  Resolved lazily so
#: callers in environments without ``$HOME`` (e.g. CI) still import
#: successfully.
PROFILES_ROOT: Path = Path.home() / ".openhear" / "profiles"


def _slugify(name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)
    return safe.lower() or "unnamed"


def save_profile(
    config_path: Path,
    name: str,
    *,
    environment: str = "",
    notes: str = "",
    root: Path = PROFILES_ROOT,
) -> Path:
    """Persist *config_path* under *name* and return the new directory.

    Raises:
        FileNotFoundError: If *config_path* does not exist.
        ValueError: If *name* is blank.
    """
    if not name.strip():
        raise ValueError("Profile name must not be blank.")
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    profile_dir = root / _slugify(name)
    profile_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config_path, profile_dir / "config.yaml")
    metadata = {
        "name": name,
        "slug": profile_dir.name,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "environment": environment,
        "notes": notes,
    }
    (profile_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return profile_dir


def load_profile(
    name: str,
    *,
    root: Path = PROFILES_ROOT,
) -> dict[str, Any]:
    """Return the saved profile's parsed config + metadata dict.

    Raises:
        FileNotFoundError: If *name* has no saved profile.
    """
    profile_dir = _profile_dir(name, root)
    metadata_path = profile_dir / "metadata.json"
    config_path = profile_dir / "config.yaml"
    if not metadata_path.exists() or not config_path.exists():
        raise FileNotFoundError(f"Profile not found: {name}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError(f"Profile metadata must be an object: {metadata_path}")
    return {
        "metadata": metadata,
        "config": load_config(config_path).to_dict(),
        "config_path": str(config_path),
    }


def list_profiles(*, root: Path = PROFILES_ROOT) -> list[str]:
    """Return every saved profile name."""
    if not root.exists():
        return []
    names: list[str] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        metadata_path = child / "metadata.json"
        if not metadata_path.exists():
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(metadata, dict):
            profile_name = metadata.get("name")
            names.append(profile_name if isinstance(profile_name, str) else child.name)
    return sorted(names, key=lambda name: name.casefold())


def delete_profile(
    name: str,
    *,
    root: Path = PROFILES_ROOT,
) -> None:
    """Remove the named profile from disk.

    Raises:
        FileNotFoundError: If *name* has no saved profile.
    """
    profile_dir = _profile_dir(name, root)
    if not profile_dir.exists():
        raise FileNotFoundError(f"Profile not found: {name}")
    shutil.rmtree(profile_dir)


def _profile_dir(name: str, root: Path) -> Path:
    return root / _slugify(name)
