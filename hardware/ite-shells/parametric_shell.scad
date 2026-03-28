// ⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE
// This file is part of OpenHear, an open-source hearing aid project.
// It has not been evaluated by any regulatory body. Consult an audiologist
// before using any hearing device. Use at your own risk.
// License: MIT
//
// parametric_shell.scad — Parametric ITE (In-The-Ear) Hearing Aid Shell
// =====================================================================
// A fully parameterized OpenSCAD model for generating custom ITE hearing
// aid shells. All critical dimensions are exposed as variables so that
// the shell can be adapted to individual ear-canal impressions.
//
// Coordinate convention:
//   X = medial-lateral   (positive toward ear canal)
//   Y = anterior-posterior
//   Z = superior-inferior (positive upward)
//
// All dimensions in millimetres (mm).

// ── User Parameters ─────────────────────────────────────────────────

// --- Canal geometry ---
canal_depth       = 12.0;   // depth of the canal portion [mm]
canal_dia_tip     =  5.0;   // diameter at the canal tip (medial end) [mm]
canal_dia_base    =  7.5;   // diameter at the canal base (junction with shell body) [mm]
canal_taper_angle =  atan2((canal_dia_base - canal_dia_tip) / 2, canal_depth);

// --- Shell body ---
shell_length      = 18.0;   // overall length of the concha / body portion [mm]
shell_width       = 14.0;   // width of the body (anterior-posterior) [mm]
shell_height      = 11.0;   // height of the body (superior-inferior) [mm]
wall_thickness    =  1.2;   // shell wall thickness [mm]

// --- Faceplate ---
faceplate_length  = 14.0;   // faceplate X extent [mm]
faceplate_width   = 12.0;   // faceplate Y extent [mm]
faceplate_thick   =  1.5;   // faceplate thickness [mm]
snap_lip_height   =  0.8;   // snap-fit retention lip height [mm]
snap_lip_depth    =  0.4;   // snap-fit lip radial protrusion [mm]

// --- Vent (anti-occlusion) ---
vent_diameter     =  1.4;   // vent bore diameter [mm] (typ. 0.8–2.0)
vent_offset_y     =  2.5;   // lateral offset from canal centre [mm]

// --- Microphone ports (dual, for basic beamforming) ---
mic_port_dia      =  1.0;   // microphone port opening diameter [mm]
mic1_pos          = [ 3.0,  3.5, shell_height / 2];  // front mic [mm]
mic2_pos          = [-3.0,  3.5, shell_height / 2];  // rear mic [mm]
mic_port_depth    =  faceplate_thick + 0.5;           // bore depth through faceplate [mm]

// --- Receiver (speaker) bore ---
receiver_bore_dia =  1.8;   // receiver sound-outlet bore diameter [mm]
receiver_bore_len =  canal_depth + 2.0;  // bore runs full canal length [mm]

// --- Battery compartment (size 10 zinc-air cell: ⌀5.8 × 3.6 mm) ---
batt_dia          =  6.2;   // compartment inner diameter (clearance fit) [mm]
batt_height       =  4.0;   // compartment depth [mm]
batt_pos          = [0, -2.0, 0];  // centre position inside shell body [mm]

// --- Wax guard recess ---
wax_recess_dia    =  2.5;   // wax guard seat outer diameter [mm]
wax_recess_depth  =  1.0;   // recess depth at canal tip [mm]

// --- Internal wire channel ---
wire_channel_dia  =  1.2;   // routing channel for receiver / mic wires [mm]

// --- Lotus-effect microstructure (experimental) ---
pillar_dia        =  0.15;  // re-entrant pillar shaft diameter [mm]
pillar_cap_dia    =  0.25;  // mushroom cap diameter [mm]
pillar_height     =  0.30;  // total pillar height [mm]
pillar_spacing    =  0.40;  // centre-to-centre pitch [mm]

// --- Rendering quality ---
$fn = 64;  // global facet count for curved surfaces


// ── Modules ─────────────────────────────────────────────────────────

// ---- shell_body() ----
// Main hollow concha-filling body, modelled as a rounded box with
// uniform wall thickness removed from the interior.
module shell_body() {
    difference() {
        // Outer hull — rounded rectangular solid
        hull() {
            for (sx = [-1, 1], sy = [-1, 1])
                translate([
                    sx * (shell_length / 2 - 3),
                    sy * (shell_width / 2 - 3),
                    0
                ])
                cylinder(r = 3, h = shell_height);
        }

        // Inner cavity (offset inward by wall_thickness)
        translate([0, 0, wall_thickness])
        hull() {
            for (sx = [-1, 1], sy = [-1, 1])
                translate([
                    sx * (shell_length / 2 - 3 - wall_thickness),
                    sy * (shell_width / 2 - 3 - wall_thickness),
                    0
                ])
                cylinder(r = 3, h = shell_height + 1);  // extend past outer hull to open top
        }
    }
}


// ---- canal_portion() ----
// Tapered canal tip extending from the medial face of the shell body.
// The taper matches the ear-canal geometry from impression data.
module canal_portion() {
    translate([0, 0, -canal_depth])
    difference() {
        // Outer tapered cylinder
        cylinder(
            d1 = canal_dia_tip,
            d2 = canal_dia_base,
            h  = canal_depth
        );

        // Hollow core
        translate([0, 0, -0.1])
        cylinder(
            d1 = canal_dia_tip - 2 * wall_thickness,
            d2 = canal_dia_base - 2 * wall_thickness,
            h  = canal_depth + 0.2
        );
    }
}


// ---- faceplate() ----
// Removable lateral faceplate with a perimeter snap-fit retention lip.
// Houses microphone ports and battery door.
module faceplate() {
    translate([0, 0, shell_height]) {
        // Main plate
        hull() {
            for (sx = [-1, 1], sy = [-1, 1])
                translate([
                    sx * (faceplate_length / 2 - 2),
                    sy * (faceplate_width / 2 - 2),
                    0
                ])
                cylinder(r = 2, h = faceplate_thick);
        }

        // Snap-fit lip (perimeter skirt that clicks into shell body)
        difference() {
            hull() {
                for (sx = [-1, 1], sy = [-1, 1])
                    translate([
                        sx * (faceplate_length / 2 - 2),
                        sy * (faceplate_width / 2 - 2),
                        -snap_lip_height
                    ])
                    cylinder(r = 2 + snap_lip_depth, h = snap_lip_height);
            }
            // Remove interior so only lip ring remains
            hull() {
                for (sx = [-1, 1], sy = [-1, 1])
                    translate([
                        sx * (faceplate_length / 2 - 2),
                        sy * (faceplate_width / 2 - 2),
                        -snap_lip_height - 0.1
                    ])
                    cylinder(r = 2, h = snap_lip_height + 0.2);
            }
        }
    }
}


// ---- vent_channel() ----
// Through-bore vent running parallel to the canal axis for pressure
// equalisation and anti-occlusion. Reduces the occlusion effect by
// allowing low-frequency energy to escape.
module vent_channel() {
    total_length = canal_depth + shell_height + faceplate_thick + 2;
    translate([0, vent_offset_y, -canal_depth - 1])
        cylinder(d = vent_diameter, h = total_length);
}


// ---- mic_port(position) ----
// Cylindrical bore through the faceplate for a MEMS microphone.
// Two ports placed apart enable a simple endfire beamformer.
module mic_port(position) {
    translate(position)
        cylinder(d = mic_port_dia, h = mic_port_depth, center = false);
}


// ---- receiver_bore() ----
// Sound outlet channel running from the receiver cavity through the
// canal tip. Terminates at the wax-guard recess.
module receiver_bore() {
    translate([0, 0, -canal_depth - 1])
        cylinder(d = receiver_bore_dia, h = receiver_bore_len);
}


// ---- battery_compartment() ----
// Cylindrical pocket sized for a standard zinc-air button cell.
// Positioned inside the shell body; accessed via faceplate removal.
module battery_compartment() {
    translate([batt_pos[0], batt_pos[1], wall_thickness + 0.5])
        cylinder(d = batt_dia, h = batt_height);
}


// ---- wax_guard_recess() ----
// Shallow circular recess at the canal tip for a push-fit cerumen
// (wax) guard / filter. Protects the receiver from debris ingress.
module wax_guard_recess() {
    translate([0, 0, -canal_depth - wax_recess_depth + 0.01])
        cylinder(d = wax_recess_dia, h = wax_recess_depth);
}


// ---- wire_channel() ----
// Internal routing channel for receiver and microphone wiring.
// Runs from the battery compartment area down through the canal.
module wire_channel() {
    wire_total = canal_depth + shell_height / 2 + 1;
    translate([wire_channel_dia, -wire_channel_dia, -canal_depth])
        cylinder(d = wire_channel_dia, h = wire_total);
}


// ---- lotus_microstructure(area_x, area_y) ----
// Generates a grid of re-entrant mushroom-cap micro-pillars over a
// rectangular patch. When applied (via union) to an exterior surface,
// these structures promote a Cassie-Baxter wetting state, yielding
// superhydrophobic (lotus-effect) behaviour that repels moisture and
// cerumen.
//
// NOTE: These features are at the resolution limit of most SLA / DLP
// printers (~50 µm). Enable only if your fabrication process supports
// sub-200 µm features.
//
// ⚡ PERFORMANCE: This module generates a large grid of tiny cylinders
// (e.g., 35 × 30 = 1050 pillars for a 14 × 12 mm patch). Use F5
// (preview) during design iteration; reserve F6 (render) for final
// output only.
module lotus_microstructure(area_x, area_y) {
    cols = floor(area_x / pillar_spacing);
    rows = floor(area_y / pillar_spacing);

    for (ix = [0 : cols - 1], iy = [0 : rows - 1]) {
        translate([
            ix * pillar_spacing - area_x / 2 + pillar_spacing / 2,
            iy * pillar_spacing - area_y / 2 + pillar_spacing / 2,
            0
        ]) {
            // Pillar shaft
            cylinder(d = pillar_dia, h = pillar_height - pillar_dia / 2);

            // Mushroom cap (re-entrant overhang traps air pockets)
            translate([0, 0, pillar_height - pillar_dia / 2])
                cylinder(
                    d1 = pillar_dia,
                    d2 = pillar_cap_dia,
                    h  = pillar_dia / 2
                );
        }
    }
}


// ── Assembly ─────────────────────────────────────────────────────────

// ---- complete_shell() ----
// Final assembly: unions the positive volumes and subtracts all
// internal channels, ports, and recesses.
module complete_shell() {
    difference() {
        union() {
            shell_body();
            canal_portion();
            faceplate();

            // Optional: apply lotus microstructure to the canal exterior.
            // Uncomment the following block if your printer supports
            // sub-200 µm features.
            // translate([0, 0, -canal_depth])
            //     rotate([0, 0, 0])
            //         lotus_microstructure(
            //             area_x = PI * canal_dia_tip,
            //             area_y = canal_depth
            //         );
        }

        // Subtract internal voids and channels
        vent_channel();
        receiver_bore();
        battery_compartment();
        wax_guard_recess();
        wire_channel();

        // Microphone ports (through faceplate)
        mic_port(mic1_pos + [0, 0, shell_height]);
        mic_port(mic2_pos + [0, 0, shell_height]);
    }
}


// ── Render ───────────────────────────────────────────────────────────
// Invoke the top-level assembly. Call with F5 (preview) or F6 (render)
// in OpenSCAD.
complete_shell();
