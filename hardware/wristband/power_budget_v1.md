# OpenHear wristband v1 power and thermal budget

Licences: hardware CERN-OHL-S-2.0; documentation CC-BY-SA-4.0.

Target: 18-24 h mixed-use runtime from 2 × 800 mAh protected Li-Po cells while
keeping the skin-facing surface below 40 °C. v1 cannot guarantee this under every
dense haptic scene; it documents the gap and provides derating rules.

| Subsystem | Idle | Typical | Peak | Notes |
|---|---:|---:|---:|---|
| ESP32-S3/RP2040 scheduler | 8 mA | 28 mA | 85 mA | RP2040 has deterministic PIO timing; ESP32-S3 adds BLE |
| 8 MEMS microphones | 6 mA | 10 mA | 14 mA | Duty-cycle only in quiet modes if latency budget allows |
| IMU | 0.1 mA | 0.8 mA | 3 mA | Low-rate pose updates outside spatial mode |
| DRV2605L banks | 2 mA | 8 mA | 24 mA | Driver logic only, not actuator current |
| 24 LRA array | 0 mA | 45-120 mA | 450 mA | Cap simultaneous duty cycle to 25% starter build |
| 64 LRA array | 0 mA | 90-260 mA | 1200 mA | Requires scene scheduler and thermal limits |
| Regulators/charger leakage | 0.03 mA | 2 mA | 8 mA | Choose low-Iq buck; avoid TP4056 for final wearable |
| BLE companion | 0 mA | 3 mA | 25 mA | Disable by default during hearing path |

Two 800 mAh cells in parallel provide roughly 1600 mAh nominal. Practical usable
capacity after regulator loss and safety margin is about 1250-1350 mAh.

- Quiet/voice sparse 24-actuator scene: 55-75 mA average → 17-24 h.
- Mixed urban 24-actuator scene: 95-140 mA average → 9-14 h.
- Dense 64-actuator research scene: 180-320 mA average → 4-7 h unless duty-cycled.

## Thermal policy

1. Maintain a rolling 60 s energy estimate per actuator and per ring.
2. Limit one actuator to 25% duty cycle until calibrated on skin.
3. Limit haptic rail current to 450 mA for 24-actuator builds and 900 mA for bench 64.
4. Begin derating at 38 °C skin-side thermistor; hard-shutdown haptics at 40 °C.
5. Refuse charging while worn unless skin temperature is below 36 °C and tested.

## Gap to the north-star architecture

The sub-5 ms latency budget can be approached for band-energy-to-haptic onset, but
full local classification and source separation below 5 ms still needs the custom
22 nm Hearing NPU described in `docs/AIDS_FREE_ARCHITECTURE.md`. Off-the-shelf
2026 MCUs can run deterministic schedulers and simple filterbanks; they cannot run
always-on high-quality source separation at the target power envelope.
