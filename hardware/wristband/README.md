# OpenHear Wristband prototype

This directory contains the first practical wristband prototype for Sharp
Hearing and other clinic-side evaluation work.

## Included

- `firmware.py` — MicroPython firmware for the BBC micro:bit v2

## Packet format

The Windows runtime sends one 3-byte BLE UART packet:

```text
[sound_class_id, intensity_0_to_255, pattern_id]
```

## Supported sound classes

| Sound | ID | Pattern | Dominant frequency |
|---|---:|---:|---:|
| silence | 0 | 0 | — |
| voice | 1 | 1 | 1000 Hz |
| doorbell | 2 | 2 | 2000 Hz |
| alarm | 3 | 3 | 3150 Hz |
| dog | 4 | 4 | 500 Hz |
| traffic | 5 | 5 | 500 Hz |
| media | 6 | 6 | 1000 Hz |

## Wiring summary

- `P0` → left motor transistor driver
- `P1` → right motor transistor driver
- common `GND` between the micro:bit and the motor battery
- each motor driven through a **2N2222A / PN2222A** low-side switch
- **1 kΩ** base resistor per transistor
- **10 kΩ** base pulldown per transistor
- **1N5819** flyback diode per motor

For the full wiring notes, see [`../../HARDWARE.md`](../../HARDWARE.md).

## Windows flashing + BLE debugging

- Flashing steps: [`../../HARDWARE.md#firmware-flashing-windows`](../../HARDWARE.md#firmware-flashing-windows)
- BLE troubleshooting: [`../../HARDWARE.md#windows-ble-debugging-checklist`](../../HARDWARE.md#windows-ble-debugging-checklist)
