"""
contact_profiles.py – per-contact DSP profile bank (roadmap S1 → metric M2).

When the user tells OpenHear "I'm about to talk with Alex", the pipeline
can apply a small, bounded :class:`~dsp.profile_delta.ProfileDelta` on top
of the generic audiogram-derived profile to better suit Alex's voice — a
gentler compressor for a softly-spoken partner, a touch more high-band
emphasis for a parent with a low fundamental, etc.

This module is **schema + storage + lookup only**.  Pipeline integration
lives in :mod:`dsp.pipeline`, and the user-facing controls live in
:mod:`dsp.contact_cli`.

Sovereignty & safety:
    * All data is stored locally in a single JSON file (default
      ``~/.openhear/contacts.json``).  Deleting that file revokes every
      stored contact profile in one move.
    * No voice-print fingerprint is computed in this v0 — the
      :attr:`ContactProfile.fingerprint` field is reserved for a later,
      consent-gated phase (§8 Q5 of the roadmap).
    * Every profile carries an explicit ``consent`` flag.  Profiles
      without consent are loaded for inspection but **never** applied to
      the DSP chain (:func:`active_delta` returns the identity delta).
    * Profiles carry an ``enabled`` flag so they can be temporarily
      disabled without deleting the per-contact tuning (BSEP-style).
    * Delta magnitudes are bounded by :mod:`dsp.profile_delta` (clipped
      on construction); there is no way for a contact profile to push
      the DSP outside the safe envelope.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from dsp.profile_delta import ProfileDelta

logger = logging.getLogger(__name__)

#: Canonical relative location of the user's contacts file.
DEFAULT_CONTACTS_RELATIVE_PATH = Path(".openhear") / "contacts.json"

#: File format version.  Bumped on breaking schema changes.
CONTACTS_FORMAT_VERSION: int = 1


def default_contacts_path() -> Path:
    """Return ``~/.openhear/contacts.json`` as a :class:`Path`."""
    return Path.home() / DEFAULT_CONTACTS_RELATIVE_PATH


# ── Dataclass ───────────────────────────────────────────────────────────────


@dataclass
class ContactProfile:
    """One stored per-contact DSP tuning.

    Attributes:
        contact_id: Stable identifier (e.g. ``"partner"`` or ``"alex"``).
            Used by :func:`active_delta` for lookup.  Should be lowercase
            and free of whitespace; the loader enforces this on read.
        label: Human-readable display name shown by the CLI.
        eq_delta_db: *Reserved for a future EQ-curve channel.*  Currently
            unused by the pipeline; included so the schema is forward-
            compatible with the per-band EQ work tracked under §4.1 of
            the roadmap.  Must be a mapping of ``frequency_hz -> dB``;
            non-empty entries are accepted but not yet applied.
        compression_ratio_delta: Bounded delta passed straight to
            :class:`~dsp.profile_delta.ProfileDelta`.
        compression_knee_delta_db: Bounded delta (dB).
        voice_gain_delta: Bounded delta (linear multiplier).
        nr_aggressiveness_delta: Bounded delta (unitless).
        consent: ``True`` only when the user has explicitly opted this
            contact in.  When ``False`` the profile is loaded but never
            applied — see :func:`active_delta`.
        enabled: BSEP-style master switch for this individual contact.
            ``False`` means "loaded but inactive".
        fingerprint: Reserved for a later, consent-gated voice-print
            phase.  Must be ``None`` in v0 — the loader rejects any
            non-null value with a clear error so users know the feature
            is not yet shipped.
        notes: Optional free-text notes (kept local; never displayed
            outside the CLI ``show`` command).
    """

    contact_id: str
    label: str = ""
    eq_delta_db: dict[int, float] = field(default_factory=dict)
    compression_ratio_delta: float = 0.0
    compression_knee_delta_db: float = 0.0
    voice_gain_delta: float = 0.0
    nr_aggressiveness_delta: float = 0.0
    consent: bool = False
    enabled: bool = True
    fingerprint: None = None
    notes: str = ""

    def to_delta(self) -> ProfileDelta:
        """Render this profile as a bounded, source-tagged ProfileDelta.

        The :mod:`dsp.profile_delta` clipping limits are the only
        guarantor of safe magnitudes — even a malformed contacts.json
        cannot push the pipeline outside the envelope.
        """
        return ProfileDelta(
            compression_ratio_delta=self.compression_ratio_delta,
            compression_knee_delta_db=self.compression_knee_delta_db,
            voice_gain_delta=self.voice_gain_delta,
            nr_aggressiveness_delta=self.nr_aggressiveness_delta,
            sources=(f"contact:{self.contact_id}",),
            reason=f"per-contact tuning for {self.label or self.contact_id}",
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict of this profile."""
        d = asdict(self)
        # eq_delta_db keys are ints; JSON requires strings.  Round-trip
        # them through str() so the file is valid JSON.
        d["eq_delta_db"] = {str(k): float(v) for k, v in self.eq_delta_db.items()}
        return d

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ContactProfile":
        if not isinstance(data, Mapping):
            raise ValueError(f"contact profile must be a mapping, got {type(data).__name__}")
        contact_id = str(data.get("contact_id", "")).strip().lower()
        if not contact_id:
            raise ValueError("contact_id is required and must be non-empty")
        if any(c.isspace() for c in contact_id):
            raise ValueError(f"contact_id must not contain whitespace, got {contact_id!r}")

        fingerprint = data.get("fingerprint", None)
        if fingerprint is not None:
            raise ValueError(
                "voice-print fingerprints are not supported in v0 "
                "(reserved for a later consent-gated phase)"
            )

        eq_raw = data.get("eq_delta_db", {}) or {}
        if not isinstance(eq_raw, Mapping):
            raise ValueError("eq_delta_db must be a mapping {freq_hz: dB}")
        try:
            eq_parsed = {int(k): float(v) for k, v in eq_raw.items()}
        except (TypeError, ValueError) as exc:
            raise ValueError(f"eq_delta_db entries must be numeric: {exc}") from exc

        return cls(
            contact_id=contact_id,
            label=str(data.get("label", "")),
            eq_delta_db=eq_parsed,
            compression_ratio_delta=float(data.get("compression_ratio_delta", 0.0)),
            compression_knee_delta_db=float(data.get("compression_knee_delta_db", 0.0)),
            voice_gain_delta=float(data.get("voice_gain_delta", 0.0)),
            nr_aggressiveness_delta=float(data.get("nr_aggressiveness_delta", 0.0)),
            consent=bool(data.get("consent", False)),
            enabled=bool(data.get("enabled", True)),
            fingerprint=None,
            notes=str(data.get("notes", "")),
        )


# ── Storage ────────────────────────────────────────────────────────────────


@dataclass
class ContactBank:
    """In-memory representation of the on-disk contacts.json file."""

    profiles: dict[str, ContactProfile] = field(default_factory=dict)
    version: int = CONTACTS_FORMAT_VERSION

    def add(self, profile: ContactProfile) -> None:
        """Insert or replace ``profile`` in the bank."""
        self.profiles[profile.contact_id] = profile

    def remove(self, contact_id: str) -> bool:
        """Remove a profile; return ``True`` if one existed."""
        return self.profiles.pop(contact_id.strip().lower(), None) is not None

    def get(self, contact_id: str) -> ContactProfile | None:
        """Look up a profile by id (case-insensitive)."""
        return self.profiles.get(contact_id.strip().lower())

    def list_ids(self) -> list[str]:
        """Sorted list of stored contact ids."""
        return sorted(self.profiles)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "profiles": [p.to_dict() for p in self.profiles.values()],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "ContactBank":
        if data is None:
            return cls()
        if not isinstance(data, Mapping):
            raise ValueError(f"contacts.json root must be a mapping, got {type(data).__name__}")
        version = int(data.get("version", CONTACTS_FORMAT_VERSION))
        if version > CONTACTS_FORMAT_VERSION:
            raise ValueError(
                f"contacts.json version {version} is newer than supported "
                f"({CONTACTS_FORMAT_VERSION}); upgrade OpenHear or downgrade "
                "the file."
            )
        raw_profiles = data.get("profiles", [])
        if not isinstance(raw_profiles, Iterable) or isinstance(raw_profiles, (str, Mapping)):
            raise ValueError("contacts.json 'profiles' must be a list")
        bank = cls(version=version)
        for entry in raw_profiles:
            profile = ContactProfile.from_dict(entry)
            if profile.contact_id in bank.profiles:
                raise ValueError(f"duplicate contact_id {profile.contact_id!r} in contacts.json")
            bank.add(profile)
        return bank


def _resolve_path(path: str | Path | None) -> Path:
    """Resolve ``~`` and env-var overrides to a concrete :class:`Path`."""
    if path is None:
        return default_contacts_path()
    return Path(os.path.expanduser(str(path)))


def load_bank(path: str | Path | None = None) -> ContactBank:
    """Load the contacts bank from disk, returning an empty bank on miss.

    Args:
        path: Explicit override; ``None`` uses :func:`default_contacts_path`.

    Returns:
        The parsed :class:`ContactBank`.  When no file exists at the
        target location, returns an empty bank (no error).
    """
    target = _resolve_path(path)
    if not target.exists():
        logger.debug("No contacts.json at %s; returning empty bank.", target)
        return ContactBank()
    text = target.read_text(encoding="utf-8")
    data = json.loads(text) if text.strip() else None
    return ContactBank.from_dict(data)


def save_bank(bank: ContactBank, path: str | Path | None = None) -> Path:
    """Write the bank atomically to disk, returning the resolved path.

    The directory is created with mode ``0o700`` if absent (user-only
    access) — these are sensitive social-tier data per §8 of the
    roadmap.  The file itself is written via the rename trick so a
    crash mid-write cannot corrupt the existing bank.
    """
    target = _resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(bank.to_dict(), indent=2), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        # Non-POSIX filesystem; the rename below still gives us atomicity.
        logger.debug("Could not chmod %s (non-POSIX filesystem?)", tmp)
    tmp.replace(target)
    return target


# ── Active-delta lookup (pipeline entry point) ─────────────────────────────


def active_delta(
    contact_id: str | None,
    bank: ContactBank | None = None,
    *,
    path: str | Path | None = None,
) -> ProfileDelta:
    """Return the :class:`ProfileDelta` to apply for ``contact_id``.

    This is the single function the pipeline calls.  It returns the
    identity delta in every case where the contact's tuning should
    **not** be applied:

    * ``contact_id`` is ``None`` or empty.
    * The bank does not contain a profile for that id.
    * The profile has ``consent=False`` (logs a warning).
    * The profile has ``enabled=False`` (logs an info message).

    Args:
        contact_id: The currently active contact, or ``None``.
        bank: Pre-loaded bank (used by tests).  When ``None``, the bank
            is loaded from ``path`` (or the default location).
        path: Override for the bank file location.

    Returns:
        A bounded, source-tagged :class:`ProfileDelta`.  The identity
        delta is returned in all "do not apply" cases above.
    """
    if not contact_id:
        return ProfileDelta()
    if bank is None:
        bank = load_bank(path)
    profile = bank.get(contact_id)
    if profile is None:
        logger.warning(
            "Active contact %r is not in the bank; falling back to generic profile.",
            contact_id,
        )
        return ProfileDelta()
    if not profile.consent:
        logger.warning(
            "Contact profile %r has consent=False; refusing to apply (Burgess Principle).",
            contact_id,
        )
        return ProfileDelta()
    if not profile.enabled:
        logger.info("Contact profile %r is disabled; using generic profile.", contact_id)
        return ProfileDelta()
    delta = profile.to_delta()
    # BGSP-style one-line audit record so receipts are recoverable later.
    logger.info("BGSP|contact-profile-applied|%s", delta.explain())
    return delta
