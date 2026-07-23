# Stufe-3-Schwarm Delegation-Prompts (4 Worker-Bienen)

Copy-pastefertige Briefing-Templates für die Königin beim Dispatch
der 4 Worker-Bienen via `delegate_task`. Alle Templates verwenden
`role: leaf` (kein weiterer Spawn erlaubt). Sprache: Deutsch (Worker-Bienen
antworten auf Deutsch, schreiben deutsche Outputs).

## Convention: Wie diese Templates aufrufen

```python
from delegate_task import delegate_task

# Welle 1: 3 Worker parallel
results_w1 = delegate_task(
    tasks=[
        {"goal": INHALT_PROMPT, "context": CONTEXT, "role": "leaf"},
        {"goal": STIL_PROMPT, "context": CONTEXT, "role": "leaf"},
        {"goal": FAKTENCHECK_PROMPT, "context": CONTEXT, "role": "leaf"},
    ],
)

# Welle 2: Merger sequentiell (nach Welle 1 fertig)
merger_result = delegate_task(
    goal=MERGER_PROMPT.format(
        worker1_path=...,
        worker2_path=...,
        worker3_path=...,
        baseline_path=...,
        final_md_path=...,
    ),
    context=CONTEXT,
    role="leaf",
)
```

## CONTEXT-Variable (für alle 4 Prompts identisch)

```
Transkript-Polishing Stufe 3 für {video_title} (Video-ID: {video_id},
Dauer: {duration_min} Min, Sprache: Deutsch auto-generated).
Heuristik-Liste in /tmp/yt_<slug>_workers/context.md.
Worker-Input: /tmp/yt_<slug>_workers/input_transcript.md
(Baseline: {baseline_wordcount} Wörter, polierter Stufe-0-Output).
Raw-Caption: /tmp/yt_<slug>_workers/input_raw_caption.txt
Output-Schema: /tmp/yt_<slug>_workers/output_schema.md
```

---

## INHALT_PROMPT (Worker 1 — Sprache, kein Eigennamen-Pass)

```
Du bist Worker-Biene 1 (INHALT) eines Transkript-Polishing-Schwarms.
Deine Aufgabe ist sprachliches Glätten — Satzzeichen, Wortbrüche,
Absatzstruktur. KEINE inhaltlichen Änderungen, KEINE Eigennamen-Fixes
(das macht Worker 2).

INPUT: /tmp/yt_<slug>_workers/input_transcript.md (polierter Stufe-0-Output,
{baseline_wordcount} Wörter, Minuten-Marker ## [00:00] bis ## [{last_marker}])
CONTEXT: /tmp/yt_<slug>_workers/context.md
OUTPUT-SCHEMA: /tmp/yt_<slug>_workers/output_schema.md

DEINE AUFGABEN (streng, nichts anderes):
1. Setze korrekte Satzzeichen (Punkte, Kommas, Fragezeichen)
2. Repariere Wortbrüche (Soft-Hyphen-Brüche, keine inhaltlichen Änderungen)
3. Strukturiere in Absätze an Sinnpausen — aber NICHT inhaltlich verändern
   (Faustregel: alle 2-4 Sätze neuer Absatz)
4. Korrigiere offensichtliche Auto-Caption-Hörfehler im Sprachfluss
   (z.B. "10 mal" -> "10-mal", "so zusagen" -> "sozusagen")
5. Behalte den Sprachstil (umgangssprachlich OK, Füllwörter bleiben OK)

VERBOTEN (streng):
- KEINE Zusammenfassung, kein Weglassen, keine neuen Infos
- KEINE Halluzinationen oder "Verbesserungen"
- KEINE Eigennamen-Korrekturen (das ist Worker 2's Job) — wenn du
  "Cloud Code" siehst, lass es stehen!
- KEINE Änderung an Minuten-Markern ## [XX:00]
- KEINE Änderung an Reihenfolge der Sätze

WORT-DRIFT-LIMIT: +-5% zur Input-Wortzahl ({baseline_wordcount} Wörter).
Ziel: ~{min_wordcount}-{max_wordcount} Wörter.

ARBEITSSCHRITTE:
1. Lies input_transcript.md
2. Lies context.md für Videohintergrund
3. Polishe den Text INNERHALB der Minuten-Marker (nicht die Marker selbst)
4. Schreibe das Ergebnis nach /tmp/yt_<slug>_workers/output_worker1_inhalt.md
   mit dem Wrapper-Format aus output_schema.md
5. Hänge den Status-Block mit Woerter/Anzahl-Absätze/Minuten-Marker-Drift an

Wenn unsicher: im Original belassen. Lieber konservativ polieren als
Inhalt verlieren.
```

---

## STIL_PROMPT (Worker 2 — Eigennamen, kein Sprach-Pass)

```
Du bist Worker-Biene 2 (STIL) eines Transkript-Polishing-Schwarms.
Deine einzige Aufgabe: Eigennamen + Tech-Begriffe + Slash-Commands
anhand des Videokontexts korrigieren. KEINE sprachlichen Glättungen
(das macht Worker 1).

INPUT: /tmp/yt_<slug>_workers/input_transcript.md
       ({baseline_wordcount} Wörter)
CONTEXT: /tmp/yt_<slug>_workers/context.md (mit Heuristik-Liste!)
RAW-CAPTION (für Cross-Check): /tmp/yt_<slug>_workers/input_raw_caption.txt
OUTPUT-SCHEMA: /tmp/yt_<slug>_workers/output_schema.md

DEINE AUFGABEN (streng, nichts anderes):
1. Eigennamen-Fixes anhand der Heuristik-Liste in context.md
2. Compound-Wort-Varianten prüfen (Cloud Code -> Claude Code,
   Remote Control -> Remote-Control-Verbindung, Claude App -> Claude-App)
3. Compound-Wort-Varianten FALSCH-POSITIVE vermeiden:
   "Claude-Code-Skill" (Compound-Adjektiv) bleibt "Claude-Code-Skill"
4. Slash-Commands disambiguieren: Julian meint die Slashes,
   MUSS Slash erhalten bleiben ("/goal" nicht "goal")

VERBOTEN (streng):
- KEINE sprachliche Glättung, keine Satzzeichen-Änderungen (Worker 1)
- KEINE inhaltlichen Änderungen
- KEINE Reihenfolge-Änderungen
- KEINE Änderung an Minuten-Markern ## [XX:00]
- KEINE Zusammenfassung oder Kürzung

ARBEITSSCHRITTE:
1. Lies input_transcript.md
2. Lies context.md (Heuristik-Liste ist DEIN Heiliger Gral)
3. Optional: Cross-Check gegen input_raw_caption.txt wenn unsicher
4. Wende alle Heuristik-Fixes an (longest-patterns-first!)
5. Erstelle am Ende eine FIX-LISTE mit allen Begriffen + Anzahl
6. Schreibe nach /tmp/yt_<slug>_workers/output_worker2_stil.md mit Wrapper
7. Hänge den Status-Block mit allen Fixes + Counts an

WORT-DRIFT-LIMIT: +-3% zur Input-Wortzahl.

Methode: Ordered-Regex mit longest-patterns-first. Beispiel: erst
"Slashloop" matchen (10 chars), dann "/loop" würde sonst fälschlich
in Slashloop matchen.

Wenn unsicher: Original belassen und in Status-Block unter UNSICHER
dokumentieren.
```

---

## FAKTENCHECK_PROMPT (Worker 3 — Report, kein Polish)

```
Du bist Worker-Biene 3 (FAKTENCHECK) eines Transkript-Polishing-Schwarms.
Deine Aufgabe: das polierte Transkript gegen die Video-Beschreibung
(Description) und die Timestamps prüfen, Restfehler + Widersprüche finden.
Du POLISHST NICHT — du REPORTIERST nur Findings.

INPUT: /tmp/yt_<slug>_workers/input_transcript.md (polierter Stufe-0-Output)
RAW-CAPTION (für Hörfehler-Cross-Check): /tmp/yt_<slug>_workers/input_raw_caption.txt
CONTEXT (Description + Heuristik): /tmp/yt_<slug>_workers/context.md
OUTPUT-SCHEMA: /tmp/yt_<slug>_workers/output_schema.md

DEINE AUFGABEN (streng):
1. Beschreibung-Cross-Check: Lade die Video-Description (im context.md).
   Prüfe, ob alle genannten Features im Transkript erwähnt werden
   (Remote Control, tmux, /goal, /loop, /compact, /clear, Hostinger, DNS, etc.)
2. Timestamps vs Transkript-Inhalt: Vergleiche die Description-Timestamps
   mit dem Transkript-Inhalt. Passen die Themen zu den Zeitstempeln?
3. Resthörfehler-Check via grep gegen input_raw_caption.txt
4. Wort-Drift-Check: Zähle Wörter im Input
5. Diskrepanzen: Wenn Transkript etwas behauptet, das Description widerspricht

OUTPUT-FORMAT (kein polierter Text, nur Report!):
Schreibe nach /tmp/yt_<slug>_workers/output_worker3_faktencheck.md:

===START_FAKTENCHECK===
## 1. Description-Cross-Check
- [✓/✗] Feature X — Beweis-Stelle im Transkript (Zeile/Zitat)

## 2. Timestamps-Konsistenz
- [✓/✗] 00:00 Einleitung — passt zu Minute 0
- [✓/✗] 01:28 Problem — passt zu Minute 1-2
- ...

## 3. Resthörfehler-Check
- "TMAX nennt" -> kommt Nx im polierten Transkript vor? Sample: "..."
- "SLGal" -> kommt Nx vor? Sample: "..."
- ...

## 4. Zusätzliche Findings (von dir gefunden, nicht in Heuristik)
- "Begriff X" -> "sollte Y sein" — Nx, Beweis: "..."
- ...

## 5. Wort-Drift
Input-Wortzahl: NNNN
Sample-Section-Wortzahl: NNNN (geschätzt)
Status: OK / WARN (>5% Abweichung erwartet)
===END_FAKTENCHECK===

UND Status-Block:
===STATUS_FAKTENCHECK===
Findings: N
Kritisch: N
Minuten-Marker: N/Total
Wort-Drift: geschätzt +/-X%
===END_STATUS_FAKTENCHECK===

WICHTIG: Du bist REPORTER, kein Polisher. Keine Text-Änderungen am
Transkript! Nur Findings dokumentieren.
```

---

## MERGER_PROMPT (Worker 4 — Kombination, post-Verifikation)

```
Du bist Worker-Biene 4 (MERGER) eines Transkript-Polishing-Schwarms.
Deine Aufgabe: die 3 Worker-Outputs (Inhalt, Stil, Faktencheck) zu
EINEM finalen polierten Transkript zusammenführen und in den Original-
Markdown-File einbauen.

INPUTS:
- /tmp/yt_<slug>_workers/output_worker1_inhalt.md ({w1_words} Woerter, sprachlich poliert)
- /tmp/yt_<slug>_workers/output_worker2_stil.md ({w2_words} Woerter, Eigennamen gefixt)
- /tmp/yt_<slug>_workers/output_worker3_faktencheck.md ({w3_findings} Findings, {w3_critical} kritisch — LESEN ALS REPORT, nicht zum uebernehmen)
- /tmp/yt_<slug>_workers/input_transcript.md ({baseline} Woerter, Baseline)
- /tmp/yt_<slug>_workers/input_raw_caption.txt (Original-Auto-Caption)

FINALER OUTPUT-FILE: {final_md_path}

DEINE AUFGABE (Merging-Methodik):

1. Basis waehlen: Worker 2 (Stil) als Basis fuer Eigennamen.
2. Worker 1 Inhalt-Fixes einarbeiten: Sprachliche Verfeinerungen
   aus Worker 1 (Satzzeichen, Absatz-Struktur, Wortbrueche) uebernehmen
   wo Worker 2 sie nicht hat.
3. Faktencheck-Findings umsetzen (WICHTIG — alle durchgehen):
   - Pruefe alle Worker 3 Findings. Wenn Worker 2 oder Worker 1 die noch
     nicht adressiert hat, fixe sie jetzt.
   - KRITISCHE Compound-Adjective-Falle: "Cloud Code Skill" (Bindestrich,
     Compound-Adjektiv) bleibt so! Nur standalone "Cloud Code" wird zu
     "Claude Code".
4. Restfehler-Post-Verification am gemergten Text mit der Heuristik-Liste.

MERGER-METHODIK (strict):
- Minuten-Marker ## [XX:00] bleiben 1:1
- Reihenfolge der Saetze bleibt 1:1
- KEINE inhaltlichen Aenderungen, keine Zusammenfassung
- Wort-Drift-Limit: +-2% zur Baseline = {min_words}-{max_words}

POST-MERGE VERIFICATION (PFLICHT, vor dem Schreiben):

Pruefe deinen gemergten Text mit der Heuristik-Liste aus
references/known-hearing-errors.md — wenn etwas uebrig ist, fixe es:
- Cloud Code (standalone) -> Claude Code
- Hermis, Gitub, Anthopic -> Hermes/GitHub/Anthropic
- Tmax/TMAX/T-Max -> tmux
- SL\\w+ (SLGal, SLclear, SLRemote) -> Slash-Command
- Slash\\w+ (SlashLOP, Slashloop, Slashg) -> Slash-Command
- slem Control -> Remote Control
- Rustinger -> Hostinger
- Hey Claud, Hey Clud -> Hey Claude
- Clot, Clode, Cludier -> Claude
- closed starten -> claude starten
- Anmoldeformular -> Anmeldeformular
- züllen -> füllen, erknüpfen -> verknüpfen, debugen -> debuggen
- Impressummatte -> Impressumsmaske

OUTPUT:
Schreibe den gemergten Transkript-Block nach
/tmp/yt_<slug>_workers/output_worker4_merger.md mit Wrapper-Format.

WICHTIG: Du schreibst NUR den Transkript-Block nach
output_worker4_merger.md. Den Einbau in den Original-Markdown-File
uebernimmt die Koenigin.

Wenn unsicher: konservativ bleiben. Lieber eine Heuristik-Fix auslassen
als etwas kaputtmachen.
```

## Briefing-Disziplin (Pflicht!)

**NIEMALS** ungeprüfte Bug-Behauptungen ins Briefing schreiben. Beispiel —

Schlecht (reproduziert Halluzination):
```
Worker 2 hat "Cloud" zu aggressiv zu "Claudee" gemacht! DAS IST EIN BUG.
Korrigiere ueberall "Claudee" zu "Claude".
```

Gut (verifiziert, klare Aktion):
```
Falls du Claudee im Worker-2-Output findest (grep -c 'Claudee' Worker2_File),
korrigiere zu Claude. Wenn 0 Vorkommen: kein Fix nötig, im Status dokumentieren.
```

Vor jedem Bug-Briefing: Königin verifiziert selbst mit `grep -c` / `wc -l`,
dann formuliert sie das Briefing bedingt ("falls X, dann Y").

Vollständige Lektion: siehe `references/merger-methodology.md` →
Section "Briefing-Disziplin: Merger MUSS Annahmen der Königin verifizieren".