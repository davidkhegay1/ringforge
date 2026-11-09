"""Tests for ringforge.sdf: distances at hand-computed points, sign convention,
input checks, and an independent brute-force check of the band's distance."""
import math

import numpy as np
import pytest

from ringforge.sdf import (band, capsule, cylinder, intersect, smooth_union, sphere,
                           subtract, union)

RI = (11.63 + 0.8128 * 7) / 2          # US 7 -> inner radius 8.6598 mm
T, W, E = 1.7, 2.3, 0.25               # thickness, width, edge radius (mm)


# --- sphere ------------------------------------------------------------------

def test_sphere_sign_convention():
    c, r = (1.0, 2.0, 3.0), 2.0
    assert sphere(c, c, r) == pytest.approx(-2.0)                  # centre: -r (inside)
    assert sphere((3.0, 2.0, 3.0), c, r) == pytest.approx(0.0)     # on the surface
    assert sphere((1.0, 2.0, 8.0), c, r) == pytest.approx(3.0)     # 5 mm away -> +3


def test_works_on_any_array_shape():
    P = np.zeros((4, 5, 6, 3))
    assert sphere(P, (0, 0, 0), 1.0).shape == (4, 5, 6)
    assert band(P, RI, T, W).shape == (4, 5, 6)


# --- band ----------------------------------------------------------------------

@pytest.mark.parametrize("z, expected", [
    (RI - 0.66, 0.66),            # inside the finger hole, 0.66 mm from the metal
    (RI, 0.0),                    # inner surface
    (RI + T / 2, -T / 2),         # middle of the metal: -0.85 (deepest point)
    (RI + T, 0.0),                # outer surface (top of the ring)
    (RI + T + 1.0, 1.0),          # 1 mm above the ring
])
def test_band_along_top(z, expected):
    assert band((0.0, 0.0, z), RI, T, W, E) == pytest.approx(expected, abs=1e-12)


def test_band_is_round():
    """Same distance from the axis -> same value, whatever the angle in y-z."""
    for angle in np.linspace(0, 2 * np.pi, 7):
        p = (0.3, 9.4 * math.sin(angle), 9.4 * math.cos(angle))
        assert band(p, RI, T, W, E) == pytest.approx(band((0.3, 0, 9.4), RI, T, W, E))


def test_band_rounded_corner():
    """Point at the sharp corner (x = w/2, r = Ri + t): the rounded corner is
    sqrt(e^2 + e^2) - e = 0.1036 mm away."""
    d = band((W / 2, 0.0, RI + T), RI, T, W, E)
    assert d == pytest.approx(math.hypot(E, E) - E, abs=1e-12)


def test_band_matches_brute_force_cross_section():
    """Independent check: sample the outline of the cross-section densely, then
    measure distances by brute force (closest outline point). The band's SDF must
    agree for random points in the (x, r) plane."""
    # outline: 4 straight sides + 4 quarter circles, about 0.0005 mm apart
    hu, hv = T / 2, W / 2                       # half sizes in r and x
    pts = []
    for s in np.linspace(-1, 1, 4000):
        pts += [(hu, s * (hv - E)), (-hu, s * (hv - E)),
                (s * (hu - E), hv), (s * (hu - E), -hv)]
    for cu, cv in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        for a in np.linspace(0, np.pi / 2, 1000):
            pts.append((cu * (hu - E + E * math.cos(a)), cv * (hv - E + E * math.sin(a))))
    outline = np.array(pts)                      # columns: (r - centre, x)

    rng = np.random.default_rng(1)
    u = rng.uniform(-2, 2, 300)                  # r - (Ri + t/2)
    v = rng.uniform(-2.5, 2.5, 300)              # x
    brute = np.min(np.hypot(u[:, None] - outline[:, 0], v[:, None] - outline[:, 1]), axis=1)
    inside = (np.abs(u) <= hu) & (np.abs(v) <= hv)
    corner = (np.abs(u) > hu - E) & (np.abs(v) > hv - E)
    inside &= ~corner | (np.hypot(np.abs(u) - (hu - E), np.abs(v) - (hv - E)) <= E)
    brute[inside] *= -1

    P = np.stack([v, np.zeros_like(u), RI + T / 2 + u], axis=-1)   # put them at the top
    assert np.max(np.abs(band(P, RI, T, W, E) - brute)) < 1e-3


def test_band_gradient_has_length_one():
    """A true distance field changes by 1 mm per mm when you walk straight away from
    the surface, so its gradient has length 1. Checked outside the band, where it
    holds everywhere."""
    rng = np.random.default_rng(2)
    P = np.stack([rng.uniform(-3, 3, 200), rng.uniform(-12, 12, 200),
                  rng.uniform(-12, 12, 200)], axis=-1)
    P = P[band(P, RI, T, W, E) > 0.05]
    h = 1e-6
    grad = np.stack([(band(P + h * e, RI, T, W, E) - band(P - h * e, RI, T, W, E)) / (2 * h)
                     for e in np.eye(3)], axis=-1)
    assert np.allclose(np.linalg.norm(grad, axis=-1), 1.0, atol=1e-5)


@pytest.mark.parametrize("args", [
    dict(inner_radius=RI, thickness=0.0, width=W),        # no wall
    dict(inner_radius=RI, thickness=T, width=-2.3),       # negative width
    dict(inner_radius=0.0, thickness=T, width=W),         # no finger hole
    dict(inner_radius=RI, thickness=T, width=W, edge_radius=0.9),   # > t/2 = 0.85
    dict(inner_radius=RI, thickness=T, width=W, edge_radius=-0.1),
])
def test_band_rejects_bad_sizes(args):
    with pytest.raises(ValueError):
        band((0, 0, 9), **args)


# --- capsule and cylinder --------------------------------------------------------

def test_capsule_distances():
    a, b, r = (0, 0, 0), (0, 0, 1), 0.4
    assert capsule((0, 1, 0.5), a, b, r) == pytest.approx(0.6)     # beside the middle
    assert capsule((0, 0, 3), a, b, r) == pytest.approx(1.6)       # past the end b
    assert capsule((0, 0, 0.5), a, b, r) == pytest.approx(-0.4)    # on the axis


def test_capsule_with_equal_ends_is_a_sphere():
    p = (0.2, -0.7, 1.1)
    assert capsule(p, (0, 0, 1), (0, 0, 1), 0.3) == pytest.approx(sphere(p, (0, 0, 1), 0.3))


def test_cylinder_distances():
    c, axis, r, h = (0, 0, 0), (0, 0, 1), 1.0, 1.0
    assert cylinder((0, 0, 0), c, axis, r, h) == pytest.approx(-1.0)     # centre
    assert cylinder((0, 3, 0), c, axis, r, h) == pytest.approx(2.0)      # beside it
    assert cylinder((0, 0, 1.5), c, axis, r, h) == pytest.approx(0.5)    # above the cap
    # diagonal from the rim: (2, 2) is (1, 1) past the rim corner -> sqrt(2)
    assert cylinder((2, 0, 2), c, axis, r, h) == pytest.approx(math.sqrt(2))


def test_cylinder_tilted_axis():
    """Axis along y-z diagonal: a point 2 mm along the axis from the centre is
    1 mm past the cap (half length 1)."""
    axis = (0, 1, 1)
    p = 2 * np.array(axis) / math.sqrt(2)
    assert cylinder(p, (0, 0, 0), axis, 0.5, 1.0) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        cylinder(p, (0, 0, 0), (0, 0, 0), 0.5, 1.0)


# --- operations --------------------------------------------------------------------

def test_union_example_from_proposal():
    """0.3 mm outside the band but 0.1 mm inside a prong -> metal (-0.1)."""
    assert union(0.3, -0.1) == pytest.approx(-0.1)


def test_intersect_and_subtract():
    assert intersect(-0.5, -0.2) == pytest.approx(-0.2)     # inside both
    assert intersect(-0.5, 0.2) == pytest.approx(0.2)       # outside one -> outside
    # metal point (-0.5) inside a seat cutter (-0.2) is removed: max(-0.5, 0.2) = 0.2
    assert subtract(-0.5, -0.2) == pytest.approx(0.2)
    # metal point (-0.5) outside the cutter (+0.3) stays metal: max(-0.5, -0.3) = -0.3
    assert subtract(-0.5, 0.3) == pytest.approx(-0.3)


def test_subtract_cuts_a_hole_through_the_band():
    """A 1 mm light hole straight down through the top of the band."""
    hole = lambda P: cylinder(P, (0, 0, RI + T / 2), (0, 0, 1), 0.5, 2.0)
    metal = lambda P: subtract(band(P, RI, T, W, E), hole(P))
    assert metal((0, 0, RI + T / 2)) > 0          # centre of the hole: air now
    assert metal((0, 0.8, RI + T / 2)) < 0        # 0.3 mm beside the hole: still metal


def test_smooth_union():
    k = 0.5
    # far apart (|a - b| >= k): same as min
    assert smooth_union(0.3, 1.0, k) == pytest.approx(0.3)
    assert smooth_union(0.3, -0.5, k) == pytest.approx(-0.5)
    # equal: k/4 below min -> 0.3 - 0.125 = 0.175
    assert smooth_union(0.3, 0.3, k) == pytest.approx(0.175)
    # in between: h = (0.5 - 0.1) / 0.5 = 0.8 -> 0.3 - 0.64 * 0.125 = 0.22
    assert smooth_union(0.3, 0.4, k) == pytest.approx(0.22)
    # never above min, and k = 0 is a plain union
    a, b = np.random.default_rng(3).uniform(-1, 1, (2, 1000))
    assert np.all(smooth_union(a, b, k) <= np.minimum(a, b))
    assert np.array_equal(smooth_union(a, b, 0.0), np.minimum(a, b))
