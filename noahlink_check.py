#!/usr/bin/env python3
"""
noahlink_check.py — OpenHear Noahlink Wireless diagnostic + fitting reader.

Strategy
--------
HIDAPI (IOHIDManager) does not enumerate the Noahlink Wireless 2 on macOS,
even with the correct VID/PID, because the device uses a vendor-specific USB
interface class that IOHIDManager ignores.

This script uses libusb-1.0 instead, which talks directly to IOUSBDevice and
can open any USB device regardless of class.

Requirements
------------
    brew install libusb          # installs to /opt/homebrew/lib/libusb-1.0.dylib

Run
---
    python3 noahlink_check.py
    # or with verbose descriptor dump:
    python3 noahlink_check.py --describe
"""

import argparse
import ctypes
import ctypes.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── 1. Load libusb-1.0 via ctypes ─────────────────────────────────────────────

LIBUSB_PATHS = [
    "/opt/homebrew/lib/libusb-1.0.dylib",   # Apple Silicon Homebrew
    "/usr/local/lib/libusb-1.0.dylib",       # Intel Homebrew
    "/opt/homebrew/lib/libusb-1.0.0.dylib",
    "/usr/local/lib/libusb-1.0.0.dylib",
]

libusb = None
for _p in LIBUSB_PATHS:
    if Path(_p).exists():
        try:
            libusb = ctypes.CDLL(_p)
            print(f"✓ Loaded {_p}")
            break
        except OSError:
            continue

if libusb is None:
    _found = ctypes.util.find_library("usb-1.0") or ctypes.util.find_library("usb")
    if _found:
        try:
            libusb = ctypes.CDLL(_found)
            print(f"✓ Loaded {_found}")
        except OSError:
            pass

if libusb is None:
    print("✗ Cannot find libusb-1.0.dylib.")
    print("  Run: brew install libusb")
    sys.exit(1)

# ── 2. libusb constants ────────────────────────────────────────────────────────

LIBUSB_SUCCESS               = 0
LIBUSB_ERROR_NOT_FOUND       = -5
LIBUSB_ERROR_ACCESS          = -3
LIBUSB_TRANSFER_TYPE_INTERRUPT = 3
LIBUSB_ENDPOINT_IN           = 0x80
LIBUSB_ENDPOINT_OUT          = 0x00

# ── 3. libusb function signatures ─────────────────────────────────────────────

libusb.libusb_init.restype  = ctypes.c_int
libusb.libusb_init.argtypes = [ctypes.POINTER(ctypes.c_void_p)]

libusb.libusb_exit.restype  = None
libusb.libusb_exit.argtypes = [ctypes.c_void_p]

libusb.libusb_open_device_with_vid_pid.restype  = ctypes.c_void_p
libusb.libusb_open_device_with_vid_pid.argtypes = [
    ctypes.c_void_p, ctypes.c_uint16, ctypes.c_uint16
]

libusb.libusb_close.restype  = None
libusb.libusb_close.argtypes = [ctypes.c_void_p]

libusb.libusb_kernel_driver_active.restype  = ctypes.c_int
libusb.libusb_kernel_driver_active.argtypes = [ctypes.c_void_p, ctypes.c_int]

libusb.libusb_detach_kernel_driver.restype  = ctypes.c_int
libusb.libusb_detach_kernel_driver.argtypes = [ctypes.c_void_p, ctypes.c_int]

libusb.libusb_claim_interface.restype  = ctypes.c_int
libusb.libusb_claim_interface.argtypes = [ctypes.c_void_p, ctypes.c_int]

libusb.libusb_release_interface.restype  = ctypes.c_int
libusb.libusb_release_interface.argtypes = [ctypes.c_void_p, ctypes.c_int]

libusb.libusb_interrupt_transfer.restype  = ctypes.c_int
libusb.libusb_interrupt_transfer.argtypes = [
    ctypes.c_void_p,   # handle
    ctypes.c_uint8,    # endpoint
    ctypes.c_char_p,   # data
    ctypes.c_int,      # length
    ctypes.POINTER(ctypes.c_int),  # actual_length
    ctypes.c_uint,     # timeout_ms
]

libusb.libusb_bulk_transfer.restype  = ctypes.c_int
libusb.libusb_bulk_transfer.argtypes = libusb.libusb_interrupt_transfer.argtypes

libusb.libusb_control_transfer.restype  = ctypes.c_int
libusb.libusb_control_transfer.argtypes = [
    ctypes.c_void_p,   # handle
    ctypes.c_uint8,    # bmRequestType
    ctypes.c_uint8,    # bRequest
    ctypes.c_uint16,   # wValue
    ctypes.c_uint16,   # wIndex
    ctypes.c_char_p,   # data
    ctypes.c_uint16,   # wLength
    ctypes.c_uint,     # timeout_ms
]

# descriptor dump helpers
libusb.libusb_get_device.restype  = ctypes.c_void_p
libusb.libusb_get_device.argtypes = [ctypes.c_void_p]

libusb.libusb_get_device_descriptor.restype  = ctypes.c_int
libusb.libusb_get_device_descriptor.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

libusb.libusb_get_string_descriptor_ascii.restype  = ctypes.c_int
libusb.libusb_get_string_descriptor_ascii.argtypes = [
    ctypes.c_void_p, ctypes.c_uint8, ctypes.c_char_p, ctypes.c_int
]

# ── 4. libusb device descriptor struct ────────────────────────────────────────

class UsbDeviceDescriptor(ctypes.Structure):
    _fields_ = [
        ("bLength",            ctypes.c_uint8),
        ("bDescriptorType",    ctypes.c_uint8),
        ("bcdUSB",             ctypes.c_uint16),
        ("bDeviceClass",       ctypes.c_uint8),
        ("bDeviceSubClass",    ctypes.c_uint8),
        ("bDeviceProtocol",    ctypes.c_uint8),
        ("bMaxPacketSize0",    ctypes.c_uint8),
        ("idVendor",           ctypes.c_uint16),
        ("idProduct",          ctypes.c_uint16),
        ("bcdDevice",          ctypes.c_uint16),
        ("iManufacturer",      ctypes.c_uint8),
        ("iProduct",           ctypes.c_uint8),
        ("iSerialNumber",      ctypes.c_uint8),
        ("bNumConfigurations", ctypes.c_uint8),
    ]

# ── 5. Target device ───────────────────────────────────────────────────────────

NOAHLINK_VID = 0x16f0
NOAHLINK_PID = 0x0003

HID_REPORT_LENGTH = 64
SYNC_BYTE         = 0xA5

# HIMSA frame endpoints — standard HID interrupt endpoints.
# We try these in order; the first one that ACKs wins.
EP_OUT_CANDIDATES = [0x01, 0x02]
EP_IN_CANDIDATES  = [0x81, 0x82]

# ── 6. HIMSA framing ───────────────────────────────────────────────────────────

def encode_frame(msg_type: int, payload: bytes, seq: int = 0) -> bytes:
    body = bytes([seq, msg_type, len(payload)]) + payload
    cs = 0
    for b in body:
        cs ^= b
    return bytes([SYNC_BYTE]) + body + bytes([cs])


def parse_frame(data: bytes):
    """Return parsed frame dict or None if invalid."""
    if len(data) < 5:
        return None
    if data[0] != SYNC_BYTE:
        # Some firmware omits the sync byte on responses
        pass
    seq      = data[1] if data[0] == SYNC_BYTE else data[0]
    msg_type = data[2] if data[0] == SYNC_BYTE else data[1]
    pay_len  = data[3] if data[0] == SYNC_BYTE else data[2]
    offset   = 4       if data[0] == SYNC_BYTE else 3
    payload  = data[offset:offset + pay_len]
    return {"seq": seq, "type": hex(msg_type), "payload": payload.hex()}


# ── 7. Helper: send padded HID report ─────────────────────────────────────────

def hid_write(handle, ep_out: int, frame: bytes) -> int:
    """Pad frame to HID_REPORT_LENGTH and send via interrupt OUT."""
    padded = b"\x00" + frame + bytes(HID_REPORT_LENGTH - len(frame))
    buf = ctypes.create_string_buffer(padded, len(padded))
    transferred = ctypes.c_int(0)
    ret = libusb.libusb_interrupt_transfer(
        handle, ep_out, buf, len(padded),
        ctypes.byref(transferred), 1000
    )
    return ret, transferred.value


def hid_read(handle, ep_in: int, timeout_ms: int = 2000) -> tuple[int, bytes]:
    """Read one HID report via interrupt IN."""
    rbuf = ctypes.create_string_buffer(HID_REPORT_LENGTH)
    transferred = ctypes.c_int(0)
    ret = libusb.libusb_interrupt_transfer(
        handle, ep_in, rbuf, HID_REPORT_LENGTH,
        ctypes.byref(transferred), timeout_ms
    )
    return ret, bytes(rbuf)[:max(0, transferred.value)]


# ── 8. Helper: get string descriptor ──────────────────────────────────────────

def get_string(handle, idx: int) -> str:
    if idx == 0:
        return ""
    buf = ctypes.create_string_buffer(256)
    n = libusb.libusb_get_string_descriptor_ascii(handle, idx, buf, 256)
    return buf.value.decode("ascii", errors="replace") if n > 0 else ""


# ── 9. Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Noahlink Wireless 2 fitting reader via libusb")
    parser.add_argument("--describe", action="store_true",
                        help="Dump USB device/interface/endpoint descriptors and exit")
    args = parser.parse_args()

    # Init libusb
    ctx = ctypes.c_void_p(None)
    ret = libusb.libusb_init(ctypes.byref(ctx))
    if ret != LIBUSB_SUCCESS:
        print(f"✗ libusb_init failed: {ret}")
        sys.exit(1)

    # Open Noahlink
    print(f"\n─── Opening Noahlink (VID={NOAHLINK_VID:#06x} PID={NOAHLINK_PID:#06x}) ───")
    handle = libusb.libusb_open_device_with_vid_pid(ctx, NOAHLINK_VID, NOAHLINK_PID)
    if not handle:
        print("✗ Device not found via libusb.")
        print("  Check it's plugged in. If system_profiler shows it, try:")
        print("  sudo python3 noahlink_check.py")
        libusb.libusb_exit(ctx)
        sys.exit(1)

    print("  ✓ Handle acquired.")

    # Describe USB descriptors if requested
    if args.describe:
        dev = libusb.libusb_get_device(handle)
        desc = UsbDeviceDescriptor()
        libusb.libusb_get_device_descriptor(dev, ctypes.byref(desc))
        mfr    = get_string(handle, desc.iManufacturer)
        prod   = get_string(handle, desc.iProduct)
        serial = get_string(handle, desc.iSerialNumber)
        print(f"\n  Manufacturer : {mfr}")
        print(f"  Product      : {prod}")
        print(f"  Serial       : {serial}")
        print(f"  bDeviceClass : {desc.bDeviceClass:#04x}")
        print(f"  bcdUSB       : {desc.bcdUSB:#06x}")
        print(f"  bMaxPacketSize0 : {desc.bMaxPacketSize0}")
        libusb.libusb_close(handle)
        libusb.libusb_exit(ctx)
        return 0

    # Detach kernel driver on interface 0 (no-op on macOS, harmless)
    if libusb.libusb_kernel_driver_active(handle, 0) == 1:
        print("  Detaching kernel driver on interface 0 …")
        libusb.libusb_detach_kernel_driver(handle, 0)

    # Claim interface 0
    ret = libusb.libusb_claim_interface(handle, 0)
    if ret != LIBUSB_SUCCESS:
        print(f"✗ libusb_claim_interface failed: {ret}")
        if ret == LIBUSB_ERROR_ACCESS:
            print("  Try running with: sudo python3 noahlink_check.py")
        libusb.libusb_close(handle)
        libusb.libusb_exit(ctx)
        sys.exit(1)

    print("  ✓ Interface 0 claimed.")

    ep_out = None
    ep_in  = None
    responses = []

    def exchange(msg_type, payload=b"", seq=0, label=None, read_count=4, timeout_ms=1500):
        """Send a framed command and collect up to read_count non-empty replies."""
        frame = encode_frame(msg_type, payload, seq)
        tag = label or f"0x{msg_type:02X}"
        print(f"\n─── {tag} ───")
        print(f"  TX: {frame.hex()}")
        ret, n = hid_write(handle, ep_out, frame)
        if ret != LIBUSB_SUCCESS:
            print(f"  ✗ write error {ret}")
            return []
        replies = []
        for _ in range(read_count):
            ret, data = hid_read(handle, ep_in, timeout_ms=timeout_ms)
            if ret == LIBUSB_SUCCESS and data and any(b != 0 for b in data):
                replies.append(data)
                f = parse_frame(data)
                print(f"  RX [{len(replies)}]: {data[:24].hex()} …  parsed={f}")
        if not replies:
            print("  (no reply)")
        return replies

    try:
        # ── Step 1: find endpoints via HELLO ──────────────────────────────────
        hello_frame = encode_frame(0x01, b"")
        for ep in EP_OUT_CANDIDATES:
            ret, n = hid_write(handle, ep, hello_frame)
            if ret == LIBUSB_SUCCESS:
                ep_out = ep
                print(f"  ✓ OUT endpoint: {ep:#04x} (HELLO sent, {n}B)")
                break
            else:
                print(f"    ep {ep:#04x} OUT → error {ret}")

        if ep_out is None:
            print("✗ No usable OUT endpoint found.")
        else:
            for ep in EP_IN_CANDIDATES:
                ret, data = hid_read(handle, ep, timeout_ms=800)
                if ret == LIBUSB_SUCCESS and data:
                    ep_in = ep
                    f = parse_frame(data)
                    print(f"  ✓ IN  endpoint: {ep:#04x} ({len(data)}B)")
                    print(f"    HELLO response: {f}")
                    break
                else:
                    print(f"    ep {ep:#04x} IN  → ret={ret}")

        if ep_out is None or ep_in is None:
            print("✗ Could not establish endpoints.")
        else:
            # ── Step 2: flush & show raw HELLO bytes ──────────────────────────
            # Re-send HELLO with seq=1 and print the raw hex so we see
            # exactly what the dongle returns.
            import time
            hello2 = encode_frame(0x01, b"", seq=1)
            hid_write(handle, ep_out, hello2)
            ret2, raw2 = hid_read(handle, ep_in, timeout_ms=1000)
            if ret2 == LIBUSB_SUCCESS and raw2:
                print(f"\n  RAW HELLO reply (hex): {raw2.hex()}")
                print(f"  First 16 bytes:        {' '.join(f'{b:02x}' for b in raw2[:16])}")

            # ── Step 3: open battery doors NOW, then press Enter ──────────────
            print("\n" + "="*60)
            print("  BATTERY AIDS: open both battery doors, wait 3 sec,")
            print("  close them, lay both aids on the Noahlink, then")
            print("  press Enter within 10 seconds of the startup chime.")
            print("="*60)
            input()

            # ── Step 4: listen for 30 seconds — show EVERY non-empty frame ────
            # Noahlink uses a push model: once aids are in range it sends
            # presence notifications without being asked. We watch for them.
            print("\n  Listening for 30s — all frames will be printed raw …")
            print("  (aids should already be on the dongle)\n")
            deadline = time.monotonic() + 30.0
            seq_n = 2
            all_frames = []

            while time.monotonic() < deadline:
                ret_r, raw = hid_read(handle, ep_in, timeout_ms=500)
                if ret_r == LIBUSB_SUCCESS and raw:
                    nonzero = any(b != 0 for b in raw)
                    tag = "DATA" if nonzero else "IDLE"
                    ts = f"{30.0 - (deadline - time.monotonic()):.1f}s"
                    print(f"  [{ts}] {tag}: {raw[:24].hex()}  (first 24B)")
                    if nonzero:
                        all_frames.append(raw)
                        f = parse_frame(raw)
                        print(f"         parsed → {f}")

            # ── Step 5: after passive listen, try active commands ─────────────
            print(f"\n  Passive listen done — captured {len(all_frames)} non-idle frame(s).")

            for cmd, label in [(0x10, "GET_DEVICE_INFO"), (0x20, "GET_FITTING"),
                               (0x03, "SCAN_0x03"), (0x12, "SCAN_0x12")]:
                frame = encode_frame(cmd, b"", seq=seq_n)
                seq_n += 1
                print(f"\n  Sending {label} (seq={seq_n-1}): {frame.hex()}")
                hid_write(handle, ep_out, frame)
                for _ in range(6):
                    ret_r, raw = hid_read(handle, ep_in, timeout_ms=1500)
                    if ret_r == LIBUSB_SUCCESS and raw and any(b != 0 for b in raw):
                        all_frames.append(raw)
                        f = parse_frame(raw)
                        print(f"    RX: {raw[:24].hex()}  parsed={f}")
                        break
                else:
                    print("    (no reply)")

            responses.extend(all_frames)

    finally:
        libusb.libusb_release_interface(handle, 0)
        libusb.libusb_close(handle)
        libusb.libusb_exit(ctx)

    # ── Save results ──
    if not responses:
        print("\n  No response data received.")
        print("  Make sure your hearing aids are:")
        print("  - Turned on and within ~1 metre of the Noahlink dongle")
        print("  - Previously paired with this specific Noahlink")
        print("  The dongle communicates wirelessly — aids must be awake.")
        return 1

    print(f"\n  ✓ Got {len(responses)} frame(s).")
    output = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "device_vid":  hex(NOAHLINK_VID),
        "device_pid":  hex(NOAHLINK_PID),
        "frames":      [r.hex() for r in responses],
    }
    out_path = Path(__file__).parent / "noahlink_raw.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"  ✓ Saved to: {out_path}")

    # Try to decode via core.protocol
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from core.protocol import decode_session
        print("\n─── Decoded frames ───")
        for frame_hex in output["frames"]:
            for f in decode_session(bytes.fromhex(frame_hex)):
                print(f"  seq={f.seq}  type={f.msg_type_name}"
                      f"  checksum={'OK' if f.checksum_ok else 'BAD'}"
                      f"  payload={f.payload.hex() if f.payload else '(empty)'}")
    except Exception as e:
        print(f"  (decode skipped: {e})")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
