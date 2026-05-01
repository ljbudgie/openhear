# OpenHear wristband v1 Gerber and fabrication notes

Licence: CERN-OHL-S-2.0.

This KiCad v8 reference project is a buildable starting point, not a one-click
medical product. Before ordering boards, replace functional-block labels with
verified vendor footprints and run KiCad ERC/DRC against the exact fab stack-up.

## Recommended stack-up

- Prototype A: four rigid PCB islands plus separate 0.1 mm FPC actuator tails.
- Prototype B: 3-layer rigid-flex, 0.8 mm FR-4 islands, 0.10-0.15 mm polyimide flex.
- Minimum track/space: 0.15/0.15 mm; minimum drill: 0.20 mm; finish: ENIG.
- No exposed nickel/copper against skin; cover user-facing conductors with solder
  mask, conformal coat, enclosure, and medical silicone.

## Routing constraints

- Star-route motor supply returns; do not share MEMS ground returns with LRA loops.
- Keep PDM/I2S clock/data traces away from actuator drive and charger switch nodes.
- Put test pads on every muxed I2C branch and every actuator ring power rail.
- Leave keep-outs under microphone acoustic ports and enclosure drain/test ports.

## Latency path notes

The v1 off-the-shelf path approaches `AIDS_FREE_ARCHITECTURE.md` with DMA capture,
short filterbank windows, precomputed audiogram LUTs, and deterministic haptic
scheduling. BLE is companion-only; no acoustic event must traverse a phone or
cloud service before reaching skin.

## Fabrication export checklist

1. Confirm fab stack-up in Board Setup.
2. Run ERC and DRC.
3. Plot F.Cu, In1.Cu, B.Cu, mask, silkscreen, Edge.Cuts, and paste if needed.
4. Generate metric drill files.
5. Tell the fab which sections are flex and which are rigid.
