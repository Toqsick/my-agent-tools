---
name: ui-factory
description: "Use when user asks for full UI factory chain, color-system → design-system → component-library → dashboard orchestration. NOT for a single UI sub-skill or non-UI tasks. Orchestrate the full UI-Factory chain (color-system → design-system → components → dashboard)."
version: 1.0.0
author: 'Yuno (Hermes Agent) — based on KIMI K2 UI-Factory-Pattern 2026-06-30

  '
license: MIT
metadata:
  hermes:
    tags:
    - ui
    - orchestrator
    - factory
    - meta-skill
    - ui-builder
    - design-system
    - dashboard
    - full-stack
    related_skills:
    - ui-color-system
    - ui-design-system
    - ui-component-library
    - ui-dashboard
    - web-design-guidelines
    part_of: ui-factory
    triggers:
    - build a UI
    - create a dashboard
    - design an app
    - make me a website
    - scaffold components
    - design system
    - look and feel
    - branding
    - from scratch UI
    - complete UI
    - production-ready UI
    - build me an app
    - design tokens
lane: worker-vision
reasoning_effort: xhigh
agent: Designer
routing_hint: '**Agent-Scope:** UI/UX, visual, art-styles, design-systems, motion.
  Off-scope: code building, data modeling, long-form copy — return to Yuno.


  Routing-Spec: `yuno-team-routing`.

  '
trigger_keywords: ['system', 'full', 'factory', 'chain', 'color']
keywords: ['system', 'full', 'factory', 'chain', 'color']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['ui-dashboard']
---


# ui-factory

> **Meta-Skill:** Orchestrates the full UI-Factory chain. Single entry-point for any UI task that needs design + build + a11y + responsiveness. Routes to the right atoms in the right order.

## When to TRIGGER

This meta-skill auto-triggers when user input matches ANY of:

### Trigger-Phrasen (UI-spezifisch)

| Category | Phrasen | Auto-Skill |
|----------|---------|------------|
| **Farben / Branding** | "color palette", "brand colors", "WCAG", "contrast", "dark mode colors", "welche Farben", "Theme", "Akzentfarbe" | → `ui-color-system` |
| **Design-System / Tokens** | "design system", "design tokens", "tokens.json", "CSS variables", "theme", "Brand-Identität als Code", "Komponenten-Standards" | → `ui-design-system` |
| **Komponenten / Library** | "component library", "UI kit", "Button bauen", "Input-Feld", "Modal", "Card", "Nav bauen", "alle Komponenten", "scaffold components" | → `ui-component-library` |
| **Dashboard / Data-UI** | "dashboard", "admin panel", "monitoring", "KPIs", "analytics view", "metrics view", "Übersichts-Seite", "Statistiken anzeigen" | → `ui-dashboard` |
| **Full-Stack / Komplett** | "build a UI", "create a dashboard", "design an app", "make me a website", "complete UI from scratch", "production-ready UI", "Komplettes UI-Projekt", "Vollständig bauen" | → **`ui-factory` (this skill)** |

### Decision-Tree: Welcher Skill passt?

```
User-Input
  |
  |- "color/brand/WCAG" -> ui-color-system
  |- "tokens/design-system" -> ui-design-system
  |- "component/button/modal" -> ui-component-library
  |- "dashboard/KPI/analytics" -> ui-dashboard
  |
  `- Komplex/Multi-Step/Full-Stack?
       |
       `- YES -> ui-factory (orchestriert alle 4 Atoms)
```

## When NOT to use

- User asks for ONE simple UI change ("make this button blue") -> direkt machen, kein Skill-Overhead
- User asks for code review on existing UI -> `web-design-guidelines` oder `simplify-code`
- User asks for creative content (writing, art) -> nicht UI-bezogen, andere Skills

## Inputs

```yaml
brief:
  product_type: "SaaS dashboard | Marketing site | E-commerce | Blog | App | Settings"
  mood: "trustworthy | playful | serious | cozy | futuristic | minimal | corporate"
  mode: "light | dark | both | high-contrast | cozy | cyberpunk"
  brand_primary: "#XXXXXX or 'auto-generate'"
  framework: "vanilla-html | react | vue | svelte | sveltekit | nextjs"
  style: "css-modules | tailwind | vanilla-extract | plain-css | styled-components"
  a11y_target: "AA | AAA"
  components_needed: ["button", "input", "card", "modal", "nav", "table", "chart", "dashboard"]
  output_target: "single-file-html | storybook | production-app | prototype"
```

## Output

**Full UI-Factory deliverable:**

1. **`tokens.json`** + **`tokens.css`** + **`tokens.d.ts`** (von ui-design-system)
2. **`colors.json`** + **`colors.css`** + **`contrast-report.md`** (von ui-color-system)
3. **Component files**: `Button.tsx`, `Input.tsx`, `Card.tsx`, etc. mit `.module.css` + `.stories.tsx` + `.test.tsx` + `.a11y.test.tsx` (von ui-component-library)
4. **Dashboard files**: `Dashboard.tsx`, `KpiCard.tsx`, `RevenueChart.tsx`, `RecentErrorsTable.tsx`, `FilterPanel.tsx` (von ui-dashboard)
5. **`index.ts`** re-exports + **`README.md`** usage-docs

## Workflow

### Phase 0: Brief-Analyse (1-2 min)

Lies den User-Brief und parse:
- **Product type** -> spacing density, layout pattern
- **Mood** -> color palette, corner radius, shadow strength
- **Mode** -> light/dark/both token-sets
- **Brand color** -> primary hue (oder auto-generate aus mood)
- **Framework** -> output format (TSX/Vue/Svelte/HTML)
- **a11y target** -> validation threshold
- **Component set** -> welche Atoms werden gebraucht

### Phase 1: ui-color-system (3-5 min)

**Input:** Brief
**Output:** `colors.json` + `colors.css` + `contrast-report.md`

Steps:
1. Brand-Color analysieren (oder auto-generate aus mood)
2. Scale generieren (50-950)
3. Semantic-Rollen zuweisen
4. Contrast-Checks durchführen (AA minimum, AAA wo möglich)
5. **4 Modi generieren** (statt nur 2-3):
   - **Cozy** (Warm-Light Mode): Cream-BG `#FFF5F5`, Pink-800 Text, weiche Schatten
   - **Dark** (Standard Dark Mode): Neutral-950 BG, Pink-300 Text, reduzierte Sättigung
   - **Cyberpunk** (Dark + Neon): Night-BG `#0D0020`, Magenta-Neon-Akzente, Sparkle-Particles, 0.12 opacity overlays
   - **A11y** (High-Contrast): Pure Black BG `#000`, White Text `#FFF`, max Kontrast

**Output-Detail:**
- 5+ Color-Scales (primary, neutral, success, warning, error, info)
- WCAG contrast report (**>=10 kritische Pairs**, pro Theme)
- Color-Blind-Simulation passed

### Phase 2: ui-design-system (3-5 min)

**Input:** `colors.json` aus Phase 1
**Output:** `tokens.json` + `tokens.css` + `tokens.d.ts`

Steps:
1. Token-Kategorien generieren: color, font, space, radius, shadow, motion, z-index, breakpoints
2. CSS-Variablen mit kebab-case: `--color-primary-500`, `--space-4`
3. TypeScript-Types für IDE-Autocompletion
4. Fluid-Typography mit `clamp()`

**Validation:**
- 4px oder 8px Spacing-Grid (keine Arbitrary-Werte)
- Alle Hex-Codes 7-stellig
- Spacing in `rem` nicht `px`

### Phase 3: ui-component-library (5-10 min)

**Input:** `tokens.json` + `colors.json`
**Output:** Component-Files (TSX/Vue/Svelte/HTML) + Stories + Tests

Steps:
1. Components wählen (Core-Set: Button, Input, Card, Badge, Avatar)
2. Pro Component: 5 Files erstellen (.tsx + .module.css + .stories.tsx + .test.tsx + .a11y.test.tsx)
3. Tokens importieren (keine hardcoded values)
4. A11y-Checklist durchgehen pro Component
5. Stories mit Controls generieren

**Validation:**
- Alle Components importieren Tokens (kein `rgb(255,255,255)` hardcoded)
- Jede Component hat jest-axe a11y test (zero violations)
- Keyboard-Handler überall
- Visible focus-indicator

### Phase 4: ui-dashboard (5-10 min)

**Input:** Components aus Phase 3 + Brief
**Output:** `Dashboard.tsx` + KPI-Cards + Charts + Table + Filter-Panel

Steps:
1. Layout planen: Header -> Sidebar + KPI-Grid -> Charts -> Table
2. KPI-Cards mit Trend-Indicators
3. Charts (line/bar/pie/area -- recharts/chart.js)
4. Data-Table mit sort/filter/pagination
5. Filter-Panel mit date-range, multi-select
6. Loading/Empty/Error states für jede Section
7. Responsive (mobile/tablet/desktop breakpoints)

**Validation:**
- 4-6 KPIs max
- Alle Charts haben hover-tooltip
- Alle Tables haben sort + filter + pagination
- Loading states überall

### Phase 5: Verification + Output (2-3 min)

**Wichtig -- Auto-Validation vor manueller Abnahme laufen lassen.** Im Yuno-Build 2026-07-06 fand die automatisierte WCAG-Pair-Validation **4 Fails** die bei manueller Prüfung übersehen worden wären (Pink-500 Text 3.2:1, Magenta-500 Body 4.29:1, Error-500 4.04:1, White-on-Magenta 3.64:1). Automatisierte Validierung ist kein Nice-to-have -- sie findet Fehler die selbst bei sorgfältigem manuellem Review durchrutschen.

**New in v1.0.2 (2026-07-08):** Nutze `scripts/html-qa-check.py <path>` für eine 5-Dimensionen-Validierung: HTML-Wohlgeformtheit, CSS-Brace-Balance, Token-Konsistenz, Inline-Style-Audit, File-Größe. Lauffähig als Phase-5-Finish.

Checkliste:
- [ ] Alle Atoms zusammen integriert (Color -> Design -> Components -> Dashboard)
- [ ] Keine hardcoded values (alle Tokens referenziert)
- [ ] A11y: alle Tests grün, alle Pairs WCAG-konform
- [ ] **Auto-Validation durchgeführt** (Token-Konsistenz + WCAG-Pairs + A11y-Attribute)
- [ ] Responsive: Mobile/Tablet/Desktop breakpoints funktionieren
- [ ] Loading/Empty/Error states überall
- [ ] Theme-Switcher funktioniert in Echtzeit (4 Modi: Cozy/Dark/Cyberpunk/A11y)
- [ ] Kontrast-Report mit **mindestens 10 kritischen Pairs** pro Theme
- [ ] Bundle-Output (ZIP oder Git-Commit-ready) erstellt

## Orchestration-Logic für Sub-Tasks

Wenn der Task lang/komplex ist (mehr als 1 Atoms):

```
User: "Bau mir ein komplettes SaaS-Dashboard mit Users/Revenue/Errors"
   |
ui-factory: Analysiere Brief
   |
[Auto-Chain triggert]:
   1. ui-color-system -> "Primary purple, dark mode default, WCAG AA"
   2. ui-design-system -> "Tokens mit 4px grid, Inter sans, JetBrains Mono"
   3. ui-component-library -> "Button, Input, Card, Badge, Modal, Nav, Table, Chart"
   4. ui-dashboard -> "4 KPIs (Users/Revenue/Errors/Latency), RevenueChart, ErrorsTable"
   |
Final: Komplettes Dashboard mit allem
```

## Auto-Orchestration Rule (Basti explicit request, 2026-07-01)

**Bei Tasks die "etwas länger" sind -> AUTOMATISCH orchestrieren, NICHT fragen.** Diese Regel wurde in Session 2026-07-01 von Basti EXPLIZIT angefordert und durch einen erfolgreichen Live-Build bewiesen (komplettes Dashboard in ~5 min ohne einzige Rückfrage).

Trigger-Heuristik für Auto-Orchestration (eines reicht):
1. Task braucht **3+ Tool-Calls**
2. Task involviert **mehrere Files/Components**
3. Task passt zu einer **existierenden Skill-Chain** (z.B. UI-Factory)
4. User-Keywords: "komplett bauen", "from scratch", "vollstandig", "alles", "production-ready"

Bei Match: **SOFORT** TodoWrite + Step-by-Step-Plan ausführen. **NICHT** erst fragen "soll ich orchestrieren?". Grund: Basti experimentierfreudig, hasst unnötige Rückfragen, will momentum.

**Ausnahme:** Bei **Trade-offs mit echten Konsequenzen** -> `clarify()` mit 2-4 konkreten Optionen und Sterne-Bewertung.

**Bewiesene Pipeline (Yuno-Dashboard, 2026-07-01):**
```
User: "okay baue mir ein komplettes Dashboard :D"
  -> ui-factory auto-triggered (match: "komplett" + "Dashboard" + "bauen")
  -> TodoWrite mit 6 Phasen
  -> Phase 1: ui-color-system (Yuno Purple/Pink + WCAG check + 1 fix)
  -> Phase 2: ui-design-system (tokens.json/css)
  -> Phase 3+4: Components + Dashboard compose (single-file HTML 37KB)
  -> Phase 5: Validation (A11y, Responsive, Token-Konsistenz)
  -> Phase 6: Doku + Smoke-Test
  -> Result: Keine Rückfrage nötig, User zufrieden ("sieht hot aus!")
```

## Live-Build-Template: Yuno-Dashboard (2026-07-01, ~5 min)

**Input:** "okay baue mir ein komplettes Dashboard :D"

**Output:** `~/yuno-dashboard/` mit:
- `index.html` (37 KB, 1034 lines, single-file)
- `tokens/colors.json` (2.3 KB, Yuno-Purple/Pink, WCAG-AA verified)
- `tokens/tokens.css` (3.4 KB, CSS-Vars)
- `tokens/tokens.json` (2.7 KB, JS/TS-tokens)
- `docs/README.md` (7.6 KB, architecture + WCAG-verification)

**Bestätigte Validation-Resultate:**
- File-Size: 37 KB (single-file, no deps)
- WCAG 2.2 AA: alle 10 Text/Bg-Pairs verified (Button-Text 6.98:1 light, 11.25:1 dark)
- Responsive: 5x @media queries
- Token-Konsistenz: 84x var-usage, 0 hardcoded-components

## Live-Build-Template: Yuno-Operator-Dashboard 4-Mode (2026-07-06, ~45 min)

**Input:** Yuno-Style-Pattern Analyse (3 Bilder -> 5 Soul-Marker) + Dashboard-Build

**Output:** `~/yuno-ui/` mit:
- `index.html` (42 KB, 1118 lines, single-file) -- 4 Modi, 273x var(--*), 0 hardcoded-hex
- `tokens/colors.json` (7.1 KB) -- 9 Scales, 4 Modes, 17 Contrast-Pairs
- `tokens/contrast-report.md` (4.7 KB) -- 17/17 WCAG-Pairs PASS
- `README.md` (10 KB) -- Architecture + WCAG-Table + Theme-Guide

**Bestätigte Validation-Resultate:**
- WCAG 2.2 AA: 17/17 Pairs PASS (alle 4 Themes)
- Token-Konsistenz: 273x var(--*), 0 hardcoded-hex in UI
- Theme-Switcher: localStorage-persistent, alle 4 Modi getestet
- Browser-Console: 0 Errors, 0 Warnings

## Live-Build-Template: Yuno-Operator-Dashboard-3-Variant (2026-07-08, ~60 min)

**Input:** "Mach nochmal redesign mit deinen neuen design ui skills — 3 varianten, ich vergleiche"

**Output:** `~/10-Projekte/10-active/yuno-ui-redesign/` mit:
- `_shared-data.js` (daten für alle 3 varianten + `sparklineSVG()` helper)
- `001-minimax-pro/index.html` (19.6 KB, 480 lines) — Vercel × Linear × Pink
- `002-glassmorphism-glow/index.html` (24.3 KB, 615 lines) — frosted-glass × neon
- `003-data-dense/index.html` (19.8 KB, 530 lines) — Stripe × Sentry
- `index.html` — Vergleichsansicht mit echten Screenshots
- `README.md` — Methodik + Lessons
- `screenshots/` — Headless-Chrome-Renders (1440×1300)

**Neue Techniken in diesem Build:**
- **Shared-data pattern:** `_shared-data.js` von allen 3 varianten geladen — eine quelle, verschiedene CSS
- **Multi-reference DNA composition:** 4 Referenz-Designs (Vercel, Linear, Sentry, MiniMax) → 3 gewichtete Mischungen
- **OpenType feature-toggles:** `font-feature-settings: "cv01" 1, "ss03" 1` — macht Inter linear-authentisch
- **Tabular-nums:** `font-variant-numeric: tabular-nums` — KPIs springen nicht beim Ändern der Ziffern
- **Variant-tag overlay:** fixed bottom-left label zur Screenshot-Identifikation
- **Screenshot-Grid-Vergleich:** index.html zeigt 3 side-by-side Screenshots → User sieht echte Renderings

**Validierung:**
- HTML wohlgeformt: stack=0, errors=0 (alle 3)
- CSS braces: balanced (alle 3)
- Token-konsistenz: 200+ var(--*) pro variant, 0 hardcoded hex
- Responsive: 3 breakpoints pro variant
- Self-contained: 0 externe deps außer Google Font CDN

**Gesamtbuild mit `sketch`-Workflow.** `sketch`-Skill ist bundled und daher nicht direkt patchbar — dieser Live-Build-Template dient als Ersatzreferenz für die dort nicht dokumentierten Techniken.

**Siehe:** `references/multi-variant-design-2026-07-08.md` für detaillierten Workflow.

## Live-Build-Template: Yuno-MiniMax-Landing-Page (2026-07-08, ~20 min)

**Input:** "Erstelle das HTML+CSS Grundgerüst für eine Landing-Page die 5 Yuno MiniMax Bundles präsentiert. Nutze ui-factory / popular-web-designs als Stil-Referenz."

**Output:** `/tmp/yuno-landing-page/` mit:
- `index.html` (40.3 KB, 829 lines, single-file) -- 206x var(--*), 2 Themes
- `style-tokens.json` (9.0 KB, 132 lines) -- 2 modes, 5 bundle accents, 7 WCAG pairs

**Besonderheiten:**
- **Erster Landing-Page-Build** im ui-factory-Pattern (vorher nur Dashboards)
- **Style-Mix:** Vercel + Linear + Stripe (siehe references/landing-page-build-2026-07-08.md)
- **Neues Validation-Script:** `scripts/html-qa-check.py` (5-Dimensionen-Check)
- **localStorage-Wrapper** für Headless Chrome Theme-Validation entdeckt
- **Size-Compression:** Iterativ von 1053 auf 829 Lines verdichtet

**Bestätigte Validation-Resultate:**
- HTML well-formed: stack=0, errors=0
- CSS braces: 142/142 balanced
- var(--*) usage: 206, hardcoded hex outside :root: 3 (alle legitim)
- External fonts: 0, External scripts: 0
- Size: 40.3 KB, 829 lines

**Siehe:** `references/landing-page-build-2026-07-08.md` für detaillierte Lessons.

## Pitfalls (from real builds, 2026-07-01)

### Pitfall 1 -- WCAG-AA Contrast bei Button-Text

**Symptom:** White-text auf `purple-500` (`#A855F7`) = 3.96:1 -> FAIL AA

**Fix:** Zwei verschiedene Primary-Shades für Light vs Dark Mode:
- **Light Mode:** Button-BG = `purple-700` (`#7E22CE`), Button-Text = `#FFFFFF` (6.98:1 AA)
- **Dark Mode:** Button-BG = `purple-300` (`#D8B4FE`), Button-Text = `#09090B` (11.25:1 AA)

**Harder Case (Pink/Magenta, 2026-07-06):** Benötigt zwei Stufen dunkler als Purple. Pink-800 (`#C2185B`) auf Cream = 6.03:1 AA.

### Pitfall 2 -- Hardcoded Hex ausserhalb `:root`

**Detection-Pattern:**
```python
total_hex = len(re.findall(r'#[0-9A-Fa-f]{6}', src))
root_match = re.search(r':root\s*{([^}]+)}', src, re.DOTALL)
in_root = len(re.findall(r'#[0-9A-Fa-f]{6}', root_match.group(1))) if root_match else 0
outside_hex = total_hex - in_root  # sollte <= 1 sein (meta theme-color)
```

### Pitfall 3 -- Framework-Choice-Lock-In

**Best-Practice Defaults:**
| Use-Case | Default Framework |
|----------|-------------------|
| Quick-Show, No-Backend | `vanilla-html` (single-file) |
| Production-SaaS | `react` + `tailwind` |
| Marketing-Site | `sveltekit` + `tailwind` |
| Internal-Tool | `vue` + `css-modules` |

### Pitfall 4 -- Token-Count-Explosion

**Budget:** ~120 Tokens max:
- Color: 5 scales x 11 shades = 55
- Font: 5 sizes + 4 families + 3 leading = 12
- Space: 13, Radius: 6, Shadow: 6, Motion: 6, Z-Index: 6

### Pitfall 5 -- Token-Konsistenz nicht messbar ohne Check-Tool

**Build-Time-Check:** `python3 scripts/html-qa-check.py index.html`

### Pitfall 6 -- Output-Grosse bei Single-File HTML

**Mitigation:**
- ASCII-Sparklines statt SVG-Charts (28-byte bars statt 5KB SVG)
- CSS-only Progress-Bars statt Chart-Libraries
- External-Files wenn >50 KB

### Pitfall 7 -- Theme-Switcher ohne A11y-freundliche Modi

**Fix:** Immer **4 Modi** anbieten: Cozy (warm-light), Dark (standard), Cyberpunk (dark+neon), A11y (pure black/white). Siehe Code-Sample in `references/yuno-operator-build-2026-07-06.md`.

### Pitfall 8 -- HC-Mode: Page-BG = Card-BG -> Cards unsichtbar

**Fix -- Subtle-Lift-Pattern:**
```css
[data-theme="hc"] {
  --yuno-bg:           #000000;   /* Page: pure black */
  --yuno-bg-subtle:    #0A0A0A;   /* Subtle regions */
  --yuno-bg-panel:     #0A0A0A;   /* Cards: lifted by 4% lightness */
  --yuno-border:       #FFFFFF;   /* White borders for separation */
}
```

### Pitfall 9 -- Headless Chrome fur Screenshot-Validation (entdeckt 2026-07-06, erweitert 2026-07-08)

**Zwei Modi:**

**Modus A -- URL-Param-Theme-Switching** (vorausgesetzt im HTML verbaut):
```bash
for theme in light dark cyberpunk hc; do
  google-chrome --headless --disable-gpu --no-sandbox --hide-scrollbars \
    --window-size=1440,1100 --virtual-time-budget=2000 \
    --screenshot=/tmp/yuno-${theme}.png \
    "http://127.0.0.1:8765/index.html?theme=${theme}"
done
```

**Modus B -- localStorage-Wrapper** (fur JS-Theme-Switcher die localStorage lesen):
```bash
cat > /tmp/light-wrapper.html <<'WRAPPER'
<!DOCTYPE html><html><head><script>
localStorage.setItem('yuno-theme', 'light');
document.documentElement.setAttribute('data-theme', 'light');
location.replace('index.html');
</script></head><body></body></html>
WRAPPER

google-chrome --headless --disable-gpu --no-sandbox --hide-scrollbars \
  --window-size=1440,3500 --virtual-time-budget=5000 \
  --screenshot=/tmp/yuno-light.png \
  "http://127.0.0.1:8765/light-wrapper.html"
```

**Warum Modus B notig ist:** `--force-prefers-color-scheme` wird von Headless Chrome fur JS-basierte Theme-Switcher ignoriert (2026-07-08 validiert). Der Wrapper setzt `localStorage` vor `location.replace()` und liefert reproduzierbare Theme-Screenshots unabhangig vom JS-Pfad.

**Script:** `scripts/headless-theme-screenshots.sh` fur Modus A. Siehe `references/landing-page-build-2026-07-08.md` fur Modus B Anwendung.

### Pitfall 10 -- Favicon-404-Larm im Server-Log

**Fix -- Inline SVG Data-URI:**
```html
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,...">
```
Zero extra HTTP-Request, Brand im Browser-Tab, Server-Log bleibt clean.

### Pitfall 11 -- Base64-Encode Tippfehler-Falle

**Fix -- IMMER nach dem Patch decode-testen:**
```python
import re, base64
m = re.search(r'href="(data:image/svg\+xml;base64,([A-Za-z0-9+/=]+))"', src)
decoded = base64.b64decode(m.group(2)).decode('utf-8')
assert decoded.startswith('<svg') and decoded.endswith('</svg>')
```

### Pitfall 12 -- Yuno-Pink/Magenta WCAG-Tabelle (entdeckt 2026-07-06)

**Key Insight:** Bright Brand-Colors (Pink, Coral, Cyan, Lime, Yellow) brauchen **immer 2-3 Shade-Stufen tiefer** als Standard-Purple/Navy/Forest. Siehe `references/yuno-operator-build-2026-07-06.md` fur die vollstandige WCAG-Tabelle.

### Pitfall 13 -- Size-Compression-Workflow fur Single-File HTML (entdeckt 2026-07-08)

**Symptom:** Der gebaute single-file HTML ist weit uber dem Line-Budget (z.B. 1053 statt 400-600 Zeilen). Einfaches Minifizieren wurde Design-Notes, Token-Kommentare und Code-Struktur zerstoren.

**Workflow -- Iterative Kompression ohne Funktionsverlust:**

1. **Messen:** `wc -l index.html` + `python3 scripts/html-qa-check.py index.html` (Basis-Line)
2. **Design-Notes verdichten:** Lange Paragraph-Form -> dichte Bullet-Liste (80 -> 25 Zeilen)
3. **CSS-Selektoren kompaktifizieren:** Multi-Line-Selektoren auf Einzeiler wo pragmatisch
4. **Leerzeilen raumen:** Section-Trennung auf einen Kommentar reduzieren (70+ -> 5)
5. **Nach jeder Runde: erneut QA laufen lassen** (Brace-Balance und Token-Konsistenz mussen stabil bleiben)
6. **Stopp-Kriterium:** Wenn weitere Kompression die Lesbarkeit (CSS-Selectors pro Zeile > 200 Zeichen) oder Token-Klarheit (Kommentare fehlen) verschlechtert.

**Erfahrungswerte (Landing-Page 2026-07-08):**
- Start: 1053 Zeilen, 42.2 KB
- Nach Kommentar-Verdichtung: 1021 Zeilen (-3%)
- Nach CSS-Kompaktifizierung: 937 Zeilen (-8%)
- Nach Leerzeilen-Raumung: 829 Zeilen (-21% vom Start)
- CSS-Dichte: von 520 auf 355 Zeilen (-32% CSS)
- **Abbruch** bei 829 weil weitere Minifikation (>200 Zeichen/Zeile) die Wartbarkeit zerstort hatte

**Golden Rule:** 400-600 Zeilen Budget gilt fur Showcases-to-throw-away. Fur produktive Builds mit Design-Notes + Token-System + Theme-Switcher + WCAG ist 800-1000 realistisch. Im Zweifel die Zeilen-Zahl im Brief anpassen, nicht den Inhalt kaputtkomprimieren.

### Pitfall 14 -- Headless Chrome validiert KEIN async JS (entdeckt 2026-07-08)

**Symptom:** Dashboard zeigt im Headless-Chrome-Screenshot schöne Skeletons, aber im echten Browser hängt es auf "connecting…". Der Screenshot war fake — `--virtual-time-budget` feuert BEVOR `fetch()` resolved.

**Warum:** `--virtual-time-budget=N` zählt Wall-Clock-Time. Wenn `fetch()` noch auf die Response wartet wenn das Budget abläuft, captured Chrome den aktuellen Frame — den Skeleton-Ladezustand. Auch bei 30s Budget passiert das, weil die Page `DOMContentLoaded` schon gefeuert hat (das zählt als "stabil").

**Fix — Browser-Tools statt Headless-Chrome für JS-Debug:**

Nutze den **Browser-Tool-Debug-Pipeline** aus `ui-dashboard/references/browser-validation-workflow.md`:

```python
# Statt Headless Chrome:
browser_navigate(url="http://127.0.0.1:8767/index.html?bust=1")
browser_console()  # → zeigt JS-Errors an
# Fix, dann:
browser_navigate(url="http://127.0.0.1:8767/index.html?bust=2")
browser_console()  # → muss empty sein
# Erst dann Headless Chrome für Screenshots nutzen
```

**Kurzregel:** Headless Chrome = Screenshots (nachdem JS validiert ist). Browser-Tools = JS-Debug + Live-Verifikation. Nie umgekehrt.

**Referenz:** `ui-dashboard` Skill → `references/browser-validation-workflow.md` für die vollständige Debugging-Pipeline + 5 häufige JS-Fehler in Dashboard-Deploys (String-null-guard, getElementById-timing, fetch-error-swallowing, Unicode-Keys, Hoisting-Fallstricke).

## Workspace-Convention fur Yuno-UI-Builds

ui-factory-Builds gehoren nach **`~/10-Projekte/10-active/<build>/`**, NICHT in `~/` direkt. Single-File Showcases: `~/Bilder/yuno-gallery/<build>-<datum>/` + `~/10-Projekte/10-active/<name>/index.html`.

## Curator-Note (Overlap, 2026-07-01)

Potenzielle Uberschneidung mit `creative/html-artifact` Skill:
- `html-artifact`: Fokus auf Explainers/Reports
- `ui-factory`: Fokus auf komponentenbasierte UI
- Decision: "Bau mir X (UI/UX)" -> ui-factory; "Erklare mir X" -> html-artifact

## Support Files

- `references/yuno-operator-build-2026-07-06.md` — Detaillierte WCAG-Tabelle + 4-Mode-Pattern
- `references/landing-page-build-2026-07-08.md` — Landing-Page-Build-Reference + localStorage-Wrapper
- `references/multi-variant-design-2026-07-08.md` — Multi-Variant-Vergleichsworkflow, Multi-Reference-DNA-Komposition, Shared-Data-Pattern, OpenType-Feature-Toggles, Headless-Chrome-Screenshot-Grid
- `scripts/headless-theme-screenshots.sh` — Bash-Script fur URL-Param-Theme-Screenshots
- `scripts/html-qa-check.py` — Python-Script fur 5-Dimensionen-HTML-QA (2026-07-08)
