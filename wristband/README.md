# OpenHear wristband v1.0.0 prototype

This is the release-facing home for the first Sharp Hearing clinic prototype.
The existing implementation stays in `stream/` and `hardware/wristband/`; this
directory gives the prototype one canonical path for firmware and setup docs.

## Canonical release paths

- Firmware to flash: `wristband/openhear_firmware.py`
- Live classifier wrapper: `yamnet_classifier.py`
- Audiogram-to-BLE command wrapper: `haptic_commander.py`
- End-to-end runtime: `stream/wristband_runtime.py`
- Legacy firmware mirror retained for compatibility: `hardware/wristband/firmware.py`

## Frozen v1.0.0 scope

The clinic prototype intentionally ships with seven sound classes only:

| Sound | Class ID | Pattern ID | Dominant frequency | Meaning |
|---|---:|---:|---:|---|
| silence | 0 | 0 | — | no haptic output |
| voice | 1 | 1 | 1000 Hz | speech and conversation |
| doorbell | 2 | 2 | 2000 Hz | doorbells and chimes |
| alarm | 3 | 3 | 3150 Hz | sirens, alarms, buzzers |
| dog | 4 | 4 | 500 Hz | barking and howls |
| traffic | 5 | 5 | 500 Hz | road traffic and horns |
| media | 6 | 6 | 1000 Hz | music, television, radio |

## Stable packet contract

Every Python sender and the micro:bit firmware use the same 3-byte BLE UART
packet:

```text
[sound_class_id, intensity, pattern_id]
```

- byte 0: stable sound class ID
- byte 1: audiogram-weighted intensity in the range `0..255`
- byte 2: stable haptic pattern ID

The intensity byte stays based on the current dominant-frequency lookup plus the
existing audiogram threshold buckets.

## micro:bit v2 motor mapping

- `P0` drives the **left** motor
- `P1` drives the **right** motor

The seven v1.0.0 patterns are unchanged from the prototype firmware.

## Windows clinic PC setup

1. Install Python 3.10+ on Windows.
2. Open PowerShell in the repository root.
3. Install dependencies:

   ```powershell
   py -m pip install -r requirements.txt
   ```

4. Download a local YAMNet `.tflite` file and keep its path on disk.
5. Use the bundled official label CSV at `stream/data/yamnet_class_map.csv`.
6. Pair or confirm visibility of the micro:bit advertising as `OpenHear`.

## Flashing and bench test

1. Open `wristband/openhear_firmware.py` in the micro:bit Python Editor or Mu.
2. Flash the board and confirm the display shows `H`.
3. Confirm the transistor stage uses `P0` for the left motor and `P1` for the right motor.
4. Run a dry packet check:

   ```powershell
   py -m haptic_commander --audiogram PATIENT.json --sound-class alarm --dry-run
   ```

5. Run a live BLE bench test:

   ```powershell
   py -m haptic_commander --audiogram PATIENT.json --sound-class alarm
   ```

6. Confirm the wristband renders the alternating alarm pattern.

## Sharp Hearing demo workflow

1. Export or save the patient audiogram as JSON.
2. Flash `wristband/openhear_firmware.py`.
3. Confirm the micro:bit advertises as `OpenHear`.
4. Optionally validate the live classifier alone:

   ```powershell
   py -m yamnet_classifier --model C:\models\yamnet.tflite --limit 10
   ```

5. Run the full wristband pipeline:

   ```powershell
   py -m stream.wristband_runtime --audiogram PATIENT.json --model C:\models\yamnet.tflite --labels stream/data/yamnet_class_map.csv
   ```

6. Trigger known sounds from the seven-class set and confirm that higher loss at
   the dominant frequency produces a stronger intensity byte and stronger haptic
   output.

## Noahlink status

Direct Noahlink extraction is not the release blocker for this prototype.
The wristband flow already consumes audiogram JSON, while direct parsing in
`core/read_fitting.py` and `audiogram/reader.py` still contains placeholder
frame parsing that needs confirmed real-device validation later.
