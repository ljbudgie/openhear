# OpenHear Wristband v2 firmware – XIAO nRF52840

Licence: MIT OR Apache-2.0 (matches v1).

This folder contains the **primary firmware path for v2**: an Arduino sketch
targeting the Seeed Studio **XIAO nRF52840** / **XIAO nRF52840 Sense** using
the open-source **NimBLE-Arduino** stack and the open-source
**Adafruit DRV2605 Library** for LRA haptics.

A Zephyr alternative is described at the bottom for users who prefer the
nRF Connect SDK / Zephyr RTOS path. Both implementations honour the same
**3-byte BLE packet contract** (`[sound_class_id, intensity, pattern_id]`)
as `wristband/openhear_firmware.py` and
`hardware/wristband/firmware/openhear_firmware_v1.py`, so the existing YAMNet
classifier, audiogram JSON, and companion phone app stream into v2 unchanged.

## Toolchain – Arduino IDE (recommended starter)

1. Install **Arduino IDE 2.x**.
2. In *Preferences → Additional Boards Manager URLs* add:

   ```
   https://files.seeedstudio.com/arduino/package_seeeduino_boards_index.json
   ```

3. *Boards Manager* → install **Seeed nRF52 mbed-enabled Boards**.
4. *Tools → Board* → **XIAO nRF52840 Sense (mbed-enabled)**.
5. *Library Manager* → install:
   - **NimBLE-Arduino** (h2zero) ≥ 1.4
   - **Adafruit DRV2605 Library** ≥ 1.2
   - **Adafruit BusIO** (auto pulled)
6. Open `openhear_v2_xiao_nrf52840.ino`, select the right serial port, click *Upload*.
7. First boot advertises as `OpenHear-v2`. Connect with the same companion
   app/script that talks to v1; the UUIDs are unchanged.

### Optional: Bluefruit nRF52 stack
Define `OPENHEAR_USE_BLUEFRUIT` (and undefine `OPENHEAR_USE_NIMBLE`) at the
top of the sketch and install **Adafruit Bluefruit nRF52 Libraries**. The
characteristic UUIDs and packet format are identical.

## BLE GATT contract (do **not** change)

| Service / Characteristic | UUID | Direction | Payload |
|---|---|---|---|
| OpenHear Haptic Service | `6f68656172-0000-1000-8000-00805f9b34fb` | – | – |
| Packet characteristic   | `6f68656172-0001-1000-8000-00805f9b34fb` | Write / Write-No-Response | **3 bytes**: `[sound_class_id, intensity, pattern_id]` |
| Config characteristic   | `6f68656172-0002-1000-8000-00805f9b34fb` | Write | `[actuator_count, intensity_cap]` |

`sound_class_id` ∈ `0..6` matches the YAMNet 7-class head used everywhere in
the repo. `pattern_id == 240` (`V0_COMPAT_PATTERN`) triggers the same legacy
micro:bit v0 shim behaviour as the v1 firmware.

## Haptic waveform map

The default class → DRV2605 ROM-effect mapping lives in `CLASS_EFFECTS[]`
inside the sketch. It is intentionally short, readable, and tunable to your
audiogram JSON:

| ID | Class      | Primary effect (DRV2605 ROM)      | Notes |
|----|------------|------------------------------------|-------|
| 0  | speech     | 14 “Strong Buzz 60%”               | sustained, gentle |
| 1  | alarm      | 47 “Buzz 1 – 100%” ×3              | urgent, repeated |
| 2  | doorbell   | 24 + 27 (sharp + double-click)     | knock-like |
| 3  | baby cry   | 82 long ramp                       | rising attention |
| 4  | vehicle    | 48 “Buzz 2 – 80%”                  | hard pulse |
| 5  | appliance  | 26 short double-click              | beep-like |
| 6  | ambient    | 58 “Long Buzz, No Stop”            | low-priority |

These are open-source effect IDs baked into the DRV2605 ROM (no proprietary
firmware download required). Swap freely without touching the BLE contract.

## Power-optimised sleep modes

The sketch follows three rules to hit an all-day target on a 300–500 mAh cell:

1. **DRV2605 standby after every effect.** `g_drv.stop()` is called on the
   silence packet and after the idle timer.
2. **`__WFE()` / `__SEV()` loop** when no BLE write has arrived for
   `IDLE_SLEEP_AFTER_MS` (8 s default). The nRF52840 BLE radio keeps
   advertising/listening in low-duty cycle.
3. **TX power capped to −12 dBm** (`NimBLEDevice::setPower(-12)` on
   nRF52, or `Bluefruit.setTxPower(-12)`). Companion is at arm’s length;
   full +4 dBm is wasted current.

Optional next steps for power tuning:

- Disable USB CDC in production builds (`Serial` calls are already absent).
- Lower advertising interval to 200 ms once paired.
- Move PDM mic capture (XIAO Sense) to event-driven mode; the v2 firmware
  does **not** stream audio – classification still happens on the phone or
  companion edge device, matching the existing OpenHear architecture.

## Zephyr alternative (advanced)

For builders on the **nRF Connect SDK** / **Zephyr** path:

- Board target: `xiao_ble` (Zephyr ships an official board definition for
  the XIAO nRF52840 Sense as of NCS ≥ 2.5).
- Use `samples/bluetooth/peripheral` as a template; add a single GATT
  primary service with the two UUIDs above and a write callback that calls
  the same `render_packet()` logic.
- Drive the DRV2605L with `drivers/i2c` + the open-source
  `zephyr/drivers/sensor/drv2605` register definitions (or port the
  Adafruit driver – it is ~200 lines of register writes).
- Power: enable `CONFIG_PM_DEVICE=y`, `CONFIG_BT_CTLR_TX_PWR_MINUS_12=y`,
  and use `pm_state_force(0u, &(struct pm_state_info){PM_STATE_SUSPEND_TO_IDLE,…})`
  in the idle hook.

The Zephyr build remains 100 % open-source and does not require any
proprietary SoftDevice binary.

## Safety reminders (unchanged from v1)

- Cap intensity to 180 / 255 in firmware; do not raise without thermal data.
- Stop on numbness, pain, skin heat, dizziness, or headache.
- Keep skin-side surface below 40 °C; derate at 38 °C.
- BLE is **companion-only**; on-wrist haptics must work with the radio off.
