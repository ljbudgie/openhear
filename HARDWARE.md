# HARDWARE.md — Noahlink Wireless 2 Setup & Fitting Software

This document covers the physical setup of the Noahlink Wireless 2 USB
programmer and links to the fitting software used to interact with Phonak
and Signia hearing aids on Windows 11.

---

## 1. Noahlink Wireless 2

### What it is
The **Noahlink Wireless 2** (manufactured by HIMSA) is a USB dongle that
communicates with Bluetooth-capable hearing aids using the HIMSA wireless
fitting protocol.  It is the bridge between fitting software running on a
Windows PC and the hearing aids worn by the user.

### USB HID identifiers
| Property    | Value  |
|-------------|--------|
| Vendor ID   | 0x0484 |
| Product ID  | 0x006E |

Verify on your machine with Python:

```python
import hid
for d in hid.enumerate():
    print(hex(d['vendor_id']), hex(d['product_id']), d['product_string'])
```

### Driver installation (Windows 11)
1. Plug the Noahlink Wireless 2 into a USB-A port.
2. Windows Update usually installs the HID driver automatically.
3. If not, download the HIMSA Noahlink Wireless software from
   <https://www.himsa.com/noahlink-wireless/> and run the installer.
4. Confirm the device appears in **Device Manager → Human Interface Devices**
   as *Noahlink Wireless 2*.

### Python `hid` library access (Windows)
The `hid` PyPI package (wraps `hidapi`) requires no additional drivers on
Windows beyond the standard HID stack.

```
pip install hid
```

---

## 2. Phonak Naída M70-SP — Fitting Software

| Item           | Detail |
|----------------|--------|
| Platform       | Marvel (M-series) |
| Form factor    | Size 13 BTE (Behind-the-Ear) |
| Connectivity   | Bluetooth Classic (A2DP / HFP) |
| Fitting tool   | **Phonak Target** |
| Download       | Requires a licensed hearing care professional login at <https://www.phonak.com/professionals> |

### Pairing for audio streaming (Windows 11)
1. Open **Settings → Bluetooth & devices → Add device → Bluetooth**.
2. Put the Naída M70-SP into pairing mode (hold both buttons for 3 s; LED
   flashes rapidly).
3. Select the device from the list; accept the pairing request.
4. Once paired, the aid appears as a standard Windows audio output device.
5. Set `OUTPUT_DEVICE_INDEX` in `dsp/config.py` to the device's PyAudio index
   (use `python -m stream.bluetooth_output --list` to find it).

---

## 3. Signia Insio 7AX — Fitting Software

| Item           | Detail |
|----------------|--------|
| Platform       | AX (Augmented Xperience) |
| Form factor    | ITC custom mould (In-The-Canal) |
| Connectivity   | Made-for-iPhone (MFi) Bluetooth LE |
| Fitting tool   | **Connexx** (by Signia / WS Audiology) |
| Download       | Requires a licensed hearing care professional login at <https://www.signia-pro.com> |

### Windows streaming caveat
The Insio 7AX uses Apple's MFi Bluetooth LE stack, which is not natively
supported on Windows.  For Phase 1 of OpenHear:

- Connect the Insio 7AX to an iPhone using the **Signia app**.
- Use the iPhone as a Bluetooth relay (play audio on the iPhone, route to
  the aid via MFi).
- Share iPhone audio to the Windows PC via a virtual audio cable solution
  (e.g. VB-Cable) or AirPlay if both devices are on the same network.

Native Windows MFi support is planned for a future phase.

---

## 4. Fitting Software Comparison

| Software     | Manufacturer   | Protocol       | Open-source? |
|--------------|----------------|----------------|--------------|
| Phonak Target | Phonak        | Noahlink / USB | No           |
| Connexx      | Signia (WSA)   | Noahlink / USB | No           |
| NOAH 4       | HIMSA          | HIMSA protocol | No           |

OpenHear does **not** depend on any of the above tools at runtime.  The
`core/read_fitting.py` module reads fitting data directly via USB HID and
currently exports the raw fitting payload to JSON; typed field parsing remains
pending confirmed HIMSA frame definitions.

---

## 5. Useful Links

- HIMSA (Noahlink Wireless 2 manufacturer): <https://www.himsa.com>
- Phonak professionals portal: <https://www.phonak.com/professionals>
- Signia professionals portal: <https://www.signia-pro.com>
- `hid` Python package: <https://pypi.org/project/hid/>
- PyAudio: <https://pypi.org/project/PyAudio/>

---

## 6. OpenHear Wristband prototype (micro:bit v2)

The first OpenHear wristband prototype uses a **BBC micro:bit v2**, two coin
vibration motors, two **2N2222** NPN transistors, two flyback diodes, and a
LiPo supply.  The Python side runs on Windows and sends a 3-byte BLE UART
packet to the micro:bit:

```
[sound_class_id, intensity_0_to_255, pattern_id]
```

### Pin map

| Function | micro:bit pin | Notes |
|---|---|---|
| Left motor driver | `P0` | Through 2N2222 transistor stage |
| Right motor driver | `P1` | Through 2N2222 transistor stage |
| Common ground | `GND` | Must be shared between micro:bit and motor supply |

### Motor driver wiring

Use a low-side transistor switch for each motor:

1. **Motor +** → battery **+**
2. **Motor -** → **collector** of a 2N2222
3. **Emitter** → common **GND**
4. micro:bit `P0` or `P1` → **1 kΩ resistor** → transistor **base**
5. Flyback diode across the motor:
   - diode **cathode** to motor/battery **+**
   - diode **anode** to the transistor collector / motor **-**
6. Tie the micro:bit ground and motor battery ground together

Do **not** drive the motors directly from the GPIO pins.  The transistor
stage is required because the micro:bit GPIO pins are current-limited.

### Exact motor driver wiring (tested values)

Use the same component values on both the left and right motor channels:

| Position | Exact part/value | Count | Notes |
|---|---|---:|---|
| Q1, Q2 | 2N2222A or PN2222A NPN transistor | 2 | TO-92 package is easiest on stripboard |
| R1, R2 | **1 kΩ**, 0.25 W, ±5% base resistor | 2 | Between `P0`/`P1` and the transistor base |
| R3, R4 | **10 kΩ**, 0.25 W, ±5% base pulldown | 2 | Base to GND so the motors stay off during boot |
| D1, D2 | **1N5819** Schottky flyback diode | 2 | Cathode to battery `+`, anode to collector / motor `-` |
| M1, M2 | 3 V coin vibration motor, ≤150 mA stall current | 2 | Keep the motor supply within the motor datasheet limit |

Per channel, wire it in this exact order:

1. micro:bit `P0`/`P1` → **1 kΩ** resistor → transistor **base**
2. transistor **base** → **10 kΩ** resistor → **GND**
3. transistor **emitter** → **GND**
4. motor **-** → transistor **collector**
5. motor **+** → motor battery **+**
6. **1N5819** across the motor, **cathode** to battery **+**, **anode** to collector
7. motor battery **-** tied to micro:bit **GND**

Practical limits for bench testing:

- Start at one motor only and confirm the transistor stays cool at a continuous
  `intensity=64` manual test.
- Keep first-power-on tests below **30 seconds** at a time until you have
  measured motor current and confirmed the wiring polarity.
- If the motor supply exceeds **3.7 V**, or a motor stalls above **150 mA**,
  do not use this transistor stage without redesigning the driver.

### Firmware flashing (Windows)

The simplest reliable Windows workflow is to flash from the official
micro:bit Python Editor or Mu Editor:

1. Install the **micro:bit Python Editor** or **Mu Editor** on Windows 11.
2. Connect the micro:bit v2 over USB and wait for the `MICROBIT` drive to
   appear in File Explorer.
3. Open `hardware/wristband/firmware.py` in the editor.
4. Click **Flash**. The editor packages the script into a MicroPython image
   and copies it to the board.
5. Wait for the yellow status LED on the micro:bit to stop flashing and for
   the board to reboot.
6. Confirm the display shows `H`; that is the wristband firmware idle marker.
7. If the board still runs an older image, press the reset button once and
   flash again with no other serial tools open.

If flashing fails on Windows:

- swap to a known data-capable USB cable,
- plug directly into the PC instead of a hub,
- close any serial terminal that may be holding the board,
- re-open the editor as Administrator once, then retry.

### Firmware

- Flash `hardware/wristband/firmware.py` to the micro:bit using a BLE-capable
  MicroPython build.
- The firmware listens for BLE UART packets and renders these patterns:
  - `voice` → both motors, gentle pulse
  - `doorbell` → two sharp pulses
  - `alarm` → rapid alternating left/right
  - `dog` → right-only pulse
  - `traffic` → left-only pulse
  - `media` → slow both-motor pulse
  - `silence` → no output

### Windows runtime

Use the integrated wristband runtime:

```bash
python -m stream.wristband_runtime --audiogram PATIENT.json --manual-sound alarm
python -m stream.wristband_runtime --audiogram PATIENT.json --model yamnet.tflite --labels stream/data/yamnet_class_map.csv
```

The runtime:

1. loads the patient's audiogram,
2. classifies sound windows into the OpenHear wristband classes,
3. scales the haptic intensity from the audiogram thresholds, and
4. sends the packet over BLE to the micro:bit advertising as `OpenHear`.

### Windows BLE debugging checklist

If the micro:bit does not appear or connect on Windows:

1. Confirm the firmware is running: the micro:bit should boot to `H`.
2. Make sure no other host is already connected to the micro:bit over BLE.
3. In **Settings → Bluetooth & devices**, remove any stale `OpenHear` pairing,
   then toggle Bluetooth off and back on.
4. Verify Windows can see the advert with Bleak:

   ```powershell
   py -c "import asyncio; from bleak import BleakScanner; print([(d.name, d.address) for d in asyncio.run(BleakScanner.discover(timeout=8.0)) if d.name])"
   ```

5. If `OpenHear` is missing, power-cycle the micro:bit and rerun the scan.
6. If `OpenHear` is present but the runtime still fails, increase the scan
   timeout:

   ```powershell
   py -m stream.wristband_runtime --audiogram PATIENT.json --manual-sound alarm --scan-timeout 15
   ```

7. If Bleak raises a Windows backend error, confirm you are using a normal
   64-bit Python build and that Windows has Bluetooth permission enabled for
   desktop apps.
