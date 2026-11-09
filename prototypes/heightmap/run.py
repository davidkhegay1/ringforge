import numpy as np, time, trimesh, math
from engine import *
from features import *
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
d = 11.63 + 0.8128*7; W, T = 4.0, 1.5
exact = math.pi*((d/2+T)**2-(d/2)**2)*W
print(f"US7 inner d = {d:.2f} mm, exact flat volume = {exact:.2f} mm3")
for n in (16, 64, 256, 720):
    V, F = ring_mesh(d, W, T, None, n_theta=n, n_z=2)
    v = signed_volume(V, F)
    print(f"  N={n:4d}: {len(F):6d} tris  volume={v:8.2f}  err={(exact-v)/exact*100:.4f}%  watertight={edge_check(F)}")
designs = {
  "grooves":  (grooves(), 720, 80),
  "hammered": (hammered(), 540, 60),
  "voronoi":  (voronoi(), 720, 80),
  "text":     (engrave_text("DAVID · 데이비드", FONT), 1440, 90),
}
for name, (fn, nt, nz) in designs.items():
    t = time.time(); V, F = ring_mesh(d, 6.0 if name=="text" else W, T, fn, nt, nz); dt = time.time()-t
    v = signed_volume(V, F); tm = trimesh.Trimesh(V, F, process=False)
    write_stl(f"{name}.stl", V, F)
    print(f"{name:8s}: {len(F):7d} tris  vol={v:7.1f} mm3 ({v/1000*10.36:.2f} g silver)  mine_watertight={edge_check(F)}  trimesh: watertight={tm.is_watertight} vol={tm.volume:.1f}  build={dt:.1f}s")
