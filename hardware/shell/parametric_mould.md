# Parametric Ear Mould Design

## Concept

Every ear is different on the outside. But the internal channels of a hearing aid ear mould follow a standard pattern. The parametric mould design separates these two concerns:

- **Outer shape:** Unique to each user. Comes from scanning your ear impression (see the [3D printing guide](README.md) for how to create this).
- **Internal channels:** Standardised. Follow a parametric template that can be applied to any scanned ear shape.

This means you scan once, then apply the same channel template regardless of ear shape. The template handles the receiver bore, vent channel, and sound tube — you just need to position them correctly within your scan.

---

## Channel Parameters

### Vent Channel

The vent equalises pressure between the sealed ear canal and the outside air. Without it, you get the occlusion effect — your own voice sounds boomy and unnatural because bone-conducted sound is trapped in the sealed canal.

Vent diameter is determined by hearing loss severity:

| Hearing Loss | Vent Diameter | Type | Purpose |
|-------------|---------------|------|---------|
| Severe-to-profound (71+ dB HL) | **0.8mm** | Pressure vent | Minimum opening. Equalises static pressure only. Preserves maximum acoustic seal for bass amplification. You need every dB you can get |
| Moderate (41–70 dB HL) | **1.5mm** | Standard vent | Balanced. Some bass leakage is acceptable in exchange for reduced occlusion. Most users find this comfortable for all-day wear |
| Mild (26–40 dB HL) | **2.5mm** | Open vent | Maximum comfort. Natural bass hearing is mostly intact, so bass leakage through the vent doesn't matter. Significantly reduces occlusion |

**Vent placement:** The vent runs parallel to the receiver bore, offset by at least 1.5mm (wall-to-wall) to maintain structural integrity. It exits at the canal tip on the medial (inner) end and at the concha surface on the lateral (outer) end.

**Vent shape:** Circular cross-section throughout. Constant diameter (no taper). Straight path preferred — gentle curves acceptable if the ear canal shape requires it, but avoid sharp bends that would restrict airflow.

### Receiver Bore

The receiver bore is the channel where the balanced armature receiver (speaker) sits. It must be sized precisely for a friction fit — tight enough that the receiver doesn't fall out, loose enough that you can remove it for replacement or servicing.

| Receiver Model | Bore Diameter | Bore Length | Tolerance | Notes |
|---------------|--------------|-------------|-----------|-------|
| Knowles ED-29689 | **2.5mm** | **8.0mm** | ±0.1mm | Smaller receiver. Suitable for mild-to-moderate loss |
| Knowles WBFK-30019 | **2.8mm** | **9.5mm** | ±0.1mm | Larger receiver. Higher output for moderately-severe to severe loss |
| Knowles WBFK-30095 | **2.8mm** | **9.5mm** | ±0.1mm | Same physical housing as WBFK-30019. Maximum output for profound loss |

**Tolerance note:** The ±0.1mm tolerance is critical. Too loose (>0.1mm oversize) and the receiver rattles, causing buzzing at certain frequencies. Too tight (>0.1mm undersize) and you risk cracking the receiver housing when inserting it. Resin printers at 0.05mm layer height can achieve this tolerance.

**Bore placement:** The receiver bore runs along the central axis of the canal portion of the mould. The receiver tip (sound output end) should sit flush with the medial tip of the mould — the sound exits directly into the ear canal.

**Wire channel:** A 1.2mm channel runs from the receiver pocket to the outer surface of the mould for the receiver wire. This channel should have a gentle curve — no sharp bends that would stress the wire.

### Sound Tube Channel

If you are using a traditional BTE (Behind-The-Ear) configuration with an external receiver and sound tube instead of a RIC (Receiver-In-Canal) configuration, the mould needs a sound tube channel instead of a receiver bore.

| Parameter | Value | Notes |
|-----------|-------|-------|
| Inner diameter | **1.93mm** | Standard #13 tubing compatible |
| Outer diameter | **3.0mm** | Wall thickness for structural support |
| Length | Full canal length | From concha surface to canal tip |

**Tubing:** Standard #13 hearing aid tubing (1.93mm ID, 3.18mm OD) is available from hearing aid supply companies. It is flexible PVC and should be replaced every 3–6 months as it yellows and stiffens with age.

> **Note:** The RIC (Receiver-In-Canal) configuration is recommended for OpenHear builds. It produces better high-frequency response than sound tube delivery and eliminates the tubing resonance peak around 1 kHz that affects tube-fit devices.

---

## Applying the Template

### Using Meshmixer

1. **Open your scanned ear mould STL** in Meshmixer.

2. **Create the vent channel.** Insert a cylinder primitive with the appropriate diameter (0.8mm, 1.5mm, or 2.5mm based on your hearing loss). Position it parallel to the canal axis, offset 1.5mm from the receiver bore centreline. Extend it through the full length of the mould.

3. **Create the receiver bore.** Insert a cylinder primitive with the appropriate diameter for your receiver model. Position it along the central axis of the canal portion. The depth should match the bore length from the table above.

4. **Create the wire channel.** Insert a 1.2mm cylinder from the receiver pocket to the outer surface. Use Meshmixer's curve tools to create a gentle path.

5. **Boolean subtract.** Select all channel cylinders and your mould body. Edit → Boolean Difference. This cuts the channels out of the solid mould.

6. **Inspect.** Check that all channels are clear (no blocked sections from boolean artifacts). Check wall thickness — minimum 1.0mm between any channel and the outer surface.

7. **Export as STL** for printing.

### Using Blender

The same operations work in Blender using the Boolean modifier:

1. Create cylinder meshes for each channel
2. Position and rotate to match the template dimensions
3. Apply Boolean modifier (Difference operation) to the mould body
4. Apply the modifier and clean up any non-manifold geometry

---

## Design Constraints

These constraints apply to all parametric moulds regardless of ear shape:

| Constraint | Value | Reason |
|-----------|-------|--------|
| Minimum wall thickness | 1.0mm | Below this, the mould is fragile and may crack during insertion/removal |
| Minimum channel-to-channel spacing | 1.5mm (wall-to-wall) | Structural integrity between vent and receiver bore |
| Maximum canal depth | 15mm from canal entrance | Safety — deeper insertion risks eardrum contact |
| Receiver bore straightness | <5° deviation from canal axis | Ensures receiver sound output is directed down the ear canal |
| Surface finish | <25μm Ra | Comfort and hygiene. Achievable with 0.05mm layer height + sanding |

---

## Validation

Before using a mould with a powered receiver:

1. **Visual inspection.** All channels clear? No cracks? No sharp edges?
2. **Receiver fit test.** Insert the receiver into the bore by hand. It should slide in with light pressure and hold by friction. Shake test: hold the mould canal-down and shake gently. The receiver should not fall out.
3. **Vent check.** Hold the mould up to a light source. You should see light through the vent channel from end to end.
4. **Fit test (unpowered).** Insert the mould into your ear without any electronics connected. Check comfort and seal quality. Wear for at least 30 minutes before connecting any powered components.
5. **Powered test.** Connect receiver, power on at minimum gain, and gradually increase. See the [safety module](../safety/README.md) for the complete calibration procedure.
