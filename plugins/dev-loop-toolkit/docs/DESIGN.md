# dev-loop-toolkit — Design-Herleitung

Stand: 2026-09-18 · v0.1.0 (Ziel 0.2.0, Plan: `~/.claude/plans/analysiere-den-workflow-von-golden-storm.md`)

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
   ZCode und Claude Code, kein Toggle-Scope-Konflikt. *Korrigiert 2026-09-18:* ZCode löst
   `dev-loop-toolkit@my-agent-tools-local` über den lokalen Marketplace gegen den
   **main-Checkout** auf, nicht gegen einen Feature-Branch; ein „live-resolve" der Arbeitskopie
   gibt es nicht. Ob ZCode das Plugin tatsächlich lädt, ist noch nicht live verifiziert
   (Plan, offene Fakten Nr. 6; `parity-check` T-0.9).
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
7. **Kein Hook in v1** — *überholt in v0.2:* Der Merge-Guard, der Banner, Stop und die Outbox sind Hooks (fail-closed), siehe Entscheidungsprotokoll Q19/Q31.

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

## Entscheidungsprotokoll v0.2 (grill-me, 2026-09-18)

| Q | Entscheidung | Kern-Begründung |
|---|---|---|
| 1 | Ein Plan, ein Release; Milestones darin sequenziell | Gesamtbild statt Stückwerk |
| 2 | Primärziel: unbeaufsichtigte Laufzeit | Engpass ist die Anwesenheit, nicht der Durchsatz |
| 3 | Claude Code primär, ZCode gleicher Skill-Text + Tool-Maps | superpowers-Muster |
| 4 | Gate-Klassen `gate:human` / `gate:auto` | nur echte Abnahmepunkte brauchen den Menschen |
| 5 | Verifikationspfad-PRs → `needs-human` + Hook gegen Testlöschung/Skip; Verifikationspfad-Milestones mergen normal, aber erzwungenes `gate:human` mit Mutationsbeleg | der Verify darf sich nicht selbst aufweichen |
| 6 | Universell für Dev; Azahar ist das Musterbeispiel | Muster verallgemeinern |
| 7 | Nur das Delta bauen, zu superpowers routen | keine Duplikate |
| 8 | Nachlaufender Polish-Milestone je Zyklus | QoL ohne Scope-Creep im Kern |
| 9 | Hybrid: Kern direkt, Rest per Loop (Dogfood my-agent-tools) | der Loop muss sich selbst bauen können |
| 10/14 | PokeRogue umstellen → präzisiert: pausiert bis der v0.2-Kern ladbar ist; Basti stoppt 45e47888 | kein Umbau unter laufendem Loop |
| 11/27 | Volle GUI-Exploration → echtes Display, Azahar nur isoliert + llvmpipe, Basti anwesend; Ausführungsschritt 0 | nvkms-Livelock-Risiko |
| 12/26/36 | Breite Deep Research → vor der Plan-Datei → nach 429: das Tragende jetzt, Literatur als T-1.1 | Plan steht auf geprüften Fakten |
| 13 | Telegram als Hauptkanal, GitHub-Kommentare für Nachvollziehbarkeit | Mobilität + Spur |
| 15 | #124/#125 bleiben in PokeRogue; #126/#127 generisch ins Plugin | Generisches ins Plugin |
| 16 | `oracle-harness` + Toolkit + Adapter, kein MCP | Methodik vor Werkzeug |
| 17/30 | beathome = Konsument #2, zuerst Server/API-Orakel | billig, hermetisch, NVIDIA-frei |
| 18 | Supergroup, Topic je Repo, Pin-Status, Buttons mit from.id, gespiegelt zu GitHub; Koordination über GitHub + State | Chat ist flüchtig |
| 19 | PreToolUse-Merge-Guard + Allow-Regel + PokeRogue-`gov:`-Commit (Driver-Modus präzisiert: nur der Driver merged) | Durchlauf per Regel, Kontrolle per Guard |
| 20 | Modell-agnostisch (Session-Default), optionales Gate-Modell | Unabhängigkeit über frischen Kontext |
| 21/29 | Externer Driver, frische Session je Issue; erst Spike, Fallback Stop-Hook | robust gegen Kontextverlust |
| 22 | Ein PR pro Task; Progress-Block im selben PR; Squash-SHA im agent-log | kein Folge-PR-Rauschen |
| 23 | `.dev-loop.toml` getrackt, `.dev-loop/` untrackt | Konfig reviewbar, State lokal |
| 24 | Dev: ZCode per Pfad, Claude per `--plugin-dir`; stabil: gleicher Tag; `parity-check`; 0.6.0-Symlinks bereinigen | ein Stand für beide |
| 25 | Nur Laufzeit-Nötiges vendoren; Routen zu plan-glm/better-plan/kanban weg | schlankes Set im Headless-Lauf |
| 28 | Done-Kriterium (s. oben) | messbar |
| 31 | Hooks: Guard, SessionStart-Banner (JSON), Stop, PostToolUse → Telegram gebündelt | Gruppenlimit 20/min |
| 32 | Polish: retro, status, Kostenreport, Scheduler, Grafana, Morgen-Digest | — |
| 33 | 0.2.0 bis Done, dann 1.0.0; Name bleibt | — |
| 34→40 | Lanes: 1 Session global, IMPL-Lanes opt-in mit Konflikt-Probe | gemeinsames Kontingent, ~20 % Konfliktrate |
| 35 | Android-Emulator-Orakel → eigener Folgeplan | NVIDIA-Risiko, nicht Done-relevant |
| 37 | Yuno liest ab v0.2 mit (Bot-zu-Bot), antwortet, handelt nie | neue Bot-API-Fähigkeit ohne Koordinationsrisiko |
| 38 | Machine-Account ab v0.2; Telegram-Tap → echtes Toqsick-Approval | Autor ≠ Approver beweisbar |
| 39 | Harness-Nahtstelle jetzt, ZCode-Adapter + Failover im Polish | Headless nur statisch belegt |

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
