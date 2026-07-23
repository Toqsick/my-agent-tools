# Documentation Planning — 4-Agent + Queen Orchestration

**Applies to:** `multi-agent-orchestration`
**Origin:** 2026-06-27 — Basti's home-directory documentation project

## Trigger

When asked to create or improve documentation for a filesystem, project tree, or directory structure — READMEs, DESCRIPTIONs, and NAVIGATION docs.

## The Pattern

```
Phase 1: Analyse (parent scans the actual structure)
Phase 2: 4 Parallel Sub-Agents (README / Description / Navigation / Control)
Phase 3: Review (Control Agent audits all outputs)
Phase 4: Queen (parent consolidates, resolves conflicts, produces final artifacts)
Phase 5: Verification (ad-hoc script checks integrity)
```

## Role Definitions

### 1. README Agent
- Creates or improves README.md files that explain purpose, conventions, usage, and maintenance
- Preserves existing content and extends it
- Practical, human-friendly Markdown
- **Key constraint:** Proposes improvements, does not execute destructive edits

### 2. Description Agent
- Creates compact, high-signal DESCRIPTION files (2-5 sentences per directory)
- Answers: what is this folder, what belongs here, what does NOT belong here
- More scannable than README — for quick orientation
- **Key constraint:** Compact — no repetition of README content

### 3. Navigation Agent
- Creates a navigation/index document (NAVIGATION.md)
- Builds a categorized map: important folders, their purpose, cross-references
- Makes discovery easy for future users/agents
- **Key constraint:** Max 60-80 lines for top-level nav

### 4. Control Agent (Review)
- Reviews all 3 other agent outputs for:
  - Safety (no destructive proposals)
  - Consistency (no contradictions between README/Desc/Nav)
  - Completeness (missing directories?)
  - Risks (possible data-loss scenarios)
  - Maintainability (are proposals sustainable?)
- Produces a Risk Report with: risk level, finding location, rationale, fix recommendation

### 5. Queen (Parent Consolidation)
- Merges all valid outputs
- Resolves inconsistencies (Control Agent findings)
- Produces the final documentation set
- Creates a Safe Action Plan (non-destructive implementation guidance)
- Executes file writes where safe (new files only, no destructive edits to existing user content)

## Sub-Agent Context Design

Each sub-agent receives the FULL directory tree and existing documentation state. 
Critical: sub-agents run in ISOLATED contexts — they cannot see each other's outputs.
The Control Agent must wait for Queen-phase visibility, or receive all outputs in its context.

### Context Template for Each Agent

```markdown
User: {username} | OS: {os} | Shell: {shell}
Home: {path}

### Directory Structure (top-level)

{tree listing — both visible and hidden directories}

### Existing Documentation

{list of existing READMEs, NAVIGATIONs, DESCRIPTIONs with sizes}

### Your Task

{role-specific instruction — see role definitions above}
```

## Toolset Assignment

| Agent | Required Toolsets | Reason |
|-------|-------------------|--------|
| README | file | Scan existing files, write proposals |
| Description | file | Scan existing files, write proposals |
| Navigation | file | Read structure, write NAVIGATION.md |
| Control | file | Read all outputs, write risk report |
| Queen (parent) | file, terminal | Consolidate, execute writes, run verification |

## Common Pitfalls

1. **Control Agent blind to Description output** — Sub-agents run in isolated contexts. The Control Agent cannot see the Description Agent's output unless it's delivered through the parent conversation. Solution: the Queen phase handles all cross-agent comparison.
2. **Navigation Agent writes directly; others propose** — The wording of the task ("erstellen" vs "vorschlagen") leads to different behavior. Be explicit: "propose content, do not write files" or "create the file directly."
3. **Shell/User assumptions** — Agents may hallucinate shell (zsh instead of fish) or path contents. Always validate with actual `ls` or `find` in the parent.
4. **Verification independence** — The verification script runs in a fresh process and should require no special dependencies (pure Python 3, no external packages beyond stdlib).
5. **Hidden directories are NOT clutter** — `.cache/`, `.config/`, `.local/`, `.steam/`, `.ollama/` etc. are system-relevant. Explicitly tell agents not to classify these as clutter.

## Queen-Bee Adaptation

Adapt the queen-bee model from `multi-agent-orchestration`:

| Role | Model | Cost | Task |
|------|-------|------|------|
| **Queen** (parent) | Strong (DeepSeek V4, Claude) | Paid | Strategy, context, synthesis, file writes |
| **Scouts** (4 sub-agents) | Cheap/free (Owl Alpha) | Free/Low | Independent exploration + drafting |
| **Verifier** | Script (`no_agent=True`) | None | Integrity checks on final artifacts |

## Risk Categories for Control Agent

| Category | What to Flag |
|----------|-------------|
| **Destructive** | Any proposal to delete, rename, move, or overwrite user files |
| **Inconsistent** | Conflicting folder purposes between README/Description/Nav |
| **Hallucinated** | Paths or directories claimed but not verified to exist |
| **Scope creep** | Proposals that would require restructuring user data |
| **Naming conflict** | Multiple files with the same name serving different levels (e.g. 3x `NAVIGATION.md`) |
| **Retention gap** | Marking temp/log/results as "safe to delete" without retention policy |

## Verification Script Template

```python
#!/usr/bin/env python3
"""Ad-hoc verification — all required files exist, have content, pass basic checks"""
from pathlib import Path
home = Path.home()
requires = ["README.md", "NAVIGATION.md", ...]
for f in requires:
    p = home / f
    assert p.exists(), f"Missing: {f}"
    assert p.stat().st_size > 50, f"Empty: {f}"
# Plus content checks, duplicate checks, cross-ref checks
```

Write to `/tmp/hermes-verify-{topic}.py`, run, clean up.