# dev-lens-swarm — RepoLens-inspiriertes universelles Multi-Agent-Development-System für ZCode

> Plan genehmigt am 2026-09-06 via ZCode Plan-Mode (Übernahme der am Session-Limit
> gestorbenen Claude-Session vom gleichen Tag, 06:27).
> Build-Prozess: Subagent-Driven Development. **Keine Git-Commits** (AGENTS.md-Regel;
> my-agent-tools hat 28 uncommittete Dateien, die unangetastet bleiben).

## Hintergrund

Teil 1 der alten Session (`schwarm-ohne-barriere`, DAG/Ready-Queue-Scheduler,
`swarm.py` 594 Z. stdlib-only, 26 Tests grün) liegt fertig in
`~/.claude/skills/schwarm-ohne-barriere/` — gebaut für Claude Code.
Teil 2 (dieser Plan): das RepoLens-inspirierte universelle Multi-Agent-System
**für ZCode**, development-fokussiert.

RepoLens (kanonisch `~/20-Workspace/RepoLens`): Lens-Based Auditing — Lenses als
.md + Registry, Runden mit Meta-Orchestrator (digest → selektiver Re-Dispatch,
Sättigungssignal NO_FRESH_ANGLES), Verifier, Synthesizer mit Dedupe, DONE×N-Streak-
Terminierung, file-basierte Semaphore.

## Genehmigte Entscheidungen

1. **Farm-Skills + Plugin-Patch** — Skills nach `~/.zcode/skills/` (reiner
   Directory-Scan, sofort aktiv), Agenten in `agent-toolkit-zcode`-Quelle +
   Cache-Refresh
2. **4×4 adaptiv-fluid** — max. 4 Runden à 4 Fragen (AskUserQuestion-Maximum),
   Frontier-gesteuert, als Plan-Modus-Standard in `superpowers-zcode` verdrahtet
3. **Agents patchen + Tier-Matrix** — zc-Agents effort-Anhebung (low→mind. medium,
   xhigh→max), Tier-Matrix im Master-Skill
4. **SDD-Build + echter Probelauf** — schließt den offenen „scharfen Lauf" ein

## Tasks

### Task 1 — Port `schwarm-ohne-barriere` → `~/.zcode/skills/`
- Quelle kopieren: SKILL.md, references/ (2), templates/ (2), scripts/swarm.py, tests/
- Anpassen: `~/.claude/…`-Pfade → `~/.zcode/…` (SKILL.md, briefing-templates.md);
  Prefetch-Blocklist `swarm.py` um `~/.zcode/cli/plugins/cache/` erweitern;
  „günstigeres Claude-Modell" → GLM-5.3-Flash; workflow.js = Claude-Substrat-Referenz
- Akzeptanz: alle 26 Tests unter neuem Pfad grün; Frontmatter valide

### Task 2 — Neuer Skill `grill-4x4` (adaptiv-fluid)
- `~/.zcode/skills/grill-4x4/`: SKILL.md + references/frontier-mechanics.md + tests/
- Mechanik: 7 Seeds (Goal, Done, Boundary, Constraints, Surface, Edge, Unknown);
  Runde 0 = Kalibrierung (Domain/Commitment/Pressure, 3 Fragen); max. 4 Runden à
  4 Fragen; früh stoppen bei leerer Frontier, 5. Runde bei Sättigung; Empfehlung
  pro Frage; Nodding-along-Guard; Facts-vs-Decisions-Split; „I don't know" parken
- Akzeptanz: Struktur-Test grün; Frontmatter valide (description ≤1024)

### Task 5 — Agent-Tier-Patch `agent-toolkit-zcode` (+ Konsistenz in agent-toolkit)
- Alle 14 zc-Agents: `effort: low` → mind. medium (meist high); `xhigh` → `max`
- Beide Quell-Locations (plugins/agent-toolkit-zcode/agents/, plugins/agent-toolkit/
  agents/zc-*) konsistent halten; **uncommittete Fremdänderungen nicht anfassen**
- `.zcode-plugin/plugin.json` 0.1.0 → 0.2.0
- Cache-Refresh aus lokalem Marketplace; Cache-Verifikation
- Akzeptanz: alle zc-Agents effort ∈ {medium, high, max}; kein xhigh; Cache aktuell

### Task 3 — Master-Skill `dev-lens-swarm`
- `~/.zcode/skills/dev-lens-swarm/`: SKILL.md (Modi feature/bugfix/refactor/review/
  greenfield/discover, Mermaid-Flowdiagramme, großzügige Token-Policy),
  references/lenses/ (12 Domänen aus coding-lenses, dev-modus-spezifisch),
  references/tier-matrix.md, references/rounds.md, config/domains.json,
  templates/plan.example.json (erweitert um mode + lenses)
- Rundenmodell: triage → Round 1..N (Lens-Worker via swarm.py ready-queue) →
  digest.md (untrusted reference) → Meta-Orchestrator (NO_FRESH_ANGLES, max-rounds)
  → Verify-Spur (konkurrierend, M3-Verbot) → Synthesizer (Dedupe/manifest)
- Tier-Matrix: GLM-5.3+max = Architektur/Gate/Sicherheit; GLM-5.3-Flash+high =
  Implementierung/Verifikation/Tracing; low nur mechanische Extraktion; M3 nie Verify
- Akzeptanz: Struktur- + Tier-Konsistenz-Tests grün

### Task 4 — Pattern-Patch `superpowers-zcode` (Schritt 2)
- „1 Frage pro Runde" → grill-4x4-Referenz als Plan-Modus-Standard; Fallback für
  Nicht-Plan-Kontexte; Version 2.0.0 → 2.1.0

### Task 6 — Workflow `dev-lens-swarm.md`
- `~/10-Projekte/10-active/my-agent-tools/workflows/dev-lens-swarm.md` im Format
  wie zcode-6lane-pipeline.md (id/name/when_to_use/agents[]/skills[]/phases[]);
  Phasen: Grill → Triage → Lens-Rounds → Meta-Orchestrator → Verify → Synthesize →
  Report; INDEX/README ergänzen

### Task 7 — Integration + Review
- Gesamt-Test-Suite grün; Discovery-Checks; Two-Reviewer-Gate (Correctness +
  Completeness parallel) über den Gesamtdiff; Mermaid-Diagramme final

### Task 8 — Echter Probelauf („scharfer Lauf")
- Realer kleiner Dev-Task durch die volle Pipeline (mode=feature/bugfix), Ablauf
  über swarm.py-Ledger, Abschluss-Metriken (Makespan, kritischer Pfad, Slot-
  Auslastung, Requeue-Rate); Abschlussbericht mit Flowdiagrammen

## Globale Constraints

- KEINE Git-Mutationen (kein commit/push/stash/branch) — Verifikation via
  ausgeführte Kommandos, nicht via Commits
- Plugin-Cache (`~/.zcode/cli/plugins/cache/`) nie direkt editieren — Quelle +
  Refresh
- `~/.zcode/v2/config.json`, `~/.hermes/.env` nicht lesen/ändern (Secrets)
- Farm-Skills: nur `name`, `description` (+ `when_to_use`) sind parser-wirksam;
  description ≤1024 Zeichen; keine Kollision mit bestehenden 427 Skills
- Uncommittete Änderungen in my-agent-tools (28 Dateien) bleiben unangetastet
- Nebengefunde (z. B. defekter ~/bin/repolens-Wrapper) nur melden
