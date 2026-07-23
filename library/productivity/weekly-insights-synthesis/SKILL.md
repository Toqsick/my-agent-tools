---
name: weekly-insights-synthesis
description: "Use when user asks for weekly insights, time-window knowledge distillation, document or log synthesis, or consolidation of recurring reports. NOT for editing a single note or performing live research from scratch. Produces structured insight notes with highlights, patterns, open questions, sources, and a concise Telegram summary."
version: 1.1.0
author: Yuno
license: MIT
platforms:
- linux
- macos
metadata:
  hermes:
    tags:
    - productivity
    - insights
    - synthesis
    - documentation
    - cron
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['weekly-insights-synthesis', 'weekly', 'insights', 'time-window', 'knowledge']
keywords: ['user', 'asks', 'weekly', 'insights', 'time']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['report-synthesis', 'perplexity-followup-plan']
---


# Weekly Insights Synthesis

Generiert strukturierte Weekly-Insights-Notizen aus einer Sammlung von Doku-Files eines Zeitfensters. Geeignet für Cron-Jobs (z.B. `knowledge-distiller`) oder manuelle Aufräum-Sessions.

## Workflow (5 Phasen)

### Phase 1: Environment-Ermittlung

Bevor du Quellen suchst: checke die aktuelle Umgebung.

```bash
hostname
pwd
whoami
find ~ -maxdepth 4 -type d -name "docs" 2>/dev/null | head -5
```

**Pitfall:** Der Cron-Job kann in einem `/tmp/`-Clone laufen (z.B. `/tmp/maxclaw-clone`) statt im echten Home. Dann existieren erwartete Pfade nicht. Löse auf:
- Existiert `~/docs/system/`? → primäre Quelle
- Existiert die erwartete Domain (z.B. `~/greyhack-tools/`)? → prüfen
- Existieren spezifische Log-Pfade (`~/.local/share/hermes/logs/`, `~/.local/share/maxclaw/cron-output/`)? → falls nein: substituieren

### Phase 2: Input-Sammlung

Sammle relevante Dateien aus einem Zeitfenster. Standard: **letzte 7 Tage** (Sonntag 22:00 → Vorwoche Mo–So).

#### Files (Dokumente, Source, Logs)

```bash
# Finde Files ab dem 28. des Monats (Vorwoche)
find ~/docs/system ~/<domain-tools> -type f \( -name "*.md" -o -name "*.json" -o -name "*.src" \) -newermt "2026-06-27" 2>/dev/null | sort
```

#### DB-Snapshots (GreyHack / SQLite)

Bei Domains mit SQLite-DB-Snapshots (z.B. `~/.local/share/maxclaw/snapshots/GreyHackDB-*.db`):

1. **Letzten Snapshot ermitteln:** `ls -lt ~/.local/share/maxclaw/snapshots/*.db | head -3`
2. **Snapshot-Hash-Vergleich** (schnelle Identitäts-Prüfung per sha256sum):  
   `sha256sum ~/.local/share/maxclaw/snapshots/*.db | awk '{print $1}' | sort -u | wc -l`  
   → `1` = alle Snapshots identisch (keine DB-Änderung), `>1` = Deltas vorhanden
3. **Delta berechnen** via `scripts/distiller-counts.py`:  
   `python3 scripts/distiller-counts.py --db-pre <before.db> --db-post <after.db>`  
   → listet welche Tabellen gewachsen/schrumpf sind und um wie viele Zeilen
4. **Files-Delta** (für GreyHack: Änderungen in Files-Tabelle):  
   `python3 scripts/distiller-files-delta.py --db-pre <before.db> --db-post <after.db>`  
   → listet neue/gelöschte Dateien zwischen zwei Snapshots

Bei **fehlenden erwarteten Inputs** (MISSION-LOG, Cron-Output, Logs):
1. Nicht blocken — substituieren durch was da ist
2. Die Substitution im Output mit "Audit-Hinweis" dokumentieren
3. `date "+%Y-%m-%d %A KW=%V"` notieren für den Insight-Kopf

**Eingrenzung:** Nicht mehr als 15–20 Dateien lesen. Wenn mehr: priorisieren nach:
- Aktuellstem Datum zuerst (Jul-Dateien vor Jun-Dateien)
- Höchstem Cluster-Beitrag (deep-* vor single-shot)
- Relevanz zum Insight-Thema

**Pitfall:** `find -newermt` filtert mtime, nicht Inhalt. Eine alte Datei die heute modifiziert wurde ist drin — das ist okay, Inhalt-Priorisierung passiert beim Lesen.

**Pitfall (Cron):** `execute_code` ist in Cron-Kontexten NICHT verfügbar. Für Datenverarbeitung (Delta-berechnung, Tabellen-Vergleiche) Helper-Scripts via `write_file` nach `/tmp/` schreiben und via `terminal` ausführen — nicht auf `execute_code` setzen.

**Pitfall (DB-state.json):** Der `db-state.json` Watchdog speichert nur Current-vs-Last-Hashes. Für historische Deltas ("Was hat sich seit letztem Montag verändert?") kann er nicht verwendet werden. Immer die SQLite-Snapshot-Paare direkt vergleichen.

### Phase 3: Lesen & Extrahieren

Lese die priorisierten Dateien (je 80–150 Zeilen, Kopf + TL;DR + Key-Sektionen). Notiere pro Datei:

| Feld | Inhalt |
|------|--------|
| Quell-Pfad | Absoluter Pfad |
| Größe | Dateigröße |
| Datum | mtime / Dateiname-Datum |
| Highlights | 2–5 Bullet-Points, Schlüsselfakten |
| Neue Patterns | Techniken, Workarounds, Bugs (als NP-XX nummerieren bei GreyHack) |
| Offene Fragen | Was unklar ist, nächstes Mal zu tun |

**Pattern-Erkennung:** Achte auf:
- Wiederkehrende Fehler/Workarounds (→ NP-Nummer vergeben)
- Neue Tools/Features/Deployments (→ Highlight)
- Brüche/Probleme die Basti lösen muss (→ offene Frage)
- Cross-Datei-Zusammenhänge (gleiches Thema in 2 Docs → konsolidiert darstellen)

**Source-Attribution:** Jeder Fakt braucht einen belegbaren Pfad:
```
Format: `~/docs/system/<datei>.md:<zeile>`
```

Das gilt besonders für behauptete "Fixes", "Status", "Bugs". Wenn eine Aussage nur aus einer Doku stammt und nicht durch Live-Test verifiziert wurde, schreib "Quelle: ..." dazu.

### Phase 4: Synthese

Baue die Insights-Notiz nach folgendem Template:

```markdown
# <Domain> Weekly Insights — KW <NN> (YYYY-MM-DD → YYYY-MM-DD)

> **Distiller:** <Prozess-Name> (<model>, <profil>)
> **Zeitfenster:** <N Tage>, Eingrenzung <start> → <ende>
> **Input-Quellen:** <N Dateien aufgelistet>
> **Hinweis Archivierung:** Bei >12 Wochen → älteste nach `~/docs/system/archive/` verschieben.

---

## Highlights (<N>)

1. **<Title>** — <2-3 Sätze>.
   *Quelle:* `<pfad>:<zeile>`

2. ...

---

## Neue Patterns / Bugs

### Pattern NP-<NN>: <Title>
- **Repro:** ...
- **Fix:** ...
- **Status:** ✅ / ⚠️
- *Quelle:* `<pfad>:<zeile>`

---

## Offene Fragen / Nächste Woche

1. **<Frage>** — <Kontext 1 Satz>
2. ...

---

## Quellen-Index

| Datei | Größe | Cluster-Beitrag |
|-------|------:|------------------|
| `<pfad>` | <KB> | Kurzbeschreibung |

**Audit-Hinweis:** Falls erwartete Inputs fehlten: hier dokumentieren.

---

## Telegram-Kurzfassung

> 🐝 **<Domain> KW<NN> — Highlights:**
> 1. ...
> 2. ...
>
> ❓ **Offene Frage:** ...
```

**Struktur-Regeln:**
- **Highlights**: maximal 5, jeweils 1–3 Sätze + Quellenangabe
- **Patterns/Bugs**: beschreibend, mit Repro+konkretem Fix-Code, und vor allem QUELLE
- **Offene Fragen**: maximal 4, jede als echte Entscheidung formuliert (keine Rhetorik)
- **Quellen-Index**: vollständige Liste aller gelesenen Quellen mit Größe + Beitrag
- **Telegram-Kurzfassung**: 5 Bullets + 1 offene Frage, max 800 Zeichen

### Phase 5: Output speichern

**Datei:** `~/docs/system/<domain>-weekly-insights-YYYY-MM-DD.md`
**Format:** Markdown, ~80–120 Zeilen, 5–10 KB

**Archivierung:** Bei >12 Wochen Insights → älteste in `~/docs/system/archive/` verschieben. Am Ende der Notiz vermerken ob Archivierung nötig ist.

## Verwendungs-Kontexte

| Kontext | Wann | Domain | Source-Pfade |
|---------|------|--------|--------------|
| GreyHack Knowledge Distiller | So 22:00 | `greyhack-tools`, `docs/system` | `~/docs/system/greyhack-*.md`, `~/greyhack-tools/` |
| DevOps Weekly | Frei | `docs/system`, `.hermes` | System-Docs, Cron-Logs, Config-Änderungen |
| Hermes V7 SSE Weekly | Frei | `docs/system/hermes-v7-sse-*.md` | SSE-Release-Notes |
| Generisch | Beliebig | Beliebiges `~/docs/system/` | `find -newermt "<date>"` |

## Pitfalls

1. **Inputs nicht vorhanden** → nicht blocken, substituieren + Audit-Hinweis
2. **Zu viele Dateien (>20)** → priorisieren nach Datum + Relevanz, Reader-Sessions begrenzen
3. **Patterns ohne Beleg** → immer "Quelle: Pfad:Zeile" mitschreiben
4. **Telegram-Kurzfassung zu lang** → max 800 Zeichen, sonst Timeout bei Delivery
5. **Offene Fragen ohne Entscheidungsoptionen** → immer als Entscheidung formulieren (Option A/B/C), nicht als "Was tun?"
6. **Insight wiederholt letzte Woche** → dann war die Woche leer — das ist OK, aber erwähne es (z.B. "nichts substanziell neues")
7. **Doppelte Highlights aus mehreren Quellen** → konsolidieren, nicht duplizieren
8. **Multi-Agent vs Sequential** — Bei Inputs <15 Dateien + <10 DB-Snapshots ist sequenzielle Verarbeitung deterministischer und günstiger. Multi-Agent-Orchestration (`delegate_task`) nur bei >20 Quellen oder parallelen unabhängigen Domains verwenden (z.B. GreyHack + DevOps + Hermes-V7 gleichzeitig).

## Templates

- Dieses Dokument ist das Template — Weekly-Notizen folgen immer der Struktur aus Phase 4
- Keine separaten Template-Files nötig

## Siehe auch

- `daily-briefing` (productivity/) — Täglicher System-Status (operational), weekly-insights ist die strategische/domain-spezifische Ergänzung
- `session-handoff` (productivity/) — Modellwechsel-Dokument (anderer Zweck)
- `greyhack` (gaming/) — Primäre Domain für GreyHack-Insights; neue Patterns aus Distiller fließen als Reference-Files dort hinein
