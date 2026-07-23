# Animation — Motion, Easing, Timing

> **Status:** Stub — geplant für Ausbau. Subagent #5 (Wave 1, 2026-07-03) hat diesen Link aus dem Original-SKILL.md übernommen, aber nicht ausgearbeitet.

## Inhalt (TODO)
- Frame-based vs time-based animation
- Easing functions: linear, ease-in-out, cubic-bezier, elastic
- Tweening libraries: p5.tween, gsap integration
- Loop patterns: ping-pong, accumulative, generative

## Quick Reference
- `frameCount`, `frameRate()`, `deltaTime`
- Easing: `easeInOutCubic(t) = t<0.5 ? 4*t³ : 1-(-2*t+2)³/2`
- Target frame rate: `frameRate(60)` for export stability