# Theme-Mapping-Layer Pattern

**Gefunden:** 2026-07-08 (Yuno Dashboard v2 Redesign)
**Quelle:** Variante 03 → `yuno-ui/index.html` deployed in `~/10-Projekte/10-active/yuno-ui/`

## Problemstellung

Ein Dashboard mit **Token-System** (`colors.css`) und **Theme-Switcher** (4 Modi: Cozy/Dark/Cyber/HC) braucht eine Brücke zwischen:

1. **Token-System** — definiert Farb-Primitive pro Shade (z.B. `--yuno-pink-500: #FF1493`)
2. **Theme-Switcher** — ändert die semantische Zuordnung pro Mode (z.B. "Akzent im Cozy-Mode = Indigo, nicht Pink")
3. **Layout-CSS** — verwendet Layout-Variablen (z.B. `--yuno-accent-strong`)

Naiver Ansatz — das Token-System pro Mode zu überschreiben — zerstört die Mode-Kompatibilität: Wenn `--yuno-pink-500` im Cozy-Mode plötzlich Indigo ist, passen die Farb-Mappings nicht mehr.

## Lösung: Drei CSS-Schichten

```
Layer 1: Token-System (colors.css)         →  :root { --yuno-pink-500: #FF1493; ... }
                                                  ┌──────────────────────────────┐
Layer 2: Theme-Mapping-Layer                →  │ [data-theme="cozy"] {         │
   (im Dashboard-HTML, NICHT in colors.css)  │   --yuno-accent-strong: #4338ca;│
                                                  └──────────────────────────────┘
Layer 3: Layout-CSS (im HTML)               →  .kpi-value { color: var(--yuno-accent-strong); }
```

### Layer 1: Token-System (colors.css)

Unverändert. Definiert Farbpalette mit 50-950 Scale pro Farbe.
**Nicht editieren** für Theme-Switcher — das bricht die Mode-Kompatibilität.

### Layer 2: Theme-Mapping-Layer

Definiert für jeden Mode `[data-theme="X"]` welche Layout-Variable welchen Wert hat.
Die Werte können entweder aus dem Token-System stammen (`var(--yuno-cream-50)`) oder hardcoded sein (für Modes, die eigene Farben brauchen — z.B. HC-Mode mit pure-black).

**Empfohlene Layout-Variablen:**

```css
--yuno-bg              /* Page-Hintergrund */
--yuno-bg-subtle       /* Subtle regions (sidebar-inactive, hover) */
--yuno-bg-panel        /* Card/Table-Hintergrund */
--yuno-bg-sidebar      /* Sidebar-Hintergrund */
--yuno-accent-strong   /* Primär-Akzent (Buttons, active-state, Status-Tags) */
--yuno-accent-soft     /* Sekundär-Akzent (Borders, muted-links) */
--yuno-accent-glow     /* Box-Shadow für Neon-Glow (transparent in HC) */
--yuno-fg-primary      /* Primär-Text */
--yuno-fg-secondary    /* Sekundär-Text (Labels, Hilfetexte) */
--yuno-border          /* Border/Card-Trennung */
--yuno-success         /* Erfolg (KPI-Trend, Status-Tag) */
--yuno-warning         /* Warnung (Disk >70%, Cron-Stau) */
--yuno-error           /* Fehler (KPI-Trend, Status-Tag) */
```

### Layer 3: Layout-CSS

Verwendet `var(--yuno-*)` für alle sichtbaren Farben.
Kein Hardcoded-Hex außerhalb des Mapping-Layers.

```css
.kpi-card {
  background: var(--yuno-bg-panel);
  border: 1px solid var(--yuno-border);
  color: var(--yuno-fg-primary);
}
.kpi-trend-success { color: var(--yuno-success); }
.kpi-trend-error   { color: var(--yuno-error); }
```

## Theme-Defaults (bewährt)

| Mode | `--yuno-bg` | `--yuno-accent-strong` | wann verwenden |
|------|-------------|------------------------|----------------|
| **Cozy** | Cream `#FFF5F5` | Indigo `#4338ca` | Tageslicht, extended use |
| **Dark** | Dark-Grey `#0f0f11` | Pink `#FF1493` | Abends, Brand-heavy |
| **Cyber** | Deep-Purple `#0D0020` | Fuchsia `#d946ef` | Power-User, Neon-Lover |
| **HC** | Pure Black `#000000` | Bright-Pink `#FF6BC6` | A11y AAA, maximale Lesbarkeit |

## Theme-Switcher JS

```javascript
function setTheme(name) {
  document.documentElement.setAttribute('data-theme', name);
  localStorage.setItem('yuno-theme', name);
  // Buttons aktualisieren
  document.querySelectorAll('.theme-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.theme === name)
  );
}

// Beim Page-Load: gespeichertes Theme oder Default
const saved = localStorage.getItem('yuno-theme');
setTheme(saved || 'cozy');
```

## Akzent-Farben für Light-Mode (2026-07-08 Insight)

**Problem:** Pink-500 (`#FF1493`) auf Cream-BG (`#FFF5F5`) = 4.5:1 → gerade so AA, aber unangenehm bei längerem Lesen.

| Akzent | Ratio auf Cream | Bewertung |
|--------|----------------|-----------|
| **Pink-500** `#FF1493` | 4.5:1 | Gerade so AA, bunt, ermüdend |
| **Pink-800** `#C2185B` | 6.03:1 | AA-sicher, Brand-fidel |
| **Indigo-700** `#4338ca` | 6.03:1 | AA-sicher, LESS ermüdend |
| **Purple-700** `#7E22CE` | 6.98:1 | AA, calm, gut für Extended-Use |

**Empfehlung:** Für Tageslicht- / Cozy-Mode Indigo-700 oder Purple-700 statt Pink. Pink-800 als Kompromiss wenn Brand-Fidelity Priorität hat.

## Integration mit ui-factory / sketch

Wenn User eine Variante aus dem `sketch`-Workflow wählt:

1. **Gewinner-Variante** (z.B. Data-Dense) als Basis nehmen
2. **Token-System** aus bestehendem Projekt übernehmen (`tokens/colors.css`)
3. **Theme-Mapping-Layer** erstellen mit 4 Modi
4. **Layout-CSS** der gewählten Variante auf `var(--yuno-*)` umstellen
5. **Kein Hardcoding** — jede sichtbare Farbe kommt aus dem Mapping-Layer

## Referenz-Implementation

Siehe `~/10-Projekte/10-active/yuno-ui/index.html`:
- Token-System: `tokens/colors.css` (Layer 1)
- Theme-Mapping-Layer: Inline-CSS im `<style>` ab `/* === THEME MAPPING LAYER ===` (Layer 2)
- Layout-CSS: Rest der Datei mit `var(--yuno-*)` References (Layer 3)
- Screenshots: `~/Bilder/yuno-gallery/dashboard-v2-2026-07-08/`

## Verwandte Pitfalls

- **HC-Mode Cards unsichtbar:** Page-BG = Card-BG = #000 → Card-BG auf `#0A0A0A` setzen (4% heller) und weiße Borders hinzufügen
- **localStorage vor Headless Chrome:** Für JS-basierte Theme-Switcher brauchst du einen localStorage-Wrapper — siehe `references/landing-page-build-2026-07-08.md` in `ui-factory`
- **Sparkline-Farben:** Bei Inline-SVG-Sparklines die Farbe via `var(--yuno-accent-strong)` setzen, nicht hardcoded — sonst brechen sie beim Theme-Wechsel
