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
python -m stream.wristband_runtime --audiogram PATIENT.json --model yamnet.tflite --labels yamnet_class_map.csv
```

The runtime:

1. loads the patient's audiogram,
2. classifies sound windows into the OpenHear wristband classes,
3. scales the haptic intensity from the audiogram thresholds, and
4. sends the packet over BLE to the micro:bit advertising as `OpenHear`.
