---
name: yuno-team-orchestrator
description: Use when orchestrating Yunos 7-agent team for multi-domain tasks.
version: 2.1.0
author: Yuno (Hermes)
license: MIT
platforms:
- linux
- macos
metadata:
  hermes:
    tags:
    - multi-agent
    - routing
    - personas
    - orchestration
    - delegation
    category: orchestration
    domain: ai-orchestration
  source: ~/Downloads/team-roster.md (Hub-built 2026-07-07)
  built: '2026-07-07'
triggers:
- route
- persona
- team
- who should handle this
- delegate to
- multi-domain
- which skills does X use
- what skills does persona Y
- skill bündel
---


# Yuno Team Orchestrator

**7 spezialisierte Agents** (Yuno + Engineer, Researcher, Designer, Analyst, Writer, Verifier) mit verbatim System-Prompts aus dem Hub-Build vom 2026-07-07. Ab v2.0.0 inkl. **Agent-Tag-System**: 52 Skills markiert mit `agent:` + `routing_hint:` im YAML-Frontmatter.

> **⚠️ Dispatch-Form:** Nicht einfach alle parallel dispatchen! Siehe `references/e2e-test-pattern.md` → "Parallel-vs-Sequential Decision Matrix". Bei abhängigen Outputs (Template → Copy → Build) muss **Chained Sequential** gewählt werden, nicht Parallel.
>
> **⚠️ Absorbed Skill:** `yuno-team-routing` (v1.0.0, 2026-07-07) ist in v2.0.0 integriert. Die Routing-Tabelle, Hand-Off-Patterns und Anti-Patterns aus der alten Standalone-Skill sind jetzt hier.

## Was das hier ist

Eine **deklarative Persona-Registry** + **Routing-Engine** fuer Yuno. Liest `personas.yaml`, matcht eine User-Anfrage gegen die Trigger-Tabelle und liefert:
- Welche Persona soll ran?
- Welche Toolsets?
- Den fertigen Subagent-Briefing-Preamble (System-Prompt + Working Contract)

Single-Domain → eine Persona. Multi-Domain → Decomposition mit Verifier als finalem Gate.

## Wann nutzen?

| Trigger | Routet zu |
|---------|-----------|
| `build` / `fix` / `refactor` / `code` / `api` | **Engineer** (terminal, file, code_execution) |
| `research` / `find me` / `what's the latest` / `compare` | **Researcher** (web, browser) |
| `design` / `landing page` / `logo` / `ui` / `ux` | **Designer** (image_gen, vision, file) |
| `spreadsheet` / `model` / `calculate` / `chart` / `data` | **Analyst** (code_execution, file) |
| `write a doc` / `draft a proposal` / `blog post` / `compose` | **Writer** (file) |
| `verify` / `audit` / `is this done` / `check this` | **Verifier** (terminal, file, code_execution, web) |

> **Multi-Word-Trigger:** Trigger wie "write a doc" matchen auch ohne Stop-Woerter — "write doc" routet korrekt zu Writer. Details: `references/routing-table.md` §6.

Multi-Domain-Tasks (2+ Personas aus verschiedenen Domaenen) → decompose → jede Persona laeuft isoliert → Yuno synthetisiert → **Verifier als finales Gate**.

## Quick Start

### Shell (von ueberall)

```bash
ln -sf ~/.hermes/skills/yuno-team-orchestrator/scripts/route ~/50-System/bin/route

route --list
route "build me a Python CSV summarizer"
route --match "fix the login bug in auth.py"
route --preamble engineer
```

### Python API

```python
import sys
sys.path.insert(0, "~/.hermes/skills/yuno-team-orchestrator/scripts")
from personas import load_registry, match_persona, build_preamble, detect_multi_domain

registry = load_registry()
task = "build me a Python CLI that summarizes CSVs"
matches = match_persona(task, registry)
print(matches)

if matches:
    preamble = build_preamble(matches[0][0], registry)
```

## Architecture

```
yuno-team-orchestrator/
├── SKILL.md                  ← this file
├── personas.yaml             ← Source of Truth: 7 Agents verbatim + Routing-Tabelle
├── references/
│   ├── routing-table.md      ← Trigger-Match-Logik, Sortier-Regeln, 52-Skill-Inventar
│   ├── prompt-templates.md   ← Subagent-Briefing-Patterns
│   ├── adversarial-tests.md  ← E2E-Tests gegen Hub
│   ├── e2e-test-pattern.md   ← Context-Injection + Verifier-Preparation
│   ├── landing-page-workflow.md  ← Landing-Page-Build: Multi-Agent, Template-Engine, CI/CD (2026-07-08)
│   ├── fix-loop-pattern.md   ← Multi-Persona Fix-Loop Vorlage
│   ├── skill-tiers.md        ← Kuratierte Tier 1+2 Skills für Yuno's Setup (adap. aus swarm-v1.0, 2026-07-11)
│   ├── bundle-evaluation-workflow.md  ← Wie Third-Party-Bundles evaluieren: Wissen extrahieren vs. Bug-Fix/Release (2026-07-11)
│   ├── agent-tag-patch-workflow.md  ← Wie `agent:` + `routing_hint:` in Skills patchen
│   ├── skill-curator-audit-2026-07-11.md  ← **NEU** Read-only Audit der 14 Tier 1+2 Skills (2026-07-11, Exec Summary)
│   └── prompt-templates.md  ← Subagent-Briefing-Patterns
    ├── personas.py           ← Routing-Engine (CLI + Python-API)
    └── route                 ← Bash-Wrapper (chmod +x verified 2026-07-15)
```

## Persona-Inquiry Antwort-Template

**Wann:** User fragt "welche Skills greift Persona X zu?" oder "was kann der Designer?" — will Überblick über einzelne Rolle, nicht Dispatch.

**Nicht einfach Skills aufzählen** (User kriegt 0 Kontext). Stattdessen 4-Schichten:

| Schicht | Was rein | Quelle |
|---|---|---|
| 1. Rolle | Persona-Name, Trigger-Phrasen, Toolset, Specialty | `personas.yaml` → `personas.<x>` |
| 2. Skill-Bündel | Liste der `agent: <Persona>`-getaggten Skills | `references/routing-table.md` §52-Skill-Matrix |
| 3. Hand-Off-Matrix | Wohin reicht diese Persona ab wenn Out-of-Scope | SKILL.md §"Hand-Off Patterns" |
| 4. Atom/Molecule/Organism | Skills = Atoms, Persona = Molecule, Multi-Agent-Loop = Organism | Basti's Architektur-Insight 2026-07-08 |

**Optional:** Real-World-Proof aus dem `references/landing-page-workflow.md` oder einem anderen Multi-Agent-Build — User sieht: "die Persona wird tatsächlich benutzt, nicht nur theoretisch definiert".

**Pitfall:** Wenn nur Skills aufgezählt werden, fragt der User typischerweise nochmal nach oder sagt "ja aber wie?". Lieber **direkt alle 4 Schichten** in einer Antwort.

## Routing-Regeln (Details)

1. **Wort-Boundary-Match**: Trigger matcht nur als ganzes Wort, kein Substring.
2. **Match-Score-Sortierung**: Mehr Trigger = hoeherer Score = hoeherer Rang.
3. **Verifier-Gate-Prioritaet**: Wenn `audit`/`verify`/`is this done`/`check this`/`validate` matched, dominiert Verifier.
4. **Multi-Domain-Detection**: 2+ Personas aus verschiedenen Domaenen → Decomposition-Modus.
5. **NO-MATCH-Fallback**: Bei Chitchat wird nichts geroutet — Yuno bleibt im Default-Mode.
6. **Multi-Word-Trigger-Fallback**: Multi-Word-Trigger matchen auch ohne Stop-Woerter (z.B. "write doc" matcht "write a doc"). Inhaltswoerter >2 Zeichen werden unabhaengig geprueft. Details in `references/routing-table.md` §6.

## Integration mit Hermes delegation

```python
from personas import load_registry, match_persona, build_preamble

registry = load_registry()
task = "build a Python CSV summarizer CLI"
matches = match_persona(task, registry)
top_persona = matches[0][0]
preamble = build_preamble(top_persona, registry)

# delegate_task(goal=task, context=preamble, toolsets=registry["routing_table"][top_persona]["toolset_hints"])
```

## Multi-Domain-Flow

```python
matches = [("researcher", [...]), (writer, [...])]

for persona_key, _ in matches:
    delegate_task(goal=task, context=build_preamble(persona_key, registry),
                  toolsets=registry["routing_table"][persona_key]["toolset_hints"])

# Yuno synthetisiert → Verifier als Gate
delegate_task(goal=f"Verify the synthesized deliverable: ...",
              context=build_preamble("verifier", registry),
              toolsets=registry["routing_table"]["verifier"]["toolset_hints"])
```

## Fix-Loop Pattern (Engineer → Verifier → Fix → Re-Audit → PASS)

Eine Schlüsselerkenntnis aus dem E2E-Test vom 2026-07-07: der Multi-Persona-Loop produziert erst dann echte Qualität, wenn **mindestens ein Verifier-Durchlauf stattfindet**.

### Workflow

```
Phase 1 — Engineer baut (Subagent)
Phase 2 — Yuno self-verify (Files lesen, Tests fahren, Math checken)
Phase 3 — Verifier auditiert (adversarial Subagent)
Phase 4 — Yuno prüft Verifier-Report (Pitfall #5 — auch Verifier nicht blind glauben!)
Phase 5 — Engineer fix-loop (mit Verifier-Bug-Liste als Briefing)
Phase 6 — Verifier re-audit (bis PASS)
Phase 7 — Yuno synthesisiert + dokumentiert Lessons
```

### Realer Durchlauf (2026-07-07, csv_summary.py, 6 Runs komplett)

| Loop | Persona | Dauer | Tests | Ergebnis |
|------|---------|-------|-------|----------|
| 1: Build | Engineer (cold) | 3:43min | 9/9 | ✅ Build OK |
| 2: Self-Verify | Yuno | 1:30min | — | ✅ Math verifiziert |
| 3: Audit | Verifier (cold) | 3:16min | — | ❌ **FAIL** — 8 Bugs |
| 4: Report-Prüfung | Yuno | 2:00min | — | ⚠️ 1 FP + 1 enger Trigger = 6/8 bestätigt |
| 5: Fix-Loop | Engineer (warm) | 2:33min | 15/15 | ✅ Fixes OK |
| 6: Re-Audit | Verifier (cold) | 4:03min | 15/15 | ⚠️ **PASS** — 2 NEUE Bugs (#9 BOM, #10 dup headers) |
| 7: Fix-Loop #2 | Engineer (warm) | 1:37min | 17/17 | ✅ Finale Fixes |
| 8: Final Audit | Verifier | ~3min | 17/17 | ✅ **PASS** oder neue Findings |

**Total:** ~22 min Wall-Time, 0 → 410 LoC, 0 → 17 Tests, 10 echte Production-Bugs identifiziert + gefixt.

### Pitfalls bei Verifier-Subagenten

**Pitfall #1: Subagent sagt Root-Cause richtig, Trigger zu eng**
→ Verifier identifizierte overflow bei großen Werten korrekt als HIGH-Severity-Bug, schrieb aber "Repro: 9999 crasht" — 9999 crasht NICHT (alle gleich → std=0). Der echte Crash passiert erst bei 1e308 (fsum overflow).
→ **Lektion:** "Root-Cause richtig ≠ Repro passt." Mechanik prüfen, nicht 1:1 Repro übernehmen.

**Pitfall #2: Verifier hat False-Positives**
→ Verifier meldete "README sagt 7 Tests, file hat 9" — README hatte gar keine Test-Count-Zahl.
→ **Lektion:** Jeden Verifier-Fund selbst nachstellen. Wenn Repro nicht sauber reproduziert → Severity runterstufen.

**Pitfall #3: Subagent-Self-Reports immer verifizieren (gilt für ALLE Personas)**
→ Verifier-Subagent hat 196s gearbeitet mit 46 API-Calls. Trotzdem: selbst nachstellen.
→ **Lektion:** Nie Output eines Subagenten 1:1 als Wahrheit akzeptieren. Pitfall #5 aus delegation-anti-patterns gilt überall.

### Wann Fix-Loop aktivieren?

- **Production-ready Deliverables:** IMMER Fix-Loop bis PASS
- **Prototypen/Demos:** Einmal Engineer reicht. Verifier optional.
- **Chitchat/Snippets:** Kein Fix-Loop nötig.
- **Basti sagt "okay C" → Fix-Loop:** Wenn Basti eine der Fix-Loop-Optionen wählt, sofort in den Cycle starten.

## Adversarial-Tests (Built-in)

Siehe `references/adversarial-tests.md` fuer den E2E-Test gegen den Hub-Engineer-Run:
- Hub: Python CSV-CLI, 273 Zeilen, 6 stdlib-Module, 12x6 Sample-Daten, salary-mean 81333.33, active 8 yes/4 no, Engineering=5
- Hermes (via dieses Skill): identische Aufgabe dispatched, Ergebnisse verglichen

## Known Limitations

- **Kein auto-Middleware**: Yuno liest die Tabelle manuell. Fuer echtes Auto-Routing braucht's einen Hermes-Hook.
- **Routing ist deterministisch**: Kein ML-Modell, nur Regex-Trigger. Kontextuelle Disambiguation limitiert.
- **Subagent-AutoApprove**: Braucht `delegation.subagent_auto_approve: true` in config.yaml (verifiziert).
- **Kein auto-sync mit team-roster.md:** `~/Downloads/team-roster.md` ist die Source of Truth. Sync ist manuell.
- **Overlap: yuno-team-routing existiert noch:** v2.0.0 absorbierte den Inhalt, aber die Standalone-Datei `~/.hermes/skills/yuno-team-routing/SKILL.md` lebt weiter. Beim nächsten Curator-Durchlauf konsolidieren (`absorbed_into=yuno-team-orchestrator`). In der Zwischenzeit: dieser Skill ist die autoritative Version.

## 🔀 Hand-Off Patterns (Cross-Agent)

Wenn ein Agent merkt dass der Task nicht in seinen Scope fällt oder er eine andere Expertise braucht:

| Von | Nach | Wann |
|---|---|---|
| **Engineer** | → Yuno | Design decision needed, scope ballooning, blocked on missing context |
| **Researcher** | → Yuno | Claim verification needed across multiple workers |
| **Designer** | → Researcher | When brand context (competitors, references, trends) is needed |
| **Designer** | → Writer | When copy/text is needed for the design |
| **Analyst** | → Designer | When data visualization / chart is the deliverable |
| **Writer** | → Researcher | When fact-check needed |
| **Writer** | → Designer | When visual layout / diagram is needed as part of copy |
| **Any** | → Verifier | When quality gate is needed before user sees the result |

**Off-Scope Protocol:** Agent merkt "das ist nicht mein Territory" → sagt "this is X's territory, not mine" + hands back to Yuno. Yuno re-routes (kein silent failure).

## 🐝 Anti-Patterns

- **Don't try to do another agent's job.** If the task is Writer's territory and you're Engineer, say so explicitly — don't write a doc.
- **Don't skip Verifier on multi-domain tasks.** Final gate belongs to Verifier.
- **Don't synthesize without domain specialist input.** Yuno is the conductor, not the orchestra.
- **Don't add extra scope during fix-runs.** Engineer must resist "while I'm here" — use "Deliberately not changed" Section in Fix-Briefings.
- **Don't take Verifier findings as gospel.** Pitfall #2 (False Positives) happens. Mechanik prüfen, nicht 1:1 Repro übernehmen.
- **Don't trust memory claims about PR/cron/service state without live verification.** Memory (Mnemosyne) kann stale sein — eine PR die vor 2 Tagen "pending" war kann heute gemerged sein. Ein Cron-Job den das Briefing als defekt listet kann nach Reboot laufen. **Check-Reflex:** `gh pr list`, `git log origin..HEAD`, `cronjob(action='list')`, `systemctl is-active` — immer live verifizieren bevor du warnst oder handelst. Siehe Lesson 2026-07-11: Rabat-PR-war-Merge-Warnung aus Memory war obsolet. Memory-consolidation-preference (2026-07-01) sagt bewusst: KEINE PR-Nummern, Commit-SHAs oder Branch-Namen in Mnemosyne speichern.
- **Don't ask the user "do we use the full matrix?" and stop at 40%.** A coverage question almost always deserves a rollout, not a report. The user wants the system activated, not an audit. Pair the answer with: (a) where the 0% lies (specific stranded tasks, missing config, missing descriptions), (b) the 4-phase sequence to fix it, (c) offer to dispatch it in this session. A report without an execution plan reads as evasion. See `references/coverage-rollout-2026-07-09.md` in `kanban-orchestrator` for the worked example.
- **"Bienen-Dispatch" works best as 2-wellen fan-out (3+3), not 6-in-one.** Dispatching 6 tasks in a single command batch creates a thundering herd that competes for tool/port resources and makes individual failure diagnosis harder. Wave 1 (3 tasks) → 5-10s pause → Wave 2 (3 tasks) lets the dispatcher settle between waves and gives the orchestrator a chance to spot spawn_failed patterns early.
- **Subagents haben KEINE `web_search` / `web_extract`-Tools (bestätigt 2026-07-10).** Reine Recherche-Tasks brauchen entweder (a) Queen sammelt extern vorher, oder (b) Briefing ist explizit "interne Quellen only". Sonst melden Subagents ehrlich "intern dokumentiert, nicht extern validiert" und das Output ist ohne Wert für externe Claims. Web-Tool-Limitation schließt Filesystem-/Konfig-/Code-Recherche NICHT aus — die läuft perfekt.
- **Verify-Layer zwischen Wellen ist Pflicht, nicht Kür.** 2-Wellen-Pattern funktioniert nur wenn Yuno zwischen Wellen die Outputs gegen das echte Filesystem cross-checkt (nicht nur Summary-Text). Beispiel-Pattern: `cronjob get <id> | grep -E '"provider"|"model"'` + `grep -E "neuer-skill" vault/MOC*.md`. Subagent-Self-Reports sind Netze, keine Garne.
- **Briefings müssen den Tool-Set der Subagent klar benennen** ("no web tools required" oder "research aus ~/Pfad/X"). Subagent kann sich keine Tools selbst dazuholen — wenn web_recherche gebraucht wird, muss sie Queen vorher erledigt haben.
- **Tier-Drift-Trap: Tier-Table und Persona-Matrix auseinander.** Wenn `references/skill-tiers.md` (Priorisierung) ODER `references/routing-table.md` (Persona-Besitz) editiert wird, MUSS ein Cross-Check laufen: jeder Tier-Skill aus `skill-tiers.md` muss in der `routing-table.md` existieren, und jede neue Persona-Sektion muss die zugehörigen Tier-Skills taggen. Ohne diesen Check hat man Skills, die im Changelog als "MUST-HAVE" stehen, aber in der 56-Skill-Matrix offiziell nicht existieren. **Trigger:** nach jeder Edit an einem der beiden Files → `for skill in $(grep -E '^\| \`[a-z]' references/skill-tiers.md | grep -oE '\`[a-z-]+\`'); do grep -q "$skill" references/routing-table.md || echo "❌ $skill fehlt in routing-table"; done`. Siehe v2.0.8 Changelog für das worked example (5 untagged Tier-Skills gefangen in derselben Session).

## 🏷️ Agent-Tag System

Seit der v2.0.0 (2026-07-07) haben 52 Hermes-Skills ein `agent:`- und `routing_hint:`-Feld im YAML-Frontmatter:

```yaml
# Beispiel: claude-coder/SKILL.md
agent: "Engineer"
routing_hint: "Focused on code build/debug/refactor. Off-scope: visual design, long-form writing, data modeling."
```

| Agent | Tagged Skills | Type |
|---|---|---|
| **Engineer** | 8 | claude-coder, claude-coding-specialist, claude-worker, systematic-debugging, github-workflow, subagent-driven-development, plan, writing-plans |
| **Researcher** | 9 | research-tools, arxiv, llm-wiki, notebooklm-bridge, firecrawl-web, research-paper-writing, bioinformatics, ocr-and-documents, web-archive-research |
| **Designer** | 12 | ui-factory/design-system/color-system, html-artifact, popular-web-designs, anime-design, film-shot, architecture-diagram, excalidraw, web-design-guidelines, humanizer, claude-design |
| **Analyst** | 9 | mlops-suite, axolotl, vllm, lm-evaluation-harness, w&b, huggingface-hub, llama-cpp, rag-pipeline-python, obliteratus |
| **Writer** | 6 | system-documentation, pr-body-standards, pdf-anthropic, nano-pdf, powerpoint, epub-export |
| **Verifier** | 8 | critic-gate, security-code-checker, requesting-code-review, output-validator, verify-before-fix, simplify-code, security-audit, test-driven-development |

**Full matrix in `references/routing-table.md`** — 52 entries with exact YAML-frontmatter examples.

### Patching-Workflow (für zukünftige Skills)

Wenn ein neuer Skill zum Agenten-Team hinzukommt:

```python
from pathlib import Path
import yaml

text = Path("skill/SKILL.md").read_text()
if not text.startswith("---"): return
end = text.index("---", 3)
fm_text = text[3:end]
fm = yaml.safe_load(fm_text)

fm["agent"] = "Engineer"  # pick from the 7 agents
fm["routing_hint"] = "Focused on X. Off-scope: Y, Z."

new_fm = yaml.safe_dump(fm, default_flow_style=False, sort_keys=False, allow_unicode=True)
text = f"---\n{new_fm}---{text[end+3:]}"
Path("skill/SKILL.md").write_text(text)
```

→ Complete workflow in `references/agent-tag-patch-workflow.md`

### In Bundles deployen

Das Agent-Tag-System wurde in alle 5 MiniMax-Bundles deployed:
- Jedes Bundle hat den `yuno-team-routing` Skill (absobiert in diese Skill v2)
- 51 von 52 Skills haben saubere `agent:` + `routing_hint:` Tags
- Einziger YAML-Edge-Case: `llm-wiki` (`Karpathy's` → block scalar statt single-quoted)


## Multi-Persona Fix-Loop Pattern (gelernt 2026-07-07)

**Erkenntnis:** Die echte Power des Teams ist nicht "eine Persona bauen lassen" — es ist der **iterative Loop** über mehrere Personas.

```
Phase 1: Engineer baut (Self-Tests grün, aber adversarial-brittle)
Phase 2: Verifier audit (FAIL: 6 HIGH/MED Bugs gefunden)
Phase 3: Engineer fixt mit Verifier-Liste als Briefing (15/15 Tests grün)
Phase 4: Verifier re-audit (PASS oder neue Regressions)
Phase 5: Yuno synthetisiert + dokumentiert Lessons
```

**Briefing-Template für Engineer-Fix-Run** (siehe `references/prompt-templates.md` → "Fix-Loop"):
- Verweis auf ALLE Verifier-Bugs mit file:line und exakter Repro
- Priorisierung (HIGH → MED → LOW)
- "Apply LOW if cheap" als Opt-in für opportunistische Fixes
- Explizite Test-Anforderungen (1 Test pro Bug)
- "Deliberately not changed" Section erzwingen → keine Scope-Ballons

**Briefing-Template für Verifier-Re-Audit** (siehe `references/prompt-templates.md` → "Re-Audit"):
- Liste der "claimed fixed" Bugs (vorher eigene Findings)
- Phase 1: Confirm-Fixes
- Phase 2: Adversarial-Regression-Hunt (NEUE Inputs, die die Fixes triggern könnten)
- Phase 3: Self-Run der Test-Suite
- Phase 4: Code-Review auf TODOs/Anti-Patterns
- "If you can't break it, say so explicitly with the inputs you tried"

**Lessons aus dem CSV-Summary-Loop:**
- **Warm-Subagents sind 2.3× schneller** — Engineer Run 5 (97s) vs Run 1 (223s). Grund: Code ist bereits im Subagent-Kontext, kein Fresh-Read + keine Initial-Environment-Friction.
- Verifier kann 8 echte Bugs in 196s finden (gegen ein 293-LoC-Tool)
- Engineer kann 6 HIGH/MED + 3 LOW Bugs in 153s fixen (gegen 6 Bug-Briefing)
- Verifier-Re-Audit findet 0-1 neue Regressions (Loop konvergiert schnell)
- Pitfall #5 gilt für ALLE Subagents, auch für Verifier: Mechanik prüfen, nicht 1:1 Repro übernehmen

## Source-of-Truth

Persona-System-Prompts sind **verbatim** aus `~/Downloads/team-roster.md` (Hub-Build 2026-07-07). Bei Hub-Updates → synchronisieren + Version bumpen.

Routing-Tabelle, Agent-Tags und Hand-Off-Matrix sind aus dem absobierten `yuno-team-routing` Skill übernommen (v1.0.0, 2026-07-07).

## See Also

- `references/routing-table.md` — Trigger-Details, Edge-Cases, **52-Skill-Routing-Matrix** (alle `agent:`-getaggten Skills)
- `references/skill-tiers.md` — **Kuratierte Skill-Priorisierung** (Tier 1 MUST-HAVE + Tier 2 HOCHWERTIG) für Yuno's Setup. Adaptiert aus swarm-v1.0 mit Hermes-Inventar-Mapping. Power-Combo-Stacks (Forschungs-/Code-/Content-/Debug-/Multi-Agent-Stack). Ehrliche Lücken (`worktree-management`, single-shot `frontend-design`) als TODO. Load wenn du Skill-Wahl für neuen Workflow planst — gibt dir die priorisierte Auswahl.
- `references/bundle-evaluation-workflow.md` — **Entscheidungsbaum und Wissensextraktion für Third-Party-Bundles.** Statt blind in Bug-Fix-Release (`third-party-bundle-patch-release`) zu gehen: Bundle auf Redundanz prüfen, Mehrwert kategorisieren (Tier-Listen, Power-Combos, Pitfalls), in existierende Skills integrieren, Quelle als Read-only referenzieren. Load wenn jemand ein ZIP/Skill-Bundle bringt und du entscheiden musst ob Patch oder Wissensextraktion.
- `references/prompt-templates.md` — Subagent-Briefing-Patterns
- `references/adversarial-tests.md` — E2E-Tests gegen Hub
- `references/e2e-test-pattern.md` — Multi-Domain Context-Injection + Verifier-Preparation-Pattern (gelernt 2026-07-07 Bundle-Showcase-Test)
- `references/landing-page-workflow.md` — Landing-Page-Build mit Multi-Agent: Researcher→Designer→Writer→Engineer→Verifier→Deploy. Template-Engine-Pass-Ordnung, Writer→Engineer Data-Shape-Handoff, CI/CD für GitHub Pages, Session-Referenz (2026-07-08)
- `references/fix-loop-pattern.md` — Multi-Persona Fix-Loop Vorlage (Engineer→Verifier→Fix→Re-Audit→PASS)
- `references/agent-tag-patch-workflow.md` — Wie neue Skills mit `agent:` + `routing_hint:` patchen
- `references/skill-curator-audit-2026-07-11.md` — **NEU** Kurzfassung des read-only Audits der 14 Tier 1+2 Skills. Findings: 4 Skills ohne `agent:`-Tag im YAML, 0 Lücken, 1 offene Empfehlung (Option A: 4 YAMLs patchen). Vollbericht: `~/.hermes/docus/audits/skill-curator-2026-07-11-tier-1-2.md`.
- `~/Downloads/team-roster.md` — Original-Hub-Quelle (Source of Truth)
- ~~`yuno-team-routing`~~ — **Absobiert.** Inhalt in v2.0.0 integriert. Skill gelöscht.
- `~/Downloads/yuno-team-agents/swarm-skill-v1.0/swarm/catalog/skill-tiers.md` — **Original-Quell-Skill-Tiers**, aus dem wir Tier-Priorisierung + Power-Combos übernommen haben (adaptiert 2026-07-11). Read-only referenziert; **nicht** als Hermes-Skill installiert (von uns in v2.7 superset).

### Orchestration Ecosystem

| `orchestration/fable-orchestration-pattern` (unprotected) — M3-Only Two-Wave Schwarm (Scout→Execute). Komplementiert das Fix-Loop-Pattern (hier: Multi-Persona iterativ, dort: Multi-Agent parallel).
| `orchestration/pr-ship-pattern` (Yuno) — End-to-End-PR-Workflow: Briefing → Fable-Strategie → M3-Mechanik → Verifier-Fix-Loop → Push/Merge → Post-Merge-Doku. Komponiert fable-orchestration-pattern + yuno-team-orchestrator + github-pr-workflow.
- `orchestration/multi-agent-orchestration` (Hub, pattern repository) — 3-Expert-Deep-Research, Queen-Bee-Konfiguration, 5-Phasen-Workflow.
- `orchestration/multi-agent-pitfalls-cheatsheet` (Hub) — Trigger-Watchlist vor jedem `delegate_task`-Call. Pitfall #5 (VERIFY EVERY CLAIM) gilt auch für Verifier-Subagenten.

### User Preferences

- `yuno-user-preferences` — Basti's Style-Präferenzen (Honest Testing, Concrete Options, DB-Safety, Doc-Policy). Vor einem Fix-Loop laden.

## Changelog

- `2.1.0 (2026-07-15)` — **2 Bugs gefunden + gefixt:** (A) `scripts/route` hatte keine execute-Permission — `chmod +x` hinzugefügt, verified. (B) SKILL.md verlinkte `references/agent-tag-patch-workflow.md` an 5 Stellen, aber Datei existierte nicht. Komplette Referenz erstellt mit 3-Schritt-Workflow + Pitfalls. Plus: Architecture-Tree zeigt jetzt `(chmod +x verified)` annotation. Gelernt aus Schwarm-Polish-Session: SKILL.md verlinkt oft Referenzen die nie erstellt wurden — nach jedem Changelog-Update Referenz-Links auditieren.

- `2.0.9 (2026-07-11)` — **Tier-Drift komplett geschlossen + Anti-Pattern eingebaut.** Zwei parallele Edits in dieser Session: (A) 4 Tier-Skills (`ideation`, `self-improving`, `skill-creator`, `mcp-server-authoring`) haben jetzt additive `agent: "Yuno"` + `routing_hint:` Felder im eigenen YAML-Frontmatter. Curator-Report `skill-curator-2026-07-11-tier-1-2.md` umgesetzt. Validation: alle 4 YAMLs parsen sauber (PyYAML `safe_load`), Bodies intakt. Pfad: skill-tiers.md ↔ routing-table.md ↔ YAML pro Skill-File → Closed Loop. (B) Tier-Drift-Pitfall als Anti-Pattern in §Anti-Patterns ergänzt (siehe Zeile direkt darunter): nach jeder Edit an einer der beiden Files (skill-tiers.md oder routing-table.md) muss Cross-Check laufen. Gelernt durch Drift-Discovery in genau dieser Session.

- `2.0.8 (2026-07-11)` — **Tier-Skill-Drift-Fix:** `references/routing-table.md` 52-Skill-Matrix um neue Section `🌸 Yuno (5 Skills)` erweitert. Tagged: `ideation` (Tier-1), `self-improving` (Tier-1), `skill-creator` (Tier-2), `multi-agent-work` (Tier-2), `mcp-server-authoring` (Tier-2, mcp-builder-Pendant). Lesson: Konsistenz zwischen `skill-tiers.md` (Priorisierung) und `routing-table.md` (Persona-Besitz) MUSS in derselben Session sichergestellt werden — sonst hat man Tier-Skills die das Team offiziell "nicht kennt". Lesson-Trigger: Skill-Curation sollte immer Tier-Tabelle ↔ Agent-Matrix Cross-Check beinhalten (siehe Tier-Drift-Pitfall-Anti-Pattern in v2.0.9-B).

- `2.0.7 (2026-07-11)` — **Added `references/skill-tiers.md`** (15.5 KB): kuratierte Tier 1 (MUST-HAVE, 7 Skills) + Tier 2 (HOCHWERTIG, 9 Skills) Priorisierung für Yuno's Hermes-Setup, adaptiert aus `~/Downloads/yuno-team-agents/swarm-skill-v1.0/swarm/catalog/skill-tiers.md`. Skill-Namen auf unser Hermes-Inventar gemappt (`brainstorming`→`ideation`, `frontend-design`→`ui-factory`-Bündel, `deep-research-agent`→`research-tools`-Bündel, `mcp-builder`→`mcp-server-authoring`). Power-Combo-Stacks (Forschungs-/Code-/Content-/Debug-/Multi-Agent-Stack) um unsere Orchestrierungs-Skills erweitert. Ehrliche Lücken dokumentiert (`worktree-management` ohne Pendant, single-shot `frontend-design` als atom fehlt). Lesson von 2026-07-11: Source-Bundle war ältere Variante unseres 7-Agent-Teams (verbatim aus team-roster.md), aber die Tier-Liste war echter Mehrwert. Konsolidierungs-Prinzip: Source-of-Truth bleibt die Team-Definition; Skill-Tiers als zweite Achse (Priorisierung) hinzugefügt. Nicht das ganze `swarm`-Bundle installiert (redundant zu v2.7).

- `2.0.6 (2026-07-10)` — Anti-Patterns ergänzt: (1) Subagents ohne `web_search`/`web_extract`-Tools — externe Recherche muss Queen vorher sammeln oder Briefing "interne Quellen only" setzen; (2) Verify-Layer zwischen Wellen ist Pflicht (Filesystem-Cross-Check statt nur Summary-Text lesen); (3) Briefings sollen den Tool-Set der Subagent explizit benennen. Gelernt aus Architektur-Schwarm-Dispatches 2026-07-10 (3 Bienen ohne Web-Tools meldeten ehrlich "nicht extern validiert"). Consolidate-Hinweis an Curator: Cron-Drift-Recovery-Workflow dreifach dokumentiert in `yuno-team-orchestrator`, `hermes-maintenance`, `daily-briefing` (Sektion 2.6) — bitte Konsolidierung in eine der drei Skills prüfen.
- `2.0.5 (2026-07-09)` — Persona-Inquiry Antwort-Template hinzugefügt: 4-Schichten-Antwort (Rolle + Skill-Bündel + Hand-Off-Matrix + Atom/Molecule/Organism). Trigger-Phrasen erweitert ("which skills does X use", "skill bündel"). Gelernt aus User-Frage 2026-07-09: User will nicht nur Skill-Liste, sondern Kontext warum diese Persona welche Skills hat.
- `2.0.4 (2026-07-08)` — Updated `references/e2e-test-pattern.md` to v1.3: added Token-Naming Convention Protocol ({{copy.X.Y}} vs {{X.Y}} Abstimmung, Backcompat-Strategie, Kritikalitätstabelle). Replaced simplified Subagent Dispatch-Strategie with full Parallel-vs-Sequential Decision Matrix (3 Entscheidungsfragen, Abhängigkeitstabelle, Standard-Strategie mit 4 Waves, Ausnahme-Regeln, Effizienz-Vergleich aus dem Landing-Page-E2E). Siehe `references/e2e-test-pattern.md` → "Subagent Dispatch-Strategie" → "Parallel-vs-Sequential Decision Matrix".
- `2.0.3 (2026-07-08)` — Updated `references/landing-page-workflow.md` to v1.3: added Pitfall #6 (Inline CSS-Class-Concat → Boolean Conditional aka featured_class-Fix). Learning from the active session: string-concat CSS classes in data-driven templates are fragile — migrate to boolean conditionals with `{{#if}}`. Migration recipe with before/after JSON + HTML templates, verification grep, and "when NOT to apply" boundary conditions.: added Deployment-Readiness Snapshot section mit HTML-Comparative Smell Tests (4-Check-Pattern für Designer-vs-Pipeline-Output), BLOCKER-Tabelle für Landing-Page-Deploys, Cache-Key/Path-Filter-Check in E2E-Quality-Bar, Data-Path-Wahl in Pre-Flight-Checklist. Learning aus dem FINAL Gate: `wc -c`-Vergleich ist der schnellste BLOCKER-Detector für Integrationsbrüche in Multi-Agent-Deliverables.
- `2.0.1 (2026-07-08)` — Added `references/landing-page-workflow.md`: Landing-Page-Build-Muster mit Multi-Agent Research→Design→Write→Engineer→Verifier→Deploy. Template-Engine-Pass-Ordnung, Writer→Engineer Data-Shape-Handoff (Auto-Wrap), CI/CD für GitHub Pages mit Least-Privilege-Permissions. Architektur-Baum + See-Also aktualisiert.
- `2.0.0 (2026-07-07)` — **Absorbed yuno-team-routing v1.0.0.** Expanded from 6→7 Agents (added Yuno as explicit root persona). New: Agent-Tag-System (52 Skills mit `agent:` + `routing_hint:`), Hand-Off-Patterns (cross-agent matrix), Anti-Patterns section. Created `references/routing-table.md` (52-skill routing matrix) and `references/agent-tag-patch-workflow.md`. Removed standalone yuno-team-routing skill.
- `1.1.0 (2026-07-07)` — Loop-Konvergenz-Tabelle mit 6 Run-Daten, Warm-Subagent-Finding (2.3× schneller), Bug-Tabelle (10 Bugs), Fix-Loop-Pattern-Reference aktualisiert
- `1.0.0 (2026-07-07)` — Initial: 6 Personas, Routing-Engine, Multi-Domain-Flow, Fix-Loop-Pattern, E2E-Test gegen Hub.