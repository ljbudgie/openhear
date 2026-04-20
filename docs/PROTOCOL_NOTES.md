# Noahlink HID Protocol — Open Notes

This document captures everything we currently know — and don't know —
about the framed messages that travel over a Noahlink Wireless 2 USB
HID endpoint between the host fitting software and a paired hearing
aid.  The goal is not a complete spec (HIMSA's protocol is proprietary
and unpublished) but a clear, evolving record of what is safe to
build on now.

## Status legend

* ✅ Verified against multiple captures and reproduced end-to-end.
* 🟡 Plausible based on a single capture or external write-up.
* ❌ Unknown / TODO.

## Transport

* **Bus**: USB HID, single interface, no vendor extensions.
* **VID/PID**: typically `0x0484 / 0x006E` (verify with
  `hid.enumerate()` — some clones rebadge to other IDs).  ✅
* **Report length**: 64 bytes per HID report.  Windows requires a
  leading `0x00` report-ID byte on writes.  ✅
* **Polling**: device only emits reports in response to host requests
  (full duplex but request/response style in practice).  🟡

## Framing (`core.protocol`)

All framed messages share the layout:

```
+------+-----+------+----------+---------+----------+
| 0xA5 | seq | type |  len(N)  | payload | checksum |
|  1B  | 1B  |  1B  |    1B    |    NB   |    1B    |
+------+-----+------+----------+---------+----------+
```

* `sync = 0xA5`  ✅
* `seq` rolls 0–255.  Devices echo it in the corresponding reply.  ✅
* `type` is one byte.  Known values (subset):
    * `0x01` HELLO  🟡
    * `0x02` ACK    🟡
    * `0x10` GET_DEVICE_INFO  🟡
    * `0x11` DEVICE_INFO  🟡
    * `0x20` GET_FITTING  🟡
    * `0x21` FITTING_BLOB  ❌ (length & internal layout unconfirmed)
    * `0x22` WRITE_FITTING  ❌ — *do not* use until verified.
    * `0x30` BACKUP / `0x31` RESTORE  ❌
* `checksum` is the 8-bit XOR of `seq..last_payload_byte`.  ✅

## High-level decoders

Higher-level interpretation (gain tables, MPO limits, programme
slots) lives in `core.fitting_data`.  Today those decoders are
**dataclass scaffolding only** — the real bytes-to-fields mapping is
still TODO.  Until `FITTING_BLOB`'s layout is reproduced from at
least three captures, treat any non-trivial fields you see as
`unknown_fields` and surface them via `ParsedFrame.unknown_fields`.

## Safety gates in the code

* `core.write_fitting.ALLOWED_PARAMETERS` is intentionally tiny.
  Expanding it before the relevant message types are confirmed risks
  bricking real devices.
* `core.backup.restore_backup` raises `NotImplementedError` for the
  same reason.

## How to contribute new captures

1. Run `python -m core.noahlink sniff --duration 30 --log capture.log`
   while the official fitting software performs the action you want
   to reproduce.
2. Diff the resulting `capture.log` against an idle baseline.
3. Run `python -c "from core.protocol import decode_session; ..."`
   over the captured bytes to extract framed messages.
4. Open a PR adding the new message-type ID to `MessageType`, the
   payload schema to `core.fitting_data`, and a regression test
   under `tests/test_core_protocol.py` that decodes the canned bytes.
