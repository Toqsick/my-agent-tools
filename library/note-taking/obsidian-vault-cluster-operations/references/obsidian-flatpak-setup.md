# Obsidian Flatpak — Pfad-Konvention (Stand 2026-07-05)

## Warum dieses Doc

Bastis Obsidian läuft als **Flatpak** (`md.obsidian.Obsidian` 1.12.7). Der Config-Pfad weicht von der Standard-Installation ab. Diese Datei dokumentiert die gefundenen Pfade, damit künftige Sessions nicht wieder in `~/.config/obsidian/` suchen.

## Pfad-Architektur

### Globaler Flatpak-Config-Pfad

```
~/.var/app/md.obsidian.Obsidian/config/obsidian/
```

Hier landet alles, was Obsidian global speichert:
- `obsidian.json` — Haupt-Einstellungen (Theme, CSS-Snippets-Aktivierung, Hotkeys)
- `community-themes.json` — installierte Themes
- `community-plugins.json` — Plugin-Registry

**Wichtig**: `themes/`, `plugins/` und `snippets/`-Ordner existieren hier **NICHT** standardmäßig. Diese sind **Vault-lokal**.

### Vault-lokale Config

Jeder Vault hat sein eigenes `.obsidian/`-Verzeichnis:

```
/home/bratan/Dokumente/Obsidian Vault/.obsidian/
├── appearance.json     — Theme- + Snippet-Konfiguration
├── community-themes.json
├── snippets/           — CSS-Snippet-Dateien (.css)
├── themes/             — Theme-Dateien (.css)
├── plugins/            — Community-Plugins (Code + Manifest)
├── app.json            — App-Einstellungen
├── community-plugins.json
├── core-plugins.json
├── core-plugins-migration.json
├── graph.json
└── workspace.json
```

### Wichtige Unterscheidung

| Pfad | Was | Wird von wem gelesen |
|------|-----|---------------------|
| `~/.var/app/.../config/obsidian/obsidian.json` | Globale Settings (Theme-Name, Snippet-Enable) | Obsidian Flatpak beim Start |
| `<vault>/.obsidian/appearance.json` | Vault-spezifische Theme + Snippet-Config | Obsidian per Vault |
| `<vault>/.obsidian/snippets/*.css` | CSS-Snippet-Dateien | Obsidian CSS-Engine |
| `<vault>/.obsidian/themes/*/*.css` | Theme-CSS-Dateien | Obsidian CSS-Engine |

## Flatpak-spezifische Besonderheiten

- **Keine globalen `themes/`**, `plugins/` oder `snippets/`-Ordner im Flatpak-Config-Pfad — alles Vault-lokal
- **Flatpak-Sandbox**: `~/.var/app/md.obsidian.Obsidian/` ist die Sandbox-Home — dort darf geschrieben werden
- **kein `$XDG_CONFIG_HOME`** — Flatpak ignoriert XDG, verwendet fixen Pfad
- **Theme wird in beiden Configs gelistet**: `obsidian.json` (global, Theme-Name) + `appearance.json` (vault-lokal, Theme-Name + CSS-Snippet-Enabled-Array)
- **CSS-Snippets-Enable-Liste** steht in `<vault>/.obsidian/appearance.json[enabledCssSnippets]` — das ist ein String-Array, Reihenfolge ist Lade-Reihenfolge! `yuno-variables.css` muss IMMER zuerst stehen (Variable-Definitionen)

## Sanktum-Theme (Live seit 2026-07-05)

| Property | Value |
|----------|-------|
| Name | `Sanctum` |
| Pfad | `<vault>/.obsidian/themes/Sanctum/manifest.json` |
| CSS | `<vault>/.obsidian/themes/Sanctum/theme.css` (420 KB) |
| Modus | `obsidian` (dark mode) |
| Quelle | GitHub: `https://github.com/jdanielmourao/obsidian-sanctum/releases/` |
| Status | aktiv |

## Aktive CSS-Snippets (Stand 2026-07-05)

Lade-Reihenfolge (aus `appearance.json[enabledCssSnippets]`):

1. `yuno-variables` — Variable-Definitionen (Purple-Palette)
2. `yuno-moc-style` — MOC-Sektionen, Boxen, Grid
3. `yuno-callout-icons` — Emoji-Icons für Callout-Titel
4. `yuno-daily-note-style` — Daily-Note-Hover-Effekte
5. `yuno-wiki-link-style` — Wiki-Link-Visuals
6. `yuno-link-graph` — Graph-View-Knoten-Stile
7. `yuno-metadata-panel` — Properties-Panel
8. `yuno-heading-underline` — Überschriften-Visuals

## Nützliche Terminal-Befehle für Obsidian-Setup

```bash
# Theme-Order erstellen (falls nicht vorhanden)
mkdir -p "<vault>/.obsidian/themes/<theme-name>"

# CSS-Snippet aktivieren (appearance.json editieren)
# enabledCssSnippets: [\"snippet1\", \"snippet2\", ...]
python3 -c "
import json
with open('<vault>/.obsidian/appearance.json') as f:
    c = json.load(f)
c['enabledCssSnippets'] = ['yuno-variables', 'snippet2', ...]
with open('<vault>/.obsidian/appearance.json', 'w') as f:
    json.dump(c, f, indent=2)
"

# Prüfen ob Obsidian Flatpak läuft
ps aux | grep -i obsidian

# Flatpak-Obsidian starten
flatpak run md.obsidian.Obsidian
```

## Anti-Patterns

- ❌ **In `~/.config/obsidian/` nach Config suchen** — das ist der Pfad für Linux-native Installationen, nicht Flatpak
- ❌ **Theme direkt in `<vault>/.obsidian/` ablegen** — muss im `themes/<name>/`-Unterordner liegen
- ❌ **CSS-Snippets ohne `yuno-variables` zuerst** — Variable-Definitionen müssen vor den Snippet-Styles geladen werden (CSS-Spezifität)
- ❌ **`appearance.json` manuell editieren ohne JSON-Validierung** — ein Syntax-Fehler deaktiviert ALLE Snippets beim nächsten Start

## Siehe auch

- `references/phase-6-results.md` — Vollständiger Phase-6-Bericht
- `~/docs/system/vault-update-strategy-2026-07-05.md` — Wartungs-Strategie
- `05 Ressourcen/Obsidian-Plugins-Setup.md` — Plugin-Infos im Vault
- `05 Ressourcen/Snippet-Liste.md` — Alle Snippets mit Beschreibung
