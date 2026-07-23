---

name: agent-config-refactoring
description: Use when user asks for agent config refactoring, Agent Configuration Refactoring, When to Use, The 6-Phase Pipeline. NOT for unrelated tasks, simple questions. Refactors agent configuration files using a 6-phase extraction pipeline.
version: 1.0.0
author: Yuno (from MaxClaw v3.0 upgrade session)
license: MIT
platforms:
- linux
- macos
metadata:
  hermes:
    category: software-development
    tags:
    - agent-config
    - refactoring
    - code-analysis
    - best-practices
    - pattern-mining
    - configuration
    - quality-gates
trigger_keywords: ['agent', 'refactoring', 'configuration', 'phase', 'pipeline']
keywords: ['agent', 'refactoring', 'configuration', 'phase', 'pipeline']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['hermes-long-run-template', 'the-dmz-transfer']
---



# Agent Configuration Refactoring

## When to Use

Load this skill when you need to:
- Upgrade an agent's IDENTITY/AGENTS/TOOLS/MEMORY/HEARTBEAT/config files
- Mine existing code artifacts (scripts, tools, libraries) for best practices to embed in agent config
- Create a validated, structured config with quality gates
- Produce a changelog that justifies every change with evidence from real code

**Do NOT load when:**
- Just tweaking one field in config.yaml (use `patch` directly)
- Writing a new agent from scratch with no existing artifacts to mine
- Only doing session documentation (use `system-documentation` instead)

## The 6-Phase Pipeline

### Phase 1: Artifact Inventory

**Goal:** Know exactly what you're working with — size, scope, and shape of all source artifacts.

Steps:
1. **Find all source files** — `search_files(target='files', pattern='*.src')`, or `find` in the source directory
2. **Measure metrics per file**:
   - Line count (`wc -l`)
   - Byte count (`wc -c`)
   - Language/type if mixed
3. **Compute aggregate metrics**:
   - Total files, total LoC
   - Mean/median/max/min line counts
   - Coverage (are all expected files accounted for?)
4. **Extract builtin frequency** if GreyScript:
   ```bash
   grep -hoE '\b[a-z_][a-z_0-9]*\b' *.src | sort | uniq -c | sort -rn | head -30
   ```
5. **Identify header patterns** — check for `//command:`, `// ====`, `// ---` markers

**Output:** A table with per-file metrics and an aggregate stats block. NO changes to anything yet.

### Phase 2: Pattern Extraction

**Goal:** Categorize every code pattern as "works" or "breaks" with concrete examples from the artifacts.

Steps:
1. **Read key scripts** — start with the largest/most complex ones (they show the most patterns)
2. **Read outliers** — the smallest scripts (25-50 LoC) show minimal patterns
3. **For each script, extract**:
   - Library loading pattern (e.g., `include_lib` + null check)
   - Control flow pattern (loops, conditionals, arg parsing)
   - String construction pattern (e.g., `char(10)` for newlines)
   - Error handling pattern
   - Connection/auth pattern
4. **Cross-reference** — which patterns appear in multiple scripts? Those are the "proven" ones.
5. **Check against known bugs** — which patterns are known to fail in the specific build toolchain?
   - For GreyScript: `else if`, Einzeiler-if, inline-if all fail without `-u` flag
   - Check `greyscript-compiler-debugging` skill for current bug catalog
6. **Organize into**:
   - **Working Patterns** with code examples AND source references
   - **Broken Patterns** with code examples, failure mode, AND workaround
   - **Reusable Code Idioms** — blocks that get copy-pasted because GreyScript has no functions

**Output:** A structured pattern catalog (save as `references/<date>-pattern-catalog.md` in the skill). NO changes to target files yet.

### Phase 3: File-by-File Refactoring

**Goal:** Upgrade each agent file with the extracted patterns. Work in logical order — each file builds on the previous.

**Standard order:**
1. **IDENTITY.md** — What is this agent? Start with core competencies derived from artifacts.
   - Add: Role, creature type, core competencies, what the agent is NOT (negatives), session identity
   - Reference: what the source scripts actually do (real work, not imagined capabilities)
2. **AGENTS.md** — How does this agent work?
   - Add: Multi-agent structure, task-specific rules, build pipeline, lifecycle management
   - Reference: the actual mission/operation flow from source scripts
3. **TOOLS.md** — What tools and syntax does this agent use?
   - Add: Syntax rule table, tool catalog, reusable code idioms, correct/incorrect examples
   - Reference: extracted working/broken patterns
4. **MEMORY.md** — What should persist across sessions?
   - Add: Structured sections for active missions, mission logs, tool registry, build errors, NPC intel, DB snapshots
   - Reference: actual mission targets, tool names, build commands from scripts
5. **HEARTBEAT.md** — What should be periodically checked?
   - Add: Heavy vs cheap task separation, mission stale detection, build rotation, cron workflow references
   - Reference: what needs periodic attention based on actual operations
6. **config.yaml** — What are the hard security/mode boundaries?
   - Add: Allow/deny lists from actual tool usage, sandbox paths, confirmation gates, dedicated domain-specific block
   - Reference: every `deny` entry justified by a real script's possible action

**For each file, document:**
- Old to New structure (what was there vs what's there now)
- Key insertions (what changed and why)
- Artifact reference (which specific script informed each change)
- Approximate line/byte counts

**Output:** 6 modified files, each with an explicit diff rationale. NO skipping — every file gets refactored.

### Phase 4: Validator Creation

**Goal:** Create a re-runnable validator script that checks all critical config invariants.

Structure:
```bash
#!/bin/bash
# config-check.sh

CONFIG="config/config.yaml"

# Per-section checks with clear pass/fail
# 1. Default-Deny Philosophy
# 2. Git-Push-Schutz
# 3. Domain-specific Build Config
# 4. Sandbox Config
# 5. Domain-specific Block Enabled
# 6. Model-Routing (cheap heartbeat + heavy defined)
# 7. Write-Paths
# 8. Browser-Schutz
# 9. Bestaetigungspflichten (HITL)
```

**Each check must:**
- Print `[OK]` on pass, `[FAIL]` on fail
- Show the actual value vs expected value
- Be self-contained (no external deps beyond `yq` or `python3 -c "import yaml"`)

**Parser fallback chain:** `yq` then `python3 yaml`, grep as last resort only.

**Exit codes:** 0 = all pass, 1 = critical errors, 2 = warnings only.

**Output:** A standalone shell script at `~/bin/<name>-config-check.sh`.

### Phase 5: Validation

**Goal:** Run the validator and fix everything until it's green.

1. **Run the validator**
2. **For each failure:**
   - Is the config actually wrong? Fix it.
   - Is the validator too strict? Adjust the check.
   - Is the parser fallback wrong? Fix the check script.
3. **Re-run after each fix batch**
4. **Only stop when 0 errors, 0 warnings**

**Output:** Final validator run output showing all checks green.

### Phase 6: Changelog Documentation

**Goal:** A standalone changelog that justifies every change with evidence from the artifacts.

Structure:
```
# Agent Upgrade <YYYY-MM-DD> — v<N> → v<N+1>

## TL;DR (table: file, before, after, delta)

## 1. Analysis Basis (artifact metrics + pattern summary)

## 2. Changes per File (diff rationale — what changed and why)

## 3. New Files (validator script, changelog itself)

## 4. Validation Output

## 5. Deliberately NOT Changed (conservative decisions)

## 6. Recommended Next Steps
```

**Each file entry must show:**
- Old size vs new size
- What was inserted (not just "refactored")
- Why (reference to which artifacts/patterns drove the change)
- Artifact reference (specific scripts, line numbers where possible)

**Output:** `<AGENT-UPGRADE-YYYY-MM-DD.md>` alongside the agent config files.

## User Preference Embedding

After refactoring, check for signals in the conversation:
- Did the user correct any style choice? Embed in SKILL.md as a pitfall.
- Did the user express a format preference? Embed as a rule.
- Did a pattern from the artifacts not survive the validator? Document the edge case.

**Don't guess user preferences** — only embed what was actually expressed or demonstrated.

## Anti-Patterns

- **Don't write theory-only sections.** Every change must reference a real artifact or known bug.
- **Don't skip the validator.** Config changes without validation gates will drift.
- **Don't refactor files in random order.** IDENTITY, AGENTS, TOOLS, MEMORY, HEARTBEAT, config.yaml builds dependencies correctly.
- **Don't put session-specific data** (specific IPs, PR numbers, temporary states) into the skill. Those go into the changelog.
- **Don't add `//command:` to scripts that use DB injection.** The `//command:` header is only needed for scripts built with `greybel build`.
- **Don't claim a pattern is "proven" from 1-2 occurrences.** Require at least 3 scripts.

## Verification

After completing all 6 phases:

```bash
# 1. All files exist?
for f in agent/IDENTITY.md agent/AGENTS.md agent/TOOLS.md agent/MEMORY.md agent/HEARTBEAT.md config/config.yaml; do
  [ -f "$f" ] && echo "OK $f" || echo "MISSING $f"
done

# 2. Validator green?
~/bin/*-config-check.sh

# 3. YAML syntax valid?
python3 -c "import yaml; yaml.safe_load(open('config/config.yaml')); print('OK YAML valid')"

# 4. Changelog exists?
[ -f "AGENT-UPGRADE-*.md" ] && echo "OK Changelog exists" || echo "MISSING Changelog"
```

## Related Skills

- `system-documentation` — for general post-hoc documentation; use that for one-off changes, this skill for full agent refactoring
- `greyscript-compiler-debugging` — GreyScript-specific compiler bugs and pattern catalog (load in Phase 2)
- `session-state-audit` — for pausing mid-session; different goal (preservation vs transformation)
- `skill-library-maintenance` — for managing the skill library itself, not agent configs
