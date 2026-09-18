# loop-phases.md — Detail-Protokoll der Loop-Phasen

Jede Phase: Input → Schritte → Output → HALT-Bedingungen. Ausführende Lane in Klammern.

## BASELINE (Session-Start, Main-Agent)

Input: Repo-Root, WORKFLOW.md/AGENTS.md mit benanntem Verify-Befehl.

1. `git pull --ff-only` — schlägt das fehl (divergiert), HALT: Mensch entscheiden lassen.
2. `git status` — Working Tree muss clean sein. Dirty → HALT mit Ausgabe; nichts stashen
   oder wegwerfen ohne Rückfrage.
3. Repo-Verify im Baseline-Modus ausführen (pokerogue-Muster: `verify.py --baseline
   --host-only`; generisch: den in WORKFLOW.md dokumentierten Befehl). Exit != 0 →
   **Baseline-Reparatur** als eigener Mini-Loop: `fix/<thema>`-Branch, jüngste
   Ursache zuerst, danach Baseline erneut. Gelingt sie nicht in 5 Iterationen →
   `blocked:`-Issue, Session-Ende.
4. Baseline-SHAs notieren (für den agent-log): `git rev-parse HEAD`, Verify-Zusammenfassung.

Output: grüne Baseline + SHAs. HALT: divergiertes main, dirty tree, rot nach 5 Versuchen.

## GATE-CHECK (Main-Agent, via frontier.sh)

`frontier.sh` (unter `${CLAUDE_PLUGIN_ROOT}/scripts/`) meldet Gate-Blocker: offene
Issues mit `gate:`-Präfix/Label im aktuellen
oder Vor-Milestone. Gate gilt als bestanden, wenn ein Mensch den literalen
Approval-Kommentar geschrieben hat („G-A approved“, „G7 approved“ — Konvention im
Gate-Issue nachlesen und exakt verwenden).

HALT-Ausgabe an den Menschen: Gate-Issue-Nummer, was bewiesen wurde (Evidenz-Links),
welcher Approval-Text erwartet wird. **Der Loop generiert den Approval-Kommentar nie selbst.**

## FRONTIER (Main-Agent, via frontier.sh)

Output des Scripts: sortierte Liste `issue | titel | blocker(dep-edges offen) | gate?`.

- Nimm das erste nicht blockierte Issue. Abweichungen von der Nummern-Reihenfolge nur
  mit dokumentiertem Grund im agent-log (pokerogue-Präzedenz: T-9.5 vor T-9.4, begründet).
- `blocked:`-Issues: überspringen, im agent-log sammeln.
- `idea:`-Issues gehören nie in die Frontier (Scope-Creep-Bremse).

## BRIEF (Explore-Lane, read-only, parallel zur CI-Watch-Phase des Vorgängers möglich)

Input: Issue-Nummer N.

1. `gh issue view N --comments` + Body lesen.
2. Governance-Docs lesen: AGENTS.md, WORKFLOW.md, DECISIONS.md **rückwärts** (jüngste
   Entscheidung zuerst), docs/TASKS.md-Abschnitt, PROGRESS.md-letzte Blöcke.
3. Berührte Dateien/Module per Grep/Glob identifizieren (read-only).
4. Brief erzeugen (Output-Format):

```
## Brief T-x.y (#N)
Ziel: <ein Satz>
Akzeptanz (jedes Kriterium = exakt ausführbarer Befehl):
  1. `python3 tools/verify.py --host-only` → Exit 0
  2. `python3 tools/parity_report.py` → 0 unerklärte Abweichungen
  3. …
Risiken: <Liste, je mit Gegenprobe>
Entscheidungen offen: <keine | Frage + Optionen>
```

HALT: `Entscheidungen offen` nicht leer → AskUserQuestion mit Optionen + Empfehlung;
Antwort im PR-Body dokumentieren („Entscheidung: Option A — <wer>, <Datum>").

## IMPL (Worker-Lane)

1. `git checkout -b wip/<task-id>` (existiert der Branch: fortsetzen, nie neu anlegen).
   Repo mit etabliertem `.worktrees/` → Worktree (siehe parallel-matrix.md).
2. Implementieren **nur** dieses Issues. Docs-only-Anteile (PROGRESS.md-Block) in
   denselben Commit.
3. Verify ausführen (Vollmodus inkl. Lint/Format). Rot → Report lesen
   (`out/verify_report.md` o. Ä.), **genau eine** Hypothese aufschreiben, minimal
   beheben, erneut. Zähler eins pro Iteration, max. 5.
4. Lokale CI-Parität: Format/Lint exakt in der CI-Version laufen lassen (Verify ohne
   Lint-Schritt ist eine bekannte Fake-Grün-Falle — siehe edge-cases.md #9).
5. Commit(s): `type(scope): beschreibung [T-x.y]` bzw. Repo-Konvention.
   `gov:`-Commits (Regelwerk/Scope) brauchen einen DECISIONS.md-Eintrag **im selben
   Commit** — sonst ist die Änderung für die nächste Session unsichtbar.

Output: grüner Verify + Commit(s) + Iterationsprotokoll (für PR-Body).
HALT: 5 Iterationen rot → `blocked:`-Issue anlegen (mit Fehlerliste), agent-log, nächstes Issue.

## VERIFY (Heavy-Lane, 3 parallel)

Drei Lenses mit unterschiedlichem Blickwinkel dispatchen, z. B.:
- Lens A: Spez-Compliance — jedes Akzeptanzkriterium aus dem Brief gegen Diff/Tests prüfen
- Lens B: Korrektheit — Logik, Edge Cases, Nebeneffekte außerhalb des Scopes
- Lens C: Beweisqualität — täuschen die Beweise? (Tests, die nichts testen; Reports,
  die übersprungene Schritte verschleiern)

Prompt-Kern (pokerogue-Kanon): „Du bist ein adversarialer Prüfer, nicht der Autor.
Deine Aufgabe ist es, den Task zu WIDERLEGEN. Liefere: WIDERLEGT/WIDERLEGT_NICHT +
Befund je Akzeptanzkriterium."

Bestanden: ≥2 Lenses geantwortet UND <2 `WIDERLEGT`. Sonst: Widerlegungen an IMPL
zurückgeben (zählt in dessen Iterationszähler).

## LAND (Main-Agent)

1. PR-Body-Datei schreiben (Evidenz-Doc):

```markdown
## T-x.y <Titel> (#N)

Closes #N

| Akzeptanzkriterium | Beweis (Befehl → Ergebnis) |
|---|---|
| verify grün | `tools/verify.py --host-only` → Exit 0 (300 Cases / 45.020 Assertions) |
| … | … |

Iterationen: <n>/5 · Verify: <Zahlen> · Abweichungen vom Plan: <honest, auch „keine">
Entscheidungen: <falls BRIEF-HALT beantwortet wurde>
```

2. `git push -u origin wip/<task-id>`
3. `gh pr create --title "T-x.y <Titel> (#N)" --body-file <datei> --milestone "<M>" --base main`
4. Merge-Modus: `${CLAUDE_PLUGIN_ROOT}/scripts/merge-probe.sh <owner/repo> main`
   - `native-auto` → `gh pr merge <PR> --squash --auto --delete-branch` (GitHub/Merge-Queue
     entscheidet)
   - `agent-side` → `gh pr checks <PR> --watch` (Hintergrund-Bash) und danach
     `gh pr merge <PR> --squash --delete-branch`
5. Branch-Weg verifizieren: `git ls-remote --heads origin wip/<task-id>` muss leer sein.
   Nicht leer → einmalig manuell löschen melden (gh-Bug cli#9073).
6. CI rot nach PR-Open: Fix als **weiterer Commit auf demselben Branch** + push; kein
   neuer PR. CI rot nach Merge (selten, merge-queue-loos): `git revert --no-edit` auf
   main, Issue zurück in Frontier, Ursache als eigenes Issue.

## LOG (Main-Agent)

1. Progress-Doku: PROGRESS.md-Session-Block (Done/NEXT/Verify-Zahlen) — als Folge-PR
   (`docs(progress)`) oder direkt-commit je Repo-Konvention; pokerogue-Muster ist der
   Folge-PR.
2. `agent-log`-Kommentar (laufendes Status-Issue):

```
## Session <Datum> — Milestone <M>
Baseline: <SHA> · Verify: <Zahlen>
Done: T-x.y (#PR), …
NEXT: T-x'.y' (#N') · Offen: <Abnahme-Issues, Gates>
```

3. Issue-Close **mit Evidenz-Kommentar** vorher: Beweis-Zitate, CI-Link. Dann
   `gh issue close N --reason completed`. Ausnahme Abnahme-Issues: offen lassen,
   im agent-log „Implementation fertig, Abnahme ausstehend" vermerken.
4. `loop-state.sh` aktualisieren (Phase → next).
