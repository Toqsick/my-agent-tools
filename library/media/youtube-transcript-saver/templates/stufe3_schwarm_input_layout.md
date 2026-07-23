# Stufe-3-Schwarm Input-Directory-Layout

Standardisierte Datei-Struktur für 4-Worker-Bienen-Orchestrierung
(Session 2026-07-09 etabliert, pvhphecd70Y Run).

## Verzeichnis

```
/tmp/yt_<slug>_workers/
├── input_transcript.md        # Polierter Stufe-0-Input (Baseline)
├── input_raw_caption.txt      # Original-Auto-Caption für Hörfehler-Cross-Check
├── context.md                 # Video-Kontext (Description, Heuristik, wichtige Eigenamen)
├── output_schema.md           # Output-Wrapper-Konvention (für alle Worker identisch)
├── output_worker1_inhalt.md   # Phase 1 / Welle 1: Worker-Biene 1 (Sprache)
├── output_worker2_stil.md     # Phase 1 / Welle 1: Worker-Biene 2 (Eigennamen)
├── output_worker3_faktencheck.md  # Phase 1 / Welle 1: Worker-Biene 3 (Report, kein Polish)
├── output_worker4_merger.md   # Phase 2 / Welle 2: Worker-Biene 4 (Kombiniert)
```

## File-Konventionen

### `input_transcript.md`

- **Inhalt**: Minuten-Marker-Transkript (`## [00:00]`, `## [01:00]`, ...) plus polierter Text INNERHALB der Marker
- **Format**: Markdown mit fester Marker-Syntax (siehe SKILL.md Schritt 6a)
- **Quelle**: Output von Stufe 0 (oder Input-Roh-Transkript wenn direkt Stufe 3 gewünscht)
- **Größe**: typisch 25-55 KB (bei 22-43 Min Videos)
- **NICHT überschreiben** während der Schwarm-Phase — bleibt als unveränderliche Baseline für Drift-Berechnung

### `input_raw_caption.txt`

- **Inhalt**: Original Auto-Caption als ein einziger Textblob (snippets-zusammengeklebt, Whitespace normalisiert aber NICHT geglättet)
- **Format**: Plain Text, keine Marker, keine Strukturierung
- **Zweck**: Hörfehler-Cross-Check — wenn Worker 3 unsicher ist ob ein Begriff wirklich im Original vorkommt, kann er hier nachschlagen
- **NICHT überschreiben** während der Schwarm-Phase

### `context.md`

Strukturiertes Markdown mit den folgenden Sektionen:

```markdown
VIDEO-KONTEXT (zur Eigennamen-Disambiguierung):

Titel: ...
Channel: ...
Upload: ...
Dauer: ...
Sprache: ...

VIDEO-INHALT (aus Description):
- Feature 1
- Feature 2
- Feature 3

WICHTIGE EIGENNAMEN in diesem Video:
- Eigenname A — ACHTUNG: Auto-Caption sagt "Verhunzer"!
- Eigenname B
- Eigenname C

BEKANNTE HOERFEHLER-PATTERNS FUER DIESES VIDEO:
- "Pattern1" -> Korrekt (Nx im Roh-Blob)
- "Pattern2" -> Korrekt (Mx im Roh-Blob)
- "Pattern3" -> Korrekt

REFERENZ-FILES (NICHT UEBERSCHREIBEN):
- /tmp/yt_<slug>_workers/input_transcript.md
- /tmp/yt_<slug>_workers/input_raw_caption.txt

HEADER DES TRANSKRIPTS — NICHT ANFASSEN:
- Die Minuten-Marker bleiben EXAKT erhalten
- Auch die Transkription-Warnung und der Hidden-Comment bleiben
- Du bearbeitest NUR den Text INNERHALB der Minuten-Marker
```

**Naming-Konvention** (für Multi-Channel-Runs wichtig):
- Verzeichnis-Suffix `<slug>` macht es einfach, parallel verschiedene Video-Pipelines zu haben ohne File-Kollisionen
- Beispiel: `/tmp/yt_remote_workers/` für pvhphecd70Y, `/tmp/yt_skills_workers/` für Vx6QlEhyybQ

### `output_schema.md`

Identisch für alle Worker. Definiert die Output-Wrapper-Convention:

```markdown
OUTPUT-FORMAT (für alle Worker):

Schreibe DEIN Ergebnis in /tmp/yt_<slug>_workers/output_<WORKER>.md
mit dem folgenden Wrapper:

===START_<WORKER>===
<Dein polierter/korrigierter Transkript-Text>
===END_<WORKER>===

UND hänge am Datei-Ende einen Status-Block an:

===STATUS_<WORKER>===
Woerter: NNNN
Gefixt: Begriff_A (Nx), Begriff_B (Mx)
Minuten-Marker: N/Total
Wort-Drift: +/-X%
===END_STATUS_<WORKER>===
```

### `output_workerN_<role>.md`

Pro Worker eine eigene Datei. Wrapper-Format siehe oben.

**Wichtig**: Worker schreiben **nicht** auf stdout — sie schreiben in die Datei. Sonst hat der Merger keinen Referenzpunkt für die Fix-Liste und muss die aus dem Text-Diff rekonstruieren.

## Naming-Convention

| Worker | Rolle | Output-File | Wrapper |
|--------|-------|-------------|---------|
| 1 | Inhalt (Sprache) | `output_worker1_inhalt.md` | `===START_WORKER1_INHALT===` |
| 2 | Stil (Eigennamen) | `output_worker2_stil.md` | `===START_WORKER2_STIL===` |
| 3 | Faktencheck (Report) | `output_worker3_faktencheck.md` | `===START_FAKTENCHECK===` |
| 4 | Merger (Kombiniert) | `output_worker4_merger.md` | `===START_MERGER===` |

## Cleanup

Nach Merger-Erfolg und Einbau in den Final-Markdown-File:

```bash
rm -rf /tmp/yt_<slug>_workers/
```

Hinterlasse KEINE Files in /tmp/ von der Pipeline — sie können mit nachfolgenden Runs kollidieren oder mit Session-TTL-Regeln (systemd-tmpfiles) automatisch gelöscht werden, was den Merger-Briefing bricht (siehe `merger-methodology.md` → `/tmp/ TTL mid-pipeline` Pitfall).