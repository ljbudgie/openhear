# Zero-Solder Assembly Guide: OpenHear v1.5 No-Solder Modular Edition

Welcome. This is the **Print → Plug → Flash → Wear** build. If you can 3D print a part, plug in a USB cable, and match labels, you can assemble this wristband.

Prototype notice: this is an open research sensory-substitution device, not a certified medical device. Start at low intensity, stop if anything feels hot or uncomfortable, and keep all data local.

## Photo checklist

Add photos when building your own copy:

- `[photo: printed main body, actuator lattice, strap, and battery cartridge]`
- `[photo: labelled pre-wired actuators A00-A23]`
- `[photo: MCU module clicked into bay]`
- `[photo: DRV2605L modules plugged into the mux with JST-SH cables]`
- `[photo: magnetic pogo connector gold-dot orientation]`
- `[photo: battery cartridge removed and hot-swapped]`
- `[photo: USB flashing screen]`
- `[photo: first low-intensity haptic test]`

## Before you start

You need:

- A 3D printer.
- A USB-C cable.
- Printed parts from `cad/parametric_modular_wristband_v1.5.scad`.
- Plug-and-play electronics from `BOM.csv`.
- Number labels for the actuator leads.

You do **not** need:

- Soldering iron.
- Crimping tool.
- Wire stripper.
- Breadboard jumper cutting.
- Oscilloscope or bench supply for the starter build.

## Step 1: Print

1. Open `cad/parametric_modular_wristband_v1.5.scad` in OpenSCAD.
2. Set `actuator_count = 24` for the weekend starter build or `64` for the dense research build.
3. Set `wrist_size` to the wearer's wrist circumference in millimetres.
4. Keep `pogo_pin_spacing = 2.54` unless your chosen magnetic connector uses another pitch.
5. Start with `snap_fit_tolerance = 0.35` for resin/PETG or `0.50` for rougher FDM printers.
6. Export STL files manually or run:

```bash
cd hardware/wristband/v1.5-no-solder/cad
./export_stls.sh
```

7. Print the main body, actuator lattice, strap/liner, and battery cartridge.
8. Remove supports and make sure every module bay clicks without force.

## Step 2: Label every plug

1. Put the 24 starter actuators on the table in a line.
2. Label them `A00` through `A23` before inserting anything.
3. For 64 actuators, label `A00` through `A63` and sort them into four rows: `R0`, `R1`, `R2`, `R3`.
4. Label JST-SH I2C cables as `I2C-IN`, `MUX-0`, `MUX-1`, etc.
5. Label the battery cartridge as `BATTERY - protected LiPo only`.

## Step 3: Click in the actuator lattice

1. Hold the printed main body with the skin side facing down.
2. Press actuator `A00` into the first socket at the left edge of the active arc.
3. Continue around the wristband until `A23` is seated.
4. The wire exits should point toward the outer module bays, not toward skin.
5. Press the click-in lattice retainer over the actuator row. It should flex slightly and snap in.
6. If a socket is tight, sand the printed pocket lightly. Do not force an actuator can.

## Step 4: Install the modules

1. Click the MCU module into the MCU bay.
2. Click the TCA9548A mux into the haptic-driver bay.
3. Click DRV2605L modules into their numbered bay positions.
4. Click the mic module or mic array into the mic bay.
5. Click the empty battery cartridge into its bay to verify the latch.

## Step 5: Plug the JST cables

Starter 24-actuator build:

1. USB/MCU `3V3`, `GND`, `SDA`, `SCL` go to the TCA9548A input through a JST-SH/STEMMA QT cable.
2. TCA9548A branch `0` goes to DRV bank `0`.
3. TCA9548A branch `1` goes to DRV bank `1`.
4. Continue until all eight DRV2605L modules are plugged in.
5. Plug actuators `A00-A02` into driver bank `0`, `A03-A05` into bank `1`, and continue by the mapping in `firmware_notes.md`.

Dense 64-actuator build:

1. Use two TCA9548A mux modules or a prebuilt 16-branch I2C hub.
2. Plug four rows of 16 actuators as `R0C00-R3C15`.
3. Keep row cables in the printed channels so the strap does not pinch them.

## Step 6: Magnetic pogo orientation

Use a consistent orientation everywhere:

```text
Gold dot / triangle / red mark side = power side
Pin 1 = VBAT or 5V, only on battery/charger docks
Pin 2 = GND
Pin 3 = 3V3
Pin 4 = SDA
Pin 5 = SCL
Pin 6 = INT/EN or actuator-bank enable
```

Rules:

- Pogo pairs must be keyed so they cannot rotate 180° and reverse power.
- Put two 3x1 mm magnets beside each pogo block with opposite polarity, so wrong modules repel instead of clicking in.
- Mark the enclosure with a small printed triangle on the pin-1 side.
- If using JST instead of pogo, use keyed JST only and never force a plug.

## Step 7: Battery cartridge and hot-swap

1. Use only protected LiPo packs with factory JST-PH connectors.
2. Plug the LiPo into the USB-C charger module inside the cartridge.
3. Close the cartridge lid by snap-fit or hand thumb screw.
4. Slide the cartridge into the wristband until the magnets align.
5. To hot-swap, hold the wristband, pull the thumb tab, remove the cartridge, and slide in a charged cartridge.
6. The MCU should brown-out safely; restart the firmware after swapping.
7. Never carry loose LiPo cells in a pocket with metal objects.

## Step 8: Flash

1. Connect USB-C directly to the MCU module.
2. Put the board into bootloader mode using the board vendor's button sequence.
3. Flash MicroPython/CircuitPython/Arduino firmware following `firmware_notes.md`.
4. Copy the OpenHear v1 scheduler and haptic mapper adaptation.
5. Keep intensity capped at 32/255 for first wear.

## Step 9: First test

1. Put the wristband on a table, not on skin.
2. Run the lowest-intensity actuator walk test.
3. Confirm the pulses move from `A00` to `A23` in order.
4. Wear for one minute at low intensity.
5. Stop immediately for heat, pain, numbness, redness, dizziness, or headache.

## Step 10: Use the aids-free mapping

The v1.5 hardware keeps the v1 OpenHear mapping target:

- 24 Bark-like bands by default.
- Audiogram-weighted intensity curves.
- Direction/spatial cue support when a mic array and IMU are installed.
- Local-only operation; no cloud dependency.
- Sub-10 ms starter haptic onset target with direct local processing.

The phone or computer may be used for setup, export, or training UI, but the hearing path must continue to run locally.
