/* OpenHear v1.5 No-Solder Modular Edition parametric CAD
   Hardware licence: CERN-OHL-S-2.0
   Print → Plug → Flash → Wear. No soldering, crimping, or stripped wire.
*/
$fn = 96;

// Required v1.5 parameters
actuator_count = 24;             // [24,64]
wrist_size = 170;                // wrist circumference in mm [140:1:220]
module_layout = "starter_24";    // [starter_24,dense_64,left_mcu,right_mcu]
pogo_pin_spacing = 2.54;         // magnetic pogo/JST alignment pitch in mm
snap_fit_tolerance = 0.35;       // printer-specific clearance in mm [0.20:0.05:0.70]

// Print/process tuning
strap_width_mm = actuator_count == 64 ? 46 : 34;
body_height_mm = 10.5;
wall_mm = 2.0;
skin_gap_mm = 0.55;
actuator_d_mm = 10.5;
actuator_h_mm = 4.2;
magnet_d_mm = 3.1;
magnet_h_mm = 1.2;
module_depth_mm = 6.0;
show_cutaway = false;

inner_radius_mm = wrist_size / (2 * PI);
outer_radius_mm = inner_radius_mm + body_height_mm;
ring_count = actuator_count == 64 ? 4 : 1;
columns = actuator_count / ring_count;
arc_gap_deg = 42;
active_arc_deg = 360 - arc_gap_deg;
ring_pitch_mm = strap_width_mm / ring_count;

module rounded_box(size, radius) {
    hull() for (x = [-size[0] / 2 + radius, size[0] / 2 - radius])
        for (y = [-size[1] / 2 + radius, size[1] / 2 - radius])
            for (z = [-size[2] / 2 + radius, size[2] / 2 - radius])
                translate([x, y, z]) sphere(r = radius);
}

module annular_segment(r_inner, r_outer, height, start_deg, end_deg) {
    step = 2;
    outer = [for (a = [start_deg:step:end_deg]) [r_outer * cos(a), r_outer * sin(a)]];
    inner = [for (a = [end_deg:-step:start_deg]) [r_inner * cos(a), r_inner * sin(a)]];
    linear_extrude(height = height, center = true) polygon(concat(outer, inner));
}

module actuator_socket(angle_deg, z_pos) {
    rotate([0, 0, angle_deg])
        translate([inner_radius_mm + wall_mm + actuator_h_mm / 2, 0, z_pos])
            rotate([0, 90, 0]) cylinder(
                d = actuator_d_mm + snap_fit_tolerance,
                h = actuator_h_mm + snap_fit_tolerance,
                center = true
            );
}

module actuator_lattice_retainer(angle_deg, z_pos) {
    rotate([0, 0, angle_deg])
        translate([inner_radius_mm + wall_mm + actuator_h_mm + 0.9, 0, z_pos])
            cube([1.0, actuator_d_mm * 0.78, min(5.0, ring_pitch_mm * 0.55)], center = true);
}

module wire_channel(angle_deg, z_pos) {
    rotate([0, 0, angle_deg])
        translate([inner_radius_mm + wall_mm + 2.0, 0, z_pos])
            cube([1.5, 7.5, max(3.0, ring_pitch_mm * 0.72)], center = true);
}

module pogo_pad_window(angle_deg, z_pos, pins = 6) {
    rotate([0, 0, angle_deg])
        translate([outer_radius_mm - 2.0, 0, z_pos]) {
            cube([4.0, pogo_pin_spacing * (pins - 1) + 3.0, 2.4], center = true);
            for (i = [0:pins - 1])
                translate([0, (i - (pins - 1) / 2) * pogo_pin_spacing, 0])
                    rotate([0, 90, 0]) cylinder(d = 0.9, h = 5.0, center = true);
        }
}

module magnet_pocket(angle_deg, z_pos) {
    rotate([0, 0, angle_deg])
        translate([outer_radius_mm - wall_mm / 2, 0, z_pos])
            rotate([0, 90, 0]) cylinder(
                d = magnet_d_mm + snap_fit_tolerance,
                h = magnet_h_mm + snap_fit_tolerance,
                center = true
            );
}

module module_bay(angle_deg, z_pos, label_width = 24, label_height = 18) {
    rotate([0, 0, angle_deg])
        translate([outer_radius_mm - module_depth_mm / 2, 0, z_pos]) {
            rounded_box([module_depth_mm + snap_fit_tolerance, label_width + snap_fit_tolerance, label_height + snap_fit_tolerance], 2.2);
            for (side = [-1, 1])
                translate([0, side * (label_width / 2 - 3), label_height / 2 - 3])
                    sphere(r = 1.0 + snap_fit_tolerance / 2);
        }
}

module battery_cartridge() {
    translate([0, -outer_radius_mm - 20, 0]) difference() {
        union() {
            rounded_box([31, 52, 13], 3.5);
            translate([0, 27, 0]) rounded_box([18, 7, 10], 2.0); // thumb tab
        }
        rounded_box([26 + snap_fit_tolerance, 45 + snap_fit_tolerance, 8.5 + snap_fit_tolerance], 2.3);
        translate([0, 21, 0]) cube([13, 10, 16], center = true); // JST/magnetic dock mouth
        for (x = [-8, 8]) translate([x, -23, 5.2]) cylinder(d = magnet_d_mm + snap_fit_tolerance, h = 2, center = true);
    }
}

module snap_fit_strap() {
    for (side = [-1, 1]) rotate([0, 0, side * (active_arc_deg / 2 + 7)])
        translate([inner_radius_mm + body_height_mm / 2, 0, 0]) difference() {
            rounded_box([26, 12, strap_width_mm * 0.88], 3);
            rotate([90, 0, 0]) cylinder(d = 4.2 + snap_fit_tolerance, h = 16, center = true);
            translate([5 * side, 0, 0]) cube([2.0, 15, strap_width_mm * 0.70], center = true);
        }
}

module main_body() {
    difference() {
        union() {
            annular_segment(inner_radius_mm, outer_radius_mm, strap_width_mm, -active_arc_deg / 2, active_arc_deg / 2);
            snap_fit_strap();
            battery_cartridge();
        }
        annular_segment(inner_radius_mm - 0.1, inner_radius_mm + skin_gap_mm, strap_width_mm + 2,
                        -active_arc_deg / 2, active_arc_deg / 2);
        for (i = [0:actuator_count - 1]) {
            ring = floor(i / columns);
            col = i % columns;
            angle = -active_arc_deg / 2 + (col + 0.5) * active_arc_deg / columns;
            z = -strap_width_mm / 2 + ring_pitch_mm * (ring + 0.5);
            actuator_socket(angle, z);
            wire_channel(angle, z);
            if (col % 4 == 0) actuator_lattice_retainer(angle, z);
        }
        // Swappable electronics bays: MCU, haptic driver, mic array, battery/interconnect.
        module_bay(-108, 0, 28, 20);
        module_bay(-42, 0, 32, 20);
        module_bay(42, 0, 32, 20);
        module_bay(108, 0, 28, 20);
        for (a = [-126, -84, -18, 18, 84, 126]) pogo_pad_window(a, 0, 6);
        for (a = [-132, -78, -24, 24, 78, 132]) for (z = [-strap_width_mm / 2 + 4, strap_width_mm / 2 - 4]) magnet_pocket(a, z);
        if (show_cutaway) translate([-outer_radius_mm, -outer_radius_mm, -strap_width_mm])
            cube([outer_radius_mm * 2, outer_radius_mm * 2, strap_width_mm * 2]);
    }
}

module actuator_lattice_click_in() {
    for (i = [0:actuator_count - 1]) {
        ring = floor(i / columns);
        col = i % columns;
        angle = -active_arc_deg / 2 + (col + 0.5) * active_arc_deg / columns;
        z = -strap_width_mm / 2 + ring_pitch_mm * (ring + 0.5);
        rotate([0, 0, angle]) translate([inner_radius_mm + wall_mm + actuator_h_mm + 2.2, 0, z])
            rounded_box([1.4, actuator_d_mm * 0.86, min(5.6, ring_pitch_mm * 0.62)], 0.7);
    }
}

module printable_set() {
    main_body();
    translate([outer_radius_mm * 2 + 25, 0, 0]) actuator_lattice_click_in();
}

printable_set();
