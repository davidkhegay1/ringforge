"""Merging two ring designs. Because every design is a height map h(theta, z), merging = combining two functions."""
import numpy as np
from features import grooves, hammered, voronoi

def union(hA, hB):                      # keep every cut from both designs
    return lambda TH, Z, Ro: np.minimum(hA(TH, Z, Ro), hB(TH, Z, Ro))

def morph(hA, hB):                      # A on one side of the ring, smoothly turning into B on the other
    def h(TH, Z, Ro):
        a = (1 - np.cos(TH)) / 2        # 0 at theta=0 (pure A) -> 1 at theta=pi (pure B), seamless at 2*pi
        return (1 - a)*hA(TH, Z, Ro) + a*hB(TH, Z, Ro)
    return h

# "Breed": a design is a recipe (genes). A child takes each gene from a parent or between them, plus a small mutation.
A = {"width": 4.0, "thick": 1.5, "dents": 260, "dent_r": 1.1, "dent_depth": 0.18, "cells": 0,  "line": 0.28, "w_hammer": 1.0, "w_vor": 0.0}
B = {"width": 5.0, "thick": 1.8, "dents": 0,   "dent_r": 1.1, "dent_depth": 0.18, "cells": 70, "line": 0.28, "w_hammer": 0.0, "w_vor": 1.0}
INT = {"dents", "cells"}
def breed(a, b, seed):
    rng = np.random.default_rng(seed); child = {}
    for k in a:
        t = rng.uniform(0.2, 0.8)                              # crossover: somewhere between the parents
        v = (1-t)*a[k] + t*b[k]
        v *= rng.normal(1.0, 0.15)                             # mutation: about +/-15%
        child[k] = int(round(v)) if k in INT else float(v)
    child["dents"] = max(child["dents"], 40); child["cells"] = max(child["cells"], 12)
    return child

def recipe_to_h(r, seed=0):
    hh = hammered(r["dents"], r["dent_r"], r["dent_depth"], seed)
    hv = voronoi(r["cells"], r["line"], 0.35, seed + 1)
    return lambda TH, Z, Ro: r["w_hammer"]*hh(TH, Z, Ro) + r["w_vor"]*hv(TH, Z, Ro)
