# WebGL, 3D & Shaders

## WebGL Mode Gotchas

- `createCanvas(w, h, WEBGL)` — origin is center, not top-left
- Y-axis is inverted (positive Y goes up in WEBGL, down in P2D)
- `translate(-width/2, -height/2)` to get P2D-like coordinates
- `push()`/`pop()` around every transform — matrix stack overflows silently
- `texture()` before `rect()`/`plane()` — not after
- Custom shaders: `createShader(vert, frag)` — test on multiple browsers

## Instance Mode for Multiple Sketches

Global mode pollutes `window`. For production, use instance mode:

```javascript
const sketch = (p) => {
  p.setup = function() {
    p.createCanvas(800, 800);
  };
  p.draw = function() {
    p.background(0);
    p.ellipse(p.mouseX, p.mouseY, 50);
  };
};
new p5(sketch, 'canvas-container');
```

Required when embedding multiple sketches on one page or integrating with frameworks.

## Shaders (GLSL)

p5.js supports two shader flavors:

- **Material shaders** — wrap 3D geometry. Override vertex/fragment transforms on `createShape()` or built-in primitives.
- **Filter shaders** — post-processing pass over the canvas. `createFilterShader(vert, frag)` + `filter(shader)`.

### Custom Shader Skeleton

```javascript
let theShader;

function preload() {
  theShader = loadShader('shader.vert', 'shader.frag');
}

function setup() {
  createCanvas(800, 800, WEBGL);
  shader(theShader);  // applied to next shape, or use filter() for post
}

function draw() {
  theShader.setUniform('uTime', millis() / 1000.0);
  theShader.setUniform('uResolution', [width, height]);
  background(0);
  rect(0, 0, width, height);
}
```

### Filter Shader (post-processing)

```javascript
let blurShader;

function preload() {
  blurShader = loadShader('blur.vert', 'blur.frag');
}

function draw() {
  // ... draw scene to canvas ...
  filter(blurShader);
}
```

## 3D Primitives Cheat-Sheet

| Primitive | Notes |
|-----------|-------|
| `box(w, h, d)` | rectangular solid |
| `sphere(r)` | UV sphere, segments controllable |
| `cone(r, h)` | cone |
| `cylinder(r, h)` | cylinder |
| `torus(r, tubeR)` | torus |
| `plane(w, h)` | flat plane, useful for shader textures |
| `ellipsoid(r1, r2, r3)` | scaled sphere |

## Lighting Models

```javascript
ambientLight(50);                    // soft fill
directionalLight(255, 255, 255, 0, -1, 0);  // key light from above
pointLight(255, 0, 0, mouseX-width/2, mouseY-height/2, 100);  // colored point
material.setSpecular(color(255));    // shiny
material.setMetalness(0.8);          // 2.x: PBR
```

## Camera & OrbitControl

```javascript
function draw() {
  orbitControl();           // mouse-drag to orbit; wheel to zoom
  background(50);
  lights();
  rotateY(frameCount * 0.01);
  box(100);
}
```