# Sanctum CSS Theming für Obsidian Vaults

Sanctum-Theme-Customization-Wissen für Basti's Vault. Dauerhafte Techniken aus Phase 5/5.5 (2026-07-05).

## Problem

Standard-Obsidian mit Sanctum-Theme hat:
- **Bunte Buchstaben-Badges** in Box-Glyph-SVGs für jeden File-Typ ("P" für Projekte, "D" für Daily Notes etc.) — unübersichtlich laut Basti
- **Nur 4 Farben** für Top-Level-Folders laut Phase-5-Setup — zu wenig, "mehr Unterteilungen" gewünscht
- **Keine Hierarchie-Visualisierung** im File-Explorer — alle Ebenen gleich behandelt

## Lösung: 2-stufig

### Stufe 1: Sanctum-Icons deaktivieren

NICHT per CSS-Override allein (zu brüchig), sondern via **Theme-internem Mechanismus**.

**`app.json` (Vault-Konfiguration):**
```json
{
  "ignoredCssClasses": ["no-sanctum-icons"]
}
```

Sanctum definiert einen CSS-Block `body:not(.no-sanctum-icons) svg.lucide-file-plus`, der nur feuert wenn die Klasse NICHT am `<body>` hängt. `ignoredCssClasses: ["no-sanctum-icons"]` in `app.json` setzt diese Klasse beim Laden des Vaults.

**Vorteil:** Theme-Update-resilient (falls Sanctum die Klasse umbenennt → Defense-in-Depth-CSS greift).

**Was wegfällt:** 
- Box-Glyph-SVGs (bunte Kreise mit Buchstaben)
- Lucide-File-Type-Icons
- Diverse Badge-Styles (calendar-check, dice, clock, etc.)

**Was bleibt:**
- Folder-Indicator-Symbole (Sanctum's eigenes nav-folder-indicators-System bleibt aktiv, sofern nicht separat deaktiviert)

### Stufe 2: Defense-in-Depth CSS

Zusätzlich in `yuno-clean-file-explorer.css`:

```css
/* Fallback falls no-sanctum-icons-Mechanik versagt */
body .nav-files-container svg.lucide,
body .nav-folder svg.box-glyph,
body .nav-folder svg.bracket-glyph,
body .nav-file svg.lucide-file-plus {
  opacity: 0 !important;
  width: 0 !important;
  height: 0 !important;
}
```

## Mehr Unterteilungen im Folder-Explorer

### 8 Top-Level + Multi-Level (14 verschiedene Marker)

| Folder | Symbol | Farbe | CSS-Marker |
|--------|--------|-------|-----------|
| 01 Kontext | ✦ | Lila-Deep | `border-left: 4px` + Gradient + Bold |
| 02 Inbox | ⚑ | Coral | `border-left: 4px` + Gradient + Bold |
| 03 Projekte | ◆ | Sky-Blue | `border-left: 4px` + Gradient + Bold |
| 04 Bereiche | ✿ | Mint | `border-left: 4px` + Gradient + Bold |
| 05 Ressourcen | ❖ | Yuno-Purple | `border-left: 4px` + Gradient + Bold |
| 06 Daily Notes | ☼ | Coral-Soft | `border-left: 4px` + Gradient + Bold |
| 07 Archiv | ⚐ | Gray | `border-left: 4px` + Opacity 0.85 |
| 08 Anhänge | ⚓ | Tan/Brown | `border-left: 4px` + Gradient |
| _templates | ❑ | Slate (dashed) | `border-left: 3px dashed` |

### Sub-Folder-Pattern

- **Sub-Folders in 03 Projekte**: Sky-Blue + `├─ ` Prefix
- **Sub-Folders in 05 Ressourcen**: Yuno-Purple + `├─ ` Prefix
- **Tiefe 3 (MOC/Pattern-Subfolders)**: Dashed Purple + `│  └─ ` Prefix
- **Alle Files**: `│  · ` prefix (Tree-Style, monospace)
- **MOC-Files**: `│  ✦ ` prefix (Purple highlight)
- **Daily Notes**: `│  ☼ ` prefix (Coral highlight)
- **Inbox-Files**: `│  ⚑ ` prefix (Coral, bold)

### CSS-Selektor-Formel für Folder-Targeting

Sanctum's DOM-Struktur erfordert `:has()` + `data-path`-Attribut:

```css
/* Top-Level Folder */
.nav-folder.mod-root:has(> .nav-folder-title[data-path="01 Kontext"]) > .nav-folder-title {
  border-left: 4px solid var(--yuno-purple-deep) !important;
  /* Gradient + Font + Symbol via ::before */
}
.nav-folder.mod-root:has(> .nav-folder-title[data-path="01 Kontext"]) .nav-folder-title-content::before {
  content: "✦ " !important;
}

/* Sub-Folder (path prefix match) */
.nav-folder:not(.mod-root) .nav-folder-title[data-path^="CP77"] {
  border-left: 3px solid var(--yuno-sky) !important;
}
.nav-folder:not(.mod-root) .nav-folder-title[data-path^="CP77"] .nav-folder-title-content::before {
  content: "├─ " !important;
}
```

**Wichtig:**
- `:has()` erfordert modernen CSS-Support (Obsidian 1.5+, Chromium 105+)
- `data-path`-Attribut-Selektion mit `^=` (prefix) für Sub-Folders
- `!important` ist nötig wegen Sanctum's CSS-Spezifität

### Yuno-Variables-CSS

```css
/* Palette */
--yuno-purple: #a78bfa;
--yuno-purple-deep: #7c3aed;
--yuno-purple-soft: rgba(167, 139, 250, 0.15);
--yuno-coral: #f472b6;
--yuno-coral-soft: rgba(244, 114, 182, 0.12);
--yuno-sky: #60a5fa;
--yuno-sky-soft: rgba(96, 165, 250, 0.12);
--yuno-mint: #34d399;
--yuno-mint-soft: rgba(52, 211, 153, 0.12);
--yuno-gray: #6b7280;
--yuno-gray-soft: rgba(107, 114, 128, 0.10);
```

## Visual-Fix-Feedback-Loop

Basti kommuniziert visuelle Issues per Screenshot. Fix-Protokoll:

1. **Issue identifizieren** mittels `vision_analyze()` auf Screenshot
2. **Ursache analysieren** per Theme/CSS-DOM-Scan (grep im Theme-CSS, DOM-Struktur via DevTools)
3. **Fix bauen** als CSS-Snippet oder `app.json`-Setting
4. **Test + Backup** (`.obsidian.backup-visualfix-<timestamp>`)
5. **Basti tested** per Obsidian-Reload (Strg+R) + neues Screenshot
6. **Iterieren** falls mehr Feedback kommt

## Snippet-Liste (Stand 2026-07-05, 9 aktive)

| Snippet | Zeilen | Zweck |
|---------|--------|-------|
| `yuno-variables.css` | 2 | CSS-Variablen (Palette) |
| `yuno-folder-colors.css` | 35 | **v3**: 8 Folder + Sub + Tree-Indent |
| `yuno-clean-file-explorer.css` | 2 | **v2**: Defense-in-Depth Icons aus |
| `yuno-tag-colors.css` | 16 | Tag-Farben + ::before-Icons |
| `yuno-callout-icons.css` | 25 | Emoji-Callout-Header |
| `yuno-callouts.css` | 13 | Callout-Styling |
| `yuno-moc-style.css` | 18 | MOC-Style (Dataview-Table-Buttons) |
| `yuno-wiki-links.css` | 13 | Wiki-Link-Visual (underline + color) |
| `yuno-daily-note-style.css` | 10 | Daily-Header-Formatierung |

## Schema: Snippet aktivieren

1. Snippet `.css` in `{vault}/.obsidian/snippets/` ablegen
2. In `appearance.json` unter `enabledCssSnippets` listen
3. Cache: `Ctrl+R` (Force-Reload) in Obsidian
4. Falls nicht sichtbar: Obsidian komplett neu starten

## Quellen

- Sanctum Theme: `~/.var/app/md.obsidian.Obsidian/config/obsidian/themes/` → Vault-lokal in `.obsidian/themes/sanctum.css`
- Produziert in Obsidian Vault Phase 5 + 5.5, 2026-07-05
- Vault-Backups: `.obsidian.backup-phase5-*`, `.obsidian.backup-visualfix-*`
