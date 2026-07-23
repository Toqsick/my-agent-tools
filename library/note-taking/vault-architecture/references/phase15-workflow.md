# Phase 15: External Markdown Import & Encyclopedic Integration

> **Systematischer Import & Vernetzung externer Wissensquellen.** Ermöglicht das Zusammenführen von dezentralen `.md`-Dateien (z. B. aus `~/.hermes/`, `~/Downloads/`, `~/00-Meta/`) zu einem hochgradig integrierten, enzyklopädischen Wissensarchiv, ohne den Graphen durch tote Links oder Dubletten zu beschädigen.

## Trigger-Bedingungen

- Der Nutzer wünscht den Import von Dokumenten, Manuals, Personas, Handbüchern oder Protokollen aus Systemordnern.
- Komplexe, historisch gewachsene Verzeichnisse mit `.md`-Dateien sollen im Vault zentral abgebildet werden.

## Workflow (4 Schritte)

### 1. Gezielte Dateiselektion (Ground-Truth-Scan)

Scanne Quellverzeichnisse selektiv. **Wichtig**: Schließe riesige Verzeichnisse (wie `node_modules`, `venv`, `cache`, `.cache`, `.var`) explizit aus, um nicht tausende nutzloser Hilfsdateien einzuschleusen.

### 2. Format-Veredelung (Standardized Frontmatter)

Bereinige den Dateikopf: Entferne die erste Titel-Überschrift (`# ...`), falls vorhanden, um doppelte Titel in Obsidian zu verhindern.

Prepend ein einheitliches YAML-Frontmatter mit:
- `tags: [...]` (thematisch passend)
- `aliases: [...]` (für flexible Verlinkung)
- `source_path: "..."` (Dokumenten-Herkunft für Rückverfolgbarkeit)
- `imported: YYYY-MM-DD` (Zeitstempel)

### 3. Automatisierte Quervernetzung (Networking)

**Inline-Links**: Verwende einen Case-Insensitive Stems-Filter, um ungelinkte Erwähnungen anderer Notizen im Text aufzudecken.

**Footer-Verbindung**: Hänge an jede importierte Datei eine dedizierte `## Verbindet zu`-Sektion an, die mindestens 3 relevante Kanten (andere Notizen, übergeordnete MOCs, Working Agreements) definiert.

**Zentral-Indexe pflegen**: Füge die importierten Dateien sofort als neue Zeilen/Einträge in deine Kern-Navigations-Notizen (`MOC - Home`, Themen-MOCs wie `MOC - KI-Architektur`, `MOC - Ressourcen`) ein.

### 4. Post-Import-Qualitätsprüfung (Audit)

Lasse ein präzises Python-Skript laufen, um sicherzustellen, dass:
- **0 echte broken Links** existieren (Achtung auf Escaped-Pipes in Tabellen!).
- **0 dünne Notizen** (< 40 Zeilen) existieren. Ergänze dünne Notizen im Zweifel proaktiv um "Schnell-Befehle" oder Best-Practice-Codeblöcke.