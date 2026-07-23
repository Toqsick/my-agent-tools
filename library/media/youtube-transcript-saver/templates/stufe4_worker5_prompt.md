# Worker 5 (LLM-Glättung) — Briefing-Template

Verwende diesen Text als `goal` für `delegate_task(role='leaf')` in Sub-Phase 4.2.

## Vollständiger Briefing-Text

```
Du bist Worker-Biene 5 (LLM-GLAETTUNG) eines Transkript-Polishing-Schwarms. 
Deine Aufgabe: sprachliche Verfeinerung eines bereits Stufe-3-polierten 
Transkripts. Du bist NICHT fuer Eigenname-Korrekturen zustaendig (Stufe 3 
hat das erledigt). Du bist NICHT fuer Inhalt zustaendig. Du POLISHST NUR 
die Sprache.

INPUTS:
- /tmp/yt_llm_worker/input_stufe3_transcript.md (Stufe-3-poliert — dein Startpunkt)
- /tmp/yt_llm_worker/input_raw_caption.txt (Original-Auto-Caption, fuer Cross-Check bei Unklarheiten)
- /tmp/yt_llm_worker/context.md (Videohintergrund + Eigenname-Liste + Ambiguitäten)
- /tmp/yt_llm_worker/output_schema.md (Output-Format)

DEINE AUFGABEN (streng, nichts anderes):

1. Satzzeichen-Korrekturen (nur wo eindeutig falsch):
   - Punkte am Satzende (Auto-Caption vergisst oft den letzten Punkt)
   - Kommas vor Nebensaetzen (typisch Auto-Caption-Fehler)
   - Fragezeichen bei direkten Fragen
   - Beispiel: "Hey Claude, ich finde die Website schon ganz gut" bleibt 
     wie es ist (Hauptsatz mit Komma, korrekt)
   - Beispiel-Fix: "Was ich jetzt mega cool finde ist" -> 
     "Was ich jetzt mega cool finde, ist"

2. Wort-Reparaturen (nur eindeutige Auto-Caption-Brueche):
   - Eigennamen NICHT anfassen (Stufe 3 erledigt — siehe Context-Liste)
   - Falsche Konjugationen: "gehen" statt "ging", "macht" statt "mach"
   - Komposita statt Komma: "Danke, Seite" -> "Danke-Seite"
   - Rechtschreibung "dass" (Konjunktion) statt "das" (Pronomen)
   - Relativpronomen-Deklination: "mit dem wir" -> "mit denen wir" 
     bei Bezug auf Plural-Substantiv
   - Fehlende Substantive ergaenzen wenn der Kontext klar ist

3. Absatz-Struktur verbessern (sparsam):
   - Vorherige Worker haben schon Absaetze gebaut — du darfst nur 
     FEINJUSTIEREN wo ein Absatz zu lang oder zu kurz ist
   - Faustregel: 2-4 Saetze pro Absatz (nicht drastisch aendern)

VERBOTEN (STRENG!):

- KEINE Zusammenfassung, kein Weglassen, keine neuen Infos
- KEINE Halluzinationen oder "Verbesserungen"
- KEINE Eigenname-Fixes (Stufe 3 erledigt — siehe Context-Liste)
- KEINE Aenderung an Minuten-Markern ## [XX:00]
- KEINE Aenderung an der Reihenfolge der Saetze
- KEINE substantielle Aenderung an Fuellwoertern (Creator-Stil erhalten — 
  "halt", "quasi", "natuerlich", "eigentlich", "irgendwie", "mega cool", 
  "ne" sind Sprachstil, NICHT eliminieren!)
- KEINE Aenderung an Rest-Ambiguitäten (im Header dokumentiert)

WORT-DRIFT-LIMIT: +-2% zur Baseline (siehe context.md). Ziel ist 
BEIBEHALTUNG der Wortzahl, nur Politur.

KONSERVATIVITAETS-CHECKLISTE vor dem Schreiben:
- [ ] Keine Saetze umformuliert die Meinung/Argumentation aendern
- [ ] Keine Fakten hinzugefuegt die der Creator nicht gesagt hat
- [ ] Keine Erklaerungen eingefuegt die nicht gegeben wurden
- [ ] Eigennamen-Liste komplett unangetastet
- [ ] Rest-Ambiguitäten unangetastet
- [ ] Drift unter +-2%
- [ ] 0 Füllwort-Reduktionen (außer klar falsche wie Doppelungen)

ARBEITSSCHRITTE:
1. Lies input_stufe3_transcript.md
2. Lies context.md (besonders die Eigennamen-Liste — die NICHT anfassen)
3. Polishe INNERHALB der Minuten-Marker
4. Schreibe das Ergebnis nach /tmp/yt_llm_worker/output_worker5_llm.md 
   mit dem Wrapper-Format aus output_schema.md
5. Hänge den Status-Block mit Woerter/Absaetze/Minuten-Marker/Drift an
6. Liste ALLE Satzzeichen/Wort-Reparaturen mit Counts im Status

Wenn unsicher: im Original belassen. Lieber konservativ polieren als 
Inhalt verändern.
```

## Wo platziert

Das Briefing wird als `goal`-Parameter an `delegate_task` übergeben. Der `context`-Parameter enthält Video-Metadaten und die zu erhaltenden Eigennamen-Liste.

```python
from delegate_task import delegate_task

result = delegate_task(
    goal="<OBIGER TEXT>",
    context=f"Video-ID: {video_id}, Sprache: Deutsch, Baseline: {baseline_words} Woerter",
    role="leaf"
)
```

## Häufige Worker-5-Antworten

Basierend auf Session 2026-07-09 (pvhphecd70Y):

| Antwort-Typ | Erwartete Counts |
|-------------|------------------|
| Satzzeichen-Korrekturen | 30-50 (v.a. Kommas vor Nebensätzen) |
| Wort-Reparaturen | 0-10 (selten, nur eindeutige Fälle) |
| Füllwort-Reduktionen | **0** (wenn Constraints respektiert) |
| Wall-Clock | 30-60 Sekunden |

## Validation (Königin prüft)

Nach Worker-5-Lieferung MUSS die Königin verifizieren:

```python
# Output-Datei lesen
output = Path("/tmp/yt_llm_worker/output_worker5_llm.md").read_text()
parts = output.split("===START_WORKER5_LLM===")
worker5_transcript = parts[1].split("===END_WORKER5_LLM===")[0].strip()

# Wort-Drift
baseline = 4904  # aus context.md
worker5_words = len(worker5_transcript.split())
drift = (worker5_words - baseline) / baseline * 100
print(f"Worker 5 Drift: {drift:+.2f}% (sollte +-2%)")

# Eigennamen-Counts (sollten UNVERÄNDERT sein)
for name in ["Claude Code", "tmux", "/loop", "/goal", "/compact", "/clear"]:
    count = worker5_transcript.count(name)
    print(f"  {count:3d}x '{name}'")

# Füllwort-Counts (sollten erhalten sein, nicht reduziert!)
fill_words = ["natürlich", "eigentlich", "halt", "quasi", "irgendwie"]
for word in fill_words:
    count = len(re.findall(rf"\b{word}\b", worker5_transcript, re.IGNORECASE))
    print(f"  {count}x '{word}'")
```

## Bei Drift > ±2% oder Halluzinations-Verdacht

Worker-Output verwerfen und **NICHT** in Final-File einbauen. Stattdessen:
1. Status-Block lesen für Hinweise was passiert ist
2. Bekannte Fixes manuell mit `re.subn` auf den Stufe-3-File anwenden
3. LLM-Pass als gescheitert markieren

NICHT den LLM nochmal dispatchen — das wiederholt den gleichen Fehler meist.