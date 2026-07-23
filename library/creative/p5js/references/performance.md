# Performance & Profiling

## Disable FES First

The Friendly Error System (FES) adds up to 10x overhead. Disable it in every production sketch:

```javascript
p5.disableFriendlyErrors = true;  // BEFORE setup()

function setup() {
  pixelDensity(1);  // prevent 2x-4x overdraw on retina
  createCanvas(1920, 1080);
}
```

## Hot-Loop Math: Use Math.* Instead of p5 Wrappers

In hot loops (particles, pixel ops), use `Math.*` instead of p5 wrappers — measurably faster:

```javascript
// In draw() or update() hot paths:
let a = Math.sin(t);          // not sin(t)
let r = Math.sqrt(dx*dx+dy*dy); // not dist() — or better: skip sqrt, compare magSq
let v = Math.random();        // not random() — when seed not needed
let m = Math.min(a, b);       // not min(a, b)
```

Other JS-engine-friendly choices in hot paths:

- Avoid object allocation in tight loops (re-use `p5.Vector` objects, mutate in place)
- Prefer typed arrays (`Float32Array`) for large numeric buffers
- Use `const` over `let` where possible; helps V8 inline
- Avoid `array.filter` / `.map` in `draw()` — they allocate each frame

## Vectorize Where Possible

p5.js draw calls are expensive. For thousands of particles:

```javascript
// SLOW: individual shapes
for (let p of particles) {
  ellipse(p.x, p.y, p.size);
}

// FAST: single shape with beginShape()
beginShape(POINTS);
for (let p of particles) {
  vertex(p.x, p.y);
}
endShape();

// FASTEST: pixel buffer for massive counts
loadPixels();
for (let p of particles) {
  let idx = 4 * (floor(p.y) * width + floor(p.x));
  pixels[idx] = r; pixels[idx+1] = g; pixels[idx+2] = b; pixels[idx+3] = 255;
}
updatePixels();
```

For shapes other than points, the pattern is the same: one `beginShape()` / `endShape()` wrapping many `vertex()` calls beats many `ellipse()` / `line()` calls.

## Rule of Thumb Targets

| Metric | Target |
|--------|--------|
| Frame rate (interactive) | 60fps sustained |
| Frame rate (animated export) | 30fps minimum |
| Particle count (P2D shapes) | 5,000–10,000 at 60fps |
| Particle count (pixel buffer) | 50,000–100,000 at 60fps |
| Canvas resolution | Up to 3840×2160 (export), 1920×1080 (interactive) |
| File size (HTML) | < 100KB (excluding CDN libraries) |
| Load time | < 2s to first frame |

## Common Mistakes

- **`console.log()` inside `draw()`** — kills framerate, allocates strings, pollutes DevTools
- **DOM manipulation in `draw()`** — `select()` / `.html()` / `.style()` are expensive
- **`mouseMoved()` without throttling** — fires hundreds of times per second
- **`loadPixels()` every frame on a huge canvas** — copy cost is `4 * w * h` bytes
- **forgetting `noLoop()` for headless export** — see `references/sketches.md`
- **`push()` without matching `pop()`** — matrix stack overflow, transforms drift
- **Creating new objects in `draw()`** — V8's GC kicks in at the worst moment

## Profiling Workflow

1. Chrome DevTools → Performance tab → record 5 seconds
2. Look for long tasks > 16ms (= dropped frames)
3. Bottom-up view → sort by Self Time
4. Hot functions are usually in `draw()`, `update()`, or pixel loops
5. Fix the top 1–2 hotspots first; they usually account for >80% of frame time

## Memory Leak Patterns

- Event listeners added but never removed (`window.addEventListener` in setup without cleanup)
- `createGraphics()` buffers recreated each frame
- Captured closures holding references to large arrays
- Loaded images / fonts held when no longer needed

## Browser Compatibility Notes

- WebGL2 is universal in modern browsers; p5.js defaults to WebGL1 (compatible with more devices)
- `saveGif()` uses `MediaRecorder` + Web Workers — fails silently on Safari < 14
- Custom fonts via `loadFont()` need CORS-safe URLs; use `https://` Google Fonts or local server
- Pointer events: p5 mouse handlers don't always fire on touch+pen mixed devices — consider `pointerdown` listeners

See `references/troubleshooting.md` for the full gotcha catalog.