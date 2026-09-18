# dev-loop-toolkit

Der autonome GitHub-Dev-Loop als Plugin: **Milestone → Issues → PRs → Squash-Merge**, mit
Mensch-Gates, adversarialer Verifikation und Evidenz-Pflicht beim Issue-Close. Generalisiert
aus dem `pokerogue-3ds`-Workflow (Basti/Toqsick, Sep. 2026: 19 gemergte PRs in 44 h, alle
squash-gemergt, Issues nur mit Beweisen geschlossen).

## Skills

| Skill | Zweck |
|---|---|
| `dev-loop` | Autonomer Ausführungs-Loop: Baseline-Gate → Frontier → BRIEF → IMPL → VERIFY (3 adversariale Lenses) → LAND (PR + CI-Watch + Squash-Merge) → LOG (Evidenz). Mit State/Resume und Single-Writer-Lock. |
| `plan-dev-loop` | Plan-Mode-Meilenstein-Planer: grill-4x4-Mining → verifizierte Ausgangslage (messen, nicht glauben) → Meilenstein-Graph mit Dep-Edges → Issues mit ausführbaren Akzeptanzkriterien → Bruchstellen-Rezepte → Emission via `gh` + Handoff-Contract an dev-loop. |
| `azahar-harness` | Azahar (Citra-Fork) als Verifikations-Orakel für 3DS-Homebrew: Xvfb-Boot, Boot-Klassifikation, Save-CRC als Beweissignal, RPC aus dem unmodifizierten Binary. Lokal, nicht CI. |
| `harness-bootstrap` | Installiert die Governance-Grundausstattung (AGENTS/WORKFLOW/DECISIONS/PROGRESS, Labels, agent-log-Issue, Verify-Befehl) in neue Repos, damit dev-loop dort läuft. Überschreibt nie Bestehendes. |

## Commands

- `/dev-loop [milestone]` — fährt den Loop für einen Milestone (leer = aktiv offener)
- `/plan-dev-loop` — startet den Plan-Mode-Meilenstein-Planer

## Installation

**ZCode (lokal, ohne Push):** Marketplace `my-agent-tools-local` zeigt auf den Repo-Root;
der Eintrag in `.claude-plugin/marketplace.json` macht das Plugin sichtbar. Enable:
`dev-loop-toolkit@my-agent-tools-local` (Plugin-Management oder
`~/.zcode/cli/config.json` → `plugins.enabledPlugins`).

**Claude Code (nach Push):** `/plugin marketplace update my-agent-tools` →
`/plugin install dev-loop-toolkit@my-agent-tools`.

Nach inhaltlichen Änderungen: `version` in `plugin.json` bumpen — installierte Kopien
löschen aus dem Cache, nicht aus dem Live-Checkout.

## Scripts

Aufruf im Skill-Kontext: `${CLAUDE_PLUGIN_ROOT}/scripts/<name>.sh` (im lokalen
Checkout: `plugins/dev-loop-toolkit/scripts/<name>.sh`).

- `scripts/frontier.sh <owner/repo> <milestone>` — offene Issues als sortierte Frontier
  (Dep-Edges aus Issue-Bodies, Gate-Blocker separat, `--json` für Maschinenlesbarkeit)
- `scripts/merge-probe.sh <owner/repo> [branch]` — Branch-Protection-Probe:
  `native-auto` (Protection aktiv → `gh pr merge --auto`) vs. `agent-side`
  (403/404, z. B. privates Free-Repo → agentenseitiges Watch+Squash)
- `scripts/loop-state.sh <repo> <cmd> …` — `.dev-loop/state.json` lesen/schreiben,
  Single-Writer-Lock mit Stale-Erkennung

## Routing (bewusst kein Duplikat)

Einzel-PR mit Briefing → `pr-ship-pattern` · PR/Issue-Mechanik → `github-pr-workflow`,
`github-issues`, `github-pr-merge-readiness` · CI-Failure-Triage → `classify-test-failures`
· Worker-Disziplin → `worker-failure-discipline` · 3 fehlgeschlagene Fixes →
`superpowers:systematic-debugging` · Lane-Isolation → `superpowers:using-git-worktrees`.

## Herleitung & Quellen

`docs/DESIGN.md` — Forensik des pokerogue-3ds-Loops, Web-Recherche (arXiv 2607.04697 zu
Agenten-PR-Konflikten, GitHub Merge-Queue-Docs, code.claude.com-Plugin-Referenz).
