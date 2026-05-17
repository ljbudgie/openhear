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

try:
    import hid as hid  # noqa: PLC0414  (native hidapi may be missing outside tests)
except Exception:  # pragma: no cover - depends on native libs
    hid = None  # type: ignore[assignment]

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
    _device: "hid.device | None" = field(default=None, init=False, repr=False)

    # ------------------------------------------------------------------

    def open(self) -> "NoahlinkDevice":
        """Open the underlying HID device, retrying transient failures.

        Returns ``self`` so the call can be chained.
        """
        if hid is None:  # pragma: no cover - native hidapi missing
            raise OSError(
                "The native `hidapi` library is not available.  Install it "
                "(`apt install libhidapi-hidraw0` or equivalent) before "
                "talking to a Noahlink device."
            )

        last_exc: Exception | None = None
        for attempt in range(1, max(1, self.retries) + 1):
            try:
                dev = hid.device()
                dev.open(self.vendor_id, self.product_id)
                dev.set_nonblocking(False)
                self._device = dev
                logger.info(
                    "Opened Noahlink Wireless 2 (VID=%#06x PID=%#06x).",
                    self.vendor_id,
                    self.product_id,
                )
                return self
            except OSError as exc:
                last_exc = exc
                logger.warning(
                    "Attempt %d/%d to open Noahlink failed: %s",
                    attempt,
                    self.retries,
                    exc,
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
            raise ValueError(f"Frame is {len(data)} bytes; max {HID_REPORT_LENGTH}.")
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
            raise TimeoutError(f"No HID report received from Noahlink within {timeout_ms} ms.")
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
    if hid is None:  # pragma: no cover - native hidapi missing
        return []

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
        vendor_id=vendor_id,
        product_id=product_id,
        log_path=log_path,
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


#: Banner shown before any output that came from a mock / unverified
#: adapter, so users never mistake placeholder data for a real fitting.
UNVERIFIED_BANNER: str = (
    "*** UNVERIFIED MOCK DATA — DO NOT WRITE TO A REAL HEARING AID *** "
    "OpenHear is not a medical device.  See docs/NOAHLINK_EXTRACTION.md."
)


def _build_parser() -> "argparse.ArgumentParser":
    parser = argparse.ArgumentParser(
        prog="openhear-noahlink",
        description="Noahlink Wireless 2 HID wrapper utilities.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("enumerate", help="List Noahlink devices currently visible.")

    sniff_p = sub.add_parser("sniff", help="Record HID traffic to a log file.")
    sniff_p.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Seconds to listen (default: 10).",
    )
    sniff_p.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help=f"Log path (default: {DEFAULT_LOG_PATH}).",
    )

    backup_p = sub.add_parser(
        "backup",
        help="Read a fitting and persist it as an openhear-extraction-v1 backup.",
    )
    backup_p.add_argument(
        "--aid",
        required=True,
        help='Vendor adapter to use (e.g. "phonak").  See `--list-adapters`.',
    )
    backup_p.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Directory under which a timestamped backup folder is created.",
    )
    backup_p.add_argument(
        "--device-serial",
        default="MOCK-PHONAK-000000",
        help="Override the serial stored in the backup (mock adapter only).",
    )
    backup_p.add_argument(
        "--list-adapters",
        action="store_true",
        help="List available vendor adapters and exit.",
    )

    extract_p = sub.add_parser(
        "extract",
        help="Read a fitting and write/print an openhear-extraction-v1 JSON.",
    )
    extract_p.add_argument("--aid", required=True, help='Vendor adapter (e.g. "phonak").')
    extract_p.add_argument(
        "--json",
        action="store_true",
        help="Print the JSON document to stdout (in addition to or instead of --output).",
    )
    extract_p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the JSON document.",
    )
    extract_p.add_argument(
        "--device-serial",
        default="MOCK-PHONAK-000000",
        help="Override the serial stored in the document (mock adapter only).",
    )

    validate_p = sub.add_parser(
        "validate",
        help="Schema- and safety-check an existing extraction JSON file.",
    )
    validate_p.add_argument(
        "path",
        type=Path,
        help="Path to a JSON file produced by `extract` or `backup`.",
    )

    return parser


def _cmd_extract(args) -> int:
    """Run a vendor adapter and emit an extraction JSON."""
    extraction = _run_vendor_adapter(args.aid, device_serial=args.device_serial)

    text = extraction.to_json(indent=2)
    if args.output is not None:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote extraction to {args.output}")
    if args.json or args.output is None:
        print(text)

    if not extraction.is_verified:
        print(UNVERIFIED_BANNER, file=sys.stderr)
    return 0


def _cmd_backup(args) -> int:
    """Run a vendor adapter and persist a full backup directory."""
    from core.backup import safe_label, sha256_file, utc_now_iso

    if args.list_adapters:
        from core.noahlink.vendors import available_adapters

        for name, desc in available_adapters().items():
            print(f"{name}: {desc}")
        return 0

    extraction = _run_vendor_adapter(args.aid, device_serial=args.device_serial)

    label = f"{safe_label(extraction.device.serial)}_{utc_now_iso().replace(':', '-')}"
    backup_dir = Path(args.output) / label
    backup_dir.mkdir(parents=True, exist_ok=True)

    extraction_path = backup_dir / "extraction.json"
    raw_path = backup_dir / "raw.bin"
    manifest_path = backup_dir / "manifest.json"

    extraction_path.write_text(extraction.to_json(indent=2), encoding="utf-8")
    raw_bytes = bytes.fromhex(extraction.raw_payload_hex) if extraction.raw_payload_hex else b""
    raw_path.write_bytes(raw_bytes)

    import json as _json

    manifest = {
        "schema_version": "openhear-backup-v1",
        "created_at": utc_now_iso(),
        "extraction_schema_version": extraction.schema_version,
        "vendor_adapter": extraction.vendor_adapter,
        "is_verified": extraction.is_verified,
        "device_serial": extraction.device.serial,
        "extraction_filename": extraction_path.name,
        "raw_filename": raw_path.name,
        "extraction_sha256": sha256_file(extraction_path),
        "raw_sha256": sha256_file(raw_path),
        "raw_size_bytes": raw_path.stat().st_size,
        "extraction_commitment_sha256": extraction.sha256_commitment(),
    }
    manifest_path.write_text(_json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote backup to {backup_dir}")
    if not extraction.is_verified:
        print(UNVERIFIED_BANNER, file=sys.stderr)
    return 0


def _cmd_validate(args) -> int:
    """Schema + safety check an existing extraction JSON file."""
    from core.safety import evaluate_extraction
    from core.schema.extraction_v1 import ExtractedFitting

    path = Path(args.path)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2
    try:
        extraction = ExtractedFitting.from_json(path.read_text(encoding="utf-8"))
    except (ValueError, KeyError) as exc:
        print(f"Schema validation failed: {exc}", file=sys.stderr)
        return 2

    report = evaluate_extraction(extraction)
    print(f"Schema: OK ({extraction.schema_version})")
    print(f"Safety: {report.summary()}")
    for flag in report.flags:
        print(f"  [{flag.level}] {flag.code}: {flag.message} (at {flag.location})")
    return 0 if report.passed else 1


def _run_vendor_adapter(aid: str, *, device_serial: str):
    """Dispatch ``--aid`` to a vendor adapter and return an extraction."""
    aid = aid.lower()
    if aid == "phonak":
        from core.noahlink.vendors.phonak import PhonakMockAdapter

        return PhonakMockAdapter(device_serial=device_serial).read()
    raise ValueError(
        f"Unknown vendor adapter {aid!r}.  Known: phonak.  "
        "Run with `--list-adapters` to see the full list."
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: enumerate, sniff, extract, backup, or validate."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "enumerate":  # pragma: no cover - hardware path
        devices = enumerate_devices()
        if not devices:
            print("No Noahlink Wireless 2 device found.", file=sys.stderr)
            return 1
        for info in devices:
            print(info)
        return 0

    if args.cmd == "sniff":  # pragma: no cover - hardware path
        log = sniff(args.duration, log_path=args.log)
        print(f"Wrote HID traffic log to {log}")
        return 0

    if args.cmd == "extract":
        return _cmd_extract(args)
    if args.cmd == "backup":
        return _cmd_backup(args)
    if args.cmd == "validate":
        return _cmd_validate(args)

    parser.error(f"Unhandled command: {args.cmd}")  # pragma: no cover
    return 2  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
