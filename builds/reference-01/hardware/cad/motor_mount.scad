// EvoBot reference-01 — TT Motor Mount Clip (print 2x)
// Open in OpenSCAD → Render (F6) → Export STL (F7)

// Parametric dimensions (mm)
channel_w   = 23;   // inside width
channel_h   = 19;   // inside height (depth of U)
wall        = 1.5;  // wall thickness
clip_len    = 30; // length along motor body
tab_w       = 8;   // bolt tab width
tab_t       = 3; // bolt tab thickness
hole_span   = 17; // M3 hole spacing
hole_dia    = 3.2; // M3 clearance

$fn = 48;

module motor_mount() {
    outer_w = channel_w + 2*wall;
    total_w = outer_w + 2*tab_w;
    total_h = channel_h + wall;

    difference() {
        union() {
            // U-channel body
            translate([-clip_len/2, -outer_w/2, 0])
                cube([clip_len, outer_w, total_h]);
            // Left tab
            translate([-clip_len/2, -total_w/2, 0])
                cube([clip_len, tab_w, tab_t]);
            // Right tab
            translate([-clip_len/2, outer_w/2, 0])
                cube([clip_len, tab_w, tab_t]);
        }
        // Channel cutout (open top)
        translate([-clip_len/2 - 1, -channel_w/2, wall])
            cube([clip_len + 2, channel_w, channel_h + 1]);
        // M3 bolt holes (4 total, 2 per side)
        for (sx = [-1, 1])
            for (sy = [-1, 1])
                translate([sx * hole_span/2, sy * (outer_w/2 + tab_w/2), -1])
                    cylinder(d=hole_dia, h=tab_t + 2);
    }
}

motor_mount();
