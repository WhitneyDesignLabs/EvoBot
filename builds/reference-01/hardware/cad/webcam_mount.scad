// EvoBot reference-01 — Webcam Mount Post (print 1x)
// Open in OpenSCAD → Render (F6) → Export STL (F7)

// Parametric dimensions (mm)
post_dia        = 12;
post_height     = 40;
base_size       = 25;
base_thick      = 3;
base_hole_dia   = 4.2;  // M4 clearance
platform_w      = 30;
platform_d      = 20;
platform_thick  = 3;
tripod_hole_dia = 6.5; // 1/4"-20 clearance

$fn = 48;

module webcam_mount() {
    difference() {
        union() {
            // Square base
            translate([-base_size/2, -base_size/2, 0])
                cube([base_size, base_size, base_thick]);
            // Vertical post
            translate([0, 0, base_thick])
                cylinder(d=post_dia, h=post_height);
            // Top platform
            translate([-platform_w/2, -platform_d/2, base_thick + post_height])
                cube([platform_w, platform_d, platform_thick]);
            // Gusset ribs (4x at 90 degree intervals)
            for (a = [0, 90, 180, 270])
                rotate([0, 0, a])
                    translate([0, -1.5, base_thick])
                        linear_extrude(height=3)
                            polygon([[post_dia/2, 0],
                                     [post_dia/2 + 8, 0],
                                     [post_dia/2, 8]]);
        }
        // Base center hole (M4)
        translate([0, 0, -1])
            cylinder(d=base_hole_dia, h=base_thick + 2);
        // Platform tripod hole (1/4"-20)
        translate([0, 0, base_thick + post_height - 1])
            cylinder(d=tripod_hole_dia, h=platform_thick + 2);
    }
}

webcam_mount();
