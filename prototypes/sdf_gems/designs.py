import numpy as np, time, json
from sdf import *
Ri = (11.63 + 0.8128 * 7) / 2              # US 7 -> inner radius 8.66 mm
out = {}

def save(name, metal_f, lo, hi, gems, step=0.07):
    t = time.time(); V, F = mesh_sdf(metal_f, lo, hi, step); dt = time.time() - t
    write_stl(f"{name}_metal.stl", V, F)
    gv, gf, off = [], [], 0
    for GV, GF in gems: gv.append(GV); gf.append(GF + off); off += len(GV)
    if gems: write_stl(f"{name}_gems.stl", np.vstack(gv), np.vstack(gf))
    vol = signed_volume(V, F)
    out[name] = dict(tris=len(F), metal_mm3=round(vol, 1), g_18k=round(vol / 1000 * 15.6, 2),
                     g_silver=round(vol / 1000 * 10.36, 2), watertight=edge_check(F), seconds=round(dt, 1))
    print(name, out[name])

# ===== 1) Solitaire: 6.5 mm round brilliant in a 6-prong head =====
D = 6.5; GV, GF, planes, gi = brilliant(D)
t, w = 1.7, 2.3; Ro = Ri + t
gz = Ro + 0.35 - gi["bottom"]             # culet floats 0.35 mm above the band
fr = frame((0, 0, gz), (0, 0, 1))
prongs = []
for k in range(6):
    a = np.pi / 6 + k * np.pi / 3
    by = 1.7 * np.sin(a); B = (0.55 * np.cos(a), by, np.sqrt(Ro**2 - by**2) - 0.35)
    M = ((gi["R"] + 0.12) * np.cos(a), (gi["R"] + 0.12) * np.sin(a), gz)
    T = ((gi["R"] - 0.3) * np.cos(a), (gi["R"] - 0.3) * np.sin(a), gz + gi["top"] * 0.55)
    prongs.append((np.array(B), np.array(M), np.array(T)))
zr = gz + gi["bottom"] * 0.55              # gallery rail height
rail = [B + (M - B) * (zr - B[2]) / (M[2] - B[2]) for B, M, _ in prongs]
def solitaire(P):
    d = band(P, Ri, t, w)
    for B, M, T in prongs:
        d = smin(d, np.minimum(capsule(P, B, M, 0.42), capsule(P, M, T, 0.38)), 0.5)
    for k in range(6):
        d = smin(d, capsule(P, rail[k], rail[(k + 1) % 6], 0.3), 0.3)
    return subtract(d, gem_sdf(to_local(P, fr), planes, 0.04))   # seat cut = the stone itself
save("solitaire", solitaire, (-4.6, -11, -11), (4.6, 11, gz + gi["top"] + 0.6),
     [(to_world(GV, fr), GF)])
gem_mm3 = signed_volume(GV, GF); out["solitaire"]["stone_ct"] = round(gem_mm3 / 1000 * 3.52 / 0.2, 2)
out["solitaire"]["stone_formula_ct"] = round(D**2 * (gi["top"] - gi["bottom"]) * 0.0061, 2)

# ===== 2) Bezel: 5 mm stone in a bezel, light hole + pierced band (through-holes) =====
D2 = 5.0; GV2, GF2, pl2, g2 = brilliant(D2)
t2, w2 = 1.6, 3.0; Ro2 = Ri + t2
gz2 = Ro2 + 0.1 - g2["bottom"] - 0.9      # stone sinks partly into the band
fr2 = frame((0, 0, gz2), (0, 0, 1)); lip = gz2 + g2["top"] * 0.35
def bezel(P):
    d = band(P, Ri, t2, w2)
    tube = cylinder(P, np.array([0, 0, (Ro2 - 1.0 + lip) / 2]), (0, 0, 1), g2["R"] + 0.55, (lip - (Ro2 - 1.0)) / 2)
    d = smin(d, tube, 0.6)
    L = to_local(P, fr2)
    cut = np.minimum(gem_sdf(L, pl2, 0.04),
                     cylinder(L, np.array([0, 0, g2["top"] + 1]), (0, 0, 1), g2["R"] * 0.92, 1.5))  # opening, lip holds girdle
    cut = np.minimum(cut, cylinder(P, np.array([0, 0, Ro2 - 1]), (0, 0, 1), 1.3, 2.5))           # light hole
    d = subtract(d, cut)
    for k in range(11):                                              # pierced holes along the bottom half
        a = np.pi + (k - 5) * 0.2
        d = subtract(d, cylinder(P, np.array([0, (Ri + t2 / 2) * np.sin(a), (Ri + t2 / 2) * np.cos(a)]),
                                 (0, np.sin(a), np.cos(a)), 0.55, 2))
    return d
save("bezel", bezel, (-3.4, -11, -11), (3.4, 11, lip + 0.6), [(to_world(GV2, fr2), GF2)])

# ===== 3) Channel half-eternity: 9 x 2.0 mm stones =====
D3 = 2.0; GV3, GF3, pl3, g3 = brilliant(D3)
t3, w3 = 2.0, 3.2; Ro3 = Ri + t3
step_a = (D3 + 0.2) / (Ro3 - 0.3)
frames = []
for k in range(9):
    a = (k - 4) * step_a                                              # angle from the top
    up = np.array([0, np.sin(a), np.cos(a)])
    frames.append(frame(up * (Ro3 - 0.08 - g3["top"]), up))
def channel(P):
    d = band(P, Ri, t3, w3)
    cut = np.full(P.shape[:-1], 1e9, np.float32)
    for fr3 in frames:
        L = to_local(P, fr3)
        c = np.minimum(gem_sdf(L, pl3, 0.03), cylinder(L, np.array([0, 0, g3["top"] + 0.6]), (0, 0, 1), g3["R"] * 0.86, 0.75))
        c = np.minimum(c, cylinder(L, np.array([0, 0, -1.5]), (0, 0, 1), 0.45, 1.6))   # light hole through the band
        cut = np.minimum(cut, c)
    return subtract(d, cut)
save("channel", channel, (-1.9, -11, -11), (1.9, 11, 11), [(to_world(GV3, f), GF3) for f in frames])
json.dump(out, open("results.json", "w"), indent=1)

# ===== accuracy check: plain rounded band vs. exact Pappus volume =====
for step in (0.14, 0.07, 0.035):
    V, F = mesh_sdf(lambda P: band(P, Ri, 1.7, 2.3), (-1.4, -10.6, -10.6), (1.4, 10.6, 10.6), step)
    exact = 2 * np.pi * (Ri + 0.85) * (1.7 * 2.3 - (4 - np.pi) * 0.25**2)
    print(f"band step={step}: MC={signed_volume(V, F):.2f} exact={exact:.2f} err={(signed_volume(V, F) - exact) / exact * 100:+.3f}% tris={len(F)}")
