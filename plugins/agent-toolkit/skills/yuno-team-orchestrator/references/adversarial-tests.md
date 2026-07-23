# Adversarial-Tests

## Test 1: Hub-Engineer-Run reproduzieren (built 2026-07-07)

**Hub-Original-Aufgabe:**
> Build a Python CLI tool that summarizes a CSV (stdlib only)

**Hub-Ergebnis (laut `~/Downloads/team-roster.md`):**
- 273 Zeilen, 6 stdlib-Module, keine Deps
- Sample: 12 rows × 6 columns
- README + tests
- Math verified: salary mean 81333.33, active 8 yes/4 no, Engineering=5 ✓
- Edge cases: empty file (exit 1), header-only (exit 0), missing file (exit 2), mixed-blanks
- "Final report included opinionated design choices + intentional limitations"

**Hermes-Reproduktion (via `yuno-team-orchestrator`):**
- Routing: `python3 scripts/personas.py match "Build a Python CLI tool that summarizes a CSV (stdlib only)"` → `engineer:build`
- Persona-Preamble: 2225 Zeichen, alle 8 Core Rules verbatim
- Toolsets: `["terminal", "file", "code_execution"]`
- Subagent dispatched mit Engineer-Persona + identischer Briefing-Struktur wie Hub

**Vergleichs-Kriterien:**
- [ ] Output-Path: `/tmp/hermes-team-test/csv_summary/` (vs Hub: `/workspace/csv_summary/`)
- [ ] Datei `csv_summary.py` existiert
- [ ] Stdlib-only (`grep -E "^import (pandas|numpy)" csv_summary.py` = 0 Treffer)
- [ ] Tests passed (pytest exit code 0)
- [ ] Sample-Datei: 12 Zeilen, 6 Spalten
- [ ] Math: salary mean 81333.33 ± 0.01, Engineering count = 5

→ **Live-Run-Ergebnis:** siehe `/tmp/hermes-team-test/csv_summary/` + `tests/test_*.py`

## Test 2: Routing-Engine-Smoke-Tests

| Input | Expected | Actual |
|-------|----------|--------|
| `"build a Python CLI"` | engineer:build | ✓ |
| `"research the latest in vector DBs"` | researcher:research+what's the latest | ✓ |
| `"design a landing page"` | designer:design+landing page | ✓ |
| `"spreadsheet financial model"` | analyst:spreadsheet+model+financial (Score 3) | ✓ |
| `"write a blog post"` | writer:blog post | ✓ |
| `"verify this code"` | verifier:verify (+engineer:code) | ✓ Verifier Gate-Prio |
| `"audit the deliverable"` | verifier:audit | ✓ |
| `"research and write a blog post"` | Multi-Domain: researcher + writer | ✓ Decomposition |
| `"hello, how are you?"` | NO MATCH | ✓ Default-Yuno |

## Test 3: Multi-Domain-Decomposition

**Task:** "Research vector databases and write a blog post about the latest trends"

**Erwarteter Flow:**
1. Routing-Engine matcht Researcher (research + latest) und Writer (blog post)
2. Multi-Domain-Detection triggert
3. Phase 1: Researcher-Dispatch (web-search)
4. Phase 1: Writer wartet (nicht parallel!)
5. Phase 2: Yuno synthetisiert Researcher-Resultate
6. Phase 3: Writer-Dispatch mit Researcher-Fakten als Briefing
7. Phase 4: Verifier-Gate

→ Manuell testbar via:
```bash
route "research the latest in vector databases and write a blog post about it"
```

## Test 4: Verifier-Gate-Mode

**Task:** "Is my CSV CLI ready to ship? Audit it."

**Erwarteter Flow:**
- Routing: Verifier (audit) + Engineer (ship)
- Gate-Priorität → Verifier als Top-Match
- Yuno feuert Verifier-Subagent mit Engineer-Preamble + Audit-Briefing
- Verifier liest Files, führt Tests aus, gibt PASS/FAIL mit Evidenz

## Regression-Test-Skript

Nach jedem personas.yaml-Update:

```bash
cd ~/.hermes/skills/yuno-team-orchestrator

# Routing-Smoke
python3 scripts/personas.py match "build something"  # engineer
python3 scripts/personas.py match "research X"        # researcher
python3 scripts/personas.py match "design UI"         # designer
python3 scripts/personas.py match "model data"        # analyst
python3 scripts/personas.py match "write doc"         # writer
python3 scripts/personas.py match "verify code"       # verifier
python3 scripts/personas.py match "hello"             # NO_MATCH

# Persona-Vollständigkeit
for p in engineer researcher designer analyst writer verifier; do
  python3 scripts/personas.py preamble $p | head -5
done

# Multi-Domain
python3 scripts/personas.py route "research and write about X"  # multi
```

## Known Limitations der Adversarial-Tests

- **Nicht alle Hub-Edge-Cases 1:1 nachgestellt**: Hub hatte z.B. "mixed-blanks in numeric column". Hermes-Repro fordert das auch, aber ob der Subagent es exakt gleich löst hängt von der LLM-Temperatur ab.
- **Persona-Version-Drift**: Wenn Hub die Persona-Prompts updated, müssen wir `personas.yaml` synchronisieren. Aktuell manuelle Sync (siehe SKILL.md "Source-of-Truth").
- **Subagent-Self-Reports nicht vertrauenswürdig**: Pitfall #5 aus `multi-agent-orchestration`. Parent (Yuno) muss Files lesen + Tests laufen lassen, nicht nur den Summary akzeptieren.