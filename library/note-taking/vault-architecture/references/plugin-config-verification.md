# Obsidian Plugin Config Verification

> Referenz: Wie man den Plugin-Status eines Obsidian-Vaults aus `.obsidian/`-Config-Dateien verifiziert.
> Angelegt: 2026-07-05, aus Session "Obsidian Plugin-Status verifizieren + Install-Anleitungen schreiben"

## Locale-Pitfall: Vault-Pfad

Auf deutschsprachigen Linux-Installationen (Zorin OS, Ubuntu mit de_DE-Locale) heißt das Benutzerverzeichnis `~/Dokumente/`, nicht `~/Documents/`.

| System-Locale | Typischer Vault-Pfad |
|---|---|
| en_US / Standard | `~/Documents/Obsidian Vault/` |
| de_DE / German | `~/Dokumente/Obsidian Vault/` |

**Erkennung:** Mit `terminal` prüfen, ob der Pfad existiert:

```bash
ls -d ~/Dokumente/Obsidian\ Vault/ 2>/dev/null || ls -d ~/Documents/Obsidian\ Vault/ 2>/dev/null
```

Oder `OBSIDIAN_VAULT_PATH` aus `~/.hermes/.env` laden.

## `.obsidian/` — die Config-Zentrale

Jeder Vault hat einen versteckten `.obsidian/`-Ordner im Vault-Root. Dieser enthält alle Obsidian-Configs und Plugin-Daten.

```
.obsidian/
├── app.json                     # Vault-Optionen (promptDelete, etc.)
├── appearance.json              # Theme, Akzentfarbe
├── core-plugins.json            # Core-Plugin-Status (true = aktiviert)
├── graph.json                   # Graph-Einstellungen
├── workspace.json               # Workspace-Layout (Fenster, Panels)
├── community-plugins.json       # (optional) Aktivierte Community-Plugins
├── plugins/                     # (optional) Installierte Community-Plugin-Ordner
│   └── <plugin-name>/
│       ├── manifest.json
│       ├── main.js
│       └── styles.css
└── snippets/                    # (optional) CSS Snippets
```

### Was bedeuten die Dateien?

### `core-plugins.json`

Listet alle eingebauten Obsidian-Plugins mit `true`/`false`:

```json
{
  "file-explorer": true,
  "global-search": true,
  "switcher": true,
  "graph": true,
  "backlink": true,
  "canvas": true,
  "outgoing-link": true,
  "tag-pane": true,
  "properties": true,
  "daily-notes": true,
  "templates": true,
  "note-composer": true,
  "command-palette": true,
  "editor-status": true,
  "bookmarks": true,
  "outline": true,
  "word-count": true,
  "file-recovery": true,
  "sync": true,
  "bases": true
}
```

**Typische standardmäßig deaktivierte Core-Plugins** (nicht installiert/gebraucht): `footnotes`, `slash-command`, `markdown-importer`, `zk-prefixer`, `random-note`, `slides`, `audio-recorder`, `workspaces`, `publish`, `webviewer`.

### `community-plugins.json` + `plugins/`

**Existiert nicht = nie initialisiert.** Das Community-Plugin-System wird erst aktiv, wenn der Benutzer in Obsidian Settings → Community Plugins → Restricted Mode deaktiviert. Dadurch werden automatisch erstellt:
- `.obsidian/community-plugins.json` (leeres JSON-Array `[]`)
- `.obsidian/plugins/` (leeres Verzeichnis)

**Wenn die Dateien existieren:**

```json
// community-plugins.json (aktivierte Community-Plugins)
["dataview", "templater-obsidian", "obsidian-calendar-plugin"]
```

Und `plugins/` enthält die installierten Ordner. **Wichtig:** Ein Plugin kann in `community-plugins.json` gelistet sein, ohne dass der Ordner in `plugins/` existiert (wenn es deinstalliert wurde).

Der Unterschied:

| Zustand | `community-plugins.json` | `plugins/<name>/` | Im Obsidian-UI |
|---|---|---|---|
| Nie initialisiert | ❌ fehlt | ❌ fehlt | "Restricted Mode" aktiv |
| Aktiviert | ✅ `["dataview"]` | ✅ `dataview/manifest.json` + `main.js` | Enabled, funktionsfähig |
| Deaktiviert | ✅ `[]` | ✅ `dataview/manifest.json` + `main.js` | Im UI disabled, aber Code liegt |
| Deinstalliert | ✅ `[]` | ❌ fehlt | Nicht in der Liste |

## Verifizierungs-Workflow (read-only)

```bash
# 1. Vault-Root bestimmen
echo "$OBSIDIAN_VAULT_PATH"
ls -d ~/Dokumente/Obsidian\ Vault/

# 2. Existiert .obsidian/?
ls ~/Dokumente/Obsidian\ Vault/.obsidian/

# 3. Core-Plugins-Status
cat ~/Dokumente/Obsidian\ Vault/.obsidian/core-plugins.json

# 4. Community-Plugin-System initialisiert?
ls ~/Dokumente/Obsidian\ Vault/.obsidian/community-plugins.json 2>&1
ls ~/Dokumente/Obsidian\ Vault/.obsidian/plugins/ 2>&1

# 5. Welche Plugins sind installiert?
ls ~/Dokumente/Obsidian\ Vault/.obsidian/plugins/

# 6. JSON-Inhalt community-plugins.json (falls vorhanden)
cat ~/Dokumente/Obsidian\ Vault/.obsidian/community-plugins.json
```

## Installations-Guides schreiben (als Vault-Notiz)

Wenn der Auftrag lautet "Installationsanleitungen für Plugin X schreiben", empfiehlt sich dieses Format:

### Struktur pro Plugin

1. **Kurzzusammenfassung** — 1 Satz: was macht das Plugin, warum brauchen wir es
2. **Installation (Schritt-für-Schritt)** — nummeriert, mit konkreten Befehlen/UI-Pfaden
3. **Konfiguration** — welche Settings müssen angepasst werden
4. **Verifikation** — wie prüfe ich, dass es funktioniert
5. **Bekannte Stolperfallen** — typische Fehler + Lösung

### Beispiel-Pattern: Erstes Community-Plugin installieren

| Schritt | Aktion |
|---|---|
| 1 | Vault in Obsidian öffnen |
| 2 | Settings → Community Plugins → Restricted Mode deaktivieren |
| 3 | Warnung bestätigen (erstellt `community-plugins.json` + `plugins/`) |
| 4 | Browse → Plugin suchen → Install |
| 5 | Enable |
| 6 | Settings des Plugins konfigurieren |
| 7 | Verifizieren (z.B. Query ausführen, Template einfügen) |

### Info: Core-Plugin-Konflikte

Bei Core-Plugins, die durch Community-Plugins ersetzt werden (z.B. `templates` → `Templater`):
- Core-Plugin kann aktiv bleiben (Konflikte sind selten)
- Oder Core-Plugin deaktivieren (`core-plugins.json` → `false`)
- Templater's Template-Folder anders setzen als das Core-Plugin, um Doppel-Konflikte zu vermeiden

## Bekannte Stolperfallen

- **Locale-Pfad**: Auf deutschen Systemen `~/Dokumente/` statt `~/Documents/`
- **Community-System nie initialisiert**: `community-plugins.json` + `plugins/` fehlen komplett — kein Bug, sondern Feature (Restricted Mode)
- **Deinstalliert ≠ deaktiviert**: `plugins/`-Ordner fehlt, aber Eintrag in `community-plugins.json` kann Remain sein
- **Snippets-Ordner**: Existiert nur, wenn mindestens ein CSS-Snippet aktiv ist — Fehlen ist normal
- **Workspace.json**: Enthält Fenster-/Panel-Layout; nach Plugin-Installation kann sich der Workspace ändern (neue Panels)
