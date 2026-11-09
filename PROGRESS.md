# RingForge progress

_Last updated: Nov 9, 2026_

## Current stage

**Stage 0: repository setup.** Next: Stage 1 (engine with gems).

## Plan (revised Nov 9)

The professor approved the idea on Nov 9 and asked for gemstone support. The engine moves
from height maps to signed distance fields (SDF), which handle stones, prongs and
through-holes. Feature freeze moved from Nov 22 to Nov 26.

| Stage | Dates | Work | Status |
|---|---|---|---|
| 0 | Nov 9 – 10 | Repo, CLAUDE.md, agents, LICENSE, README skeleton, .gitignore, CI | in progress |
| 1 | Nov 10 – 13 | SDF engine, own marching cubes, gems (round brilliant), settings (prong, bezel, channel), sizes and metals, STL writer, tests | |
| 2 | Nov 14 – 17 | Patterns on SDF (grooves, hammered, Voronoi, text, image relief), `.ring` recipe language | |
| 3 | Nov 18 – 21 | Web UI with 3D preview, fast preview (coarse grid / octree), thickness heatmap | |
| 4 | Nov 22 – 26 | Photo merge analyzer (band + stone detection), merge / evolve. **Feature freeze Nov 26** | |
| 5 | Nov 27 – Dec 5 | Bug fixes, README with GIFs and benchmarks, real ring photo. **Submit Dec 5** | |

Only if time: couple rings, ring size from photo. Cut: AR try-on, mesh optimizer.

## David's tasks

- [ ] Connect GitHub to Claude, create the `ringforge` repo (Nov 9)
- [ ] Create the Claude Project "RingForge" with the proposal and instructions (Nov 9)
- [ ] Collect 20–30 ring photos (own or freely licensed; not committed to the repo) (by Nov 20)
- [ ] Order a resin 3D print of a RingForge solitaire (by Nov 21)
- [ ] Record demo GIFs (Nov 27 – Dec 3)

## Known numbers (from prototypes in `prototypes/`)

| Check | Value |
|---|---|
| Height-map engine, flat band US 7, 4 × 1.5 mm, N = 720 | 354.74 mm³ (exact 354.74), error 0.0013 % |
| SDF + marching cubes, rounded band 2.3 × 1.7 mm, 0.07 mm grid | −0.076 % vs exact 230.42 mm³ |
| Same band, 0.035 mm grid | −0.020 % |
| Solitaire, 6.5 mm stone, 6 prongs | metal 248.4 mm³ (3.88 g 18k), stone 1.04 ct (industry formula 1.02 ct), 33 s |
| Bezel + pierced band, 5 mm stone | metal 300.4 mm³ (4.69 g 18k), 19 s |
| Channel, 9 × 2 mm stones | metal 360.0 mm³ (5.62 g 18k), 49 s |

All prototype meshes were watertight. Prototype used scikit-image's marching cubes; Stage 1
replaces it with our own and keeps scikit-image as a test reference.

## Open problems

- SDF generation is slow (19–49 s). Plan: coarse preview grid + octree / narrow band.
- Marching cubes slightly rounds sharp metal edges (stones stay exact). Stretch: dual contouring.
- Prong positions in the prototype were hand-tuned; Stage 1 computes them from stone size.
- Patterns (height maps) on top of the SDF band are not tested yet.

## Decisions log

- Oct 28: idea chosen (RingForge), proposal written.
- Nov 9: professor approved; asked for gem support → engine switched to SDF + marching cubes.
