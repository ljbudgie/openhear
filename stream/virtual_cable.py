"""
virtual_cable.py – detect and target virtual audio cable devices.

Many users route OpenHear audio between processes (e.g. teleconference
input, OBS, pipewire bridges) via a *virtual audio cable* — a kernel
driver that creates a paired Output / Input device.  The most common
implementations on each platform are:

* Windows: **VB-Audio Virtual Cable** (and the multi-cable VoiceMeeter
  Banana / Potato variants).
* macOS: **BlackHole** and **Loopback** (Rogue Amoeba).
* Linux: PulseAudio / PipeWire **null-sink + monitor** combinations
  (typically ``OpenHear-virtual.monitor`` or similar).

Rather than try to drive the cable itself, this module just *finds*
the matching PyAudio device indices so the rest of the pipeline can
use them as input or output devices.

CLI::

    python -m stream.virtual_cable --list
    python -m stream.virtual_cable --best output
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from typing import Iterable

import pyaudio

logger = logging.getLogger(__name__)


# Substrings that uniquely identify common virtual-cable products.
# Matching is case-insensitive substring.
VIRTUAL_CABLE_HINTS: tuple[str, ...] = (
    "vb-audio",
    "vb-cable",
    "voicemeeter",
    "blackhole",
    "loopback",
    "soundflower",
    "virtual cable",
    "null sink",
    "null-sink",
    ".monitor",     # PulseAudio/PipeWire monitor sources
    "openhear",     # any user-named OpenHear bridge
)


@dataclass(frozen=True)
class VirtualCable:
    """A single virtual-cable endpoint discovered on the host.

    Attributes:
        index: PyAudio device index.
        name: Device name as reported by PortAudio.
        direction: ``"input"`` or ``"output"``.
        sample_rate: Default sample rate reported by the driver.
    """

    index: int
    name: str
    direction: str
    sample_rate: float


def _is_virtual(name: str) -> bool:
    lower = name.lower()
    return any(hint in lower for hint in VIRTUAL_CABLE_HINTS)


def detect_virtual_cables(pa: pyaudio.PyAudio | None = None) -> list[VirtualCable]:
    """Enumerate all virtual-cable input and output devices on this host.

    Args:
        pa: Optional :class:`pyaudio.PyAudio` to reuse.  If ``None``, a
            fresh instance is created and terminated locally.

    Returns:
        List of :class:`VirtualCable` records (may be empty).
    """
    owns_pa = pa is None
    pa = pa or pyaudio.PyAudio()
    found: list[VirtualCable] = []
    try:
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            name = str(info.get("name", ""))
            if not _is_virtual(name):
                continue
            sr = float(info.get("defaultSampleRate", 0))
            if int(info.get("maxOutputChannels", 0)) > 0:
                found.append(VirtualCable(i, name, "output", sr))
            if int(info.get("maxInputChannels", 0)) > 0:
                found.append(VirtualCable(i, name, "input", sr))
    finally:
        if owns_pa:
            pa.terminate()
    return found


def best_virtual_cable(
    direction: str,
    cables: Iterable[VirtualCable] | None = None,
) -> VirtualCable | None:
    """Return the most likely virtual cable for *direction*, or ``None``.

    Selection prefers VB-Cable/BlackHole over PulseAudio monitor sources
    (which are usually loopbacks, not true cables).

    Args:
        direction: ``"input"`` or ``"output"``.
        cables: Optional pre-detected list (used by tests).

    Returns:
        The first matching :class:`VirtualCable`, or ``None`` if none
        of the detected devices match the requested direction.
    """
    if direction not in ("input", "output"):
        raise ValueError(f"direction must be 'input' or 'output', got {direction!r}")
    items = list(cables) if cables is not None else detect_virtual_cables()
    candidates = [c for c in items if c.direction == direction]
    if not candidates:
        return None

    def _rank(cable: VirtualCable) -> int:
        # Lower rank = more preferred.
        lower = cable.name.lower()
        if "vb-cable" in lower or "vb-audio" in lower:
            return 0
        if "blackhole" in lower or "loopback" in lower:
            return 1
        if "voicemeeter" in lower:
            return 2
        if "openhear" in lower:
            return 3
        return 9

    candidates.sort(key=_rank)
    return candidates[0]


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: list cables or pick the best one for I/O."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(
        description="Detect virtual audio cables (VB-Cable, BlackHole, …).",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--list", action="store_true",
        help="Print every detected virtual-cable endpoint.",
    )
    group.add_argument(
        "--best", choices=("input", "output"),
        help="Print the index of the recommended cable for the given direction.",
    )
    args = parser.parse_args(argv)

    cables = detect_virtual_cables()

    if args.list:
        if not cables:
            print(
                "No virtual audio cables detected.  "
                "Install VB-Cable (Windows), BlackHole (macOS), or set up a "
                "PulseAudio/PipeWire null sink (Linux)."
            )
            return 0
        print(f"{'Index':<6} {'Direction':<8} {'SR':>8}  Name")
        print("-" * 70)
        for c in cables:
            print(f"{c.index:<6} {c.direction:<8} {int(c.sample_rate):>8}  {c.name}")
        return 0

    pick = best_virtual_cable(args.best, cables)
    if pick is None:
        print(f"No virtual {args.best} cable detected.", file=sys.stderr)
        return 1
    print(pick.index)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
