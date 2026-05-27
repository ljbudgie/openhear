"""
reader.py – audiogram (hearing threshold) reader for OpenHear.

Reads Hearing Threshold Level (HTL) data from a paired hearing aid via the
Noahlink Wireless 2 USB programmer.  The thresholds are returned as a plain
Python dict keyed by frequency (Hz) and ear ('left', 'right'), expressed in
dB HL (Hearing Level) — the conventional audiometric unit where 0 dB HL
represents the average threshold of a normal-hearing adult.

Why this module exists separately from core/read_fitting.py:
  - Fitting data (gains, compression ratios) and audiometric data (HTLs)
    are conceptually distinct; keeping them separate makes each easier to
    test and maintain.
  - The audiogram is the input to any prescriptive fitting formula (e.g.
    NAL-NL2, DSL v5); the fitting profile is the output.

HID communication notes:
  The Noahlink Wireless 2 uses HIMSA protocol framing over USB HID.
  The exact command bytes below are best-effort placeholders based on
  publicly available HIMSA documentation.  Verify on real hardware and
  update CMD_GET_AUDIOGRAM accordingly.

Usage:
    python -m audiogram.reader --output audiogram.json
"""

import argparse
import json
import logging
import time

import hid

from core.read_fitting import (
    HID_REPORT_LENGTH,
    NOAHLINK_PRODUCT_ID,
    NOAHLINK_VENDOR_ID,
    _utc_now_iso,
    open_device,
    read_response,
    send_command,
)

logger = logging.getLogger(__name__)

# Audiometric standard test frequencies (Hz) per ISO 8253-1.
STANDARD_FREQUENCIES_HZ = (250, 500, 1000, 2000, 3000, 4000, 6000, 8000)

# Placeholder HID command to request audiogram data.
# Replace with the real HIMSA frame bytes once confirmed on hardware.
CMD_GET_AUDIOGRAM = bytes([0x00, 0x02, 0x00] + [0x00] * (HID_REPORT_LENGTH - 3))


def parse_audiogram_response(raw: bytes) -> dict:
    """Parse a raw HID response payload into per-ear threshold dicts.

    Args:
        raw: Bytes read from the Noahlink device in response to
             CMD_GET_AUDIOGRAM.

    Returns:
        dict with structure::

            {
                "left":  {250: 30.0, 500: 35.0, ...},
                "right": {250: 25.0, 500: 30.0, ...},
            }

        All values are in dB HL.

    Notes:
        The byte layout below is a placeholder.  Each threshold is currently
        decoded as a raw unsigned byte interpreted as dB HL directly, which
        will not be accurate until the HIMSA frame format is confirmed.
        Update the slice indices and scale factors once validated on real
        hardware.
    """
    thresholds: dict = {"left": {}, "right": {}}

    # Placeholder parsing: read sequential bytes and map to frequencies.
    # Byte 2..9  = left ear thresholds for STANDARD_FREQUENCIES_HZ (0-indexed).
    # Byte 10..17 = right ear thresholds.
    # This layout is fictional — replace with real HIMSA offsets.
    n = len(STANDARD_FREQUENCIES_HZ)
    left_bytes = raw[2: 2 + n]
    right_bytes = raw[2 + n: 2 + 2 * n]

    for i, freq in enumerate(STANDARD_FREQUENCIES_HZ):
        thresholds["left"][freq] = float(left_bytes[i]) if i < len(left_bytes) else 0.0
        thresholds["right"][freq] = float(right_bytes[i]) if i < len(right_bytes) else 0.0

    return thresholds


def read_audiogram(device: hid.device) -> dict:
    """Request and return the audiogram from the connected hearing aid.

    Returns:
        dict with keys 'left', 'right', 'timestamp'.
    """
    send_command(device, CMD_GET_AUDIOGRAM)
    time.sleep(0.05)
    response = read_response(device)
    logger.debug("Raw audiogram payload: %s", response.hex())

    thresholds = parse_audiogram_response(response)
    thresholds["timestamp"] = _utc_now_iso()
    return thresholds


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="Read audiogram thresholds from Noahlink Wireless 2."
    )
    parser.add_argument(
        "--output", "-o", default="audiogram.json",
        help="Output JSON file path (default: audiogram.json).",
    )
    parser.add_argument(
        "--vendor-id", type=lambda x: int(x, 0), default=NOAHLINK_VENDOR_ID,
    )
    parser.add_argument(
        "--product-id", type=lambda x: int(x, 0), default=NOAHLINK_PRODUCT_ID,
    )
    args = parser.parse_args()

    device = open_device(args.vendor_id, args.product_id)
    try:
        data = read_audiogram(device)
    finally:
        device.close()

    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    print(f"Audiogram data saved to {args.output}")


if __name__ == "__main__":
    main()
