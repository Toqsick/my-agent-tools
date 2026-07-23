# Export Pipeline — PNG, GIF, MP4, SVG

> **Status:** Stub — geplant für Ausbau. Subagent #5 (Wave 1, 2026-07-03) hat diesen Link aus dem Original-SKILL.md übernommen, aber nicht ausgearbeitet.

## Inhalt (TODO)
- PNG: `saveCanvas(name, 'png')`
- GIF: `saveGif(name, duration, { delay, units })` — p5.js 1.x
- MP4: `saveFrames()` + ffmpeg concat
- WebM: CCapture.js
- Headless batch: Puppeteer + Node
- SVG: p5.js-svg (optional)

## Quick Reference
- PNG: `saveCanvas('sketch', 'png')`
- GIF: `saveGif('sketch', 5)` — 5s loop
- MP4: `ffmpeg -framerate 60 -i frame_%05d.png -c:v libx264 out.mp4`