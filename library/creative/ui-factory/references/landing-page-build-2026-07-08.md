# Yuno MiniMax Bundles Landing Page — UI-Factory Build (2026-07-08)

## Context

Third ui-factory chain run. Previous builds were **dashboards** (Yuno-Dashboard 07-01, Yuno-Operator 07-06). This one is a **product landing page** — a different deliverable class:

- **Product type:** Marketing Landing Page (single-file, self-contained)
- **Brand:** Yuno MiniMax Skills-Bundles
- **Style Reference:** Vercel (black slabs, system stack, monospace accents) + Linear.app (grid-cards, switcher) + Stripe (eyebrow tags, color-coded sections)
- **Target:** ~400-600 lines (final: 829 — justified by tokens, theme-switcher, design-notes, WCAG-AA)
- **Output:** `/tmp/yuno-landing-page/index.html` (40.3 KB) + `style-tokens.json` (9.0 KB)

## Key Differences from Dashboard Builds

| Aspect | Dashboard (07-01/07-06) | Landing Page (07-08) |
|--------|------------------------|---------------------|
| Layout | Sidebar + KPI-Grid + Charts + Table | Hero + Bundle-Showcase + Why + Installation + CTA + Footer |
| Cards | Data-driven (KPI, sparklines) | Product-driven (5 bundles with color-coded accent stripes) |
| Theme Switcher | 4 modes (Cozy/Dark/Cyberpunk/A11y) | 2 modes (Light/Dark) |
| Token count | 273 var(--*) | 206 var(--*) |
| Size | 42 KB / 1118 lines | 40.3 KB / 829 lines |

## Validation Results

| Check | Result |
|-------|--------|
| HTML Wohlgeformtheit | stack=0, errors=0 |
| CSS Braces balanced | 142/142 |
| var(--*) usage | 206 |
| Hardcoded hex outside :root | 3 (all legitimate) |
| External fonts/scripts | 0 |
| Size | 40.3 KB, 829 lines |

## Headless Chrome localStorage-Wrapper

This build used a localStorage-based theme switcher. The localStorage wrapper (discovered 2026-07-08) was required because `--force-prefers-color-scheme` is ignored by headless Chrome for JS-based theme switchers. See Pitfall 9 in SKILL.md for implementation details.

## Lessons Learned

1. **Landing Page vs Dashboard:** Different layout primitives required (Hero, Showcase-Grid, Feature-Cards, CTA-Band, Footer) — not applicable to Phase 4 of the standard ui-factory pipeline. This indicates a need for a Phase-6 "Showcase/Marketing" template.

2. **Line Budget vs Richness:** Brief asked for ~400-600 lines, final 829. Delta from: Design-Notes (~25 lines), Token-definitions (~130 lines CSS :root + dark mode), Theme-Switcher JS (~68 lines), IntersectionObserver (~20 lines), 5 bundle cards (~80 lines non-compressible). Minification could hit ~450 but would lose token consistency and inline docs.

3. **LocalStorage Wrapper for Headless Chrome:** Essential pattern when theme switchers read localStorage exclusively (no URL-param path). The wrapper sets localStorage before `location.replace()` to the real page. Validated via MD5 comparison.

## Style Reference

- **Vercel:** Black-Slab-Terminal, System-Stack, monospace-accents, precision orange
- **Linear:** Grid-Cards, Theme-Switcher, clean whitespace
- **Stripe:** Eyebrow-Tags, color-coded sections, 3-up value props
- **Rejected:** shadcn templates, Inter-on-white-default, gradient blobs, AI-stock

## Output Location

`/tmp/yuno-landing-page/index.html` + `style-tokens.json`
