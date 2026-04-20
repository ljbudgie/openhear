"""
backup.py – read-and-archive the full state of a hearing aid.

Performs a *binary* read of every byte the Noahlink wrapper can extract
from the connected hearing aid and stores it as an opaque archive
together with the structured :class:`core.fitting_data.FittingSession`
JSON.  The pair is enough to restore the aid to a known-good state if a
later write goes wrong (see :mod:`core.write_fitting`).

Storage layout::

    output/backups/<serial>_<utc-iso>/
        ├── fitting.json        (FittingSession.to_json())
        ├── raw.bin             (concatenated HID reports)
        └── manifest.json       (sha256 + sizes for integrity check)

The restore path is currently a documented stub: writing arbitrary
bytes back to a hearing aid via reverse-engineered HIMSA framing is
unsafe without verified protocol coverage.  ``restore_backup`` raises
``NotImplementedError`` until that work is done.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from core.fitting_data import FittingSession

logger = logging.getLogger(__name__)


@dataclass
class BackupArchive:
    """Pointer to a backup that lives on disk.

    Attributes:
        directory: Root directory of the backup.
        fitting_path: Path to the structured ``fitting.json``.
        raw_path: Path to the binary ``raw.bin`` dump.
        manifest_path: Path to ``manifest.json`` (integrity metadata).
    """

    directory: Path
    fitting_path: Path
    raw_path: Path
    manifest_path: Path

    def verify(self) -> bool:
        """Recompute checksums and confirm they match the manifest."""
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        computed = {
            "fitting_sha256": _sha256_file(self.fitting_path),
            "raw_sha256": _sha256_file(self.raw_path),
        }
        return (
            manifest.get("fitting_sha256") == computed["fitting_sha256"]
            and manifest.get("raw_sha256") == computed["raw_sha256"]
        )


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _safe_label(serial: str) -> str:
    """Sanitise a serial number for use as a directory name."""
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in serial)
    return safe or "unknown"


def write_backup(
    session: FittingSession,
    raw_payload: bytes,
    *,
    output_dir: Path,
) -> BackupArchive:
    """Persist *session* and *raw_payload* under *output_dir*.

    Args:
        session: Structured fitting data (from :mod:`core.read_fitting`).
        raw_payload: Concatenated binary HID dump captured during read.
        output_dir: Root under which a timestamped subdirectory is
            created.

    Returns:
        A :class:`BackupArchive` describing the new directory.
    """
    serial = session.device.serial
    label = f"{_safe_label(serial)}_{_utc_now_iso().replace(':', '-')}"
    backup_dir = Path(output_dir) / label
    backup_dir.mkdir(parents=True, exist_ok=True)

    fitting_path = backup_dir / "fitting.json"
    raw_path = backup_dir / "raw.bin"
    manifest_path = backup_dir / "manifest.json"

    fitting_path.write_text(session.to_json(indent=2), encoding="utf-8")
    raw_path.write_bytes(bytes(raw_payload))

    manifest = {
        "schema_version": "openhear-backup-v1",
        "created_at": _utc_now_iso(),
        "device_serial": serial,
        "fitting_filename": fitting_path.name,
        "raw_filename": raw_path.name,
        "fitting_sha256": _sha256_file(fitting_path),
        "raw_sha256": _sha256_file(raw_path),
        "raw_size_bytes": raw_path.stat().st_size,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info("Wrote backup to %s", backup_dir)

    return BackupArchive(
        directory=backup_dir,
        fitting_path=fitting_path,
        raw_path=raw_path,
        manifest_path=manifest_path,
    )


def load_backup(directory: Path) -> tuple[FittingSession, bytes]:
    """Load a backup written by :func:`write_backup`.

    Args:
        directory: Path returned by :func:`write_backup` (or any
            directory containing the same three files).

    Returns:
        ``(session, raw_payload)``.

    Raises:
        FileNotFoundError: If any expected file is missing.
        ValueError: If the manifest checksums do not match.
    """
    directory = Path(directory)
    fitting_path = directory / "fitting.json"
    raw_path = directory / "raw.bin"
    manifest_path = directory / "manifest.json"

    for required in (fitting_path, raw_path, manifest_path):
        if not required.exists():
            raise FileNotFoundError(f"Backup is missing {required.name}.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("fitting_sha256") != _sha256_file(fitting_path):
        raise ValueError("fitting.json checksum does not match manifest.")
    if manifest.get("raw_sha256") != _sha256_file(raw_path):
        raise ValueError("raw.bin checksum does not match manifest.")

    session = FittingSession.from_json(fitting_path.read_text(encoding="utf-8"))
    raw = raw_path.read_bytes()
    return session, raw


def restore_backup(directory: Path) -> None:  # pragma: no cover - stub
    """Restore a backup to a connected device.

    **Not yet implemented.**  Writing arbitrary bytes back to a hearing
    aid via the reverse-engineered HIMSA framing risks bricking the
    device.  This function will be implemented once the protocol
    coverage in :mod:`core.protocol` is verified end-to-end.
    """
    _ = directory  # silence linters until implementation lands
    raise NotImplementedError(
        "restore_backup() is not yet implemented.  See "
        "docs/PROTOCOL_NOTES.md for the unresolved fields blocking it."
    )
