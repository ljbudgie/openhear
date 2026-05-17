"""Vendor-specific Noahlink adapters.

Each module under :mod:`core.noahlink.vendors` exposes a single
``read_extraction`` entry point (and possibly ``WRITE_SUPPORTED``
flags) so the CLI can dispatch by ``--aid <vendor>``.

All adapters in this PR are **read-only mock implementations**.  Real
vendor protocols (Phonak Marvel/Lumity/Infinio, Signia AX, ReSound,
Oticon, Widex) are proprietary; OpenHear will not ship write paths
that have not been validated against the corresponding hardware.
"""

from __future__ import annotations

from core.noahlink.vendors.phonak import PhonakMockAdapter
from core.noahlink.vendors.phonak import read_extraction as read_phonak

__all__ = ["PhonakMockAdapter", "read_phonak", "available_adapters"]


def available_adapters() -> dict[str, str]:
    """Return a mapping ``{vendor_id: description}`` for CLI listing."""
    return {
        "phonak": (
            "Phonak (Marvel/Lumity/Infinio) — MOCK ADAPTER, read-only, "
            "unverified against real hardware."
        ),
    }
