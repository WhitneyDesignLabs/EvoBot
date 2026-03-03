// EvoBot reference-01 — Caster Skid / Drag Tip (v1)
//
// USE OPENSCAD to render: F6 (Render) → F7 (Export STL)
// Or use generate_stl.py which produces an equivalent STL directly.
//
// DESIGN:
//   Fixed hemisphere dome on a cylindrical stem with bolt-on flange.
//   No moving parts — the dome slides on the ground surface.
//   Works well for a lightweight (~500g) robot on smooth floors.
//   Can be upgraded to a ball caster later if needed.
//
// PRINT: Flange flat on bed. Dome at top has gentle overhang
//   but prints fine at this small size. No supports needed.
//
// MOUNT: Bolt flange to underside of bottom deck plate (3x M3).
//   The 3 bolt holes match the caster mount pattern on the deck.
//
// CROSS-SECTION (mounted orientation):
//
//        ========= DECK PLATE =========
//       |                               |
//       +----+                   +------+  <- flange (bolted to deck)
//            |                   |
//            |   stem (16mm OD)  |
//            |                   |
//            +---+           +---+
//                 \         /
//                  (  dome  )              <- hemisphere, slides on ground
//                   \     /
//                    (   )
//                     ---
//                   GROUND

// === Parameters (all in mm) ===

dome_radius = 8;                      // Hemisphere radius (ground contact)
stem_dia = dome_radius * 2;           // Stem matches dome diameter
flange_dia = 35;                      // Mounting flange outer diameter
flange_thick = 3;                     // Flange thickness

// Ride height: 29.5mm from deck bottom to ground
// = flange_thick + stem_height + dome_radius
// stem_height = 29.5 - 3 - 8 = 18.5mm
stem_height = 18.5;

mount_bolt_radius = 12;               // Matches DXF CASTER_BOLT_RADIUS
mount_hole_dia = 3.4;                 // M3 clearance

$fn = 60;

module caster_skid() {
    total_height = flange_thick + stem_height + dome_radius;

    difference() {
        union() {
            // Mounting flange (z=0 = on print bed)
            cylinder(d=flange_dia, h=flange_thick);

            // Cylindrical stem
            translate([0, 0, flange_thick])
                cylinder(d=stem_dia, h=stem_height);

            // Hemisphere dome (ground contact when mounted/flipped)
            translate([0, 0, flange_thick + stem_height])
                sphere(r=dome_radius);
        }

        // Cut off bottom half of sphere (below stem top)
        translate([0, 0, flange_thick + stem_height - dome_radius])
            translate([0, 0, -dome_radius])
                cube([flange_dia + 2, flange_dia + 2, dome_radius * 2], center=true);

        // 3x M3 mounting holes through flange (120° apart)
        for (i = [0:2])
            rotate([0, 0, i * 120 + 90])
                translate([mount_bolt_radius, 0, -1])
                    cylinder(d=mount_hole_dia, h=flange_thick + 2);
    }
}

caster_skid();
