---
name: dev-loop
version: 0.1.0
author: Basti
license: MIT
description: "Use when ein GitHub-Milestone autonom abgearbeitet werden soll („fahr dev-loop fort“, „arbeite Milestone M9 ab“, „continue the milestone loop“, „nächstes Issue bitte“) — Issues → Branch → PR → CI → Squash-Merge → Evidenz-Close, Issue für Issue. NOT for Einzel-PR-Aufträge mit eigenem Briefing (pr-ship-pattern), Kanban-Dispatch ohne GitHub (kanban-orchestrator), reines Issue-Triage (github-issues) oder Planung neuer Milestones (plan-dev-loop)."
metadata:
  hermes:
    tags: [github, automation, dev-loop, milestones, pull-requests, loop]
    related_skills: [github-pr-workflow, github-issues, github-pr-merge-readiness, classify-test-failures, pr-ship-pattern, task-weight-routing, worker-failure-discipline, plan-dev-loop, harness-bootstrap, azahar-harness]
---

# dev-loop — autonomer GitHub-Milestone-Loop

Ein Milestone wird Issue für Issue abgearbeitet. Jedes Issue durchläuft
BRIEF → IMPL → VERIFY → LAND → LOG. Der Loop stoppt deterministisch an
Gates, offenen Entscheidungen und roter Baseline — niemals durch Rätselraten.

Generalisiert aus dem pokerogue-3ds-Kanon (WORKFLOW.md/AGENTS.md, Sep. 2026).
Das Ziel-Repo braucht Governance-Grundausstattung — wenn fehlend, zuerst
`harness-bootstrap` ausführen.

Script-Aufrufe: `${CLAUDE_PLUGIN_ROOT}/scripts/<name>.sh` (installiertes Plugin;
im lokalen Checkout `plugins/dev-loop-toolkit/scripts/<name>.sh`).

```
BASELINE ──► GATE offen? ──ja──► HALT (Approval-Kommentar abwarten)
   │              nein
   ▼
FRONTIER (nächstes freies Issue, Dep-Edges respektieren)
   │
   ├─► BRIEF   (read-only: Akzeptanz = ausführbare Befehle)
   ├─► IMPL    (wip/<task-id>, max. 5 Iterationen, 1 Hypothese/Runde)
   ├─► VERIFY  (3 adversariale Lenses parallel)
   ├─► LAND    (PR + CI-Watch + Squash-Merge — Modus per merge-probe)
   └─► LOG     (Progress-Doc, agent-log-Kommentar, Evidenz-Close)
   │
   └──► nächstes Issue … Milestone leer ──► GATE anlegen/anhalten
```

## Phasen-Kurzfassung

Jede Phase hat ein Detail-Protokoll: → `references/loop-phases.md`.

1. **BASELINE** (Session-Start, Pflicht): `git pull --ff-only`; Working Tree muss clean
   sein; Repo-Verify-Befehl (aus WORKFLOW.md/AGENTS.md) im Baseline-Modus muss grün sein.
   Rot → **erst Baseline reparieren, nie auf Rot bauen.** Der Loop endet hier, nicht
   "später irgendwann".
2. **GATE-CHECK**: Gibt es im (Vor-)Milestone ein offenes `gate:`-Issue ohne
   Approval-Kommentar („G-X approved“ o. ä., vom Menschen)? → HALT. Der Loop beginnt den
   Folge-Milestone nicht ohne Approval. Gate-Erkennung übernimmt
   `${CLAUDE_PLUGIN_ROOT}/scripts/frontier.sh`.
3. **FRONTIER**: `${CLAUDE_PLUGIN_ROOT}/scripts/frontier.sh <owner/repo> <milestone>` liefert die offenen
   Issues sortiert nach Dep-Edges (`Depends-on: #N` / „Setzt #N voraus" im Issue-Body).
   Nimm das erste freie. `blocked:`-Issues überspringen und melden. **Mit dem letzten
   agent-log-Block abgleichen**: Issues, die dort als „Abnahme ausstehend" geführt
   werden, sind implementiert und warten auf den Menschen — überspringen, nicht
   erneut bauen (der Marker `Abnahme: Mensch` im Issue-Body automatisiert das für
   neue Repos; frontier.sh weist sie als `[abnah]` aus).
4. **BRIEF** (read-only Subagent, Explore-Lane): Issue + Kommentare + Governance-Docs
   (DECISIONS rückwärts lesen!) → Brief mit Akzeptanzkriterien als **exakt ausführbare
   Befehle**, Risiken, `decision_pending`-Flag. Offene Entscheidung → HALT mit Frage an
   den Menschen; die beantwortete Entscheidung später im PR-Body dokumentieren.
5. **IMPL**: Branch `wip/<task-id>` (Worktree, wenn `.worktrees/` etabliert — Lane-Regeln
   unten), nur dieses eine Issue implementieren, Verify Exit 0, lokale CI-Parität
   (Format/Lint exakt wie CI), Progress-Block im selben Commit, Commit-Konvention
   `type(scope): beschreibung [T-x.y]` (oder Repo-Konvention aus WORKFLOW.md). Rot:
   Verify-Report lesen, **eine** Hypothese pro Iteration, max. 5, dann `blocked:`.
   Nach 3 fehlgeschlagenen Fixes am selben Fehler: `superpowers:systematic-debugging`.
6. **VERIFY**: 3 adversariale Lenses **parallel** dispatchen („Du bist ein adversarialer
   Prüfer, nicht der Autor — deine Aufgabe ist es, den Task zu WIDERLEGEN"). Bestanden
   iff ≥2 Lenses geantwortet haben UND <2 widerlegt haben. Sonst zurück in IMPL mit den
   Widerlegungen als Input.
7. **LAND**: `git push -u origin wip/<task-id>` → `gh pr create` mit
   Evidenz-Body (Akzeptanz-Tabelle mit Beweis je Kriterium + `Closes #NN`) und
   `--milestone` → CI-Watch → Merge. Exakte gh-Befehle: → `references/gh-recipes.md`.
   **Merge-Modus per `${CLAUDE_PLUGIN_ROOT}/scripts/merge-probe.sh`:**
   Protection aktiv → `gh pr merge --squash --auto --delete-branch`; sonst (403/404 —
   privates Free-Repo) → agentenseitig `gh pr checks --watch` +
   `gh pr merge --squash --delete-branch`. Branch-Weg via `git ls-remote` verifizieren
   (Workaround für gh-Bug cli#9073). CI rot → Fix als **weiterer Commit auf demselben
   Branch**, nie ein neuer PR.
8. **LOG**: Progress-Doku (PROGRESS.md-Block o. Ä.) als Folge-Commit/-PR landen;
   `agent-log`-Kommentar (Baseline-SHAs, Done mit PR-Nummern, Verify-Zahlen, NEXT);
   Issue schließen **nur mit Evidenz** („kein ‚erledigt' ohne Nachweis": Checksummen,
   Testzahlen, CI-Link). Abnahme-kritische Issues (Mensch-Abnahme) offen lassen und im
   agent-log als „Implementation fertig, Abnahme ausstehend" führen.

## Parallel vs. Sequential (Kurzfassung)

Vollständige Matrix + Lane-Protokoll: → `references/parallel-matrix.md`.

| Immer parallel | Immer sequenziell | Bedingt (max. 2–3 Lanes) |
|---|---|---|
| Explore/Recon, BRIEF (read-only) | IMPL im selben Worktree | file-disjoint Issues in getrennten Worktrees |
| 3 VERIFY-Lenses, Reviewer-Paare | LAND/Merge — ein PR nach dem anderen | nur nach Konflikt-Probe (Dateiüberlappung) |
| CI-Watch als Hintergrund-Bash | Meilenstein-Übergänge, Gates, Baseline-Reparatur | Baseline-Test pro Lane verpflichtend |

Beleg: ~20 % textuelle Konflikte selbst bei same-agent-PRs (arXiv 2607.04697) —
Parallelität ist ein Werkzeug, kein Default.

## ZCode-Tool-Map

| Aktion | Tool |
|---|---|
| Loop-Ledger | `TodoWrite` — eine Task pro Phase des aktuellen Issues |
| BRIEF | `Agent(subagent_type="Explore")` — read-only, billig |
| VERIFY | 3 × `Agent(subagent_type="code-reviewer")` **in einer Nachricht** (parallel) |
| CI-Watch | `Bash("gh pr checks --watch …", run_in_background=true)` + `TaskOutput` |
| Model-Lanes | BRIEF/Recon → Worker-Tier (Flash); VERIFY/Gates → Heavy-Tier (GLM-5.3) |
| State | `${CLAUDE_PLUGIN_ROOT}/scripts/loop-state.sh` bei jedem Phasenwechsel |
| Unbeaufsichtigter Anstoß (optional) | `CronCreate`/`OffPeakCreate` mit Prompt „fahr dev-loop im Repo X fort — Respektiere Gates und Single-Writer-Lock" |

## Halte-Regeln (deterministische HALTs)

- Rote Baseline → reparieren oder Session beenden (nie weiterbauen)
- Offenes `gate:` ohne Approval → HALT; Milestone-Übergang wartet
- `decision_pending` im BRIEF → HALT mit konkreter Frage + Optionen
- 5 IMPL-Iterationen ohne Grün → `blocked:`-Issue + agent-log, nächstes Issue
- VERIFY widerlegt 2× → zurück in IMPL (zählt gegen die 5)
- `.dev-loop/lock` hält fremde session-id (jünger als 6 h) → HALT mit Hinweis auf die fremde Session

## Edge Cases

Die 15 wichtigsten mit Detektion + Reaktion: → `references/edge-cases.md`
(Plan-Mode-Write-Block, Branch-Protection-403, Fake-Grün, tote Vorwärtsverweise,
Doc-Drift, CI≠lokal, Context-Verlust/Resume, …).

## State & Resume

Schema + Lock-Protokoll: → `references/state-contract.md`. Kurz: `.dev-loop/state.json`
(Repo, untracked/gitignored) hält aktuelles Issue, Phase, Iterationszähler, letzte
Evidenz. Nach Sessionverlust: State lesen, agent-log lesen, Phase fortsetzen statt
neu beginnen.

## Routing zu Bestehendem (kein Duplikat)

| Bedarf | Skill |
|---|---|
| Einzelner PR mit eigenem Briefing | `pr-ship-pattern` |
| PR/Issue-Mechanik im Detail | `github-pr-workflow`, `github-issues`, `github-pr-merge-readiness` |
| CI-Failure-Klassifikation | `classify-test-failures` |
| Worker-Output-Verifikation | `worker-failure-discipline` |
| Root-Cause nach Fix-Serie | `superpowers:systematic-debugging` |
| Worktree-Lanes | `superpowers:using-git-worktrees` |
| Neuer Milestone/Plan | `plan-dev-loop` (Plan-Mode) |
| Repo ohne Governance-Canon | `harness-bootstrap` |
| Emulator-/Orakel-Verifikation (3DS-Homebrew) | `azahar-harness` |

## Es läuft gut, wenn

- Kein Commit/PR/Issue-Close ohne zitierten Beweis (Befehl + Exit-Code + Zahlen) passiert ist
- Jeder HALT mit einer konkreten, beantwortbaren Frage beim Menschen gelandet ist
- `main` am Sessionende grün, gemergte `wip/*`-Branches weg, agent-log aktuell ist
- Der State-File-Inhalt mit dem agent-log übereinstimmt (nächste Session kann fortsetzen)
