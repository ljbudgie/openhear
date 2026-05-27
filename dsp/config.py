"""
config.py – user-tunable DSP parameters for the OpenHear pipeline.

All constants in this file are intentionally kept as plain Python values
(no classes, no environment variables, no config files) so that users can
read and tweak them in a single glance.  Comments explain the purpose and
acceptable range of every parameter.

To customise your pipeline:
  1. Open this file in any text editor.
  2. Change the value you want.
  3. Save and restart the pipeline (`python -m dsp.pipeline`).

DO NOT hardcode audiogram values here.  Per-ear gain is loaded at runtime
from the fitting profile read by core/read_fitting.py.
"""

# ── Audio I/O ─────────────────────────────────────────────────────────────────

# Audio sample rate in Hz.
# 16 000 Hz is sufficient for speech intelligibility and keeps FFT size small
# enough to meet the <20 ms latency budget.  Use 44 100 or 48 000 if music
# quality matters more than latency.
SAMPLE_RATE: int = 16_000

# Number of audio channels captured from the microphone.
# 1 = mono (recommended for speech processing).
INPUT_CHANNELS: int = 1

# Number of audio channels sent to the Bluetooth output stream.
# Most hearing aid streamers present as stereo; use 2 here.
OUTPUT_CHANNELS: int = 2

# PyAudio sample format.  16-bit signed integer gives 96 dB dynamic range,
# which is adequate for hearing aid applications.
# Corresponds to pyaudio.paInt16.
SAMPLE_FORMAT_WIDTH_BYTES: int = 2  # 2 bytes = 16-bit

# Frames per buffer (chunk size).
# At 16 000 Hz, 256 frames ≈ 16 ms — under the 20 ms latency target.
# Increasing this reduces CPU load but raises latency.
FRAMES_PER_BUFFER: int = 256

# PyAudio device index for the microphone input.
# None = use system default input device.
INPUT_DEVICE_INDEX = None

# PyAudio device index for the audio output (sent to Bluetooth streamer).
# None = use system default output device.
OUTPUT_DEVICE_INDEX = None


# ── Wide Dynamic Range Compression (WDRC) ────────────────────────────────────

# Enable / disable WDRC stage.
COMPRESSION_ENABLED: bool = True

# Compression ratio applied above the knee point (linear, input:output).
# 1.0 = no compression; 2.0 = 2:1 (mild); 4.0 = 4:1 (moderate).
COMPRESSION_RATIO: float = 2.0

# Input level (dBFS) at which compression starts engaging (knee point).
# Signals below this threshold are amplified linearly.
# Typical hearing aid range: -60 to -30 dBFS (use more negative for louder knee).
COMPRESSION_KNEE_DBFS: float = -40.0

# Attack time in seconds (how quickly the compressor responds to a loud sound).
# Shorter = snappier response; recommended range 0.001 – 0.020 s.
COMPRESSION_ATTACK_S: float = 0.005

# Release time in seconds (how quickly gain recovers after a loud sound).
# Shorter = faster recovery; recommended range 0.020 – 0.200 s.
COMPRESSION_RELEASE_S: float = 0.060


# ── Spectral-Subtraction Noise Reduction ────────────────────────────────────

# Enable / disable noise reduction stage.
NOISE_REDUCTION_ENABLED: bool = True

# Noise floor threshold as a linear spectral magnitude multiplier.
# The estimated noise spectrum is multiplied by this value before subtraction,
# providing a safety margin above the true noise floor.
# 1.0 = subtract exactly estimated noise; 1.5 = 50% over-subtraction
# (more aggressive reduction but may introduce musical noise artefacts).
NOISE_FLOOR_MULTIPLIER: float = 1.2

# Spectral floor: minimum fraction of the original magnitude to retain after
# subtraction, preventing over-subtraction artefacts (musical noise).
# Range: 0.0 – 1.0; typical: 0.05 – 0.15.
SPECTRAL_FLOOR: float = 0.10

# Number of initial frames used to estimate the background noise profile.
# At FRAMES_PER_BUFFER=256 and SAMPLE_RATE=16000, 8 frames ≈ 128 ms of
# noise-only signal captured before speech begins.
NOISE_ESTIMATION_FRAMES: int = 8


# ── Voice Clarity (Speech Frequency Emphasis) ────────────────────────────────

# Enable / disable voice clarity stage.
VOICE_CLARITY_ENABLED: bool = True

# Lower bound of the speech emphasis band in Hz.
VOICE_CLARITY_LOW_HZ: float = 1000.0

# Upper bound of the speech emphasis band in Hz.
VOICE_CLARITY_HIGH_HZ: float = 4000.0

# Gain boost applied within the speech band (linear multiplier).
# 1.0 = flat; 1.5 = +3.5 dB; 2.0 = +6 dB.
# Keep below 3.0 to avoid loudness discomfort.
VOICE_CLARITY_GAIN: float = 1.6


# ── Feedback Cancellation (LMS Adaptive Filter) ────────────────────────────

# Enable / disable adaptive feedback cancellation.
FEEDBACK_CANCELLATION_ENABLED: bool = True

# Length of the LMS adaptive filter in samples.
# Longer filters model longer feedback paths but require more CPU.
# Typical range: 64 – 256 samples.
FEEDBACK_FILTER_LENGTH: int = 128

# LMS step size (learning rate).
# Smaller = more stable but slower adaptation; larger = faster but risk divergence.
# Typical range: 0.001 – 0.05.
FEEDBACK_MU: float = 0.01

# Additional gain reduction (dB) applied in the feedback frequency region.
# Reduces loop gain to prevent oscillation.  0 = no extra attenuation.
ANTI_FEEDBACK_GAIN_DB: float = -6.0


# ── Own-Voice Detection & Bypass ────────────────────────────────────────────

# Enable / disable own-voice detection bypass.
OWN_VOICE_BYPASS_ENABLED: bool = True

# Fundamental frequency range for own-voice detection (Hz).
# Human speech fundamental typically falls within 80–300 Hz.
OWN_VOICE_F0_LOW_HZ: float = 80.0
OWN_VOICE_F0_HIGH_HZ: float = 300.0

# RMS energy threshold (dBFS) above which the signal may be classified as own voice.
# Own voice is typically louder than external sounds due to bone conduction.
OWN_VOICE_ENERGY_THRESHOLD_DBFS: float = -20.0

# Gain multiplier applied to DSP output when own voice is detected.
# 1.0 = no change; 0.5 = halve the DSP effect (more natural own voice).
OWN_VOICE_BYPASS_GAIN: float = 0.5


# ── Occlusion Reduction ────────────────────────────────────────────────────

# Enable / disable occlusion reduction (low-frequency attenuation for ITE shells).
OCCLUSION_REDUCTION_ENABLED: bool = False

# High-pass corner frequency (Hz) for occlusion reduction.
# Reduces the boomy low-frequency buildup caused by a sealed ear canal.
# Typical range: 200 – 500 Hz.
OCCLUSION_REDUCTION_CORNER_HZ: float = 300.0

# Attenuation slope (dB/octave) below the corner frequency.
# Steeper = more aggressive occlusion reduction.
# Typical range: 6 – 18 dB/octave.
OCCLUSION_REDUCTION_SLOPE_DB_OCT: float = 12.0


# ── Logging ─────────────────────────────────────────────────────────────────

# Python logging level for the DSP pipeline.
# Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR'.
LOG_LEVEL: str = "INFO"
