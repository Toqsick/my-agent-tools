# Shapes & Geometry — SDF, SVG Paths, Vectors

> **Status:** Stub — geplant für Ausbau. Subagent #5 (Wave 1, 2026-07-03) hat diesen Link aus dem Original-SKILL.md übernommen, aber nicht ausgearbeitet.

## Inhalt (TODO)
- 2D primitives: `rect()`, `ellipse()`, `triangle()`, `arc()`
- 3D primitives: `box()`, `sphere()`, `cylinder()`, `cone()`, `torus()`, `plane()`
- Custom shapes: `beginShape()`, `vertex()`, `endShape(CLOSE)`
- SDF (Signed Distance Functions) for raymarching
- SVG paths: `loadSVG()` from p5.js-svg

## Quick Reference
- Bezier: `bezier(x1,y1, cx1,cy1, cx2,cy2, x2,y2)`
- Curve: `curve(x1,y1, x2,y2, x3,y3, x4,y4)` — Catmull-Rom
- Vertex modes: `LINES`, `TRIANGLES`, `TRIANGLE_STRIP`, `QUADS`