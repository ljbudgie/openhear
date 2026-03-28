"""
pipeline.py – real-time audio processing loop for OpenHear.

Reads audio from the system microphone, passes it through the DSP chain
(noise reduction → WDRC compression → voice clarity emphasis), and writes
the processed audio to the system output device (which should be mapped to
the Bluetooth audio streamer by the OS).

Processing chain (all stages optional via dsp/config.py):
    Microphone input
        → SpectralSubtractor  (noise_reduction.py)
        → WDRCompressor       (compression.py)
        → VoiceClarityEnhancer (voice_clarity.py)
        → Bluetooth output

Latency budget:
    FRAMES_PER_BUFFER = 256 samples @ 16 000 Hz ≈ 16 ms per block.
    Total target: < 20 ms (hardware I/O buffers add overhead).

Usage:
    python -m dsp.pipeline

Press Ctrl+C to stop.
"""

import logging
import struct
import sys

import numpy as np
import pyaudio

from dsp import config
from dsp.compression import WDRCompressor
from dsp.noise_reduction import SpectralSubtractor
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


def build_dsp_chain() -> list:
    """Construct and return the ordered list of active DSP processors."""
    chain = []

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
            ratio=config.COMPRESSION_RATIO,
            knee_dbfs=config.COMPRESSION_KNEE_DBFS,
            attack_s=config.COMPRESSION_ATTACK_S,
            release_s=config.COMPRESSION_RELEASE_S,
        ))
        logger.info("Stage added: WDRCompressor (ratio=%.1f, knee=%.0f dBFS)",
                    config.COMPRESSION_RATIO, config.COMPRESSION_KNEE_DBFS)

    if config.VOICE_CLARITY_ENABLED:
        chain.append(VoiceClarityEnhancer(
            frame_length=config.FRAMES_PER_BUFFER,
            sample_rate=config.SAMPLE_RATE,
            low_hz=config.VOICE_CLARITY_LOW_HZ,
            high_hz=config.VOICE_CLARITY_HIGH_HZ,
            gain=config.VOICE_CLARITY_GAIN,
        ))
        logger.info("Stage added: VoiceClarityEnhancer (%.0f–%.0f Hz, gain=%.2f)",
                    config.VOICE_CLARITY_LOW_HZ, config.VOICE_CLARITY_HIGH_HZ,
                    config.VOICE_CLARITY_GAIN)

    if not chain:
        logger.warning("All DSP stages disabled – audio will be passed through unchanged.")

    return chain


def run_pipeline() -> None:
    """Open audio streams and run the processing loop until interrupted."""
    pa = pyaudio.PyAudio()

    try:
        input_stream = pa.open(
            rate=config.SAMPLE_RATE,
            channels=config.INPUT_CHANNELS,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=config.FRAMES_PER_BUFFER,
            input_device_index=config.INPUT_DEVICE_INDEX,
        )
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

    dsp_chain = build_dsp_chain()
    logger.info(
        "Pipeline running — %d Hz, %d frames/buffer (~%.1f ms latency). "
        "Press Ctrl+C to stop.",
        config.SAMPLE_RATE,
        config.FRAMES_PER_BUFFER,
        config.FRAMES_PER_BUFFER / config.SAMPLE_RATE * 1000,
    )

    try:
        while True:
            raw = input_stream.read(
                config.FRAMES_PER_BUFFER, exception_on_overflow=False
            )
            samples = _bytes_to_float32(raw)

            for stage in dsp_chain:
                samples = stage.process(samples)

            output_stream.write(_float32_to_bytes(samples, config.OUTPUT_CHANNELS))

    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user.")
    finally:
        input_stream.stop_stream()
        input_stream.close()
        output_stream.stop_stream()
        output_stream.close()
        pa.terminate()


if __name__ == "__main__":
    run_pipeline()
