# RingForge progress

_Last updated: Nov 9, 2026_

## Current stage

**Stage 1 in progress** (SDF engine with gems). Stage 0 is done.

### Stage 1 steps

| Step | Work | Status |
|---|---|---|
| 1.1 | SDF primitives (sphere, band, capsule, cylinder) and operations (union, intersect, subtract, smooth union); grid sampling and grid volume estimate (`ringforge/sdf.py`, `ringforge/grid.py`) | done Nov 9 (PR) |
| 1.2 | Own marching cubes (scikit-image as test reference) | next |
| 1.3 | Mesh checks: signed volume, watertight edge check, binary STL writer | |
| 1.4 | Round brilliant gem polyhedron, carat estimate, seat cutter | |
| 1.5 | Settings: prong (positions from stone size), bezel, channel | |
| 1.6 | Ring sizes (US / KR / JP / mm) and metals (weight, cost) | |
| 1.7 | Stage review (geometry-verifier, code-reviewer), fixes | |

## Plan (revised Nov 9)

The professor approved the idea on Nov 9 and asked for gemstone support. The engine moves
from height maps to signed distance fields (SDF), which handle stones, prongs and
through-holes. Feature freeze moved from Nov 22 to Nov 26. Also added on Nov 9: the
**AI merge assistant** (David's request). The full plan is in
`docs/proposal/RingForge_Proposal_v2.pdf`.

| Stage | Dates | Work | Status |
|---|---|---|---|
| 0 | Nov 9 – 10 | Repo, CLAUDE.md, agents, LICENSE, README skeleton, .gitignore, CI | done Nov 9 |
| 1 | Nov 10 – 13 | SDF engine, own marching cubes, gems (round brilliant), settings (prong, bezel, channel), sizes and metals, STL writer, tests | |
| 2 | Nov 14 – 17 | Patterns on SDF (grooves, hammered, Voronoi, text, image relief), `.ring` recipe language, merge / evolve (union, morph, breed) | |
| 3 | Nov 18 – 21 | Web UI with 3D preview, fast preview (coarse grid / octree), thickness heatmap | |
| 4 | Nov 22 – 26 | Photo merge analyzer (band + stone detection), AI merge assistant. **Feature freeze Nov 26** | |
| 5 | Nov 27 – Dec 5 | Bug fixes, README with GIFs and benchmarks, real ring photo. **Submit Dec 5** | |

### AI merge assistant (Stage 4)

The user writes how two designs should be merged ("stone from A, hammered band from B,
2 mm wide"). The AI (Claude API) gets the recipe grammar, recipe A, recipe B and the
instruction, and must reply with a recipe only. The recipe parser validates syntax and
manufacturing rules; on an error, the message goes back to the AI (at most 2 retries).
The user sees the merged recipe and the changes vs. A and B, and can edit it before
building. Without `ANTHROPIC_API_KEY` the assistant is hidden; manual merge still works.
Targets: ≥ 90 % of 20 test instructions give a valid ring within 2 retries; 0 invalid
recipes reach the engine. Tests must not call the real API (use a fake model).

Only if time: couple rings, ring size from photo. Cut: AR try-on, mesh optimizer.

## David's tasks

- [x] Connect GitHub to Claude, create the `ringforge` repo (Nov 9)
- [x] Create the Claude Project "RingForge" with the proposal and instructions (Nov 9)
- [ ] Collect 20–30 ring photos (own or freely licensed; not committed to the repo) (by Nov 20)
- [ ] Order a resin 3D print of a RingForge solitaire (by Nov 21)
- [ ] Create a Claude API key in the Claude Console for the AI features; keep it in `.env`, never commit it (by Nov 21)
- [ ] Record demo GIFs (Nov 27 – Dec 3)

## Known numbers (from prototypes in `prototypes/`)

| Check | Value |
|---|---|
| Height-map engine, flat band US 7, 4 × 1.5 mm, N = 720 | 354.74 mm³ (exact 354.74), error 0.0013 % |
| SDF + marching cubes, rounded band 2.3 × 1.7 mm, 0.07 mm grid | −0.076 % vs exact 230.42 mm³ |
| Same band, 0.035 mm grid | −0.020 % |
| Stage 1.1: same band, grid volume estimate Σ clamp(0.5 − d/s, 0, 1)·s³ | +0.149 % (0.14 mm), +0.026 % (0.07 mm), +0.007 % (0.035 mm) |
| Stage 1.1: same band, naive inside-point count | +2.89 % / +0.49 % / −0.82 % (jumps with grid alignment) |
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
- Grid sampling evaluates every point; 0.035 mm band grid (81 × 607 × 607 = 30 M points)
  takes 1.5 s for the plain band. Gems with many planes will be slower (octree later).

## Decisions log

- Oct 28: idea chosen (RingForge), proposal written.
- Nov 9: professor approved; asked for gem support → engine switched to SDF + marching cubes.
- Nov 9: added the AI merge assistant (Stage 4); merge / evolve moved to Stage 2 to balance
  the stages; proposal v2 written (`docs/proposal/`).
