# EvoBot reference-01 Parametric Chassis Design

## Overview

Two-deck rectangular chassis for a 2WD differential-drive robot. Bottom deck carries motors, battery, and motor driver. Top deck carries the Pi 3B, ESP32, breadboard, and sensors. Decks are connected by standoffs. All corners rounded for safety. The entire design is parametric -- every dimension is a named variable so the chassis can be scaled, adapted, or reproduced at any size.

**Fabrication target:** Laser-cut 3mm plywood (primary) or hand-cut with jigsaw (alternative).
**3D printed parts:** Motor mounts, ball caster, standoffs (optional).
**Fasteners:** M3 bolts/nuts throughout (except Pi mount holes which are M2.5).

---

## Parametric Variables

All dimensions in millimeters unless noted. Change these values to scale the entire design.

### Chassis Envelope

```
PLATE_LENGTH          = 250       # X dimension (front-to-back)
PLATE_WIDTH           = 200       # Y dimension (left-to-right)
PLATE_THICKNESS       = 3         # Material thickness (3mm ply default)
CORNER_RADIUS         = 15        # Rounded corner radius
DECK_SPACING          = 35        # Vertical gap between bottom and top deck
```

### Motor Geometry (TT Yellow Geared DC)

```
MOTOR_BODY_LENGTH     = 70        # Motor body, axle direction
MOTOR_BODY_WIDTH      = 22        # Motor body, perpendicular to axle
MOTOR_BODY_HEIGHT     = 18        # Motor body, vertical
MOTOR_SHAFT_OFFSET    = 9         # Center of shaft from bottom of motor body
MOTOR_MOUNT_HOLE_DIA  = 3.2       # M3 clearance hole
MOTOR_MOUNT_HOLE_SPAN = 17        # Center-to-center of the two M3 mounting holes
MOTOR_AXLE_PROTRUDE   = 10        # Shaft extension beyond motor body end
```

### Wheel Geometry

```
WHEEL_DIAMETER        = 65        # TT motor wheel outer diameter
WHEEL_WIDTH           = 28        # Wheel width (tire + hub)
WHEEL_CLEARANCE       = 2         # Gap between wheel inner face and plate edge
```

### Motor Placement

```
MOTOR_X_OFFSET        = 65        # Motor axle center, measured from FRONT edge of plate
MOTOR_Y_INSET         = 0         # Motor body flush with plate edge (0 = flush)
                                  # Negative values = motor body overhangs plate edge
                                  # Positive values = motor body inset from edge
```

### Caster

```
CASTER_BALL_DIA       = 16        # Ball diameter (marble or 3D printed sphere)
CASTER_HOUSING_DIA    = 25        # Outer diameter of caster housing
CASTER_MOUNT_HOLE_DIA = 3.2       # M3 clearance
CASTER_MOUNT_HOLE_SPAN= 30        # Bolt pattern diameter (2 or 3 holes on circle)
CASTER_X_OFFSET       = 30        # Caster center, measured from REAR edge of plate
```

### Standoffs (Deck-to-Deck)

```
STANDOFF_DIAMETER     = 6         # Standoff outer diameter (hex or round)
STANDOFF_LENGTH       = 35        # Must equal DECK_SPACING
STANDOFF_HOLE_DIA     = 3.2       # M3 clearance hole in plates
STANDOFF_INSET_X      = 15        # Standoff center from plate front/rear edges
STANDOFF_INSET_Y      = 15        # Standoff center from plate left/right edges
```

### Pi 3B Mounting

```
PI_BOARD_LENGTH       = 85.6      # Pi 3B PCB length
PI_BOARD_WIDTH        = 56.5      # Pi 3B PCB width
PI_MOUNT_HOLE_DIA     = 2.7       # M2.5 clearance hole
PI_MOUNT_RECT_X       = 58        # Hole pattern, X span (center-to-center)
PI_MOUNT_RECT_Y       = 49        # Hole pattern, Y span (center-to-center)
PI_STANDOFF_HEIGHT    = 5         # Clearance under Pi for airflow + solder joints
```

### ESP32 Dev Board Mounting

```
ESP32_BOARD_LENGTH    = 51        # Typical ESP32 DevKit V1
ESP32_BOARD_WIDTH     = 28        # Including pin headers
ESP32_MOUNT_HOLE_DIA  = 2.2       # M2 clearance (or use adhesive standoffs)
ESP32_MOUNT_RECT_X    = 44        # Hole pattern, X span (if board has holes)
ESP32_MOUNT_RECT_Y    = 23        # Hole pattern, Y span
```

### Other Component Mounting Areas

```
BREADBOARD_LENGTH     = 83        # Mini breadboard (170 tie points)
BREADBOARD_WIDTH      = 55        # Mini breadboard width
BATTERY_LENGTH        = 105       # 2S pack approximate
BATTERY_WIDTH         = 35        # 2S pack approximate
BATTERY_HEIGHT        = 20        # 2S pack approximate
BUCK_LENGTH           = 43        # Typical small buck converter module
BUCK_WIDTH            = 21        # Typical small buck converter module
MOTOR_SHIELD_LENGTH   = 70        # L293D motor shield (Arduino form factor)
MOTOR_SHIELD_WIDTH    = 55        # L293D motor shield
```

### Fastener Holes (General)

```
M2_CLEARANCE          = 2.2
M2_5_CLEARANCE        = 2.7
M3_CLEARANCE          = 3.2
M3_COUNTERSINK_DIA    = 6.5       # If using countersunk M3 bolts
```

---

## Layer Breakdown

### Bottom Deck (Base Plate)

The structural foundation. Carries all heavy and drive-related components.

**Material:** 3mm plywood or MDF (use 5mm if hand-cutting for added rigidity)

**Components mounted to bottom deck:**

| Component | Attachment | Location | Notes |
|---|---|---|---|
| Left TT motor | 3D printed clip mount | Front-left, axle at MOTOR_X_OFFSET from front | Motor body parallel to X axis, shaft points outward |
| Right TT motor | 3D printed clip mount | Front-right, mirror of left | Motor body parallel to X axis, shaft points outward |
| Battery pack (2S) | Velcro strap or 3D printed cradle | Center, between motors and caster | Low and centered for stability |
| Buck converter | M3 bolts or double-sided tape | Near battery, rear-center area | Short wire run from battery |
| Motor driver shield | M3 standoffs | Center or rear-center | Near ESP32 on upper deck (wires pass through) |
| Ball caster | M3 bolts through plate | Rear center, CASTER_X_OFFSET from rear | Supports rear of chassis, allows zero-radius turns |

**Cutouts and holes in bottom deck:**

| Feature | Purpose | Size |
|---|---|---|
| 4x standoff holes (corners) | Deck-to-deck standoffs | M3_CLEARANCE |
| 2x left motor mount holes | Secure left motor clip | M3_CLEARANCE |
| 2x right motor mount holes | Secure right motor clip | M3_CLEARANCE |
| 2-3x caster mount holes | Secure ball caster housing | M3_CLEARANCE |
| 2x motor shaft slots | Allow motor shafts to pass through (if motors mount on top of plate) | ~12mm wide x 25mm long |
| Wire pass-through hole | Route wires from bottom deck to top deck | ~20mm diameter, center-rear area |
| Battery strap slots (2x) | Thread velcro strap to hold battery | ~3mm x 15mm, flanking battery area |

### Top Deck (Electronics Plate)

The brain platform. Carries all compute, sensing, and prototyping components.

**Material:** 3mm plywood or MDF (can be thinner -- 2mm acrylic also works)

**Components mounted to top deck:**

| Component | Attachment | Location | Notes |
|---|---|---|---|
| Raspberry Pi 3B | M2.5 standoffs (5mm) | Rear half, USB ports facing rear edge | Allows USB webcam + power cable access from rear |
| ESP32 dev board | M2 standoffs or pin-header friction fit on breadboard | Front half, near center | Close to wire pass-through for motor driver connection |
| Mini breadboard | Self-adhesive base (peel and stick) | Center, between Pi and ESP32 | Sensor wiring, level shifter, power distribution |
| HC-SR04 sensors (2x) | 3D printed bracket or hot glue | Front edge, angled outward 15-30 deg | Left and right obstacle detection |
| MPU6050 IMU | Soldered to breadboard or standalone mount | Center of top deck | At or near center of rotation for best readings |
| USB webcam | Clip or 3D printed mount | Front-center, elevated | Forward-facing, above ultrasonic sensors |

**Cutouts and holes in top deck:**

| Feature | Purpose | Size |
|---|---|---|
| 4x standoff holes (corners) | Deck-to-deck standoffs, matching bottom deck | M3_CLEARANCE |
| 4x Pi mounting holes | 58x49mm rectangle pattern | M2_5_CLEARANCE |
| 2x ESP32 mounting holes | If board has mounting holes | M2_CLEARANCE |
| Wire pass-through hole | Aligned with bottom deck pass-through | ~20mm diameter |
| Sensor bracket mounting holes | Front edge, for HC-SR04 mounts | M3_CLEARANCE |

---

## ASCII Art: Top-Down Layout

### Bottom Deck (viewed from above)

```
    FRONT
    ________________________________
   /                                \        Y
  |  [L-MTR SLOT]      [R-MTR SLOT] |       ^
  |   ||                        ||   |       |
  |   || Left        Right  ||   |       |
  |   || Motor       Motor  ||   |       +-----> X
  |   ||                        ||   |
  |   (O)---axle---[=WHEEL=]   (O)---axle---[=WHEEL=]
  |                                  |
  |   (S)                      (S)   |   (S) = Standoff hole
  |                                  |
  |       +--------------------+     |
  |       |                    |     |
  |       |   BATTERY (2S)     |     |
  |       |                    |     |
  |       +--------------------+     |
  |                                  |
  |        [BUCK]    [MTR DRV]       |
  |                                  |
  |   (S)          (o)         (S)   |   (o) = Wire pass-through
  |                                  |
  |            ( CASTER )            |
   \                                /
    --------------------------------
    REAR
```

### Top Deck (viewed from above)

```
    FRONT
    ________________________________
   /                                \
  |                                  |
  |  [HC-SR04-L]  [WEBCAM]  [HC-SR04-R]
  |                                  |
  |   (S)                      (S)   |   (S) = Standoff hole
  |                                  |
  |        +----------------+        |
  |        |  ESP32 DevKit  |        |
  |        +----------------+        |
  |                                  |
  |     +----------------------+     |
  |     |                      |     |
  |     |   MINI BREADBOARD    |     |
  |     |   [IMU] [LVL SHFT]  |     |
  |     |                      |     |
  |     +----------------------+     |
  |                                  |
  |   (S)          (o)         (S)   |   (o) = Wire pass-through
  |                                  |
  |     +------------------------+   |
  |     |                        |   |
  |     |   RASPBERRY PI 3B     |   |
  |     |   [USB]----[USB]      |   |   USB ports face rear
  |     |   [ETH]  [HDMI][PWR] |   |
  |     +------------------------+   |
   \                                /
    --------------------------------
    REAR
```

### Side Profile (Left Side View)

```
                 FRONT                              REAR
    _______________________________________________
   |  [HC-SR04]    TOP DECK (3mm)    [Pi 3B]      |  <-- Top deck
   |_______________________________________________|
        |  5mm Pi standoffs                    |
        |                                      |
   ---(S)---- 35mm gap (DECK_SPACING) -------(S)---  <-- Standoffs
        |                                      |
   _____|______________________________________|___
   |  [Motor]   BOTTOM DECK (3mm)   [Battery]     |  <-- Bottom deck
   |_______________________________________________|
     [WHEEL]                           (CASTER)
   =====================      ___         ___
                             (   )  <-- ball caster
                              ---
```

---

## Component Placement Coordinates

Origin (0,0) is at the **rear-left corner** of the plate (bottom-left when viewed from above with front at top). X increases toward front. Y increases toward right.

### Bottom Deck

| Component | Center X (mm) | Center Y (mm) | Notes |
|---|---|---|---|
| Left motor axle | 185 | 0 (at edge) | PLATE_LENGTH - MOTOR_X_OFFSET. Shaft exits left side. |
| Right motor axle | 185 | 200 (at edge) | Mirror of left motor. Shaft exits right side. |
| Left motor mount hole 1 | 176.5 | 15 | Offset from axle: -(MOTOR_MOUNT_HOLE_SPAN/2) in X |
| Left motor mount hole 2 | 193.5 | 15 | Offset from axle: +(MOTOR_MOUNT_HOLE_SPAN/2) in X |
| Right motor mount hole 1 | 176.5 | 185 | Mirror of left |
| Right motor mount hole 2 | 193.5 | 185 | Mirror of left |
| Battery center | 110 | 100 | Centered between motors and caster |
| Buck converter | 65 | 130 | Near battery, offset right |
| Motor driver shield | 65 | 70 | Near center, accessible from above |
| Caster center | 30 | 100 | CASTER_X_OFFSET from rear, centered Y |
| Wire pass-through | 50 | 100 | Between caster and motor driver |
| Standoff, rear-left | 15 | 15 | STANDOFF_INSET from edges |
| Standoff, rear-right | 15 | 185 | STANDOFF_INSET from edges |
| Standoff, front-left | 235 | 15 | PLATE_LENGTH - STANDOFF_INSET |
| Standoff, front-right | 235 | 185 | PLATE_LENGTH - STANDOFF_INSET |

### Top Deck

| Component | Center X (mm) | Center Y (mm) | Notes |
|---|---|---|---|
| Pi 3B center | 45 | 105 | Rear half, slightly right of center. USB ports face rear edge. |
| Pi mount hole 1 | 16 | 80.5 | Pi hole pattern: 58x49mm rectangle |
| Pi mount hole 2 | 74 | 80.5 | |
| Pi mount hole 3 | 16 | 129.5 | |
| Pi mount hole 4 | 74 | 129.5 | |
| ESP32 center | 170 | 100 | Front half, centered |
| Breadboard center | 115 | 100 | Between Pi and ESP32 |
| IMU (MPU6050) | 125 | 100 | Center of deck (center of rotation) |
| HC-SR04 left | 245 | 45 | Front edge, left quadrant |
| HC-SR04 right | 245 | 155 | Front edge, right quadrant |
| Webcam mount | 245 | 100 | Front edge, centered |

---

## 3D Printed Parts

All parts designed for FDM printing in PETG (strong, heat-resistant, low warp). No supports needed if designed with flat print-in-place geometry.

### 1. TT Motor Mount Clip (print 2x)

```
Purpose:    Clamp TT motor body to base plate
Material:   PETG
Infill:     40% minimum
Walls:      3 perimeters

Dimensions:
  CLIP_LENGTH         = 35        # Wraps around motor body width (22mm) + wall thickness
  CLIP_WIDTH          = 30        # Along motor body length, enough for 2x M3 holes
  CLIP_HEIGHT         = 22        # Motor body height (18mm) + plate thickness (3mm) + clearance
  CLIP_WALL           = 2.5       # Wall thickness of clip
  CLIP_TAB_WIDTH      = 10        # Bolt tab extending beyond motor body

Design:
  - U-channel that cradles the motor body (22x18mm cross-section)
  - Two M3 bolt tabs on each side, holes at MOTOR_MOUNT_HOLE_SPAN (17mm) apart
  - Slight interference fit (make channel 21.5mm wide) for snug grip
  - Open at both ends to allow shaft and wiring to pass through
  - Optional: snap-fit clip on top instead of fully enclosed channel

Cross-section (looking at motor end-on):

    [TAB]----+============+----[TAB]    <-- bolt tabs with M3 holes
             |            |
             |   MOTOR    |             <-- motor sits in channel
             |   BODY     |
             |            |
    =========+============+=========    <-- rests on base plate
    ^^^^^^^^^  base plate  ^^^^^^^^^
```

### 2. Ball Caster Assembly (print 1x set)

```
Purpose:    Rear support, allows omnidirectional sliding
Material:   PETG housing, smooth PLA or glass marble for ball
Infill:     50% (housing needs strength)

Dimensions:
  HOUSING_OD          = 25        # Outer diameter of cup
  HOUSING_ID          = 16.5      # Inner diameter (ball + 0.5mm clearance)
  HOUSING_HEIGHT      = 20        # Total height including mounting flange
  BALL_DIA            = 16        # Standard marble or printed sphere
  FLANGE_DIA          = 35        # Mounting flange with bolt holes
  FLANGE_THICK        = 3         # Flange thickness
  GROUND_CLEARANCE    = 8         # Ball protrusion below housing bottom

Design:
  - Hemispherical cup holds the ball
  - Three small support nubs inside cup (120 deg apart) to reduce friction
  - Ball protrudes ~8mm below housing (provides ground clearance for bottom deck)
  - Top flange with 2 or 3 M3 bolt holes on CASTER_MOUNT_HOLE_SPAN circle
  - Height chosen so bottom deck sits level with motor axle height:
    Caster total height = WHEEL_DIAMETER/2 - PLATE_THICKNESS
    = 65/2 - 3 = 29.5mm (from bottom of plate to ground)
    So housing height = 29.5 - GROUND_CLEARANCE = ~21.5mm above plate bottom

Side view:
                +---------+
                | FLANGE  |  M3 bolt holes
    ============+====o====+============  <-- base plate (bottom surface)
                |         |
                | HOUSING |
                |  (   )  |  <-- ball sits in cup
                +--( O )--+
                   (   )     <-- ball protrudes below
                    ---
                  GROUND
```

### 3. Standoffs (print 4x, or use metal M3 standoffs if available)

```
Purpose:    Space top deck above bottom deck
Material:   PETG
Infill:     100% (solid -- these are structural)

Dimensions:
  STANDOFF_OD         = 8         # Outer diameter (hex or round)
  STANDOFF_ID         = 3.2       # M3 bolt passes through center
  STANDOFF_HEIGHT     = 35        # DECK_SPACING

Design:
  - Simple hollow cylinder (or hex prism for wrench grip)
  - M3 bolt passes through top deck, through standoff, into bottom deck
  - Use M3x45mm bolt (plate + standoff + plate + nut = 3+35+3+nut)
  - Alternative: M3 threaded insert in standoff ends for tool-free deck removal

Note: Metal M3 standoff kits are cheap and better. 3D print only if
buying is not an option (which it isn't for v1 -- $0 budget).
```

### 4. HC-SR04 Sensor Bracket (print 2x)

```
Purpose:    Mount ultrasonic sensors at front edge, angled outward
Material:   PETG
Infill:     30%

Dimensions:
  BRACKET_WIDTH       = 48        # HC-SR04 board width (45mm + clearance)
  BRACKET_HEIGHT      = 22        # HC-SR04 board height (20mm + clearance)
  BRACKET_DEPTH       = 15        # How far bracket extends from plate edge
  SENSOR_ANGLE        = 15        # Outward angle in degrees (0 = straight ahead)

Design:
  - Clip or friction-fit holder for HC-SR04 board
  - Mounts to front edge of top deck with M3 bolt
  - Angled outward at SENSOR_ANGLE degrees for wider detection cone
  - Open back for wiring access to 4-pin header
```

### 5. Webcam Mount Post (print 1x, optional)

```
Purpose:    Elevate USB webcam above deck for unobstructed forward view
Material:   PETG
Infill:     40%

Dimensions:
  POST_HEIGHT         = 40        # Height above top deck
  POST_BASE           = 30x20     # Bolt-down footprint
  CLAMP_WIDTH         = varies    # Sized to webcam body

Design:
  - Simple post with flat base (2x M3 holes) and top clamp/cradle for webcam
  - Height puts camera above ultrasonic sensors for clear view
  - Slight forward tilt (~10 deg) for ground-ahead visibility
```

---

## Assembly Order

1. **Cut both deck plates** to PLATE_LENGTH x PLATE_WIDTH with CORNER_RADIUS rounded corners.
2. **Drill/cut all holes** in both plates per the coordinate tables above.
3. **Print all 3D parts** (2x motor clips, 1x caster, 4x standoffs, 2x sensor brackets).
4. **Install motors** -- press TT motors into clips, bolt clips to bottom deck.
5. **Install caster** -- bolt caster housing to bottom deck at rear center.
6. **Test rolling** -- set bottom deck on wheels + caster, verify it rolls level and straight. Adjust caster height if needed (sand housing or add washer shims).
7. **Mount battery** -- velcro strap or cradle, centered on bottom deck.
8. **Mount motor driver** -- standoffs or direct bolt to bottom deck.
9. **Mount buck converter** -- near battery on bottom deck.
10. **Install standoffs** -- bolt 4x standoffs to bottom deck corner positions.
11. **Attach top deck** -- set top deck on standoffs, bolt down.
12. **Mount Pi 3B** -- M2.5 standoffs on top deck, Pi board on top.
13. **Mount ESP32** -- standoffs or breadboard friction-fit on top deck.
14. **Mount breadboard** -- peel-and-stick adhesive to top deck.
15. **Mount sensors** -- HC-SR04 brackets at front edge, IMU on breadboard.
16. **Route wires** -- through wire pass-through hole between decks.
17. **Mount webcam** -- post or clip at front of top deck.
18. **Wheels on last** -- press TT wheels onto motor shafts.

---

## Hand-Cutting Alternative (No Laser Needed)

The laser is convenient but not required. Here is how to hand-fabricate the plates.

### Tools Required

- Jigsaw or coping saw (for curves)
- Drill with 2.2mm, 2.7mm, 3.2mm, and 20mm bits (or step drill)
- Ruler, square, pencil
- Sandpaper (120 and 220 grit)
- Compass (for corner radii)

### Process

1. **Print the template at 1:1 scale.** When SVG files are generated (future step), print on paper at 100% scale. Tape sheets together if the plate is larger than one page.
2. **Transfer to wood.** Tape template to plywood/MDF. Use an awl or nail to mark all hole centers through the paper into the wood. Trace the outline with a pencil.
3. **Cut the outline.** Jigsaw for straight edges. For rounded corners: drill a pilot hole at the tangent point, then use the jigsaw or coping saw to follow the radius. Alternatively, cut square corners and round them with a rasp or sanding block.
4. **Drill all holes.** Use the marked centers. Start with a small pilot drill (1.5mm), then step up to final size. For the 20mm wire pass-through, use a spade bit, Forstner bit, or step drill.
5. **Cut motor shaft slots.** Drill two holes at slot ends, then connect with jigsaw.
6. **Sand all edges.** 120 grit to remove splinters, 220 grit to smooth. Round over all edges slightly -- a robot should not have sharp edges.
7. **Seal the wood (optional).** Light coat of polyurethane, clear spray paint, or even white glue thinned with water. Prevents moisture absorption and strengthens the surface.

### Hand-Cut Tolerances

| Feature | Laser Tolerance | Hand-Cut Tolerance | Impact |
|---|---|---|---|
| Outline shape | +/- 0.1mm | +/- 2mm | Cosmetic only, does not affect function |
| Hole positions | +/- 0.1mm | +/- 1mm | Use oversized holes (3.5mm for M3) to allow adjustment |
| Hole diameter | +/- 0.1mm | +/- 0.3mm | Drill press improves this; hand drill is fine with pilot hole |
| Corner radius | Exact | Approximate | Cosmetic; any smooth curve works |
| Slot width | +/- 0.1mm | +/- 1mm | Make slots 1-2mm oversized, motor clip handles alignment |

**Key tip:** For hand-cut builds, make all clearance holes one size larger than specified (M3 -> 3.5mm, M2.5 -> 3.0mm). This compensates for positional error and makes assembly much easier. The bolt head or washer provides clamping force regardless.

---

## Material Options and Thickness Considerations

### Recommended Materials

| Material | Thickness | Weight (est. per plate) | Pros | Cons | Verdict |
|---|---|---|---|---|---|
| **Birch plywood** | 3mm | ~60g | Stiff, laser-cuts clean, cheap, screws hold well | Can delaminate at edges if cheap | **Best overall choice** |
| MDF | 3mm | ~75g | Smooth, uniform, laser-cuts well | Weak at screw holes, absorbs moisture, dust is toxic | Good for laser, fragile at fastener points |
| Hardboard (Masonite) | 3mm | ~70g | Very smooth, cheap, uniform | Flexes more than ply, poor screw holding | Acceptable if stiffened by standoffs |
| Acrylic (cast) | 3mm | ~90g | Looks great, laser-cuts beautifully | Brittle, cracks at screw holes under vibration | Good for top deck only (show piece) |
| PETG sheet | 2-3mm | ~100g | Tough, vibration-resistant, no cracking | Harder to laser-cut, expensive | Overkill for v1 |
| Corrugated cardboard | 3-5mm | ~15g | Free, instant, cuttable with box cutter | Weak, temporary, absorbs moisture | **Prototype/test fit only** |

### Thickness Decision Guide

| Thickness | When to Use | Notes |
|---|---|---|
| **3mm** | Laser-cut plywood or MDF. This is the default. | Stiff enough with standoffs providing structural bracing. Lightest option. |
| **4mm** | Hand-cut plywood if 3mm is not available. | Slightly heavier but more forgiving for hand cutting -- less likely to crack at drill holes. |
| **5mm** | Hand-cut builds with weaker materials (MDF, hardboard). | Extra thickness compensates for reduced material strength at fastener points. |
| **6mm+** | Not recommended. | Adds unnecessary weight. TT motors are low-torque -- keep the chassis light. |

### Weight Budget

Keeping the chassis light matters because TT motors produce approximately 0.5 kg-cm of torque. A heavy chassis means slow acceleration, poor hill climbing, and inability to turn on carpet.

| Component | Estimated Weight |
|---|---|
| Bottom deck (3mm ply, 250x200) | ~60g |
| Top deck (3mm ply, 250x200) | ~60g |
| 2x TT motors | ~60g |
| 2x TT wheels | ~40g |
| Caster assembly | ~15g |
| 4x standoffs (M3x35 printed) | ~10g |
| Motor clips (2x printed) | ~10g |
| Battery (2S Li-Ion) | ~80-120g |
| Pi 3B | ~42g |
| ESP32 dev board | ~10g |
| Motor driver shield | ~25g |
| Buck converter | ~10g |
| Breadboard + wiring | ~30g |
| Sensors (HC-SR04 x2, IMU, webcam) | ~40g |
| Fasteners (screws, nuts, washers) | ~20g |
| **TOTAL ESTIMATED** | **~500-550g** |

TT motors can comfortably drive a 500-600g robot on hard floors. Above 700g, turning on carpet becomes sluggish. Stay under 600g if possible.

---

## Critical Dimensions and Checks

Before cutting, verify these relationships hold:

```
1. Wheels must not collide with plate:
   WHEEL_WIDTH/2 + WHEEL_CLEARANCE < (how far motor shaft extends beyond plate edge)
   28/2 + 2 = 16mm < MOTOR_AXLE_PROTRUDE + overhang = OK if motor body is at plate edge

2. Chassis must sit level (front wheels and rear caster at same height):
   WHEEL_DIAMETER/2 = caster ground contact to plate bottom surface
   65/2 = 32.5mm from ground to motor axle
   Caster must also provide 32.5mm from ground to bottom plate surface
   Caster height = 32.5 - PLATE_THICKNESS (if motors mount on top of plate)
   = 32.5 - 3 = 29.5mm (ball bottom to plate top surface)

3. Top deck clearance:
   DECK_SPACING (35mm) must be greater than tallest bottom-deck component
   Battery height (20mm) + any standoffs/wiring = ~25mm max → 35mm provides 10mm margin

4. Standoff bolts must be long enough:
   Bolt length >= PLATE_THICKNESS + STANDOFF_LENGTH + PLATE_THICKNESS + nut height
   = 3 + 35 + 3 + 2.5 = 43.5mm → use M3x45mm bolts

5. Total height from ground to top of webcam:
   Ground to bottom plate bottom: 32.5mm (wheel radius)
   Bottom plate: 3mm
   Deck spacing: 35mm
   Top plate: 3mm
   Webcam post: 40mm
   = ~113.5mm total (~4.5 inches) — compact and stable
```

---

## Design Rationale

**Why rectangular, not circular?** Rectangular plates are trivially easy to cut by hand, use material efficiently (no waste triangles), and provide obvious mounting alignment. Circular chassis look cool but waste material and make hand-cutting harder.

**Why two decks?** Separation of concerns. Heavy, hot, and mechanical (motors, battery) go on the bottom for low center of gravity. Delicate electronics go on top where they are accessible and away from wheel spray. The air gap between decks provides natural ventilation.

**Why motors at the front?** In a 2WD + rear caster configuration, front-wheel drive provides better straight-line tracking because the caster trails passively. Rear-wheel drive can cause the front to "wander" or the caster to oscillate (shimmy). Front-drive with a trailing caster is more stable.

**Why 35mm deck spacing?** Must clear the battery (20mm) with room for wiring above it. Must be short enough to keep center of gravity low. 35mm is the sweet spot -- 30mm works but is tight, 40mm works but raises the CG unnecessarily.

**Why M3 throughout?** One bolt size means one wrench, one drill bit, and one tap. M3 is strong enough for a 500g robot, small enough to not weaken 3mm plywood, and universally available. The only exception is the Pi 3B which uses M2.5 mounting holes per its board spec.

---

## Files to Generate (Future Step)

Once this design is approved, the following files will be created:

| File | Format | Contents |
|---|---|---|
| `bottom_deck.svg` | SVG | Laser-cuttable bottom plate outline + all holes |
| `top_deck.svg` | SVG | Laser-cuttable top plate outline + all holes |
| `motor_clip.stl` | STL | 3D printable TT motor mount clip |
| `ball_caster.stl` | STL | 3D printable ball caster housing |
| `standoff_35mm.stl` | STL | 3D printable deck standoff |
| `sensor_bracket.stl` | STL | 3D printable HC-SR04 angle bracket |
| `webcam_post.stl` | STL | 3D printable webcam elevation post |
| `assembly_guide.svg` | SVG | Full assembly reference with dimensions |

**No files are generated by this document.** This is the specification that those files will be built from.

---

*This design is intentionally simple, cheap, and reproducible. A hand saw, a drill, and a 3D printer can build the entire chassis. No precision CNC required. The parametric variables at the top let you scale it for different motors, different boards, or different plate sizes without redesigning from scratch.*
