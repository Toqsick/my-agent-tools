# Visual Effects — Particles, Texture, Image Processing

> **Status:** Stub — geplant für Ausbau. Subagent #5 (Wave 1, 2026-07-03) hat diesen Link aus dem Original-SKILL.md übernommen, aber nicht ausgearbeitet.

## Inhalt (TODO)
- Particle systems (boids, curl noise, flow fields)
- Texture overlays (p5.grain, procedural noise)
- Image processing (filter chains, pixel manipulation)
- Post-processing effects (bloom, chromatic aberration, displacement)

## Quick Reference
- Particle class: position, velocity, acceleration, lifespan
- Flow field: `noise(x*0.01, y*0.01, t*0.01) * TAU * 2`
- Image: `loadImage()`, `filter(BLUR)`, `get()/set()` for pixels