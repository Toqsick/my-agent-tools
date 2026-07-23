# Interaction, Audio & Generative-Platform Patterns

## Mouse / Keyboard / Touch

p5 provides global event handlers:

```javascript
function mousePressed()  { /* fires on press */ }
function mouseReleased() { /* fires on release */ }
function mouseDragged()  { /* fires while dragging */ }
function mouseMoved()    { /* fires on any motion (expensive!) */ }
function keyPressed()    { /* fires on key down */ }
function keyReleased()   { /* fires on key up */ }
function touchStarted()  /* mobile */ }
function touchMoved()    /* mobile */ }

function keyPressed() {
  if (key === ' ') CONFIG.paused = !CONFIG.paused;
  if (key === 'r') { randomSeed(millis()); noiseSeed(millis()); }
}
```

Global state at any moment: `mouseX`, `mouseY`, `mouseIsPressed`, `pmouseX`, `pmouseY`, `key`, `keyCode`, `keyIsPressed`, `touches[]`.

## DOM Controls

```javascript
let slider = createSlider(0, 100, 50);
slider.input(() => CONFIG.amount = slider.value());

let btn = createButton('regenerate');
btn.mousePressed(() => reseed());

let input = createInput('seed');
input.input(() => { CONFIG.seed = int(input.value()); regenerate(); });
```

## Audio Reactivity (p5.sound)

```javascript
let mic, fft, amp;

function setup() {
  createCanvas(800, 800);
  mic = new p5.AudioIn();
  mic.start();

  fft = new p5.FFT();
  fft.setInput(mic);

  amp = new p5.Amplitude();
  amp.setInput(mic);
}

function draw() {
  let spectrum = fft.analyze();       // 1024-length Uint8Array
  let bass = fft.getEnergy('bass');   // band shorthand
  let level = amp.getLevel();         // 0..1 RMS

  // Drive visuals:
  let r = map(bass, 0, 255, 20, 200);
  ellipse(width/2, height/2, r);
}
```

**Browser autoplay rule**: `mic.start()` and any audio playback must follow a user gesture. Always start audio in `mousePressed()` / `keyPressed()`, not `setup()`.

## Scroll-Driven Animation

```javascript
let scrollY = 0;
window.addEventListener('scroll', () => {
  scrollY = window.scrollY;
});

function draw() {
  let t = scrollY * 0.001;
  // Drive visuals from t...
}
```

## Generative-Art Platform Support (fxhash / Art Blocks)

For generative art platforms, replace p5's PRNG with the platform's deterministic random:

```javascript
// fxhash convention
const SEED = $fx.hash;              // unique per mint
const rng = $fx.rand;               // deterministic PRNG
$fx.features({ palette: 'warm', complexity: 'high' });

// In setup():
randomSeed(SEED);   // for p5's noise()
noiseSeed(SEED);

// Replace random() with rng() for platform determinism
let x = rng() * width;  // instead of random(width)
```

See `references/export-pipeline.md` § Platform Export.

## CreateGraphics() for Layers

Flat single-pass rendering looks flat. Use offscreen buffers for composition:

```javascript
let bgLayer, fgLayer, trailLayer;

function setup() {
  createCanvas(1920, 1080);
  bgLayer = createGraphics(width, height);
  fgLayer = createGraphics(width, height);
  trailLayer = createGraphics(width, height);
}

function draw() {
  renderBackground(bgLayer);
  renderTrails(trailLayer);   // persistent, fading
  renderForeground(fgLayer);  // cleared each frame
  image(bgLayer, 0, 0);
  image(trailLayer, 0, 0);
  image(fgLayer, 0, 0);
}
```

For **trails**, draw a translucent rectangle over the trail layer each frame instead of clearing it:

```javascript
trailLayer.noStroke();
trailLayer.fill(0, 0, 0, 8);  // low alpha = slow fade
trailLayer.rect(0, 0, width, height);
```

For **masks**, render the mask shape to a buffer in white-on-black, then `mask()` the target image with it.

## Responsive Canvas

```javascript
function setup() {
  createCanvas(windowWidth, windowHeight);
}

function windowResized() {
  resizeCanvas(windowWidth, windowHeight);
}
```

For pixel-density concerns on retina, set `pixelDensity(1)` in setup to prevent 2x–4x overdraw.