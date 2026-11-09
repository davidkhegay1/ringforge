"""Smoke test for the height-map prototype: volume vs. exact formula, watertight mesh."""
import math, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "prototypes" / "heightmap"))
from engine import ring_mesh, signed_volume, edge_check

def test_flat_band_volume_matches_formula():
    d = 11.63 + 0.8128 * 7                       # US 7 -> 17.32 mm inner diameter
    w, t = 4.0, 1.5
    exact = math.pi * ((d / 2 + t) ** 2 - (d / 2) ** 2) * w   # 354.74 mm^3
    V, F = ring_mesh(d, w, t, None, n_theta=720, n_z=2)
    assert abs(signed_volume(V, F) - exact) / exact < 1e-4
    assert edge_check(F)
