# Sanctum CSS Override + Graph.json Config

> **Session:** 2026-07-05 visual fix release
> **Trigger:** User said "Theme passt nicht — Punkte haben alle gleiche Farbe + Kreise machen unübersichtlich"
> **Fixes:** 3 Files patched/created (graph.json, yuno-folder-colors.css, yuno-clean-file-explorer.css)

## Fix 1: Graph.json Tag-Colorization

### Symptom

All graph nodes are white/gray. Only the central hub node has a color (green via graph's default single-hub coloring). Tags are not reflected in node colors.

### Root Cause

Obsidian's `graph.json` has:
```json
{
  "showTags": false,
  "colorGroups": [],
  ...
}
```

### Solution

```json
{
  "showTags": true,
  "colorGroups": [
    {"query": "tag:#daily", "color": {"a": 0.65, "rgb": 2899180543}},
    {"query": "tag:#moc", "color": {"a": 0.65, "rgb": 4286878434}},
    {"query": "tag:#wiki", "color": {"a": 0.65, "rgb": 4281137716}},
    {"query": "tag:#glossar", "color": {"a": 0.65, "rgb": 4294953215}},
    {"query": "tag:#kontext", "color": {"a": 0.65, "rgb": 4285396290}},
    {"query": "tag:#projekt", "color": {"a": 0.65, "rgb": 4284788309}},
    {"query": "tag:#ressource", "color": {"a": 0.65, "rgb": 4286878434}},
    {"query": "tag:#bereich", "color": {"a": 0.65, "rgb": 4280420456}},
    {"query": "tag:#skill", "color": {"a": 0.65, "rgb": 4281137716}},
    {"query": "tag:#hermes", "color": {"a": 0.65, "rgb": 4280420456}},
    {"query": "tag:#ai", "color": {"a": 0.65, "rgb": 4284788309}},
    {"query": "tag:#ki", "color": {"a": 0.65, "rgb": 4284788309}},
    {"query": "tag:#vault", "color": {"a": 0.65, "rgb": 4286878434}},
    {"query": "tag:#archiv", "color": {"a": 0.65, "rgb": 2873096319}},
    {"query": "tag:#todo", "color": {"a": 0.65, "rgb": 2899180543}},
    {"query": "tag:#offen", "color": {"a": 0.65, "rgb": 2899180543}}
  ],
  "collapse-color-groups": false,
  "lineSizeMultiplier": 0.45,
  "nodeSizeMultiplier": 0.6
}
```

### RGB Integer Conversion (Obsidian Encoding)

Obsidian stores RGB colors as a signed int32 in `graph.json`. The formula:
```
rgb = (255 << 24) | (r << 16) | (g << 8) | b
```

Python helper:
```python
def css_color_to_rgb_int(hex_color: str) -> int:
    """Convert '#a78bfa' → 4286878434"""
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return (255 << 24) | (r << 16) | (g << 8) | b
```

### Basti's Vault Color Mapping

| Color | Hex | RGB Int | Used for |
|-------|-----|---------|----------|
| Coral-Orange | `#f97316` | 2899180543 | daily, todo, offen |
| Purple | `#a78bfa` | 4286878434 | moc, ressource, vault |
| Pink | `#f472b6` | 4281137716 | wiki, skill |
| Sun-Yellow | `#eab308` | 4294953215 | glossar |
| Blue-Sky | `#60a5fa` | 4285396290 | kontext |
| Sky-Blue | `#38bdf8` | 4284788309 | projekt, ai, ki |
| Mint | `#34d399` | 4280420456 | bereich, hermes |
| Gray | `#6b7280` | 2873096319 | archiv |

## Fix 2: Folder-Colorization — Sanctum-compatible Selectors

### Symptom

`yuno-folder-colors.css` shows no effect — folder headers (01 Kontext, 02 Inbox, etc.) are styled only by Sanctum's default, not by the Yuno CSS snippet.

### Root Cause

Sanctum uses specific DOM nesting that the original CSS selectors didn't match. The correct selector chain for Sanctum:

```css
/* Top-Level Folder (01-08) */
.nav-folder.mod-root:has(> .nav-folder-title[data-path="01 Kontext"]) > .nav-folder-title { ... }

/* Sub-Folder */
.nav-folder:not(.mod-root) .nav-folder-title { ... }

/* Active State */
.nav-folder.is-active > .nav-folder-title { ... }
```

### Basti's Folder-Color Mapping (8-Folder Schema)

| Folder | Border Color | Background Gradient | Font Weight |
|--------|-------------|---------------------|-------------|
| 01 Kontext | `--yuno-purple-deep` | `--yuno-purple-soft` → transparent | 700 |
| 02 Inbox | `--yuno-coral` | `--yuno-coral-soft` → transparent | 700 |
| 03 Projekte | `--yuno-sky` | `--yuno-sky-soft` → transparent | 700 |
| 04 Bereiche | `--yuno-mint` | `--yuno-mint-soft` → transparent | 700 |
| 05 Ressourcen | `--yuno-purple` | `--yuno-purple-soft` → transparent | 700 |
| 06 Daily Notes | `--yuno-coral` | `--yuno-coral-soft` → transparent | 700 |
| 07 Archiv | `--yuno-gray` | `--yuno-gray-soft` → transparent | 700, opacity 0.8 |
| 08 Anhänge | `#a78a6b` (tan) | `rgba(167,138,107,0.20)` → transparent | 700 |

Subfolder coloring for projects (03 Projekte/):
```css
.nav-folder:not(.mod-root) .nav-folder-title[data-path^="CP77"],
.nav-folder:not(.mod-root) .nav-folder-title[data-path^="Yuno"] {
  border-left: 2px solid var(--yuno-sky) !important;
  background: rgba(96, 165, 250, 0.06) !important;
}
```

## Fix 3: Sanctum File-Explorer Icon Cleanup

### Symptom

Sanctum shows colored circle badges with single letters next to every file name:
- "B" for Bereich, "D" for Daily Note, "I" for Inbox Note, "P" for Projekt README, "R" for Ressource, "T" for Templates

User described it as *"die Kreise machen das menschliche Lesen sehr unübersichtlich"*.

### Root Cause

Sanctum injects colored SVG icons with letter-glyphs via `body:not(.no-sanctum-icons) svg.lucide-file-*` CSS rules. The theme provides a `body.no-sanctum-icons` class to disable these, but setting it requires either Obsidian CSS class injection (via `app.json` `ignoredCssClasses`) or direct CSS override.

### Solution (yuno-clean-file-explorer.css)

The CSS snippet does:
1. **Opacity-reduction** on all SVG icons in file explorer (0.45 → 0.85 on hover)
2. **Size-reduction**: `width: 14px; height: 14px` (Sanctum default is ~28-32px)
3. **Bullet-style** for files: `·` prefix via `::before` on content elements
4. **Arrow-indicators** for folders: `▸` (collapsed) / `▾` (expanded)
5. **Transparent backgrounds** on icon containers (removes the colored circle base)
6. **Active file** style: `rgba(167, 139, 250, 0.10)` background with Yuno-Purple text

```css
/* Core — icon deactivation */
.nav-files-container .nav-file svg,
.nav-files-container .nav-folder svg {
  opacity: 0.45 !important;
  width: 14px !important;
  height: 14px !important;
}

/* File bullet prefix */
.nav-files-container .nav-file-title-content::before {
  content: "·" !important;
  color: var(--yuno-purple) !important;
  margin-right: 6px !important;
}

/* Folder arrow indicator */
.nav-folder .nav-folder-title-content::before {
  content: "▸" !important;
  color: var(--yuno-purple) !important;
}
```

### Snippet Registration

The new snippet must be registered in `appearance.json` (additive — never remove existing entries):

```json
"enabledCssSnippets": [
  "yuno-variables",
  "yuno-clean-file-explorer",   // NEW — must be after yuno-variables
  "yuno-folder-colors",
  ...
]
```

Also add an entry to the vault's `Snippet-Liste.md`:
```markdown
### yuno-clean-file-explorer.css *(Phase-5.5-Fix, 2026-07-05)*
**Was:** Deaktiviert Sanctums bunte Kreise/Buchstaben-Badges im File-Explorer
und ersetzt sie durch Bullet-Style (`·` für Files, `▸`/`▾` für Folders).
**Basiert auf:** Gestaltungs-Insight von Basti 2026-07-05
```
