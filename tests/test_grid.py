"""Tests for ringforge.grid: grid layout, and volumes from the grid compared with
exact formulas (sphere; Pappus' theorem for the rounded band)."""
import math

import numpy as np
import pytest

from ringforge.grid import axis_points, count_volume, sample, voxel_volume
from ringforge.sdf import band, sphere

RI = (11.63 + 0.8128 * 7) / 2          # US 7 -> inner radius 8.6598 mm
T, W, E = 1.7, 2.3, 0.25
BAND_BOX = ((-1.4, -10.6, -10.6), (1.4, 10.6, 10.6))
# Pappus: area of the rounded cross-section times the path of its centre
BAND_EXACT = 2 * math.pi * (RI + T / 2) * (T * W - (4 - math.pi) * E ** 2)   # 230.42 mm^3


def us7_band(P):
    return band(P, RI, T, W, E)


def test_axis_points():
    xs = axis_points(-1.4, 1.4, 0.07)
    assert len(xs) == 41                       # 2.8 / 0.07 = 40 steps -> 41 points
    assert xs[0] == -1.4 and xs[-1] == pytest.approx(1.4)
    assert len(axis_points(0.0, 1.0, 0.3)) == 5   # 0, 0.3, 0.6, 0.9, 1.2 (covers 1.0)
    with pytest.raises(ValueError):
        axis_points(0.0, 1.0, 0.0)
    with pytest.raises(ValueError):
        axis_points(1.0, 1.0, 0.1)


def test_sample_shape_and_values():
    g = sample(us7_band, *BAND_BOX, 0.07)
    assert g.values.shape == (41, 304, 304)
    assert g.values.dtype == np.float32
    for i, j, k in [(0, 0, 0), (20, 152, 290), (40, 303, 303), (7, 150, 3)]:
        assert g.values[i, j, k] == pytest.approx(us7_band(g.point(i, j, k)), abs=1e-5)


def test_sample_chunk_size_does_not_matter():
    a = sample(us7_band, *BAND_BOX, 0.2, chunk=1)
    b = sample(us7_band, *BAND_BOX, 0.2, chunk=64)
    assert np.array_equal(a.values, b.values)


def test_sphere_volume():
    exact = 4 / 3 * math.pi * 3.0 ** 3                      # 113.10 mm^3
    g = sample(lambda P: sphere(P, (0, 0, 0), 3.0), (-3.2,) * 3, (3.2,) * 3, 0.1)
    assert abs(voxel_volume(g) - exact) / exact < 0.001
    assert abs(count_volume(g) - exact) / exact < 0.005


@pytest.mark.parametrize("step, tolerance", [(0.14, 0.002), (0.07, 0.0005), (0.035, 0.0002)])
def test_band_volume_matches_pappus(step, tolerance):
    g = sample(us7_band, *BAND_BOX, step)
    assert abs(voxel_volume(g) - BAND_EXACT) / BAND_EXACT < tolerance
    assert abs(count_volume(g) - BAND_EXACT) / BAND_EXACT < 0.03    # naive: within 3 %
