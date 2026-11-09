# RingForge: rules for every Claude session

RingForge is David's Open Source Software term project: a web app that designs
manufacturable rings (bands, patterns, gemstones in prong / bezel / channel settings)
and exports watertight STL files, with weight, cost and carat estimates.
Deadline: Dec 6, 2026 23:59 (planned submission Dec 5). License: MIT.

## Start of every session

1. Read `PROGRESS.md`: current stage, what is done, what is next, known numbers.
2. Work only on the next unfinished stage unless David asks otherwise.

## How we work

- **Small steps.** Build one piece, run the tests, explain it, commit. Never one giant commit.
- **David must understand everything.** After each piece, explain it step by step with
  concrete numbers and an iteration table (or ask the `tutor` agent). He will be asked
  about this code by his professor.
- **End of every stage:** run the `geometry-verifier` and `code-reviewer` agents, fix what
  they find, then update `PROGRESS.md` and commit.
- **End of every session:** update `PROGRESS.md` (done / next / open problems) and push.
- **Before submission (and weekly as a dry run):** run the `submission-checker` agent.
- Commit messages: `area: what changed` (for example `engine: add marching cubes`), each
  ending with the Co-Authored-By trailer for Claude.

## Technical conventions

- Python 3.10+. Units are millimetres everywhere. Coordinates: finger axis = x, ring
  circle in the y-z plane, top of the ring (where the stone sits) at +z.
- Engine: signed distance fields (negative inside, positive outside), combined with
  min / max / smooth-min, turned into triangles with our own marching cubes.
  Gemstones are exact convex polyhedra and are exported separately from the metal.
- Every exported metal mesh must be watertight with positive volume (tested).
- Layout: `ringforge/` (package), `tests/`, `benchmarks/`, `docs/` (images, GIFs),
  `examples/` (`.ring` recipes and sample STLs), `app.py` (web UI; `--smoke` builds one
  ring and exits), `prototypes/` (early experiments, kept for history).

## Own code vs. libraries

- Written in this repo: SDF primitives and operations, marching cubes, gem polyhedra and
  seat cutters, settings, mesh checks, volume, STL writer, patterns, recipe language,
  merge / evolve, photo analyzer, thickness analysis.
- Allowed libraries: NumPy, SciPy (convex hull), Pillow, OpenCV (image loading and basic
  filters), Gradio, three.js, pytest. scikit-image and trimesh only in tests, as
  independent references.
- Anything adapted from elsewhere gets a source comment AND an entry in the README
  References. Never copy code from GPL projects (for example JewelCraft) into this MIT repo.
- Never commit API keys (`.env` is git-ignored) or user-uploaded photos.
