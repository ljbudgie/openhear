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
from typing import Iterable

import numpy as np
import pyaudio

logger = logging.getLogger(__name__)


# Substrings that commonly appear in the device names of Bluetooth audio
# devices likely to be hearing-aid streamers.  Used by
# :func:`is_likely_bluetooth_device` and ``--list`` filtering.
LIKELY_BLUETOOTH_NAME_HINTS: tuple[str, ...] = (
    "bluetooth", "bt", "phonak", "signia", "oticon", "resound", "starkey",
    "widex", "hearing", "naida", "insio", "audeo", "marvel", "ax", "sennheiser",
)


def is_likely_bluetooth_device(name: str) -> bool:
    """Return ``True`` if *name* looks like a Bluetooth/hearing-aid device.

    The check is a case-insensitive substring search against
    :data:`LIKELY_BLUETOOTH_NAME_HINTS`.  False positives (e.g. a
    keyboard whose name contains "BT") are acceptable because this
    helper is only used to suggest devices to the user.
    """
    lower = name.lower()
    return any(hint in lower for hint in LIKELY_BLUETOOTH_NAME_HINTS)


def resample_to(samples: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    """Cheap linear-interpolation sample-rate converter.

    Used when the user's Bluetooth output device only supports a sample
    rate different from the pipeline's working rate (typical for
    headsets locked to 48 kHz).  Linear interpolation is good enough for
    speech and avoids pulling in ``scipy.signal.resample_poly`` as a
    runtime dep.

    Args:
        samples: Mono 1-D float32 array of normalised PCM.
        src_rate: Original sample rate in Hz.
        dst_rate: Target sample rate in Hz.

    Returns:
        Resampled float32 1-D array at *dst_rate*.

    Raises:
        ValueError: If either rate is non-positive.
    """
    if src_rate <= 0 or dst_rate <= 0:
        raise ValueError("Sample rates must be positive.")
    x = np.asarray(samples, dtype=np.float32)
    if src_rate == dst_rate or x.size == 0:
        return x.astype(np.float32, copy=False)

    ratio = dst_rate / src_rate
    n_out = int(round(x.size * ratio))
    if n_out <= 1:
        return x[:1].astype(np.float32, copy=True)

    # Index of each output sample in the input timeline.
    src_index = np.linspace(0.0, x.size - 1, n_out, dtype=np.float64)
    floor = np.floor(src_index).astype(np.int64)
    frac = src_index - floor
    ceil = np.minimum(floor + 1, x.size - 1)
    out = (1.0 - frac) * x[floor] + frac * x[ceil]
    return out.astype(np.float32)


def list_output_devices(pa: pyaudio.PyAudio | None = None) -> list[dict]:
    """Return information about every available output device.

    Args:
        pa: Optional :class:`pyaudio.PyAudio` instance to reuse.  If
            ``None``, a fresh one is created and terminated locally.

    Returns:
        List of dicts with ``index``, ``name``, ``max_output_channels``,
        ``default_sample_rate``, and ``likely_bluetooth`` keys.
    """
    owns_pa = pa is None
    pa = pa or pyaudio.PyAudio()
    devices: list[dict] = []
    try:
        count = pa.get_device_count()
        for i in range(count):
            info = pa.get_device_info_by_index(i)
            if int(info.get("maxOutputChannels", 0)) <= 0:
                continue
            devices.append({
                "index": i,
                "name": str(info["name"]),
                "max_output_channels": int(info["maxOutputChannels"]),
                "default_sample_rate": float(info.get("defaultSampleRate", 0)),
                "likely_bluetooth": is_likely_bluetooth_device(str(info["name"])),
            })
    finally:
        if owns_pa:
            pa.terminate()
    return devices


def _print_device_table(devices: Iterable[dict], bluetooth_only: bool) -> None:
    """Render :func:`list_output_devices` output as a readable table."""
    rows = [d for d in devices if not bluetooth_only or d["likely_bluetooth"]]
    print(f"{'Index':<6} {'Name':<48} {'Out':>3}  {'SR (Hz)':>8}  BT?")
    print("-" * 76)
    for d in rows:
        bt_marker = "✓" if d["likely_bluetooth"] else " "
        print(
            f"{d['index']:<6} {d['name'][:46]:<48} "
            f"{d['max_output_channels']:>3}  "
            f"{int(d['default_sample_rate']):>8}  {bt_marker}"
        )


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

def main(argv: list[str] | None = None) -> int:
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
    parser.add_argument(
        "--bluetooth-only", action="store_true",
        help="With --list, hide non-Bluetooth-looking devices.",
    )
    args = parser.parse_args(argv)

    if args.list:
        devices = list_output_devices()
        _print_device_table(devices, bluetooth_only=args.bluetooth_only)
        return 0

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
    return 0


if __name__ == "__main__":
    sys.exit(main())

