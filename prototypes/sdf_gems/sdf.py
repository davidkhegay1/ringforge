"""Prototype: rings with gemstones using signed distance fields (SDF) + marching cubes.
Coordinates: finger axis = x, ring circle in the y-z plane, top of ring at +z."""
import numpy as np, time, struct
from scipy.spatial import ConvexHull
from skimage.measure import marching_cubes

# ---------- SDF building blocks: f(p) < 0 inside, > 0 outside ----------
def smin(a, b, k):                       # smooth union -> fillets where parts meet
    h = np.maximum(k - np.abs(a - b), 0) / k
    return np.minimum(a, b) - h * h * k / 4
def subtract(a, b): return np.maximum(a, -b)

def capsule(P, a, b, r):
    a, b = np.asarray(a, float), np.asarray(b, float); ba = b - a
    pa = P - a; h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return np.linalg.norm(pa - h[..., None] * ba, axis=-1) - r

def band(P, Ri, t, w, e=0.25):           # rounded rectangle cross-section revolved around x
    r = np.hypot(P[..., 1], P[..., 2])
    qx = np.abs(r - (Ri + t / 2)) - t / 2 + e
    qy = np.abs(P[..., 0]) - w / 2 + e
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - e

def cylinder(P, c, axis, r, half_len):   # finite cylinder
    axis = np.asarray(axis, float) / np.linalg.norm(axis); d = P - c
    along = d @ axis; radial = np.linalg.norm(d - along[..., None] * axis, axis=-1)
    return np.maximum(radial - r, np.abs(along) - half_len)

# ---------- Round brilliant gem as an exact convex polyhedron ----------
def brilliant(D, table=0.56, crown=0.15, girdle=0.03, pav=0.43, n_girdle=32):
    R, rt, g = D / 2, table * D / 2, girdle * D
    ch, pd = crown * D, pav * D
    V = []
    for k in range(8):
        a = k * np.pi / 4
        V.append((rt * np.cos(a), rt * np.sin(a), g / 2 + ch))                      # table
        b = a + np.pi / 8; rm = 0.82 * R
        frac = (rm - rt) / (R - rt)
        V.append((rm * np.cos(b), rm * np.sin(b), g / 2 + ch * (1 - frac) + 0.02 * D))  # star / kite points
        rp = 0.52 * R
        V.append((rp * np.cos(a), rp * np.sin(a), -g / 2 - pd * (1 - rp / R) - 0.02 * D))  # pavilion mains
    for k in range(n_girdle):
        a = 2 * np.pi * k / n_girdle
        V += [(R * np.cos(a), R * np.sin(a), g / 2), (R * np.cos(a), R * np.sin(a), -g / 2)]
    V.append((0, 0, -g / 2 - pd))                                                      # culet
    V = np.array(V); hull = ConvexHull(V)
    F = hull.simplices.copy()
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    flip = np.einsum("ij,ij->i", n, V[F].mean(1)) < 0; F[flip] = F[flip][:, ::-1]
    planes = np.unique(np.round(hull.equations, 6), axis=0)                          # n.x + d <= 0 inside
    return V, F, planes, dict(top=g / 2 + ch, bottom=-g / 2 - pd, R=R)

def gem_sdf(P_local, planes, grow=0.0):
    d = np.full(P_local.shape[:-1], -1e9, np.float32)
    for n0, n1, n2, off in planes:                       # running max keeps memory small
        np.maximum(d, P_local[..., 0] * n0 + P_local[..., 1] * n1 + P_local[..., 2] * n2 + off, out=d)
    return d - grow

def frame(origin, up):                   # local frame: z' = up, x' = finger axis x
    up = np.asarray(up, float) / np.linalg.norm(up)
    xa = np.array([1.0, 0, 0]); xa -= (xa @ up) * up; xa /= np.linalg.norm(xa)
    ya = np.cross(up, xa)
    return np.asarray(origin, float), np.stack([xa, ya, up])     # rows = local axes
def to_local(P, fr): return (P - fr[0]) @ fr[1].T
def to_world(V, fr): return V @ fr[1] + fr[0]

# ---------- Polygonize ----------
def mesh_sdf(f, lo, hi, step, chunk=6):
    xs, ys, zs = (np.arange(l, h + step, step) for l, h in zip(lo, hi))
    vol = np.empty((len(xs), len(ys), len(zs)), np.float32)
    Y, Z = np.meshgrid(ys, zs, indexing="ij")
    for i in range(0, len(xs), chunk):
        X = xs[i:i + chunk][:, None, None] + 0 * Y[None]
        P = np.stack([X, np.broadcast_to(Y, X.shape), np.broadcast_to(Z, X.shape)], -1).astype(np.float32)
        vol[i:i + chunk] = f(P)
    vol = np.pad(vol, 1, constant_values=1.0)                       # closed surface at the box edge
    V, F, _, _ = marching_cubes(vol, 0.0, spacing=(step,) * 3)
    V += np.array(lo) - step
    return V, F

def signed_volume(V, F):
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    return np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6
def edge_check(F):
    e = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    return bool((np.unique(e, axis=0, return_counts=True)[1] == 2).all())
def write_stl(path, V, F):
    tri = V[F].astype(np.float32); n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(F), dtype=[("n", "<f4", 3), ("v", "<f4", 9), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri.reshape(-1, 9)
    with open(path, "wb") as fh:
        fh.write(b"RingForge SDF prototype".ljust(80)); fh.write(struct.pack("<I", len(F))); fh.write(rec.tobytes())
