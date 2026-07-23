# Skill-Tiers für Yuno's Hermes-Setup

> Adaptiert aus dem `swarm`-Bundle v1.0 (Mavis/MiniMax-Architektur, 2026-07-11).
> **Source of Truth für Skill-Empfehlungen:** dieses Dokument.
> Aktualisiert durch das Yuno-Konsolidierungs-Team oder direkt hier editiert.
>
> **Was anders ist als im Original:** Skill-Namen sind auf das echte Hermes-Inventar
> gemappt (Claude-Ökosystem → Hermes-Pendants), `agent:`-Tags verweisen auf unseren
> 7-Agent-Roster, Power-Combo-Stacks sind um unsere Orchestrierungs-Skills erweitert,
> ehrliche Lücken sind markiert (z.B. `worktree-management` → TODO, kein Pendant).
>
> **Versionierung:** v1.0 (2026-07-11) — Initial-Import aus swarm-v1.0 + Mapping.

## Kontext: Was Mavis + MiniMax anders macht

Seit Mai 2026 läuft MiniMax's Agent-Produkt auf **Mavis** (MiniMax as a Jarvis):

- **Team Engine:** Leader-Worker-Verifier-Architektur (deterministische State Machine)
- **Adversarial Verification:** Worker muss gegen Verifier bestehen — "挑刺"-Pattern
- **Context Isolation:** Jeder Agent sieht nur seinen Task-Ausschnitt
- **Memory + Skills Evolution:** "踩过的坑会进记忆，有价值的动作会变成 Skill"
- **IM-Integration:** WeChat/Feishu-Pipeline mit "秒回 + 后台执行" Entkopplung

**Implikation für Skill-Auswahl:** Skills die das Team-Engine-Pattern optimal nutzen sind
wertvoller als reine Single-Agent-Skills. Skills die chained/nested werden können, gewinnen.
Skills die deterministische Verifikation ermöglichen (statt subjektiver Bewertung), passen besser.

**Unser Match:** Das `yuno-team-orchestrator` Skill-Pairing (Routing-Spec + Fix-Loop-Pattern)
realisiert exakt diese Architektur. Skill-Tiers hier sind die **priorisierte Welche-Skills-zu-welchem-Workflow-Combo**.

---

## Tier 1 — MUST-HAVE (sofort aktivieren)

Zahlen auf den Kern-Use-Case jedes Yuno-Setups ein, validiert als hochwertig in
mehreren unabhängigen Quellen (bestskills.dev, Anthropic-Top-10, Mavis-Doku).

### 1. `brainstorming` → **`ideation`** (Unser Pendant)
**Warum:** Vor JEDER kreativen/Build-Arbeit zwingt dieser Skill zu Intent-Klärung. Spart massiv Token und Rework.
**Use-Case:** Neue Features, Bug-Investigations, Design-Entscheidungen, "was will ich eigentlich?"
**Quellen:** Anthropic-Top-10, ShareUhack's "5 Skills that Actually Work".
**Trigger:** "lass uns X bauen" / "ich brauche Y" / "hilf mir Z zu designen"
**Agent-Tag:** `agent: Yuno` (root, decompose-first)

### 2. `plan` → **`plan`** (1:1 Match, ggf. + `writing-plans`)
**Warum:** Strukturierter Plan-Modus vor Execution. Verhindert Mid-Execution-Drift. Matched 1:1 das Mavis-Team-Pattern.
**Use-Case:** Jede komplexe Aufgabe mit >3 Schritten.
**Quellen:** Plan-Modus ist explizit im Mavis-Workflow erwähnt.
**Trigger:** Multi-Step-Aufgaben, "wie gehen wir vor", "liefere einen Plan"
**Agent-Tag:** `agent: Engineer` (1-Strike in `references/routing-table.md`)

### 3. `systematic-debugging` → **`systematic-debugging`** (1:1 Match)
**Warum:** 4-Phasen Root-Cause-Methode. Akademisch validiert: Korrektheit 80% vs 20-44% bei traditionellem Ansatz.
**Use-Case:** Jeder Bug, jedes "es funktioniert nicht", jedes Mystery-Failure.
**Quellen:** bestskills.dev Score 94/100, explizit als "Excellent" eingestuft.
**Iron-Law:** "NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST"
**Trigger:** "X geht nicht", "Bug", "Error", "warum crasht das"
**Agent-Tag:** `agent: Engineer`

### 4. `frontend-design` → **`ui-factory`-Bündel** (Unsere Variante)
**Warum:** Höchst-installierte Skill-Familie im gesamten Ökosystem. Generiert production-grade Frontend.
**Use-Case:** Landing Pages, Dashboards, React-Components, HTML-Artifakte.
**Quellen:** Konsistent in Top-10-Listen (Zima Store, ScriptByAI, ShareUhack, OpenDataScience).
**Trigger:** "bau eine Webseite", "UI für X", "design Y"
**Bonus:** Anthropic-Empfehlung, Outputs direkt als HTML zu liefern statt Markdown ("The Unreasonable Effectiveness of HTML").
**Bei uns:** `ui-factory` orchestriert die volle Kette `ui-color-system` → `ui-design-system` → `ui-component-library` → `ui-dashboard`. Plus `claude-design`, `html-artifact`, `popular-web-designs` als Atoms.
**Agent-Tag:** `agent: Designer`

### 5. `web-design-guidelines` → **`web-design-guidelines`** (1:1 Match)
**Warum:** Audit gegen Vercel's Web Interface Guidelines. Pair mit `ui-factory` für Qualitätssicherung.
**Use-Case:** Review/Check bestehender UIs.
**Quellen:** 28.8k stars, 449k installs.
**Trigger:** "review das UI", "check accessibility", "audit design"
**Agent-Tag:** `agent: Designer`

### 6. `deep-research-agent` → **`research-tools`-Bündel** (Unsere Variante)
**Warum:** Multi-Phase Research-Pipeline mit Decomposition → Gathering → Reasoning → Verification → Synthesis. Academic-Grade.
**Use-Case:** Marktanalysen, Competitor-Research, Technology-Trends, Fact-Checking.
**Quellen:** Explizit in Top-10-Listen, arxiv validiert in "Step-DeepResearch"-Studie.
**Trigger:** "research X", "was ist der Stand zu Y", "vergleich Z"
**Bei uns:** `research-tools` ist Hub, spezialisierte Atoms sind `arxiv`, `llm-wiki`, `notebooklm-bridge`, `firecrawl-web`, `web-archive-research`, `blogwatcher`, `ocr-and-documents`, `research-paper-writing`.
**Agent-Tag:** `agent: Researcher`

### 7. `self-improving` → **`self-improving`** (1:1 Match)
**Warum:** Persistiert Lessons aus Fehlern in dauerhafte, grep-bare Memory-Einträge. Verhindert dasselbe Problem 2x.
**Use-Case:** Nach jedem nicht-trivialen Fehler sofort triggern.
**Quellen:** Aligns mit Mavis' "M3 Training auf vergangenen Traektorien".
**Trigger:** "das war falsch", "fix it this way", "merken für nächstes Mal"
**Bei uns:** Pair mit `mnemosyne_remember`/`mnemosyne_validate` für durable Memory. Lesson-Skill-Pattern: Meta-Skill nach 5+ Tool-Calls oder tricky Fix.
**Agent-Tag:** `agent: Yuno` (root, lessons sind cross-domain)

---

## Tier 2 — HOCHWERTIG (regelmäßig nutzen)

Lösen spezifische Probleme gut, sind aber nicht alltäglich nötig.

### 1. `skill-creator` → **`skill-creator`** (1:1 Match)
**Warum:** Erstellt Skills aus Beschreibungen. Wenn du 3x denselben Workflow machst → Skill. Anthropic's eigener Meta-Skill.
**Use-Case:** Eigene Custom-Skills bauen.
**Quellen:** 25.5k stars, 2M installs — **#1 meistinstallierte Skill**. Anthropic built-in tool.
**Best Practice:** "Notice, name, write, test, refine" — der 5-Schritte-Loop.
**Trigger:** "diesen Workflow immer wieder", "bau einen Skill", "kapsel das"
**Bei uns:** Pair mit `skill-install-workflow` für externe Skills.sh-Imports.
**Agent-Tag:** `agent: Yuno`

### 2. `code-review` → **`requesting-code-review`** (Unsere Variante)
**Warum:** Multi-Agent-Pattern: spezialisierte Sub-Agents reviewen Code. Vor jedem Commit/Merge.
**Use-Case:** Pre-commit, Pre-PR, nach langer Session.
**Quellen:** Konsistent in Top-Listen, OpenDataScience Top 10.
**Trigger:** "review das", "ist der Code sauber", "check bitte"
**Bei uns:** Plus `github-code-review` für PR-Review via `gh`.
**Agent-Tag:** `agent: Verifier`

### 3. `test-driven-development` → **`test-driven-development`** (1:1 Match)
**Warum:** Red-Green-Refactor erzwingen. Phase-Gates. TDD Skill allein triggert ~20% der Zeit, mit Hooks 84%.
**Use-Case:** Feature-Development, Refactoring.
**Quellen:** ShareUhack's "5 Skills that Actually Work" — `tdd` ist #1 dort.
**Trigger:** "bau Feature X mit Tests", "TDD", "test-first"
**Agent-Tag:** `agent: Verifier`

### 4. `simplify-code` → **`simplify-code`** (1:1 Match)
**Warum:** 3 parallele Sub-Agents für Cleanup. Erkennt +20% bis +30% Effizienzgewinne.
**Use-Case:** Nach Feature-Completion, vor PR.
**Quellen:** Snyk, OpenDataScience Top-Listen.
**Trigger:** "räum das auf", "simplify", "refactor"
**Agent-Tag:** `agent: Verifier`

### 5. `multi-agent-work` → **`multi-agent-work`** (1:1 Match)
**Warum:** 6-Phasen-Workflow (Research → Fixes → ...). Matched Mavis' Team-Pattern 1:1.
**Use-Case:** Komplexe Multi-Domain-Tasks.
**Trigger:** "wir brauchen einen Plan mit mehreren Phasen", "research und umsetzen"
**Bei uns:** Pair mit `multi-agent-orchestration` (Hub), `multi-agent-master-workflow`, `queen-bee-schwarm-dispatch` (Pattern), `orchestration/fable-orchestration-pattern` (M3-Scout→Execute).
**Agent-Tag:** `agent: Yuno`

### 6. `team` → **`yuno-team-orchestrator`** (Unser Pendant)
**Warum:** Plan-basierte Producer-Verifier-Workflows. Direkter Mavis-Match. (Bei uns: das Swarm-Roster selbst, nicht der Plan-Engine.)
**Use-Case:** High-stakes Deliverables, "muss verifiziert sein".
**Quellen:** Aligns exakt mit Mavis' Team Engine.
**Trigger:** "wichtig, brauche verification", "mehrere agenten parallel"
**Bei uns:** Pair mit `yuno-team-routing` (deprecated ab v2.0.0, in orchestrator absorbed) für Persona-Decision-Lookup.
**Agent-Tag:** `agent: Yuno`

### 7. `worktree-management` → ⚠️ **LÜCKE: kein natives Pendant** (TODO)
**Original:** Git worktree-Pattern. Saubere Isolation pro Task. **Vor jedem Code-Change laden.**
**Use-Case:** Multi-Branch-Entwicklung, isolierte Features.
**Quellen:** Anthropic-Standard für Claude Code.
**Trigger:** "neuer Branch", "isoliert arbeiten", "feature in worktree"
**Workaround aktuell:** Manuell via `git worktree add` oder eigenes Helper-Skript. Substitution durch `git-clone-audit` nur für Clone-Vergleiche, nicht für Live-Worktrees.
**TODO:** Skill kreieren wenn der Worktree-Use-Case 3x auftritt. Trigger-Detection: User erwähnt "Branch X isoliert entwickeln" oder "Parallel-Worktrees für Feature A/B".
**Agent-Tag:** `agent: Engineer` (wenn existent)

### 8. `verify-before-fix` → **`verify-before-fix`** (1:1 Match)
**Warum:** Verifiziert dass Bug noch existiert bevor er angefasst wird. Verhindert veraltete Fixes.
**Use-Case:** Bei Issues aus alten Bug-Reports, gestaffelten Bugs.
**Trigger:** "issue #X fixen", "alter bug report"
**Agent-Tag:** `agent: Verifier`

### 9. `mcp-builder` → **`mcp-server-authoring`** (Unsere Variante)
**Warum:** Baut MCP-Server (Model Context Protocol). Erweitert Yuno's Tool-Reach substantiell.
**Use-Case:** Eigene Tools/Anbindungen zu externe Services.
**Quellen:** OpenDataScience, Firecrawl Listen.
**Trigger:** "bau MCP server", "integriere X"
**Bei uns:** Plus `hermes-mcp-integration` für Plugin-Registry-Pattern, `native-mcp` für Client-Seite.
**Agent-Tag:** `agent: Engineer`

---

## Bewährte Workflow-Stacks (Power-Combos)

Die hier sind die adaptierten Stacks für Yuno's Hermes-Setup. Abweichungen vom
Original sind mit **[Hermes-Adapt]** markiert.

### Forschungs-Stack
```
ideation → research-tools → multi-agent-work → plan → output-validator
```
Plus optional: `arxiv` für Academic-Paper, `firecrawl-web` für Web-Recherche,
`web-archive-research` für historische Snapshots, `notebooklm-bridge` für grounded Q&A.

### Code-Stack **[Hermes-Adapt]**
```
systematic-debugging (bei Bug) ODER plan (bei Feature)
  ↓
git worktree-pattern [TODO: kein Skill bei uns, siehe Tier-2 #7]
  ↓
claude-coding-specialist (Architecture) + claude-coder (Implementation) + claude-worker (Mechanical)
  ↓
test-driven-development (Tests first/parallel)
  ↓
requesting-code-review + security-code-checker + simplify-code
  ↓
github-pr-workflow + pr-body-standards
```
**Pitfall-Block aus unseren Lessons (2026-07-07+):**
- **Worktree-Step manuell:** aktuell via `git worktree add`, nicht skill-gated.
- **Fix-Loop nach Verifier-PASS:** siehe SKILL.md § "Multi-Persona Fix-Loop Pattern".

### Content-Stack **[Hermes-Adapt]**
```
plan → html-artifact (HTML) ODER system-documentation (Markdown)
  ↓
ui-factory (wenn UI involved) → popular-web-designs (für Reference) → web-design-guidelines (Review)
  ↓
humanizer (gegen AI-isms) → pr-body-standards (wenn PR-relevant)
```
Plus optional: `powerpoint` für Deck, `pdf`/`nano-pdf` für Druck-Output,
`audio-instructions` für Hör-Leitfaden, `epub-export` für E-Reader.

### Debug-Stack **[Hermes-Adapt]**
```
systematic-debugging → verify-before-fix
  ↓
claude-coding-specialist (für hard cases) → github-code-review
  ↓
self-improving (Lesson persist) → mnemosyne_remember (Memory Bank)
```
Plus optional: `python-debugpy`/`node-inspect-debugger` je nach Sprache,
`greyscript-compiler-debugging` für GreyScript, `debugging-hermes-tui-commands`
für Hermes-eigene TUI-Debugging.

### Multi-Agent-Stack (maximale Mavis-Auslastung) **[Hermes-Adapt]**
```
yuno-team-orchestrator (Routing/Lookup) → multi-agent-cluster-patterns (Pattern-Wahl A/B/C)
  ↓
queen-bee-schwarm-dispatch (2-Wellen 3+3) ODER orchestration/fable-orchestration-pattern (M3 Two-Tier)
  ↓
critic-gate → output-validator → security-code-checker (Gate)
  ↓
self-improving (Lessons persistieren, nach 5+ Tool-Calls)
```
**Bei uns verfügbar, im Original nicht erwähnt:**
- `delegation-anti-patterns` VOR dem Dispatch (Pitfall-Watchlist)
- `hermes-context-budget` für lange Sessions (>10 Tool-Calls, 85%-Compaction)
- `hermes-react-pattern` für expliziten Thought/Action/Observation-Loop

---

## Skill-Health-Check (monatlich)

```bash
# 1. Welche Skills wurden die letzte Zeit getriggert?
grep "skill:" ~/.hermes/logs/sessions.log | sort | uniq -c | sort -rn | head -20

# 2. Welche Skills laden aber helfen nicht?
# → Manuell reviewen, Description schärfen

# 3. Welche wiederkehrenden Workflows sind NICHT als Skill erfasst?
# → Kandidaten für neuen Skill via skill-creator
```

**Bei uns zusätzlich:**
```bash
# 4. Welche Skills sind im routing-table.md getaggt aber real nie benutzt?
# → Trigger-Phrasen vs. Real-Trigger-Mismatch in `references/routing-table.md` § Edge-Cases

# 5. Wo ist agent:-Tag fehlend obwohl Persona klar?
# → Cross-Check mit `references/routing-table.md` § 52-Skill-Matrix
```

---

## Echte Lücken (ehrliche TODO-Liste)

| Fehlend bei uns | Original | Workaround | Trigger für Skill-Kreation |
|---|---|---|---|
| **`worktree-management`** ⏳ | git worktree-Pattern | Manuell `git worktree add` oder Helper-Skeleton in `~/.hermes/docus/audits/worktree-helper.sh` (Pattern: prep/status/cleanup, bash -n verified). Skill-DRAFT in `~/.hermes/docus/audits/worktree-management-skill-plan-2026-07-11.md`. **Trigger-Counter: 1/3** (Mnemosyne `63d4c331169e97f4`). | User sagt "Worktree für Feature X", "isoliert arbeiten", "Multi-Branch-Entwicklung" o.ä. × 2 weitere Male. Bei 3/3: promote DRAFT → `~/.hermes/skills/worktree-management/SKILL.md` (v1.0), `agent: "Engineer"`, in `routing-table.md` Engineer-Sektion, TODO hier entfernen. |
| **`frontend-design` als Single-Skill** | Highest-installed overall | `ui-factory` als Orchestrator + 12 Designer-Atoms | Wenn User "single-shot HTML" braucht ohne Factory-Orchestration |
| **`deep-research-agent` als Pipeline-Skill** | Multi-Phase Pipeline als Skill | `research-tools` + `multi-agent-work` als manueller Combo | Wenn Multi-Phase-Research zum Hot-Path wird |

**Wenn eines davon 3x triggert: neuen Skill via `skill-creator` extrahieren.**

---

## Quellen (Auswahl)

- Mavis/MiniMax-Architektur: minimax-ai.chat, 36Kr, 网易订阅
- Skill Effectiveness: bestskills.dev, OpenDataScience, ShareUhack, Anthropic
- Skill Chaining: MattPaige68, Skywork, InnovaitionPartners
- Ecosystem Reports: AgentMan, AGNT.gg, arxiv, Firecrawl, Zima Store, ScriptByAI
- Skill Authoring: platform.claude.com/docs (Anthropic)
- Hermes-Skill-Inventur: `~/.hermes/skills/` (snapshot 2026-07-11, 263+ skills, 462 SKILL.md files)
- 7-Agent-Team-Roster: `~/Downloads/team-roster.md` (Hub-built 2026-07-07)

## Changelog

- **v1.0 (2026-07-11)** — Initial-Import aus swarm-Bundle v1.0 (Original-Datum 2026-07-11).
  Adaptiert für Hermes-Setup: Skill-Namen gemappt, `agent:`-Tags konsistent gehalten,
  Power-Combo-Stacks mit `[Hermes-Adapt]`-Markern versehen, ehrliche Lücken (worktree-management,
  single-shot frontend-design) als TODO dokumentiert, Health-Check um Hermes-spezifische
  Inventur-Querchecks erweitert.
