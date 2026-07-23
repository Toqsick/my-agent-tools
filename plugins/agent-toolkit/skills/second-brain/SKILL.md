---
name: second-brain
description: Bastis Obsidian Vault als Domän-Wissensbank nutzen. Verwenden bei Fragen zu Bastis Wissen/Notizen ("was weiß ich über X", "steht dazu was im Vault?"), zum Nachschlagen von System-/Projekt-Kontext (Gaming-Performance, KI-Architektur, Security, Yuno/Hermes), zum Erfassen neuer Notizen/Erkenntnisse, für Daily Notes, oder zum Erstellen/Lesen von Excalidraw-Skizzen im Vault.
---

# Second Brain — Bastis Obsidian Vault

Vault-Pfad: `/home/bratan/Dokumente/Obsidian Vault/` — lokales Markdown, Zugriff direkt per Read/Grep/Glob (kein MCP nötig). Julian-Ivanov-8-Ordner-Struktur ("KI-Betriebssystem"), ~164 Notizen, stark quervernetzt über Wiki-Links.

## Struktur

| Ordner | Inhalt |
|---|---|
| `01 Kontext/` | Wer/Was: Basti-Profil, Hardware (ERAZER 17 P1), Yuno-Identität, Working Agreement |
| `02 Inbox/` | Quick-Pickup-Notizen, Lebensdauer max. 7 Tage, dann einsortieren |
| `03 Projekte/` | Aktive Projekte |
| `04 Bereiche/` | Dauerhafte Verantwortungsbereiche |
| `05 Ressourcen/` | Referenzwissen |
| `06 Daily Notes/` | Tagesjournal |
| `07 Archiv/` | Abgeschlossenes |
| `08 Anhaenge/` | Attachments (Bilder, Audio) |
| `09 System-Doku/` | Import der System-Dokumentation (Spiegel von `~/docs/system/`) |
| `99 Capture/` | Automatische Captures (z.B. GreyHack-Sessions) |
| `_templates/` | Templater-Vorlagen: `Inbox-Note.md`, `Daily Note.md`, `Bereich.md`, `Ressource.md`, `Projekt README.md` |

Einstiegspunkte auf Top-Level: `MOC - Home.md` (Hub), Themen-MOCs (`MOC - Gaming-Performance`, `MOC - KI-Architektur`, `MOC - Security-Hardening`, `MOC - System-Tuning`, `MOC - System-Wartung`, `MOC - Voice-Pipeline`, `MOC - Lernen & Orchestration`, `MOC - Content-Creation`, `MOC - Obsidian-Vault`, `MOC - System-Doku`, `MOC - Daily Notes`), `00 Knowledge Graph.md`.

## Recall-Workflow (Wissen abrufen)

1. Passenden Themen-MOC lesen (oder `MOC - Home.md` als Index).
2. Volltextsuche über den Vault: Grep mit `glob: "*.md"` im Vault-Pfad.
3. Wiki-Links `[[Note-Name]]` folgen — Dateiname = Link-Ziel (Top-Level oder per Glob suchen, Obsidian löst ordnerübergreifend auf).
4. Achtung: ` ```dataview `-Blöcke sind Live-Queries, kein statischer Inhalt — die Ergebnisse selbst per Grep/Glob reproduzieren, nicht aus dem Block ablesen (Rezepte unten).

## Dataview-Emulation (Read-only-Rezepte)

Die drei Query-Patterns des Vaults und ihre Shell-Äquivalente (`V="/home/bratan/Dokumente/Obsidian Vault"`):

1. **Backlink-Cluster** (`LIST FROM "" WHERE contains(file.outlinks/inlinks, this.file.link)` — steht in fast jedem MOC und in den Projekt-Notes unter `## Live-Status`):
   - Inlinks: `grep -rl '\[\[Notizname' "$V" --include='*.md'` (Notizname ohne `.md`, auch Alias-Formen `[[Name|…]]` matchen dank Präfix-Match)
   - Outlinks: `grep -o '\[\[[^]|#]*' "<Note>" | sort -u`
2. **Ordner-Liste** (`LIST from "03 Projekte" WHERE contains(file.tags,"projekt")`): Glob `03 Projekte/**/*.md`, dann Frontmatter-Filter `grep -l 'projekt' <Dateien>` (Tags stehen im Frontmatter-`tags:`-Block).
3. **TABLE mtime / GROUP BY folder** (`SORT file.mtime DESC LIMIT 5`): `find "$V" -name '*.md' -newermt '7 days ago' -not -path '*/.trash/*'` bzw. `stat -c '%Y %n' … | sort -rn | head -5`.

### Vault-Health-Messrezept

Methodik nach `[[Vault-Health-Metrics]]` (Zielwerte dort nachschlagen, nicht hier duplizieren):

- **Notes gesamt**: `find "$V" -name '*.md' -not -path '*/.trash/*' -not -path '*/.obsidian/*' | wc -l`
- **Link-Density (avg Out-Links/Note)**: `grep -o '\[\[' <alle .md> | wc -l` geteilt durch Notes-Anzahl
- **Verwaiste Notes** (weder In- noch Outlinks): Notes ohne `[[`-Treffer im Inhalt UND deren Basename nirgendwo als `[[Name` vorkommt
- **Frontmatter-Quote**: Anteil Notes, deren Zeile 1 `---` ist

## MOC-Updates

Nur auf explizite Anweisung — Workflow siehe [references/moc-update.md](references/moc-update.md).

## Capture-Workflow (Inbox-first — verbindliche Schreibregel)

- **Neue Notizen ausschließlich nach `02 Inbox/`** (Dateiname: `YYYY-MM-DD - Titel.md`), Schnell-Captures nach `99 Capture/`. Vorlage: `_templates/Inbox-Note.md` — Templater-Platzhalter (`<% ... %>`) durch echte Werte ersetzen.
- Daily Notes nach `06 Daily Notes/` als `YYYY-MM-DD.md` nach `_templates/Daily Note.md` (Platzhalter `{{date}}` etc. ausfüllen; `modell:` auf das tatsächliche Modell setzen).
- Frontmatter mit `tags:` und `datum:` setzen; **mindestens 2 Wiki-Links** zu existierenden Notizen (Vault-Konvention: Link-Density ≥ 6,5 avg, keine verwaisten Notizen).
- **Bestehende Notizen, MOCs und `.obsidian/` nur auf explizite Anweisung von Basti editieren.** Keine Umstrukturierung, keine Umbenennungen, Audio-/`.canvas`-Dateien nicht anfassen.

## Excalidraw

Plugin `obsidian-excalidraw-plugin` ist installiert. Zeichnungen sind `.excalidraw.md`-Dateien; neue Zeichnungen ebenfalls Inbox-first (`02 Inbox/`). Dateiformat: siehe [references/excalidraw.md](references/excalidraw.md).
