# dev-loop-toolkit — Design-Herleitung

Stand: 2026-09-17 · v0.1.0 · Branch `dev-loop-toolkit`

## Woher der Kanon kommt

Forensik des `pokerogue-3ds`-Loops (Toqsick, 16.–17.09.2026: 19 squash-gemergte PRs in
44 h, alle Issue→Branch→PR, Evidenz-Pflicht beim Close):

- **Loop-Form:** Baseline-Gate → (Gate-HALT) → Frontier → BRIEF → IMPL (max. 5
  Iterationen, 1 Hypothese/Runde) → VERIFY (3 adversariale Lenses, ≥2 erreicht, <2
  widerlegt) → LAND (`gh pr create --milestone` + `checks --watch` + squash) →
  LOG (docs(progress)-Folge-PR, agent-log-Kommentar, Evidenz-Close)
- **Merge agentenseitig**, weil Branch-Protection am privaten Free-Repo HTTP 403
  liefert (live geprüft 16.09.2026) — kein Bug, sondern Rahmenbedingung
- **Azahar als Orakel, nicht als CI**: Save-CRC-Beweis, RPC aus dem unmodifizierten
  Binary (Kein-Hook-Regel), vier dokumentierte Gründe gegen CI-Emulator-Jobs
- Quellen im Repo: `WORKFLOW.md`, `AGENTS.md`, `tools/verify.py`, `tools/emu/`,
  Plan-Doc „rosy-lemon" (`~/.claude/plans/bei-meinem-pokerouge3ds-projekt-rosy-lemon.md`)

## Design-Entscheidungen

1. **Plugin statt Skills-Ordner:** eigene Marketplace-Identität, aktivierbar in
   ZCode (lokal, live-resolve) und Claude Code (nach Push), kein Toggle-Scope-Konflikt.
   Name `dev-loop-toolkit`, weil `agent-toolkit` vom 129-Skill-Plugin belegt ist.
2. **Thin Orchestrator:** die Skills routen zu Bestehendem (pr-ship-pattern,
   github-pr-workflow/-issues/-merge-readiness, classify-test-failures, grill-4x4,
   plan/plan-glm, better-plan-strategy, superpowers-Methodik) statt es zu kopieren —
   Dedup-Regel aus skill-library-maintenance.
3. **Merge-Modus per Probe, nicht per Glaube:** `merge-probe.sh` entscheidet
   native-auto vs. agent-side aus dem Protection-API-Status (200/403/404). Das
   Ergebnis gehört dokumentiert in WORKFLOW.md („nicht erneut danach suchen").
4. **Serialität als Default, Parallelität als bewiesene Ausnahme:** IMPL sequenziell;
   parallel nur Recon/BRIEF/VERIFY-Lenses/CI-Watch; IMPL-Lanes (max. 2–3) nur nach
   Konflikt-Probe in getrennten Worktrees. Beleg: arXiv 2607.04697 (~20 % Konflikte
   selbst bei same-agent-PRs, ~42 % strukturell); rmax.ai („small but coupled tasks
   still collide", lowest-risk-first-Landing); Anthropic Multi-Agent-Research
   (3–5 parallele Subagents als Sweet Spot, Over-Delegation als Failure-Mode).
5. **State dual:** `.dev-loop/state.json` (billig, präzise, Mid-Phase) +
   agent-log-Issue (öffentlich, merge-sicher). Bei Divergenz gewinnt der agent-log.
   Single-Writer über Session-Lock mit Heartbeat + 6-h-Stale-Regel (Agenten-Sessions
   sind stundenlang aktiv; eine Script-PID wäre nach Sekunden tot).
6. **Abnahme-Trennung:** `Abnahme: Mensch`-Marker (Body) bzw. agent-log-Führung;
   frontier.sh weist solche Issues als `[abnah]` aus. Implementiert ≠ abgenommen.
7. **Kein Hook in v1:** SessionStart-Banner wäre nice-to-have; read-only-first.

## Verifiziert

- `shellcheck scripts/*.sh` → 0 Findings (SC2015-Fixes eingebaut)
- `plugin.json` JSON-valide; alle SKILL.md < 200 Zeilen; YAML-Frontmatter parser-geprüft
- Dry-Run gegen `Toqsick/pokerogue-3ds` (rein lesend):
  `frontier.sh "M-A — Automations-Harness"` → korrekte Frontier (#120/#121/#123–#127
  ready, `gate:G-A` #128 als HALT ausgewiesen); `merge-probe.sh` → `agent-side`
  (HTTP 403, deckungsgleich mit der Live-Prüfung vom 16.09.)
- Two-Reviewer-Gate (Correctness + Completeness, parallel): Befunde alle behoben —
  YAML-Frontmatter (deutsche Anführungszeichen), Lock-Doc-Drift (session-id/6 h statt
  PID/60 min), Milestone-Existenzcheck gegen Tippfehler-Leerfrontier, unlock-Semantik
  (fremder frischer Lock nur mit id/`--force`), DEP-Regex (Listen, `#`-Pflicht),
  merge-probe 404-Typo-Guard, `${CLAUDE_PLUGIN_ROOT}`-Pfade, gh-recipes-Pointer,
  related_skills/Routing um azahar-harness + Geschwister, gitignore-Schleife,
  int-Koersion im State, Exit-Code-Doku, Kleinigkeiten (Backtick, NOT-for, Länge)

## Offen (W-Punkte)

- Commit/Push nach GitHub + Claude-Code-Installation — nur auf Aufforderung
- ZCode-Neustart/Reload, damit der Enable-Eintrag greift (config.json editiert,
  Backup `config.json.bak-devlooptoolkit`)
- INDEX.json-Regeneration (Repo-Index) erst mit dem Commit
- Cron/OffPeak-Anstoß für unattended Loop-Fahrten: dokumentiert im SKILL
  (ZCode-Tool-Map), bewusst nicht vorkonfiguriert

## Quellen

- code.claude.com/docs: plugins-reference, plugin-marketplaces, skills,
  slash-commands, best-practices
- cli.github.com/manual: gh pr merge / gh issue list; cli/cli#9073 (--auto -d
  löscht Branch nicht immer), cli/cli#1200 (kein Milestone-CRUD)
- docs.github.com: linking PR↔issue, managing-a-merge-queue
- arxiv.org/html/2607.04697 (Agenten-PR-Konflikt-Studie, 33.596 PRs)
- rmax.ai/notes/building-an-autonomous-development-loop (Loop-Shape, Guardrails)
- anthropics/engineering: Agent-Skills-Blog, Multi-Agent-Research-System
- github.com/anthropics/claude-code-action (Guardrails: write-only-Trigger,
  Bot-Filter, keine PATs)
- github.com/azahar-emu/azahar + Wiki (Build, CLI, kein Lua/Headless,
  libretro-Core); pokerogue-3ds tools/emu + WORKFLOW.md §6 (lokale Orakel-Grenzen)
