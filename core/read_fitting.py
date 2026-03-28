"""
read_fitting.py – Noahlink Wireless 2 fitting reader.

Connects to a Noahlink Wireless 2 USB programmer via the HID protocol,
reads the current fitting data stored on a paired hearing aid, and
exports it as a structured JSON file.  The Noahlink communicates over
USB HID (vendor ID 0x0484, product ID 0x006E are the commonly reported
values for the HIMSA Noahlink Wireless 2 dongle – verify with your own
device using `hid.enumerate()`).

Why this approach:
  - The `hid` library gives direct, cross-platform USB HID access without
    requiring proprietary SDKs.
  - Output is plain JSON so every other part of the pipeline can consume
    fitting data without depending on this module.

Usage (CLI):
    python -m core.read_fitting --output fitting.json
"""

import argparse
import json
import logging
import time

import hid

# ── Noahlink Wireless 2 USB identifiers ──────────────────────────────────────
# Verify these on your machine with:  hid.enumerate()
NOAHLINK_VENDOR_ID = 0x0484
NOAHLINK_PRODUCT_ID = 0x006E

# HID report length expected by the device (bytes)
HID_REPORT_LENGTH = 64

# Command bytes (HIMSA / Noahlink proprietary framing – best-effort reverse
# engineering; replace with confirmed values once verified on real hardware)
CMD_GET_FITTING = bytes([0x00, 0x01, 0x00] + [0x00] * (HID_REPORT_LENGTH - 3))

logger = logging.getLogger(__name__)


def open_device(vendor_id: int = NOAHLINK_VENDOR_ID,
                product_id: int = NOAHLINK_PRODUCT_ID) -> hid.device:
    """Open the first matching HID device and return the handle.

    Raises:
        OSError: if the device cannot be found or opened.
    """
    device = hid.device()
    try:
        device.open(vendor_id, product_id)
    except OSError as exc:
        raise OSError(
            f"Cannot open Noahlink Wireless 2 "
            f"(VID={vendor_id:#06x}, PID={product_id:#06x}). "
            "Ensure the dongle is plugged in and drivers are installed."
        ) from exc
    device.set_nonblocking(False)
    logger.info("Opened Noahlink Wireless 2 successfully.")
    return device


def send_command(device: hid.device, command: bytes) -> None:
    """Write a raw HID report to the device."""
    # hid.write requires a bytes-like object; length must equal HID_REPORT_LENGTH+1
    # (the leading 0x00 is the report ID required by the library on Windows).
    padded = bytes([0x00]) + command[:HID_REPORT_LENGTH]
    padded += bytes(HID_REPORT_LENGTH + 1 - len(padded))
    written = device.write(padded)
    if written < 0:
        raise IOError("Failed to write HID report to Noahlink device.")


def read_response(device: hid.device, timeout_ms: int = 2000) -> bytes:
    """Read a single HID report from the device.

    Args:
        device:     Open HID device handle.
        timeout_ms: Read timeout in milliseconds.

    Returns:
        Raw bytes of the report payload.
    """
    data = device.read(HID_REPORT_LENGTH, timeout_ms=timeout_ms)
    if not data:
        raise TimeoutError("No response received from Noahlink device.")
    return bytes(data)


def read_fitting_data(device: hid.device) -> dict:
    """Request fitting data from the connected aid and return it as a dict.

    The raw HID payload is parsed into a generic key/value structure that
    fitting_schema.py can convert into a typed dataclass.  Byte positions
    are placeholders – update once real HIMSA frame definitions are available.

    Returns:
        dict with keys: raw_payload (hex string), timestamp (ISO-8601)
    """
    send_command(device, CMD_GET_FITTING)
    # Some devices need a short settle time after the command.
    time.sleep(0.05)
    response = read_response(device)

    payload_hex = response.hex()
    logger.debug("Raw fitting payload: %s", payload_hex)

    # TODO: parse individual fields once HIMSA frame layout is confirmed.
    return {
        "raw_payload": payload_hex,
        "timestamp": _utc_now_iso(),
    }


def export_json(data: dict, path: str) -> None:
    """Serialise *data* to a JSON file at *path*."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    logger.info("Fitting data written to %s", path)


def _utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    from datetime import datetime, timezone
    return datetime.now(tz=timezone.utc).isoformat()


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="Read fitting data from Noahlink Wireless 2 and export as JSON."
    )
    parser.add_argument(
        "--output", "-o",
        default="fitting.json",
        help="Path for the output JSON file (default: fitting.json).",
    )
    parser.add_argument(
        "--vendor-id", type=lambda x: int(x, 0), default=NOAHLINK_VENDOR_ID,
        help=f"USB vendor ID (default: {NOAHLINK_VENDOR_ID:#06x}).",
    )
    parser.add_argument(
        "--product-id", type=lambda x: int(x, 0), default=NOAHLINK_PRODUCT_ID,
        help=f"USB product ID (default: {NOAHLINK_PRODUCT_ID:#06x}).",
    )
    args = parser.parse_args()

    device = open_device(args.vendor_id, args.product_id)
    try:
        data = read_fitting_data(device)
    finally:
        device.close()

    export_json(data, args.output)
    print(f"Fitting data saved to {args.output}")


if __name__ == "__main__":
    main()
