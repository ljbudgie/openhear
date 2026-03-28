"""
bluetooth_output.py – Bluetooth audio streaming to hearing aids.

Streams processed audio to the hearing aids via the Windows system
Bluetooth audio stack.  The strategy for each supported device is:

  Phonak Naída M70-SP (Marvel platform, Bluetooth Classic / A2DP):
    Pairs via Windows Bluetooth settings as a standard A2DP sink.
    Once paired and connected the device appears as a Windows audio
    output device.  Select it by device name or index in dsp/config.py
    (OUTPUT_DEVICE_INDEX).  No proprietary API is needed.

  Signia Insio 7AX (AX platform, Made-for-iPhone / MFi Bluetooth LE):
    MFi devices use Apple's proprietary Bluetooth LE stack and are not
    directly accessible from Windows.  Phase 1 workaround: connect the
    Insio 7AX to an iPhone acting as an audio relay, and share iPhone
    audio to the Windows machine via the iPhone's Bluetooth PAN or a
    virtual audio cable.  Native Windows MFi support is planned for a
    future phase.

Phase 1 implementation:
  BluetoothAudioOutput wraps PyAudio output and adds device enumeration
  helpers so users can identify the correct Windows audio device index
  for their hearing aid streamer.

Usage:
    python -m stream.bluetooth_output --list
    python -m stream.bluetooth_output --device-index 3
"""

import argparse
import logging
import sys

import pyaudio

logger = logging.getLogger(__name__)


def list_output_devices() -> None:
    """Print all available PyAudio output devices to stdout.

    Use this to find the device index for your Bluetooth hearing aid
    streamer and set OUTPUT_DEVICE_INDEX in dsp/config.py.
    """
    pa = pyaudio.PyAudio()
    count = pa.get_device_count()
    print(f"{'Index':<6} {'Name':<50} {'Max Output Ch'}")
    print("-" * 70)
    for i in range(count):
        info = pa.get_device_info_by_index(i)
        if info["maxOutputChannels"] > 0:
            print(f"{i:<6} {info['name'][:48]:<50} {int(info['maxOutputChannels'])}")
    pa.terminate()


class BluetoothAudioOutput:
    """PyAudio output stream targeting a named or indexed Bluetooth device.

    Args:
        sample_rate:   Audio sample rate in Hz (must match the pipeline).
        channels:      Number of output channels (typically 2 for stereo BT).
        frames_per_buffer:
                       Buffer size in frames (should match FRAMES_PER_BUFFER).
        device_index:  PyAudio device index for the target Bluetooth device.
                       Pass None to use the system default output.
        device_name_hint:
                       Optional substring of the device name to search for
                       if *device_index* is None.  The first match is used.
    """

    def __init__(
        self,
        sample_rate: int,
        channels: int = 2,
        frames_per_buffer: int = 256,
        device_index: int | None = None,
        device_name_hint: str | None = None,
    ) -> None:
        self._pa = pyaudio.PyAudio()
        self._sample_rate = sample_rate
        self._channels = channels
        self._frames_per_buffer = frames_per_buffer
        self._stream = None

        resolved_index = device_index
        if resolved_index is None and device_name_hint is not None:
            resolved_index = self._find_device_by_name(device_name_hint)
            if resolved_index is None:
                logger.warning(
                    "Bluetooth device containing '%s' not found; "
                    "falling back to system default output.",
                    device_name_hint,
                )

        self._device_index = resolved_index

    # ------------------------------------------------------------------

    def open(self) -> None:
        """Open the output audio stream."""
        try:
            self._stream = self._pa.open(
                rate=self._sample_rate,
                channels=self._channels,
                format=pyaudio.paInt16,
                output=True,
                frames_per_buffer=self._frames_per_buffer,
                output_device_index=self._device_index,
            )
            logger.info(
                "Bluetooth audio output opened (device_index=%s, %d Hz, %d ch).",
                self._device_index, self._sample_rate, self._channels,
            )
        except OSError as exc:
            raise OSError(
                f"Cannot open Bluetooth output device (index={self._device_index}): {exc}"
            ) from exc

    def write(self, pcm_bytes: bytes) -> None:
        """Write a buffer of int16 PCM bytes to the output stream.

        Args:
            pcm_bytes: Raw interleaved int16 PCM data.  Length must equal
                       frames_per_buffer * channels * 2.
        """
        if self._stream is None:
            raise RuntimeError("Stream is not open. Call open() first.")
        self._stream.write(pcm_bytes)

    def close(self) -> None:
        """Stop and close the output stream and terminate PyAudio."""
        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        self._pa.terminate()
        logger.info("Bluetooth audio output closed.")

    # Context manager support ------------------------------------------------

    def __enter__(self) -> "BluetoothAudioOutput":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ------------------------------------------------------------------

    def _find_device_by_name(self, name_hint: str) -> int | None:
        """Return the device index of the first output device whose name
        contains *name_hint* (case-insensitive), or None if not found.
        """
        hint_lower = name_hint.lower()
        for i in range(self._pa.get_device_count()):
            info = self._pa.get_device_info_by_index(i)
            if (info["maxOutputChannels"] > 0
                    and hint_lower in info["name"].lower()):
                logger.debug("Found Bluetooth device '%s' at index %d.",
                             info["name"], i)
                return i
        return None


# ── CLI entry point ──────────────────────────────────────────────────────────

def main() -> None:
    """CLI helper: list available output devices or run a loopback test."""
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="Bluetooth audio output helper for OpenHear."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--list", action="store_true",
        help="List all available PyAudio output devices and their indices.",
    )
    group.add_argument(
        "--device-index", type=int, metavar="N",
        help="Open device N and play 1 second of silence as a connection test.",
    )
    args = parser.parse_args()

    if args.list:
        list_output_devices()
    else:
        import numpy as np
        bt = BluetoothAudioOutput(
            sample_rate=16_000,
            channels=2,
            frames_per_buffer=256,
            device_index=args.device_index,
        )
        silence = np.zeros(256 * 2, dtype=np.int16).tobytes()  # 1 silent buffer
        frames = int(16_000 / 256)  # ~1 second
        print(f"Playing {frames} silent buffers to device {args.device_index} …")
        with bt:
            for _ in range(frames):
                bt.write(silence)
        print("Done.")


if __name__ == "__main__":
    main()
