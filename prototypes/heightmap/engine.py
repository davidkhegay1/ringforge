"""Prototype: a ring = cylinder surface (theta, z) + height map h(theta, z). Pure NumPy mesh engine."""
import numpy as np, struct, time

def ring_mesh(inner_d, width, thick, height_fn=None, n_theta=720, n_z=80):
    Ri, Ro = inner_d/2, inner_d/2 + thick
    th = np.linspace(0, 2*np.pi, n_theta, endpoint=False)
    z = np.linspace(-width/2, width/2, n_z)
    TH, Z = np.meshgrid(th, z, indexing="ij")                 # shape (n_theta, n_z)
    H = np.zeros_like(TH) if height_fn is None else height_fn(TH, Z, Ro)
    def cyl(R):  # (n_theta, n_z) radii -> xyz
        return np.stack([R*np.cos(TH), R*np.sin(TH), Z], -1).reshape(-1, 3)
    outer = cyl(Ro + H); inner = cyl(np.full_like(TH, Ri))
    V = np.vstack([outer, inner]); off = n_theta*n_z
    idx = lambda i, j: (i % n_theta)*n_z + j
    F = []
    for i in range(n_theta):
        for j in range(n_z-1):
            a, b, c, d = idx(i,j), idx(i+1,j), idx(i+1,j+1), idx(i,j+1)
            F += [(a,b,c),(a,c,d)]                                  # outer skin
            F += [(a+off,c+off,b+off),(a+off,d+off,c+off)]          # inner skin (flipped)
        for j, s in ((0, 1), (n_z-1, -1)):                          # side walls
            a, b = idx(i,j), idx(i+1,j)
            q = [(a, a+off, b+off), (a, b+off, b)]
            F += q if s == 1 else [(x, z_, y) for x, y, z_ in q]
    F = np.array(F)
    if signed_volume(V, F) < 0: F = F[:, ::-1]
    return V, F

def signed_volume(V, F):   # sum of tetrahedra (origin, v1, v2, v3): V = Σ v1·(v2×v3)/6
    a, b, c = V[F[:,0]], V[F[:,1]], V[F[:,2]]
    return np.einsum("ij,ij->i", a, np.cross(b, c)).sum()/6

def edge_check(F):          # watertight <=> every edge shared by exactly 2 triangles
    e = np.sort(np.vstack([F[:,[0,1]], F[:,[1,2]], F[:,[2,0]]]), 1)
    _, counts = np.unique(e, axis=0, return_counts=True)
    return bool((counts == 2).all())

def write_stl(path, V, F):  # binary STL written by hand: 80-byte header, count, 50 bytes per triangle
    with open(path, "wb") as f:
        f.write(b"RingForge".ljust(80, b" ")); f.write(struct.pack("<I", len(F)))
        tri = V[F]; n = np.cross(tri[:,1]-tri[:,0], tri[:,2]-tri[:,0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        for k in range(len(F)):
            f.write(struct.pack("<12fH", *n[k], *tri[k].ravel(), 0))
