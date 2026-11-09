import json
from engine import *; from features import *; from merge import *
d = 11.63 + 0.8128*7
out = {}
for name, fn, W, T in [
    ("union_hv", union(hammered(), voronoi()), 4.0, 1.5),
    ("morph_gv", morph(grooves(), voronoi()), 4.0, 1.5)]:
    V, F = ring_mesh(d, W, T, fn, 720, 80); write_stl(name + ".stl", V, F)
    out[name] = (round(signed_volume(V, F), 1), edge_check(F))
for i, seed in enumerate((7, 21)):
    c = breed(A, B, seed); print("child", i+1, {k: round(v, 2) for k, v in c.items()})
    V, F = ring_mesh(d, c["width"], c["thick"], recipe_to_h(c, seed), 720, 80)
    write_stl(f"child{i+1}.stl", V, F); out[f"child{i+1}"] = (round(signed_volume(V, F), 1), edge_check(F))
print(out)
