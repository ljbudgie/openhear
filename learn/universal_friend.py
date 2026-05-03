"""
universal_friend.py – local-only trusted contact/session mirroring helpers.

OpenHear does not maintain a phone-style contact graph.  A Universal Friend is
therefore represented as a consent-scoped local invite that references a saved
profile by digest and mirrors only profile policy metadata.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from learn.profiles import PROFILES_ROOT, load_profile

ConsentScope = Literal[
    "profile_summary",
    "focus_policy",
    "haptic_ack",
    "guardian_alert",
]

_CONSENT_SCOPES: tuple[ConsentScope, ...] = (
    "profile_summary",
    "focus_policy",
    "haptic_ack",
    "guardian_alert",
)
DEFAULT_CONSENT_SCOPES: tuple[ConsentScope, ...] = (
    "profile_summary",
    "focus_policy",
    "haptic_ack",
)

__all__ = [
    "ConsentScope",
    "DEFAULT_CONSENT_SCOPES",
    "UniversalFriendInvite",
    "create_invite",
    "load_invite",
    "start_mirrored_session",
    "write_invite",
]


@dataclass(frozen=True)
class UniversalFriendInvite:
    """Consent-scoped reference to a local profile for a trusted contact."""

    alias: str
    profile_name: str
    profile_slug: str
    profile_digest: str
    scopes: tuple[ConsentScope, ...] = DEFAULT_CONSENT_SCOPES
    created_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["scopes"] = list(self.scopes)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UniversalFriendInvite":
        if not isinstance(data, dict):
            raise ValueError("Universal Friend invite must be a JSON object.")
        scopes = _normalise_scopes(data.get("scopes", DEFAULT_CONSENT_SCOPES))
        return cls(
            alias=_required_text(data, "alias"),
            profile_name=_required_text(data, "profile_name"),
            profile_slug=_required_text(data, "profile_slug"),
            profile_digest=_required_text(data, "profile_digest"),
            scopes=scopes,
            created_at=_required_text(data, "created_at"),
            note=str(data.get("note", "")),
        )


def create_invite(
    profile_name: str,
    *,
    alias: str = "Universal Friend",
    scopes: tuple[ConsentScope, ...] = DEFAULT_CONSENT_SCOPES,
    note: str = "",
    root: Path = PROFILES_ROOT,
) -> UniversalFriendInvite:
    """Create a Universal Friend invite for a saved profile.

    The invite carries a SHA-256 digest of the local profile config, not the
    config itself, and never imports an address book or exports raw audio.

    Raises:
        FileNotFoundError: If *profile_name* has no saved profile.
        ValueError: If *alias*, *profile_name*, or *scopes* are invalid.
    """
    if not alias.strip():
        raise ValueError("Universal Friend alias must not be blank.")
    if not profile_name.strip():
        raise ValueError("Universal Friend profile name must not be blank.")

    loaded = load_profile(profile_name, root=root)
    metadata = loaded["metadata"]
    profile_slug = str(metadata["slug"])
    config_path = Path(str(loaded["config_path"]))
    return UniversalFriendInvite(
        alias=alias,
        profile_name=str(metadata["name"]),
        profile_slug=profile_slug,
        profile_digest=_sha256_file(config_path),
        scopes=_normalise_scopes(scopes),
        note=note,
    )


def write_invite(invite: UniversalFriendInvite, output_path: Path) -> Path:
    """Write *invite* as deterministic JSON and return *output_path*."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(invite.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def load_invite(path: Path) -> UniversalFriendInvite:
    """Load a Universal Friend invite from *path*."""
    return UniversalFriendInvite.from_dict(json.loads(path.read_text(encoding="utf-8")))


def start_mirrored_session(
    invite: UniversalFriendInvite,
    *,
    session_id: str = "",
) -> dict[str, Any]:
    """Return session-mirroring metadata for a trusted contact.

    The returned payload is suitable for a UI/runtime to activate mirrored focus
    policy.  It intentionally excludes phone numbers, address-book IDs, raw
    audio, audiograms, biometrics, and full profile configuration.
    """
    return {
        "session_id": session_id,
        "started_at": datetime.now(tz=timezone.utc).isoformat(),
        "status": "mirroring_profile_policy",
        "trusted_contact": invite.alias,
        "profile_name": invite.profile_name,
        "profile_slug": invite.profile_slug,
        "profile_digest": invite.profile_digest,
        "scopes": list(invite.scopes),
        "raw_personal_data": False,
    }


def _normalise_scopes(scopes: Any) -> tuple[ConsentScope, ...]:
    if isinstance(scopes, str) or not scopes:
        raise ValueError("Universal Friend invite must include at least one consent scope.")
    normalised: list[ConsentScope] = []
    for scope in scopes:
        if scope not in _CONSENT_SCOPES:
            raise ValueError(f"Unknown Universal Friend consent scope: {scope!r}.")
        if scope not in normalised:
            normalised.append(scope)
    return tuple(normalised)


def _required_text(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Universal Friend invite field {key!r} must be non-blank text.")
    return value


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
