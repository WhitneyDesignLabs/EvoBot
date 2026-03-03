// EvoBot reference-01 — HC-SR04 Sensor Bracket (print 2x)
// L-bracket with channel rails for slide-in PCB retention
// Open in OpenSCAD → Render (F6) → Export STL (F7)

// Parametric dimensions (mm)
bracket_len    = 50;       // X dimension
base_w         = 18;       // Y dimension (base depth)
base_t         = 3;       // Z (base thickness)
wall_t         = 2.5;       // Y (back wall thickness)
wall_h         = 30;       // Z (wall height above base top)
rail_d         = 3;   // Y (rail protrusion)
rail_h         = 2;       // Z (rail thickness)
bot_rail_z     = 8;   // Z offset for bottom rail
board_gap      = 20.5;    // gap between rails (HC-SR04 height)
hole_span      = 35;    // M3 bolt hole spacing
mount_hole_dia = 3.2;         // M3 clearance

$fn = 48;

module sensor_bracket() {
    top_rail_z = bot_rail_z + rail_h + board_gap;

    difference() {
        union() {
            // Base plate
            cube([bracket_len, base_w, base_t]);
            // Back wall
            cube([bracket_len, wall_t, base_t + wall_h]);
            // Bottom rail
            translate([0, -rail_d, bot_rail_z])
                cube([bracket_len, rail_d, rail_h]);
            // Top rail
            translate([0, -rail_d, top_rail_z])
                cube([bracket_len, rail_d, rail_h]);
        }
        // M3 bolt holes through base
        for (sx = [-1, 1])
            translate([bracket_len/2 + sx*hole_span/2, base_w/2, -1])
                cylinder(d=mount_hole_dia, h=base_t + 2);
    }
}

sensor_bracket();
