/* OpenHear aids-free wristband v2 "Premium Slim" parametric CAD
   Fork of hardware/wristband/cad/parametric_wristband_v1.scad.
   Target: daily-wear, Apple Watch Ultra / Whoop 4.0 style rectangular case
           on the Seeed Studio XIAO nRF52840 (or XIAO nRF52840 Sense).
   Hardware licence: CERN-OHL-S-2.0
   Docs licence:     CC-BY-SA-4.0

   Design intent (do not regress from v1):
   - Same 3-byte BLE haptic packet contract  [sound_class_id, intensity, pattern_id]
   - Same 7 YAMNet sound classes + audiogram JSON intensity weighting
   - Same Burgess-Principle local-only data path; BLE is companion-only
   - 100% open-source, sovereign, local-first, individually buildable

   Form factor goals:
   - Rectangular slim case, 42-46 mm long x 36-40 mm wide
   - <= 12 mm total stack thickness (wrist side + electronics + lid)
   - Curved wrist underside (cylindrical sweep) for comfortable contact
   - Internal pockets for: 1x XIAO nRF52840(Sense), 2-4x LRA (coin or 10 mm),
     1x thin 300-500 mAh LiPo, optional 1-2x DRV2605L STEMMA QT carriers,
     pogo/magnetic charging contacts on the lid edge
   - Subtle engraved "OpenHear" logo on the lid
   - IP-ish lid seal lips (mating tongue + groove)
   - 20-22 mm quick-release lug pockets OR integrated TPU strap option
   - FDM/TPU printable, 0.8-1.2 mm walls, 2-3 mm fillets, minimal supports
*/

$fn = 96;

// ============================================================================
// PARAMETERS
// ============================================================================

// ---- Build selection -------------------------------------------------------
build_part      = "case";       // [case, lid, strap_tpu, jig, all_exploded]
strap_style     = "lugs";       // [lugs, integrated_tpu, none]
show_cutaway    = false;        // half-section preview
preview_pcb     = false;        // draw XIAO + LRAs as solids for visual check

// ---- Outer case dimensions (Apple Watch Ultra / Whoop 4.0 feel) -----------
case_length_mm        = 44;     // [40:1:48]   long axis (lug-to-lug body)
case_width_mm         = 38;     // [34:1:42]   short axis (across wrist)
case_total_height_mm  = 11.8;   // [9:0.2:13]  total stack thickness <= 12 mm
case_corner_r_mm      = 6.0;    // [4:0.5:9]   rounded rectangle corner radius
wrist_radius_mm       = 32.0;   // [22:1:45]   cylindrical sweep of underside
wall_thickness_mm     = 1.0;    // [0.8:0.1:1.6]
floor_thickness_mm    = 1.1;    // [0.8:0.1:1.6]
lid_thickness_mm      = 1.2;    // [0.8:0.1:1.8]
fillet_r_mm           = 2.5;    // [1.5:0.1:3.0]
print_tolerance_mm    = 0.20;   // [0.10:0.05:0.40]
skin_relief_mm        = 0.30;   // gentle relief band on wrist face

// ---- XIAO nRF52840 (Sense) pocket -----------------------------------------
// Datasheet: 21.0 x 17.5 mm; height ~3.5 mm incl. shield; USB-C on short side.
xiao_len_mm           = 21.0;
xiao_wid_mm           = 17.5;
xiao_thk_mm           = 3.6;
xiao_usbc_w_mm        = 9.4;
xiao_usbc_h_mm        = 3.6;
xiao_offset_y_mm      = 6.0;    // shift toward "top" of case (away from lugs)

// ---- Battery pocket (thin LiPo, 300-500 mAh) ------------------------------
// Examples: 502535 (5x25x35 mm, ~400 mAh) or 402030 (~250 mAh) or 552535.
battery_len_mm        = 35.0;   // [25:1:42]
battery_wid_mm        = 25.0;   // [18:1:34]
battery_thk_mm        = 5.2;    // [3.5:0.1:6.5]
battery_clearance_mm  = 0.4;

// ---- Haptic actuators ------------------------------------------------------
// Default: 2 small LRA coins (10 mm) flanking the centre line.
// Bump to 4 for richer spatialisation (still fits 44 x 38 mm shell).
actuator_count        = 2;      // [2,3,4]
actuator_d_mm         = 10.0;   // 10 mm LRA coin
actuator_h_mm         = 3.4;
actuator_pitch_mm     = 18.0;   // centre-to-centre across long axis

// ---- DRV2605L STEMMA QT carrier (optional second slot) --------------------
// Adafruit DRV2605L STEMMA QT outline ~ 17.8 x 17.8 mm, ~3 mm thick.
drv_carrier_pocket    = true;
drv_len_mm            = 17.8;
drv_wid_mm            = 17.8;
drv_thk_mm            = 3.2;

// ---- Pogo / magnetic charging pads ----------------------------------------
// Two-pin pogo on the bottom edge of the case (VBUS + GND).
pogo_pin_d_mm         = 2.6;
pogo_pin_pitch_mm     = 4.0;
pogo_pad_recess_mm    = 0.6;

// ---- Lid + IP-ish seal -----------------------------------------------------
seal_lip_w_mm         = 1.2;
seal_lip_h_mm         = 0.7;
seal_lip_relief_mm    = 0.15;   // groove side relief for compression
lid_screw_count       = 0;      // 0 = snap-fit only; 4 = M1.6 corner screws
lid_screw_d_mm        = 1.7;
lid_screw_head_d_mm   = 3.0;

// ---- Strap interface -------------------------------------------------------
lug_width_mm          = 22.0;   // [20:1:24] standard quick-release width
lug_thickness_mm      = 3.0;
lug_pin_d_mm          = 1.6;    // M1.5 spring-bar pin clearance
lug_recess_depth_mm   = 1.8;
tpu_strap_thk_mm      = 2.0;    // integrated_tpu band initial section
tpu_strap_total_mm    = 160;    // unwrapped length per side
tpu_strap_taper_pct   = 0.85;

// ---- Branding --------------------------------------------------------------
engrave_logo          = true;
logo_text             = "OpenHear";
logo_font             = "Liberation Sans:style=Bold";
logo_size_mm          = 3.2;
logo_depth_mm         = 0.4;

// ---- Mic vent (optional, only when XIAO Sense PDM mic is enabled) ---------
mic_vent_d_mm         = 0.9;
mic_vent_offset_mm    = 6.0;    // from case centre toward "top" edge

// ============================================================================
// DERIVED
// ============================================================================
inner_len    = case_length_mm - 2 * wall_thickness_mm;
inner_wid    = case_width_mm  - 2 * wall_thickness_mm;
inner_h      = case_total_height_mm - floor_thickness_mm - lid_thickness_mm;
inner_corner = max(case_corner_r_mm - wall_thickness_mm, 0.6);
lid_corner   = case_corner_r_mm;

// ============================================================================
// PRIMITIVES
// ============================================================================
module rounded_rect(size, r) {
    // 2D rounded rectangle via minkowski-free hull of corner circles
    w = size[0]; d = size[1];
    hull() {
        for (x = [-w/2 + r, w/2 - r])
            for (y = [-d/2 + r, d/2 - r])
                translate([x, y]) circle(r = r);
    }
}

module rounded_slab(size, r, fillet = 1.2) {
    // 3D rounded-corner slab with top/bottom fillets via minkowski.
    w = size[0]; d = size[1]; h = size[2];
    f = min(fillet, h/2 - 0.05, r - 0.05);
    minkowski() {
        linear_extrude(height = max(h - 2*f, 0.01), center = true)
            rounded_rect([w - 2*f, d - 2*f], max(r - f, 0.4));
        sphere(r = f);
    }
}

module wrist_curve_cut() {
    // Cylindrical removal that gives the underside a comfortable wrist sweep.
    translate([0, 0, -wrist_radius_mm + (case_total_height_mm/2) - 0.4])
        rotate([90, 0, 0])
            cylinder(r = wrist_radius_mm, h = case_length_mm * 2.2, center = true);
}

// ============================================================================
// POCKETS
// ============================================================================
module xiao_pocket() {
    translate([0, xiao_offset_y_mm, -inner_h/2 + xiao_thk_mm/2 + 0.2])
        cube([xiao_len_mm + 2*print_tolerance_mm,
              xiao_wid_mm + 2*print_tolerance_mm,
              xiao_thk_mm + 2*print_tolerance_mm],
             center = true);
    // USB-C cut-out toward the "top" edge of the case
    translate([0,
               xiao_offset_y_mm + xiao_wid_mm/2 + wall_thickness_mm,
               -inner_h/2 + xiao_usbc_h_mm/2 + 0.6])
        cube([xiao_usbc_w_mm + 2*print_tolerance_mm,
              wall_thickness_mm * 4,
              xiao_usbc_h_mm + 2*print_tolerance_mm],
             center = true);
}

module drv_pocket() {
    if (drv_carrier_pocket)
        translate([-(inner_len/2 - drv_len_mm/2 - 1.2),
                   xiao_offset_y_mm - xiao_wid_mm/2 - drv_wid_mm/2 - 1.2,
                   -inner_h/2 + drv_thk_mm/2 + 0.2])
            cube([drv_len_mm + 2*print_tolerance_mm,
                  drv_wid_mm + 2*print_tolerance_mm,
                  drv_thk_mm + 2*print_tolerance_mm],
                 center = true);
}

module battery_pocket() {
    // Battery sits below the lid, above the XIAO/DRV layer.
    translate([0,
               -((case_length_mm/2) - battery_len_mm/2 - wall_thickness_mm - 2.0)
                 + (case_length_mm/2 - battery_len_mm/2 - wall_thickness_mm - 2.0),
               inner_h/2 - battery_thk_mm/2 - 0.3])
        // re-centre toward the lug end of the case
        translate([0, -(xiao_offset_y_mm + xiao_wid_mm/2 + battery_len_mm/2 + 0.8
                        - case_length_mm/2 + wall_thickness_mm + 1.0), 0])
            cube([battery_wid_mm + 2*battery_clearance_mm,
                  battery_len_mm + 2*battery_clearance_mm,
                  battery_thk_mm + 2*battery_clearance_mm],
                 center = true);
}

module actuator_pockets() {
    // Lay actuators along the long axis, sandwiched between XIAO and lid.
    z = -inner_h/2 + xiao_thk_mm + actuator_h_mm/2 + 0.4;
    start = -((actuator_count - 1) * actuator_pitch_mm) / 2;
    for (i = [0 : actuator_count - 1])
        translate([start + i * actuator_pitch_mm,
                   xiao_offset_y_mm - xiao_wid_mm/2 - actuator_d_mm/2 - 1.8,
                   z])
            cylinder(d = actuator_d_mm + 2*print_tolerance_mm,
                     h = actuator_h_mm + 2*print_tolerance_mm,
                     center = true);
}

module pogo_pads() {
    // Two pogo holes on the wrist-side floor near the lug end (charging dock).
    z_floor = -case_total_height_mm/2 + floor_thickness_mm/2;
    y_pos   = -case_length_mm/2 + 6.0;
    for (s = [-1, 1])
        translate([s * pogo_pin_pitch_mm/2, y_pos, z_floor])
            cylinder(d = pogo_pin_d_mm + 2*print_tolerance_mm,
                     h = floor_thickness_mm + 1.0,
                     center = true);
    // Shallow magnet recess ring around the pads
    translate([0, y_pos, z_floor + floor_thickness_mm/2 - pogo_pad_recess_mm/2])
        cylinder(d = pogo_pin_pitch_mm * 2.6,
                 h = pogo_pad_recess_mm + 0.05,
                 center = true);
}

module mic_vent() {
    // Single PDM vent (XIAO Sense onboard mic faces up through this hole).
    translate([0, mic_vent_offset_mm, case_total_height_mm/2 - lid_thickness_mm])
        cylinder(d = mic_vent_d_mm, h = lid_thickness_mm * 3, center = true);
}

// ============================================================================
// SEAL LIPS
// ============================================================================
module case_seal_groove() {
    // Groove on top rim of case body that mates with lid tongue.
    translate([0, 0, case_total_height_mm/2 - lid_thickness_mm - seal_lip_h_mm/2])
        difference() {
            linear_extrude(height = seal_lip_h_mm + 0.02, center = true)
                rounded_rect([case_length_mm - 2*wall_thickness_mm + 2*seal_lip_relief_mm,
                              case_width_mm  - 2*wall_thickness_mm + 2*seal_lip_relief_mm],
                             max(inner_corner - 0.2, 0.4));
            linear_extrude(height = seal_lip_h_mm + 0.5, center = true)
                rounded_rect([case_length_mm - 2*wall_thickness_mm - 2*seal_lip_w_mm,
                              case_width_mm  - 2*wall_thickness_mm - 2*seal_lip_w_mm],
                             max(inner_corner - seal_lip_w_mm, 0.3));
        }
}

module lid_seal_tongue() {
    translate([0, 0, -seal_lip_h_mm/2])
        difference() {
            linear_extrude(height = seal_lip_h_mm, center = true)
                rounded_rect([case_length_mm - 2*wall_thickness_mm - 2*print_tolerance_mm,
                              case_width_mm  - 2*wall_thickness_mm - 2*print_tolerance_mm],
                             max(inner_corner - 0.3, 0.4));
            linear_extrude(height = seal_lip_h_mm + 0.5, center = true)
                rounded_rect([case_length_mm - 2*wall_thickness_mm - 2*seal_lip_w_mm - 2*print_tolerance_mm,
                              case_width_mm  - 2*wall_thickness_mm - 2*seal_lip_w_mm - 2*print_tolerance_mm],
                             max(inner_corner - seal_lip_w_mm - 0.2, 0.3));
        }
}

// ============================================================================
// STRAP INTERFACE
// ============================================================================
module lug_pair() {
    // Quick-release lug pockets at +/- Y ends, sized for 20-22 mm spring bars.
    for (s = [-1, 1])
        translate([0, s * (case_length_mm/2 - lug_recess_depth_mm/2 + 0.01), 0])
            difference() {
                // Recessed cavity inside the case wall to host the strap end
                translate([0, s * lug_recess_depth_mm/2, 0])
                    cube([lug_width_mm + 2*print_tolerance_mm,
                          lug_recess_depth_mm + 0.4,
                          lug_thickness_mm + 2*print_tolerance_mm],
                         center = true);
                // Spring-bar through-hole (drilled across the lug)
                rotate([0, 90, 0])
                    translate([0, s * 0, 0])
                        cylinder(d = lug_pin_d_mm + 2*print_tolerance_mm,
                                 h = case_width_mm + 4, center = true);
            }
}

module integrated_tpu_strap() {
    // Print-in-place TPU strap stub that fuses to each short end.
    // Real bands use community-parametric Apple-Watch-style links.
    for (s = [-1, 1])
        hull() {
            translate([0,
                       s * (case_length_mm/2 + 1.0),
                       0])
                cube([lug_width_mm, 2.0, tpu_strap_thk_mm], center = true);
            translate([0,
                       s * (case_length_mm/2 + tpu_strap_total_mm),
                       0])
                cube([lug_width_mm * tpu_strap_taper_pct,
                      2.0,
                      tpu_strap_thk_mm * 0.85],
                     center = true);
        }
}

// ============================================================================
// MAIN BODIES
// ============================================================================
module case_body_solid() {
    rounded_slab([case_length_mm, case_width_mm, case_total_height_mm],
                 case_corner_r_mm, fillet_r_mm);
}

module case_body() {
    difference() {
        union() {
            case_body_solid();
            if (strap_style == "lugs") {
                // External nubs that contain the lug recess
                for (s = [-1, 1])
                    translate([0, s * (case_length_mm/2 + 1.0), 0])
                        rounded_slab([lug_width_mm + 4,
                                      4.0,
                                      lug_thickness_mm + 2.4],
                                     1.2, 0.8);
            }
        }
        // Hollow interior
        translate([0, 0, floor_thickness_mm/2])
            rounded_slab([inner_len, inner_wid,
                          case_total_height_mm - floor_thickness_mm + 0.2],
                         inner_corner, 1.0);
        // Wrist sweep
        wrist_curve_cut();
        // Skin-side comfort relief band
        translate([0, 0, -case_total_height_mm/2 - skin_relief_mm + 0.01])
            rounded_slab([case_length_mm - 6, case_width_mm - 6, skin_relief_mm * 2],
                         case_corner_r_mm - 2, 0.6);
        // Pockets & ports
        xiao_pocket();
        drv_pocket();
        actuator_pockets();
        battery_pocket();
        pogo_pads();
        // Seal groove around top rim
        case_seal_groove();
        // Lug spring-bar holes
        if (strap_style == "lugs") lug_pair();
        // Optional corner screws
        if (lid_screw_count == 4)
            for (sx = [-1, 1]) for (sy = [-1, 1])
                translate([sx * (case_length_mm/2 - 3.0),
                           sy * (case_width_mm/2 - 3.0),
                           case_total_height_mm/2 - 6.0])
                    cylinder(d = lid_screw_d_mm + 2*print_tolerance_mm,
                             h = 8, center = true);
        // Half-section preview
        if (show_cutaway)
            translate([case_length_mm, 0, 0])
                cube([case_length_mm * 2, case_width_mm * 2, case_total_height_mm * 3],
                     center = true);
    }
}

module case_lid() {
    difference() {
        union() {
            // Lid plate
            translate([0, 0, lid_thickness_mm/2])
                rounded_slab([case_length_mm - 2*wall_thickness_mm - 2*print_tolerance_mm + 2*seal_lip_relief_mm,
                              case_width_mm  - 2*wall_thickness_mm - 2*print_tolerance_mm + 2*seal_lip_relief_mm,
                              lid_thickness_mm],
                             max(inner_corner - 0.2, 0.5), 0.6);
            // Sealing tongue protruding downward
            translate([0, 0, -seal_lip_h_mm/2 + 0.01])
                lid_seal_tongue();
        }
        // Mic vent (XIAO Sense)
        mic_vent();
        // Engraved logo
        if (engrave_logo)
            translate([0, 0, lid_thickness_mm - logo_depth_mm + 0.01])
                linear_extrude(height = logo_depth_mm + 0.02)
                    text(logo_text, size = logo_size_mm,
                         halign = "center", valign = "center",
                         font = logo_font);
        // Optional corner screw counterbores
        if (lid_screw_count == 4)
            for (sx = [-1, 1]) for (sy = [-1, 1])
                translate([sx * (case_length_mm/2 - 3.0 - wall_thickness_mm - print_tolerance_mm),
                           sy * (case_width_mm/2 - 3.0 - wall_thickness_mm - print_tolerance_mm),
                           lid_thickness_mm/2])
                    union() {
                        cylinder(d = lid_screw_d_mm + 2*print_tolerance_mm,
                                 h = lid_thickness_mm + 0.5, center = true);
                        translate([0, 0, lid_thickness_mm/2 - 0.4])
                            cylinder(d = lid_screw_head_d_mm,
                                     h = 0.8, center = true);
                    }
    }
}

// ============================================================================
// PCB / PART PREVIEW (visual only, not exported)
// ============================================================================
module pcb_preview() {
    if (preview_pcb) {
        color("DimGray")
            translate([0, xiao_offset_y_mm, -inner_h/2 + xiao_thk_mm/2 + 0.2])
                cube([xiao_len_mm, xiao_wid_mm, xiao_thk_mm], center = true);
        color("Goldenrod")
            translate([0, 0, inner_h/2 - battery_thk_mm/2 - 0.3])
                cube([battery_wid_mm, battery_len_mm, battery_thk_mm], center = true);
        color("FireBrick")
            for (i = [0 : actuator_count - 1]) {
                start = -((actuator_count - 1) * actuator_pitch_mm) / 2;
                translate([start + i * actuator_pitch_mm,
                           xiao_offset_y_mm - xiao_wid_mm/2 - actuator_d_mm/2 - 1.8,
                           -inner_h/2 + xiao_thk_mm + actuator_h_mm/2 + 0.4])
                    cylinder(d = actuator_d_mm, h = actuator_h_mm, center = true);
            }
    }
}

// ============================================================================
// DISPATCH
// ============================================================================
module openhear_v2() {
    if (build_part == "case") {
        case_body();
        pcb_preview();
    } else if (build_part == "lid") {
        case_lid();
    } else if (build_part == "strap_tpu") {
        if (strap_style == "integrated_tpu") integrated_tpu_strap();
        else echo("strap_style must be 'integrated_tpu' for strap_tpu build_part");
    } else if (build_part == "jig") {
        // Simple flat assembly jig: outline of case at floor level
        linear_extrude(height = 2)
            rounded_rect([case_length_mm + 4, case_width_mm + 4], case_corner_r_mm + 2);
    } else if (build_part == "all_exploded") {
        case_body();
        translate([0, 0, case_total_height_mm + 6]) case_lid();
        if (strap_style == "integrated_tpu")
            translate([0, 0, -case_total_height_mm]) integrated_tpu_strap();
    }
}

openhear_v2();
