# Troubleshooting — Common p5.js Issues & Fixes

> **Status:** Stub — geplant für Ausbau. Subagent #5 (Wave 1, 2026-07-03) hat diesen Link aus dem Original-SKILL.md übernommen, aber nicht ausgearbeitet.

## Inhalt (TODO)
- CORS issues with `loadImage()` from external URLs
- WebGL context lost on tab switch
- Performance: too many particles, GPU stalls
- `requestAnimationFrame` loop conflicts
- Browser autoplay policies for audio
- Memory leaks with `loadSound`

## Quick Reference
- CORS: use `mode: 'cors'` and CORS-enabled server
- WebGL recovery: bind `webglcontextlost` event
- Audio unlock: require user gesture before `new p5.AudioIn()`