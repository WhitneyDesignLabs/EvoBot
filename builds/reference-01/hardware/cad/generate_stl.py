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

# ─── Caster skid / drag tip parameters ───────────────────────────────────────
SKID_DOME_RADIUS = 8        # mm hemisphere radius (ground contact surface)
SKID_STEM_DIA = 16          # mm stem diameter (= dome diameter)
SKID_FLANGE_DIA = 35        # mm mounting flange outer diameter
SKID_FLANGE_THICK = 3       # mm
# Ride height: 29.5mm from deck bottom to ground
# = flange_thick + stem_height + dome_radius = 3 + 18.5 + 8 = 29.5mm
SKID_STEM_HEIGHT = 18.5     # mm
SKID_MOUNT_BOLT_RADIUS = 12 # mm bolt circle radius (matches DXF)
SKID_MOUNT_HOLE_DIA = 3.4   # mm M3 clearance (generous for print tolerance)

# ─── Standoff parameters ─────────────────────────────────────────────────────
STANDOFF_OD = 8            # mm outer diameter
STANDOFF_ID = 3.2          # mm M3 through-hole
STANDOFF_HEIGHT = 35       # mm
STANDOFF_FLANGE_DIA = 10   # mm
STANDOFF_FLANGE_THICK = 1.5  # mm

# ─── Sensor bracket parameters (L-bracket with channel rails) ────────────────
BRACKET_LENGTH = 50         # mm (X dimension, bracket width)
BRACKET_BASE_W = 18         # mm (Y dimension, base depth)
BRACKET_BASE_T = 3          # mm (Z, base thickness)
BRACKET_WALL_T = 2.5        # mm (Y, back wall thickness)
BRACKET_WALL_H = 30         # mm (Z, back wall height from base top)
BRACKET_RAIL_DEPTH = 3      # mm (Y, rail protrusion from wall)
BRACKET_RAIL_H = 2          # mm (Z, rail height/thickness)
BRACKET_BOT_RAIL_Z = 8      # mm (Z offset from base bottom for bottom rail)
BRACKET_BOARD_GAP = 20.5    # mm (gap between rails = HC-SR04 board height)
BRACKET_HOLE_SPAN = 35      # mm (M3 bolt hole spacing on base)

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


def frustum_tube_mesh(outer_r_bot, outer_r_top, inner_r_bot, inner_r_top,
                      height, segments=SEGMENTS, center_xy=(0, 0), z_base=0):
    """Create a frustum (truncated cone) tube — outer and inner radii can
    differ between bottom and top. Returns array of shape (n_triangles, 3, 3)."""
    cx, cy = center_xy
    triangles = []
    angles = [2 * math.pi * i / segments for i in range(segments)]
    z0 = z_base
    z1 = z_base + height

    for i in range(segments):
        a1 = angles[i]
        a2 = angles[(i + 1) % segments]
        ca1, sa1 = math.cos(a1), math.sin(a1)
        ca2, sa2 = math.cos(a2), math.sin(a2)

        # Bottom points
        ob1 = [cx + outer_r_bot * ca1, cy + outer_r_bot * sa1, z0]
        ob2 = [cx + outer_r_bot * ca2, cy + outer_r_bot * sa2, z0]
        ib1 = [cx + inner_r_bot * ca1, cy + inner_r_bot * sa1, z0]
        ib2 = [cx + inner_r_bot * ca2, cy + inner_r_bot * sa2, z0]
        # Top points
        ot1 = [cx + outer_r_top * ca1, cy + outer_r_top * sa1, z1]
        ot2 = [cx + outer_r_top * ca2, cy + outer_r_top * sa2, z1]
        it1 = [cx + inner_r_top * ca1, cy + inner_r_top * sa1, z1]
        it2 = [cx + inner_r_top * ca2, cy + inner_r_top * sa2, z1]

        # Bottom annular face (normal -Z)
        triangles.append([ob1, ob2, ib2])
        triangles.append([ob1, ib2, ib1])
        # Top annular face (normal +Z)
        triangles.append([ot1, it1, it2])
        triangles.append([ot1, it2, ot2])
        # Outer wall
        triangles.append([ob1, ot1, ot2])
        triangles.append([ob1, ot2, ob2])
        # Inner wall
        triangles.append([ib1, ib2, it2])
        triangles.append([ib1, it2, it1])

    return np.array(triangles, dtype=np.float64)


def disk_with_holes_mesh(outer_r, height, holes, segments=96, rings=6,
                         center_xy=(0, 0), z_base=0):
    """Create a solid disk (cylinder) with cylindrical through-holes.

    Uses a fine radial grid and centroid-based hole exclusion to produce
    proper geometry with real through-holes — no CSG subtraction needed.

    Args:
        outer_r: outer radius of the disk
        height: thickness of the disk
        holes: list of (hx, hy, hr) — hole center x/y relative to disk center, hole radius
        segments: angular divisions (higher = rounder holes, 96 is good)
        rings: radial divisions (higher = better hole edge resolution)
        center_xy: (cx, cy) center of disk
        z_base: z position of disk bottom
    Returns:
        triangle array (n, 3, 3)
    """
    cx, cy = center_xy
    z0, z1 = z_base, z_base + height
    triangles = []

    ring_radii = [outer_r * i / rings for i in range(rings + 1)]
    angles = [2 * math.pi * i / segments for i in range(segments)]

    def point_in_hole(px, py):
        for hx, hy, hr in holes:
            dx, dy = px - (cx + hx), py - (cy + hy)
            if dx * dx + dy * dy < hr * hr:
                return True
        return False

    # Top and bottom faces: radial grid cells, skip those inside holes
    for ri in range(rings):
        r_in = ring_radii[ri]
        r_out = ring_radii[ri + 1]

        for ai in range(segments):
            a1 = angles[ai]
            a2 = angles[(ai + 1) % segments]
            ca1, sa1 = math.cos(a1), math.sin(a1)
            ca2, sa2 = math.cos(a2), math.sin(a2)

            if ri == 0:
                # Center triangle (fan from origin)
                p0x, p0y = cx, cy
                p1x, p1y = cx + r_out * ca1, cy + r_out * sa1
                p2x, p2y = cx + r_out * ca2, cy + r_out * sa2
                cent_x = (p0x + p1x + p2x) / 3
                cent_y = (p0y + p1y + p2y) / 3
                if not point_in_hole(cent_x, cent_y):
                    # Bottom face (-Z normal)
                    triangles.append([[p0x, p0y, z0], [p2x, p2y, z0], [p1x, p1y, z0]])
                    # Top face (+Z normal)
                    triangles.append([[p0x, p0y, z1], [p1x, p1y, z1], [p2x, p2y, z1]])
            else:
                # Quad cell between two rings
                p1x, p1y = cx + r_in * ca1, cy + r_in * sa1
                p2x, p2y = cx + r_in * ca2, cy + r_in * sa2
                p3x, p3y = cx + r_out * ca2, cy + r_out * sa2
                p4x, p4y = cx + r_out * ca1, cy + r_out * sa1
                cent_x = (p1x + p2x + p3x + p4x) / 4
                cent_y = (p1y + p2y + p3y + p4y) / 4
                if not point_in_hole(cent_x, cent_y):
                    # Bottom face (-Z normal, two triangles)
                    triangles.append([[p1x, p1y, z0], [p3x, p3y, z0], [p4x, p4y, z0]])
                    triangles.append([[p1x, p1y, z0], [p2x, p2y, z0], [p3x, p3y, z0]])
                    # Top face (+Z normal, two triangles)
                    triangles.append([[p1x, p1y, z1], [p4x, p4y, z1], [p3x, p3y, z1]])
                    triangles.append([[p1x, p1y, z1], [p3x, p3y, z1], [p2x, p2y, z1]])

    # Outer cylinder wall
    for ai in range(segments):
        a1 = angles[ai]
        a2 = angles[(ai + 1) % segments]
        x1 = cx + outer_r * math.cos(a1)
        y1 = cy + outer_r * math.sin(a1)
        x2 = cx + outer_r * math.cos(a2)
        y2 = cy + outer_r * math.sin(a2)
        triangles.append([[x1, y1, z0], [x2, y2, z0], [x2, y2, z1]])
        triangles.append([[x1, y1, z0], [x2, y2, z1], [x1, y1, z1]])

    # Hole cylinder walls (inner surfaces)
    hole_segs = 32
    for hx, hy, hr in holes:
        h_angles = [2 * math.pi * i / hole_segs for i in range(hole_segs)]
        for i in range(hole_segs):
            a1 = h_angles[i]
            a2 = h_angles[(i + 1) % hole_segs]
            hx1 = cx + hx + hr * math.cos(a1)
            hy1 = cy + hy + hr * math.sin(a1)
            hx2 = cx + hx + hr * math.cos(a2)
            hy2 = cy + hy + hr * math.sin(a2)
            # Inner wall (normals point toward hole center)
            triangles.append([[hx1, hy1, z0], [hx2, hy2, z1], [hx2, hy2, z0]])
            triangles.append([[hx1, hy1, z0], [hx1, hy1, z1], [hx2, hy2, z1]])

    return np.array(triangles, dtype=np.float64)


def box_with_holes_mesh(sx, sy, sz, holes, origin=(0, 0, 0), grid_res=1.0):
    """Create a solid box with cylindrical through-holes (Z-axis).

    Uses a rectangular grid and centroid-based hole exclusion to produce
    proper geometry with real through-holes — no CSG subtraction needed.

    Args:
        sx, sy, sz: box dimensions (X width, Y depth, Z height)
        holes: list of (hx, hy, hr) — hole center x/y relative to origin, hole radius
        origin: (x0, y0, z0) corner at min x,y,z
        grid_res: approximate grid cell size in mm (smaller = finer mesh)
    Returns:
        triangle array (n, 3, 3)
    """
    x0, y0, z0 = origin
    z1 = z0 + sz
    triangles = []

    # Grid divisions
    nx = max(2, int(math.ceil(sx / grid_res)))
    ny = max(2, int(math.ceil(sy / grid_res)))
    dx = sx / nx
    dy = sy / ny

    def point_in_hole(px, py):
        for hx, hy, hr in holes:
            ex, ey = px - (x0 + hx), py - (y0 + hy)
            if ex * ex + ey * ey < hr * hr:
                return True
        return False

    # Top and bottom faces — grid cells, skip those inside holes
    for ix in range(nx):
        for iy in range(ny):
            gx0 = x0 + ix * dx
            gx1 = x0 + (ix + 1) * dx
            gy0 = y0 + iy * dy
            gy1 = y0 + (iy + 1) * dy
            # Centroid test
            cx = (gx0 + gx1) / 2
            cy = (gy0 + gy1) / 2
            if point_in_hole(cx, cy):
                continue
            # Bottom face (-Z normal)
            triangles.append([[gx0, gy0, z0], [gx1, gy1, z0], [gx1, gy0, z0]])
            triangles.append([[gx0, gy0, z0], [gx0, gy1, z0], [gx1, gy1, z0]])
            # Top face (+Z normal)
            triangles.append([[gx0, gy0, z1], [gx1, gy0, z1], [gx1, gy1, z1]])
            triangles.append([[gx0, gy0, z1], [gx1, gy1, z1], [gx0, gy1, z1]])

    # Four side walls (full rectangles — holes don't intersect edges)
    # Front wall (-Y)
    triangles.append([[x0, y0, z0], [x0 + sx, y0, z0], [x0 + sx, y0, z1]])
    triangles.append([[x0, y0, z0], [x0 + sx, y0, z1], [x0, y0, z1]])
    # Back wall (+Y)
    triangles.append([[x0, y0 + sy, z0], [x0 + sx, y0 + sy, z1], [x0 + sx, y0 + sy, z0]])
    triangles.append([[x0, y0 + sy, z0], [x0, y0 + sy, z1], [x0 + sx, y0 + sy, z1]])
    # Left wall (-X)
    triangles.append([[x0, y0, z0], [x0, y0, z1], [x0, y0 + sy, z1]])
    triangles.append([[x0, y0, z0], [x0, y0 + sy, z1], [x0, y0 + sy, z0]])
    # Right wall (+X)
    triangles.append([[x0 + sx, y0, z0], [x0 + sx, y0 + sy, z0], [x0 + sx, y0 + sy, z1]])
    triangles.append([[x0 + sx, y0, z0], [x0 + sx, y0 + sy, z1], [x0 + sx, y0, z1]])

    # Hole cylinder walls (inner surfaces)
    hole_segs = 32
    for hx, hy, hr in holes:
        h_cx = x0 + hx
        h_cy = y0 + hy
        h_angles = [2 * math.pi * i / hole_segs for i in range(hole_segs)]
        for i in range(hole_segs):
            a1 = h_angles[i]
            a2 = h_angles[(i + 1) % hole_segs]
            px1 = h_cx + hr * math.cos(a1)
            py1 = h_cy + hr * math.sin(a1)
            px2 = h_cx + hr * math.cos(a2)
            py2 = h_cy + hr * math.sin(a2)
            # Inner wall (normals point toward hole center)
            triangles.append([[px1, py1, z0], [px2, py2, z1], [px2, py2, z0]])
            triangles.append([[px1, py1, z0], [px1, py1, z1], [px2, py2, z1]])

    return np.array(triangles, dtype=np.float64)


def hemisphere_mesh(radius, segments=SEGMENTS, lat_segments=16,
                    center_xy=(0, 0), z_base=0):
    """Create a solid hemisphere (dome pointing up from z_base).

    Flat circular base at z_base, dome extends up to z_base + radius.
    Includes the flat bottom cap.

    Returns triangle array (n, 3, 3).
    """
    cx, cy = center_xy
    triangles = []
    angles = [2 * math.pi * i / segments for i in range(segments)]

    # Flat bottom disk (circular base face, normal -Z)
    for i in range(segments):
        a1 = angles[i]
        a2 = angles[(i + 1) % segments]
        x1 = cx + radius * math.cos(a1)
        y1 = cy + radius * math.sin(a1)
        x2 = cx + radius * math.cos(a2)
        y2 = cy + radius * math.sin(a2)
        triangles.append([[cx, cy, z_base], [x2, y2, z_base], [x1, y1, z_base]])

    # Hemisphere surface (latitude rings from equator to pole)
    for i in range(lat_segments):
        theta1 = (math.pi / 2) * i / lat_segments
        theta2 = (math.pi / 2) * (i + 1) / lat_segments

        r1 = radius * math.cos(theta1)
        r2 = radius * math.cos(theta2)
        z1 = z_base + radius * math.sin(theta1)
        z2 = z_base + radius * math.sin(theta2)

        for j in range(segments):
            a1 = angles[j]
            a2 = angles[(j + 1) % segments]
            ca1, sa1 = math.cos(a1), math.sin(a1)
            ca2, sa2 = math.cos(a2), math.sin(a2)

            if r2 < 0.01:
                # Near pole: single triangle to pole point
                p1 = [cx + r1 * ca1, cy + r1 * sa1, z1]
                p2 = [cx + r1 * ca2, cy + r1 * sa2, z1]
                pole = [cx, cy, z_base + radius]
                triangles.append([p1, p2, pole])
            else:
                # Quad strip between two latitude rings
                p1 = [cx + r1 * ca1, cy + r1 * sa1, z1]
                p2 = [cx + r1 * ca2, cy + r1 * sa2, z1]
                p3 = [cx + r2 * ca2, cy + r2 * sa2, z2]
                p4 = [cx + r2 * ca1, cy + r2 * sa1, z2]
                triangles.append([p1, p2, p3])
                triangles.append([p1, p3, p4])

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
    """Generate caster skid / drag tip STL.

    Fixed hemisphere dome on a cylindrical stem with bolt-on flange.
    No moving parts — the dome slides on the ground surface.
    One solid piece, prints without supports.

    Replaces the original ball caster design with a simpler, more
    printable drag tip suitable for a lightweight robot on smooth floors.
    """
    print("Generating caster_skid.stl ...")

    parts = []

    dome_r = SKID_DOME_RADIUS               # 8mm
    stem_r = SKID_STEM_DIA / 2               # 8mm
    stem_h = SKID_STEM_HEIGHT                # 18.5mm
    flange_r = SKID_FLANGE_DIA / 2           # 17.5mm
    flange_t = SKID_FLANGE_THICK             # 3mm
    bolt_r = SKID_MOUNT_BOLT_RADIUS          # 12mm
    hole_r = SKID_MOUNT_HOLE_DIA / 2         # 1.7mm

    # Bolt hole positions (3x M3, 120° apart, starting at 90°)
    bolt_holes = []
    for k in range(3):
        angle = 2 * math.pi * k / 3 + math.pi / 2
        bolt_holes.append((bolt_r * math.cos(angle),
                           bolt_r * math.sin(angle),
                           hole_r))

    # Layer 1: Flange with real through-holes (z=0 to z=flange_t)
    parts.append(disk_with_holes_mesh(flange_r, flange_t, bolt_holes,
                                      segments=96, rings=6, z_base=0))

    # Layer 2: Cylindrical stem (z=flange_t to z=flange_t+stem_h)
    parts.append(cylinder_mesh(stem_r, stem_h, z_base=flange_t))

    # Layer 3: Hemisphere dome (z=flange_t+stem_h, dome extends upward)
    parts.append(hemisphere_mesh(dome_r, segments=SEGMENTS, lat_segments=16,
                                 z_base=flange_t + stem_h))

    m = make_mesh_from_triangles(parts)
    path = os.path.join(OUTPUT_DIR, "caster_skid.stl")
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

    Vertical L-bracket with horizontal channel rails.
    Base plate bolts to top deck (2x M3 through-holes).
    Back wall rises vertically from front edge of base.
    Two horizontal rails on the front of the wall grip the HC-SR04 PCB.
    Sensor slides in from the side between the rails.

    Cross-section (looking from the side):
         +--+  <- top rail
         |  |  <- HC-SR04 board in channel (20.5mm gap)
         +--+  <- bottom rail
         |  |  <- 5mm header clearance
         |  |  <- back wall
    =====+  +===  <- base plate with bolt holes
      DECK SURFACE
    """
    print("Generating sensor_bracket.stl ...")

    parts = []

    length = BRACKET_LENGTH       # 50mm (X dimension)
    base_w = BRACKET_BASE_W       # 18mm (Y dimension, base depth)
    base_t = BRACKET_BASE_T       # 3mm  (Z, base thickness)
    wall_t = BRACKET_WALL_T       # 2.5mm (Y, wall thickness)
    wall_h = BRACKET_WALL_H       # 30mm (Z, wall height)
    rail_d = BRACKET_RAIL_DEPTH   # 3mm  (Y, rail protrusion)
    rail_h = BRACKET_RAIL_H       # 2mm  (Z, rail thickness)
    bot_rail_z = BRACKET_BOT_RAIL_Z  # 8mm from base bottom
    top_rail_z = bot_rail_z + rail_h + BRACKET_BOARD_GAP  # 28.5mm
    hole_span = BRACKET_HOLE_SPAN # 35mm between bolt holes
    hole_r = M3_CLEARANCE / 2     # 1.6mm

    # Coordinate system: X = bracket length, Y = depth (wall at Y=0), Z = height
    # Base sits on deck, wall rises from front edge (Y=0)

    # ── Base plate with 2x M3 through-holes ──
    # Holes centered on base: X = length/2 ± hole_span/2, Y = base_w/2
    holes = [
        (length / 2 - hole_span / 2, base_w / 2, hole_r),
        (length / 2 + hole_span / 2, base_w / 2, hole_r),
    ]
    parts.append(box_with_holes_mesh(length, base_w, base_t, holes,
                                     origin=(0, 0, 0), grid_res=1.0))

    # ── Back wall (rises from front edge of base) ──
    # Y: from 0 to wall_t, Z: from base_t to base_t + wall_h
    parts.append(box_mesh(length, wall_t, wall_h,
                          origin=(0, 0, base_t)))

    # ── Bottom rail (horizontal shelf on front of wall) ──
    # Y: from -rail_d to 0 (protrudes forward from wall face)
    # Z: from bot_rail_z to bot_rail_z + rail_h
    parts.append(box_mesh(length, rail_d, rail_h,
                          origin=(0, -rail_d, bot_rail_z)))

    # ── Top rail ──
    # Z: from top_rail_z to top_rail_z + rail_h
    parts.append(box_mesh(length, rail_d, rail_h,
                          origin=(0, -rail_d, top_rail_z)))

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

    # Caster skid — read the SCAD file we already maintain separately
    scad_path = os.path.join(OUTPUT_DIR, "ball_caster.scad")
    if os.path.exists(scad_path):
        print(f"  Exists: {scad_path} (caster skid, maintained separately)")
    else:
        print(f"  Warning: {scad_path} not found — create from ball_caster.scad template")

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

    # Sensor bracket (L-bracket with channel rails)
    scad = f"""// EvoBot reference-01 — HC-SR04 Sensor Bracket (print 2x)
// L-bracket with channel rails for slide-in PCB retention
// Open in OpenSCAD → Render (F6) → Export STL (F7)

// Parametric dimensions (mm)
bracket_len    = {BRACKET_LENGTH};       // X dimension
base_w         = {BRACKET_BASE_W};       // Y dimension (base depth)
base_t         = {BRACKET_BASE_T};       // Z (base thickness)
wall_t         = {BRACKET_WALL_T};       // Y (back wall thickness)
wall_h         = {BRACKET_WALL_H};       // Z (wall height above base top)
rail_d         = {BRACKET_RAIL_DEPTH};   // Y (rail protrusion)
rail_h         = {BRACKET_RAIL_H};       // Z (rail thickness)
bot_rail_z     = {BRACKET_BOT_RAIL_Z};   // Z offset for bottom rail
board_gap      = {BRACKET_BOARD_GAP};    // gap between rails (HC-SR04 height)
hole_span      = {BRACKET_HOLE_SPAN};    // M3 bolt hole spacing
mount_hole_dia = {M3_CLEARANCE};         // M3 clearance

$fn = {SEGMENTS};

module sensor_bracket() {{
    top_rail_z = bot_rail_z + rail_h + board_gap;

    difference() {{
        union() {{
            // Base plate
            cube([bracket_len, base_w, base_t]);
            // Back wall
            cube([bracket_len, wall_t, base_t + wall_h]);
            // Bottom rail
            translate([0, -rail_d, bot_rail_z])
                cube([bracket_len, rail_d, rail_h]);
            // Top rail
            translate([0, -rail_d, top_rail_z])
                cube([bracket_len, rail_d, rail_h]);
        }}
        // M3 bolt holes through base
        for (sx = [-1, 1])
            translate([bracket_len/2 + sx*hole_span/2, base_w/2, -1])
                cylinder(d=mount_hole_dia, h=base_t + 2);
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
