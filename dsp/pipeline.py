"""
pipeline.py – real-time audio processing loop for OpenHear.

Reads audio from the system microphone, passes it through the DSP chain
(noise reduction → WDRC compression → voice clarity emphasis → feedback
cancellation → own-voice bypass), and writes the processed audio to the
system output device (which should be mapped to the Bluetooth audio
streamer by the OS).

    Processing chain (all stages optional via dsp/config.py):
        Microphone input
        → SpectralSubtractor  (noise_reduction.py)
        → WDRCompressor       (compression.py)
        → VoiceClarityEnhancer (voice_clarity.py)
        → FeedbackCanceller   (feedback_canceller.py)
        → OwnVoiceBypass      (own_voice_bypass.py)
        → Bluetooth output

Latency budget:
    FRAMES_PER_BUFFER = 256 samples @ 16 000 Hz ≈ 16 ms per block.
    Total target: < 20 ms (hardware I/O buffers add overhead).

CLI:
    python -m dsp.pipeline               # live processing
    python -m dsp.pipeline --bypass      # passthrough only (for A/B)
    python -m dsp.pipeline --test-tone   # 1 kHz tone instead of microphone
    python -m dsp.pipeline --latency     # measure & log per-block latency
    python -m dsp.pipeline --audiogram PATH  # load audiogram and tune DSP

Press Ctrl+C to stop.
"""

import argparse
import json
import logging
import sys
import time

import numpy as np
import pyaudio

from dsp import config
from dsp.audiogram_profile import Prescription, prescribe
from dsp.compression import WDRCompressor
from dsp.feedback_canceller import FeedbackCanceller
from dsp.noise_reduction import SpectralSubtractor
from dsp.occlusion_reduction import OcclusionReducer
from dsp.output_limiter import PeakLimiter
from dsp.own_voice_bypass import OwnVoiceBypass
from dsp.voice_clarity import VoiceClarityEnhancer

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Derived constant: bytes per buffer frame for int16 mono input.
_BYTES_PER_FRAME = config.FRAMES_PER_BUFFER * config.SAMPLE_FORMAT_WIDTH_BYTES


def _bytes_to_float32(raw: bytes) -> np.ndarray:
    """Convert raw int16 PCM bytes to normalised float32 [-1.0, 1.0]."""
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    samples /= 32768.0
    return samples


def _float32_to_bytes(samples: np.ndarray, channels: int) -> bytes:
    """Convert normalised float32 samples to int16 PCM bytes.

    If *channels* > 1 the mono signal is duplicated to fill all channels
    (interleaved layout expected by PyAudio).
    """
    clipped = np.clip(samples, -1.0, 1.0)
    int16 = (clipped * 32767).astype(np.int16)
    if channels > 1:
        int16 = np.repeat(int16, channels)
    return int16.tobytes()


def generate_test_tone(
    frame_count: int,
    sample_rate: int,
    frequency_hz: float = 1000.0,
    amplitude: float = 0.2,
    phase: float = 0.0,
) -> tuple[np.ndarray, float]:
    """Synthesise a sine-wave test tone block.

    Args:
        frame_count: Number of samples in the block.
        sample_rate: Sample rate in Hz.
        frequency_hz: Tone frequency.
        amplitude: Linear amplitude (0.0–1.0).
        phase: Starting phase (radians).  Used so successive blocks join
            without a discontinuity.

    Returns:
        A tuple ``(samples, next_phase)`` where ``next_phase`` should be
        passed back in for the following block.
    """
    t = (np.arange(frame_count, dtype=np.float64) / sample_rate)
    samples = amplitude * np.sin(2.0 * np.pi * frequency_hz * t + phase)
    next_phase = (phase + 2.0 * np.pi * frequency_hz * frame_count / sample_rate) % (2.0 * np.pi)
    return samples.astype(np.float32), float(next_phase)


def _load_prescription(audiogram_path: str) -> Prescription:
    """Load an audiogram JSON file and compute a DSP prescription.

    Sovereignty note: the audiogram is loaded locally, no cloud call is made.
    The prescription values are logged so the user can inspect exactly which
    parameters will drive the DSP chain.

    Args:
        audiogram_path: Path to an openhear-audiogram-v1 JSON file.

    Returns:
        A :class:`~dsp.audiogram_profile.Prescription` with per-ear, per-band
        insertion gains and WDRC compression parameters.
    """
    from audiogram.audiogram import Audiogram

    with open(audiogram_path, encoding="utf-8") as fh:
        data = json.load(fh)

    audiogram = Audiogram.from_dict(data)
    prescription = prescribe(audiogram)
    logger.info("Audiogram loaded: %s", audiogram_path)
    logger.info("Prescription method: %s", prescription.method)

    for ear in ("right", "left"):
        gains = prescription.gains_db(ear)
        ratios = prescription.ratios(ear)
        knees = prescription.knees_dbfs(ear)
        logger.info(
            "Prescription (%s ear) — gains_db=%s  ratios=%s  knees_dbfs=%s",
            ear,
            {k: round(v, 1) for k, v in gains.items()},
            {k: round(v, 2) for k, v in ratios.items()},
            {k: round(v, 1) for k, v in knees.items()},
        )

    return prescription


def _mean_prescription_values(
    prescription: Prescription,
) -> tuple[float, float, float]:
    """Derive mean ratio, knee, and speech-band gain from a bilateral prescription.

    For mono output the left and right ear values are averaged to produce a
    single set of compressor parameters.  The speech-band gain is the mean
    gain across the 1000–4000 Hz octave bands — the frequency range most
    critical for speech understanding.

    Returns:
        ``(ratio, knee_dbfs, speech_gain_db)`` — all floats.
    """
    speech_freqs = {1000, 2000, 4000}

    all_ratios: list[float] = []
    all_knees: list[float] = []
    speech_gains: list[float] = []

    for ear in ("right", "left"):
        all_ratios.extend(prescription.ratios(ear).values())
        all_knees.extend(prescription.knees_dbfs(ear).values())
        for freq, gain in prescription.gains_db(ear).items():
            if freq in speech_freqs:
                speech_gains.append(gain)

    ratio = sum(all_ratios) / len(all_ratios) if all_ratios else config.COMPRESSION_RATIO
    knee = sum(all_knees) / len(all_knees) if all_knees else config.COMPRESSION_KNEE_DBFS
    speech_gain = (
        sum(speech_gains) / len(speech_gains) if speech_gains else config.VOICE_CLARITY_GAIN
    )
    return ratio, knee, speech_gain


def build_dsp_chain(prescription: "Prescription | None" = None) -> list:
    """Construct and return the ordered list of active DSP processors.

    Args:
        prescription: Optional :class:`~dsp.audiogram_profile.Prescription`
            produced by :func:`~dsp.audiogram_profile.prescribe`.  When
            provided, the compressor ratio/knee and the voice-clarity gain are
            derived from the individual's audiogram rather than the static
            config defaults.  The mean of left and right ear values is used
            for the mono output path; the specific values chosen are logged so
            the user can inspect them (sovereignty requirement).
            When ``None``, the static ``dsp/config.py`` defaults are used and
            behaviour is identical to before this parameter was added.
    """
    chain = []

    if config.OCCLUSION_REDUCTION_ENABLED:
        chain.append(OcclusionReducer(
            sample_rate=config.SAMPLE_RATE,
            corner_hz=config.OCCLUSION_REDUCTION_CORNER_HZ,
            slope_db_oct=config.OCCLUSION_REDUCTION_SLOPE_DB_OCT,
        ))
        logger.info(
            "Stage added: OcclusionReducer (corner=%.0f Hz, slope=%.0f dB/oct)",
            config.OCCLUSION_REDUCTION_CORNER_HZ,
            config.OCCLUSION_REDUCTION_SLOPE_DB_OCT,
        )

    # Derive compressor and voice-clarity parameters.  When a prescription is
    # present, use the mean of both ears (appropriate for a mono output path);
    # otherwise fall back to the static config defaults.
    if prescription is not None:
        rx_ratio, rx_knee, rx_speech_gain = _mean_prescription_values(prescription)
        logger.info(
            "Audiogram prescription applied; compressor and voice-clarity "
            "parameters set from user profile (mean of both ears)"
        )
        comp_ratio = rx_ratio
        comp_knee = rx_knee
        voice_gain = rx_speech_gain
    else:
        comp_ratio = config.COMPRESSION_RATIO
        comp_knee = config.COMPRESSION_KNEE_DBFS
        voice_gain = config.VOICE_CLARITY_GAIN

    if config.NOISE_REDUCTION_ENABLED:
        chain.append(SpectralSubtractor(
            frame_length=config.FRAMES_PER_BUFFER,
            noise_floor_multiplier=config.NOISE_FLOOR_MULTIPLIER,
            spectral_floor=config.SPECTRAL_FLOOR,
            noise_estimation_frames=config.NOISE_ESTIMATION_FRAMES,
        ))
        logger.info("Stage added: SpectralSubtractor")

    if config.COMPRESSION_ENABLED:
        chain.append(WDRCompressor(
            sample_rate=config.SAMPLE_RATE,
            ratio=comp_ratio,
            knee_dbfs=comp_knee,
            attack_s=config.COMPRESSION_ATTACK_S,
            release_s=config.COMPRESSION_RELEASE_S,
        ))
        logger.info("Stage added: WDRCompressor")

    if config.VOICE_CLARITY_ENABLED:
        chain.append(VoiceClarityEnhancer(
            frame_length=config.FRAMES_PER_BUFFER,
            sample_rate=config.SAMPLE_RATE,
            low_hz=config.VOICE_CLARITY_LOW_HZ,
            high_hz=config.VOICE_CLARITY_HIGH_HZ,
            gain=voice_gain,
        ))
        logger.info("Stage added: VoiceClarityEnhancer (%.0f–%.0f Hz)",
                    config.VOICE_CLARITY_LOW_HZ, config.VOICE_CLARITY_HIGH_HZ)

    if config.FEEDBACK_CANCELLATION_ENABLED:
        chain.append(FeedbackCanceller(
            filter_length=config.FEEDBACK_FILTER_LENGTH,
            mu=config.FEEDBACK_MU,
            sample_rate=config.SAMPLE_RATE,
            anti_feedback_gain_db=config.ANTI_FEEDBACK_GAIN_DB,
        ))
        logger.info(
            "Stage added: FeedbackCanceller (length=%d, mu=%.4f, gain=%.1f dB)",
            config.FEEDBACK_FILTER_LENGTH,
            config.FEEDBACK_MU,
            config.ANTI_FEEDBACK_GAIN_DB,
        )

    if config.OWN_VOICE_BYPASS_ENABLED:
        chain.append(OwnVoiceBypass(
            sample_rate=config.SAMPLE_RATE,
            f0_low_hz=config.OWN_VOICE_F0_LOW_HZ,
            f0_high_hz=config.OWN_VOICE_F0_HIGH_HZ,
            energy_threshold_dbfs=config.OWN_VOICE_ENERGY_THRESHOLD_DBFS,
            bypass_gain=config.OWN_VOICE_BYPASS_GAIN,
        ))
        logger.info(
            "Stage added: OwnVoiceBypass (F0 %.0f–%.0f Hz, threshold=%.1f dBFS, gain=%.2f)",
            config.OWN_VOICE_F0_LOW_HZ,
            config.OWN_VOICE_F0_HIGH_HZ,
            config.OWN_VOICE_ENERGY_THRESHOLD_DBFS,
            config.OWN_VOICE_BYPASS_GAIN,
        )

    if config.OUTPUT_LIMITER_ENABLED:
        chain.append(PeakLimiter(
            ceiling_dbfs=config.OUTPUT_LIMITER_CEILING_DBFS,
            attack_s=config.OUTPUT_LIMITER_ATTACK_S,
            release_s=config.OUTPUT_LIMITER_RELEASE_S,
            sample_rate=config.SAMPLE_RATE,
        ))
        logger.info(
            "Stage added: PeakLimiter (ceiling=%.1f dBFS, attack=%.0f ms, release=%.0f ms)",
            config.OUTPUT_LIMITER_CEILING_DBFS,
            config.OUTPUT_LIMITER_ATTACK_S * 1000,
            config.OUTPUT_LIMITER_RELEASE_S * 1000,
        )

    if not chain:
        logger.warning("All DSP stages disabled – audio will be passed through unchanged.")

    return chain


def run_pipeline(
    *,
    bypass: bool = False,
    test_tone: bool = False,
    measure_latency: bool = False,
    metrics_path: str | None = None,
    audiogram_path: str | None = None,
) -> None:
    """Open audio streams and run the processing loop until interrupted.

    Args:
        bypass: If ``True``, skip the DSP chain entirely (passthrough).
        test_tone: If ``True``, replace mic input with a 1 kHz sine tone.
        measure_latency: If ``True``, log per-block latency to the
            standard logger every second.
        metrics_path: If set, append per-block metrics to this CSV path
            (see :class:`dsp.metrics.MetricsLogger`).
        audiogram_path: If set, load the audiogram JSON at this path and
            derive DSP parameters from the individual's hearing profile.
            When ``None``, static ``dsp/config.py`` defaults are used.
    """
    pa = pyaudio.PyAudio()

    try:
        if not test_tone:
            input_stream = pa.open(
                rate=config.SAMPLE_RATE,
                channels=config.INPUT_CHANNELS,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=config.FRAMES_PER_BUFFER,
                input_device_index=config.INPUT_DEVICE_INDEX,
            )
        else:
            input_stream = None
        output_stream = pa.open(
            rate=config.SAMPLE_RATE,
            channels=config.OUTPUT_CHANNELS,
            format=pyaudio.paInt16,
            output=True,
            frames_per_buffer=config.FRAMES_PER_BUFFER,
            output_device_index=config.OUTPUT_DEVICE_INDEX,
        )
    except OSError as exc:
        logger.error("Failed to open audio device: %s", exc)
        pa.terminate()
        sys.exit(1)

    dsp_chain = [] if bypass else build_dsp_chain(
        prescription=_load_prescription(audiogram_path) if audiogram_path else None,
    )
    if bypass:
        logger.info("Bypass mode: DSP chain skipped.")
    if test_tone:
        logger.info("Test-tone mode: synthesising 1 kHz sine instead of mic input.")
    logger.info(
        "Pipeline running — %d Hz, %d frames/buffer (~%.1f ms latency). "
        "Press Ctrl+C to stop.",
        config.SAMPLE_RATE,
        config.FRAMES_PER_BUFFER,
        config.FRAMES_PER_BUFFER / config.SAMPLE_RATE * 1000,
    )

    metrics_logger = None
    if metrics_path is not None:
        from dsp.metrics import MetricsLogger
        metrics_logger = MetricsLogger(path=metrics_path).open()

    last_latency_log = time.monotonic()
    tone_phase = 0.0
    try:
        while True:
            block_start = time.perf_counter()
            if test_tone:
                samples, tone_phase = generate_test_tone(
                    config.FRAMES_PER_BUFFER, config.SAMPLE_RATE, phase=tone_phase,
                )
            else:
                raw = input_stream.read(
                    config.FRAMES_PER_BUFFER, exception_on_overflow=False
                )
                samples = _bytes_to_float32(raw)

            for stage in dsp_chain:
                samples = stage.process(samples)

            output_stream.write(_float32_to_bytes(samples, config.OUTPUT_CHANNELS))
            block_seconds_processed = time.perf_counter() - block_start

            if metrics_logger is not None:
                metrics_logger.log_block(
                    block_samples=config.FRAMES_PER_BUFFER,
                    sample_rate=config.SAMPLE_RATE,
                    process_seconds=block_seconds_processed,
                    samples=samples,
                )

            if measure_latency and (time.monotonic() - last_latency_log) >= 1.0:
                latency_ms = block_seconds_processed * 1000.0
                logger.info(
                    "latency=%.2f ms  (block=%.1f ms budget)",
                    latency_ms,
                    config.FRAMES_PER_BUFFER / config.SAMPLE_RATE * 1000.0,
                )
                last_latency_log = time.monotonic()

    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user.")
    finally:
        if input_stream is not None:
            input_stream.stop_stream()
            input_stream.close()
        output_stream.stop_stream()
        output_stream.close()
        pa.terminate()
        if metrics_logger is not None:
            metrics_logger.close()


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the OpenHear real-time DSP pipeline.",
    )
    parser.add_argument(
        "--bypass", action="store_true",
        help="Skip the DSP chain (passthrough).  Useful for A/B testing.",
    )
    parser.add_argument(
        "--test-tone", action="store_true",
        help="Synthesise a 1 kHz sine wave instead of reading the mic. "
             "Useful when no microphone is available.",
    )
    parser.add_argument(
        "--latency", action="store_true",
        help="Log per-block latency once per second.",
    )
    parser.add_argument(
        "--metrics-csv", default=None,
        help="Append per-block latency/CPU/level metrics to this CSV file.",
    )
    parser.add_argument(
        "--audiogram", default=None, metavar="PATH",
        help="Path to an openhear-audiogram-v1 JSON file.  When provided, "
             "compression ratio/knee and voice-clarity gain are derived from "
             "the individual's audiogram rather than the static config defaults.",
    )
    return parser


if __name__ == "__main__":
    args = _build_arg_parser().parse_args()
    run_pipeline(
        bypass=args.bypass,
        test_tone=args.test_tone,
        measure_latency=args.latency,
        metrics_path=args.metrics_csv,
        audiogram_path=args.audiogram,
    )

