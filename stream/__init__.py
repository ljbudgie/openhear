"""
stream package – audio and wearable transport for OpenHear.

Includes:
  - bluetooth_output.py   Existing Bluetooth audio output for hearing aids.
  - ble_haptic.py         BLE UART transport for the micro:bit wristband.
  - haptic_mapper.py      Audiogram-weighted intensity mapping.
  - haptic_packet.py      Single source-of-truth 3-byte BLE packet codec.
  - haptic_policy.py      Sound → haptic decision layer (confidence, refractory).
  - haptic_primitive.py   Parametrised haptic primitives (v2 continuous channels).
  - crowd_arousal.py      Continuous crowd-energy estimation for haptic rendering.
  - sound_classifier.py   YAMNet-oriented sound-class mapping helpers.
  - wristband_runtime.py  End-to-end Windows wristband prototype runner.
"""
