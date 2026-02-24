// EvoBot reference-01 — Ball Caster Assembly (print 1x)
// Open in OpenSCAD → Render (F6) → Export STL (F7)

// Parametric dimensions (mm)
ball_dia          = 16;
cup_id            = 16.5;
cup_depth         = 10;
cup_wall          = 1.5;
flange_dia        = 30;
flange_thick      = 3;
stem_height       = 22;
mount_hole_spacing = 20;
mount_hole_dia    = 3.2;
snap_slot_w       = 5;

$fn = 48;

module ball_caster() {
    cup_od = cup_id + 2*cup_wall;
    stem_r = cup_od/2 + 1;

    difference() {
        union() {
            // Flange
            cylinder(d=flange_dia, h=flange_thick);
            // Stem
            translate([0, 0, flange_thick])
                cylinder(r=stem_r, h=stem_height);
            // Cup (solid sphere shell)
            translate([0, 0, flange_thick + stem_height])
                difference() {
                    sphere(d=cup_od);
                    sphere(d=cup_id);
                    // Cut off top half (keep bottom hemisphere = cup)
                    translate([0, 0, cup_od/2])
                        cube([cup_od+2, cup_od+2, cup_od], center=true);
                    // Cut off below the equator to desired depth
                    translate([0, 0, -(cup_od/2 + cup_depth)])
                        cube([cup_od+2, cup_od+2, cup_od], center=true);
                }
        }
        // Mounting holes (3x, equilateral triangle)
        for (i = [0:2])
            rotate([0, 0, i*120 + 30])
                translate([mount_hole_spacing/sqrt(3), 0, -1])
                    cylinder(d=mount_hole_dia, h=flange_thick + 2);
        // Snap-in slot (rectangular notch in cup rim)
        translate([-snap_slot_w/2, -cup_od/2-1, flange_thick + stem_height - cup_depth])
            cube([snap_slot_w, cup_od+2, cup_depth + cup_wall + 1]);
    }
}

ball_caster();
