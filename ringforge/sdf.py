"""Signed distance functions (SDFs): the shapes RingForge is built from.

An SDF takes points P and returns, for each point, its distance to the surface of a
shape: NEGATIVE inside, POSITIVE outside, zero exactly on the surface.

    P has shape (..., 3): the last axis holds (x, y, z) in millimetres.
    The result has shape (...): one distance per point.

So one call can evaluate a single point (shape (3,)), a list of points (shape (n, 3))
or a whole 3D grid (shape (nx, ny, nz, 3)).

Coordinates: finger axis = x, the ring circle lies in the y-z plane, top of the ring
(where a stone sits) is at +z.

Shapes are combined with simple math on their distances:

    union(a, b)        = min(a, b)       inside if inside EITHER shape
    intersect(a, b)    = max(a, b)       inside if inside BOTH shapes
    subtract(a, b)     = max(a, -b)      inside a AND outside b (cuts b out of a)
    smooth_union(a, b) = min(a, b) - h^2 * k / 4,  h = max(k - |a - b|, 0) / k

The distance formulas for the rounded box (used by the band), the segment (capsule)
and the polynomial smooth minimum follow Inigo Quilez's articles "Distance functions"
and "Smooth minimum" (iquilezles.org), listed in the README References.
"""
import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _points(P):
    """Return P as a float array whose last axis has length 3."""
    P = np.asarray(P, dtype=float)
    if P.shape[-1] != 3:
        raise ValueError(f"points must have shape (..., 3), got {P.shape}")
    return P


def _require_positive(**values):
    """Raise ValueError if any named value is not > 0 (e.g. a negative radius)."""
    for name, value in values.items():
        if not value > 0:
            raise ValueError(f"{name} must be > 0 mm, got {value}")


def _rounded_rect_2d(u, v, half_u, half_v, corner):
    """Exact 2D distance to a rectangle centred at (0, 0) with rounded corners.

    The rectangle spans |u| <= half_u and |v| <= half_v; its corners are rounded with
    radius `corner` (0 gives sharp corners).

    Idea: shrink the rectangle by `corner`, measure the distance to the shrunk
    rectangle, then subtract `corner`. Every point of the shrunk rectangle grows into
    a disc of radius `corner`, which is exactly what rounds the corners.

        qu, qv = |u| - (half_u - corner), |v| - (half_v - corner)
        outside part: length of (max(qu, 0), max(qv, 0))   (0 when inside)
        inside part:  min(max(qu, qv), 0)                  (0 when outside)
        distance = outside part + inside part - corner
    """
    qu = np.abs(u) - (half_u - corner)
    qv = np.abs(v) - (half_v - corner)
    outside = np.hypot(np.maximum(qu, 0.0), np.maximum(qv, 0.0))
    inside = np.minimum(np.maximum(qu, qv), 0.0)
    return outside + inside - corner


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

def sphere(P, center, radius):
    """Sphere: distance = |P - center| - radius."""
    _require_positive(radius=radius)
    P = _points(P)
    return np.linalg.norm(P - np.asarray(center, float), axis=-1) - radius


def band(P, inner_radius, thickness, width, edge_radius=0.25):
    """The ring band: a rounded rectangle revolved around the finger axis (x).

    Cross-section (looking along the band, in the plane of x and r):

        r = Ri + t  +----------------+   outer surface (top of the ring at +z)
                    |                |   thickness t (radial)
        r = Ri      +----------------+   inner surface (touches the finger)
                    x = -w/2      x = +w/2

    For each point we take its distance from the finger axis, r = sqrt(y^2 + z^2),
    and measure the 2D distance from (r, x) to that rectangle, whose centre is at
    r = Ri + t/2, x = 0. Its corners are rounded with `edge_radius`.

    Parameters (mm): inner_radius Ri, thickness t, width w, edge_radius e.
    Example (US 7): Ri = 8.66, t = 1.7, w = 2.3, e = 0.25.
    """
    _require_positive(inner_radius=inner_radius, thickness=thickness, width=width)
    if not 0 <= edge_radius <= min(thickness, width) / 2:
        raise ValueError(
            f"edge_radius must be between 0 and {min(thickness, width) / 2} mm "
            f"(half the smaller of thickness and width), got {edge_radius}")
    P = _points(P)
    r = np.hypot(P[..., 1], P[..., 2])
    return _rounded_rect_2d(r - (inner_radius + thickness / 2), P[..., 0],
                            thickness / 2, width / 2, edge_radius)


def capsule(P, a, b, radius):
    """Capsule: all points within `radius` of the segment from a to b (a prong).

    Project P onto the segment: h = clamp((P - a) . (b - a) / |b - a|^2, 0, 1).
    The closest point on the segment is a + h (b - a); the distance to the capsule is
    the distance to that point minus the radius. If a == b this is a sphere.
    """
    _require_positive(radius=radius)
    P = _points(P)
    a, b = np.asarray(a, float), np.asarray(b, float)
    ab = b - a
    pa = P - a
    length2 = ab @ ab
    if length2 == 0.0:
        h = np.zeros(P.shape[:-1])
    else:
        h = np.clip((pa @ ab) / length2, 0.0, 1.0)
    return np.linalg.norm(pa - h[..., None] * ab, axis=-1) - radius


def cylinder(P, center, axis, radius, half_length):
    """Finite cylinder with flat caps (light holes, bezel tubes, seat openings).

    The cylinder is centred at `center`, points along `axis` (any length, it is
    normalised), and spans `half_length` on each side of the centre.

    For each point: along  = (P - center) . axis           (signed height)
                    radial = distance from the axis line
    That is again a 2D rectangle problem (|radial| <= radius, |along| <= half_length)
    with sharp corners, so the distance is exact, also near the rim.
    """
    _require_positive(radius=radius, half_length=half_length)
    P = _points(P)
    axis = np.asarray(axis, float)
    norm = np.linalg.norm(axis)
    if norm == 0.0:
        raise ValueError("cylinder axis must not be the zero vector")
    axis = axis / norm
    d = P - np.asarray(center, float)
    along = d @ axis
    radial = np.linalg.norm(d - along[..., None] * axis, axis=-1)
    return _rounded_rect_2d(radial, along, radius, half_length, 0.0)


# ---------------------------------------------------------------------------
# Operations (combine distances of already evaluated shapes)
# ---------------------------------------------------------------------------

def union(a, b):
    """Inside if inside either shape: min(a, b)."""
    return np.minimum(a, b)


def intersect(a, b):
    """Inside if inside both shapes: max(a, b)."""
    return np.maximum(a, b)


def subtract(a, b):
    """Cut shape b out of shape a: max(a, -b).

    -b is "everything outside b", so max(a, -b) is inside a AND outside b.
    Used for stone seats, light holes and pierced patterns.
    """
    return np.maximum(a, -np.asarray(b))


def smooth_union(a, b, k):
    """Union with a rounded fillet of size about k mm where the shapes meet.

    Polynomial smooth minimum (Quilez):
        h = max(k - |a - b|, 0) / k        (1 where a == b, 0 once |a - b| >= k)
        result = min(a, b) - h^2 * k / 4

    Far from the joint (|a - b| >= k) it equals min(a, b). Exactly at the joint
    (a == b) it is k/4 below the plain minimum, which adds a little metal: the fillet.
    k <= 0 means no smoothing (plain union).
    """
    a, b = np.asarray(a, float), np.asarray(b, float)
    if k <= 0:
        return np.minimum(a, b)
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k / 4
