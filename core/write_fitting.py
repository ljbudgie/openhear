"""
write_fitting.py – gated writer for hearing-aid fitting parameters.

Writing to a hearing aid via reverse-engineered HIMSA framing is
high-risk: a malformed packet can leave the device in a state only the
manufacturer can recover.  This module therefore *gates* every write
behind two safeguards:

1. **Allow-list of safe parameters** – only programme name, volume
   offset, and streaming preference can be modified.  Gain tables,
   compression curves, MPO limits, and anything else that affects
   safety are explicitly refused at the API boundary.
2. **Backup-before-write** – every successful write is preceded by a
   :func:`core.backup.write_backup` call so the user can restore the
   prior state if the change is unwanted.

The module exposes one public function, :func:`write_safe_parameters`.
A real hardware path will be wired up once the corresponding
:class:`core.protocol.MessageType` codes are confirmed; until then the
function still performs the safety checks and the backup, then raises
``NotImplementedError`` for the actual transmission.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from core.backup import BackupArchive, write_backup
from core.fitting_data import FittingSession, ProgrammeSlot

logger = logging.getLogger(__name__)


#: Parameters this module is willing to write back to the device.
ALLOWED_PARAMETERS: frozenset[str] = frozenset({
    "programme_name",
    "volume_offset_db",
    "streaming_preference",
})


@dataclass(frozen=True)
class WriteRequest:
    """A single requested change to a programme slot.

    Attributes:
        programme_slot: ``ProgrammeSlot.slot_index`` to modify.
        parameter: Field name, must be in :data:`ALLOWED_PARAMETERS`.
        value: New value (type depends on *parameter*).
    """

    programme_slot: int
    parameter: str
    value: object


def _validate_request(request: WriteRequest) -> None:
    if request.parameter not in ALLOWED_PARAMETERS:
        raise PermissionError(
            f"Refusing to write parameter {request.parameter!r}.  "
            f"Only {sorted(ALLOWED_PARAMETERS)} are currently allowed.  "
            "Edit core.write_fitting.ALLOWED_PARAMETERS to expand the "
            "allow-list once the corresponding HIMSA message type has "
            "been verified end-to-end."
        )

    if request.parameter == "programme_name":
        if not isinstance(request.value, str) or not request.value.strip():
            raise ValueError("programme_name must be a non-empty string.")
        if len(request.value) > 32:
            raise ValueError("programme_name must be ≤ 32 characters.")
    elif request.parameter == "volume_offset_db":
        if not isinstance(request.value, (int, float)):
            raise ValueError("volume_offset_db must be a number.")
        if not (-12.0 <= float(request.value) <= 12.0):
            raise ValueError("volume_offset_db must be in [-12, +12] dB.")
    elif request.parameter == "streaming_preference":
        allowed = {"automatic", "priority", "off"}
        if request.value not in allowed:
            raise ValueError(
                f"streaming_preference must be one of {sorted(allowed)}, "
                f"got {request.value!r}."
            )


def _apply_request_to_session(session: FittingSession, request: WriteRequest) -> None:
    """Mirror the requested change in the in-memory ``session`` object."""
    matches = [p for p in session.programmes if p.slot_index == request.programme_slot]
    if not matches:
        # Create the slot rather than fail — the user might be
        # initialising it for the first time.
        slot = ProgrammeSlot(slot_index=request.programme_slot)
        session.programmes.append(slot)
        matches = [slot]

    for slot in matches:
        if request.parameter == "programme_name":
            slot.name = str(request.value)
        elif request.parameter == "volume_offset_db":
            slot.volume_offset_db = float(request.value)  # type: ignore[arg-type]
        elif request.parameter == "streaming_preference":
            slot.streaming_preference = str(request.value)


def write_safe_parameters(
    session: FittingSession,
    raw_payload: bytes,
    requests: list[WriteRequest],
    *,
    backup_dir: Path,
    transmit: bool = False,
) -> BackupArchive:
    """Validate, back up, and (optionally) transmit *requests*.

    Args:
        session: The most recently read :class:`FittingSession`.
        raw_payload: The raw HID bytes captured during that read (will
            be archived as part of the backup).
        requests: Changes to apply.
        backup_dir: Directory under which the backup is written.
        transmit: If ``True``, attempt to actually send the changes to
            the device.  This currently raises ``NotImplementedError``
            because the corresponding HIMSA message types have not yet
            been verified.

    Returns:
        The :class:`BackupArchive` written before any transmission.

    Raises:
        PermissionError: If a request targets a non-allow-listed field.
        ValueError: If a request value is outside the safe range.
        NotImplementedError: When ``transmit=True`` (transmission
            implementation pending).
    """
    if not requests:
        raise ValueError("At least one WriteRequest is required.")

    for req in requests:
        _validate_request(req)

    # Snapshot the pre-write state to disk before mutating anything.
    archive = write_backup(session, raw_payload, output_dir=backup_dir)
    logger.info("Pre-write backup at %s", archive.directory)

    # Apply the requested changes to the in-memory session.  This makes
    # the function still useful in dry-run mode.
    for req in requests:
        _apply_request_to_session(session, req)

    if transmit:
        raise NotImplementedError(
            "write_safe_parameters(transmit=True) is gated until the "
            "HIMSA WRITE_FITTING message type is verified.  See "
            "docs/PROTOCOL_NOTES.md for the open questions and "
            "core.protocol.MessageType.WRITE_FITTING for the placeholder."
        )

    return archive
