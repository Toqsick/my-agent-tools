# Deployment-Dokumentation erstellen (Multi-Source Research + Template)

## Wann

Wenn Basti sagt "erstell eine Deployment-Doku für <tool>" oder ich ein In-Game-Tool dokumentieren muss.

## Workflow — 3 Quellen kombinieren, keine raten

| Quelle | Pfad | Was gibt's? |
|--------|------|-------------|
| Build-Artefakte | `~/build/`, `~/greyhack-tools/build/` | Source-Größe, Module, Commands |
| Existierende Doku | `~/docs/system/greyhack-yuno-*.md` | Feature-Übersichten, Build-Status, Naming-Conventions |
| DB-Archäologie | `~/docs/system/greyhack-deep-*.md` (content, systems, intel, research) | In-Game-Modul-Listen, Player-PC-Pfade, File-Größen, Credentials |

## Dokument-Struktur-Vorlage

| Sektion | Inhalt |
|---------|--------|
| `Warum KEIN <common-but-wrong-assumption>` | Erstes Hindernis entkräften (z.B. pc.wget existiert NICHT im Game-Terminal — Erklärung der Verwechslung) |
| `Deployment Workflow (N Schritte)` | Schritt-für-Schritt: Host → Transfer → CodeEditor (Ctrl+O/Ctrl+B/Ctrl+S/F5) → Run → Auto-Config |
| `Module & Command-Übersicht` | Tabelle aller Sektionen/Module mit Command-Listen |
| `Build-Schritte (Host)` | Exakte Build-Kommandos + Smoke-Test-Checklist |
| `Troubleshooting` | 10+ Fehlerszenarien: Build-Fehler (Memory-Limit, Index-Bounds) + Runtime (Not-in-shell, Config-korrupt, Lib-fehlt) + In-Game (Persistenz-Verlust, nmap tot) |
| `Quick-Reference-Card` | Ein-Panel-Übersicht der gesamten Pipeline |

## Agent-4/Subagent-Result-Check Pattern

Wenn der Auftrag auf ein Subagent-Ergebnis verweist ("wartet auf Agent 4 Ergebnis"):

1. **Vor Loslegen** die erwarteten Result-Pfade durchsuchen (check filesystem, search for agent-4 mention)
2. **Wenn nicht vorhanden**: das Gap in der Doku mit einem Pending-Marker dokumentieren — nicht blocken
3. **Erwartetes Format** beschreiben (was würde Agent 4 liefern? In-Game-Validierung? Performance-Metriken?)
4. **Zustellung trotzdem machen** — das fehlende Stück ist kein Grund, den Rest zurückzuhalten

## Beispiel

Die erstellte Datei `~/docs/system/greyhack-yuno-v6-deploy-2026-07-04.md` (438 Zeilen, 16.9 KB) ist das konkrete Artefakt dieser Vorlage — inkl. Agent-4-Pending-Marker, Modultabelle, QuickRef-Card, und 12 Troubleshooting-Einträgen.