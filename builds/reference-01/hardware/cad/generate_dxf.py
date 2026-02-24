#!/usr/bin/env python3
"""
EvoBot reference-01 Chassis DXF Generator
==========================================
Generates laser-cuttable DXF files for the two-deck robot chassis.

Reads parametric dimensions from variables at the top of this file.
All dimensions in millimeters. Origin (0,0) at rear-left corner of each plate.
X increases toward front, Y increases toward right.

Output files:
  - bottom_deck.dxf   : Base plate with motor mounts, caster, standoffs, wire slot
  - top_deck.dxf       : Electronics plate with Pi, ESP32, sensor mounts
  - all_parts.dxf      : Both plates side-by-side for single-sheet cutting

DXF conventions:
  - Layer "CUT" (color 1 / red)     : Cut lines (outline, holes, slots)
  - Layer "ENGRAVE" (color 5 / blue) : Reference/engrave lines (labels, outlines)
  - Units: millimeters
  - Rounded corners as arcs, holes as circles

Requires: ezdxf >= 1.0
"""

import math
import ezdxf
from ezdxf.math import Vec2

# =============================================================================
# PARAMETRIC DIMENSIONS — Change these to resize the entire design
# =============================================================================

# --- Chassis Envelope ---
PLATE_LENGTH          = 250       # X dimension (front-to-back)
PLATE_WIDTH           = 200       # Y dimension (left-to-right)
PLATE_THICKNESS       = 3         # Material thickness (3mm ply default)
CORNER_RADIUS         = 15        # Rounded corner radius
DECK_SPACING          = 35        # Vertical gap between decks

# --- Motor Geometry (TT Yellow Geared DC) ---
MOTOR_MOUNT_HOLE_DIA  = 3.2       # M3 clearance
MOTOR_MOUNT_HOLE_SPAN = 17        # Center-to-center of two M3 mounting holes
MOTOR_X_OFFSET        = 65        # Motor axle center from FRONT edge
MOTOR_Y_INSET_LEFT    = 15        # Left motor mount holes Y position
MOTOR_Y_INSET_RIGHT   = 185       # Right motor mount holes Y position

# --- Caster ---
CASTER_MOUNT_HOLE_DIA = 3.2       # M3 clearance
CASTER_MOUNT_HOLE_SPAN= 30        # Bolt pattern diameter (3 holes on circle)
CASTER_X_OFFSET       = 30        # Caster center from REAR edge
CASTER_NUM_HOLES      = 3         # Triangle pattern

# --- Standoffs (Deck-to-Deck) ---
STANDOFF_HOLE_DIA     = 3.2       # M3 clearance
STANDOFF_INSET_X      = 15        # From front/rear edges
STANDOFF_INSET_Y      = 15        # From left/right edges

# --- Wire Pass-Through ---
WIRE_SLOT_WIDTH       = 10        # Slot width (Y direction in spec request)
WIRE_SLOT_LENGTH      = 30        # Slot length (X direction in spec request)
WIRE_SLOT_X           = 50        # Center X (from spec coordinate table)
WIRE_SLOT_Y           = 100       # Center Y

# --- Battery Area (Reference Only) ---
BATTERY_LENGTH        = 105       # From spec
BATTERY_WIDTH         = 35        # From spec
BATTERY_CENTER_X      = 110       # From spec coordinate table
BATTERY_CENTER_Y      = 100       # From spec coordinate table

# --- Pi 3B Mounting ---
PI_MOUNT_HOLE_DIA     = 2.7       # M2.5 clearance
PI_MOUNT_RECT_X       = 58        # Hole pattern X span (center-to-center)
PI_MOUNT_RECT_Y       = 49        # Hole pattern Y span (center-to-center)
PI_CENTER_X           = 45        # From spec coordinate table
PI_CENTER_Y           = 105       # From spec coordinate table

# --- ESP32 Dev Board Mounting ---
ESP32_MOUNT_HOLE_DIA  = 3.2       # Using M3 as per user request
ESP32_MOUNT_HOLE_SPAN = 52        # X span between 2 holes, per user request
ESP32_CENTER_X        = 170       # From spec coordinate table
ESP32_CENTER_Y        = 100       # From spec coordinate table

# --- Breadboard Area (Reference Only) ---
BREADBOARD_LENGTH     = 55        # Per user request (reference outline)
BREADBOARD_WIDTH      = 35        # Per user request
BREADBOARD_CENTER_X   = 115       # From spec coordinate table
BREADBOARD_CENTER_Y   = 100       # From spec coordinate table

# --- HC-SR04 Sensor Mount Slots ---
SENSOR_SLOT_WIDTH     = 45        # Rectangular cutout width (Y direction)
SENSOR_SLOT_HEIGHT    = 20        # Rectangular cutout depth (X direction)
SENSOR_LEFT_X         = 245       # From spec coordinate table
SENSOR_LEFT_Y         = 45        # From spec coordinate table
SENSOR_RIGHT_X        = 245       # From spec coordinate table
SENSOR_RIGHT_Y        = 155       # From spec coordinate table
SENSOR_ANGLE          = 15        # Outward angle in degrees

# --- Webcam Mount ---
WEBCAM_HOLE_DIA       = 4.2       # M4 clearance per user request (M3 or M4)
WEBCAM_X              = 245       # Front-center edge
WEBCAM_Y              = 100       # Centered

# --- All Parts Layout ---
LAYOUT_GAP            = 10        # Gap between plates in all_parts layout

# --- Crosshair Mark Size ---
CROSSHAIR_SIZE        = 5         # Half-length of crosshair lines

# --- Fastener Reference ---
M3_CLEARANCE          = 3.2
M2_5_CLEARANCE        = 2.7

# =============================================================================
# LAYER SETUP
# =============================================================================

# DXF color indices
COLOR_RED   = 1   # Cut lines
COLOR_BLUE  = 5   # Engrave/reference lines


def setup_layers(doc):
    """Create CUT and ENGRAVE layers in the document."""
    doc.layers.add("CUT", color=COLOR_RED)
    doc.layers.add("ENGRAVE", color=COLOR_BLUE)


# =============================================================================
# GEOMETRY HELPERS
# =============================================================================

def draw_rounded_rect(msp, x0, y0, width, height, radius, layer="CUT"):
    """
    Draw a rectangle with rounded corners using lines and arcs.
    (x0, y0) is the bottom-left corner. Width is in Y, Height is in X.

    For our coordinate system:
      - x0, y0: rear-left corner
      - height: length in X direction (front-to-back)
      - width: width in Y direction (left-to-right)
    """
    r = radius
    w = width
    h = height

    # Corner centers
    bl = (x0 + r, y0 + r)          # bottom-left (rear-left)
    br = (x0 + r, y0 + w - r)      # bottom-right (rear-right)
    tl = (x0 + h - r, y0 + r)      # top-left (front-left)
    tr = (x0 + h - r, y0 + w - r)  # top-right (front-right)

    # Bottom edge (rear): from bl arc end to br arc start
    msp.add_line((x0, y0 + r), (x0, y0 + w - r), dxfattribs={"layer": layer})
    # Top edge (front): from tl arc end to tr arc start
    msp.add_line((x0 + h, y0 + r), (x0 + h, y0 + w - r), dxfattribs={"layer": layer})
    # Left edge: from bl arc to tl arc
    msp.add_line((x0 + r, y0), (x0 + h - r, y0), dxfattribs={"layer": layer})
    # Right edge: from br arc to tr arc
    msp.add_line((x0 + r, y0 + w), (x0 + h - r, y0 + w), dxfattribs={"layer": layer})

    # Corner arcs (center, radius, start_angle, end_angle) — angles in degrees
    # Bottom-left (rear-left): 180 to 270
    msp.add_arc(bl, r, 180, 270, dxfattribs={"layer": layer})
    # Bottom-right (rear-right): 270 to 360
    msp.add_arc(br, r, 270, 360, dxfattribs={"layer": layer})
    # Top-left (front-left): 90 to 180
    msp.add_arc(tl, r, 90, 180, dxfattribs={"layer": layer})
    # Top-right (front-right): 0 to 90
    msp.add_arc(tr, r, 0, 90, dxfattribs={"layer": layer})


def draw_circle(msp, cx, cy, diameter, layer="CUT"):
    """Draw a circle at (cx, cy) with given diameter."""
    msp.add_circle((cx, cy), diameter / 2, dxfattribs={"layer": layer})


def draw_rect_slot(msp, cx, cy, slot_width, slot_length, layer="CUT"):
    """
    Draw a rectangular slot (cutout) centered at (cx, cy).
    slot_length is in X direction, slot_width is in Y direction.
    Uses lines (sharp corners for simplicity — these are small cutouts).
    """
    x1 = cx - slot_length / 2
    x2 = cx + slot_length / 2
    y1 = cy - slot_width / 2
    y2 = cy + slot_width / 2
    msp.add_line((x1, y1), (x2, y1), dxfattribs={"layer": layer})
    msp.add_line((x2, y1), (x2, y2), dxfattribs={"layer": layer})
    msp.add_line((x2, y2), (x1, y2), dxfattribs={"layer": layer})
    msp.add_line((x1, y2), (x1, y1), dxfattribs={"layer": layer})


def draw_rect_outline(msp, cx, cy, length_x, width_y, layer="ENGRAVE"):
    """Draw a reference rectangle outline centered at (cx, cy)."""
    draw_rect_slot(msp, cx, cy, width_y, length_x, layer=layer)


def draw_crosshair(msp, cx, cy, size=CROSSHAIR_SIZE, layer="ENGRAVE"):
    """Draw crosshair marks at a point."""
    msp.add_line((cx - size, cy), (cx + size, cy), dxfattribs={"layer": layer})
    msp.add_line((cx, cy - size), (cx, cy + size), dxfattribs={"layer": layer})


def draw_rotated_rect_slot(msp, cx, cy, slot_width, slot_height, angle_deg, layer="CUT"):
    """
    Draw a rectangular slot rotated by angle_deg around its center (cx, cy).
    slot_width is the horizontal dimension (before rotation).
    slot_height is the vertical dimension (before rotation).
    """
    a = math.radians(angle_deg)
    cos_a = math.cos(a)
    sin_a = math.sin(a)

    # Half dimensions
    hw = slot_width / 2
    hh = slot_height / 2

    # Corner offsets relative to center (before rotation)
    corners_local = [
        (-hh, -hw),
        ( hh, -hw),
        ( hh,  hw),
        (-hh,  hw),
    ]

    # Rotate and translate
    corners = []
    for dx, dy in corners_local:
        rx = cx + dx * cos_a - dy * sin_a
        ry = cy + dx * sin_a + dy * cos_a
        corners.append((rx, ry))

    # Draw edges
    for i in range(4):
        msp.add_line(corners[i], corners[(i + 1) % 4], dxfattribs={"layer": layer})


def add_label(msp, x, y, text, height=5, layer="ENGRAVE"):
    """Add a text label."""
    msp.add_text(text, height=height, dxfattribs={"layer": layer}).set_placement((x, y))


# =============================================================================
# PLATE COORDINATE CALCULATIONS
# =============================================================================

def get_standoff_positions():
    """Return the 4 standoff hole positions (same for both decks)."""
    return [
        (STANDOFF_INSET_X, STANDOFF_INSET_Y),                                    # Rear-left
        (STANDOFF_INSET_X, PLATE_WIDTH - STANDOFF_INSET_Y),                      # Rear-right
        (PLATE_LENGTH - STANDOFF_INSET_X, STANDOFF_INSET_Y),                     # Front-left
        (PLATE_LENGTH - STANDOFF_INSET_X, PLATE_WIDTH - STANDOFF_INSET_Y),       # Front-right
    ]


def get_motor_mount_positions():
    """
    Return left and right motor mount hole positions (2 holes each).
    Motor axle X = PLATE_LENGTH - MOTOR_X_OFFSET = 185
    Mount holes are +/- MOTOR_MOUNT_HOLE_SPAN/2 from axle X.
    """
    axle_x = PLATE_LENGTH - MOTOR_X_OFFSET  # 185
    half_span = MOTOR_MOUNT_HOLE_SPAN / 2   # 8.5

    left = [
        (axle_x - half_span, MOTOR_Y_INSET_LEFT),   # 176.5, 15
        (axle_x + half_span, MOTOR_Y_INSET_LEFT),   # 193.5, 15
    ]
    right = [
        (axle_x - half_span, MOTOR_Y_INSET_RIGHT),  # 176.5, 185
        (axle_x + half_span, MOTOR_Y_INSET_RIGHT),  # 193.5, 185
    ]
    return left, right


def get_caster_mount_positions():
    """
    Return caster mount hole positions (triangle pattern on a circle).
    Center at (CASTER_X_OFFSET, PLATE_WIDTH/2).
    """
    cx = CASTER_X_OFFSET  # 30
    cy = PLATE_WIDTH / 2  # 100
    r = CASTER_MOUNT_HOLE_SPAN / 2  # 15

    positions = []
    for i in range(CASTER_NUM_HOLES):
        angle = math.radians(90 + i * (360 / CASTER_NUM_HOLES))  # Start top, go clockwise
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        positions.append((px, py))
    return positions


def get_pi_mount_positions():
    """Return the 4 Pi 3B mounting hole positions."""
    cx = PI_CENTER_X
    cy = PI_CENTER_Y
    hx = PI_MOUNT_RECT_X / 2  # 29
    hy = PI_MOUNT_RECT_Y / 2  # 24.5

    return [
        (cx - hx, cy - hy),  # 16, 80.5
        (cx + hx, cy - hy),  # 74, 80.5
        (cx - hx, cy + hy),  # 16, 129.5
        (cx + hx, cy + hy),  # 74, 129.5
    ]


def get_esp32_mount_positions():
    """Return the 2 ESP32 mounting hole positions."""
    cx = ESP32_CENTER_X
    cy = ESP32_CENTER_Y
    half_span = ESP32_MOUNT_HOLE_SPAN / 2  # 26

    return [
        (cx - half_span, cy),  # 144, 100
        (cx + half_span, cy),  # 196, 100
    ]


# =============================================================================
# BOTTOM DECK
# =============================================================================

def draw_bottom_deck(msp, offset_x=0, offset_y=0):
    """Draw the complete bottom deck plate."""
    ox, oy = offset_x, offset_y

    # --- Plate outline (CUT) ---
    draw_rounded_rect(msp, ox, oy, PLATE_WIDTH, PLATE_LENGTH, CORNER_RADIUS, layer="CUT")

    # --- Origin crosshair (ENGRAVE) ---
    draw_crosshair(msp, ox, oy)

    # --- Standoff holes (CUT) ---
    for (sx, sy) in get_standoff_positions():
        draw_circle(msp, ox + sx, oy + sy, STANDOFF_HOLE_DIA, layer="CUT")

    # --- Motor mount holes (CUT) ---
    left_motors, right_motors = get_motor_mount_positions()
    for (mx, my) in left_motors + right_motors:
        draw_circle(msp, ox + mx, oy + my, MOTOR_MOUNT_HOLE_DIA, layer="CUT")

    # --- Caster mount holes (CUT) ---
    for (cx_pos, cy_pos) in get_caster_mount_positions():
        draw_circle(msp, ox + cx_pos, oy + cy_pos, CASTER_MOUNT_HOLE_DIA, layer="CUT")

    # --- Wire pass-through slot (CUT) ---
    draw_rect_slot(msp, ox + WIRE_SLOT_X, oy + WIRE_SLOT_Y,
                   WIRE_SLOT_WIDTH, WIRE_SLOT_LENGTH, layer="CUT")

    # --- Battery area outline (ENGRAVE — reference only) ---
    draw_rect_outline(msp, ox + BATTERY_CENTER_X, oy + BATTERY_CENTER_Y,
                      BATTERY_LENGTH, BATTERY_WIDTH, layer="ENGRAVE")

    # --- Labels (ENGRAVE) ---
    add_label(msp, ox + PLATE_LENGTH / 2 - 30, oy + PLATE_WIDTH / 2 - 3,
              "BOTTOM DECK", height=6, layer="ENGRAVE")
    add_label(msp, ox + BATTERY_CENTER_X - 12, oy + BATTERY_CENTER_Y - 3,
              "BATTERY", height=3, layer="ENGRAVE")

    # Motor labels
    axle_x = PLATE_LENGTH - MOTOR_X_OFFSET
    add_label(msp, ox + axle_x - 8, oy + MOTOR_Y_INSET_LEFT + 5,
              "L MTR", height=3, layer="ENGRAVE")
    add_label(msp, ox + axle_x - 8, oy + MOTOR_Y_INSET_RIGHT - 15,
              "R MTR", height=3, layer="ENGRAVE")

    # Caster label
    add_label(msp, ox + CASTER_X_OFFSET - 8, oy + PLATE_WIDTH / 2 + 18,
              "CASTER", height=3, layer="ENGRAVE")

    # Wire slot label
    add_label(msp, ox + WIRE_SLOT_X - 12, oy + WIRE_SLOT_Y + 18,
              "WIRE SLOT", height=2.5, layer="ENGRAVE")


# =============================================================================
# TOP DECK
# =============================================================================

def draw_top_deck(msp, offset_x=0, offset_y=0):
    """Draw the complete top deck plate."""
    ox, oy = offset_x, offset_y

    # --- Plate outline (CUT) ---
    draw_rounded_rect(msp, ox, oy, PLATE_WIDTH, PLATE_LENGTH, CORNER_RADIUS, layer="CUT")

    # --- Origin crosshair (ENGRAVE) ---
    draw_crosshair(msp, ox, oy)

    # --- Standoff holes (CUT) — same positions as bottom deck ---
    for (sx, sy) in get_standoff_positions():
        draw_circle(msp, ox + sx, oy + sy, STANDOFF_HOLE_DIA, layer="CUT")

    # --- Pi 3B mount holes (CUT) ---
    for (px, py) in get_pi_mount_positions():
        draw_circle(msp, ox + px, oy + py, PI_MOUNT_HOLE_DIA, layer="CUT")

    # --- ESP32 mount holes (CUT) ---
    for (ex, ey) in get_esp32_mount_positions():
        draw_circle(msp, ox + ex, oy + ey, ESP32_MOUNT_HOLE_DIA, layer="CUT")

    # --- Breadboard area outline (ENGRAVE — reference only) ---
    draw_rect_outline(msp, ox + BREADBOARD_CENTER_X, oy + BREADBOARD_CENTER_Y,
                      BREADBOARD_LENGTH, BREADBOARD_WIDTH, layer="ENGRAVE")

    # --- HC-SR04 sensor mount slots (CUT) ---
    # Left sensor: angled outward (negative angle = toward left edge)
    draw_rotated_rect_slot(msp, ox + SENSOR_LEFT_X, oy + SENSOR_LEFT_Y,
                           SENSOR_SLOT_WIDTH, SENSOR_SLOT_HEIGHT,
                           -SENSOR_ANGLE, layer="CUT")
    # Right sensor: angled outward (positive angle = toward right edge)
    draw_rotated_rect_slot(msp, ox + SENSOR_RIGHT_X, oy + SENSOR_RIGHT_Y,
                           SENSOR_SLOT_WIDTH, SENSOR_SLOT_HEIGHT,
                           SENSOR_ANGLE, layer="CUT")

    # --- Wire pass-through slot (CUT) — aligned with bottom deck ---
    draw_rect_slot(msp, ox + WIRE_SLOT_X, oy + WIRE_SLOT_Y,
                   WIRE_SLOT_WIDTH, WIRE_SLOT_LENGTH, layer="CUT")

    # --- Webcam mount hole (CUT) ---
    draw_circle(msp, ox + WEBCAM_X, oy + WEBCAM_Y, WEBCAM_HOLE_DIA, layer="CUT")

    # --- Labels (ENGRAVE) ---
    add_label(msp, ox + PLATE_LENGTH / 2 - 25, oy + PLATE_WIDTH / 2 - 3,
              "TOP DECK", height=6, layer="ENGRAVE")

    # Pi label
    add_label(msp, ox + PI_CENTER_X - 6, oy + PI_CENTER_Y - 3,
              "Pi 3B", height=3, layer="ENGRAVE")

    # ESP32 label
    add_label(msp, ox + ESP32_CENTER_X - 8, oy + ESP32_CENTER_Y + 8,
              "ESP32", height=3, layer="ENGRAVE")

    # Breadboard label
    add_label(msp, ox + BREADBOARD_CENTER_X - 12, oy + BREADBOARD_CENTER_Y - 3,
              "BREADBOARD", height=2.5, layer="ENGRAVE")

    # Sensor labels
    add_label(msp, ox + SENSOR_LEFT_X - 20, oy + SENSOR_LEFT_Y - 18,
              "HC-SR04 L", height=2.5, layer="ENGRAVE")
    add_label(msp, ox + SENSOR_RIGHT_X - 20, oy + SENSOR_RIGHT_Y + 14,
              "HC-SR04 R", height=2.5, layer="ENGRAVE")

    # Webcam label
    add_label(msp, ox + WEBCAM_X - 10, oy + WEBCAM_Y + 5,
              "WEBCAM", height=2.5, layer="ENGRAVE")


# =============================================================================
# FILE GENERATION
# =============================================================================

def create_dxf():
    """Create a new DXF document with standard setup."""
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4  # 4 = millimeters
    doc.header["$MEASUREMENT"] = 1  # 1 = metric
    setup_layers(doc)
    return doc


def generate_bottom_deck(output_path):
    """Generate bottom_deck.dxf."""
    doc = create_dxf()
    msp = doc.modelspace()
    draw_bottom_deck(msp)
    doc.saveas(output_path)
    print(f"  Created: {output_path}")


def generate_top_deck(output_path):
    """Generate top_deck.dxf."""
    doc = create_dxf()
    msp = doc.modelspace()
    draw_top_deck(msp)
    doc.saveas(output_path)
    print(f"  Created: {output_path}")


def generate_all_parts(output_path):
    """Generate all_parts.dxf with both plates side by side."""
    doc = create_dxf()
    msp = doc.modelspace()

    # Bottom deck at origin
    draw_bottom_deck(msp, offset_x=0, offset_y=0)

    # Top deck offset to the right by plate width + gap
    top_offset_y = PLATE_WIDTH + LAYOUT_GAP
    draw_top_deck(msp, offset_x=0, offset_y=top_offset_y)

    # Layout labels (larger, above the plates)
    add_label(msp, PLATE_LENGTH / 2 - 30, -15,
              "BOTTOM DECK", height=8, layer="ENGRAVE")
    add_label(msp, PLATE_LENGTH / 2 - 25, top_offset_y - 15,
              "TOP DECK", height=8, layer="ENGRAVE")

    # Overall title
    add_label(msp, -10, PLATE_WIDTH + LAYOUT_GAP / 2 - 5,
              "EvoBot ref-01 — All Parts", height=6, layer="ENGRAVE")

    doc.saveas(output_path)
    print(f"  Created: {output_path}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    import os

    output_dir = os.path.dirname(os.path.abspath(__file__))

    print("EvoBot reference-01 Chassis DXF Generator")
    print("=" * 50)
    print(f"Plate size: {PLATE_LENGTH} x {PLATE_WIDTH} mm")
    print(f"Corner radius: {CORNER_RADIUS} mm")
    print(f"Output directory: {output_dir}")
    print()

    bottom_path = os.path.join(output_dir, "bottom_deck.dxf")
    top_path    = os.path.join(output_dir, "top_deck.dxf")
    all_path    = os.path.join(output_dir, "all_parts.dxf")

    generate_bottom_deck(bottom_path)
    generate_top_deck(top_path)
    generate_all_parts(all_path)

    print()
    print("File sizes:")
    for path in [bottom_path, top_path, all_path]:
        size = os.path.getsize(path)
        name = os.path.basename(path)
        print(f"  {name}: {size:,} bytes ({size / 1024:.1f} KB)")

    print()
    print("Done. All DXF files generated successfully.")

    # Print a summary of what's in each file
    print()
    print("Summary:")
    print("-" * 50)
    print("bottom_deck.dxf:")
    print("  - 250x200mm rounded rect outline (15mm radii)")
    print("  - 4x M3 standoff holes at corners")
    print("  - 4x M3 motor mount holes (2 per motor, front-left/right)")
    print("  - 3x M3 caster mount holes (triangle pattern, rear-center)")
    print("  - 1x 10x30mm wire pass-through slot (center)")
    print("  - Battery area reference outline (engrave layer)")
    print()
    print("top_deck.dxf:")
    print("  - 250x200mm rounded rect outline (15mm radii)")
    print("  - 4x M3 standoff holes at corners (matching bottom)")
    print("  - 4x M2.5 Pi 3B mounting holes (58x49mm pattern)")
    print("  - 2x M3 ESP32 mounting holes (52mm apart)")
    print("  - 2x HC-SR04 sensor slot cutouts (45x20mm, angled 15 deg)")
    print("  - 1x M4 webcam mount hole (front-center)")
    print("  - 1x 10x30mm wire pass-through slot (aligned with bottom)")
    print("  - Breadboard area reference outline (engrave layer)")
    print()
    print("all_parts.dxf:")
    print("  - Both plates side-by-side, 10mm gap")
    print(f"  - Total sheet: {PLATE_LENGTH}x{PLATE_WIDTH * 2 + LAYOUT_GAP}mm")


if __name__ == "__main__":
    main()
