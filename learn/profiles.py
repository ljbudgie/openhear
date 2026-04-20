"""
profiles.py – per-environment saved profiles (Phase 6 stub).

A *profile* is a named config + metadata bundle the user can recall
with one tap: "Restaurant", "Quiet home", "Wind outdoors".

    save_profile(config_path, name, metadata) → Path
    load_profile(name) → dict   # parsed YAML + metadata
    list_profiles() → list[str]
    delete_profile(name) → None

All are :class:`NotImplementedError` stubs today.  The on-disk layout
is documented here so any future implementer (or user following the
architecture docs) has a clear target:

    ~/.openhear/profiles/<slug>/
        config.yaml
        metadata.json    {name, created_at, environment, notes}
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
    """Helper placeholder — finalise once the stubs are implemented."""
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
        NotImplementedError: Always — implementation pending.
    """
    _ = config_path, name, environment, notes, root
    raise NotImplementedError(
        "learn.profiles.save_profile is a Phase 6 scaffold.  "
        "Expected layout: <root>/<slug>/config.yaml + metadata.json."
    )


def load_profile(
    name: str,
    *,
    root: Path = PROFILES_ROOT,
) -> dict[str, Any]:
    """Return the saved profile's parsed config + metadata dict.

    Raises:
        NotImplementedError: Always — implementation pending.
    """
    _ = name, root
    raise NotImplementedError(
        "learn.profiles.load_profile is a Phase 6 scaffold."
    )


def list_profiles(*, root: Path = PROFILES_ROOT) -> list[str]:
    """Return every saved profile name.

    Raises:
        NotImplementedError: Always — implementation pending.
    """
    _ = root
    raise NotImplementedError(
        "learn.profiles.list_profiles is a Phase 6 scaffold."
    )


def delete_profile(
    name: str,
    *,
    root: Path = PROFILES_ROOT,
) -> None:
    """Remove the named profile from disk.

    Raises:
        NotImplementedError: Always — implementation pending.
    """
    _ = name, root
    raise NotImplementedError(
        "learn.profiles.delete_profile is a Phase 6 scaffold."
    )
