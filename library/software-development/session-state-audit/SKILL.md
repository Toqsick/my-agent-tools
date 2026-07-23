---
name: session-state-audit
title: Session-Pause Audit Workflow (4-Phase Gate-Mode)
description: "Use when a session is paused mid-work, a component changed across sessions, or the user asks for a structured audit or clean handoff before resuming. NOT for a fresh-session plan or ordinary bug debugging. Reconstructs state, re-tests claims, evaluates four audit axes, and writes a human-readable and machine-queryable handover."
triggers:
- User says "Audit", "Review the conversation", or invokes Gate/Worker/DMZ-Pattern
  explicitly
- Session ends mid-debug or mid-feature with an unresolved state
- Component has been touched multiple times and current state is unclear
- A future session needs to resume work without re-deriving the full context
version: 1.0.0
author: Hermes Agent
lane: koenigin
reasoning_effort: xhigh
license: MIT
trigger_keywords: ['session', 'audit', 'paused', 'work', 'component']
keywords: ['session', 'audit', 'paused', 'work', 'component']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['ui-component-library']
---


# Session-Pause Audit Workflow

When a session is paused mid-work and a future session needs to resume cleanly, this 4-phase audit pattern produces a handover document that is **both** human-readable (Markdown) and machine-queryable (Mnemosyne-tagged JSON).

## When to use

- Session paused mid-debug with no clean exit
- Component has been modified across multiple sessions and current state is unclear
- User explicitly asks for "Audit", "Gate review", or invokes a structured pattern (Queen/Worker/Gate, DMZ, etc.)
- A future session needs to resume work without re-deriving the full context

## When NOT to use

- Clean session exit with no unresolved state → just write a normal summary
- Trivial 1-file change → normal `system-documentation` skill is enough
- Active development in progress → finish the work first, audit later

## The 4 Phases (strict sequence)

### Phase 1 — Reconstruction

**Goal:** Understand what happened in the previous session(s), what state the system is in NOW, and what hypotheses have already been tested.

Steps:
1. Check live state (`ps`, port-listeners, last-modified files, server health endpoint)
2. Recall prior context via `mnemosyne_recall` or `session_search`
3. List existing docs in `~/docs/system/` for the component
4. Reconstruct the timeline from console-output snippets, server logs, Mnemosyne

**Output:** A reconstruction paragraph or bullet list. NO new fixes.

### Phase 2 — Re-Test

**Goal:** Reproduce the issue or verify the current state, with explicit isolation.

Steps:
1. Identify the **real** endpoints (don't trust your memory — `grep -rn` the route definitions)
2. Test against the actual server (curl with the right token)
3. If rate-limited, wait for cooldown OR use a separate test endpoint (don't work around the limit by code changes — that's a Phase 3 audit finding)
4. For each test, record: timestamp, expected, actual, pass/fail

**Pitfalls:**
- Don't curl endpoints that don't exist (Phase 2 false-positive trap). Verify route definitions FIRST.
- Don't trigger additional rate-limit pressure during re-tests.
- Mark unverifizierte hypotheses as "unverifiziert" — don't claim them.

**Output:** A test log. NO new fixes.

### Phase 3 — Audit (4-axis evaluation)

**Goal:** Categorize findings, not fix them.

Evaluate each of these axes:
- **Security** — auth gates, header/query token handling, CSP, browser-extension noise (note as separate from real issues)
- **Stability** — rate-limit behavior, reconnect logic, network-flap handling, multi-client
- **DMZ-Pattern-Compliance** — does the component respect the layered architecture? (only if relevant)
- **Performance** — event frequency, payload size, backpressure, buffer sizes

For each axis, classify as: `ok`, `warn`, `fail`. Cite specific test results.

**Output:** A 4-line summary. NO new fixes.

### Phase 4 — Documentation

**Goal:** Produce TWO artifacts that together give the next session full context:

1. **Markdown file** at `~/docs/system/<component>-<audit-type>-<YYYY-MM-DD>.md`
2. **Mnemosyne memory** with a stable tag like `hermes-v7/<component>/audit/<YYYY-MM-DD>`

Both must contain:
- **Summary** (2-3 sentences: state + what was checked)
- **Root cause** (confirmed? unverifiziert? what evidence?)
- **Audit findings** (4-axis summary)
- **Open items** (explicit list, so nothing gets lost)
- **Next steps** (prioritized P0/P1/P2)

Mnemosyne tag must be searchable so the next session can do `mnemosyne_recall(query=<tag>)` and find the full handover.

**Update the README-Index** (`~/docs/system/README.md`) with a link to the new doc.

## Output Format

### Markdown templateately

```markdown
# <Component> — Session-Audit

**Datum:** YYYY-MM-DD
**Agent:** <role>
**Component:** <name> @ <version>
**Mnemosyne-Tag:** <tag>

## Zusammenfassung
<2-3 sentences>

## Root Cause (Phase 1+2)
<confirmed root cause + evidence>

## Audit-Ergebnisse (Phase 3)
- Security: ok | warn | fail
- Stability: ok | warn | fail
- DMZ-Pattern-Compliance: ok | warn | fail
- Performance: ok | warn | fail

## Offene Punkte
<numbered list>

## Nächste Schritte
- P0: <action>
- P1: <action>
- P2: <action>

## Mnemosyne-Status-Block (siehe nächsten Eintrag)
<json block inline>
```

### Mnemosyne template

```python
mnemosyne_remember(
  content="<tag> — <one-paragraph summary of state + findings + next steps>",
  importance=0.85,    # high — handover doc
  scope="global",     # survives session boundary
  source="audit",
  veracity="tool"     # we verified it via tools
)
```

## Common Pitfalls

1. **Doing fixes during audit.** The audit pattern explicitly forbids this. If you find a fix-worthy issue during Phase 3, file it in Open Items and exit the audit. The next session decides.
2. **Trusting memory over tools.** Mnemosyne can be stale. Always verify live state in Phase 1, even if Mnemosyne says "I know this".
3. **Skipping Phase 2 because "we already know what's broken".** The re-test exists to confirm current state. The system may have changed (server restarted, configs drifted).
4. **Forgetting the Mnemosyne tag uniqueness.** Tag must include date. `hermes-v7/sse/audit/2026-06-30` is good. `hermes-v7/sse/audit` is bad — collides with future audits.
5. **Not updating README-Index.** The handover doc is unfindable without an index entry. Always add a one-line link.

## See also

- `system-documentation` — for general repo-doc maintenance (CHANGELOG, ROADMAP)
- `sse-frontend-patterns` — example of a domain-specific skill (real-time web dashboards) that audit findings may produce