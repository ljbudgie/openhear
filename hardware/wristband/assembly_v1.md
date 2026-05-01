# OpenHear aids-free wristband v1 assembly and 3D-printing guide

Licences: hardware CERN-OHL-S-2.0; documentation CC-BY-SA-4.0. This is a DIY
research sensory-substitution prototype, not a certified hearing aid or medical
device. It does not diagnose, treat, or cure hearing loss. A clinical version
would require a formal Class IIa-style safety case; builders assume prototype risk.

## Printer settings

### SLA/MSLA resin shell

- Resin: biocompatible dental/surgical-guide resin where possible; otherwise fully
  seal with medical-grade silicone before skin contact.
- Layer height: 0.03-0.05 mm.
- Exposure: start with vendor profile; tune until 0.30-0.50 mm pockets remain accurate.
- Orientation: 30-45° off the build plate, dorsal battery opening upward.
- Supports: medium supports on outer wall/lugs; avoid pockets, mic ports, sealing lips.
- Wash: two-stage IPA wash, 3-5 min dirty bath then 2-3 min clean bath.
- Cure: vendor-specified cure; inspect for tackiness before silicone coating.

### FDM/TPU alternatives

- Shell: PETG or PA12-CF, 0.12-0.16 mm layer, 0.4 mm nozzle.
- Strap/skin liner: TPU 85A-95A, 0.16-0.20 mm layer, 3 perimeters, 20-35% gyroid.
- Do not rely on raw FDM layer lines for IP67; use gasket compression and coating.

## Post-processing

1. Wet-sand user-facing edges with 600 then 1000 grit.
2. Clean mic ports with a 1.0 mm hand drill only; do not enlarge acoustic paths.
3. Apply conformal coat to electronics, leaving connectors and mic membranes clear.
4. Apply medical silicone dip/overmold to the skin side, preserving the skin gap.
5. Fit IP67 acoustic membrane dots over every mic port.

## Wiring overview

```text
        MIC1..MIC8        IMU
            │              │
            ├── PDM/I2S ───┤
            │              │
      ┌─────▼──────────────▼─────┐
      │ ESP32-S3 or RP2040 core  │  BLE companion only
      │ DMA capture + scheduler  │────────────── phone UI/export
      └─────┬──────────────┬─────┘
            │ I2C/SPI      │ v0 shim UART/PWM
      ┌─────▼─────┐   ┌────▼──────┐
      │ TCA9548A  │   │ micro:bit │ optional upgrade bridge
      └─────┬─────┘   └───────────┘
            │
   ┌────────▼────────┐
   │ DRV2605L banks  │ 8 drivers starter / 16 drivers dense
   └──┬──┬──┬──┬─────┘
      │  │  │  │
     LRA ring/column actuator lattice on flex tails
```

## Assembly steps

1. Print the selected shell from `cad/parametric_wristband_v1.scad` and verify fit.
2. Dry-fit LRAs into pockets; sand pockets lightly rather than forcing actuators.
3. Build MCU/power island: charger, regulator, MCU/module, USB-C, battery connector.
4. Confirm 3.3 V rail quiescent current before adding haptic drivers.
5. Add muxes and DRV2605L drivers. Validate each I2C branch with one LRA.
6. Add MEMS microphones and IMU. Keep silicone, dust, and flux out of acoustic ports.
7. Route flex PCB tails or silicone wire harnesses through flex channels.
8. Install protected batteries in the hot-swap cartridge and verify charger termination.
9. Flash `firmware/openhear_firmware_v1.py`; keep BLE disabled during latency tests.
10. Seal with silicone gasket, close screws evenly, and run a dry ingress test.

## Safety checklist

- Start with intensity cap 32/255 and no more than 5 minutes continuous wear.
- Stop for numbness, pain, skin redness, heat, dizziness, or headache.
- Keep user-facing surface below 40 °C; derate at 38 °C.
- Do not sleep with a prototype until battery, charger, and thermal tests pass.
- IP67 DIY test: sealed empty shell only, 1 m water for 30 min before live electronics.
- Burgess Principle binary test: if raw audio, audiogram data, or adaptation data
  must leave the device/cloud to function, the build fails.
