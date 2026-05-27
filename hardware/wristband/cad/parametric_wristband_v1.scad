/* OpenHear aids-free wristband v1 parametric CAD
   Hardware licence: CERN-OHL-S-2.0
   Nothing in/on the ear; wrist is the complete system; skin is the transducer.
*/
$fn = 96;

wrist_circumference_mm = 170; // [140:1:220]
actuator_count = 24;          // [24,64,128]
ring_count_override = 0;      // 0 = infer 24->1, 64->4, 128->8
strap_width_mm = 34;
body_height_mm = 8.2;
wall_thickness_mm = 1.8;
resin_tolerance_mm = 0.35;    // validated target 0.30-0.50 mm
skin_gap_mm = 0.45;
silicone_overmold_mm = 1.0;
actuator_pocket_d_mm = 10.5;
actuator_pocket_h_mm = 3.8;
mic_count = 8;                // [8,16]
mic_port_d_mm = 1.15;
flex_channel_w_mm = 7.0;
flex_channel_h_mm = 1.0;
seal_lip_w_mm = 1.4;
seal_lip_h_mm = 0.8;
battery_len_mm = 45;
battery_w_mm = 25;
battery_h_mm = 8;
battery_clearance_mm = 0.5;
lug_len_mm = 15;
lug_hole_d_mm = 2.2;
show_cutaway = false;

inner_radius_mm = wrist_circumference_mm / (2 * PI);
outer_radius_mm = inner_radius_mm + body_height_mm;
ring_count = ring_count_override > 0 ? ring_count_override :
    (actuator_count <= 24 ? 1 : (actuator_count <= 64 ? 4 : 8));
columns = ceil(actuator_count / ring_count);
arc_gap_deg = 34;
active_arc_deg = 360 - arc_gap_deg;
ring_pitch_mm = strap_width_mm / ring_count;

module rounded_box(size, radius) {
    hull() for (x = [-size[0]/2 + radius, size[0]/2 - radius])
        for (y = [-size[1]/2 + radius, size[1]/2 - radius])
            for (z = [-size[2]/2 + radius, size[2]/2 - radius])
                translate([x, y, z]) sphere(r = radius);
}

module annular_segment(r_inner, r_outer, height, start_deg, end_deg) {
    step = 2;
    outer = [for (a = [start_deg:step:end_deg]) [r_outer * cos(a), r_outer * sin(a)]];
    inner = [for (a = [end_deg:-step:start_deg]) [r_inner * cos(a), r_inner * sin(a)]];
    linear_extrude(height = height, center = true) polygon(concat(outer, inner));
}

module actuator_pocket(angle_deg, z_pos) {
    rotate([0, 0, angle_deg])
        translate([inner_radius_mm + wall_thickness_mm + actuator_pocket_h_mm / 2, 0, z_pos])
            rotate([0, 90, 0])
                cylinder(d = actuator_pocket_d_mm + resin_tolerance_mm,
                         h = actuator_pocket_h_mm + resin_tolerance_mm,
                         center = true);
}

module flex_channel(angle_deg, z_pos) {
    rotate([0, 0, angle_deg])
        translate([inner_radius_mm + wall_thickness_mm + 1.8, 0, z_pos])
            cube([flex_channel_h_mm, flex_channel_w_mm, ring_pitch_mm * 0.72], center = true);
}

module mic_port(angle_deg) {
    rotate([0, 0, angle_deg])
        translate([outer_radius_mm - wall_thickness_mm / 2, 0, strap_width_mm / 2 - 2.2])
            rotate([0, 90, 0]) cylinder(d = mic_port_d_mm, h = wall_thickness_mm * 3, center = true);
}

module ip67_seal_lips() {
    annular_segment(inner_radius_mm + 0.25, inner_radius_mm + seal_lip_w_mm, seal_lip_h_mm,
                    -active_arc_deg / 2, active_arc_deg / 2);
    translate([0, 0, strap_width_mm / 2 - seal_lip_h_mm / 2])
        annular_segment(inner_radius_mm + 0.25, inner_radius_mm + seal_lip_w_mm, seal_lip_h_mm,
                        -active_arc_deg / 2, active_arc_deg / 2);
    translate([0, 0, -strap_width_mm / 2 + seal_lip_h_mm / 2])
        annular_segment(inner_radius_mm + 0.25, inner_radius_mm + seal_lip_w_mm, seal_lip_h_mm,
                        -active_arc_deg / 2, active_arc_deg / 2);
}

module strap_lugs() {
    for (side = [-1, 1]) rotate([0, 0, side * (active_arc_deg / 2 + 4)])
        translate([inner_radius_mm + body_height_mm / 2, 0, 0])
            difference() {
                rounded_box([lug_len_mm, 7, strap_width_mm * 0.86], 2);
                rotate([90, 0, 0]) cylinder(d = lug_hole_d_mm, h = 10, center = true);
            }
}

module battery_cartridge() {
    translate([0, -outer_radius_mm - lug_len_mm / 2, 0]) difference() {
        rounded_box([battery_w_mm + 2*battery_clearance_mm + 3,
                     battery_len_mm + 2*battery_clearance_mm + 3,
                     battery_h_mm + 3], 3);
        rounded_box([battery_w_mm + 2*battery_clearance_mm,
                     battery_len_mm + 2*battery_clearance_mm,
                     battery_h_mm + battery_clearance_mm], 2);
        translate([0, battery_len_mm / 2 + 1, 0]) cube([battery_w_mm * 0.5, 4, battery_h_mm + 5], center = true);
    }
}

module wristband_body() {
    difference() {
        union() {
            annular_segment(inner_radius_mm, outer_radius_mm, strap_width_mm, -active_arc_deg / 2, active_arc_deg / 2);
            ip67_seal_lips(); strap_lugs(); battery_cartridge();
        }
        annular_segment(inner_radius_mm - 0.1, inner_radius_mm + silicone_overmold_mm + skin_gap_mm,
                        strap_width_mm + 2, -active_arc_deg / 2, active_arc_deg / 2);
        for (i = [0:actuator_count - 1]) {
            ring = floor(i / columns); col = i % columns;
            angle = -active_arc_deg / 2 + (col + 0.5) * active_arc_deg / columns;
            z = -strap_width_mm / 2 + ring_pitch_mm * (ring + 0.5);
            actuator_pocket(angle, z); flex_channel(angle, z);
        }
        for (m = [0:mic_count - 1]) mic_port(-active_arc_deg / 2 + (m + 0.5) * active_arc_deg / mic_count);
        for (a = [-active_arc_deg / 2 + 8, active_arc_deg / 2 - 8])
            rotate([0, 0, a]) translate([outer_radius_mm - 1, 0, 0]) rotate([0, 90, 0])
                cylinder(d = 0.85, h = 5, center = true);
        if (show_cutaway) translate([-outer_radius_mm, -outer_radius_mm, -strap_width_mm])
            cube([outer_radius_mm * 2, outer_radius_mm * 2, strap_width_mm * 2]);
    }
}

wristband_body();
