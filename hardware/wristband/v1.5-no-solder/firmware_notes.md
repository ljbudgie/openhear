# Firmware Notes and Connector Pinout: v1.5 No-Solder Modular Edition

v1.5 uses the existing v1 mapping and scheduler concepts with a friendlier connector layout. The firmware goal is unchanged: local Bark-band/audiogram haptic rendering with no cloud dependency.

## Recommended board profiles

### Starter: Seeed XIAO ESP32S3 Sense

- Flashing: USB-C vendor bootloader, Arduino, ESP-IDF, CircuitPython, or MicroPython.
- Best for: compact beginner build with onboard mic for first tests.
- Notes: disable camera features unless explicitly used; keep radio off during latency testing.

### Starter alternate: Adafruit Feather ESP32-S3

- Flashing: USB-C UF2/Arduino/CircuitPython path.
- Best for: larger bay with easy battery ecosystem.
- Notes: FeatherWing/ STEMMA QT ecosystem reduces no-solder wiring risk.

### Research scheduler: RP2040 USB-C board

- Flashing: hold BOOTSEL, plug USB-C, copy UF2.
- Best for: deterministic PIO/DMA timing and dense 64-actuator experiments.
- Notes: add BLE only as a companion/config link, never as the hearing path dependency.

## Connector map

### MCU bay connector `J-MCU-6`

| Pin | Signal | Direction | Notes |
|---:|---|---|---|
| 1 | 3V3 | Out | Logic rail to mux/driver modules only |
| 2 | GND | Common | First-mate/last-break preferred on pogo blocks |
| 3 | SDA | Bidirectional | I2C data to TCA9548A/STEMMA QT |
| 4 | SCL | Out | I2C clock |
| 5 | INT/READY | In | Optional haptic-bank ready/interrupt |
| 6 | EN_HAPTIC | Out | Optional driver-bank enable |

### Battery cartridge connector `J-BAT-4`

| Pin | Signal | Notes |
|---:|---|---|
| 1 | VBAT | Protected LiPo output only |
| 2 | GND | Battery ground |
| 3 | 5V_USB | Charger/dock 5 V when present |
| 4 | BATT_NTC/ID | Optional thermistor or cartridge ID resistor |

### Haptic driver branch `J-HAPTIC-x`

| Pin | Signal | Notes |
|---:|---|---|
| 1 | 3V3 | DRV2605L logic and module power where supported |
| 2 | GND | Shared ground |
| 3 | SDA | Branch-local I2C data from mux |
| 4 | SCL | Branch-local I2C clock from mux |
| 5 | EN | Optional enable |
| 6 | FAULT/READY | Optional status |

### Actuator connector `J-ACT-n`

| Pin | Signal | Notes |
|---:|---|---|
| 1 | ACT+ | Pre-wired LRA lead |
| 2 | ACT- | Pre-wired LRA lead |

Use factory pre-crimped 2-pin JST leads. Do not strip or tin motor wires.

## 24-actuator starter mapping

The 24-actuator build preserves one actuator per Bark-like band.

| Bark band | Actuator | Driver bank | Suggested label |
|---:|---:|---:|---|
| 0 | 0 | 0 | A00 |
| 1 | 1 | 0 | A01 |
| 2 | 2 | 0 | A02 |
| 3 | 3 | 1 | A03 |
| 4 | 4 | 1 | A04 |
| 5 | 5 | 1 | A05 |
| 6 | 6 | 2 | A06 |
| 7 | 7 | 2 | A07 |
| 8 | 8 | 2 | A08 |
| 9 | 9 | 3 | A09 |
| 10 | 10 | 3 | A10 |
| 11 | 11 | 3 | A11 |
| 12 | 12 | 4 | A12 |
| 13 | 13 | 4 | A13 |
| 14 | 14 | 4 | A14 |
| 15 | 15 | 5 | A15 |
| 16 | 16 | 5 | A16 |
| 17 | 17 | 5 | A17 |
| 18 | 18 | 6 | A18 |
| 19 | 19 | 6 | A19 |
| 20 | 20 | 6 | A20 |
| 21 | 21 | 7 | A21 |
| 22 | 22 | 7 | A22 |
| 23 | 23 | 7 | A23 |

## 64-actuator dense mapping

The 64-actuator build uses 4 rings x 16 columns. The existing mapper already supports this with:

```python
WristbandLayout(actuator_count=64)
```

Recommended labels:

- Ring 0 distal/high-elevation row: `R0C00-R0C15`.
- Ring 1: `R1C00-R1C15`.
- Ring 2: `R2C00-R2C15`.
- Ring 3 proximal/low-elevation row: `R3C00-R3C15`.

## Changes needed in existing firmware

No breaking changes are required in `hardware/wristband/firmware/haptic_mapper.py` or `openhear_firmware_v1.py` for the first v1.5 build.

Recommended small adaptation when porting to a real board:

1. Set `DEFAULT_ACTUATOR_COUNT = 24` for starter hardware or pass `actuator_count=64` to `HapticScheduler` for dense hardware.
2. Add a board-specific DRV2605L backend that writes to the selected TCA9548A mux branch before driving a module.
3. Keep `MAX_INTENSITY` conservative for first wear; start with 32/255 and raise only after comfort testing.
4. Keep the existing Bark-band and audiogram weighting logic unchanged so v1.5 remains compatible with v1 training profiles.
5. If using magnetic pogo hot-swap, debounce `EN_HAPTIC` for at least 100 ms after module attach.

## Flashing workflow

1. Install the board vendor's USB driver only if your OS needs it.
2. Plug in USB-C.
3. Enter bootloader mode:
   - XIAO ESP32S3: hold BOOT, tap RESET, release BOOT.
   - Feather ESP32-S3: double-tap RESET for UF2 where supported.
   - RP2040: hold BOOTSEL while plugging USB.
4. Flash your chosen runtime.
5. Copy the adapted `openhear_firmware_v1.py` as the main file.
6. Copy `haptic_mapper.py` or import it from the OpenHear source tree during development.
7. Run an actuator walk test before wearing.

## Local-only sovereignty checklist

- No cloud inference.
- No raw audio upload.
- No account required to hear through haptics.
- BLE/Wi-Fi may be used only for optional companion setup/export.
- Audiogram and haptic preference files stay under user control.
