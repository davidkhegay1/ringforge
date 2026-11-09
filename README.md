# RingForge

**A ring design studio with its own 3D geometry engine.**

> 🚧 Work in progress. Open Source Software term project, Fall 2026. Planned release: December 5, 2026.

RingForge designs rings that can actually be made: choose a size, a profile, a surface
pattern and a gemstone setting, see the ring in 3D, get its metal weight, cost and stone
carat, and export a watertight STL file for 3D printing or wax casting. It can also merge
two reference ring photos into a new design, and merge designs the way you describe in
plain language.

![Prototype: prong, bezel and channel settings](docs/prototype_gems.png)

## Planned features

- Own geometry engine: signed distance fields + marching cubes, watertight STL export
- Gemstones: round brilliant stones with automatic seat cutting; prong, bezel and channel settings
- Ring sizes (US / Korean 호 / JP / mm), metal weight and cost, stone carat
- Pattern studio: grooves, hammered, Voronoi, engraved text, image relief
- `.ring` recipe language for sharing designs
- Merge and evolve designs; merge two reference photos into a new ring
- AI merge assistant: describe how to merge two designs ("stone from A, hammered band
  from B, 2 mm wide"); the AI writes a ring recipe that RingForge validates before
  building. Optional: needs a Claude API key, and the app works fully without it
- Thickness heatmap for manufacturability
- Web interface with live 3D preview

## Status

See [PROGRESS.md](PROGRESS.md) for the current stage and plan, and the full proposal:
[v2 (current)](docs/proposal/RingForge_Proposal_v2.pdf) ·
[v1](docs/proposal/RingForge_Proposal_v1.pdf).
Early experiments are kept in [`prototypes/`](prototypes/).

## AI assistance

This project is developed with the help of Claude (Anthropic) as a coding assistant.
All AI-assisted work is disclosed here and in commit messages. I review and test all code.

## References

To be completed as the project grows. Prior art: JewelCraft (Blender add-on, GPL-3; no
code used), OpenSCAD, build123d. Algorithms: Lorensen & Cline (1987) marching cubes;
Tolkowsky (1919) diamond proportions. Services: Claude API by Anthropic (optional AI
features).

- Inigo Quilez, "Distance functions" and "Smooth minimum", https://iquilezles.org/articles/
  (formulas for the rounded-box, segment / capsule and cylinder distances and the
  polynomial smooth minimum, re-derived and written from scratch in `ringforge/sdf.py`).
- Pappus' centroid theorem, used in the tests for the exact volume of the revolved band.

## License

MIT, see [LICENSE](LICENSE).
