"""Sampling an SDF on a regular 3D grid.

Marching cubes (next step) needs the SDF's value at every corner of a 3D grid. This
module builds that grid and fills it, a few x-slices at a time so memory stays small.

    sample(f, lo, hi, step) -> Grid with
        values  shape (nx, ny, nz): values[i, j, k] = f(lo + (i, j, k) * step)
        origin  the point of values[0, 0, 0]  (= lo)
        step    grid spacing in mm

Example: the US 7 band (inner radius 8.66 mm, 2.3 x 1.7 mm) fits in the box
lo = (-1.4, -10.6, -10.6), hi = (1.4, 10.6, 10.6). With step 0.07 mm that is
nx = 2.8 / 0.07 + 1 = 41 and ny = nz = 21.2 / 0.07 + 1 = 304 points per axis,
41 x 304 x 304 = 3.8 million SDF values (15 MB as float32).

`count_volume` and `voxel_volume` estimate the volume straight from the grid (no
triangles). They let us test the SDFs against exact formulas before marching cubes
exists, and later serve as an independent check of the marching-cubes volume.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class Grid:
    """SDF values on a regular grid. values[i, j, k] is at origin + (i, j, k) * step."""
    values: np.ndarray
    origin: np.ndarray
    step: float

    def point(self, i, j, k):
        """World coordinates (mm) of grid index (i, j, k)."""
        return self.origin + np.array([i, j, k], float) * self.step


def axis_points(lo, hi, step):
    """Grid coordinates from lo up to at least hi, spaced `step` apart.

    The count is ceil((hi - lo) / step) + 1, so the last point is >= hi and the
    whole box is covered. Example: lo = -1.4, hi = 1.4, step = 0.07 -> 41 points.
    """
    if not step > 0:
        raise ValueError(f"step must be > 0 mm, got {step}")
    if not hi > lo:
        raise ValueError(f"hi must be greater than lo, got lo={lo}, hi={hi}")
    # The small tolerance stops float error (2.8 / 0.07 = 40.000000000000004) from
    # adding an extra point.
    n = int(np.ceil((hi - lo) / step - 1e-9)) + 1
    return lo + step * np.arange(n)


def sample(f, lo, hi, step, chunk=8):
    """Evaluate the SDF f on every point of the grid covering the box [lo, hi].

    f takes points of shape (..., 3) and returns distances of shape (...).
    The grid is filled `chunk` x-slices at a time, so at most
    chunk * ny * nz points (times 3 coordinates) are in memory at once.
    """
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    xs, ys, zs = (axis_points(lo[a], hi[a], step) for a in range(3))
    values = np.empty((len(xs), len(ys), len(zs)), np.float32)
    Y, Z = np.meshgrid(ys, zs, indexing="ij")            # shape (ny, nz)
    for i in range(0, len(xs), chunk):
        X = xs[i:i + chunk]                              # up to `chunk` x values
        P = np.empty((len(X), len(ys), len(zs), 3))
        P[..., 0] = X[:, None, None]
        P[..., 1] = Y
        P[..., 2] = Z
        values[i:i + len(X)] = f(P)
    return Grid(values=values, origin=lo.copy(), step=float(step))


def count_volume(grid):
    """Naive volume (mm^3): number of inside points (value < 0) times step^3.

    Each grid point stands for one cube of side `step`, counted as either fully
    metal or fully air. Along a flat face the grid points may sit just inside or just
    outside, so the error jumps around with the grid alignment (+2.9 %, +0.5 %, -0.8 % for
    the US 7 band at 0.14, 0.07, 0.035 mm). Kept as the simplest possible check.
    """
    return float(np.count_nonzero(grid.values < 0)) * grid.step ** 3


def voxel_volume(grid):
    """Better volume estimate (mm^3) that uses the distance, not only its sign.

    A grid point with distance d sits d mm from the surface. If the surface is a flat
    plane parallel to a face of the point's cube (side s = step), the part of the cube
    that is inside is

        fraction = clamp(0.5 - d / s, 0, 1)

    d = 0 (point on the surface) -> half the cube is inside: 0.5
    d = -s/2 or less              -> whole cube inside:        1
    d = +s/2 or more              -> whole cube outside:       0

    volume = sum of fractions * s^3. This only works because our SDFs return true
    distances; for the US 7 band it is within 0.03 % at a 0.07 mm grid.
    """
    s = grid.step
    fraction = np.clip(0.5 - grid.values.astype(float) / s, 0.0, 1.0)
    return float(fraction.sum()) * s ** 3
