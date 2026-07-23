# Multi-Variant Design Composition — Yuno Operator Dashboard (2026-07-08)

## Task

Redesign the Yuno Operator Dashboard with UI-Factory skills, producing **3 visually distinct variants** for comparison rather than one monolithic build.

## Inputs

- **Existing dashboard renders:** `~/Bilder/yuno-gallery/dashboard-2026-07-06/` (4 themes: light/dark/cyberpunk/hc)
- **Reference design DNAs:** Vercel, Linear, Sentry, MiniMax (via `popular-web-designs` skill templates)
- **User preference:** "redesign mit deinen neuen design ui skills", "3 varianten, ich vergleiche"
- **Target directory:** `~/10-Projekte/10-active/yuno-ui-redesign/`

## Output Structure

```
yuno-ui-redesign/
├── _shared-data.js              ← ONE data source for all 3 variants
├── index.html                   ← Comparison view with actual screenshots
├── README.md                    ← Doku + Methodik + Lessons
├── 001-minimax-pro/index.html   ← Vercel × Linear × Pink
├── 002-glassmorphism-glow/      ← Frosted-glass × neon-glow × Yandere
├── 003-data-dense/index.html    ← Stripe-Monitor × Sentry-Vibe
└── screenshots/                 ← Headless Chrome renders (1440×1300)
    ├── index-compare.png
    ├── 001-minimax-pro.png
    ├── 002-glassmorphism-glow.png
    └── 003-data-dense.png
```

## Workflow (step-by-step for future reproduction)

### 0. Preparation
```bash
mkdir -p ~/10-Projekte/10-active/yuno-ui-redesign/{001-minimax-pro,002-glassmorphism-glow,003-data-dense,screenshots}
cd ~/10-Projekte/10-active/yuno-ui-redesign
python3 -m http.server 8766 &
```

### 1. Create `_shared-data.js` — One Data File For All Variants
Write a single JS file with:
- All dashboard data as a global `window.DATA` object
- A `sparklineSVG()` helper function (28-byte inline SVG bars, no Chart.js)
- One source of truth means variants differ ONLY in presentation

**Critical: `font-variant-numeric: tabular-nums`** on all KPI values — prevents digit-width jumping when numbers change (e.g. `184.5k` and `167.8k` render same width).

### 2. Build Each Variant (single self-contained HTML)
Each variant:
- `<script src="../_shared-data.js">` + renders from `DATA` global
- One Google Font via `<link>` (Inter or Rubik)
- Inline `<style>` — no build step, no external deps
- Realistic fake content
- **Variant-tag overlay** in bottom-left corner for screenshot identification

#### DNA Composition: How 4 References → 3 Outputs

| Variant | References | DNA Mix |
|---------|-----------|---------|
| 001-minimax-pro | Vercel (70%) + Linear (20%) + MiniMax (10%) | Dark chrome BG, shadow-as-border, negative tracking, Inter cv01+ss03, pink accent from Yuno brand |
| 002-glassmorphism-glow | MiniMax (50%) + Linear (30%) + Vercel (20%) | Frosted-glass cards with `backdrop-filter: blur()`, radial-glow halos behind stat cards, pink→cyan gradient sparkline bars, heart-beat animation on greeting |
| 003-data-dense | Vercel (40%) + Sentry (40%) + MiniMax (20%) | Dark purple-black canvas (`#08040C`), lime-cyan accents, Rubik + JetBrains Mono, monospaced KPIs, inset panel shadows, high information density |

#### OpenType Feature-Toggles for Font Authenticity

Without these, Inter renders in default "friendly" mode (round `a`, open `g`). With cv01 + ss03, it matches Linear's tighter, more technical silhouette:

```css
body, .heading {
  font-family: "Inter", system-ui, sans-serif;
  font-feature-settings: "cv01" 1, "ss03" 1;
}
```

This is a **20-cent line that makes the HTML look dramatically more like the reference.** Always use with Inter when the target design is Linear.

#### Variant-Tag Overlay
```css
.variant-tag {
  position: fixed; bottom: 8px; left: 8px;
  font-size: 10px; line-height: 1;
  color: rgba(255,255,255,0.35);
  background: rgba(0,0,0,0.4);
  padding: 3px 6px; border-radius: 4px;
  pointer-events: none; user-select: none;
  z-index: 9999;
}
```

### 3. Generate Screenshots + Comparison View
After building all 3 variants:

```bash
# Screenshot each variant
for v in 001-minimax-pro 002-glassmorphism-glow 003-data-dense; do
  google-chrome --headless --disable-gpu --no-sandbox --hide-scrollbars \
    --window-size=1440,1200 --virtual-time-budget=4000 \
    --screenshot="screenshots/$v.png" \
    "http://127.0.0.1:8766/$v/index.html"
done

# Build comparison index.html that shows 3 side-by-side cards
# Each card has: variant title, design-stance description, screenshot image (cropped to ~450px wide), "Live öffnen" + "Full PNG" buttons
# Bottom section: "MEINE EMPFEHLUNG" with recommendation
```

The index.html pattern:
```html
<div class="variants">
  <div class="variant-card" data-variant="01">
    <div class="variant-header">VARIANTE 01 · EMPFEHLUNG</div>
    <h3>MiniMax-Pro</h3>
    <p class="variant-desc">Vercel-Präzision × Linear-Dark × Yuno-Pink-Akzent</p>
    <img src="screenshots/001-minimax-pro.png" alt="Variant 1" loading="lazy">
    <div class="variant-actions">
      <a href="001-minimax-pro/index.html" target="_blank">Live öffnen</a>
      <a href="screenshots/001-minimax-pro.png" target="_blank">Full PNG</a>
    </div>
  </div>
  <!-- repeat for 02, 03 -->
</div>
```

### 4. User Selection
Present the 3 variants with opinionated recommendation. User can:
- Pick one ("nimm 01")
- Mix elements ("nimm 01 aber die Health-Bars aus 03")
- Request adjustments ("mach 02 fetter mit mehr Glow")

## Key Techniques

| Technique | Why | Code |
|-----------|-----|------|
| Shared data file | One source of truth, variants differ only in presentation | `_shared-data.js` with `window.DATA` + `sparklineSVG()` |
| Opentype cv01+ss03 | Makes Inter look like Linear without paying for the font | `font-feature-settings: "cv01" 1, "ss03" 1` |
| Tabular nums | KPI digits don't visually jump when values change | `font-variant-numeric: tabular-nums` |
| Variant tag | Screenshot identification without reading the filename | Fixed bottom-left overlay |
| Shadow-as-border | Cleaner than CSS borders for card separation | `box-shadow: 0 0 0 1px rgba(255,255,255,0.06)` |
| Headless screenshot grid | User sees real rendered output, not mental simulation | 3 screenshots side-by-side in index.html |
| Multi-reference DNA composition | More meaningful diversity than "change the accent color" | Pick 3-4 design systems, compose each variant as a weighted mix |

## Pitfalls

### Pitfall 1 — Glassmorphism Hero overlaps Top-Bar
**Symptom:** The "Hallo Basti" hero section and the search/theme-toggle bar overlap vertically on variant 02.
**Fix:** Add explicit `margin-bottom: var(--space-4)` and `padding-bottom` to `.topbar` to create breathing room before the hero. Test at 1440×900 as your minimum viewport.

### Pitfall 2 — Headless Chrome ignores `prefers-color-scheme`
JS-based theme switchers that read `prefers-color-scheme` via CSS media queries do NOT get picked up by headless Chrome even with `--force-prefers-color-scheme`. Use localStorage-wrapper pattern (see `scripts/headless-theme-screenshots.sh`) when capturing themed screenshots.

### Pitfall 3 — Font not applied in headless Chrome
If the Google Font `@import` uses `display=swap` and the page renders before the font loads, headless Chrome captures the unstyled flash. Fix: Add `?display=block` or use `@import url('...')` with sufficient `--virtual-time-budget` (2000+).

## Validation Results (this build)

- **3 variants built**, each 480-615 lines, 19.6-24.3 KB
- **WCAG AA contrast:** verified per theme (17/17 pairs)
- **Token consistency:** 206+ var(--*) per variant, 0 hardcoded hex
- **Responsive:** 3 breakpoints per variant (1100px, 720px)
- **Self-contained:** 0 external deps except Google Fonts CDN `<link>`
- **Interactive:** Each variant has hover states, clickable filter tabs, theme toggle visually selectable
