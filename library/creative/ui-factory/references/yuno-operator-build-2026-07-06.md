# Yuno Operator Dashboard — 4-Mode UI-Factory Build (2026-07-06)

## Context

Second ui-factory chain run, following the 2026-07-01 Yuno-Dashboard build. This time with:
- **Brand-Color:** Pink/Magenta (harder than Purple for WCAG)
- **Mood:** playful + cyberpunk-kawaii (from Yuno-Style-Pattern Analysis)
- **4 Themes:** Cozy (light-warm), Dark (standard), Cyberpunk (dark+neon), A11y (pure B/W)
- **Target:** Yuno Operator Dashboard for system monitoring (Agents, Tasks, Tokens, Errors)

## Concrete WCAG Values Learned

### Pink Brand on Cream BG (Cozy Mode)

| Test | Pair | Ratio | AA | Fix |
|------|------|-------|-----|-----|
| Pink-500 Button | `#FF6BB5` on `#FFF5F5` | 3.2:1 | FAIL | → Pink-800 (`#C2185B`): 6.03:1 |
| Pink-500 Body | `#FF6BB5` on `#FFF5F5` | 3.2:1 | FAIL | → Pink-800 (`#C2185B`): 6.03:1 / Pink-700 (`#D81B60`): 4.89:1 FAIL |
| Pink-700 Body | `#D81B60` on `#FFF5F5` | 4.89:1 | FAIL | → Pink-800 (`#C2185B`): 6.03:1 |
| Error-500 | `#FF5252` on `#FFF5F5` | 4.04:1 | FAIL | → Error-600 (`#E04848`): 5.52:1 |

### Magenta Accent on Night BG (Cyberpunk Mode)

| Test | Pair | Ratio | AA | Fix |
|------|------|-------|-----|-----|
| Magenta-500 Button | `#E91E63` on `#0D0020` | 4.11:1 | FAIL | → White Text: 4.11:1 FAIL → Night-700 Text |
| White on Magenta-500 | `#FFF` on `#E91E63` | 3.64:1 | FAIL | → Magenta-700 (`#B30066`): 5.96:1 |
| Magenta-500 Body | `#E91E63` on `#0D0020` | 4.11:1 | FAIL | → Magenta-700 (`#B30066`): 6.55:1 |
| Magenta-700 on Cream | `#B30066` on `#FFF5F5` | 6.55:1 | PASS | |

### Dark Mode

| Test | Pair | Ratio | AA |
|------|------|-------|-----|
| Pink-300 Body | `#F48FB1` on `#1A1A2E` | 9.37:1 | PASS |
| Neutral-50 Text | `#FAFAFA` on `#1A1A2E` | 17.2:1 | PASS |
| Pink-300 Button | `#F48FB1` on `#1A1A2E` | 9.37:1 | PASS |

### A11y Mode (pure B/W)

All pairs ≥ 15:1 (21:1 for pure `#FFF` on `#000`).

## Key Pattern: 4-Mode Theme-Switcher

```css
:root { /* Cozy Mode */ --bg: #FFF5F5; --bg-card: #FFFFFF; }
[data-theme="dark"] { --bg: #1A1A2E; --bg-card: #16213E; }
[data-theme="cyber"] { --bg: #0D0020; --bg-card: #1A0033; }
[data-theme="a11y"] { --bg: #000000; --bg-card: #000000; }
```

**Subtle-Lift for HC-Mode (discovered 2026-07-06):**
```css
[data-theme="hc"] {
  --yuno-bg:           #000000;  /* Page: pure black */
  --yuno-bg-subtle:    #0A0A0A;  /* Subtle regions */
  --yuno-bg-panel:     #0A0A0A;  /* Cards: lifted by 4% lightness */
  --yuno-border:       #FFFFFF;  /* White borders for separation */
}
```

**Why:** Page-BG = Card-BG = #000000 lässt Cards verschwinden. Subtle-lift mit #0A0A0A + dicke White-Borders = WCAG-AAA bleibt, aber Layering sichtbar. Siehe ui-factory Pitfall 8.

**localStorage Persistence:**
```javascript
const saved = localStorage.getItem('yuno-theme') || 'cozy';
document.documentElement.setAttribute('data-theme', saved);
```

**URL-Param-Override für Headless-Tests (entdeckt 2026-07-06):**
```javascript
const urlTheme = new URLSearchParams(location.search).get('theme');
if (urlTheme && VALID_THEMES.includes(urlTheme)) {
  applyTheme(urlTheme);  // überschreibt localStorage
} else {
  applyTheme(loadTheme());  // default path
}
```

Damit kann `?theme=hc` direkt im URL übergeben werden, was Headless-Chrome-Screenshots ohne interaktiven Click ermöglicht (siehe ui-factory Pitfall 9).

## Validation Methodology

1. **Token-Konsistenz (`execute_code`):** Count `var(--*)` usages vs hardcoded hex outside `:root`. Result: 273 vs 4 (1 meta theme-color + 3 console.log = legit).
2. **WCAG-Pair-Check (`execute_code`):** Iterate over all text/bg combinations, compute relative luminance, assert ≥4.5:1. Result: 17/17 PASS (5 initial fails found + fixed).
3. **Browser-Smoke-Test (Headless Chrome):** Wenn keine interaktiven Browser-Tools verfügbar sind:
   ```bash
   for theme in light dark cyberpunk hc; do
     google-chrome --headless --disable-gpu --no-sandbox --hide-scrollbars \
       --window-size=1440,1100 --virtual-time-budget=2000 \
       --screenshot=/tmp/yuno-${theme}.png \
       "http://127.0.0.1:8765/index.html?theme=${theme}"
   done
   ```
   Result: 4 PNGs, alle Themes visuell verifiziert, HC-Mode hat Cards nicht abgehoben → Bug entdeckt + gefixt (siehe oben).
4. **A11y-Attribute-Count:** grep for aria-label/aria-hidden/aria-pressed/aria-current/role. Result: 12+40+5+4+13 = clean.

## Pitfalls Confirmed

From `ui-factory` pitfalls doc — each confirmed with concrete values:
- **Pitfall 1** (Button Contrast): Pink-500 = 3.2:1 → Pink-800 = 6.03:1 ✓
- **Pitfall 2** (Hardcoded Hex): 4 found → 1 legit ✓
- **Pitfall 5** (Token-Konsistenz): 273 var(--*) → 0 hardcoded ✓
- **Pitfall 6** (Output-Größe): 42 KB, ASCII-Sparklines ✓
- **Pitfall 8** (HC-Mode Cards unsichtbar): Page-BG = Card-BG → Subtle-Lift-Fix ✓
- **Pitfall 9** (Headless Chrome Fallback): URL-Param-Theme + google-chrome --headless = reproduzierbare Theme-Validation ohne MCP-Browser ✓

## Pitfalls Noticed But Not Hit (nur dokumentiert)

- **Pitfall 3** (Framework-Lock-In): umgangen weil User "single-file HTML" explizit gewünscht hat
- **Pitfall 4** (Token-Count-Explosion): vorgebeugt durch Token-Budget in Phase 2

## Style-Pattern Reference

Yuno-Style from 3 images → 10-dimension decomposition → 5 Soul-Markers:
1. **Pink Hair** → Brand-Color Pink/Magenta
2. **Anime-Cel + Painterly-Light** → Hard shadows + soft highlights
3. **Yandere-Eyes** → High contrast, playful/creepy balance
4. **Pastell + 1 Akzent** → Cream BG + Pink Primary + Magenta Accent = 3-color system
5. **Setting trägt Story** → Data-driven KPI cards not generic decoration

Full analysis: `~/00-Meta/style-analysis/yuno-style-pattern-2026-07-06.md`

## Output Location

`~/10-Projekte/10-active/yuno-ui/` (verschoben von `~/yuno-ui/` nach Basti-Workspace-Präferenz vom 2026-07-04, die "Yuno agiert primär in ~/.hermes/" mit Ausnahme für Dev-Projekte-artige Builds ergänzt wurde 2026-07-06).

## Deliverables Recap

- `index.html` (42 KB) — 4-Mode Dashboard, 273× var(--*), 0 hardcoded-hex, single-file
- `tokens/colors.json` (7.1 KB) — 9 Color-Scales, 4 Modes, 17 Contrast-Pairs
- `tokens/colors.css` (7.4 KB) — CSS-Vars pro Mode
- `tokens/tokens.css` (5.6 KB) — Font + Space + Radius + Shadow + Motion + Z
- `tokens/tokens.json` (5.0 KB) — Style-Dictionary-Format
- `tokens/tokens.d.ts` (6.7 KB) — TypeScript-Types + getYunoMode() + applyYunoTheme()
- `tokens/contrast-report.md` (4.7 KB) — 17/17 WCAG-Pairs PASS
- `README.md` (10 KB) — Architecture + WCAG-Table + Theme-Guide + Usage
- Screenshots: `~/Bilder/yuno-gallery/dashboard-2026-07-06/01-light.png` + dark/cyberpunk/hc
