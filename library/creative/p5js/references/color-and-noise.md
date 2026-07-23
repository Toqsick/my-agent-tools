# Color, Noise & Math Foundations

## Color Mode — Use HSB

HSB (Hue, Saturation, Brightness) is dramatically easier to work with than RGB for generative art:

```javascript
colorMode(HSB, 360, 100, 100, 100);
// Now: fill(hue, sat, bri, alpha)
// Rotate hue: fill((baseHue + offset) % 360, 80, 90)
// Desaturate: fill(hue, sat * 0.3, bri)
// Darken: fill(hue, sat, bri * 0.5)
```

Never hardcode raw RGB values. Define a palette object, derive variations procedurally. See `references/color-systems.md`.

### Palette Object Convention

```javascript
const PALETTE = {
  bg: '#0a0a0f',
  ink: '#e8d5b7',
  accent: '#c9462d',
  shadow: '#1a1a26',
};

function setup() {
  colorMode(HSB, 360, 100, 100, 100);
}

// Derive variations
function tint(base, dhue, dsat, dbri) {
  let c = color(base);                       // accepts hex string
  let h = hue(c) + dhue;
  let s = saturation(c) + dsat;
  let b = brightness(c) + dbri;
  return color((h+360)%360, constrain(s,0,100), constrain(b,0,100));
}
```

### Palette Generators

- **Complementary**: hue + 180°
- **Analogous**: hue ± 30°
- **Triadic**: hue + 0°, +120°, +240°
- **Monochrome**: same hue, vary saturation/brightness
- **Procedural harmony**: seed-driven selection from curated library

## Noise — Multi-Octave, Not Raw

Raw `noise(x, y)` looks like smooth blobs. Layer octaves for natural texture:

```javascript
function fbm(x, y, octaves = 4) {
  let val = 0, amp = 1, freq = 1, sum = 0;
  for (let i = 0; i < octaves; i++) {
    val += noise(x * freq, y * freq) * amp;
    sum += amp;
    amp *= 0.5;
    freq *= 2;
  }
  return val / sum;
}
```

For flowing organic forms, use **domain warping** — feed noise output back as noise input coordinates:

```javascript
function warped(x, y) {
  let q1 = fbm(x, y);
  let q2 = fbm(x + 5.2, y + 1.3);
  return fbm(x + 4.0 * q1, y + 4.0 * q2);
}
```

Domain warp produces the characteristic "ink in water" or "marbled" look.

For **flow-field following**, sample noise gradient to get a vector direction:

```javascript
function flowAngle(x, y, t) {
  let n = noise(x * 0.01, y * 0.01, t * 0.001);
  return n * TAU * 2;  // rotate 2 full turns across noise range
}
```

For **curl noise** (incompressible flow — particles don't bunch up), take perpendicular gradients:

```javascript
function curl(x, y) {
  let eps = 0.01;
  let n1 = noise(x, y + eps);
  let n2 = noise(x, y - eps);
  let n3 = noise(x + eps, y);
  let n4 = noise(x - eps, y);
  let dx = (n1 - n2) / (2 * eps);
  let dy = (n3 - n4) / (2 * eps);
  return { x: dy, y: -dx };  // perpendicular to gradient
}
```

## p5.Vector Essentials

```javascript
let v = createVector(1, 2, 3);
v.add(u);                    // v += u
v.mult(0.5);                 // v *= 0.5
v.normalize();               // unit length
v.limit(5);                  // clamp magnitude
v.setMag(3);                 // set magnitude
v.lerp(u, 0.1);              // ease toward u

let m = v.mag();             // length
let mSq = v.magSq();         // squared length — cheaper for comparisons
let d = v.dist(u);           // distance to u

v.heading();                 // angle (2D)
v.rotate(angle);             // rotate by angle
```

**Performance tip**: prefer `magSq()` over `mag()` when comparing distances — avoids the sqrt. Compare against `d * d` instead of `d`.

## Easing & Interpolation

```javascript
// Linear (boring)
let x = lerp(a, b, t);

// Smoothstep (soft ends)
function smoothstep(a, b, t) {
  t = constrain((t - a) / (b - a), 0, 1);
  return t * t * (3 - 2 * t);
}

// Cubic ease-in-out
function easeInOutCubic(t) {
  return t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3) / 2;
}

// Spring (no overshoot, settles)
function spring(current, target, vel, k = 0.1, d = 0.8) {
  let force = (target - current) * k;
  vel = (vel + force) * d;
  return { value: current + vel, vel };
}
```

## Map & Constrain

```javascript
let y = map(value, 0, 1, 100, 300);     // remap range
y = constrain(y, 0, height);             // clamp
let n = norm(x, 0, width);               // 0..1 normalized position
```

## Trig Quick-Reference

| Need | Use |
|------|-----|
| Full circle | `TAU` (= 2π) |
| Quarter | `HALF_PI` |
| Oscillate | `sin(t)` returns -1..1 |
| One-shot pulse | `pow(sin(t), 8)` — sharp peak |
| Pendulum | `sin(t)` |
| Cycle without restart | `(t * speed) % TAU` |
| Random angle | `random(TAU)` |
| Lerp angle (shortest path) | custom `lerpAngle(a, b, t)` wrapping `((b-a+PI)%TAU) - PI` |