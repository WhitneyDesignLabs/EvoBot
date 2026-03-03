#!/usr/bin/env python3
"""
EvoBot reference-01 Chassis DXF Generator (v2 — laser-ready)
=============================================================
Generates laser-cuttable DXF files with CLOSED POLYLINE paths.

All outlines use LWPOLYLINE with bulge values for rounded corners,
ensuring the laser follows a single continuous cut path.

Outputs DXF files + PNG previews for visual verification.

Coordinate system:
  - Origin (0,0) at bottom-left (rear-left of robot)
  - X = left-to-right (width, 200mm)
  - Y = bottom-to-top (length/depth, 250mm — rear to front)

All dimensions in millimeters.
Requires: ezdxf >= 1.0, matplotlib (for preview)
"""

import math
import os
import ezdxf

# =============================================================================
# PARAMETRIC DIMENSIONS — Change these to resize the entire design
# =============================================================================

# Chassis envelope
PLATE_WIDTH   = 200    # X dimension (left-to-right)
PLATE_LENGTH  = 250    # Y dimension (rear-to-front)
CORNER_RADIUS = 15     # Rounded corner radius

# Standoff holes (deck-to-deck, M3)
STANDOFF_HOLE_DIA = 3.2
STANDOFF_INSET    = 15  # From each edge

# Motor mounts (bottom deck only)
# TT motors at front, symmetric about centerline
MOTOR_HOLE_DIA    = 3.2   # M3
MOTOR_HOLE_SPAN   = 17    # Between two holes per motor
MOTOR_Y_CENTER    = 185   # Y position of motor axle (near front)
MOTOR_LEFT_X      = 25    # Left motor centerline from left edge
MOTOR_RIGHT_X     = 175   # Right motor centerline from right edge

# Caster mount (bottom deck, rear center)
CASTER_HOLE_DIA   = 3.2
CASTER_BOLT_RADIUS= 12    # Bolt pattern circle radius
CASTER_Y_CENTER   = 30    # From rear edge
CASTER_X_CENTER   = 100   # Centered

# Wire pass-through slot
WIRE_SLOT_W       = 30    # Width (X)
WIRE_SLOT_H       = 10    # Height (Y)
WIRE_SLOT_X       = 100   # Center X
WIRE_SLOT_Y       = 55    # Center Y (between caster and battery)

# Battery reference area (engrave only)
BATTERY_W         = 80
BATTERY_H         = 50
BATTERY_X         = 100   # Center X
BATTERY_Y         = 120   # Center Y

# Pi 3B mount (top deck, rear area)
PI_HOLE_DIA       = 2.7   # M2.5
PI_RECT_W         = 58    # Hole pattern width
PI_RECT_H         = 49    # Hole pattern height
PI_X              = 100   # Center X
PI_Y              = 60    # Center Y (rear portion)

# ESP32 mount (top deck, mid area)
ESP32_HOLE_DIA    = 3.2
ESP32_HOLE_SPAN   = 52    # Between two holes
ESP32_X           = 100   # Center X
ESP32_Y           = 135   # Center Y

# Breadboard reference area (engrave only)
BREAD_W           = 55
BREAD_H           = 35
BREAD_X           = 100
BREAD_Y           = 100

# HC-SR04 sensor cutouts (top deck, front edge area)
# Rectangular cutouts for ultrasonic transducers to face forward
SENSOR_SLOT_W     = 45    # Width (X)
SENSOR_SLOT_H     = 20    # Height (Y)
SENSOR_LEFT_X     = 50    # Center X of left sensor
SENSOR_RIGHT_X    = 150   # Center X of right sensor
SENSOR_Y          = 232   # Center Y (near front edge, 18mm from edge)
SENSOR_ANGLE      = 15    # Outward angle in degrees

# Sensor bracket bolt holes (top deck, behind each sensor cutout)
BRACKET_HOLE_DIA  = 3.2    # M3
BRACKET_HOLE_SPAN = 35     # mm between 2 holes per bracket
BRACKET_Y         = SENSOR_Y - SENSOR_SLOT_H / 2 - 8  # 8mm behind sensor cutout rear edge

# Webcam mount hole (top deck, front center)
WEBCAM_HOLE_DIA   = 4.2   # M4
WEBCAM_X          = 100
WEBCAM_Y          = 240   # 10mm from front edge

# All-parts layout gap
LAYOUT_GAP        = 20

# =============================================================================
# DXF SETUP
# =============================================================================

COLOR_RED  = 1  # Cut
COLOR_BLUE = 5  # Engrave


def create_doc():
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4      # mm
    doc.header["$MEASUREMENT"] = 1   # metric
    doc.layers.add("CUT", color=COLOR_RED)
    doc.layers.add("ENGRAVE", color=COLOR_BLUE)
    return doc


# =============================================================================
# GEOMETRY: Closed polyline rounded rectangle
# =============================================================================

def add_rounded_rect(msp, cx, cy, w, h, r, layer="CUT"):
    """
    Add a CLOSED rounded rectangle as a single LWPOLYLINE.
    cx, cy = center of rectangle
    w = width (X), h = height (Y), r = corner radius

    Uses bulge values for 90-degree arcs at each corner.
    The polyline is a single closed entity — one continuous cut path.
    """
    # Half dimensions
    hw, hh = w / 2, h / 2
    # Bulge for 90-degree arc (CCW): tan(theta/4) = tan(22.5deg)
    bulge = math.tan(math.pi / 8)  # ≈ 0.41421356

    # 8 points going CCW from bottom-left corner
    # Each corner contributes 2 points (arc start and arc end)
    # Bulge is applied at the arc-start point
    points = [
        # Bottom-left corner (rear-left)
        (cx - hw,     cy - hh + r, 0, 0, -bulge),  # arc start
        (cx - hw + r, cy - hh,     0, 0, 0),        # arc end / bottom edge start
        # Bottom-right corner (rear-right)
        (cx + hw - r, cy - hh,     0, 0, -bulge),   # arc start
        (cx + hw,     cy - hh + r, 0, 0, 0),        # arc end / right edge start
        # Top-right corner (front-right)
        (cx + hw,     cy + hh - r, 0, 0, -bulge),   # arc start
        (cx + hw - r, cy + hh,     0, 0, 0),        # arc end / top edge start
        # Top-left corner (front-left)
        (cx - hw + r, cy + hh,     0, 0, -bulge),   # arc start
        (cx - hw,     cy + hh - r, 0, 0, 0),        # arc end / left edge start
    ]

    poly = msp.add_lwpolyline(
        points, format="xyseb", close=True,
        dxfattribs={"layer": layer}
    )
    return poly


def add_rect_slot(msp, cx, cy, w, h, layer="CUT"):
    """Add a closed rectangular cutout as LWPOLYLINE."""
    hw, hh = w / 2, h / 2
    points = [
        (cx - hw, cy - hh),
        (cx + hw, cy - hh),
        (cx + hw, cy + hh),
        (cx - hw, cy + hh),
    ]
    msp.add_lwpolyline(points, close=True, dxfattribs={"layer": layer})


def add_rotated_rect_slot(msp, cx, cy, w, h, angle_deg, layer="CUT"):
    """Add a closed rotated rectangular cutout as LWPOLYLINE."""
    hw, hh = w / 2, h / 2
    a = math.radians(angle_deg)
    cos_a, sin_a = math.cos(a), math.sin(a)

    corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    points = []
    for dx, dy in corners:
        rx = cx + dx * cos_a - dy * sin_a
        ry = cy + dx * sin_a + dy * cos_a
        points.append((rx, ry))

    msp.add_lwpolyline(points, close=True, dxfattribs={"layer": layer})


def add_circle(msp, cx, cy, dia, layer="CUT"):
    """Add a circle (for drill holes)."""
    msp.add_circle((cx, cy), dia / 2, dxfattribs={"layer": layer})


def add_label(msp, x, y, text, height=4, layer="ENGRAVE"):
    """Add a text label."""
    msp.add_text(text, height=height, dxfattribs={"layer": layer}).set_placement((x, y))


def add_crosshair(msp, cx, cy, size=5, layer="ENGRAVE"):
    """Add crosshair registration mark."""
    msp.add_line((cx - size, cy), (cx + size, cy), dxfattribs={"layer": layer})
    msp.add_line((cx, cy - size), (cx, cy + size), dxfattribs={"layer": layer})


# =============================================================================
# POSITION CALCULATIONS
# =============================================================================

def standoff_positions():
    """4 corner standoff holes."""
    return [
        (STANDOFF_INSET, STANDOFF_INSET),
        (PLATE_WIDTH - STANDOFF_INSET, STANDOFF_INSET),
        (PLATE_WIDTH - STANDOFF_INSET, PLATE_LENGTH - STANDOFF_INSET),
        (STANDOFF_INSET, PLATE_LENGTH - STANDOFF_INSET),
    ]


def motor_positions():
    """Left and right motor mount holes (2 per motor)."""
    hs = MOTOR_HOLE_SPAN / 2
    return [
        (MOTOR_LEFT_X,  MOTOR_Y_CENTER - hs),
        (MOTOR_LEFT_X,  MOTOR_Y_CENTER + hs),
        (MOTOR_RIGHT_X, MOTOR_Y_CENTER - hs),
        (MOTOR_RIGHT_X, MOTOR_Y_CENTER + hs),
    ]


def caster_positions():
    """3 caster mount holes in triangle pattern."""
    positions = []
    for i in range(3):
        angle = math.radians(90 + i * 120)  # Start top, 120 deg apart
        x = CASTER_X_CENTER + CASTER_BOLT_RADIUS * math.cos(angle)
        y = CASTER_Y_CENTER + CASTER_BOLT_RADIUS * math.sin(angle)
        positions.append((x, y))
    return positions


def pi_positions():
    """4 Pi 3B mount holes."""
    hw, hh = PI_RECT_W / 2, PI_RECT_H / 2
    return [
        (PI_X - hw, PI_Y - hh), (PI_X + hw, PI_Y - hh),
        (PI_X - hw, PI_Y + hh), (PI_X + hw, PI_Y + hh),
    ]


def esp32_positions():
    """2 ESP32 mount holes."""
    hs = ESP32_HOLE_SPAN / 2
    return [(ESP32_X - hs, ESP32_Y), (ESP32_X + hs, ESP32_Y)]


# =============================================================================
# PLATE DRAWING FUNCTIONS
# =============================================================================

def draw_bottom_deck(msp, ox=0, oy=0):
    """Draw complete bottom deck."""
    cx = ox + PLATE_WIDTH / 2
    cy = oy + PLATE_LENGTH / 2

    # Outline — single closed polyline with rounded corners
    add_rounded_rect(msp, cx, cy, PLATE_WIDTH, PLATE_LENGTH, CORNER_RADIUS)

    # Crosshair at plate center
    add_crosshair(msp, cx, cy)

    # Standoff holes
    for x, y in standoff_positions():
        add_circle(msp, ox + x, oy + y, STANDOFF_HOLE_DIA)

    # Motor mount holes
    for x, y in motor_positions():
        add_circle(msp, ox + x, oy + y, MOTOR_HOLE_DIA)

    # Caster mount holes
    for x, y in caster_positions():
        add_circle(msp, ox + x, oy + y, CASTER_HOLE_DIA)

    # Wire pass-through slot
    add_rect_slot(msp, ox + WIRE_SLOT_X, oy + WIRE_SLOT_Y, WIRE_SLOT_W, WIRE_SLOT_H)

    # Battery reference (engrave only)
    add_rect_slot(msp, ox + BATTERY_X, oy + BATTERY_Y, BATTERY_W, BATTERY_H, layer="ENGRAVE")

    # Labels
    add_label(msp, ox + 60, oy + PLATE_LENGTH / 2, "BOTTOM DECK", height=6)
    add_label(msp, ox + BATTERY_X - 12, oy + BATTERY_Y - 2, "BATTERY", height=3)
    add_label(msp, ox + MOTOR_LEFT_X - 8, oy + MOTOR_Y_CENTER + 12, "L MTR", height=3)
    add_label(msp, ox + MOTOR_RIGHT_X - 8, oy + MOTOR_Y_CENTER + 12, "R MTR", height=3)
    add_label(msp, ox + CASTER_X_CENTER - 10, oy + CASTER_Y_CENTER - 20, "CASTER", height=3)


def draw_top_deck(msp, ox=0, oy=0):
    """Draw complete top deck."""
    cx = ox + PLATE_WIDTH / 2
    cy = oy + PLATE_LENGTH / 2

    # Outline — single closed polyline with rounded corners
    add_rounded_rect(msp, cx, cy, PLATE_WIDTH, PLATE_LENGTH, CORNER_RADIUS)

    # Crosshair at plate center
    add_crosshair(msp, cx, cy)

    # Standoff holes (same positions as bottom)
    for x, y in standoff_positions():
        add_circle(msp, ox + x, oy + y, STANDOFF_HOLE_DIA)

    # Pi 3B mount holes
    for x, y in pi_positions():
        add_circle(msp, ox + x, oy + y, PI_HOLE_DIA)

    # ESP32 mount holes
    for x, y in esp32_positions():
        add_circle(msp, ox + x, oy + y, ESP32_HOLE_DIA)

    # HC-SR04 sensor cutouts (angled)
    add_rotated_rect_slot(msp, ox + SENSOR_LEFT_X, oy + SENSOR_Y,
                          SENSOR_SLOT_W, SENSOR_SLOT_H, SENSOR_ANGLE)
    add_rotated_rect_slot(msp, ox + SENSOR_RIGHT_X, oy + SENSOR_Y,
                          SENSOR_SLOT_W, SENSOR_SLOT_H, -SENSOR_ANGLE)

    # Sensor bracket bolt holes (2 per bracket, 4 total)
    for sensor_x in [SENSOR_LEFT_X, SENSOR_RIGHT_X]:
        for sign in [-1, 1]:
            hx = sensor_x + sign * BRACKET_HOLE_SPAN / 2
            add_circle(msp, ox + hx, oy + BRACKET_Y, BRACKET_HOLE_DIA)

    # Wire pass-through slot (aligned with bottom)
    add_rect_slot(msp, ox + WIRE_SLOT_X, oy + WIRE_SLOT_Y, WIRE_SLOT_W, WIRE_SLOT_H)

    # Webcam mount hole
    add_circle(msp, ox + WEBCAM_X, oy + WEBCAM_Y, WEBCAM_HOLE_DIA)

    # Reference outlines (engrave)
    add_rect_slot(msp, ox + BREAD_X, oy + BREAD_Y, BREAD_W, BREAD_H, layer="ENGRAVE")

    # Labels
    add_label(msp, ox + 65, oy + PLATE_LENGTH / 2, "TOP DECK", height=6)
    add_label(msp, ox + PI_X - 8, oy + PI_Y - 2, "Pi 3B", height=3)
    add_label(msp, ox + ESP32_X - 8, oy + ESP32_Y + 8, "ESP32", height=3)
    add_label(msp, ox + BREAD_X - 16, oy + BREAD_Y - 2, "BREADBOARD", height=2.5)
    add_label(msp, ox + SENSOR_LEFT_X - 10, oy + SENSOR_Y - 18, "SR04-L", height=2.5)
    add_label(msp, ox + SENSOR_RIGHT_X - 10, oy + SENSOR_Y - 18, "SR04-R", height=2.5)
    add_label(msp, ox + WEBCAM_X - 10, oy + WEBCAM_Y - 8, "WEBCAM", height=2.5)


# =============================================================================
# PREVIEW RENDERING
# =============================================================================

def render_preview(dxf_path, png_path):
    """Render a DXF file to PNG for visual verification."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

        doc = ezdxf.readfile(dxf_path)
        fig, ax = plt.subplots(1, 1, figsize=(12, 15), dpi=150)
        ax.set_aspect('equal')
        ax.set_facecolor('#f8f8f8')
        ax.grid(True, linewidth=0.3, alpha=0.5)
        ax.set_title(os.path.basename(dxf_path), fontsize=14, fontweight='bold')

        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(doc.modelspace())

        fig.tight_layout()
        fig.savefig(png_path, bbox_inches='tight')
        plt.close(fig)
        print(f"  Preview: {png_path}")
        return True
    except Exception as e:
        print(f"  Preview failed: {e}")
        return False


# =============================================================================
# FILE GENERATION
# =============================================================================

def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))

    print("EvoBot reference-01 Chassis DXF Generator v2")
    print("=" * 50)
    print(f"Plate: {PLATE_WIDTH} x {PLATE_LENGTH} mm, R{CORNER_RADIUS} corners")
    print(f"Output: {output_dir}")
    print()

    # --- Bottom deck ---
    path = os.path.join(output_dir, "bottom_deck.dxf")
    doc = create_doc()
    draw_bottom_deck(doc.modelspace())
    doc.saveas(path)
    print(f"  Created: bottom_deck.dxf ({os.path.getsize(path):,} bytes)")
    render_preview(path, os.path.join(output_dir, "bottom_deck_preview.png"))

    # --- Top deck ---
    path = os.path.join(output_dir, "top_deck.dxf")
    doc = create_doc()
    draw_top_deck(doc.modelspace())
    doc.saveas(path)
    print(f"  Created: top_deck.dxf ({os.path.getsize(path):,} bytes)")
    render_preview(path, os.path.join(output_dir, "top_deck_preview.png"))

    # --- All parts ---
    path = os.path.join(output_dir, "all_parts.dxf")
    doc = create_doc()
    msp = doc.modelspace()
    draw_bottom_deck(msp, ox=0, oy=0)
    draw_top_deck(msp, ox=PLATE_WIDTH + LAYOUT_GAP, oy=0)
    add_label(msp, 30, PLATE_LENGTH + 10, "EvoBot ref-01 — Chassis Plates", height=8, layer="ENGRAVE")
    add_label(msp, 50, -15, "BOTTOM DECK", height=6, layer="ENGRAVE")
    add_label(msp, PLATE_WIDTH + LAYOUT_GAP + 50, -15, "TOP DECK", height=6, layer="ENGRAVE")
    doc.saveas(path)
    print(f"  Created: all_parts.dxf ({os.path.getsize(path):,} bytes)")
    render_preview(path, os.path.join(output_dir, "all_parts_preview.png"))

    print()
    print("Done. Open the PNG previews to verify before cutting!")


if __name__ == "__main__":
    main()
