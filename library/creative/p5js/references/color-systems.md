# Color Systems — Palettes, Color Spaces, Theory

> **Status:** Stub — geplant für Ausbau. Subagent #5 (Wave 1, 2026-07-03) hat diesen Link aus dem Original-SKILL.md übernommen, aber nicht ausgearbeitet.

## Inhalt (TODO)
- Color spaces: RGB, HSB, HSL, OKLCH (p5.js 2.0)
- Palette generation: complementary, triadic, split-complementary
- Library palettes: coolors, colorhunt, paletton
- Contrast: WCAG AA/AAA, colorblind-safe palettes

## Quick Reference
- HSB: `colorMode(HSB, 360, 100, 100)`
- OKLCH (p5 2.0): `colorMode(OKLCH)`
- Random palette: `[...Array(5)].map(() => color(random(360), 80, 80))`