// EvoBot reference-01 — HC-SR04 Sensor Bracket (print 2x)
// Open in OpenSCAD → Render (F6) → Export STL (F7)

// Parametric dimensions (mm)
board_w         = 45;       // HC-SR04 board width
board_h         = 20;       // HC-SR04 board height
base_depth      = 15;      // horizontal base depth
wall_thick      = 2.5;      // wall/base thickness
angle           = 15;       // outward tilt (degrees)
transducer_dia  = 16;  // ultrasonic cylinder diameter
transducer_span = 26; // center-to-center spacing
base_hole_span  = 35;  // mounting hole spacing
mount_hole_dia  = 3.2;           // M3 clearance

$fn = 48;

module sensor_bracket() {
    total_w = board_w + 2*wall_thick;
    face_h  = board_h + 2*wall_thick;

    difference() {
        union() {
            // Horizontal base
            translate([-total_w/2, 0, 0])
                cube([total_w, base_depth, wall_thick]);
            // Angled vertical face
            translate([0, 0, wall_thick])
                rotate([angle, 0, 0])
                    translate([-total_w/2, -wall_thick/2, 0])
                        cube([total_w, wall_thick, face_h]);
            // Gusset ribs (left and right)
            for (sx = [-1, 1])
                translate([sx * (total_w/2 - wall_thick), 0, wall_thick])
                    linear_extrude(height = wall_thick)
                        polygon([[0,0], [12,0], [0,12]]);
        }
        // Transducer holes (2x cylinders through the angled face)
        for (sx = [-1, 1])
            translate([sx * transducer_span/2, 0, wall_thick + face_h/2])
                rotate([angle, 0, 0])
                    rotate([90, 0, 0])
                        translate([0, 0, -wall_thick - 1])
                            cylinder(d=transducer_dia, h=wall_thick + 2);
        // HC-SR04 board slot (recessed area for the PCB)
        translate([0, 0, wall_thick + wall_thick])
            rotate([angle, 0, 0])
                translate([-board_w/2, -0.1, wall_thick])
                    cube([board_w, 1.6, board_h]);  // 1.6mm PCB thickness
        // Base mounting holes
        for (sx = [-1, 1])
            translate([sx * base_hole_span/2, base_depth/2, -1])
                cylinder(d=mount_hole_dia, h=wall_thick + 2);
    }
}

sensor_bracket();
