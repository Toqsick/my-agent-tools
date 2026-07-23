# Sketch Scaffold & Conventions

## Single-HTML Skeleton

Every sketch is one self-contained HTML file. No build step, no bundler, no server required for vanilla sketches. CDN libraries pulled in via `<script>` tags.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Project Name</title>
  <script>p5.disableFriendlyErrors = true;</script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.11.3/p5.min.js"></script>
  <!-- <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.11.3/addons/p5.sound.min.js"></script> -->
  <!-- <script src="https://unpkg.com/p5.js-svg@1.6.0"></script> -->  <!-- SVG export -->
  <!-- <script src="https://cdn.jsdelivr.net/npm/ccapture.js-npmfixed/build/CCapture.all.min.js"></script> -->  <!-- video capture -->
  <style>
    html, body { margin: 0; padding: 0; overflow: hidden; }
    canvas { display: block; }
  </style>
</head>
<body>
<script>
// === Configuration ===
const CONFIG = {
  seed: 42,
  // ... project-specific params
};

// === Color Palette ===
const PALETTE = {
  bg: '#0a0a0f',
  primary: '#e8d5b7',
  // ...
};

// === Global State ===
let particles = [];

// === Preload (fonts, images, data) ===
function preload() {
  // font = loadFont('...');
}

// === Setup ===
function setup() {
  createCanvas(1920, 1080);
  randomSeed(CONFIG.seed);
  noiseSeed(CONFIG.seed);
  colorMode(HSB, 360, 100, 100, 100);
  // Initialize state...
}

// === Draw Loop ===
function draw() {
  // Render frame...
}

// === Helper Functions ===
// ...

// === Classes ===
class Particle {
  // ...
}

// === Event Handlers ===
function mousePressed() { /* ... */ }
function keyPressed() { /* ... */ }
function windowResized() { resizeCanvas(windowWidth, windowHeight); }
</script>
</body>
</html>
```

## Implementation Patterns

- **Seeded randomness**: Always `randomSeed()` + `noiseSeed()` for reproducibility
- **Color mode**: Use `colorMode(HSB, 360, 100, 100, 100)` for intuitive color control
- **State separation**: CONFIG for parameters, PALETTE for colors, globals for mutable state
- **Class-based entities**: Particles, agents, shapes as classes with `update()` + `display()` methods
- **Offscreen buffers**: `createGraphics()` for layered composition, trails, masks

## Standard Key Bindings

Every sketch should include these in `keyPressed()`:

```javascript
function keyPressed() {
  if (key === 's' || key === 'S') saveCanvas('output', 'png');
  if (key === 'g' || key === 'G') saveGif('output', 5);
  if (key === 'r' || key === 'R') { randomSeed(millis()); noiseSeed(millis()); }
  if (key === ' ') CONFIG.paused = !CONFIG.paused;
}
```

## Headless Video Export — noLoop() Required

For headless rendering via Puppeteer, the sketch **must** use `noLoop()` in setup. Without it, p5's draw loop runs freely while screenshots are slow — the sketch races ahead and you get skipped/duplicate frames.

```javascript
function setup() {
  createCanvas(1920, 1080);
  pixelDensity(1);
  noLoop();                    // capture script controls frame advance
  window._p5Ready = true;      // signal readiness to capture script
}
```

The bundled `scripts/export-frames.js` detects `_p5Ready` and calls `redraw()` once per capture for exact 1:1 frame correspondence. See `references/export-pipeline.md` § Deterministic Capture.

For multi-scene videos, use the per-clip architecture: one HTML per scene, render independently, stitch with `ffmpeg -f concat`. See `references/export-pipeline.md` § Per-Clip Architecture.

## File Structure Conventions

```
project/
├── sketch.html           # the sketch
├── index.html            # viewer wrapper (optional, see templates/viewer.html)
├── assets/               # fonts, images, data files
└── output/               # exported PNGs, GIFs, MP4s
```