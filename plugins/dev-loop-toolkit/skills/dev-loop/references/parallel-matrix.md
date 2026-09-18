# parallel-matrix.md — Parallel- vs. Sequential-Regeln

## Die Matrix

| Tätigkeit | Modus | Warum |
|---|---|---|
| Explore/Recon (2–3 Agenten) | **immer parallel** | read-only, keine Kollision möglich |
| BRIEF (read-only) | **immer parallel** | dito — darf mit CI-Watch des Vorgänger-PRs überlappen |
| VERIFY-Lenses (3 Stück) | **immer parallel** | unterschiedliche Blickwinkel, frischer Kontext je Lens; Parallelität ist Teil des Beweises (unabhängige Prüfer) |
| Reviewer-Paare (Correctness + Completeness) | **immer parallel** | superpowers:Two-Reviewer-Regeln |
| CI-Watch (`gh pr checks --watch`) | **Hintergrund-Bash** | blockiert sonst die Session (`run_in_background=true` + `TaskOutput`) |
| Research/Lookups | parallel zu allem Lesenden | — |
| IMPL | **immer sequenziell** im selben Worktree | ein Task = ein Branch = ein PR; parallele Edits am selben Checkout zerstören den Beweis charakter |
| LAND/Merge | **immer sequenziell** | ein PR nach dem anderen; Merges ändern `main`, jede folgende PR-Basis verschiebt sich |
| Meilenstein-Übergänge, Gates | **sequenziell + Mensch** | Gates sind Abnahmepunkte, kein Fließband |
| Baseline-Reparatur | **sequenziell, vor allem anderen** | alles Andere baut auf der Baseline auf |

## Bedingte Parallelität: IMPL-Lanes (max. 2–3)

Voraussetzung **alle**: file-disjoint Issues, getrennte Worktrees, Konflikt-Probe grün,
Baseline-Test pro Lane grün, Single-Writer-Lock hält die Lane-Registrierung.

### Lane-Protokoll

1. **Konflikt-Probe zuerst**: berührte Dateien je Issue schätzen (aus BRIEF), dann
   - überlappungsfrei? → Lanes erlaubt
   - Überschneidung in auch nur einer Datei → **sequenziell** („small but coupled
     tasks still collide" — rmax.ai)
   - harte Probe statt Schätzung: `git merge-tree` zwischen den Lane-Branches oder
     `gh pr files` gegen offene PRs.
2. **Worktree je Lane** (Regeln aus `superpowers:using-git-worktrees`):
   `git worktree add .worktrees/T-9.3 -b wip/T-9.3` — `.worktrees/` muss in
   `.gitignore` stehen; existierende Isolation erkennen (`git rev-parse --git-dir`
   vs. `--common-dir`), nie doppelt isolieren.
3. **Baseline-Test pro Lane verpflichtend**, bevor implementiert wird.
4. **Landing bleibt sequenziell**: Lane A merged → Lane B rebase/merge auf neues main,
   CI erneut, dann Land. Reihenfolge nach Risiko: lowest-risk zuerst (rmax.ai-Muster).
5. **Konflikt beim Landing = Ambiguity-Event**: HALT für den Menschen, nicht
   eigenmächtig resolven. Merge-Konflikte zwischen eigenen Lanes sind ein
   Dekompositionsfehler — Issue-Split im agent-log zur späteren besseren Zerlegung
   notieren (plan-dev-loop lernt daraus).

### Beleg-Lage (warum so strikt)

- arXiv 2607.04697 (33.596 Agenten-PRs): ~20 % textuelle Konflikte selbst wenn
  derselbe Agent beide PRs stellt; ~42 % davon strukturell (Agenten sind sich nicht
  einig, ob eine Datei existieren soll); 84 % der Konflikt-Dateien sind Quellcode.
- Anthropic Multi-Agent-Research: 3–5 parallele Subagents sind das Sweet Spot für
  Research; Over-Delegation (50 Subagents) und endloses Suchen sind die beobachteten
  Failure-Modes → Lanes deckeln, BRIEFs begrenzen.
- Token-Ökonomie: Multi-Agent kostet ~15× Chat-Tokens — Parallelität nur, wenn der
  Task-Wert es trägt (`task-weight-routing`).

## Anti-Muster

- „Noch eine Lane ist fast frei" → über 3 Lanes steigen Konflikt-Wahrscheinlichkeit
  und Landing-Warteschlange schneller als der Durchsatz.
- IMPL parallel zum LAND desselben Issues („während CI läuft, schon mal anfangen") —
  nie: der Fix-nach-CI-rot-Pfad braucht denselben Branch-Kontext.
- VERIFY-Lenses hintereinander statt parallel — verlieren ihre Unabhängigkeit nicht,
  aber die Zeitersparnis und das „unabhängige Prüfer"-Argument.
