# Core API — p5.js 1.x vs 2.x Reference

> **Status:** Stub — geplant für Ausbau. Subagent #5 (Wave 1, 2026-07-03) hat diesen Link aus dem Original-SKILL.md übernommen, aber nicht ausgearbeitet.

## Inhalt (TODO)
- p5.js 1.11.3 (default) — full API surface
- p5.js 2.0 — neue Features: `async setup()`, OKLCH color, `splineVertex()`, shader `.modify()`, variable fonts, `textToContours()`
- Globals: `setup()`, `draw()`, `preload()`, `mousePressed()`, `keyPressed()`
- Modes: instance mode vs global mode

## Quick Reference (1.x vs 2.x)
| Feature | 1.11.3 | 2.0 |
|---|---|---|
| `setup()` | sync | sync + async |
| Color | RGB, HSB | RGB, HSB, **OKLCH** |
| Curves | `bezierVertex`, `quadraticVertex` | + `splineVertex` |
| Shaders | `createShader` | + `.modify()` |
| Fonts | Static | + variable fonts, `textToContours` |