# governance-templates.md — Skelette für die Grundausstattung

Minimalausstattung, an pokerogue-3ds angelehnt, auf das Nötigste gekürzt.
Bestehendes im Zielrepo hat immer Vorrang — diese Skelette füllen nur Lücken.

## WORKFLOW.md (Kernstück)

```markdown
# WORKFLOW.md — Entwicklungs-Workflow (bindend für Mensch und Agent)

## Branch-Modell
| Branch | Zweck | Wer schreibt |
|---|---|---|
| main | stabil, Verify grün — nur über PR | Agent (über PR), Mensch |
| wip/<task-id> | ein Task = ein Branch = ein PR | Agent |
Kein Direkt-Commit auf main. wip/* wird nach Merge gelöscht.

## PR-Flow
git push -u origin wip/<id> &&
gh pr create --title "T-x.y <Titel> (#NN)" --body-file <evidenz> --milestone "<M>" &&
gh pr checks --watch &&
gh pr merge --squash --delete-branch        # Merge-Modus: <merge-probe-Ergebnis + Datum + Grund>

## Verify-Loop
- Baseline (Session-Start): `<BEFEHL --baseline-Variante>`
- Nach Implementierung: `<BEFEHL>` → Exit 0, sonst Fix-Loop (max. 5, 1 Hypothese/Runde)
- Format/Lint lokal vor jedem Push: `<BEFEHL>`

## Commit-Konventionen
type(scope): beschreibung [T-x.y] — feat/fix/refactor/test/docs/chore/gov
gov: braucht DECISIONS.md-Eintrag im selben Commit. Ein Task = ein Commit+.

## Issue-Konventionen
agent = abarbeitbar · gate = Gate-Review (Approval-Kommentar) · idea = geparkt ·
blocked = eskaliert · agent-log-Issue #<NR> = Session-Protokoll

## Gates
Ohne Approval-Kommentar („G-n approved") beginnt der Agent den Folge-Meilenstein nicht.
```

## AGENTS.md (Ergänzung, falls noch nicht vorhanden)

```markdown
# AGENTS.md
## Regeln für Agenten
1. Nie auf roter Baseline weiterbauen; Verify Exit 0 vor jedem Commit.
2. Evidenz-Pflicht: kein „erledigt" ohne zitierten Beweis (Befehl + Exit-Code + Zahlen).
3. Implementiert ≠ abgenommen: Abnahme-Issues bleiben offen für den Menschen.
4. Scope-Creep → idea:-Issue, nie einbauen.
5. Nach 3 fehlgeschlagenen Fixes: Root-Cause-Analyse statt Symptom-Patch.
6. Eskalation: blocked:-Issue + agent-log, nächster Task.
## Loop
dev-loop-Skill (dev-loop-toolkit-Plugin); Phasen und State: siehe WORKFLOW.md.
```

## DECISIONS.md

```markdown
# DECISIONS.md — Entscheidungs-Log (append-only, rückwärts lesen)
## D-1 — <Titel> (2026-09-17)
<Was wurde entschieden, warum, wem es widerspricht. gov:-Commits tragen die Nummer.>
```

## PROGRESS.md / HANDOFF.md

```markdown
# PROGRESS.md
## Session 2026-09-17
Baseline: <SHA> · Verify: <Zahlen>
Done: T-x.y (#PR) · Next: T-x'.y' (#N) · Blocked: —

# HANDOFF.md
Checkliste Session-Wechsel: main sauber? agent-log aktuell? State-File konsistent?
offene HALTs notiert?
```

## GitHub-Anlage-Skript (vom Skill ausführen)

```bash
R=OWNER/REPO
gh label create -R "$R" agent -d "autonom abarbeitbarer Task" 2>/dev/null || true
gh label create -R "$R" gate  -d "Gate-Review, Approval-Kommentar des Menschen" 2>/dev/null || true
gh label create -R "$R" idea  -d "geparkte Scope-Idee" 2>/dev/null || true
gh label create -R "$R" blocked -d "eskaliert nach 5 Iterationen" 2>/dev/null || true
gh issue create -R "$R" --title "agent-log — Laufendes Session-Protokoll" \
  --body "Ein Kommentar je Session: Baseline/Done/NEXT/Blocked." --label agent
for e in '.dev-loop/' '.worktrees/'; do
  grep -qxF "$e" .gitignore 2>/dev/null || echo "$e" >> .gitignore
done
```

## merge-probe-Dokumentationszeile (in WORKFLOW.md)

```
Merge-Modus: agent-side — Branch-Protection-API HTTP 403 (Free-Plan, privat), live geprüft <Datum>.
Bitte nicht erneut danach suchen.
```
(oder `native-auto — Protection aktiv, gh pr merge --auto erlaubt`, je Probe-Ergebnis)
