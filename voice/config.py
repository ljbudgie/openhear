"""
config.py – user-tunable parameters for the OpenHear voice analysis module.

All constants in this file are plain Python values — no classes, no
environment variables, no config files.  Open, read, change, save, restart.

To customise your voice analysis:
  1. Open this file in any text editor.
  2. Change the value you want.
  3. Save and restart the analyser.
"""

# ── Audio I/O ─────────────────────────────────────────────────────────────────

# PyAudio device index for the microphone input.
# None = use system default input device.
MIC_DEVICE_INDEX = None

# Audio sample rate in Hz.
# 44 100 Hz is used here (not the 16 000 Hz pipeline rate) because vocal
# frequency analysis benefits from full-bandwidth capture — formant detail
# above 8 kHz matters for sibilance and breathiness.
SAMPLE_RATE: int = 44100

# Frames per buffer (chunk size).
# 1024 frames at 44 100 Hz ≈ 23 ms — fast enough for real-time visual
# feedback without excessive CPU load.
FRAME_BUFFER: int = 1024


# ── Reference Profile ────────────────────────────────────────────────────────

# Bandpass filter range (Hz) used to isolate vocal frequencies when
# loading a reference recording.  80 Hz captures the lowest male
# fundamental; 8 000 Hz captures sibilance and breathiness.
REFERENCE_BANDPASS: tuple = (80, 8000)


# ── Formant Detection ────────────────────────────────────────────────────────

# Number of formant peaks to extract from the spectral envelope.
# F1, F2, F3 are the standard speech formants; increase if you want F4+.
FORMANT_PEAKS: int = 3


# ── Comparison Thresholds ────────────────────────────────────────────────────

# Tolerance in dB for considering a frequency band as "matched" between
# the user's voice and the reference profile.  ±3 dB is the just-
# noticeable difference for most listeners.
MATCH_TOLERANCE_DB: float = 3.0

# Gap threshold in dB.  If the user's energy in a frequency band is more
# than this many dB below the reference, the feedback display highlights
# it as a significant gap.
GAP_THRESHOLD_DB: float = 6.0
