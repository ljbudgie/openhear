"""
noahlink.py – HID wrapper for the Noahlink Wireless 2 USB programmer.

Wraps the third-party ``hid`` library with three things that real-world
users need:

1. **Reconnect logic** – the dongle drops out occasionally; this
   wrapper retries the open call before giving up.
2. **Send/receive with timeout** – higher level code shouldn't deal
   with raw HID quirks like the leading report-ID byte on Windows.
3. **Traffic logging + sniff mode** – every byte flowing in and out is
   appended to ``core/logs/hid_traffic.log`` (when enabled) and a
   ``--sniff`` CLI mode lets users record a session for later analysis
   with :func:`core.protocol.decode_session`.

The hardware path is intentionally guarded: every method that talks to
real USB raises a clear "plug in your Noahlink Wireless 2" message
when the device is missing, so users always know what to do next.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import hid

logger = logging.getLogger(__name__)


# ── Identifiers ────────────────────────────────────────────────────────────

#: USB Vendor ID commonly reported by HIMSA Noahlink Wireless 2 dongles.
NOAHLINK_VENDOR_ID: int = 0x0484

#: USB Product ID commonly reported by HIMSA Noahlink Wireless 2 dongles.
NOAHLINK_PRODUCT_ID: int = 0x006E

#: Standard HID report length for Noahlink frames.
HID_REPORT_LENGTH: int = 64

#: Default location of the traffic-sniff log relative to the repo.
DEFAULT_LOG_PATH: Path = Path(__file__).resolve().parent / "logs" / "hid_traffic.log"


# ── Wrapper ────────────────────────────────────────────────────────────────


@dataclass
class NoahlinkDevice:
    """Thin context-manager around an ``hid.device`` handle.

    The constructor does *not* open the device — call :meth:`open` (or
    use the ``with`` form) so the object can be created and inspected
    even when no hardware is plugged in.

    Attributes:
        vendor_id: USB Vendor ID to look for.
        product_id: USB Product ID to look for.
        log_path: When set, every read/write is appended (hex-encoded)
            to this file with a timestamp so a session can be replayed
            through :func:`core.protocol.decode_session`.
        retries: How many times to retry :meth:`open` on transient
            ``OSError``.
    """

    vendor_id: int = NOAHLINK_VENDOR_ID
    product_id: int = NOAHLINK_PRODUCT_ID
    log_path: Path | None = None
    retries: int = 3
    _device: hid.device | None = field(default=None, init=False, repr=False)

    # ------------------------------------------------------------------

    def open(self) -> "NoahlinkDevice":
        """Open the underlying HID device, retrying transient failures.

        Returns ``self`` so the call can be chained.
        """
        last_exc: Exception | None = None
        for attempt in range(1, max(1, self.retries) + 1):
            try:
                dev = hid.device()
                dev.open(self.vendor_id, self.product_id)
                dev.set_nonblocking(False)
                self._device = dev
                logger.info(
                    "Opened Noahlink Wireless 2 (VID=%#06x PID=%#06x).",
                    self.vendor_id, self.product_id,
                )
                return self
            except OSError as exc:
                last_exc = exc
                logger.warning(
                    "Attempt %d/%d to open Noahlink failed: %s",
                    attempt, self.retries, exc,
                )
                time.sleep(0.1 * attempt)
        raise OSError(
            f"Cannot open Noahlink Wireless 2 "
            f"(VID={self.vendor_id:#06x}, PID={self.product_id:#06x}). "
            "Plug in the dongle and confirm it appears in your OS device list."
        ) from last_exc

    def close(self) -> None:
        """Close the underlying HID device."""
        if self._device is not None:
            try:
                self._device.close()
            finally:
                self._device = None
                logger.info("Closed Noahlink Wireless 2.")

    def __enter__(self) -> "NoahlinkDevice":
        return self.open()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ------------------------------------------------------------------

    def write(self, data: bytes) -> int:
        """Write a single HID report.

        On Windows the ``hid`` library expects a leading report-ID byte
        (``0x00``) followed by exactly :data:`HID_REPORT_LENGTH`
        payload bytes; shorter frames are padded with zeros and longer
        ones are rejected.
        """
        if self._device is None:
            raise RuntimeError(
                "Noahlink device is not open.  Call open() first or use "
                "`with NoahlinkDevice(...)` syntax."
            )
        if len(data) > HID_REPORT_LENGTH:
            raise ValueError(
                f"Frame is {len(data)} bytes; max {HID_REPORT_LENGTH}."
            )
        padded = bytes([0x00]) + bytes(data) + bytes(HID_REPORT_LENGTH - len(data))
        n = self._device.write(padded)
        if n < 0:
            raise IOError("HID write failed (driver returned <0).")
        self._log("TX", data)
        return n

    def read(self, timeout_ms: int = 2_000) -> bytes:
        """Read one HID report, returning its raw bytes.

        Args:
            timeout_ms: Read timeout in milliseconds.

        Raises:
            TimeoutError: If no report is delivered within the timeout.
        """
        if self._device is None:
            raise RuntimeError("Noahlink device is not open.")
        data = self._device.read(HID_REPORT_LENGTH, timeout_ms=timeout_ms)
        if not data:
            raise TimeoutError(
                f"No HID report received from Noahlink within {timeout_ms} ms."
            )
        out = bytes(data)
        self._log("RX", out)
        return out

    def send_and_receive(
        self,
        request: bytes,
        timeout_ms: int = 2_000,
    ) -> bytes:
        """Convenience helper — write *request* and read one reply."""
        self.write(request)
        return self.read(timeout_ms=timeout_ms)

    # ------------------------------------------------------------------

    def _log(self, direction: str, data: bytes) -> None:
        if self.log_path is None:
            return
        Path(self.log_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(f"{time.time():.6f} {direction} {data.hex()}\n")


# ── Helpers ────────────────────────────────────────────────────────────────


def enumerate_devices() -> list[dict]:
    """Return ``hid.enumerate()`` filtered to common Noahlink VID/PIDs.

    When debugging "device not found" issues, calling
    :func:`hid.enumerate` directly is the fastest way to confirm
    whether the OS sees the dongle at all.
    """
    found = []
    for info in hid.enumerate():
        vid = info.get("vendor_id")
        pid = info.get("product_id")
        if vid == NOAHLINK_VENDOR_ID and pid == NOAHLINK_PRODUCT_ID:
            found.append(info)
    return found


def sniff(
    duration_seconds: float,
    *,
    log_path: Path = DEFAULT_LOG_PATH,
    vendor_id: int = NOAHLINK_VENDOR_ID,
    product_id: int = NOAHLINK_PRODUCT_ID,
) -> Path:  # pragma: no cover - hardware path
    """Record every HID report received from the dongle for *duration_seconds*.

    No requests are sent; the wrapper purely observes what arrives.
    Returns the log file path.
    """
    dev = NoahlinkDevice(
        vendor_id=vendor_id, product_id=product_id, log_path=log_path,
    ).open()
    end = time.monotonic() + max(0.0, float(duration_seconds))
    try:
        while time.monotonic() < end:
            try:
                dev.read(timeout_ms=200)
            except TimeoutError:
                continue
    finally:
        dev.close()
    return log_path


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - hardware path
    """CLI entry point: enumerate or sniff Noahlink traffic."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(
        description="Noahlink Wireless 2 HID wrapper utilities.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("enumerate", help="List Noahlink devices currently visible.")
    sniff_p = sub.add_parser("sniff", help="Record HID traffic to a log file.")
    sniff_p.add_argument("--duration", type=float, default=10.0,
                         help="Seconds to listen (default: 10).")
    sniff_p.add_argument("--log", type=Path, default=DEFAULT_LOG_PATH,
                         help=f"Log path (default: {DEFAULT_LOG_PATH}).")
    args = parser.parse_args(argv)

    if args.cmd == "enumerate":
        devices = enumerate_devices()
        if not devices:
            print("No Noahlink Wireless 2 device found.", file=sys.stderr)
            return 1
        for info in devices:
            print(info)
        return 0

    log = sniff(args.duration, log_path=args.log)
    print(f"Wrote HID traffic log to {log}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
