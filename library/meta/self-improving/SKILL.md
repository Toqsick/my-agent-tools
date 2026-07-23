---
name: self-improving
description: >-
  Use when user asks for recording a non-trivial failure and its fix, learning from a user correction, capturing a discovered workaround or edge case, or preventing a repeated CI or tool mistake. NOT for logging trivial typos or saving stable user-profile preferences. Runs a deduplicated lesson loop that classifies, writes, verifies, promotes, and expires reusable operational learnings.
version: 1.5.0
author: Basti + Yuno (adaptiert aus OpenClaw self-improving)
license: MIT
agent: Yuno
lane: koenigin
trigger_keywords:
- fehlschlag
- fehler
- korrigiert
- workaround
- quirk
- lesson
- root cause
- build error
- fix
- das war falsch
- mach es anders
- kaputt
- patch replace_all
- quality gate
- trippelfehler
keywords:
- self-improving
- mnemosyne
- lesson
- pitfall
- dedupe
- promote
related_skills:
- subagent-driven-development
- skill-creator
- writing-plans
last_curated: 2026-07-17
curated_by: Yuno (Biene 3 von 2026-07-17)
routing_hint: Persistiert Lessons aus Fehlern in Mnemosyne. Cross-domain. Trigger
  nach jedem nicht-trivialen Fehler (mind. 5+ Tool-Calls oder Heisenbug-Fix). Pair
  mit mnemosyne_remember/validate für durable Storage.
---


# Self-Improving — Yuno lernt aus Fehlern

> *Aus "OpenClaw 10x stärker" Technik 3, gemappt auf Hermes-native Mechanismen.*
> *Statt Klebezettel in TOOLS.md/MEMORY.md zu kleben, nutzt dieser Skill*
> *Mnemosyne (semantic recall), skill_manage (dauerhafte Skills) und*
> *~/docs/system/ (Projekt-Doku).*

## Wann dieser Skill greift

**Immer** wenn eine der folgenden Situationen auftritt:

- Ein Shell-Befehl/Build schlägt fehl und der Fix ist **nicht trivial**.
- Ein Tool-Aufruf produziert ein falsches Ergebnis, das erst nach Umweg korrigiert wird.
- Basti korrigiert Yuno (*"nein, so nicht"* / *"das war falsch"* / *"mach es anders"*).
- Eine CI schlägt fehl und die Ursache wird identifiziert.
- Ein Workaround/Quirk/Edge-Case wird entdeckt, der wiederverwendbar ist.
- Ein `mnemosyne_recall` oder `session_search` enthüllt, dass derselbe Fehler **schon einmal** gemacht wurde → **sofort** dokumentieren!

## Trigger-Wörter (vollständig)

| Deutsch | English | Domain |
|---|---|---|
| fehlschlag, kaputt, geht nicht | failed, broken | generic |
| korrigiert, fix, workaround | corrected, fix, workaround | generic |
| root cause, warum | root cause | debugging |
| lesson, pitfall, falle | lesson, pitfall | meta |
| patch replace_all, write_file | patch tool | tools |
| quality gate, gate fehlt | gate, validation | process |
| dedupe, doppelt, schon mal | duplicate | hygiene |
| promote, hochziehen, in skill | promote | hygiene |
| obsolete, veraltet, replaced | obsolete | hygiene |

## Der Lern-Loop (5 Schritte)

### 1. Erkennen

Benenne in **einem Satz**, was schiefging und **warum** (Root Cause, nicht nur Symptom).

> *Schlecht:* "Build kaputt."
> *Gut:* "greybel build -u kann Inline-if nicht parsen — Parser-Bug in v3.7.x."

### 2. Einordnen

Wähle das Ziel-System basierend auf der Art der Lektion:

| Lektionstyp | Ziel-Mechanismus | Wann |
|---|---|---|
| **Tool-/CLI-Quirk** (wiederkehrend) | `skill_manage(action='patch')` → passenden Skill aktualisieren | Wenn ein bestehender Skill den Quirk nicht abdeckt |
| **Projekt-Build-Fehler** | `mnemosyne_remember` mit `metadata.tags=["build-error", "<projekt>"]` | GreyHack-Build-Errors, Compiler-Bugs |
| **Prozess-/Workflow-Lektion** | `mnemosyne_remember` mit `metadata.tags=["lesson", "<domain>"]` | Debugging-Patterns, Architektur-Entscheidungen |
| **Wiederkehrender Quirk (3×+)** | **Promote:** → Skill-Reference oder harte Regel | Siehe Hygiene-Regel *Promote* |
| **Projekt-Refactor-Lektion** | `~/docs/system/` Markdown-Doc | Basti's Doku-Konvention |

### 3. Schreiben (Mnemosyne-Eintrag)

Schreibe einen **präzisen** Mnemosyne-Eintrag. **Kein Roman** — ein strukturierter Eintrag, den das Zukunfts-Ich in 5 Sekunden versteht.

**Pflicht-Felder im Eintrag:**

```
### [YYYY-MM-DD] <Kurztitel>
- Symptom: <was sichtbar war>
- Root Cause: <die eigentliche Ursache>
- Fix: <der konkrete Befehl / die Änderung>
- Guard: <wie künftig vermieden>
- Status: verified | hypothese
```

**Als Mnemosyne-Aufruf:**

```python
mnemosyne_remember(
    content="""
    ### [2026-07-07] greybel build -u bricht Inline-if
    - Symptom: Build-Output korrupt bei Einzeiler-if
    - Root Cause: -u-Flag inkompatibel mit Inline-if/Einzeiler-if-Pattern
    - Fix: immer `greybel build <tool>.src -o build/<tool>.xml` ohne -u
    - Guard: CI-Build-Skript prüft auf -u-Flag
    - Status: verified
    """.strip(),
    importance=0.8,  # hoch, weil wiederverwendbar
    source="self-improving",
    veracity="verified",  # oder "inferred" bei hypothese
    metadata={
        "tags": ["lesson", "greyhack", "build-error"],
        "status": "verified",  # oder "hypothese"
        "category": "tool-quirk",
    },
    extract_entities=True,  # GreyHack, greybel etc. als Entities
)
```

### 4. Verifizieren

- **Fix bestätigt** (getestet, CI grün, Basti nickt): `Status: verified`, `veracity: "verified"`.
- **Fix nur vermutet** (Logik stimmt, aber nicht getestet): `Status: hypothese`, `veracity: "inferred"`.
- Hypothese-Einträge werden vom **täglichen Hypothesen-Review-Cronjob** (`self-improving-daily-review`, täglich 10:00) erfasst und bei Basti zur Verifikation vorgelegt.

### 5. Kein Auto-Push

- Einträge in Mnemosyne sind **lokal und sicher** — kein Commit, kein PR.
- Commits/PRs/Config-Änderungen **nur** nach Bastis expliziter Freigabe.
- `main` branch ist tabu ohne Info/Tests/Freigabe.

## Hygiene-Regeln (sonst wächst Memory ins Uferlose)

### Dedupe — Vor dem Schreiben suchen

**IMMER** vor dem Schreiben `mnemosyne_recall(query="<Kurztitel>")` ausführen.

- Existiert ein ähnlicher Eintrag → **aktualisieren** (`mnemosyne_update`), nicht duplizieren.
- Existiert exakt der gleiche → Importance erhöhen, Content merge.
- Für ID-Discovery (\"welche Mnemosyne-ID gehört zu dieser Lesson?\") siehe `references/mnemosyne-id-resolution.md` — `recall` allein reicht nicht, `export`+JSON für Metadata nötig.

### Promote — 3×-Regel

Taucht dieselbe Lektion **3×+** auf (gleicher Root Cause bei unterschiedlichen Gelegenheiten):

1. In einen **Skill** hochziehen: `skill_manage(action='patch', name='<passender-skill>')` → als `references/<topic>.md` oder direkt in SKILL.md.
2. Falls hart genug: als eigener Skill-Reference-File mit build/test-Check verankern.
3. Mnemosyne-Eintrag mit `metadata.promoted_to="<skill-name>"` markieren.

### Verfall — Obsolete Lektionen

Lektionen, die durch neue Tool-Versionen obsolet werden:

- Mnemosyne-Eintrag **nicht löschen** — mit `mnemosyne_invalidate(memory_id=..., replacement_id=None)` als expired markieren.
- Content mit `~~durchgestrichen~~ (obsolet seit <Version>)` markieren via `mnemosyne_update`.
- Falls eine neue Version der Lektion existiert: `replacement_id` auf den neuen Eintrag setzen.

### Flush-Kopplung

Diese Einträge sind genau das, was `mnemosyne_sleep` (Consolidation) vor dem Komprimieren retten soll — deshalb **IMMER** in Mnemosyne schreiben, nie nur im Kontext behalten.

## Quality Gates (Lessons als Pflicht-Schritte, nicht Empfehlungen)

> **Lesson-Hintergrund 2026-07-15:** Daily-Quality-Gate (EmDashes ≤ 1,
> Boldface = 0, InlineHdr = 0, NegParall = 0) muss VOR dem Patch
> laufen, nicht erst beim Recoil.

### Das Pattern

Quality Gates sind Pre-Commit-Checks die **vor** der finalen Schreib-
Aktion laufen. Wenn das Gate rot flaggt → kein Patch, stattdessen
Output fixen.

### Implementierungs-Rezepte

```bash
# Daily-Addendum / Wiki-Link-Section Gate
bash ~/docs/system/quality-gates/daily-addendum-gate.sh

# Skill-Curation Gate (prüft 5 Pflicht-Felder)
bash ~/docs/system/quality-gates/skill-curator-gate.sh <skill-path>

# Subagent-Output-Verifier Gate (Pitfall #36)
bash ~/docs/system/quality-gates/subagent-self-test-gate.sh <report-path>
```

### Faustregel

> **Wenn du einen Output schreibst, der durch eine fremde Pipeline
> läuft (Daily-Humanizer, Wiki-Processor, CI), LÄUFT das Gate ZUERST.**
> Kein Patchen-erst-dann-gaten. Ever.

## Pitfall-Katalog (die teuren Cases)

> Numerierte Pitfalls mit klarem Symptom → Root Cause → Fix → Guard.
> Ein Pitfall wird promoted wenn: importance ≥ 0.85 UND mindestens 1
> Re-Auftreten.

### Pitfall #5 — patch replace_all=true auf common-prefix-Strings (Trippel-Injection)

- **Symptom:** Nach `patch(mode='replace', old_string='**', new_string='', replace_all=true)`
  sind 3+ identische Kopien des Inhalts in der Datei.
- **Root Cause:** `replace_all=true` matcht **jedes** Vorkommen von `old_string`.
  Bei 3 leeren Bullet-Listen trifft der Match 3× → Content 3× injiziert.
- **Bestätigte Wiederholung:** 2026-07-14 um 01:48 mit `old_string='**'` → 14
  Mid-sentence-Header zu Plain-Header + potenzielle Trippel-Injection.
- **Fix:** `write_file` mit vollständigem korrektem Content überschreibt
  sicher; nie `replace_all=true` mit common-prefix-Strings.
- **Guard:**
  - `replace_all=true` NUR wenn `old_string` in der ganzen Datei GENAU 1× vorkommt.
  - Bei Mehrfach-Match-Verdacht: vorher `grep -c "<old_string-prefix>" <file>` zählen.
  - Bei Datei-Korruption: `write_file` ist sicherer als ein Korrektur-Patch.
- **Status:** verified (zwei unabhängige Vorfälle, IDs `9a88228f4e99bf07` + `fce51cbf4276cd43`)

### Pitfall #36 — Sub-Agent meldet "alle Tests grün" trotz File-Violations (TEILWEISE REVIDIERT 2026-07-17)

- **Symptom (Original, 2026-07-13):** Subagent-Bericht sagt "PASS — alle
  Tests grün", aber die Implementierung hat File-Violations (fehlende
  Imports, falsche Pfade, tote Referenzen). Subagent-Bee hat entweder (a)
  den Test gar nicht ausgeführt oder (b) einen fehlgeschlagenen Test als
  "interpretiert passed" zurückgemeldet. Variante (c) 2026-07-15:
  Subagent crasht ohne Result (`owner exited before recording a terminal result`).
- **REVIDIERT 2026-07-17 nach Live-Investigation:** Die "Mnemosyne-ID-Halluzination"-Variante
  wurde gestern 7-mal in Folge bei Subagenten beobachtet (Welle 1: 3/3,
  Welle 2: 3/3, Master-Anker 1/1). Root Cause war NICHT Subagent-Halluzination
  sondern **Tool-Bug** (siehe neues Pitfall #44): `mnemosyne_get` liefert
  `not_found` für ALLE Memory-IDs, auch für selbst-gesetzte. SQLite-Direkt-Query
  und `mnemosyne_recall` bestätigen dass die IDs real persistiert sind.
  → **Mnemosyne-Halluzinations-Vorwurf an Subagenten war 7/7 false positive.**
- **Erkennungs-Marker (Original):**
  - **"verified by inspection"** + **0 exit codes gemessen** = Variante (a)
  - **"minor warnings ignored"** + **keine Test-Logs angehängt** = Variante (b)
  - **"outcome unknown"** + leerer Output = Variante (c)
  - **"Mnemosyne-Anker ✅ ID <xyz>"** + mnemosyne_get not_found = Variante (d)
    → **Aber:** seit 2026-07-17 NICHT mehr als Halluzinations-Marker nutzen
    ohne SQLite-Cross-Check. Variante (d) ist Pitfall #44, nicht Subagent-Fehler.
- **Fix (Original bleibt gültig für Varianten a/b/c):** Queen-Seite MUSS
  Test-Output gegen Report-Claim prüfen: pytest exit code lesen, git diff
  scannen, Drittanbieter-Comments einholen, Crash-Rate monitoren.
- **Fix (Variante d — siehe #44):** Dual-Verification-Workflow mit
  `mnemosyne_recall(query=...)` statt `mnemosyne_get(id=...)`. SQLite-DB-
  Direkt-Query als Audit-Schicht.
- **Guard:** Queen-Briefing muss **"liefer exit code + letzte 20 stderr-Zeilen"**
  enthalten. Marker-Checkliste vor Queen-Approval abhaken.
- **Vollständige Methodik:** `references/subagent-self-test-deception.md`
- **Status:** teilweise-revidiert (Original-Varianten a/b/c weiterhin verified;
  Variante d zu Pitfall #44 verschoben)

### Pitfall #44 — mnemosyne_get Tool-Bug: liefert not_found für alle Memory-IDs (NEU 2026-07-17)

- **Symptom:** Nach jedem `mnemosyne_remember()`-Aufruf (sowohl von Subagent
  als auch von Queen) liefert `mnemosyne_get(memory_id=...)` den Status
  `not_found`, obwohl `mnemosyne_recall(query=...)` und SQLite-Direkt-Query
  die Memory eindeutig finden. Manifestation: 7/7 False-Positives an einem
  einzigen Tag (2026-07-17, Audit-Recovery-Plan-Execution), inklusive
  selbst-gesetzter Queen-Anker.
- **Root Cause:** Tool-Bug in `mnemosyne_get` — vermutlich falsche
  Memory-Bank abgefragt (working vs. episodic vs. long-term), falscher
  Index, oder falscher Filter. **NICHT** Subagent-Halluzination. Beweis:
  1. SQLite-Query `SELECT id FROM memories WHERE id=?` findet alle IDs.
  2. `mnemosyne_recall` mit Query auf Memory-Content findet dieselben IDs.
  3. `mnemosyne_get` für DIESELBEN IDs liefert not_found.
  → Asymmetrie zwischen mnemosyne_get und mnemosyne_recall + SQLite ist
  der Beweis dass das Tool kaputt ist, nicht die Daten.
- **Erkennungs-Marker:**
  - `mnemosyne_get(id=X)` → not_found, **aber** `mnemosyne_recall(query=Inhalt)`
    liefert ID X als Top-Treffer → Tool-Bug bestätigt
  - Subagent meldet "Mnemosyne-Anker ✅ ID X" → Queen-Check mit SQLite
    findet ID X mit korrektem Content → Halluzinations-Vorwurf ist false-positive
- **Fix — Dual-Verification-Workflow (Pitfall #36 Variante d):**
  1. **Statt** `mnemosyne_get(id=X)` direkt nach `mnemosyne_remember`:
     nutze `mnemosyne_recall(query="eindeutige Phrase aus X-Content")`
     und prüfe ob X als Top-Treffer mit Score ≥ 0.5 zurückkommt.
  2. **Wenn** Recall X nicht findet: SQLite-Audit
     `sqlite3 ~/.hermes/mnemosyne/data/mnemosyne.db "SELECT id, source, importance FROM memories WHERE id=X"`
     → wenn Treffer: Tool-Bug, X ist real.
     → wenn kein Treffer: tatsächlich nicht persistiert.
  3. **Queen-Anker IMMER selbst setzen** nach Subagent-Output als
     Defense-in-Depth (auch wenn Tool repariert wäre).
- **Workaround für Subagent-Briefings:** Statt "mnemosyne_get direkt nach
  remember" verlangen — das hat in Welle 2 die Halluzinations-Rate NICHT
  gesenkt (siehe 2026-07-17 Welle-2-Resultat). Statt dessen:
  - Subagent soll `mnemosyne_remember` aufrufen, ID zeigen, dann
  - Subagent soll `mnemosyne_recall` mit Query auf ersten 20 Zeichen
    des Contents machen und zeigen dass die ID als Top-Treffer kommt.
  - Das funktioniert weil Recall funktioniert (Tool nur asymmetrisch defekt).
- **Guard:** Bei jedem Mnemosyne-Verify-Workflow:
  - **Erst** Recall mit Query (funktioniert).
  - **Dann** SQLite-Cross-Check (funktioniert immer).
  - **Niemals** nur `mnemosyne_get` ohne Cross-Check akzeptieren.
  - Bei Anker-Count-Diskrepanz zwischen Subagent-Report und SQLite:
    es ist ein Tool-Bug, kein Subagent-Versagen.
- **Status:** verified (7/7 Live-Manifestationen am 2026-07-17, SQLite +
  Recall bestätigen alle Anker real; Master-Anker `55ac752a22eeb9f8`)
- **Cross-Reference:** Pitfall #36 (Variante d), Hermes-Tool-Bug-Report
  (Yuno-Report `~/.hermes/docus/reports/2026-07-17-mnemosyne-get-tool-bug.md`)

### Pitfall #37 — Bash→Python Migration Threshold (Validator Reliability)

- **Symptom:** Bash-Validator (`validate-design-kit.sh`) mit `awk -F','` erkennt 0 von 5 Failure-Pfaden korrekt. Exit-Code ist 0 statt 1 bei quoted CSV fields, fehlenden JSON-Schema-Feldern, und fehlender Nische im Pitch-JSON.
- **Root Cause:** Bash ist für einfache Exit-Code-Checks (1-3 Pfade) OK, aber bei >4 Edge-Cases, CSV-Quoting, und JSON-Schema-Validierung unzuverlässig: `awk` ignoriert CSV-Quotes, Pipe-Chains maskieren Exit-Codes, JSON-Handling erfordert `python -c`-Aufrufe.
- **Entscheidungsmatrix:**
  | Faktor | Bash | Python |
  |---|---|---|
  | CSV-Parsing mit Quotes | ❌ `awk -F','` bricht | ✅ `csv.reader` |
  | Schema-Validierung (>2 Felder) | ❌ Zeilenweises grep/find | ✅ dict-Keys + set-Compare |
  | Exit-Code-Reliability | ❌ Pipe-Chain maskiert | ✅ Explizites sys.exit |
  | >5 Edge-Cases | ❌ Jeder Case = neue Zeile awk/grep | ✅ Klare if/elif/else |
  | JSON-Handling | ❌ python -c Aufruf | ✅ Native json.load |
  | Encoding-Check | ❌ file + grep -aP | ✅ Python encode/decode |
  | Einfache Bedingungen (1-3 Checks) | ✅ Schneller geschrieben | ⚠️ Overhead |
- **Faustregel:** Wenn ein Validator/Script mehr als 3 Edge-Cases abdecken muss ODER CSV-Quoting involviert → sofort in Python. Bash ist ab 4 Failure-Pfaden nicht mehr reliability-safe.
- **Fix:** Komplett-Rewrite von Bash → Python. 4 Bugs gefixt, 5 neue Edge-Cases abgedeckt, 0 Regression.
- **Guard:** Vor jedem neuen Validator oder Script die Entscheidungsmatrix checken. Bei CSV-Quoting oder >3 Edge-Cases: Python.
- **Status:** verified (2026-07-15, tiktok-design-assistant Polish-Iteration, 16 von 18 Tests grün, 4 Bash-Bugs gefixt)

### Pitfall #38 — Strikte String-Matches in Heuristiken ohne Vault-Realitäts-Check (Daily-Report-Trigger-Welle-1)

- **Symptom:** Detection-Script prüfte nur exakt `^## Was lief` Section-Header. Real-Vault hat 11+ Variationen (`## Was lief (vermutet aus Mnemosyne-Recall)`, `## Was lief (echte Sessions rekonstruiert)`, `## Was lief (Nachmittag)`, `## Was Subagent C final berichtet hat`, `## Was noch offen ist für Phase 3`, `## Was Basti heute explizit gewollt hat`, plus `## 🚀 Hauptphase: ...` mit Emoji-Präfix). Resultat: 2026-07-03 wurde fälschlich als PARTIAL klassifiziert, obwohl die Section echten Inhalt hat.
- **Root Cause:** Plan-Annahmen basierten auf Template-Vorlage (`## Was lief` als einziger Header). Vault-Realität hat Variations-Space über 16 Daily-Files hinweg, aber Inventory wurde vor Plan-Phase nicht gemacht.
- **Fix:** Multi-Marker-Strategie mit case-insensitive Substring-Match auf Marker-Liste. Erste Section die matcht UND echten Content hat → HEALTHY. Marker-Set: `["was lief", "erkenntnisse", "lessons learned", "hauptaufgaben", "hauptphase"]`.
- **Guard:** Bei jeder Detection-/Heuristik-Planung **Vault-Inventory zuerst** — `find <vault> -name "*.md" | xargs grep -hE "^## " | sort | uniq -c | sort -rn` um zu sehen welche Section-Header existieren. Wenn Variations-Space > 3, dann Marker-Liste statt String-Match.
- **Status:** verified (live-manifested 2026-07-16, gefangen durch Queen-Audit, gefixt in Welle 2)
- **Kategorie:** workflow
- **Verwandt:** [[Daily-Report Session-Trigger Handoff 2026-07-16]]

### Pitfall #39 — Subagent Self-Report + enge Test-Annahmen = False-Green (Daily-Report-Trigger-Welle-1)

- **Symptom:** Subagent Welle 1 meldete "6/6 Tests grün" und "Implementation 1:1 wie im Plan". Real-Vault-Check durch Queen zeigte: 2026-07-03 mit `## Was lief (vermutet aus Mnemosyne-Recall)` Header wurde fälschlich als PARTIAL klassifiziert (4/5 Tage falsch klassifiziert). Subagent-Bericht war SELF-REPORT ohne Live-Verify. Hätte Basti das Feature 2 Tage später deaktiviert ("nervt der Trigger").
- **Root Cause:** Subagent-Tests testeten genau das was im Plan stand (exakter String-Match auf "Was lief"). Subagent hat keine Variation getestet. Es gab keine Verifikation gegen echte Vault-Daten.
- **Fix:** Queen-Audit mit Real-Vault-Verify nach jeder Subagent-Welle die Heuristiken implementiert. Pattern: ALLE existierenden Files im Vault gegen den erwarteten Output laufen lassen, nicht nur Test-Fixtures.
- **Guard:** Queen-Briefing für Heuristik-Subagents MUSS enthalten:
  1. "Liste ALLE Files im Target-Verzeichnis mit ihren erwarteten Klassen"
  2. "Lauf das Script gegen jedes File und zeige Output"
  3. "Bei Drift: STOP, frage die Queen"
- **Status:** verified (live-manifested 2026-07-16, Pitfall #36 hat sich fast selbst realisiert)
- **Kategorie:** orchestration
- **Verwandt:** [[Daily-Report Session-Trigger Handoff 2026-07-16]], Pitfall #36

### Pitfall #40 — Daily-Quality-Gate nicht gelaufen vor write_file = WikiLink-Strings statt echte Obsidian-WikiLinks (2026-07-16 Daily-Stub-Heilung)

- **Symptom:** Beim Daily-Stub-Heilen für 2026-07-16 hatte ich WikiLinks als Plain-Text-Bullets geschrieben (`- Daily-Briefing Skill v1.3.0 mit neuer Sektion 0.9`) statt als Obsidian-WikiLinks (`- [[Daily-Briefing Skill]] v1.3.0 mit neuer Sektion 0.9`). Grep-Check `\[\[` fand 0 WikiLinks obwohl ich 16 geschrieben hatte. Hätte Obsidian-Datenbank-Verknüpfungen verhindert.
- **Root Cause:** Quality-Gate-Check (EmDashes ≤ 1, Boldface = 0, InlineHdr = 0, NegParall = 0) hat WikiLink-COUNT nicht drin. Ich war nach den 4 Checks "grün" und hab nicht weiter geprüft.
- **Fix:** WikiLink-Count-Check mit ins Quality-Gate aufnehmen: Soll ≥ 3 (laut Mnemosyne-Discipline `b14b658422f017aa` Stub-Heuristik). Python-Check ist verlässlicher als grep:
  ```python
  import re
  wiki = re.findall(r'\[\[([^\]]+)\]\]', content)
  assert len(wiki) >= 3, f"WikiLink-Count {len(wiki)} unter Minimum 3"
  ```
  Achtung: bash `grep -F '\[\['` matcht NICHT weil bash die Klammern nicht literal behandelt — Python/json ist robuster.
- **Guard:** WikiLink-Count als 5. Quality-Gate ergänzen. Daily-Quality-Gate-Skript (`~/docs/system/quality-gates/daily-addendum-gate.sh`) updaten. Reihenfolge-Patch dokumentieren.
- **Status:** verified (live-manifested 2026-07-16, gefangen durch Queen-Audit mit Python-Regex statt grep-Bug)
- **Kategorie:** workflow
- **Verwandt:** Pitfall #37 (Bash→Python Migration Threshold), [[Daily-Briefing Skill]]

### Pitfall #41 — Audit-Scope-Creep verhindert Cross-Domain-Sanity-Check (Daily-Tracking-Audit 2026-07-16)

- **Symptom:** Heute Abend habe ich ein Deep-Audit auf Daily-Tracking durchgeführt (4 Reports, 1.200+ Wörter, ~135 Min Tool-Chain). Habe die Daily-Notes, Vault-Section-Header, Crontab, Mnemosyne-Memories und 4 Subagent-Wellen verifiziert. Was ich NICHT verifiziert habe: die SECURITY-LÜCKEN vom 09.07. (GitHub-OAuth hardcoded in `config.yaml:727`) und 13.07. (Zep-API-Key-Exposure in `state.db`). Beide sind 8 Tage alt und waren in Mnemosyne dokumentiert mit `importance 0.95` — ich habe sie in der heutigen Pipeline nicht angesprochen. Audit-Prompt war "Daily-Tracking + Memory + Vault" — diese Scope-Definition hat verhindert, dass ich die Schwester-Domain Security-Hardening cross-validiere.
- **Root Cause:** Deep-Audits sind stark, aber sie verengen den Scope auf eine Domain. Der tägliche Audit-Prompt ("daily briefing audit alle tage getrackt") hat mich fokussiert auf Tracking-Aspekte gehalten, ohne dass ich die system-weite Risikoliste geprüft habe. Pitfall #38 ist erkannt worden (Heuristik-Bug), aber die Cross-Domain-Sicherheitslücken sind unentdeckt geblieben.
- **Fix:** T-Shaped Audit-Pattern (Broad + Deep): vor jedem Deep-Audit ein 2-Min Cross-Domain-Sanity-Check (`grep -E '(gho_|ghp_|sk-|sk_ant-|api_key|token|secret).*='` in kritischen Config-Files + `journalctl -p warning -S today` + `df -h`). Dann erst die Deep-Audit-Schicht. Diese Cross-Domain-Sanity-Check-Liste sollte in `self-improving` Skill als Standard-Workflow dokumentiert sein.
- **Guard:** Bei jedem Audit-Auftrag mit Domain-Scope ("daily audit", "memory audit", "performance audit") — MUSS vor Deep-Dive ein 3-Fragen-Cross-Check laufen: (1) Welche Schwester-Domänen gibt es? (2) Was war im Mnemosyne-High-Importance-Bereich (≥ 0.85) der letzten 30 Tage? (3) Gibt es bekannte open Issues in `~/.hermes/docus/reports/` oder `~/docs/system/`?

**Konkrete Operationalisierung:**

```bash
# Vor jedem Deep-Audit (Memory, Performance, Daily, Vault):
bash ~/.hermes/scripts/audit-cross-domain-sanity.sh --dry-run
# Bei RED in einer Domain → diese Domain NICHT im aktuellen Audit vertiefen,
# sondern Quick-Acknowledge + Eskalation an Basti (Telegram-Route).
```

**Trigger-Words für Audit-Skill-Routing:** "audit", "review", "health-check", "verifiziere", "prüfe" → immer Sanity-Check zuerst.
- **Status:** verified (live-manifested 2026-07-16, gefangen durch Bastis direkte Nachfrage "die kritischen Lücken können wir ignorieren")
- **Kategorie:** workflow
- **Verwandt:** Pitfall #38 (Vault-Realitäts-Check), Mnemosyne `49a2c910fcb83e35` (Security-CRITICAL-Fund 09.07.), Mnemosyne `06d4c32b66bb7f4d` (Forensik-Audit Zep-Key 13.07.)

### Pitfall #42 — Mnemosyne-Referenced-File-Existence-Halluzination (Quality-Gate-Fantasie 2026-07-17)

- **Symptom:** Mnemosyne-Recall behauptet dass ein File existiert — z.B. `~/docs/system/quality-gates/daily-addendum-gate.sh`, referenziert in Memory mit importance 0.88. Agent startet Workflow der annimmt File existiert. `ls -la` zeigt: **File existiert nicht.** 30-60 Min für einen 5-Min-Patch verschwendet.
- **Root Cause:** Mnemosyne ist ein semantic-recall System. Es merkt sich dass ÜBER ein File GESPROCHEN wurde („sollte erstellt werden", „wir haben besprochen dass"), nicht dass es EXISTIERT. Mnemosyne hat KEINEN Filesystem-Zugriff — es kann Pfad-Existenz nicht verifizieren. Der Agent muss das selbst machen.
- **Fix:** Vor JEDEM memory-getriebenen File-Zugriff: `ls -la <path>` IMMER vor dem ersten Tool-Call. Wenn File nicht existiert: (a) in Memory vermerken dass Pfad nicht existiert (damit Mnemosyne lernt), (b) File neu erstellen oder Workflow anpassen. NIE annehmen dass Memory-File-Pfade aktuellen Disk-State abbilden.
- **Guard:** 3-Fragen-Regel vor jedem Memory-getriebenen File-Operation-Start:
  1. `ls -la` — existiert das File im aktuellen System?
  2. `stat` — stimmt Größe/ModTime mit Memory-Beschreibung?
  3. `head -5` — ist Inhalt was Memory beschreibt?
  Erst wenn alle 3 ✅ → auf Memory-Annahme bauen.
- **Status:** verified (live-manifested 2026-07-17, Pre-Scout Queen-Phase entdeckte Fantasie BEVOR Dispatch — erfolgreiche Mitigation durch Queen-Pre-Execute-Pattern)
- **Kategorie:** workflow
- **Verwandt mit:** Pitfall #38 (Vault-Realitäts-Check), Pitfall #41 (Audit-Scope-Creep), post-plan-queen-verify.md (Plan-Annahmen-Check), plan-glm SKILL.md (Plan assumptions about real system state)

### Pitfall #43 — Anthropomorphizing Tool Interfaces (Telegram-Notify aus Cron 2026-07-17)

- **Symptom:** Bei der Erstellung von 4 Audit-Cron-Wächtern schrieb ich
  `hermes send_message "$TELEGRAM_TARGET" "msg"` in die Bash-Skripte. Sanity-Test
  zeigte: `hermes` CLI gibt nur `usage: hermes [-h] ...` zurück — `send_message`
  existiert NICHT als CLI-Subcommand. Musste 3 Skripte nachträglich auf
  `source $HOME/.hermes/.env` + `curl` umschreiben (das Pattern das 3 bestehende
  Cron-Skripte bereits korrekt verwenden).
- **Root Cause:** Ich habe das CLI-Interface von `hermes` **anthropomorphisiert** —
  weil Hermes der "Messenger" ist, nahm ich an `hermes send_message` müsse
  existieren. Statt nach vorhandenen Mustern zu suchen (`grep -r "send_message\|curl.*telegram" ~/50-System/bin/`), habe ich die CLI-Signatur geraten.
- **Fix:** Vor dem Schreiben von Cron-Skripten die Telegram-Notify-Pattern aus
  bestehenden Implementierungen scannen:
  ```bash
  grep -rl "TELEGRAM_BOT_TOKEN\|sendMessage" ~/50-System/bin/ ~/.hermes/scripts/
  ```
  Der korrekte Pattern ist `source $HOME/.hermes/.env` + `curl` —
  dokumentiert in `linux-system-maintenance/references/telegram-cron-notify-pattern.md`.
- **Guard:** Drei-Fragen-Regel vor jedem CLI-Tool-Zugriff in neuem Kontext:
  1. Existiert dieses Subcommand? (`hermes --help` / `hermes <subcommand> --help`)
  2. Gibt es existierende Implementierungen die ich als Template nutzen kann?
     (`grep -r "pattern" ~/50-System/bin/ ~/.hermes/scripts/`)
  3. Falls NEIN: ist der Pattern sinnvoll oder rate ich nur? → Klären, nicht raten.
- **Status:** verified (live-manifested 2026-07-17, gefangen durch Sanity-Test Phase 4)
- **Kategorie:** tool-quirk
- **Verwandt mit:** Pitfall #37 (Bash→Python Migration Threshold — Interface-Raten als Variante), `linux-system-maintenance/references/telegram-cron-notify-pattern.md` (der korrekte Pattern)

### Pitfall #45 — yaml.safe_load + Re-Render zerstört FM-Blöcke (Skill-Audit 2026-07-23)

- **Symptom:** Nach Patch-Frontmatter-Skript (yaml.safe_load + manual Re-Render) waren nested dicts (`metadata.hermes.tags: ['Research', ...]`) zu Python-Repr-Strings mutiert (`metadata: > {'hermes': {'tags': [...]}}`). YAML war valid aber semantisch kaputt — Skill-Loader kann Tags nicht mehr lesen.
- **Root Cause:** `yaml.safe_load` parst folded/literal scalars (`description: >`, `description: |`) zu Plain-Strings, aber beim Re-Render geht die Scalar-Style-Info verloren. Nested dicts (z.B. `metadata:` mit Sub-Keys) werden als Python-dict-Repr gerendert statt als YAML-Nesting. **Information Loss beim Round-Trip.**
- **Fix:** **NIEMALS** yaml.safe_load + Re-Render für Frontmatter-Modifikation. Stattdessen: **Raw-Text-Injection** — FM-Block als Text behalten, neue Keys per `regex.subn` am Ende des FM-Blocks (vor schließendem `---`) injecten. Siehe `~/.hermes/scripts/skill-audit/patch_frontmatter_v3.py`.
- **Guard:** Bei jedem Massen-Patch auf SKILL.md Frontmatter: (1) Raw-Text-Approach nutzen, (2) Dry-Run auf ≥5 Skills mit YAML-Validation, (3) `yaml.safe_load` nur zum VALIDIEREN nicht zum SCHREIBEN.
- **Status:** verified (3 Iterationen: v1 zerstörte dicts, v2 zerstörte folded scalars, v3 raw-text-injection OK)
- **Kategorie:** tool-quirk

### Pitfall #46 — routing_hint: | enthält andere Keys als Description (Skill-Audit 2026-07-23)

- **Symptom:** `polish_triggers.py` regex `r"trigger_keywords:\s*\[[^\]]*\]"` matcht nicht nur den Top-Level-FM-Key sondern AUCH Vorkommen innerhalb von `routing_hint: |` Multi-Line-Blocks (die Skill-Beschreibungen mit `trigger_keywords: [...]` als Beispiel-Text enthalten). Resultat: `trigger_keywords`-Zeile im Body überschrieben, FM-Key intakt → Skill hat keine Trigger mehr im Body aber falsche im FM.
- **Root Cause:** `routing_hint: |` ist ein Literal-Block-Scalar. Der gesamte Block wird als Text behandelt, aber regex-Sub ohne `re.MULTILINE` + `^`-Anchor matcht beliebige Vorkommen im Text.
- **Fix:** Regex MUSS `^key:` mit `re.MULTILINE` matchen, damit nur Top-Level-FM-Keys (Spalte 1, keine Einrückung) getroffen werden. Siehe `polish_triggers_v3.py`: `re.compile(r'^trigger_keywords:\s*\[[^\]]*\]', re.MULTILINE)`.
- **Guard:** Bei jedem Regex-Replace auf YAML-FM: IMMER `re.MULTILINE` + `^`-Anchor für Top-Level-Keys. Niemals ungreedy-Match ohne Anchor.
- **Status:** verified (2 Iterationen bis Fix in v3)
- **Kategorie:** tool-quirk

### Pitfall #47 — curated_by Heuristik: 'Yuno (Klammer)' ≠ 'Yuno' (Skill-Audit 2026-07-23)

- **Symptom:** `polish_triggers_v2.py` überschrieb hand-curated `trigger_keywords` von mirofish (`['mirofish', 'simulation', 'multi-agent', 'distill', 'monitor', 'ontology', 'report']`) mit auto-generierten generischen Tokens (`['simulation', 'report', 'set', 'run']`). Die curated_by-Heuristik `cb == 'yuno'` matchte fälschlich `curated_by: Yuno (auto-curated v2.1)` weil die Klammer-Signatur als Substring durchging.
- **Root Cause:** `looks_auto(curated_by)` prüfte `cb in ('yuno', "'yuno'")` — das matched `Yuno` aber die Heuristik war zu permissiv mit Klammer-Suffixen. `"yuno (auto-curated v2.1)".lower()` enthält `"yuno"` als Substring → matched `in ('yuno', ...)` fälschlich.
- **Fix:** Strikte Trennung: `cb == 'yuno'` (exact) ODER `'auto-curated' in cb` (substring für explizite Auto-Signaturen). Klammer-Suffixe wie `Yuno (Biene 3 von 2026-07-17)` oder `Yuno (v2.5.0 — Dual-Path...)` sind HAND-curated und werden NICHT gematcht.
- **Guard:** Auto-Curation-Heuristik MUSS folgende Fälle unterscheiden: `Yuno` (auto, match), `Yuno (auto-curated v2.1)` (auto, match), `Yuno (Biene 3 von 2026-07-17)` (hand-curated, NO match). Test-Suite vor Deployment.
- **Status:** verified (1 Fehlalarm auf mirofish, gefixt in v3)
- **Kategorie:** workflow

### Pitfall #48 — ~/.hermes/skills/ hat kein Git: tar.gz-Backup OBLIGATORISCH (Skill-Audit 2026-07-23)

- **Symptom:** Nach 319 Frontmatter-Patches wollte ich den Stand sichern. `git status` in `~/.hermes/skills/` → "fatal: Kein Git-Repository". Keine Versionssicherung, keine Möglichkeit zu Rollback außer externes Backup.
- **Root Cause:** Skills-Directory ist kein Git-Repo. Anders als Code-Repos gibt es keinen automatischen History-Trail. Massen-Edits (319+ Files) sind irreversibel ohne externes Backup.
- **Fix:** **Vor JEDEM Massen-Patch** (≥10 Files): `tar -czf /tmp/skill-audit-backups/skills-<reason>-$(date +%Y-%m-%dT%H-%M-%S).tar.gz -C ~/.hermes skills`. Wrapper-Script: `~/.hermes/scripts/skill-audit/run-backup.sh`.
- **Guard:** Pre-Flight-Check vor Massen-Patch: `git -C ~/.hermes/skills status 2>/dev/null || echo "NO GIT → tar.gz backup needed"`. Wenn kein Git → Backup-Script MUSS laufen vor Patch.
- **Status:** verified (hat 1× das Leben gerettet: Polish-Bug zerstörte trigger_keywords, rsync-Restore aus tar.gz in 5 Sekunden)
- **Kategorie:** workflow

### Pitfall #49 — Monolith-Split Self-Reference in related_skills (Skill-Audit 2026-07-23)

- **Symptom:** mirofish v2.6 hatte `related_skills: ['mirofish', 'multi-agent-cluster-patterns', ...]` — Self-Reference. Nach Split in mirofish-pipeline/-analysis/-pitfalls/-runbook referenzierte der Original-Skill sich selbst statt die neuen Sub-Skills.
- **Root Cause:** Beim Split wurde der Original-Skill zum Router, aber `related_skills` wurde nicht auf die Sub-Skill-Namen aktualisiert. Sub-Skills wiederum referenzieren die Geschwister korrekt, aber der Router zeigt auf sich selbst.
- **Fix:** Bei JEDEM Monolith-Split: (1) Original `related_skills` durch Sub-Skill-Namen ersetzen, (2) Sub-Skills mit Geschwister-Referenzen ausstatten, (3) Cross-Check: `grep -r "related_skills" <family>` zeigt keine Self-References mehr.
- **Guard:** Post-Split-Verification: für jeden Sub-Skill prüfen dass `related_skills` mind. 1 Geschwister + den Router enthält, KEINE Self-Reference.
- **Status:** verified (beim mirofish+kanban Split 2026-07-23 korrigiert)
- **Kategorie:** workflow

### Pitfall #50 — Section-Heading-Routing für Monolith-Splits braucht State-Machine (Skill-Audit 2026-07-23)

- **Symptom:** Erstes Split-Skript gruppierte Sections nur nach Top-Level-Heading (`## Step 1`, `## Step 2`). Sub-Sections (`### 1. Kill Stale Workers`) ohne aktuellen Parent gingen in den Default-Bucket, verloren ihren Kontext.
- **Root Cause:** Simple if/elif-Routing ohne State-Machine kennt den "current parent" nicht. Wenn eine `###` Section kommt ohne dass die vorherige `##` Section erkannt wurde, fällt sie in den Default-Bucket.
- **Fix:** State-Machine mit `current_group` Variable: jede `##` Section setzt `current_group`, jede `###` Section erbt `current_group`. Nur unbekannte `##` Sections starten neuen Default-Bucket.
- **Guard:** Split-Skripte benötigen IMMER: (1) State-Machine mit `current_group` für H3/H4-Inheritance, (2) Dry-Run mit Section-Count pro Bucket (Summe muss Original matchen), (3) Post-Verify: jeder Sub-Skill hat ≥1 Section aus jeder deklarierten Phase.
- **Status:** verified (State-Machine in split_mirofish.py + split_kanban.py)
- **Kategorie:** workflow

### Pitfall #51 — Cyber-Skill-Import Prefix non-idempotent (kyssta-Bulk-Import 2026-07-23)

- **Symptom:** Beim 2. Lauf von `import_kyssta.py cyber` wäre `cyber-cyber-analyzing-cyber-kill-chain` rausgekommen — die Prefix-Logik prüft `if not s["name"].startswith("cyber-")` aber der Re-Run findet einen skill `cyber-X` als SKILL-Namen (mit kurated_by bereits drin) und der Match im inventory hat den un-prefix-ierten Namen. Resultat: doppelte Skills oder Prefix-Chain.
- **Root Cause:** Bulk-Import-Pattern hat zwei Modi: (a) initial — prefix hinzufügen, (b) re-run — skippen via `curated_by`-Check. Aber inventory wird vom Mirror-Dump geladen, nicht vom Filesystem-Stand. Inventory hat immer die un-prefix-ierten Namen.
- **Fix:** **Idempotenter Gate vor jedem Import:** `if /home/bratan/.hermes/skills/cyber-<name>/SKILL.md.exists() and 'yuno-kyssta-import' in content: skip; else: import with prefix`. Plus: Inventory-Detail-File (`01-inventory-detail.jsonl`) cachen und mit aktuellem Filesystem-Stand abgleichen, dann ggf. Re-Download vom Mirror.
- **Guard:** Vor jedem Bulk-Import ≥50 Skills: (1) Snapshot via `tar -czf` (siehe P48), (2) Inventory-Refresh vom aktuellen Mirror, (3) Idempotenter Gate mit 'curated_by'-Check, (4) Dry-Run-Mode vor echtem Lauf.
- **Status:** verified (kyssta-Import 2026-07-23: 884 Skills, idempotent via Gate geplant)
- **Kategorie:** workflow

### Pitfall #52 — Cyber-Skills in unzulässige Profile leaken = Lane-Lock verletzt (kyssta-Bulk-Import 2026-07-23)

- **Symptom:** Cyber-Skills dürfen per Security-Lane-Isolation NICHT in `yuno-vision`, `yuno-flash`, `ui-builder`, `yunoo` Profile — sonst triggern sie in Vision- oder UI-Kontexten (was gefährlich ist: Security-Tools in Non-Security-Kontext = false-positive-Trigger oder ungewollte Tool-Empfehlungen).
- **Root Cause:** `LANE_PROFILE_MAP` im profile_sync-Adapter muss jede Cyber-Skill gegen die Blacklist prüfen. Wenn Profile-Sync-Logik `profiles/<name>/skills/<category>/<skill>/` mechanisch folgt und die lane-Blacklist nicht enforced, landen Skills überall.
- **Fix:** **Hard-Lane-Map mit Default-Deny:** Cyber-skills gehen **ausschliesslich** in default, yuno, yuno-coder, local-9b. Andere Profile bekommen sie NICHT, auch wenn ihre Category-Folder vorhanden wäre. Plus: Post-Sync-Validation `find <prof>/skills -name "SKILL.md" | xargs grep -l "^lane: security" | wc -l` muss in vision/flash/ui/yunoo = 0 sein.
- **Guard:** Profile-Sync-Adapter MUSS immer eine Post-Sync-Lane-Check-Pass machen: für jedes Profile `security_count = grep ... | wc -l`, und Lane-Blacklist (`vision`, `flash`, `ui-builder`, `yunoo`) MUSS `security_count == 0` haben.
- **Status:** verified (kyssta-Import: yuno=822, default=823, yuno-coder=823, local-9b=822 Cyber-skills; vision/flash/ui-builder/yunoo = 0 Cyber-skills)
- **Kategorie:** workflow

---

## Post-Audit Mnemosyne-Reflexion (Pflicht nach jedem Audit ≥ 30min)

Nach jedem Audit (Daily, Memory, Performance, Vault, Security, Skill) MUSS innerhalb von 15 Min ein Mnemosyne-Eintrag erzeugt werden. Template: `~/.hermes/templates/post-audit-mnemosyne-template.md`. Audit-Pattern-Lessons lernen NICHT aus Reports — sie lernen aus strukturiertem Recall. Ohne Template wird die nächste Subagent-Welle die gleichen Pitfalls wiederholen.

**Trigger-Words (Audit-Skill-Routing):** "audit", "review", "verifiziere", "prüfe system", "memory health" → am Ende IMMER Post-Audit-Mnemosyne-Call.

---

## Cross-Session Lesson Consolidation (Einzel-Agent)

> **Ergänzung zum Proaktiven Lessons-Scan** — für den Fall, dass du **ohne
> Subagenten** arbeitest (Standard bei TUI/CLI-Sessions) und Lessons aus
> mehreren Sessions kombinieren musst.
> **Eingesetzt 2026-07-07:** 3 Sessions → 17 Lessons in 3 Kategorien.

### Wann dieser Modus greift

- TUI/CLI-Session ohne Dispatch-Fähigkeit (kein Schwarm)
- Basti sagt: "analysiere Sessions X, Y, Z kombiniert auf Thema T"
- Lessons liegen **über mehrere Sessions verteilt** und müssen zusammengeführt werden
- Session-Größe übersteigt Context-Window → Scroll-Strategie nötig
- **NICHT** bei akuten Einzelfehlern (dann 5-Step-Loop)

### Phase 0: Gezielte Session-Discovery

Anders als beim Schwarm (breite Suche via Keywords): hier kennst du Sessions
(oder Basti hat sie genannt). Nutze `session_search` mit präzisen Queries:

```python
# Discovery mit verschiedenen Suchwinkeln (parallel batching!)
session_search(query="<Kernbegriff1>", limit=3)
session_search(query="<Kernbegriff2> OR <Kernbegriff3>", limit=3)
```

**⛔ Falle FTS5-Trefferquote:** Die Session-DB hat Keyword-Indexing, kein
semantisches Verständnis. Phrasen wie "telegram delivery cron gateway error
timeout" können **0 Treffer** liefern, während der Inhalt in der Session steckt.
**Workaround:** Zerlege die Query in Einzelbegriffe (`cron AND gateway`,
`telegram AND timeout`) und prüfe die Treffer.

**Wenn eine Session 229+ Messages hat** → lies `bookend_start` (erste 3
Messages = Goal/Kickoff) + `bookend_end` (letzte 3 = Resolution) und die
`snippet` der Match-Stelle. Entscheide dann ob Scrollen nötig ist.

### Phase 1: Progressiver Scroll (Batch-Strategie)

Scrolle **alle Sessions sequentiell** und **in Batches**:

```python
# Batch 1: Discovery parallel
session_search(query="topic1", limit=3)
session_search(query="topic2", limit=3)

# Batch 2: Scroll in die ergiebigsten Sessions (parallel!)
session_search(session_id="A", around_message_id=X, window=10)
session_search(session_id="B", around_message_id=X, window=10)
```

**Max 3 Batches pro Phase.** Wenn nach 3 Batches kein klarer Kern da → `clarify()`.

**⛔ Scroll-Fallen:**

| Falle | Symptom | Workaround |
|-------|---------|------------|
| `around_message_id` out of range | "not in session" | Session-ID aus `bookend_start` prüfen |
| Session >100KB | Jeder Scroll-Call 200+ Tokens | Nur Schwerpunkte scrollen |
| Discovery auf tool-output | Snippet zeigt Tool-Response, nicht User-Context | 2 Messages davor lesen |
| **Massive Truncation** | "Full output could not be saved (179,792 chars)" | Discovery hat whole-session-Read getriggert → `limit=3`, präzisere Query |

### Phase 2: Konsolidierung

Nachdem alle Sessions durch sind:

1. **Alle Funde sammeln** in einem Rohdokument
2. **Deduplizieren** — gleicher Root Cause: detailliertere Version behalten
3. **Kategorisieren** — 3–4 Oberkategorien (Treiber/GPU, EDID/Display, Cron/Telegram, Workflow)
4. **Priorisieren** — 🟥 (verified+high) > 🟧 (verified+medium) > 🟨 (hypothese)
5. **Cross-Links setzen** — verwandte Lessons referenzieren
6. **Output schreiben** — typischerweise als Obsidian-Archiv-Notiz

**⛔ Kontext-Verlust:** 3 Sessions nacheinander scrollen → was in Session A
war, ist bei Session C weg. **Fix:** Zwischenergebnisse im `todo`-Tool oder
in einer Datei sammeln.

### Phase 3: Output-Format (Kombiniertes Lessons-Dokument)

```markdown
# Self-Improving Lessons — <Thema> (Konsolidiert <Datum>)

**Quell-Sessions:**
1. `<session_id>` (<Titel>)

---

## 🟥 <KATEGORIE 1>

### [<DATUM>] <Titel>
- **Symptom:** ...
- **Root Cause:** ...
- **Fix:** ...
- **Guard:** ...
- **Status:** verified | hypothese
- **Kategorie:** tool-quirk | build-error | workflow | orchestration | hardware

---

## 🟧 <KATEGORIE 2>
...

## 🔗 Cross-References
- `<Link zu Datei/Skill>`
```

**Unterschied zum Einzel-Lesson-Format:**
- **Priority-Emoji** (🟥/🟧/🟩) pro Kategorie
- **Cross-Links** zwischen verwandten Lessons
- Alle Felder **fett** (`**Status:**` statt `Status:`)
- Dokument **nicht** >30 KB (sonst unleserlich)

**Referenz-Output 2026-07-07:**  
`~/Dokumente/Obsidian Vault/07 Archiv/2026-07-07 - Self-Improving Lessons Hardware Performance.md`  
(26.6 KB, 17 Lessons)

**Referenz-Output 2026-07-07 (2 Sessions, Orchestrierung + Tools):**  
`~/docs/system/session-lessons-2026-07-02-and-2026-07-06.md`  
(32.3 KB, 28 Lessons, 5 Kategorien: tool-quirk 11, workflow 10, orchestration 5, build-error 2)

### Query-Erfahrungen

Erfahrungen aus 2026-07-07 (3 Sessions analysed):
- **lange Phrasen (>4 Wörter) liefern oft 0 Treffer** — auf 2-3 Wort-Kombos reduzieren
- **session_id = bester Einstieg** wenn Session bekannt ist
- **Scroll immer batchen** — nie nur eine Session nacheinander
- **279,792-Char-Truncation** vermeiden: `limit=3` statt 10 bei Discovery

Detail: `references/cross-session-consolidation.md`

### Discovery-Tuning (FTS5-Pitfalls, Stand 2026-07-15)

#### Pitfall: Lange Phrasen (>4 Wörter) liefern 0 Treffer

- **Symptom:** `session_search(query="2026-07-14 OR 14.07 Mission Hermes Daily", limit=3)`
  → 0 Treffer trotz klarem Inhalt.
- **Root Cause:** FTS5-Index arbeitet auf Token-Ebene. Bei Phrasen mit Sonderzeichen
  (`OR`, `.`, Bindestrichen) wird der Index gesplittet und kein zusammenhängender Match gefunden.
- **Fix:** Phrasen auf 2-3 Wort-Kombos reduzieren:
  ```python
  session_search(query="mission hermes", limit=3)
  session_search(query="telegram cron", limit=3)
  ```
- **Guard:** Phrasen-Queries IMMER mit `OR` zerlegen und Sub-Queries parallel batchen.

#### Pitfall: Massive Truncation blockiert Folge-Tool-Calls

- **Symptom:** "Full output could not be saved (179,792 chars)" → /tmp-Persistierung,
  jeder weitere Tool-Call muss Output laden.
- **Root Cause:** Discovery limit zu hoch (10) bei dichten Sessions → Reader triggert
  Whole-Session-Read.
- **Fix:** `limit=3` bei Discovery, präzisere Queries (siehe oben), Scroll statt Discovery.
- **Guard:** Niemals `limit > 5` bei Discovery. Snippet-Länge im Output prüfen —
  wenn >5KB → Phrase zerlegen.

## Proaktiver Lessons-Scan (Session-Mining)

Dieser Skill hat zwei Modi:

### Reaktiv (5-Step-Loop oben)
Ein konkreter Fehler/Korrektur passiert → Erkennen → Einordnen → Schreiben → Verifizieren.

### Proaktiv (Session-Mining)
Periodisches Durchforsten vergangener Sessions, um Lektionen zu extrahieren, auch
wenn kein akuter Fehler vorliegt. **Eingesetzt 2026-07-07:** 6-Bee-Schwarm über
9 Sessions der letzten 7 Tage → 30+ Lessons extrahiert.

**Workflow:**
1. Session-Discovery: `session_search` mit Error/Workaround-Keywords
2. Welle 1: 3 Bienen auf die ergiebigsten Sessions (fokussierte Briefings)
3. Welle 2: 2-3 Bienen auf restliche Sessions
4. Königinnen-Konsolidierung: Dedup → Priorisieren → Mnemosyne → Skill-Promote
5. Basti-Report: Kurzes Summary mit Top-3, Bug-Quote, Promote-Status

**Detaillierte Methodik:** Siehe `references/session-analysis-methodology.md`
— enthält Briefing-Vorlage pro Biene, Such-Queries, Output-Schema, Check-Liste.

## Externe Analyse Verifikation

> **Eingesetzt 2026-07-07:** Claude-Audit von 248 Hermes Skills — 7 Claims
> live verifiziert, 1 Major-Misinterpretation korrigiert, 55MB Phase-1-Fixes,
> 2 neue Mnemosyne-Lessons.
> **Kern-Lektion:** Externe Audits sind KEINE Wahrheit — immer Claims
> gegen Live-Code verifizieren, bevor Lessons gespeichert werden.

### Wann dieser Modus greift

- Basti teilt einen externen Report / Audit / Analyse (von Claude, Gemini, Hub, etc.)
- Der Report enthält **überprüfbare Claims** (Zahlen, Pfade, Code-Strukturen)
- Du sollst selbstständig bewerten — nicht blind übernehmen
- **NICHT** bei Bastis eigenen Workflow-Korrekturen (dann der normale 5-Step-Loop)

### Workflow (6 Phasen)

#### Phase 1: Empfang + Struktur-Erfassung

1. Rohdokument lesen (beide Files — Report + Fix-Skript wenn vorhanden)
2. Claims extrahieren: Jede Behauptung mit Zahlen/Pfaden/Code-Zitaten notieren
3. Priorität zuweisen (P0–P3 basierend auf Autor-Bewertung)

#### Phase 2: Live-Verifikation

Jeden Claim einzeln gegen Live-Code prüfen:

```bash
# Claim: "0/72 Hash-Matches im Manifest"
→ cat .bundled_manifest | wc -l   # Einträge zählen
→ grep skill_name .bundled_manifest | head -3  # Format prüfen
→ code inspection: tools/skills_sync.py  # WAS das Manifest macht
```

Für Code-Claims:
```bash
grep -rn '<Schlüsselwort>' ~/.hermes/hermes-agent/tools/ --include='*.py' | grep -v __pycache__
code inspection: cat -n <relevant_file.py>
```

3 Outcomes pro Claim:

| Prüfung | Bedeutung | Aktion |
|---|---|---|
| 🟩 Bestätigt | Behauptung stimmt | Claim akzeptieren, ggf. in Fix-Plan aufnehmen |
| 🟨 Teils richtig | Wahrheit aber Fehlinterpretation | Adjustieren, korrigierte Version speichern |
| 🟥 Falsch | Nicht belegbar oder falsch interpretiert | Korrigieren, Mnemosyne-Lesson mit Gegenbeweis schreiben |

#### Phase 3: Fixes anwenden (nur Safe Fixes)

Prinzip: Nur fixen, was live bestätigt und rückgängig machbar ist.

- ✅ Python-Bytecode löschen (`__pycache__`, `.pyc`)
- ✅ Backup-Rekursionen kappen (Archiv im Archiv)
- ✅ Curator-Backup-Retention (nur 3 Generationen)
- ✅ Manifest neu generieren (SHA-256 statt MD5)
- ❌ **NICHT:** Code patchen / Configs ändern / Services restarten ohne Bastis Freigabe
- ❌ **NICHT:** Pfade auslagern (Verschieben = Code-Änderung = Phase 4)

#### Phase 4: Mnemosyne-Lessons speichern

Mindestens 2 Lessons pro Audit:

1. **Korrektur-Lesson:** Was der Audit falsch hatte + warum + Code-Beweis
2. **Fix-Lesson:** Was angewendet wurde + wieviel gespart + was offen blieb

Tags-Schema für Audit-Lessons:
```python
tags=["lesson", "hermes", "audit-correction", "<domain>"],
metadata={
    "category": "self-improving-lesson",
    "status": "verified",
}
```

#### Phase 5: Report an Basti

```markdown
## 🔬 Yuno's Audit-Review

### Verifizierte Fakten
| Claim | Audit sagt | Live geprüft | Status |
|---|---|---|---|
| 1. Hash-Provenance | 🟥 P0 = ... | Code: ... | 🟩 Korrigiert |

### Kein Fix (mit Begründung)
| Aus Audit | Nicht gemacht | Grund |
|---|---|---|
| Schritt X | ... | ... |

### Angewendete Fixes
1. ✅ Pycache entfernt (N Files)
2. ✅ SHA-256 Manifest (N Einträge)
...
**Gespart:** X MB
```

#### Phase 6: Korrektur in Self-Improving verewigen

- Jede korrigierte Fehlinterpretation als `status: verified` Lesson in Mnemosyne
- Tags: `["hermes", "audit-correction", "<domain>"]`
- So vermeidest du denselben Fehler selbst zu machen

### Typische Audit-Fehler (aus der Praxis 2026-07-07)

1. **Provenance-Überinterpretation:** Ein Sync-Tracker (`.bundled_manifest`) wird als Security-Feature missverstanden. Immer Code lesen, nicht Doku.
2. **Zahlen ohne Kontext:** "36 Dupes" klingt schlimm — aber wenn 36/248 Skills 1 Look-alike haben ist das normal. Prüfe ob Dupes echte Duplikate sind oder ähnliche Kategorien.
3. **Hardcoded-Path-Alarm:** "140× /home/bratan" — wenn der Path vom Framework gesetzt wird (Agent-CWD) ist das KEIN Fix. Prüfe ob der Path aktiv schadet.
4. **Code lesen > Doc lesen:** `skill_usage.py` macht was anderes als der Audit behauptet. Immer tatsächlichen Code lesen, nicht Kommentare.

Detail: `references/audit-verification-workflow.md`

## Diagnostic Methodology — Avoiding False Negatives from Default Tool Output

> **Gelernt 2026-07-16:** Bei der GPU-Split-Diagnose sagte ich fälschlich
> "nicht realisierbar" — weil ich mich auf default `vulkaninfo` + `xrandr`
> verließ, ohne die ICD zu forcieren oder sysfs zu prüfen. Basti fragte
> nach ("warum nicht?") und beim tieferen Graben zeigte sich: Intel iGPU
> hat Vulkan-Compute, war nur vom Default-Loader versteckt.
> **Root Cause:** Default-Tools zeigen nur, was sichtbar ist — nicht was
> existiert. Wayland hat keine PRIME-Provider-API; `xrandr: number=0` ist
> normal. `vulkaninfo` default priorisiert den primären Display-GPU-ICD.
> **Kern-Lektion:** "Nicht gefunden" ≠ "nicht vorhanden" auf Dual-GPU.
> **Detail-Reference:** `references/gpu-verification-methodology.md`

### Wann dieser Abschnitt relevant ist

Immer wenn du eine **Hardware-Capability negativ diagnostizierst**:

- GPU-Compute (Vulkan/OpenCL/SYCL) "nicht verfügbar"
- Display-Ausgang "blockiert" oder "deaktiviert"
- PCIe-Gerät "fehlt" (lspci zeigt es nicht)
- Treiber "nicht geladen" (lsmod zeigt ihn nicht)
- Sensor "nicht lesbar" (sensors, nvidia-smi)

### Die 4-Routen-Regel

Bei jeder negativen Hardware-Diagnose: **mindestens 4 unabhängige Routen** prüfen,
bevor du "nicht realisierbar" sagst:

| Route | Tool | Findet |
|---|---|---|
| **User-Space-API** | `vulkaninfo`, `clinfo`, `nvidia-smi` | Was der Treiber exponiert |
| **Explicit ICD/Driver Override** | `VK_ICD_FILENAMES`, `--device` Flags | Was hinter Default-Loader versteckt ist |
| **Sysfs / Kernel-Device-Tree** | `/sys/class/drm/`, `/sys/bus/pci/devices/` | Was der Kernel kennt (unabhängig vom Userspace-Treiber) |
| **Prozess-Topologie** | `lspci`, `ls /dev/dri/`, driver-Links | Was PCIe-ebene existiert |

### Typische Dual-GPU-False-Negatives

| Default-Tool Output | Falsche Schlussfolgerung | Wahrheit nach 4-Routen-Check |
|---|---|---|
| `vulkaninfo` zeigt nur NVIDIA | "Intel hat kein Vulkan" | Intel iGPU hat Mesa-Vulkan-ICD, wird nur vom Loader ausgeblendet |
| `xrandr --listproviders: 0` | "PRIME blockt iGPU" | Wayland hat keine Provider-API; `number: 0` ist normal |
| `glxinfo` zeigt nur NVIDIA | "Intel kann kein OpenGL" | EGL/Mesa-Vulkan existiert parallel |
| Render-Knoten fehlt in `ls /dev/dri/` | "GPU nicht erkannt" | `/sys/class/drm/` hat den Knoten, nur nicht als char-device exponiert |

### Workflow für Dual-GPU Laptop Compute-Verifikation

```
1. Nimm "nicht gefunden" nie als "nicht vorhanden"

2. Default-Tools fragen:
   vulkaninfo | grep deviceName
   xrandr --listproviders
   nvidia-smi

3. Wenn negativ → ICD forcieren:
   VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/intel_icd.json vulkaninfo
   VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json vulkaninfo

4. Sysfs-Kernel-Walk:
   ls /sys/class/drm/card*/device/driver  → PCI-Treiberbindung
   cat /sys/class/drm/card*/device/vendor  → Hersteller-ID
   cat /sys/class/drm/card*/device/device → Device-ID
   ls -la /sys/class/drm/renderD*/device/driver → Render-Knoten-Treiber

5. Prozess-Topologie:
   lspci | grep -iE "vga|3d|display"
   ls /dev/dri/
   cat /proc/bus/pci/devices | grep -i nvidia

6. Finale Aussage erst nach 4-Routen-Prüfung.
```

### Was in Mnemosyne, was in Skill

- **Mnemosyne:** Die konkrete Korrektur ("2026-07-16: iGPU-Split DOCH realisierbar — false negative von default vulkaninfo"). Importance 0.7.
- **Skill (hier):** Die allgemeine Methodik von "nie 'nicht gefunden' = 'nicht vorhanden'" bei Dual-GPU-Diagnosen.
- **Reference (`gpu-verification-methodology.md`):** Vollständige Command-Sequenz mit Copy-Paste-Blöcken, ICD-Pfaden, Sysfs-Topologie von Bastis MEDION ERAZER.

## References

| File | Inhalt |
|------|--------|
| `references/session-analysis-methodology.md` | Vollständige Methodik: 6-Bee-Dispatch UND Single-Agent Deep-Dive (Scroll-by-Bookend-Technik), Output-Format, Such-Patterns, Vermeidungsregeln |
| `references/cross-session-consolidation.md` | Einzel-Agent-Modus: Progressive-Scroll-Strategie, Query-Erfahrungen (2026-07-07), FTS5-Pitfalls, Scroll-Optimierung. **Erweitert 2026-07-07:** Tesseract-PSM, Cuad-Driver-Key-Inkonsistenz, Storage-Bloat, User-Driven-Navigation |
| `references/audit-verification-workflow.md` | **NEU 2026-07-07:** Externe Analyse Verifikation — 6-Phasen-Workflow, Live-Code-Prüfung, Claim-Taxonomie (bestätigt/teils/falsch), Safe-Fix-Katalog, Mnemosyne-Schema für korrigierte Audits, 4 typische Audit-Fehler aus der Praxis |
| `references/batch-feeding-consolidation.md` | 69→25 Dedup-Yield-Strategie, Welle 1→2 Timing, 5×5 Mnemosyne-Batch-Plan, Yield-Optimierung, Final-Report-Template — aus 6-Bee-Schwarm-Daten validiert |
| `templates/deep-dive-lesson-report.md` | Vorlage für strukturierte Deep-Dive-Reports: 5-Felder-Lesson-Format, Summary-Tabelle (Severity), Meta-Lesson-Sektion |
| `references/health-check-testing-methodology.md` | **NEU 2026-07-09:** Cron-Health-Check-Testing — exakte Cron-Replikation, WARNING-Provozierung via DB-Manipulation mit Rollback, alerts.md-Verhalten, Smart-Approval-Pitfalls, Cleanup-Checkliste |
| `references/batch-humanizer-swarm.md` | **NEU 2026-07-13:** Batch-Humanizer-Swarm-Pattern — 16 Dailies in 5 Min über 3 Wellen (6+6+3), Briefing-Template, Queen-Verifikation, Override-Protokoll. 88% bee pass rate, 6x ROI vs sequential |
| `references/subagent-self-test-deception.md` | **NEU 2026-07-13:** Pitfall #36 — Subagent meldet "alle Tests grün" obwohl file violations hat. Zwei Varianten (Tool nicht ausgeführt vs. Test reinterpretiert), Marker-Checkliste für false-green Reports, Queen-Verifikationsmuster |
| `references/write-file-truncation.md` | **NEU 2026-07-14:** write_file silent truncation bei ~1000+ Zeichen — Tool-Constraint statt User-Error. 3 Chunked-Write-Strategien (Append/Python+Heredoc/Chunked-Terminal), Größen-Verifikation als Guard, verwandt mit patch-replace_all-Tripling (Beispiel 4). Entdeckt in Sub-Bee Cross-Verification. |
| `references/mnemosyne-id-resolution.md` | **NEU 2026-07-15:** Mnemosyne-ID-Discovery — `recall` liefert nur Text+Score, braucht `export` für Metadata. `summary_of`-Chain von Episodic→Working auflösen. Schema-Unterschiede, Confidence-Assessment, Python-Cheatsheet. |
| `references/gpu-verification-methodology.md` | **NEU 2026-07-16:** Dual-GPU Compute-Verifikation — korrekte Methodik gegen false negatives von Default-Tools. VK_ICD_FILENAMES-Override, Sysfs-Topologie, PRIME/Wayland-Indikatoren. Lesson #1: "nicht realisierbar" war falsch. Workflow-Template für jeden künftigen GPU-Diagnose-Versuch. |
| `scripts/self-assessment-harvest.py` | Mnemosyne-Harvest-Script für wöchentlichen Review |

## Skill-Curation Hygiene (Drei-Schichten-Konsistenz)

> **Lesson-Hintergrund 2026-07-11:** Wenn `skill-tiers.md` und
> `routing-table.md` in derselben Session geändert werden, ohne dass
> die SKILL.md-YAML-Frontmatter mitgezogen wird, entstehen
> "Tier-Skills die das Team offiziell nicht kennt".

### Three-File-Pflicht-Check

Jede Skill-Curation-Aktion MUSS diese drei Ebenen gleichzeitig prüfen:

```
skill-tiers.md       (Priorisierung — ist es wichtig?)
   ↕ MUSS konsistent sein
routing-table.md     (Persona — wer hat es?)
   ↕ MUSS konsistent sein
SKILL.md (YAML)      (Self-Declaration — kennt der Skill seine Persona?)
```

### Check-Snippet

```bash
grep -oP '`\K[a-z][-a-z]+(?=`)' references/routing-table.md \
  | sort -u \
  | while read skill; do
      found=$(find ~/.hermes/skills -name "SKILL.md" -path "*/$skill/*" 2>/dev/null \
              | grep -v ".archive" | head -1)
      [ -z "$found" ] && echo "❌ $skill: kein SKILL.md" && continue
      grep -q "^agent:" "$found" && echo "✅ $skill" || echo "🚨 $skill: KEIN agent:-Tag"
    done
```

### Trigger-Situationen

- Jede Edit in `skill-tiers.md` → Check sofort.
- Jede Edit in `routing-table.md` → Check sofort.
- Jedes neue `SKILL.md` → Check, dass die Persona-Matrix es kennt.
- Jede Agent-Reorder-Operation → Check alle drei Layer.

### Wenn Drift erkannt

1. **Erst:** Den fehlenden Tag ergänzen (in SKILL.md-YAML), **nicht** die Matrix ändern.
2. **Dann:** Snippet erneut laufen — alle drei Layer ✅.
3. **Schluss:** Mnemosyne-Lesson mit "fixed: <skill-name>" ablegen.

## Was dieser Skill NICHT tut

- ❌ Keine selbstständige Config-Änderung (`~/.hermes/config.yaml`, `.env`).
- ❌ Kein Ändern von Persona-Dateien (`SOUL.md`, `IDENTITY.md`) — Charakter bleibt stabil.
- ❌ Kein Speichern von Secrets in Mnemosyne (Keys/Tokens/Bot-Tokens niemals).
- ❌ Kein automatisches Committen/Pushen/PR-Erstellen ohne Bastis Freigabe.
- ❌ Kein Blindlöschen von Memory-Einträgen — immer invalidieren mit Begründung.

## Beispiele

### Beispiel 1: Build-Fehler (real)

```python
mnemosyne_remember(
    content="""
    ### [2026-07-07] greybel one-line-if bricht Build (40 Vorkommen im Repo)
    - Symptom: "no matching open if block" bei greybel build -dbf
    - Root Cause: greybel 3.7.x kann `if X then Y end if` nicht in einer Zeile parsen
    - Fix: Auf Mehrzeiler expanden: if X then\\n  Y\\nend if
    - Guard: CI-Build-Skript (ci-build.sh) prüft mit Pattern-Match vor Commit
    - Status: verified
    """.strip(),
    importance=0.9,
    source="self-improving",
    veracity="verified",
    metadata={"tags": ["lesson", "greyhack", "build-error", "greybel"], "status": "verified"},
)
```

### Beispiel 2: Workaround entdeckt

```python
mnemosyne_remember(
    content="""
    ### [2026-07-04] Hermes Gateway Restart blockiert via hermes CLI
    - Symptom: `hermes gateway restart` hängt / blocked
    - Root Cause: CLI-Restart-Path deadlockt mit laufenden Gateway-Prozessen
    - Fix: systemctl --user stop hermes-gateway.service && sleep 3 && start
    - Guard: Niemals `hermes gateway restart` nutzen — immer systemctl --user
    - Status: verified
    """.strip(),
    importance=0.9,
    source="self-improving",
    veracity="verified",
    metadata={"tags": ["lesson", "hermes", "gateway", "systemctl"], "status": "verified"},
)
```

### Beispiel 3: Basti korrigiert

```
Basti: "nein, main ist tabu, mach das auf develop"
→ Yuno erkennt: Korrektur → Loop triggert
→ Mnemosyne-Eintrag: "main branch ohne Freigabe → develop/feature verwenden"
→ Status: verified (weil Basti es gesagt hat)
```

### Beispiel 4: `replace_all=true` verursacht Triple-Injection (2026-07-09)

- **Symptom:** Nach `patch(mode='replace', old_string='## Was lief\\\\n\\\\n- \\\\n- ', new_string='...', replace_all=true)` waren **3 identische Kopien** des Inhalts in der Datei — einmal pro leerer Bullet-Liste die gematcht wurde.
- **Root Cause:** `replace_all=true` ersetzt **alle** Vorkommen von `old_string`. Bei 3 leeren Bullet-Listen traf der Match 3× und injectete den Content 3× an verschiedenen Stellen → Datei korrupt (dreifacher Inhalt).
- **Fix:** `write_file` mit vollständigem, korrektem Content → Datei komplett überschrieben (sicherster Weg bei korruptem Zustand).
- **Guard:** `replace_all=true` NIE verwenden, wenn der `old_string` in mehreren Sektionen vorkommen könnte. Stattdessen:
  - **Eindeutigen `old_string`** mit genug Kontext wählen (3+ Zeilen drumrum: die Überschrift, den Absatz drüber, das nächste Element)
  - Bei großer Content-Menge direkt `write_file` nutzen (Überschreibung ist sicherer als Triangulation)
- **Status:** verified

**Zusätzliche Regel:** Bei Datei-Korruption durch Patch-Fehler → **immer `write_file`** (komplette Überschreibung), nie einen zweiten Patch auf korruptem Zustand riskieren. Ein weiterer Patch könnte die Verdopplung noch verstärken.

### Beispiel 5: Tier-Drift-Cross-Check (2026-07-11, aus Skill-Curator-Audit)

- **Symptom:** Nach Build einer `skill-tiers.md` (Tier 1+2 Priorisierung) und Update der `routing-table.md` (Persona-Matrix) zeigten 4 Skills im Inventar keinen `agent:`-Tag im eigenen YAML — obwohl sie in der Matrix korrekt als Yuno getaggt waren.
- **Root Cause:** Der Cross-Reference-Fix (Tier-Table → Routing-Table) hat die **dritte Schicht verpasst**: die SKILL.md-Dateien selbst. Die Matrix ist die Routing-Ebene (`routing-table.md`), der Tier-Table ist die Priorisierungs-Ebene (`skill-tiers.md`), aber die **Skill-Inventar-Ebene** (jedes `SKILL.md` YAML) hat eine eigene `agent:`-Deklaration. Alle drei müssen konsistent sein.
- **Fix:** `grep`-One-Liner für Cross-Reference-Check nach jeder Edit:
  ```bash
  grep -oP '`\K[a-z][-a-z]+(?=`)' references/routing-table.md \
    | sort -u \
    | while read skill; do
        found=$(find ~/.hermes/skills -name "SKILL.md" -path "*/$skill/*" 2>/dev/null | grep -v ".archive" | head -1)
        [ -z "$found" ] && echo "❌ $skill: kein SKILL.md" && continue
        grep -q "^agent:" "$found" && echo "✅ $skill" || echo "🚨 $skill: KEIN agent:-Tag"
      done
  ```
- **Guard:** Jedes Mal wenn `skill-tiers.md` ODER `routing-table.md` editiert wird, MUSS der Cross-Check laufen. Three-File-Check:
  ```
  skill-tiers.md  (was wichtig ist)
  routing-table.md (wer es hat)
  SKILL.md        (ob der Skill selbst seine Persona kennt)
  ```
- **Auswirkung:** 4 von 14 Tier-Skills (`ideation`, `self-improving`, `skill-creator`, `mcp-server-authoring`) ohne eigenen `agent:`-Tag. System funktioniert (Routing liest aus routing-table), aber Future-Agent-Runner bekommt "no agent".
- **Status:** verified (in derselben Session erkannt + dokumentiert + Report in `~/.hermes/docus/audits/skill-curator-2026-07-11-tier-1-2.md`)
- **Kategorie:** workflow
