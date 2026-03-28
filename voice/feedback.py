"""
feedback.py – terminal-based real-time visual feedback for OpenHear.

Renders a live-updating frequency spectrum in the terminal using unicode
block characters.  The user's voice energy is shown alongside a reference
profile target line so they can see — in real time — where their vocal
energy matches the reference and where the gaps are.

Colour coding:
  - Green: user energy is within MATCH_TOLERANCE_DB of the reference.
  - Red:   user energy is more than GAP_THRESHOLD_DB below the reference.
  - Default: everything in between.

This is a training display, not a performance meter.  The goal is to give
the brain a consistent, accurate visual feedback loop so it can develop
vocal control in frequency ranges that were previously inaccessible due to
sensorineural hearing loss.

Terminal requirements:
  - Unicode support (any modern terminal: Windows Terminal, iTerm2, GNOME
    Terminal, etc.).
  - Minimum 80 columns wide for readable output.
"""

from __future__ import annotations

import sys
import time

import numpy as np

from voice import config
from voice.analyser import VoiceSnapshot
from voice.compare import VoiceComparison


# ── ANSI colour codes ────────────────────────────────────────────────────────

_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

# Unicode block characters for bar rendering (increasing fill).
_BLOCKS = " ▏▎▍▌▋▊▉█"


# ── Rendering helpers ────────────────────────────────────────────────────────

def _bar(value_db: float, ref_db: float, max_db: float,
         bar_width: int, match_tol: float, gap_thr: float) -> str:
    """Render a single spectrum bar with colour coding.

    Args:
        value_db:  User's energy in this bin (dB).
        ref_db:    Reference energy in this bin (dB).
        max_db:    Maximum dB value for full-scale display.
        bar_width: Maximum character width of the bar.
        match_tol: Match tolerance in dB (green zone).
        gap_thr:   Gap threshold in dB (red zone).

    Returns:
        A coloured unicode string representing the bar.
    """
    # Normalise value to [0, 1] range for display.
    normalised = max(0.0, min(1.0, (value_db + 100.0) / (max_db + 100.0)))
    fill = normalised * bar_width

    full_blocks = int(fill)
    fractional = fill - full_blocks
    frac_index = int(fractional * (len(_BLOCKS) - 1))

    bar_str = _BLOCKS[-1] * full_blocks
    if full_blocks < bar_width:
        bar_str += _BLOCKS[frac_index]
        bar_str += " " * (bar_width - full_blocks - 1)

    # Colour based on difference from reference.
    diff = value_db - ref_db
    if abs(diff) <= match_tol:
        return f"{_GREEN}{bar_str}{_RESET}"
    elif diff < -gap_thr:
        return f"{_RED}{bar_str}{_RESET}"
    else:
        return bar_str


def _ref_marker(ref_db: float, max_db: float, bar_width: int) -> int:
    """Return the character column position for the reference marker."""
    normalised = max(0.0, min(1.0, (ref_db + 100.0) / (max_db + 100.0)))
    return int(normalised * bar_width)


def _format_freq(hz: float) -> str:
    """Format a frequency value for display."""
    if hz >= 1000.0:
        return f"{hz / 1000.0:.1f}k"
    return f"{hz:.0f}"


# ── Public API ───────────────────────────────────────────────────────────────

def render_frame(snapshot: VoiceSnapshot,
                 ref_envelope: np.ndarray,
                 comparison: VoiceComparison,
                 sample_rate: int = config.SAMPLE_RATE,
                 frame_size: int = config.FRAME_BUFFER,
                 bar_width: int = 40,
                 n_bands: int = 24,
                 match_tol: float = config.MATCH_TOLERANCE_DB,
                 gap_thr: float = config.GAP_THRESHOLD_DB) -> str:
    """Render one frame of visual feedback as a multi-line string.

    Produces a frequency spectrum display with the user's voice bars,
    reference target markers, and live stats.

    Args:
        snapshot:     Current VoiceSnapshot from the analyser.
        ref_envelope: Reference spectral envelope (dB), or empty array if
                      no reference is loaded.
        comparison:   Current VoiceComparison result.
        sample_rate:  Sample rate used during analysis.
        frame_size:   FFT frame size used during analysis.
        bar_width:    Character width of each spectrum bar.
        n_bands:      Number of frequency bands to display (bins are
                      averaged into bands for readability).
        match_tol:    Match tolerance in dB for green highlighting.
        gap_thr:      Gap threshold in dB for red highlighting.

    Returns:
        A multi-line string ready for terminal output.
    """
    user_env = snapshot.spectral_envelope
    lines: list[str] = []

    # Header with live stats.
    f0_str = (f"{snapshot.fundamental_frequency_hz:.0f} Hz"
              if snapshot.fundamental_frequency_hz > 0 else "—")
    lines.append(
        f"  {_BOLD}F0:{_RESET} {_CYAN}{f0_str}{_RESET}  "
        f"{_BOLD}HNR:{_RESET} {_CYAN}{snapshot.hnr_db:.1f} dB{_RESET}  "
        f"{_BOLD}Similarity:{_RESET} {_CYAN}{comparison.similarity_score:.0%}{_RESET}  "
        f"{_BOLD}Energy:{_RESET} {_CYAN}{snapshot.energy_db:.1f} dBFS{_RESET}"
    )
    lines.append("")

    if len(user_env) == 0:
        lines.append("  (no signal)")
        return "\n".join(lines)

    # Build frequency axis.
    freqs = np.fft.rfftfreq(frame_size, d=1.0 / sample_rate).astype(np.float32)
    n_bins = min(len(user_env), len(freqs))

    # Average bins into display bands.
    band_size = max(1, n_bins // n_bands)
    max_db = float(np.max(user_env[:n_bins])) if n_bins > 0 else 0.0
    if len(ref_envelope) > 0:
        max_db = max(max_db, float(np.max(ref_envelope[:n_bins])))
    max_db = max(max_db, -20.0)  # Floor for display scaling.

    for i in range(n_bands):
        start = i * band_size
        end = min(start + band_size, n_bins)
        if start >= n_bins:
            break

        band_freq = float(freqs[start])
        user_db = float(np.mean(user_env[start:end]))

        ref_db = -100.0
        if len(ref_envelope) >= end:
            ref_db = float(np.mean(ref_envelope[start:end]))

        freq_label = _format_freq(band_freq).rjust(6)
        bar_str = _bar(user_db, ref_db, max_db, bar_width, match_tol, gap_thr)

        # Reference target marker.
        ref_col = _ref_marker(ref_db, max_db, bar_width)
        ref_mark = " " * ref_col + "│" if len(ref_envelope) > 0 and ref_db > -100.0 else ""

        lines.append(f"  {freq_label} Hz {bar_str}  {_YELLOW}{ref_mark}{_RESET}")

    # Legend.
    lines.append("")
    lines.append(
        f"  {_GREEN}██{_RESET} within {match_tol:.0f} dB  "
        f"{_RED}██{_RESET} gap > {gap_thr:.0f} dB  "
        f"{_YELLOW}│{_RESET} reference target"
    )

    return "\n".join(lines)


def run_live(snapshot_generator,
             ref_envelope: np.ndarray,
             comparison_fn,
             refresh_hz: float = 15.0,
             **kwargs) -> None:
    """Run the live feedback display in the terminal.

    This is a blocking loop that clears the screen and re-renders on every
    frame.  Press Ctrl-C to stop.

    Args:
        snapshot_generator: An iterable or generator yielding VoiceSnapshot
                            objects (e.g. a loop calling capture_snapshot).
        ref_envelope:       Reference spectral envelope, or empty array.
        comparison_fn:      A callable(snapshot) -> VoiceComparison.
        refresh_hz:         Target refresh rate in Hz.
        **kwargs:           Passed through to render_frame().
    """
    interval = 1.0 / refresh_hz

    try:
        for snapshot in snapshot_generator:
            comparison = comparison_fn(snapshot)
            frame = render_frame(snapshot, ref_envelope, comparison, **kwargs)

            # Clear screen and move cursor to top-left.
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.write(frame)
            sys.stdout.write("\n")
            sys.stdout.flush()

            time.sleep(interval)
    except KeyboardInterrupt:
        sys.stdout.write(f"\n{_BOLD}Stopped.{_RESET}\n")
        sys.stdout.flush()
