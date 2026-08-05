"""
living_profile.py – Living Hearing Profile core for OpenHear.

A :class:`LivingHearingProfile` is a sovereign, versioned, user-owned
representation of a person's hearing that grows alongside them.  It wraps
the immutable clinical pure-tone core from ``openhear-audiogram-v1`` and
adds:

- **Preference layer** — per-frequency loudness growth offsets and comfort
  settings that the user tunes over time.
- **Context map** — named situational presets (quiet conversation, noisy
  venue, music, etc.) that swap processing parameters at runtime.
- **Haptic layer** — per-sound-class substitution weights derived from the
  audiogram and adjustable by the user for their wristband experience.
- **History** — an append-only change log with SHA-256 content commitments
  compatible with the Burgess Principle (no mutation, only attestation).

The format is stored as ``openhear-living-profile-v1`` JSON.  The clinical
core thresholds remain identical to ``openhear-audiogram-v1`` so every
existing loader, visualiser, and DSP module continues to work unmodified.

Usage::

    from audiogram.living_profile import LivingHearingProfile

    # Load from file
    profile = LivingHearingProfile.from_file("audiogram/data/burgess_living_profile.json")

    # Inspect the clinical core
    print(profile.get_thresholds("right"))
    print(profile.get_pta("right"))

    # Apply a user preference update and commit it to history
    profile.set_loudness_offset("right", 1000, offset_db=4)
    profile.commit("Boosted speech band slightly — feels more natural")
    profile.save("audiogram/data/burgess_living_profile.json")

    # Export DSP gain (clinical + preference offsets)
    print(profile.get_gain_profile("right"))

    # Export haptic weights for the wristband
    print(profile.get_haptic_weights())

    # Export as Hearing Passport
    from audiogram.passport import export_passport
    export_passport(profile, "burgess_passport.md")
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

# ── Constants ─────────────────────────────────────────────────────────────────

FORMAT_VERSION = "openhear-living-profile-v1"
_CLINICAL_V1_VERSION = "openhear-audiogram-v1"

_NORMAL_THRESHOLD_DB = 20
_PTA_FREQUENCIES = {500, 1000, 2000, 4000}


# ── Public API ────────────────────────────────────────────────────────────────


class LivingHearingProfile:
    """A sovereign, versioned, evolving hearing profile.

    All mutations are tracked in an append-only history with SHA-256
    content commitments.  The clinical core is never altered in place.

    Args:
        data: A parsed ``openhear-living-profile-v1`` dict.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        _validate(data)
        self._data = data

    # ── Constructors ──────────────────────────────────────────────────────────

    @classmethod
    def from_file(cls, path: str) -> "LivingHearingProfile":
        """Load a Living Hearing Profile from a JSON file.

        Also accepts a plain ``openhear-audiogram-v1`` file; the clinical
        data is wrapped into the v2 structure automatically so users can
        start their living profile from any existing audiogram.

        Args:
            path: Path to the JSON file.

        Returns:
            A validated :class:`LivingHearingProfile`.

        Raises:
            FileNotFoundError: If *path* does not exist.
            ValueError: If the file is not a recognised format.
        """
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)

        version = data.get("format_version", "")
        if version == FORMAT_VERSION:
            return cls(data)
        if version == _CLINICAL_V1_VERSION:
            return cls(_wrap_v1_audiogram(data))
        raise ValueError(
            f"Unsupported format version: {version!r}. "
            f"Expected '{FORMAT_VERSION}' or '{_CLINICAL_V1_VERSION}'."
        )

    @classmethod
    def from_manual_entry(
        cls,
        subject: str,
        right_thresholds: list[tuple[int, int]],
        left_thresholds: list[tuple[int, int]],
        source: str = "Manual entry",
        notes: str = "",
    ) -> "LivingHearingProfile":
        """Create a new profile from manually entered threshold values.

        Args:
            subject:           Name of the profile owner.
            right_thresholds:  List of ``(freq_hz, db_hl)`` pairs.
            left_thresholds:   List of ``(freq_hz, db_hl)`` pairs.
            source:            Where the thresholds came from.
            notes:             Free-text notes.

        Returns:
            A fresh :class:`LivingHearingProfile` with empty preference,
            context, and haptic layers.
        """
        today = datetime.now(tz=timezone.utc).date().isoformat()
        data = _make_empty_profile(
            subject=subject,
            source=source,
            date=today,
            notes=notes,
            right_thresholds=right_thresholds,
            left_thresholds=left_thresholds,
        )
        return cls(data)

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        """Serialise the profile to a JSON file.

        Args:
            path: Destination path.
        """
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")

    def to_dict(self) -> dict[str, Any]:
        """Return a deep copy of the underlying data dict."""
        return json.loads(json.dumps(self._data))

    # ── Clinical core read access ─────────────────────────────────────────────

    @property
    def subject(self) -> str:
        """Name of the profile owner."""
        return self._data["subject"]

    @property
    def clinical_date(self) -> str:
        """ISO 8601 date of the clinical audiogram."""
        return self._data["clinical_core"]["date"]

    def get_thresholds(self, ear: str) -> list[tuple[int, int]]:
        """Return sorted ``(freq_hz, db_hl)`` pairs from the clinical core.

        Args:
            ear: ``"right"`` or ``"left"``.
        """
        ear_key = _resolve_ear(ear)
        raw = self._data["clinical_core"][ear_key]["thresholds"]
        return sorted((int(t["freq_hz"]), int(t["db_hl"])) for t in raw)

    def get_pta(self, ear: str) -> float:
        """Compute the Pure Tone Average from the clinical core.

        Args:
            ear: ``"right"`` or ``"left"``.

        Returns:
            PTA in dB HL, rounded to one decimal place.

        Raises:
            ValueError: If not all four PTA frequencies are present.
        """
        thresholds = dict(self.get_thresholds(ear))
        missing = _PTA_FREQUENCIES - set(thresholds)
        if missing:
            raise ValueError(
                f"Cannot compute PTA: missing thresholds at "
                f"{', '.join(str(f) for f in sorted(missing))} Hz."
            )
        return round(sum(thresholds[f] for f in _PTA_FREQUENCIES) / 4, 1)

    # ── Gain profile (clinical + preference offsets) ──────────────────────────

    def get_gain_profile(self, ear: str, *, include_preference: bool = True) -> list[tuple[int, int]]:
        """Compute the amplification gain at each tested frequency.

        By default the preference-layer loudness growth offsets are added
        on top of the clinical prescription.  Pass ``include_preference=False``
        to get the raw clinical gain only.

        Gain = max(0, threshold − 20) + preference_offset

        Args:
            ear:                ``"right"`` or ``"left"``.
            include_preference: Whether to add the preference-layer offsets.

        Returns:
            Sorted list of ``(freq_hz, gain_db)`` tuples.
        """
        thresholds = self.get_thresholds(ear)
        pref_offsets: dict[int, int] = {}
        if include_preference:
            pref_offsets = self._get_preference_offsets(ear)

        result: list[tuple[int, int]] = []
        for freq, db in thresholds:
            base_gain = max(0, db - _NORMAL_THRESHOLD_DB)
            offset = pref_offsets.get(freq, 0)
            result.append((freq, max(0, base_gain + offset)))
        return result

    # ── Haptic weights ────────────────────────────────────────────────────────

    def get_haptic_weights(self) -> dict[str, float]:
        """Return the haptic substitution weight for each sound class.

        Returns a dict of ``{sound_class_name: weight}`` for enabled classes.
        Weights are in the range 0.0 – 1.0.
        """
        classes = self._data.get("haptic_layer", {}).get("sound_classes", [])
        return {
            sc["name"]: float(sc["weight"])
            for sc in classes
            if sc.get("enabled", True)
        }

    def set_haptic_weight(self, sound_class: str, weight: float) -> None:
        """Update the haptic weight for a sound class.

        Args:
            sound_class: Name of the sound class (e.g. ``"alarm"``).
            weight:      New weight value, clamped to 0.0 – 1.0.

        Raises:
            KeyError: If *sound_class* is not present in the haptic layer.
        """
        weight = max(0.0, min(1.0, float(weight)))
        classes = self._data.setdefault("haptic_layer", {}).setdefault("sound_classes", [])
        for sc in classes:
            if sc["name"] == sound_class:
                sc["weight"] = weight
                return
        raise KeyError(f"Sound class {sound_class!r} not found in haptic layer.")

    # ── Context map ───────────────────────────────────────────────────────────

    def get_active_context(self) -> dict[str, Any]:
        """Return the currently active listening context dict.

        Returns:
            The context dict, or an empty dict if no context map is set.
        """
        ctx_map = self._data.get("context_map", {})
        active_name = ctx_map.get("active_context", "")
        for ctx in ctx_map.get("contexts", []):
            if ctx.get("name") == active_name:
                return dict(ctx)
        return {}

    def set_active_context(self, name: str) -> None:
        """Switch to a named listening context.

        Args:
            name: Context name (e.g. ``"noisy_environment"``).

        Raises:
            KeyError: If *name* is not defined in the context map.
        """
        ctx_map = self._data.setdefault("context_map", {})
        names = [c["name"] for c in ctx_map.get("contexts", [])]
        if name not in names:
            raise KeyError(
                f"Context {name!r} not found. Available: {names}"
            )
        ctx_map["active_context"] = name

    def list_contexts(self) -> list[str]:
        """Return the names of all defined listening contexts."""
        return [c["name"] for c in self._data.get("context_map", {}).get("contexts", [])]

    # ── Preference mutations ──────────────────────────────────────────────────

    def set_loudness_offset(self, ear: str, freq_hz: int, *, offset_db: int) -> None:
        """Set a per-frequency loudness preference offset.

        If the frequency is not already in the preference layer, it is added.

        Args:
            ear:       ``"right"`` or ``"left"``.
            freq_hz:   The frequency to adjust.
            offset_db: dB offset to apply (positive = louder, negative = quieter).
        """
        ear_key = _resolve_ear(ear)
        pref = self._data.setdefault("preference_layer", {})
        growth = pref.setdefault("loudness_growth", {})
        entries: list[dict] = growth.setdefault(ear_key, [])
        for entry in entries:
            if entry["freq_hz"] == freq_hz:
                entry["offset_db"] = offset_db
                return
        entries.append({"freq_hz": freq_hz, "offset_db": offset_db})

    def set_comfort_ceiling(self, db_spl: int) -> None:
        """Set the maximum comfortable listening level.

        Args:
            db_spl: Ceiling in dB SPL (typical range: 70–100).
        """
        self._data.setdefault("preference_layer", {})["comfort_ceiling_db_spl"] = db_spl

    # ── History and commitment ────────────────────────────────────────────────

    def commit(
        self,
        description: str,
        *,
        author: str | None = None,
        change_type: str = "user_update",
        layers_changed: list[str] | None = None,
    ) -> str:
        """Record a change to the profile history with a SHA-256 commitment.

        The SHA-256 hash is computed over the JSON serialisation of the
        current profile state (before writing the new history entry).  This
        gives a Burgess-Principle-compatible tamper-evident log: each entry
        proves what the profile looked like at the moment of commitment.

        Args:
            description:    Human-readable description of the change.
            author:         Who made the change (defaults to subject name).
            change_type:    Category string (e.g. ``"preference_update"``).
            layers_changed: Which top-level layers were modified.

        Returns:
            The hex-encoded SHA-256 hash of the committed state.
        """
        if author is None:
            author = self._data.get("subject", "unknown")
        if layers_changed is None:
            layers_changed = []

        # Hash the current state before appending the new entry.
        state_bytes = json.dumps(self._data, sort_keys=True, ensure_ascii=False).encode("utf-8")
        sha256 = hashlib.sha256(state_bytes).hexdigest()

        history = self._data.setdefault("history", {})
        entries: list[dict] = history.setdefault("entries", [])
        version = len(entries) + 1

        entries.append(
            {
                "version": version,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "author": author,
                "change_type": change_type,
                "description": description,
                "sha256": sha256,
                "layers_changed": layers_changed,
            }
        )

        self._data["last_updated"] = datetime.now(tz=timezone.utc).date().isoformat()
        return sha256

    def get_history(self) -> list[dict[str, Any]]:
        """Return the list of history entries in chronological order."""
        return list(self._data.get("history", {}).get("entries", []))

    # ── Convenience summary ───────────────────────────────────────────────────

    def summary(self) -> dict[str, Any]:
        """Return a concise summary dict suitable for display or serialisation.

        Includes subject name, clinical date, PTA per ear, severity per ear,
        active context, and the number of history entries.
        """
        from audiogram.loader import get_severity  # avoid circular at module level

        out: dict[str, Any] = {
            "subject": self.subject,
            "clinical_date": self.clinical_date,
            "last_updated": self._data.get("last_updated", "unknown"),
            "history_entries": len(self.get_history()),
        }
        for ear in ("right", "left"):
            try:
                pta = self.get_pta(ear)
                out[f"{ear}_pta"] = pta
                out[f"{ear}_severity"] = get_severity(int(pta))
            except ValueError:
                out[f"{ear}_pta"] = None
                out[f"{ear}_severity"] = "unknown"

        out["active_context"] = self.get_active_context().get("name", "none")
        return out

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_preference_offsets(self, ear: str) -> dict[int, int]:
        """Return {freq_hz: offset_db} from the preference layer for *ear*."""
        ear_key = _resolve_ear(ear)
        growth = (
            self._data.get("preference_layer", {})
            .get("loudness_growth", {})
            .get(ear_key, [])
        )
        return {int(e["freq_hz"]): int(e["offset_db"]) for e in growth}


# ── Module-level helpers ──────────────────────────────────────────────────────


def load_living_profile(path: str) -> LivingHearingProfile:
    """Convenience function — load a Living Hearing Profile from *path*.

    Also accepts plain ``openhear-audiogram-v1`` files (wraps automatically).

    Args:
        path: Path to a JSON file.

    Returns:
        A validated :class:`LivingHearingProfile`.
    """
    return LivingHearingProfile.from_file(path)


# ── Private helpers ───────────────────────────────────────────────────────────


def _resolve_ear(ear: str) -> str:
    """Map ``'right'``/``'left'`` to ``'right_ear'``/``'left_ear'``."""
    ear = ear.lower().strip()
    if ear == "right":
        return "right_ear"
    if ear == "left":
        return "left_ear"
    raise ValueError(f"ear must be 'right' or 'left', got {ear!r}")


def _validate(data: dict[str, Any]) -> None:
    """Raise :class:`ValueError` if *data* is not a valid living profile."""
    if data.get("format_version") != FORMAT_VERSION:
        raise ValueError(
            f"Expected format_version '{FORMAT_VERSION}', "
            f"got {data.get('format_version')!r}."
        )
    for field in ("subject", "clinical_core"):
        if field not in data:
            raise ValueError(f"Living profile is missing required field: '{field}'")
    core = data["clinical_core"]
    for ear_key in ("right_ear", "left_ear"):
        if ear_key not in core:
            raise ValueError(f"clinical_core is missing '{ear_key}'")
        if "thresholds" not in core[ear_key]:
            raise ValueError(f"clinical_core.{ear_key} is missing 'thresholds'")


def _wrap_v1_audiogram(v1: dict[str, Any]) -> dict[str, Any]:
    """Wrap a plain ``openhear-audiogram-v1`` dict into the v2 structure."""
    today = datetime.now(tz=timezone.utc).date().isoformat()
    return {
        "format_version": FORMAT_VERSION,
        "subject": v1.get("subject", "Unknown"),
        "created": v1.get("date", today),
        "last_updated": today,
        "clinical_core": {
            "locked": True,
            "source": v1.get("source", ""),
            "date": v1.get("date", today),
            "notes": v1.get("notes", ""),
            "right_ear": v1["right_ear"],
            "left_ear": v1["left_ear"],
            "classification": v1.get("classification", {}),
        },
        "preference_layer": {
            "version": 1,
            "loudness_growth": {"right_ear": [], "left_ear": []},
            "comfort_ceiling_db_spl": 85,
            "preferred_compression_ratio": 2.0,
            "voice_enhancement_enabled": True,
        },
        "context_map": {"version": 1, "contexts": [], "active_context": ""},
        "haptic_layer": {"version": 1, "strategy": "severity_weighted", "comfort_scale": 1.0, "sound_classes": []},
        "history": {
            "entries": [
                {
                    "version": 1,
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    "author": v1.get("subject", "Unknown"),
                    "change_type": "clinical_audiogram_loaded",
                    "description": "Profile created by wrapping openhear-audiogram-v1 file.",
                    "sha256": hashlib.sha256(
                        json.dumps(v1, sort_keys=True).encode()
                    ).hexdigest(),
                    "layers_changed": ["clinical_core"],
                }
            ]
        },
        "sovereignty_notice": (
            f"This profile is the personal data of {v1.get('subject', 'the subject')}. "
            "Licensed Apache 2.0 + Sovereign Use Addendum."
        ),
    }


def _make_empty_profile(
    subject: str,
    source: str,
    date: str,
    notes: str,
    right_thresholds: list[tuple[int, int]],
    left_thresholds: list[tuple[int, int]],
) -> dict[str, Any]:
    """Build a minimal v2 profile dict from raw threshold lists."""

    def _thresh_list(pairs: list[tuple[int, int]]) -> list[dict]:
        return [{"freq_hz": f, "db_hl": db} for f, db in sorted(pairs)]

    today = datetime.now(tz=timezone.utc).date().isoformat()
    data: dict[str, Any] = {
        "format_version": FORMAT_VERSION,
        "subject": subject,
        "created": date,
        "last_updated": today,
        "clinical_core": {
            "locked": True,
            "source": source,
            "date": date,
            "notes": notes,
            "right_ear": {"symbol": "O", "thresholds": _thresh_list(right_thresholds)},
            "left_ear": {"symbol": "X", "thresholds": _thresh_list(left_thresholds)},
            "classification": {},
        },
        "preference_layer": {
            "version": 1,
            "loudness_growth": {"right_ear": [], "left_ear": []},
            "comfort_ceiling_db_spl": 85,
            "preferred_compression_ratio": 2.0,
            "voice_enhancement_enabled": True,
        },
        "context_map": {"version": 1, "contexts": [], "active_context": ""},
        "haptic_layer": {
            "version": 1,
            "strategy": "severity_weighted",
            "comfort_scale": 1.0,
            "sound_classes": [],
        },
        "history": {"entries": []},
        "sovereignty_notice": (
            f"This profile is the personal data of {subject}. "
            "Licensed Apache 2.0 + Sovereign Use Addendum."
        ),
    }
    return data
