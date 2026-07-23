# Session-Analyse-Methodik — Proaktiver Lessons-Scan

> **Zweck:** Definierte Methodik, um proaktiv Lektionen aus vergangenen Sessions
> zu extrahieren — ohne auf einen konkreten Fehler zu warten.
> **Erstmalig eingesetzt:** 2026-07-07 (6-Bee-Schwarm über 9 Sessions, 7 Tage)

## Wann

- **Wöchentlich** via Cronjob (Hypothesen-Review)
- **Auf Anforderung** — Basti sagt "geh die letzten Sessions durch"
- **Konkrete Session-Analyse** — Basti sagt "analysiere Session X" (Single-Agent Deep-Dive)
- **Nach Projekt-Meilenstein** — GreyHack-Release, Build-CI-Grün, Refactor
- **NICHT** bei kontinuierlicher Arbeit (Skills-update läuft über den 5-Step-Loop)

## Methodik-Wahl: Multi-Agent (Schwarm) vs Single-Agent (Deep-Dive)

| Aspekt | 6-Bee Schwarm (Multi-Agent) | Single-Agent Deep-Dive |
|--------|----------------------------|------------------------|
| **Ziel** | 5–15 Sessions in ≤7 Tagen scannen | 1 Session Tiefenanalyse |
| **Agenten** | 5–6 Delegates + Königin | Du selbst |
| **Dauer** | ~20-30 Min (parallel) | ~5-10 Min (sequentiell) |
| **Token-Kosten** | Mittel (viele kleine Briefings) | Mittel (wenige große Scrolls) |
| **Setup** | `delegate_task`-Briefings schreiben | Direkt loslegen |
| **Ergebnis** | Breiter Scan, viele Lessons über Domänen | Tiefe Analyse einer Session, Meta-Lessons |
| **Wann** | Wöchentlicher Review, nach Meilenstein | Konkrete Analyse-Anfrage von Basti |

## Ablauf — Multi-Agent (6-Bee-Schwarm, 2 Wellen)

### Phase 0: Session-Discovery

```python
# Drei Suchdurchläufe mit unterschiedlichen Queries:
session_search(query="fehler error fail broken workaround fix kaputt bug", limit=10, sort="newest")
session_search(query="correction \"das war falsch\" \"mach anders\"", limit=10, sort="newest")
session_search(query="workaround quirk edge case", limit=10, sort="newest")
```

**Erwartung:** 5–15 Sessions (Multi-Agent) oder 1 Session (Single-Agent).

### Phase 1 (Single-Agent): Deep-Dive in eine Session

**Wann:** Basti sagt "analysiere Session <id>" — kein Schwarm nötig.

**Scroll-by-Bookend-Technik (zuverlässig):**

Der Discovery-Response enthält `bookend_start` (= erste 3 Messages der Session). Extrahiere daraus die message_ids für den ersten Scroll — **nicht** die `match_message_id`.

**⚠️ Pitfall: `session_search(scroll)` kann mit "message_id not in session" fehlschlagen.**

Grund: FTS5 findet die Session, aber die `match_message_id` zeigt auf eine Message AUSSERHALB des scrollbaren Fensters (Session > ~200 Messages). **Fix:** Nutze die message_ids aus `bookend_start` — die sind GARANTIERT im Fenster.

```python
# Schritt 1: Discovery — finde Session
result = session_search(query="<session-title-begriff>", limit=3, sort="newest")

# Schritt 2: Scroll INS Fenster — nutze bookend_start message IDs
anchor = result[0].bookend_start[1].id   # erste assistant message
# Alternativ: result[0].bookend_start[0].id (user message)
data = session_search(session_id=result[0].session_id,
                      around_message_id=anchor, window=20)

# Schritt 3: Vorwärts scrollen
while data.messages and data.messages_after == 20:
    last_msg = data.messages[-1]
    data = session_search(session_id=result[0].session_id,
                          around_message_id=last_msg.id, window=20)
    # Sammle Findings aus jeder Seite
```

**Der "30-Sekunden-Check":** Wenn nach 3 Scrolls (~30s) noch keine Struktur erkennbar:
- Session ist zu groß/diffus → aufgeben
- Nur bookend_start + bookend_end lesen (Goal + Resolution)
- Mit dem zusammenfassen, was sichtbar ist → abbrechen

**Findings sammeln:**

```markdown
### [YYYY-MM-DD] <Lesson-Titel>
- Symptom: <was sichtbar war>
- Root Cause: <die eigentliche Ursache>
- Fix: <der konkrete Befehl / die Änderung>
- Guard: <wie künftig vermieden>
- Status: verified | hypothese
- Kategorie: <tool-quirk | build-error | workflow | orchestration | hardware>
```

Ausführlicheres Template mit Summary-Tabelle: siehe `templates/deep-dive-lesson-report.md`.

**Cross-Session Verify (Pflicht):**

Nach allen Findings: `session_search(query="<lesson-keyword>")` — prüft ob derselbe Fehler schon in ANDEREN Sessions vorkam:
- 1×: Mnemosyne-Lesson (bleibt lokal)
- 2×: Skill-Update prüfen (Promote-Schwelle)
- 3×+: **Skill-Update ZWINGEND** (3×-Regel)

**Dokumentation speichern:**

Optional: Findings als vollständige Markdown-Datei ablegen:
```
~/docs/system/<session-date>-<kurztitel>-self-improving.md
```
- Enthält ALLE Lessons + Summary-Tabelle + Meta-Lesson
- Referenz für spätere Sessions, ohne die ganze Session scrollen zu müssen
- Beispiel: `maxclaw-session-2026-07-04-self-improving.md` (13 Lessons, 15 KB)

### Phase 1 (Multi-Agent): Welle 1 — Die 3 ergiebigsten Sessions

Wähle die 3 Sessions mit den meisten Match-Snippets. Dispatche je 1 Biene:

**Briefing-Struktur pro Biene:**

```
Kontext: <2-3 Sätze Session-Kontext, was passiert ist, was relevant ist>
Goal: Analysiere die Session <session_id>. Extrahiere ALLE Fehlschläge,
Workarounds, Syntax-Bugs und Korrekturen im self-improving Format.
Start bei session_search(session_id=..., around_message_id=..., window=20)
als Startpunkt und scrolle vor/zurück wie nötig.
Suche besonders nach: <spezifische Patterns, die in der Session vorkamen>

Output-Format pro Fund:

### [DATUM] <Kurztitel>
- Symptom: ...
- Root Cause: ...
- Fix: ...
- Guard: ...
- Status: verified | hypothese
- Kategorie: tool-quirk | build-error | workflow | orchestration | hardware
```

### Phase 2: Welle 2 — Die restlichen Sessions

Dispatche 2–3 Bienen für die verbleibenden Sessions (kann zusammengefasst werden).

### Phase 3: Königinnen-Konsolidierung

Wenn alle Bienen zurück sind:

1. **Deduplizieren** — Gleicher Root Cause, ähnliches Symptom → zusammenführen
2. **Priorisieren** — Verified > Hypothese, High-Importance > Low
3. **Mnemosyne füttern** — Jede Lesson als `mnemosyne_remember` mit:
   - `importance=0.7–0.9` (verified) oder `0.3–0.5` (hypothese)
   - `veracity="verified"` oder `"inferred"`
   - `metadata.tags` mit Domäne + Kategorie
4. **Skill-Promote prüfen** — Taucht Pattern 3×+ auf? → In passenden Skill patchen

### Phase 4: Basti-Report

Kurzer Report mit:
- 🐝 Wieviele Bienen waren im Einsatz
- 📊 Wieviele Lessons extrahiert (verified vs hypothese)
- 🔥 Top-3 wichtigste Lessons
- ⚡ Was wurde automatisch gefördert (Skills gepatcht)
- ❓ Hypothese-Punkte zum Review

## Output-Format-Spezifikation

Jeder Fund MUSS folgendes Schema haben — das ist das Minimalformat,
das Mnemosyne versteht und der Hypothesis-Review-Cronjob verarbeiten kann:

```markdown
### [YYYY-MM-DD] <Eindeutiger Kurztitel>
- Symptom: <was sichtbar war, max 2 Sätze>
- Root Cause: <die eigentliche Ursache, max 2 Sätze>
- Fix: <der konkrete Befehl / die Änderung, max 2 Sätze>
- Guard: <wie künftig vermieden, max 2 Sätze>
- Status: verified | hypothese
- Kategorie: <eine aus: tool-quirk | build-error | workflow | orchestration | hardware>
```

**Status-Regeln:**
- `verified` — Fix wurde getestet, CI grün, Basti hat bestätigt
- `hypothese` — Logik stimmt, aber nicht im Live-System getestet

## Was zu suchen ist (Checkliste)

| # | Pattern-Signal | Beispiel |
|---|---|---|
| 1 | **Build-Error** (Compiler failt) | `greybel build -u bricht bei Inline-if` |
| 2 | **Tool-Quirk** (Tool verhält sich unerwartet) | `hermes config set persistiert nicht beim 1. Mal` |
| 3 | **Workflow-Fail** (Ansatz funktioniert nicht) | `Copy-Paste von 444 Links überfordert User` |
| 4 | **Basti-Korrektur** (User sagt "nein, anders") | `"main branch tabu — develop/feature verwenden"` |
| 5 | **Race-Condition** (Timing-Problem) | `Parallel writes auf Config führen zu inkonsistentem Zustand` |
| 6 | **Orchestrierungs-Fail** (Subagent-Problem) | `Subagent halluziniert Modell-Provider-Response` |
| 7 | **Hardware-Limit** (Physik schlägt Software) | `PCIe x8 statt x16, kein Workaround` |

## Vermeidungs-Regeln

- ❌ **Keine Environment-dependent failures** — fehlende Binaries, frische Install-Errors
- ❌ **Keine transienten Fehler** — retry hat geholfen? Dann ist retry die Lesson
- ❌ **Keine negativen Tool-Claims** — nicht "X tool does not work", sondern "Fix: <Install-Befehl/Config-Step>"
- ❌ **Keine One-off Task Narrative** — "PR #42 analysiert" ist kein Skill
