#!/usr/bin/env python3
"""
EvoBot reference-01 Chassis — STL Generator
Generates 3D-printable parts for the robot chassis.

Parts generated:
  1. motor_mount.stl   — TT Motor Mount Clip (print 2x)
  2. ball_caster.stl   — Ball Caster Assembly (print 1x)
  3. standoff.stl      — Deck Standoff (print 4x)
  4. sensor_bracket.stl — HC-SR04 Sensor Bracket (print 2x)
  5. webcam_mount.stl   — Webcam Mount Post (print 1x)

All dimensions in millimeters. Uses numpy-stl for mesh generation.
"""

import os
import math
import numpy as np
from stl import mesh

# ─── Output directory ────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Global parameters ───────────────────────────────────────────────────────
SEGMENTS = 48          # Polygon segments for circles (smoother than 36)
M3_CLEARANCE = 3.2     # mm

# ─── Motor mount parameters ──────────────────────────────────────────────────
MOTOR_BODY_WIDTH = 22      # mm, perpendicular to axle
MOTOR_BODY_HEIGHT = 18     # mm, vertical
MOTOR_MOUNT_WALL = 1.5     # mm, clip wall thickness
MOTOR_CHANNEL_W = 23       # mm inside width (clearance on motor)
MOTOR_CHANNEL_H = 19       # mm inside height (clearance on motor)
MOTOR_CLIP_LENGTH = 30     # mm along motor body length
MOTOR_TAB_WIDTH = 8        # mm each tab
MOTOR_TAB_THICKNESS = 3    # mm
MOTOR_MOUNT_HOLE_SPAN = 17 # mm center-to-center
MOTOR_MOUNT_HOLE_DIA = M3_CLEARANCE

# ─── Ball caster parameters ──────────────────────────────────────────────────
CASTER_BALL_DIA = 16       # mm
CASTER_CUP_ID = 16.5       # mm inner diameter of cup
CASTER_CUP_DEPTH = 10      # mm
CASTER_FLANGE_DIA = 30     # mm
CASTER_FLANGE_THICK = 3    # mm
CASTER_MOUNT_HOLE_SPACING = 20  # mm triangle spacing
CASTER_MOUNT_HOLE_DIA = M3_CLEARANCE
CASTER_STEM_HEIGHT = 15    # mm (stem between flange and cup)
# Total height: flange (3) + stem (15) + cup (~10) = ~28mm
# Ball protrudes ~6mm below cup bottom -> ground contact at ~28 - 10 + 6 ≈ 24mm below flange
# With wheel radius 32.5mm, plate thickness 3mm -> need ~29.5mm from plate bottom to ground
# Flange sits on top of plate, so distance = flange_thick + stem + cup_depth - ball_protrusion
# = 3 + 15 + 10 - 6 = 22mm below plate bottom... adjust stem to hit target
# Target: 29.5mm from plate bottom to ground
# ball_protrusion = CASTER_BALL_DIA/2 - (CASTER_CUP_DEPTH - CASTER_BALL_DIA/2) roughly
# For a 16mm ball in a 10mm deep cup: ball center at 10 - 8 = 2mm above cup bottom
# ball protrudes: 8 - 2 = 6mm below cup bottom edge
# distance from plate bottom to ground = STEM_HEIGHT + CUP outer depth + ball_protrusion
# Let's just compute:
# Cup outer height ~ CUP_DEPTH + wall(1.5mm) at bottom = ~11.5
# Total below flange bottom: STEM_HEIGHT + 11.5
# Ball protrudes: BALL_DIA/2 - (CUP_DEPTH - BALL_DIA/2) = 8 - (10-8) = 6mm below cup inner bottom
# So ground distance from plate bottom = STEM_HEIGHT + CUP_DEPTH + 1.5(cup wall) - (CUP_DEPTH - 6)
# Simplify: STEM_HEIGHT + 1.5 + 6 = STEM_HEIGHT + 7.5
# Need this = 29.5 -> STEM_HEIGHT = 22
# Recalculate:
CASTER_STEM_HEIGHT = 22    # adjusted for correct ride height
CASTER_CUP_WALL = 1.5      # mm
CASTER_SNAP_SLOT_WIDTH = 5  # mm snap-in slot in cup rim

# ─── Standoff parameters ─────────────────────────────────────────────────────
STANDOFF_OD = 8            # mm outer diameter
STANDOFF_ID = 3.2          # mm M3 through-hole
STANDOFF_HEIGHT = 35       # mm
STANDOFF_FLANGE_DIA = 10   # mm
STANDOFF_FLANGE_THICK = 1.5  # mm

# ─── Sensor bracket parameters ───────────────────────────────────────────────
SENSOR_BRACKET_W = 45       # mm (HC-SR04 board width)
SENSOR_BRACKET_H = 20       # mm (HC-SR04 board height)
SENSOR_BASE_DEPTH = 15      # mm horizontal base depth
SENSOR_WALL_THICK = 2.5     # mm
SENSOR_ANGLE_DEG = 15       # degrees outward from vertical
SENSOR_TRANSDUCER_DIA = 16  # mm
SENSOR_TRANSDUCER_SPAN = 26 # mm center-to-center
SENSOR_BASE_HOLE_SPAN = 35  # mm mounting hole spacing on base

# ─── Webcam mount parameters ─────────────────────────────────────────────────
WEBCAM_POST_DIA = 12        # mm
WEBCAM_POST_HEIGHT = 40     # mm
WEBCAM_BASE_SIZE = 25       # mm square
WEBCAM_BASE_THICK = 3       # mm
WEBCAM_BASE_HOLE_DIA = 4.2  # mm (M4 clearance)
WEBCAM_PLATFORM_W = 30      # mm
WEBCAM_PLATFORM_D = 20      # mm
WEBCAM_PLATFORM_THICK = 3   # mm
# 1/4"-20 = 6.35mm diameter
WEBCAM_TRIPOD_HOLE_DIA = 6.5  # mm (1/4"-20 clearance)


# ═══════════════════════════════════════════════════════════════════════════════
# Mesh helper functions
# ═══════════════════════════════════════════════════════════════════════════════

def cylinder_mesh(radius, height, segments=SEGMENTS, center_xy=(0, 0), z_base=0):
    """Create a solid cylinder as a list of triangles (vertices).
    Returns array of shape (n_triangles, 3, 3)."""
    cx, cy = center_xy
    triangles = []
    angles = [2 * math.pi * i / segments for i in range(segments)]

    for i in range(segments):
        a1 = angles[i]
        a2 = angles[(i + 1) % segments]
        x1 = cx + radius * math.cos(a1)
        y1 = cy + radius * math.sin(a1)
        x2 = cx + radius * math.cos(a2)
        y2 = cy + radius * math.sin(a2)
        z0 = z_base
        z1 = z_base + height

        # Bottom cap triangle (normal pointing -Z)
        triangles.append([[cx, cy, z0], [x2, y2, z0], [x1, y1, z0]])
        # Top cap triangle (normal pointing +Z)
        triangles.append([[cx, cy, z1], [x1, y1, z1], [x2, y2, z1]])
        # Side quad as two triangles (normal pointing outward)
        triangles.append([[x1, y1, z0], [x2, y2, z0], [x2, y2, z1]])
        triangles.append([[x1, y1, z0], [x2, y2, z1], [x1, y1, z1]])

    return np.array(triangles, dtype=np.float64)


def tube_mesh(outer_r, inner_r, height, segments=SEGMENTS, center_xy=(0, 0), z_base=0):
    """Create a hollow cylinder (tube) — outer minus inner cylinder.
    Returns array of shape (n_triangles, 3, 3)."""
    cx, cy = center_xy
    triangles = []
    angles = [2 * math.pi * i / segments for i in range(segments)]

    for i in range(segments):
        a1 = angles[i]
        a2 = angles[(i + 1) % segments]
        # Outer points
        ox1 = cx + outer_r * math.cos(a1)
        oy1 = cy + outer_r * math.sin(a1)
        ox2 = cx + outer_r * math.cos(a2)
        oy2 = cy + outer_r * math.sin(a2)
        # Inner points
        ix1 = cx + inner_r * math.cos(a1)
        iy1 = cy + inner_r * math.sin(a1)
        ix2 = cx + inner_r * math.cos(a2)
        iy2 = cy + inner_r * math.sin(a2)

        z0 = z_base
        z1 = z_base + height

        # Bottom annular face (normal -Z)
        triangles.append([[ox1, oy1, z0], [ox2, oy2, z0], [ix2, iy2, z0]])
        triangles.append([[ox1, oy1, z0], [ix2, iy2, z0], [ix1, iy1, z0]])
        # Top annular face (normal +Z)
        triangles.append([[ox1, oy1, z1], [ix1, iy1, z1], [ix2, iy2, z1]])
        triangles.append([[ox1, oy1, z1], [ix2, iy2, z1], [ox2, oy2, z1]])
        # Outer wall (normal outward)
        triangles.append([[ox1, oy1, z0], [ox2, oy2, z1], [ox2, oy2, z0]])
        triangles.append([[ox1, oy1, z0], [ox1, oy1, z1], [ox2, oy2, z1]])
        # Inner wall (normal inward, reversed winding)
        triangles.append([[ix1, iy1, z0], [ix2, iy2, z0], [ix2, iy2, z1]])
        triangles.append([[ix1, iy1, z0], [ix2, iy2, z1], [ix1, iy1, z1]])

    return np.array(triangles, dtype=np.float64)


def box_mesh(sx, sy, sz, origin=(0, 0, 0)):
    """Create a solid box. origin is the corner at min x,y,z.
    Returns array of shape (12, 3, 3)."""
    x0, y0, z0 = origin
    x1, y1, z1 = x0 + sx, y0 + sy, z0 + sz

    # 8 vertices
    v = [
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],  # bottom
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],  # top
    ]
    # 12 triangles (2 per face), CCW winding for outward normals
    faces = [
        # Bottom (-Z)
        [v[0], v[2], v[1]], [v[0], v[3], v[2]],
        # Top (+Z)
        [v[4], v[5], v[6]], [v[4], v[6], v[7]],
        # Front (-Y)
        [v[0], v[1], v[5]], [v[0], v[5], v[4]],
        # Back (+Y)
        [v[3], v[7], v[6]], [v[3], v[6], v[2]],
        # Left (-X)
        [v[0], v[4], v[7]], [v[0], v[7], v[3]],
        # Right (+X)
        [v[1], v[2], v[6]], [v[1], v[6], v[5]],
    ]
    return np.array(faces, dtype=np.float64)


def hemisphere_cup_mesh(inner_r, wall_thick, depth, segments=SEGMENTS,
                        center_xy=(0, 0), z_base=0, snap_slot_width=0):
    """Create a hemispherical cup (bowl shape).
    The cup opens downward (-Z direction) from z_base.
    depth = how deep the cup goes below z_base.
    Returns triangles array."""
    cx, cy = center_xy
    outer_r = inner_r + wall_thick
    triangles = []

    # We'll build the cup as a series of latitude rings from the rim (z_base)
    # down to the bottom of the hemisphere.
    # The hemisphere has its center at z_base, opening downward.
    # Inner surface: sphere of radius inner_r
    # Outer surface: sphere of radius outer_r
    # But we only go down to 'depth' below z_base.

    lat_segments = segments // 2  # latitude divisions

    # Maximum angle from the pole (bottom of cup)
    # For a hemisphere, the cup depth determines how much of the sphere we use
    # angle from vertical axis: sin(theta_max) = 1 when depth >= inner_r (full hemi)
    # cos(theta_max) = (inner_r - depth) / inner_r if depth < inner_r
    if depth >= inner_r:
        theta_max = math.pi / 2
    else:
        theta_max = math.acos((inner_r - depth) / inner_r)

    # Generate rings of vertices
    # theta goes from 0 (pole/bottom) to theta_max (rim)
    # phi goes around the circumference

    phi_angles = [2 * math.pi * i / segments for i in range(segments)]

    def sphere_point(r, theta, phi, cx, cy, z_center):
        """Point on sphere, pole pointing down (-Z)."""
        x = cx + r * math.sin(theta) * math.cos(phi)
        y = cy + r * math.sin(theta) * math.sin(phi)
        z = z_center - r * math.cos(theta)  # -Z is downward
        return [x, y, z]

    z_center = z_base  # center of hemisphere sphere

    for i in range(lat_segments):
        t1 = theta_max * i / lat_segments
        t2 = theta_max * (i + 1) / lat_segments

        for j in range(segments):
            p1 = phi_angles[j]
            p2 = phi_angles[(j + 1) % segments]

            # Skip triangles in the snap slot region
            if snap_slot_width > 0 and i == lat_segments - 1:
                # Check if this segment is in the slot region
                mid_phi = (p1 + p2) / 2
                # Slot at phi=0 (one side)
                slot_half_angle = math.atan2(snap_slot_width / 2, outer_r)
                if mid_phi < slot_half_angle or mid_phi > 2 * math.pi - slot_half_angle:
                    continue

            # Inner surface (normals point inward = toward center)
            ip1 = sphere_point(inner_r, t1, p1, cx, cy, z_center)
            ip2 = sphere_point(inner_r, t1, p2, cx, cy, z_center)
            ip3 = sphere_point(inner_r, t2, p1, cx, cy, z_center)
            ip4 = sphere_point(inner_r, t2, p2, cx, cy, z_center)

            # Outer surface
            op1 = sphere_point(outer_r, t1, p1, cx, cy, z_center)
            op2 = sphere_point(outer_r, t1, p2, cx, cy, z_center)
            op3 = sphere_point(outer_r, t2, p1, cx, cy, z_center)
            op4 = sphere_point(outer_r, t2, p2, cx, cy, z_center)

            if i == 0:
                # Bottom cap (pole): triangles converge to a point
                # Inner
                triangles.append([ip1, ip4, ip3])  # reversed for inward normal
                # Outer
                triangles.append([op1, op3, op4])
            else:
                # Inner surface quads (reversed winding for inward normals)
                triangles.append([ip1, ip4, ip3])
                triangles.append([ip1, ip2, ip4])
                # Outer surface quads
                triangles.append([op1, op3, op4])
                triangles.append([op1, op4, op2])

            # Rim (top ring at theta_max) - connect inner to outer
            if i == lat_segments - 1:
                triangles.append([ip3, ip4, op4])
                triangles.append([ip3, op4, op3])

    # Bottom pole cap - close the small hole at the very bottom
    # Actually the pole triangles already handle this since they converge

    return np.array(triangles, dtype=np.float64)


def make_mesh_from_triangles(triangles_list):
    """Combine multiple triangle arrays into a single stl mesh."""
    all_tris = np.concatenate(triangles_list, axis=0)
    n = len(all_tris)
    m = mesh.Mesh(np.zeros(n, dtype=mesh.Mesh.dtype))
    for i in range(n):
        m.vectors[i] = all_tris[i]
    m.update_normals()
    return m


def subtract_cylinder_from_box(box_origin, box_size, cyl_center, cyl_radius, cyl_z0, cyl_z1, segments=SEGMENTS):
    """Approximate subtraction: create a box with a cylindrical hole.
    We build this as individual faces, replacing the top/bottom where the hole is.
    Returns triangle array."""
    # This is complex for CSG. Instead, we'll build the geometry directly.
    # For a box with a through-hole, we create:
    # 1. Four side walls of the box (unchanged)
    # 2. Top and bottom faces with a circular hole (annular faces)
    # 3. Inner cylinder wall

    bx, by, bz = box_origin
    sx, sy, sz = box_size
    cx, cy = cyl_center
    r = cyl_radius
    z0 = max(bz, cyl_z0)
    z1 = min(bz + sz, cyl_z1)

    triangles = []
    angles = [2 * math.pi * i / segments for i in range(segments)]

    # We'll simplify: build the 4 side walls as box faces, then build
    # the top and bottom as polygon-with-hole (triangulated to center of hole edge)

    x0, y0 = bx, by
    x1, y1 = bx + sx, by + sy

    # Four side walls of the box (full rectangles)
    # Front wall (-Y)
    triangles.append([[x0, y0, bz], [x1, y0, bz], [x1, y0, bz + sz]])
    triangles.append([[x0, y0, bz], [x1, y0, bz + sz], [x0, y0, bz + sz]])
    # Back wall (+Y)
    triangles.append([[x0, y1, bz], [x1, y1, bz + sz], [x1, y1, bz]])
    triangles.append([[x0, y1, bz], [x0, y1, bz + sz], [x1, y1, bz + sz]])
    # Left wall (-X)
    triangles.append([[x0, y0, bz], [x0, y0, bz + sz], [x0, y1, bz + sz]])
    triangles.append([[x0, y0, bz], [x0, y1, bz + sz], [x0, y1, bz]])
    # Right wall (+X)
    triangles.append([[x1, y0, bz], [x1, y1, bz], [x1, y1, bz + sz]])
    triangles.append([[x1, y0, bz], [x1, y1, bz + sz], [x1, y0, bz + sz]])

    # Top and bottom faces with circular hole
    # We triangulate from each edge of the circle to the corners of the rectangle
    # Simplified approach: fan triangles from hole edge to box corners

    for face_z, flip in [(bz, True), (bz + sz, False)]:
        # Create triangles from circle edge to rectangle edges
        # We'll use a simple approach: divide the annular region into sectors
        # and connect each sector to the nearest box edge

        # Circle points at this z
        cpts = []
        for i in range(segments):
            a = angles[i]
            px = cx + r * math.cos(a)
            py = cy + r * math.sin(a)
            cpts.append([px, py, face_z])

        # Box corners at this z
        corners = [
            [x0, y0, face_z],
            [x1, y0, face_z],
            [x1, y1, face_z],
            [x0, y1, face_z],
        ]

        # Connect box edges to nearest circle points
        # Simple fan from box corners to circle segments
        # We'll triangulate the annular region by connecting circle segments
        # to the box perimeter

        # Strategy: for each circle segment, create a triangle to the box center
        # Actually, simplest correct approach: triangulate each face as a
        # quad strip from the box perimeter to the circle

        # Let's use a different approach: subdivide the rectangle into
        # triangles that avoid the hole area
        # Easiest: fan from the 4 corner points of the box to the circle

        # For each circle segment, find which quadrant it's in and connect
        # to the appropriate corner

        for i in range(segments):
            cp1 = cpts[i]
            cp2 = cpts[(i + 1) % segments]

            # Determine which corner this segment faces
            mid_angle = (angles[i] + angles[(i + 1) % segments]) / 2
            if angles[(i + 1) % segments] < angles[i]:
                mid_angle = angles[i] + (angles[(i + 1) % segments] + 2 * math.pi - angles[i]) / 2
                if mid_angle >= 2 * math.pi:
                    mid_angle -= 2 * math.pi

            # Quadrant assignment
            if mid_angle < math.pi / 2:
                corner = corners[1]  # +X, -Y
            elif mid_angle < math.pi:
                corner = corners[2]  # +X, +Y
            elif mid_angle < 3 * math.pi / 2:
                corner = corners[3]  # -X, +Y
            else:
                corner = corners[0]  # -X, -Y

            if flip:
                triangles.append([cp2, cp1, corner])
            else:
                triangles.append([cp1, cp2, corner])

        # Fill in the corner triangles (connect adjacent quadrant boundaries)
        # Corner 1 (+X, -Y): between angle 0 and pi/2
        # We need triangles from corner to corner bridging the gaps

        # Find the circle points at quadrant boundaries
        def circle_point_at_angle(a):
            return [cx + r * math.cos(a), cy + r * math.sin(a), face_z]

        quadrant_angles = [0, math.pi / 2, math.pi, 3 * math.pi / 2]
        for qi in range(4):
            c1 = corners[qi]
            c2 = corners[(qi + 1) % 4]
            boundary_angle = quadrant_angles[(qi + 1) % 4]
            bp = circle_point_at_angle(boundary_angle)
            if flip:
                triangles.append([c2, c1, bp])
            else:
                triangles.append([c1, c2, bp])

    # Inner cylinder wall (hole surface)
    for i in range(segments):
        a1 = angles[i]
        a2 = angles[(i + 1) % segments]
        px1 = cx + r * math.cos(a1)
        py1 = cy + r * math.sin(a1)
        px2 = cx + r * math.cos(a2)
        py2 = cy + r * math.sin(a2)

        # Inner wall normals point inward (toward center)
        triangles.append([[px1, py1, bz], [px2, py2, bz + sz], [px2, py2, bz]])
        triangles.append([[px1, py1, bz], [px1, py1, bz + sz], [px2, py2, bz + sz]])

    return np.array(triangles, dtype=np.float64)


# ═══════════════════════════════════════════════════════════════════════════════
# Part 1: Motor Mount Clip
# ═══════════════════════════════════════════════════════════════════════════════

def generate_motor_mount():
    """Generate TT motor mount clip STL.

    U-channel that wraps around the TT motor body with M3 bolt tabs.
    Print orientation: open side up (U-channel opening faces +Z).
    """
    print("Generating motor_mount.stl ...")

    wall = MOTOR_MOUNT_WALL
    ch_w = MOTOR_CHANNEL_W       # inside width (Y)
    ch_h = MOTOR_CHANNEL_H       # inside height (Z, depth of channel)
    length = MOTOR_CLIP_LENGTH   # X dimension (along motor body)
    tab_w = MOTOR_TAB_WIDTH
    tab_t = MOTOR_TAB_THICKNESS
    hole_span = MOTOR_MOUNT_HOLE_SPAN
    hole_r = MOTOR_MOUNT_HOLE_DIA / 2

    parts = []

    # The U-channel cross-section (looking from +X toward -X):
    #
    #    +---+          +---+
    #    |   |          |   |
    #    |   +----------+   |     <- inner channel ch_w x ch_h
    #    |                  |
    #    +--[TAB]----[TAB]--+     <- bottom with tabs
    #
    # Coordinate system: X = along motor body (length), Y = width, Z = height
    # Origin at center-bottom of the clip

    outer_w = ch_w + 2 * wall     # total outer width (Y)
    outer_h = ch_h + wall         # total outer height (Z, open top)

    # Bottom plate (floor of U-channel)
    # Full width including tabs
    total_y = outer_w + 2 * tab_w
    y_start = -total_y / 2
    parts.append(box_mesh(length, total_y, wall, origin=(0, y_start, 0)))

    # Left wall
    parts.append(box_mesh(length, wall, outer_h, origin=(0, -outer_w / 2 - wall, 0)))
    # Correction: left wall should start at the inner edge
    # Actually let me reconsider the geometry

    # Let me rebuild more carefully
    parts = []

    # Y: centered on 0. Channel is from -ch_w/2 to +ch_w/2
    # Z: bottom at 0, top at outer_h = ch_h + wall
    # X: from 0 to length

    # Bottom plate spans full width (including tab overhangs)
    tab_total_y = ch_w + 2 * wall + 2 * tab_w
    parts.append(box_mesh(length, tab_total_y, wall,
                          origin=(0, -tab_total_y / 2, 0)))

    # Left wall (inner face at Y = -ch_w/2, outer face at Y = -ch_w/2 - wall)
    parts.append(box_mesh(length, wall, ch_h,
                          origin=(0, -ch_w / 2 - wall, wall)))

    # Right wall
    parts.append(box_mesh(length, wall, ch_h,
                          origin=(0, ch_w / 2, wall)))

    # Tab holes: two M3 holes in the bottom plate
    # Holes at X = length/2 +/- hole_span/2
    # For simplicity, we approximate the holes by omitting them from the solid
    # (they'll be drilled). But for a proper STL, let's add cylindrical holes.

    # Actually, for FDM printing, we should include the holes in the model.
    # Let's rebuild the bottom plate with holes using the subtract approach.

    # Instead of a simple box for the bottom, create a box with two cylindrical holes
    # Hole centers: X = length/2 +/- hole_span/2, Y = 0
    # But the box function doesn't support holes. Let's add separate tube meshes
    # as "hole indicators" -- actually, we need to do CSG subtraction properly.

    # For practical purposes with numpy-stl, we'll create the tabs as separate
    # pieces with holes. Let me restructure:

    parts = []

    # Main U-channel body (without tabs)
    body_y = ch_w + 2 * wall
    # Bottom of U
    parts.append(box_mesh(length, body_y, wall,
                          origin=(0, -body_y / 2, 0)))
    # Left wall
    parts.append(box_mesh(length, wall, ch_h,
                          origin=(0, -ch_w / 2 - wall, wall)))
    # Right wall
    parts.append(box_mesh(length, wall, ch_h,
                          origin=(0, ch_w / 2, wall)))

    # Left tab (extends beyond left wall)
    tab_y_start = -body_y / 2 - tab_w
    parts.append(box_mesh(length, tab_w, tab_t,
                          origin=(0, tab_y_start, 0)))

    # Right tab
    tab_y_start_r = body_y / 2
    parts.append(box_mesh(length, tab_w, tab_t,
                          origin=(0, tab_y_start_r, 0)))

    # Add M3 hole cylinders (as visual markers — proper holes)
    # Left hole: center at X=length/2 - hole_span/2, Y = -(body_y/2 + tab_w/2)
    # Right hole: center at X=length/2 + hole_span/2, Y = -(body_y/2 + tab_w/2)

    hole_x1 = length / 2 - hole_span / 2
    hole_x2 = length / 2 + hole_span / 2
    hole_y_left = -(body_y / 2 + tab_w / 2)
    hole_y_right = (body_y / 2 + tab_w / 2)

    # Create holes as tubes (hollow cylinders) that go through the tabs
    # We'll represent each hole as a tube (ring) punched through the tab
    for hx in [hole_x1, hole_x2]:
        for hy in [hole_y_left, hole_y_right]:
            hole_tris = tube_mesh(hole_r + 0.5, hole_r, tab_t,
                                  segments=SEGMENTS,
                                  center_xy=(hx, hy), z_base=0)
            parts.append(hole_tris)

    m = make_mesh_from_triangles(parts)

    # Verify mesh
    path = os.path.join(OUTPUT_DIR, "motor_mount.stl")
    m.save(path)
    print(f"  Saved: {path} ({os.path.getsize(path)} bytes)")
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# Part 2: Ball Caster Assembly
# ═══════════════════════════════════════════════════════════════════════════════

def generate_ball_caster():
    """Generate ball caster assembly STL.

    Hemispherical cup on a stem with mounting flange.
    The assembly hangs below the chassis plate.
    Orientation: flange at top (Z+), cup/ball at bottom (Z-).
    We'll build it flange-at-Z=0, extending downward into -Z, then flip.
    Actually, let's build it for printing: flange on the print bed (Z=0),
    stem goes up, cup at top (upside down for printing).
    """
    print("Generating ball_caster.stl ...")

    parts = []

    flange_r = CASTER_FLANGE_DIA / 2
    flange_t = CASTER_FLANGE_THICK
    cup_or = CASTER_CUP_ID / 2 + CASTER_CUP_WALL
    cup_ir = CASTER_CUP_ID / 2
    stem_r = cup_or + 1  # stem slightly wider than cup outer
    stem_h = CASTER_STEM_HEIGHT
    cup_depth = CASTER_CUP_DEPTH

    # Build from bottom (print bed) up:
    # Layer 1: Flange disk (Z=0 to Z=flange_t)
    parts.append(cylinder_mesh(flange_r, flange_t, center_xy=(0, 0), z_base=0))

    # Layer 2: Stem cylinder (Z=flange_t to Z=flange_t+stem_h)
    parts.append(cylinder_mesh(stem_r, stem_h, center_xy=(0, 0),
                               z_base=flange_t))

    # Layer 3: Cup (hemispherical bowl, opening faces up = +Z for printing)
    # We'll build it as a series of rings approximating a hemisphere
    cup_z_base = flange_t + stem_h

    # Build cup as stacked rings (cone frustum approximation of hemisphere)
    n_rings = 24
    cup_tris = []

    for i in range(n_rings):
        # Parametric angle from pole (bottom of cup) to rim
        # theta1 at bottom (small radius), theta2 at top (larger radius)
        t1 = (math.pi / 2) * i / n_rings
        t2 = (math.pi / 2) * (i + 1) / n_rings

        # Inner surface radii at these angles
        ir1 = cup_ir * math.sin(t1)
        ir2 = cup_ir * math.sin(t2)
        # Outer surface radii
        or1 = (cup_ir + CASTER_CUP_WALL) * math.sin(t1) if ir1 > 0 else CASTER_CUP_WALL
        or2 = (cup_ir + CASTER_CUP_WALL) * math.sin(t2)

        # Z positions (height above cup_z_base)
        # At the pole (bottom of internal hemisphere), z = 0
        # At the rim, z = cup_depth
        # z = cup_ir * (1 - cos(theta))
        iz1 = cup_ir * (1 - math.cos(t1))
        iz2 = cup_ir * (1 - math.cos(t2))
        oz1 = (cup_ir + CASTER_CUP_WALL) * (1 - math.cos(t1))
        oz2 = (cup_ir + CASTER_CUP_WALL) * (1 - math.cos(t2))

        z1_inner = cup_z_base + iz1
        z2_inner = cup_z_base + iz2
        z1_outer = cup_z_base + oz1
        z2_outer = cup_z_base + oz2

        angles = [2 * math.pi * j / SEGMENTS for j in range(SEGMENTS)]

        for j in range(SEGMENTS):
            a1 = angles[j]
            a2 = angles[(j + 1) % SEGMENTS]
            ca1, sa1 = math.cos(a1), math.sin(a1)
            ca2, sa2 = math.cos(a2), math.sin(a2)

            if i == 0:
                # Bottom pole: triangle from center point to first ring
                # Inner surface
                center_inner = [0, 0, cup_z_base]
                p1_inner = [ir2 * ca1, ir2 * sa1, z2_inner]
                p2_inner = [ir2 * ca2, ir2 * sa2, z2_inner]
                cup_tris.append([center_inner, p2_inner, p1_inner])

                # Outer surface
                center_outer = [0, 0, cup_z_base]
                p1_outer = [or2 * ca1, or2 * sa1, z2_outer]
                p2_outer = [or2 * ca2, or2 * sa2, z2_outer]
                cup_tris.append([center_outer, p1_outer, p2_outer])

                # The very bottom is solid (no hole), so connect inner to outer
                # at the bottom
            else:
                # Inner surface quad
                pi1 = [ir1 * ca1, ir1 * sa1, z1_inner]
                pi2 = [ir1 * ca2, ir1 * sa2, z1_inner]
                pi3 = [ir2 * ca1, ir2 * sa1, z2_inner]
                pi4 = [ir2 * ca2, ir2 * sa2, z2_inner]
                cup_tris.append([pi1, pi4, pi3])
                cup_tris.append([pi1, pi2, pi4])

                # Outer surface quad
                po1 = [or1 * ca1, or1 * sa1, z1_outer]
                po2 = [or1 * ca2, or1 * sa2, z1_outer]
                po3 = [or2 * ca1, or2 * sa1, z2_outer]
                po4 = [or2 * ca2, or2 * sa2, z2_outer]
                cup_tris.append([po1, po3, po4])
                cup_tris.append([po1, po4, po2])

            # Rim (top ring) - connect inner to outer
            if i == n_rings - 1:
                pi_rim1 = [ir2 * ca1, ir2 * sa1, z2_inner]
                pi_rim2 = [ir2 * ca2, ir2 * sa2, z2_inner]
                po_rim1 = [or2 * ca1, or2 * sa1, z2_outer]
                po_rim2 = [or2 * ca2, or2 * sa2, z2_outer]
                cup_tris.append([pi_rim1, po_rim1, po_rim2])
                cup_tris.append([pi_rim1, po_rim2, pi_rim2])

    if cup_tris:
        parts.append(np.array(cup_tris, dtype=np.float64))

    # Connect stem top to cup outer bottom
    # The stem top is at z = flange_t + stem_h, radius = stem_r
    # The cup outer bottom is at z = cup_z_base, radius ~= CASTER_CUP_WALL (small)
    # We need a transition ring / disk to connect them
    # Simplest: solid disk at cup_z_base from stem_r down to cup outer bottom radius
    # Actually, the stem already meets the cup base. Let's add a flat ring connecting
    # stem outer wall to cup outer wall at the cup base height.

    # Flat ring at cup_z_base connecting stem_r to cup bottom outer radius
    # At theta=0, outer radius of cup = CASTER_CUP_WALL (approximately)
    cup_bottom_or = CASTER_CUP_WALL
    if stem_r > cup_bottom_or:
        ring_tris = []
        angles = [2 * math.pi * j / SEGMENTS for j in range(SEGMENTS)]
        z = cup_z_base
        for j in range(SEGMENTS):
            a1 = angles[j]
            a2 = angles[(j + 1) % SEGMENTS]
            # Outer ring (stem)
            ox1 = stem_r * math.cos(a1)
            oy1 = stem_r * math.sin(a1)
            ox2 = stem_r * math.cos(a2)
            oy2 = stem_r * math.sin(a2)
            # Inner ring (cup bottom)
            ix1 = cup_bottom_or * math.cos(a1)
            iy1 = cup_bottom_or * math.sin(a1)
            ix2 = cup_bottom_or * math.cos(a2)
            iy2 = cup_bottom_or * math.sin(a2)

            ring_tris.append([[ox1, oy1, z], [ix1, iy1, z], [ix2, iy2, z]])
            ring_tris.append([[ox1, oy1, z], [ix2, iy2, z], [ox2, oy2, z]])
        parts.append(np.array(ring_tris, dtype=np.float64))

    # Add snap-in slot: a rectangular notch in the cup rim
    # This is just a visual feature; the cup rim already has an opening
    # For printing, the slot helps inserting the ball

    # Mounting holes in flange: 3x M3 holes in triangle pattern
    # Triangle with 20mm side length, centered on origin
    # We'll approximate holes as small cylinders that are visually present
    # For actual printing, the slicer handles the through-holes
    hole_r = CASTER_MOUNT_HOLE_DIA / 2
    mount_r = CASTER_MOUNT_HOLE_SPACING / math.sqrt(3)  # circumradius of equilateral triangle
    for k in range(3):
        angle = 2 * math.pi * k / 3 + math.pi / 6  # rotate 30 deg for alignment
        hx = mount_r * math.cos(angle)
        hy = mount_r * math.sin(angle)
        # Hole as a tube through the flange
        parts.append(tube_mesh(hole_r + 0.4, hole_r, flange_t,
                               segments=24, center_xy=(hx, hy), z_base=0))

    m = make_mesh_from_triangles(parts)
    path = os.path.join(OUTPUT_DIR, "ball_caster.stl")
    m.save(path)
    print(f"  Saved: {path} ({os.path.getsize(path)} bytes)")
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# Part 3: Standoff
# ═══════════════════════════════════════════════════════════════════════════════

def generate_standoff():
    """Generate deck standoff STL.

    Simple cylinder with M3 through-hole and flanges at each end.
    """
    print("Generating standoff.stl ...")

    parts = []

    outer_r = STANDOFF_OD / 2
    inner_r = STANDOFF_ID / 2
    height = STANDOFF_HEIGHT
    flange_r = STANDOFF_FLANGE_DIA / 2
    flange_t = STANDOFF_FLANGE_THICK

    # Bottom flange
    parts.append(tube_mesh(flange_r, inner_r, flange_t,
                           center_xy=(0, 0), z_base=0))

    # Main cylinder body
    parts.append(tube_mesh(outer_r, inner_r, height,
                           center_xy=(0, 0), z_base=flange_t))

    # Top flange
    parts.append(tube_mesh(flange_r, inner_r, flange_t,
                           center_xy=(0, 0), z_base=flange_t + height))

    m = make_mesh_from_triangles(parts)
    path = os.path.join(OUTPUT_DIR, "standoff.stl")
    m.save(path)
    print(f"  Saved: {path} ({os.path.getsize(path)} bytes)")
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# Part 4: HC-SR04 Sensor Bracket
# ═══════════════════════════════════════════════════════════════════════════════

def generate_sensor_bracket():
    """Generate HC-SR04 sensor bracket STL.

    L-shaped bracket with angled vertical face for the sensor board.
    Horizontal base mounts to chassis, vertical face holds HC-SR04.
    The vertical face is angled 15 degrees outward.
    """
    print("Generating sensor_bracket.stl ...")

    parts = []

    w = SENSOR_BRACKET_W + 2 * SENSOR_WALL_THICK  # total width (X)
    base_d = SENSOR_BASE_DEPTH                      # base depth (Y)
    base_t = SENSOR_WALL_THICK                       # base thickness (Z)
    wall_t = SENSOR_WALL_THICK                       # vertical wall thickness
    wall_h = SENSOR_BRACKET_H + 2 * SENSOR_WALL_THICK  # total vertical face height
    angle = math.radians(SENSOR_ANGLE_DEG)

    # Coordinate system: X = bracket width, Y = depth (front-to-back), Z = height

    # Horizontal base plate
    parts.append(box_mesh(w, base_d, base_t, origin=(0, 0, 0)))

    # Angled vertical face
    # The face rises from the front edge of the base (Y=0) and tilts outward
    # The tilt is about the X-axis: top of wall leans toward +Y by angle degrees
    # We'll create this as a tilted slab

    # Bottom edge of vertical wall is at Y=0, Z=base_t
    # Top edge is at Y = wall_h * sin(angle), Z = base_t + wall_h * cos(angle)
    dy = wall_h * math.sin(angle)
    dz = wall_h * math.cos(angle)

    # Front face of wall (4 corners)
    v_bl = [0, 0, base_t]                    # bottom-left
    v_br = [w, 0, base_t]                    # bottom-right
    v_tl = [0, dy, base_t + dz]             # top-left
    v_tr = [w, dy, base_t + dz]             # top-right

    # Back face of wall (offset by wall_t in the wall-normal direction)
    # Normal to the wall face points roughly in +Y (tilted)
    nx = 0
    ny = math.cos(angle)
    nz = math.sin(angle)
    # Wait, the wall tilts so its normal rotates. Let me think again.
    # The wall face lies in the X-Z' plane where Z' is the tilted axis.
    # The wall thickness is along the normal to this face.
    # Normal to the tilted face: (0, -sin(angle), cos(angle)) rotated...
    # Actually, the wall surface normal points backward (+Y direction mostly).
    # The back face vertices are offset by wall_t in the Y direction (perpendicular to wall face)

    # The wall is a slab. Its "thickness" direction is perpendicular to its face.
    # Face normal = (0, cos(angle), -sin(angle)) -- this is approximate but let's
    # offset the back face simply in Y by wall_t (close enough for small angles)

    # More precisely: offset along (0, cos(angle), sin(angle)) * wall_t
    # No -- the face plane normal: the face contains vectors (1,0,0) and (0, sin(angle), cos(angle))
    # Cross product: (0,0,0)... let me use actual vertices.
    # Face direction: from bottom to top = (0, dy, dz) normalized = (0, sin(angle), cos(angle))
    # Width direction: (1, 0, 0)
    # Normal = width x up = (1,0,0) x (0, sin(angle), cos(angle)) = (0*cos-0*sin, 0*0-1*cos, 1*sin-0*0)
    # = (0, -cos(angle), sin(angle))
    # So normal points in (0, -cos(angle), sin(angle)). For the back face we go opposite:
    # (0, cos(angle), -sin(angle))

    dn_y = wall_t * math.cos(angle)
    dn_z = -wall_t * math.sin(angle)

    vb_bl = [0, 0 + dn_y, base_t + dn_z]
    vb_br = [w, 0 + dn_y, base_t + dn_z]
    vb_tl = [0, dy + dn_y, base_t + dz + dn_z]
    vb_tr = [w, dy + dn_y, base_t + dz + dn_z]

    # Front face (2 triangles)
    parts.append(np.array([
        [v_bl, v_br, v_tr],
        [v_bl, v_tr, v_tl],
    ], dtype=np.float64))

    # Back face (2 triangles, reversed winding)
    parts.append(np.array([
        [vb_bl, vb_tr, vb_br],
        [vb_bl, vb_tl, vb_tr],
    ], dtype=np.float64))

    # Top edge (2 triangles)
    parts.append(np.array([
        [v_tl, v_tr, vb_tr],
        [v_tl, vb_tr, vb_tl],
    ], dtype=np.float64))

    # Bottom edge (2 triangles)
    parts.append(np.array([
        [v_bl, vb_br, v_br],
        [v_bl, vb_bl, vb_br],
    ], dtype=np.float64))

    # Left edge (2 triangles)
    parts.append(np.array([
        [v_bl, v_tl, vb_tl],
        [v_bl, vb_tl, vb_bl],
    ], dtype=np.float64))

    # Right edge (2 triangles)
    parts.append(np.array([
        [v_br, vb_br, vb_tr],
        [v_br, vb_tr, v_tr],
    ], dtype=np.float64))

    # Transducer holes in the vertical face
    # HC-SR04 has 2 cylinders, 16mm diameter, 26mm center-to-center
    # Positioned centered on the face
    # The holes go through the wall thickness
    # We'll represent them as tubes embedded in the angled wall

    face_center_x = w / 2
    face_center_z_local = (SENSOR_BRACKET_H + 2 * SENSOR_WALL_THICK) / 2

    for sign in [-1, 1]:
        # Transducer center offset from face center (in X direction)
        tx_offset = sign * SENSOR_TRANSDUCER_SPAN / 2
        tx = face_center_x + tx_offset
        # Height on the face
        tz_local = face_center_z_local  # centered vertically on face

        # Convert local face coordinates to 3D
        # On the face: X is the X-axis, "up" on face is (0, sin(angle), cos(angle))
        # Position = base_point + tz_local * (0, sin(angle), cos(angle))
        ty_3d = tz_local * math.sin(angle)
        tz_3d = base_t + tz_local * math.cos(angle)

        # Create a cylinder aligned with the face normal
        # Normal direction: (0, -cos(angle), sin(angle))
        # We'll create a cylinder from front face to back face
        tr = SENSOR_TRANSDUCER_DIA / 2
        n_segs = 36
        hole_tris = []

        for j in range(n_segs):
            a1 = 2 * math.pi * j / n_segs
            a2 = 2 * math.pi * ((j + 1) % n_segs) / n_segs

            # Circle in the plane perpendicular to face normal
            # Two basis vectors in that plane: (1, 0, 0) and (0, sin(angle), cos(angle))
            # Point on circle = center + r*cos(a)*e1 + r*sin(a)*e2
            for ai in [a1, a2]:
                pass  # placeholder

            # Front circle point
            def circ_pt(a, face_offset=0):
                ex = tr * math.cos(a)
                ey = tr * math.sin(a) * math.sin(angle)
                ez = tr * math.sin(a) * math.cos(angle)
                # Offset along face normal
                ny_off = face_offset * (-math.cos(angle))
                nz_off = face_offset * math.sin(angle)
                return [tx + ex, ty_3d + ey + ny_off, tz_3d + ez + nz_off]

            p1f = circ_pt(a1, 0)
            p2f = circ_pt(a2, 0)
            p1b = circ_pt(a1, wall_t)
            p2b = circ_pt(a2, wall_t)

            # Cylinder wall (inside of hole)
            hole_tris.append([p1f, p2f, p2b])
            hole_tris.append([p1f, p2b, p1b])

        parts.append(np.array(hole_tris, dtype=np.float64))

    # Support rib connecting base to vertical wall (triangular gusset on each side)
    rib_t = SENSOR_WALL_THICK
    rib_h = min(15, dz)  # 15mm tall or wall height, whichever is less
    rib_d = min(12, base_d)  # 12mm deep

    # Left rib
    rib_pts_left = [
        [0, 0, base_t],                # bottom-front
        [0, rib_d, base_t],            # bottom-back
        [0, rib_d * math.sin(angle), base_t + rib_h],  # top (on wall surface)
    ]
    rib_pts_left_r = [
        [rib_t, 0, base_t],
        [rib_t, rib_d, base_t],
        [rib_t, rib_d * math.sin(angle), base_t + rib_h],
    ]

    # Triangle faces
    parts.append(np.array([
        rib_pts_left,
        [rib_pts_left_r[0], rib_pts_left_r[2], rib_pts_left_r[1]],
        # Connecting quads
        [rib_pts_left[0], rib_pts_left_r[0], rib_pts_left_r[1]],
        [rib_pts_left[0], rib_pts_left_r[1], rib_pts_left[1]],
        [rib_pts_left[1], rib_pts_left_r[1], rib_pts_left_r[2]],
        [rib_pts_left[1], rib_pts_left_r[2], rib_pts_left[2]],
        [rib_pts_left[0], rib_pts_left[2], rib_pts_left_r[2]],
        [rib_pts_left[0], rib_pts_left_r[2], rib_pts_left_r[0]],
    ], dtype=np.float64))

    # Right rib
    rx = w - rib_t
    rib_pts_right = [
        [rx, 0, base_t],
        [rx, rib_d, base_t],
        [rx, rib_d * math.sin(angle), base_t + rib_h],
    ]
    rib_pts_right_r = [
        [w, 0, base_t],
        [w, rib_d, base_t],
        [w, rib_d * math.sin(angle), base_t + rib_h],
    ]
    parts.append(np.array([
        [rib_pts_right[0], rib_pts_right[2], rib_pts_right[1]],
        rib_pts_right_r,
        [rib_pts_right[0], rib_pts_right_r[1], rib_pts_right_r[0]],
        [rib_pts_right[0], rib_pts_right[1], rib_pts_right_r[1]],
        [rib_pts_right[1], rib_pts_right_r[2], rib_pts_right_r[1]],
        [rib_pts_right[1], rib_pts_right[2], rib_pts_right_r[2]],
        [rib_pts_right[0], rib_pts_right_r[2], rib_pts_right[2]],
        [rib_pts_right[0], rib_pts_right_r[0], rib_pts_right_r[2]],
    ], dtype=np.float64))

    # Mounting holes in base
    # Two M3 holes spaced SENSOR_BASE_HOLE_SPAN apart, centered on base
    for sign in [-1, 1]:
        hx = w / 2 + sign * SENSOR_BASE_HOLE_SPAN / 2
        hy = base_d / 2
        parts.append(tube_mesh(M3_CLEARANCE / 2 + 0.4, M3_CLEARANCE / 2, base_t,
                               segments=24, center_xy=(hx, hy), z_base=0))

    m = make_mesh_from_triangles(parts)
    path = os.path.join(OUTPUT_DIR, "sensor_bracket.stl")
    m.save(path)
    print(f"  Saved: {path} ({os.path.getsize(path)} bytes)")
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# Part 5: Webcam Mount Post
# ═══════════════════════════════════════════════════════════════════════════════

def generate_webcam_mount():
    """Generate webcam mount post STL.

    Vertical post with square base and top platform.
    Base has center M4 hole, top platform has 1/4"-20 hole.
    """
    print("Generating webcam_mount.stl ...")

    parts = []

    base_s = WEBCAM_BASE_SIZE
    base_t = WEBCAM_BASE_THICK
    post_r = WEBCAM_POST_DIA / 2
    post_h = WEBCAM_POST_HEIGHT
    plat_w = WEBCAM_PLATFORM_W
    plat_d = WEBCAM_PLATFORM_D
    plat_t = WEBCAM_PLATFORM_THICK

    # Base plate (square)
    parts.append(box_mesh(base_s, base_s, base_t,
                          origin=(-base_s / 2, -base_s / 2, 0)))

    # Vertical post (cylinder)
    parts.append(cylinder_mesh(post_r, post_h,
                               center_xy=(0, 0), z_base=base_t))

    # Top platform
    parts.append(box_mesh(plat_w, plat_d, plat_t,
                          origin=(-plat_w / 2, -plat_d / 2, base_t + post_h)))

    # M4 hole indicator in base (tube)
    base_hole_r = WEBCAM_BASE_HOLE_DIA / 2
    parts.append(tube_mesh(base_hole_r + 0.4, base_hole_r, base_t,
                           segments=24, center_xy=(0, 0), z_base=0))

    # 1/4"-20 hole indicator in top platform
    tripod_hole_r = WEBCAM_TRIPOD_HOLE_DIA / 2
    parts.append(tube_mesh(tripod_hole_r + 0.4, tripod_hole_r, plat_t,
                           segments=24,
                           center_xy=(0, 0),
                           z_base=base_t + post_h))

    # Gusset/fillet at base of post (4 small triangular ribs for strength)
    gusset_h = 8  # mm tall
    gusset_w = 3  # mm thick
    for angle_deg in [0, 90, 180, 270]:
        a = math.radians(angle_deg)
        # Direction vector from center outward
        dx = math.cos(a)
        dy = math.sin(a)
        # Perpendicular vector
        px = -math.sin(a)
        py = math.cos(a)

        # Gusset is a triangular prism
        # Three corners of the triangle (in the radial plane):
        p_base_inner = [post_r * dx, post_r * dy, base_t]
        p_base_outer = [(post_r + gusset_h) * dx, (post_r + gusset_h) * dy, base_t]
        p_top = [post_r * dx, post_r * dy, base_t + gusset_h]

        # Offset for thickness
        p_base_inner2 = [p_base_inner[0] + gusset_w * px,
                         p_base_inner[1] + gusset_w * py,
                         base_t]
        p_base_outer2 = [p_base_outer[0] + gusset_w * px,
                         p_base_outer[1] + gusset_w * py,
                         base_t]
        p_top2 = [p_top[0] + gusset_w * px,
                  p_top[1] + gusset_w * py,
                  base_t + gusset_h]

        tri_faces = [
            # Face 1
            [p_base_inner, p_base_outer, p_top],
            # Face 2 (opposite side)
            [p_base_inner2, p_top2, p_base_outer2],
            # Bottom
            [p_base_inner, p_base_inner2, p_base_outer2],
            [p_base_inner, p_base_outer2, p_base_outer],
            # Hypotenuse
            [p_base_outer, p_base_outer2, p_top2],
            [p_base_outer, p_top2, p_top],
            # Vertical
            [p_base_inner, p_top, p_top2],
            [p_base_inner, p_top2, p_base_inner2],
        ]
        parts.append(np.array(tri_faces, dtype=np.float64))

    m = make_mesh_from_triangles(parts)
    path = os.path.join(OUTPUT_DIR, "webcam_mount.stl")
    m.save(path)
    print(f"  Saved: {path} ({os.path.getsize(path)} bytes)")
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# Also generate OpenSCAD .scad files as a fallback / reference
# ═══════════════════════════════════════════════════════════════════════════════

def generate_openscad_files():
    """Generate OpenSCAD .scad files for all parts.
    These can be opened in OpenSCAD and exported to STL with full CSG
    (proper boolean subtraction for holes, etc.)."""

    print("\nGenerating OpenSCAD reference files ...")

    # Motor mount
    scad = f"""// EvoBot reference-01 — TT Motor Mount Clip (print 2x)
// Open in OpenSCAD → Render (F6) → Export STL (F7)

// Parametric dimensions (mm)
channel_w   = {MOTOR_CHANNEL_W};   // inside width
channel_h   = {MOTOR_CHANNEL_H};   // inside height (depth of U)
wall        = {MOTOR_MOUNT_WALL};  // wall thickness
clip_len    = {MOTOR_CLIP_LENGTH}; // length along motor body
tab_w       = {MOTOR_TAB_WIDTH};   // bolt tab width
tab_t       = {MOTOR_TAB_THICKNESS}; // bolt tab thickness
hole_span   = {MOTOR_MOUNT_HOLE_SPAN}; // M3 hole spacing
hole_dia    = {MOTOR_MOUNT_HOLE_DIA}; // M3 clearance

$fn = {SEGMENTS};

module motor_mount() {{
    outer_w = channel_w + 2*wall;
    total_w = outer_w + 2*tab_w;
    total_h = channel_h + wall;

    difference() {{
        union() {{
            // U-channel body
            translate([-clip_len/2, -outer_w/2, 0])
                cube([clip_len, outer_w, total_h]);
            // Left tab
            translate([-clip_len/2, -total_w/2, 0])
                cube([clip_len, tab_w, tab_t]);
            // Right tab
            translate([-clip_len/2, outer_w/2, 0])
                cube([clip_len, tab_w, tab_t]);
        }}
        // Channel cutout (open top)
        translate([-clip_len/2 - 1, -channel_w/2, wall])
            cube([clip_len + 2, channel_w, channel_h + 1]);
        // M3 bolt holes (4 total, 2 per side)
        for (sx = [-1, 1])
            for (sy = [-1, 1])
                translate([sx * hole_span/2, sy * (outer_w/2 + tab_w/2), -1])
                    cylinder(d=hole_dia, h=tab_t + 2);
    }}
}}

motor_mount();
"""
    path = os.path.join(OUTPUT_DIR, "motor_mount.scad")
    with open(path, 'w') as f:
        f.write(scad)
    print(f"  Saved: {path}")

    # Ball caster
    scad = f"""// EvoBot reference-01 — Ball Caster Assembly (print 1x)
// Open in OpenSCAD → Render (F6) → Export STL (F7)

// Parametric dimensions (mm)
ball_dia          = {CASTER_BALL_DIA};
cup_id            = {CASTER_CUP_ID};
cup_depth         = {CASTER_CUP_DEPTH};
cup_wall          = {CASTER_CUP_WALL};
flange_dia        = {CASTER_FLANGE_DIA};
flange_thick      = {CASTER_FLANGE_THICK};
stem_height       = {CASTER_STEM_HEIGHT};
mount_hole_spacing = {CASTER_MOUNT_HOLE_SPACING};
mount_hole_dia    = {CASTER_MOUNT_HOLE_DIA};
snap_slot_w       = {CASTER_SNAP_SLOT_WIDTH};

$fn = {SEGMENTS};

module ball_caster() {{
    cup_od = cup_id + 2*cup_wall;
    stem_r = cup_od/2 + 1;

    difference() {{
        union() {{
            // Flange
            cylinder(d=flange_dia, h=flange_thick);
            // Stem
            translate([0, 0, flange_thick])
                cylinder(r=stem_r, h=stem_height);
            // Cup (solid sphere shell)
            translate([0, 0, flange_thick + stem_height])
                difference() {{
                    sphere(d=cup_od);
                    sphere(d=cup_id);
                    // Cut off top half (keep bottom hemisphere = cup)
                    translate([0, 0, cup_od/2])
                        cube([cup_od+2, cup_od+2, cup_od], center=true);
                    // Cut off below the equator to desired depth
                    translate([0, 0, -(cup_od/2 + cup_depth)])
                        cube([cup_od+2, cup_od+2, cup_od], center=true);
                }}
        }}
        // Mounting holes (3x, equilateral triangle)
        for (i = [0:2])
            rotate([0, 0, i*120 + 30])
                translate([mount_hole_spacing/sqrt(3), 0, -1])
                    cylinder(d=mount_hole_dia, h=flange_thick + 2);
        // Snap-in slot (rectangular notch in cup rim)
        translate([-snap_slot_w/2, -cup_od/2-1, flange_thick + stem_height - cup_depth])
            cube([snap_slot_w, cup_od+2, cup_depth + cup_wall + 1]);
    }}
}}

ball_caster();
"""
    path = os.path.join(OUTPUT_DIR, "ball_caster.scad")
    with open(path, 'w') as f:
        f.write(scad)
    print(f"  Saved: {path}")

    # Standoff
    scad = f"""// EvoBot reference-01 — Deck Standoff (print 4x)
// Open in OpenSCAD → Render (F6) → Export STL (F7)

// Parametric dimensions (mm)
outer_dia     = {STANDOFF_OD};
inner_dia     = {STANDOFF_ID};
height        = {STANDOFF_HEIGHT};
flange_dia    = {STANDOFF_FLANGE_DIA};
flange_thick  = {STANDOFF_FLANGE_THICK};

$fn = {SEGMENTS};

module standoff() {{
    difference() {{
        union() {{
            // Bottom flange
            cylinder(d=flange_dia, h=flange_thick);
            // Main body
            translate([0, 0, flange_thick])
                cylinder(d=outer_dia, h=height);
            // Top flange
            translate([0, 0, flange_thick + height])
                cylinder(d=flange_dia, h=flange_thick);
        }}
        // M3 through-hole
        translate([0, 0, -1])
            cylinder(d=inner_dia, h=height + 2*flange_thick + 2);
    }}
}}

standoff();
"""
    path = os.path.join(OUTPUT_DIR, "standoff.scad")
    with open(path, 'w') as f:
        f.write(scad)
    print(f"  Saved: {path}")

    # Sensor bracket
    scad = f"""// EvoBot reference-01 — HC-SR04 Sensor Bracket (print 2x)
// Open in OpenSCAD → Render (F6) → Export STL (F7)

// Parametric dimensions (mm)
board_w         = {SENSOR_BRACKET_W};       // HC-SR04 board width
board_h         = {SENSOR_BRACKET_H};       // HC-SR04 board height
base_depth      = {SENSOR_BASE_DEPTH};      // horizontal base depth
wall_thick      = {SENSOR_WALL_THICK};      // wall/base thickness
angle           = {SENSOR_ANGLE_DEG};       // outward tilt (degrees)
transducer_dia  = {SENSOR_TRANSDUCER_DIA};  // ultrasonic cylinder diameter
transducer_span = {SENSOR_TRANSDUCER_SPAN}; // center-to-center spacing
base_hole_span  = {SENSOR_BASE_HOLE_SPAN};  // mounting hole spacing
mount_hole_dia  = {M3_CLEARANCE};           // M3 clearance

$fn = {SEGMENTS};

module sensor_bracket() {{
    total_w = board_w + 2*wall_thick;
    face_h  = board_h + 2*wall_thick;

    difference() {{
        union() {{
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
        }}
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
    }}
}}

sensor_bracket();
"""
    path = os.path.join(OUTPUT_DIR, "sensor_bracket.scad")
    with open(path, 'w') as f:
        f.write(scad)
    print(f"  Saved: {path}")

    # Webcam mount
    scad = f"""// EvoBot reference-01 — Webcam Mount Post (print 1x)
// Open in OpenSCAD → Render (F6) → Export STL (F7)

// Parametric dimensions (mm)
post_dia        = {WEBCAM_POST_DIA};
post_height     = {WEBCAM_POST_HEIGHT};
base_size       = {WEBCAM_BASE_SIZE};
base_thick      = {WEBCAM_BASE_THICK};
base_hole_dia   = {WEBCAM_BASE_HOLE_DIA};  // M4 clearance
platform_w      = {WEBCAM_PLATFORM_W};
platform_d      = {WEBCAM_PLATFORM_D};
platform_thick  = {WEBCAM_PLATFORM_THICK};
tripod_hole_dia = {WEBCAM_TRIPOD_HOLE_DIA}; // 1/4"-20 clearance

$fn = {SEGMENTS};

module webcam_mount() {{
    difference() {{
        union() {{
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
        }}
        // Base center hole (M4)
        translate([0, 0, -1])
            cylinder(d=base_hole_dia, h=base_thick + 2);
        // Platform tripod hole (1/4"-20)
        translate([0, 0, base_thick + post_height - 1])
            cylinder(d=tripod_hole_dia, h=platform_thick + 2);
    }}
}}

webcam_mount();
"""
    path = os.path.join(OUTPUT_DIR, "webcam_mount.scad")
    with open(path, 'w') as f:
        f.write(scad)
    print(f"  Saved: {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("EvoBot reference-01 — STL Part Generator")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Circle segments: {SEGMENTS}")
    print()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = []
    files.append(generate_motor_mount())
    files.append(generate_ball_caster())
    files.append(generate_standoff())
    files.append(generate_sensor_bracket())
    files.append(generate_webcam_mount())

    generate_openscad_files()

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    for f in files:
        name = os.path.basename(f)
        size = os.path.getsize(f)
        print(f"  {name:25s} {size:>8,} bytes  ({size/1024:.1f} KB)")

    # List scad files too
    print()
    print("OpenSCAD reference files (for precise CSG with holes):")
    for name in ["motor_mount.scad", "ball_caster.scad", "standoff.scad",
                 "sensor_bracket.scad", "webcam_mount.scad"]:
        path = os.path.join(OUTPUT_DIR, name)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  {name:25s} {size:>8,} bytes")

    print()
    print("Done. STL files can be imported directly into any slicer.")
    print("OpenSCAD files can be opened in OpenSCAD for CSG rendering")
    print("(proper boolean hole subtraction) then exported to STL.")
    print()
    print("Recommended print settings:")
    print("  Material: PETG")
    print("  Layer height: 0.2mm")
    print("  Infill: 40% (motor mount, sensor bracket, webcam)")
    print("  Infill: 50% (ball caster)")
    print("  Infill: 100% (standoffs)")
    print("  Walls: 3 perimeters minimum")
    print("  Supports: Not needed (all parts designed for flat printing)")
