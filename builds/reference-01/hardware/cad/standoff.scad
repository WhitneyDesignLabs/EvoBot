// EvoBot reference-01 — Deck Standoff (print 4x)
// Open in OpenSCAD → Render (F6) → Export STL (F7)

// Parametric dimensions (mm)
outer_dia     = 8;
inner_dia     = 3.2;
height        = 35;
flange_dia    = 10;
flange_thick  = 1.5;

$fn = 48;

module standoff() {
    difference() {
        union() {
            // Bottom flange
            cylinder(d=flange_dia, h=flange_thick);
            // Main body
            translate([0, 0, flange_thick])
                cylinder(d=outer_dia, h=height);
            // Top flange
            translate([0, 0, flange_thick + height])
                cylinder(d=flange_dia, h=flange_thick);
        }
        // M3 through-hole
        translate([0, 0, -1])
            cylinder(d=inner_dia, h=height + 2*flange_thick + 2);
    }
}

standoff();
