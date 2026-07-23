# Typography — Text, Fonts, Layout

> **Status:** Stub — geplant für Ausbau. Subagent #5 (Wave 1, 2026-07-03) hat diesen Link aus dem Original-SKILL.md übernommen, aber nicht ausgearbeitet.

## Inhalt (TODO)
- `textFont()`, `textSize()`, `textAlign()`, `textLeading()`
- Custom fonts: `loadFont()`, `textToPoints()` (1.x), `textToContours()` (2.0)
- Variable fonts (p5.js 2.0)
- Layout: `textWidth()`, `textBounds()`

## Quick Reference
- Alignment: `textAlign(CENTER, CENTER)`
- Bounds: `font.textBounds(str, x, y, size)` → bounding box for layout
- Outline: `font.textToPoints(str, x, y, size, density)` → point cloud