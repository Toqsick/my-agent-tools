---
name: swarm-router
description: >-
  Use when user asks for routing a multi-agent request, handling a /swarm command, choosing between inline, scout, pipeline, or parallel modes, or audit-logging a dispatch decision. NOT for single-worker tasks under thirty seconds or pure plan writing. Classifies intent, dependency shape, cost, and failure risk to select the correct Hermes swarm primitive and recovery path.
version: 1.0.0
author: Hermes Agent (hermes-v2 plan, H-40, 2026-07-20)
license: MIT
platforms:
  - linux
  - macos
metadata:
  hermes:
    tags: ['swarm', 'routing', 'delegation', 'orchestration', 'consensus', 'hermes-v2']
    related_skills:
      - delegation
      - queen-bee-schwarm-dispatch
      - multi-agent-work
      - kanban-system-health
      - coding-pipeline-orchestrator
      - writing-plans
      - critic-gate
lane: koenigin
reasoning_effort: xhigh
agent: Orchestrator
routing_hint: |
  **Agent-Scope:** Routing work to the right multi-agent primitive.
  Off-scope: single-worker tasks, planning, pipeline orchestration.
trigger_keywords: ['swarm', 'and', 'swarm-router', 'routing', 'multi-agent']
keywords: ['swarm', 'user', 'asks', 'routing', 'multi']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['hybrid-swarm-evaluation', 'multi-agent-cluster-patterns', 'fable-orchestration-pattern']
---

# Swarm Router (hermes-v2, H-40)

Single entry point for "I want multiple agents on this". Reads the
request, classifies it against four routing modes, and dispatches
via the right primitive. Replaces the pattern of "operator knows
which subagent API to call" with "operator flips the front door;
router picks the primitive".

## When to Use

Load this skill when ANY of these signals is present in the
operator's request:

- Phrases like "do X with multiple agents", "/swarm", "in parallel",
  "fan out", "consensus", "with proper code review".
- A request that smells like more than a single worker can handle
  (multi-hour, multi-subsystem, crash-recoverable, verifier-gated).
- A dispatch decision the operator wants audit-logged in
  `hermes logs`.

**Off-scope (do not route):**

- Single-worker tasks — just do them inline.
- Pure planning — use `writing-plans` / `/plan <intent>`.
- Pipeline orchestration specifics — use
  `coding-pipeline-orchestrator`.
- Trivial CLI queries (<30 s, deterministic) — inline.

## Quick Start

1. **Flip the front door** — operator sends `/swarm on`. Current
   `/swarm` semantics only accept `on | off | status`; the router
   reads that gate state, not a free-form intent string.
2. **Operator states the work** — describe the task in plain
   language. The router applies the decision matrix
   (next section) and picks exactly one mode.
3. **Operator confirms the classification trace** — the router
   emits one line, e.g. `swarm-router: classify(kanban-swarm) →
   board=hermes-v2, root+5 children`. If the operator disagrees,
   cancel/archive the spawned board and re-classify.
4. **Dispatch via the chosen primitive** — only one of:
   - `delegate_task(tasks=[...])` for parallel-reads
   - `hermes kanban swarm --worker ... --verifier ... --synthesizer ...` for kanban-swarm
   - `hermes kanban create` chained with `skill_lanes` for persona-pipeline
   - `/moa <prompt>` (after `hermes moa configure` sets the slots) for MoA-consensus
5. **Verify** — see "Verification / Acceptance" below.

## Routing Modes

| Mode | When | Primitive | Cost |
|---|---|---|---|
| **parallel-reads** | Multiple independent read-only inspections; no shared state; one-shot results | `delegate_task(tasks=[...])` | Lowest (no claim/heartbeat overhead) |
| **kanban-swarm** | Long-running, multi-step, retry-eligible, observable; needs crash recovery | `hermes kanban swarm --worker P:TITLE[:SKILL,SKILL] ...` (repeat `--worker` per parallel card) | Medium (DB rows + heartbeats) |
| **persona-pipeline** | Sequential specialist handoff; each step has a focused role and a verifier | `hermes kanban create` chained with `skill_lanes` | Medium (sequential, no parallel speedup) |
| **MoA-consensus** | Multi-perspective deliberation on a single decision; outputs are aggregated | `/moa <prompt>` after `hermes moa configure` (sets slots; no `--preset` flag) | High (multiple LLM calls per turn) |

Plus two "do not swarm" options:

| Mode | When | Action |
|---|---|---|
| **trivial** | One-step work; single worker suffices | Just do it. Don't route. |
| **plan-first** | Multi-step but unclear; better as a plan than a swarm | `/plan <intent>` → `/plan approve` → kanban seed → kanban-swarm (loop back to kanban-swarm row) |

> **Betriebshinweis — welches Modell fährt ein Kanban-Swarm? (2026-07-21)** Ein `kanban-swarm` läuft **nur dann** auf M3/GLM, wenn die Worker-/Verifier-/Synthesizer-**Profile** darauf zeigen. Die Router-Defaults in `swarm_routing.py` sind generische Assignee-Namen (`worker`/`reviewer`/`writer`), die **nicht** auf die `yuno-*`-Profile aus `skill_lanes` mappen. Um M3/GLM zu treffen, entweder `swarm.kanban_worker_profile`/`kanban_verifier`/`kanban_synthesizer` auf `yuno-*`-Profile setzen **oder** in den `--worker P:TITLE`-Specs das Profil `P` explizit als `yuno-vision` (M3) / `yuno-coder` (GLM) angeben. Das Modell selbst kommt aus dem Profil (Assignee→Profil→config), **nie** aus dem Swarm-Primitive. Lane→Modell = `skill_lanes` (Source of Truth). *(Der Router flippt außerdem nie ein bestehendes Board auf `dispatchable` — P-71.)*

## Decision Matrix

Apply in order; first match wins:

```
1. Is the work a single-step task (one read, one edit, one shell)?
   → trivial: just do it.

2. Does the work require crash recovery / heartbeats / claim-locks?
   (e.g. "runs over hours", "may need retries", "operator may
   pause mid-task")
   → kanban-swarm

3. Is the work "get N independent opinions, then pick"?
   (e.g. "what's the best approach to X", "should we use Y or Z")
   → MoA-consensus (configure MoA slots first; invoke via /moa)

4. Does the work require sequential specialist handoff?
   (e.g. "draft → review → fix", "research → implement → verify")
   → persona-pipeline (kanban tasks with skill_lanes)

5. Is the work "run N identical tasks in parallel, each writes its
   own output"?
   (e.g. "scan all these files for X", "scrape these URLs")
   → parallel-reads (delegate_task batch)

6. None of the above fit cleanly?
   → plan-first: route to /plan on, write a structured plan,
     /plan approve → kanban seed → kanban-swarm (loop back to 2).
```

The matrix is intentionally **strict** — false positives (routing
to swarm when work was trivial) waste cycles; false negatives
(routing to trivial when work needed swarm) are recoverable by
the operator re-asking. Prefer false negatives.

## Cost Gate

Before dispatching, check the cost gate:

- **Is the work > 5 minutes of single-worker time?** If not,
  parallel-reads is overkill; do it inline.
- **Is the work parallelisable?** If there's a strict sequential
  dependency between every step, parallel-reads gives no
  speedup — use persona-pipeline.
- **Are N workers likely to find N distinct outputs?** MoA-consensus
  degrades if all workers converge on the same answer; only
  invoke when perspectives genuinely differ.

If the cost gate fails, fall through to "trivial" or "plan-first".

## Anti-Patterns Absorbed from `delegation-anti-patterns`

The hermes catalog exposes **18** delegation anti-patterns. Not all
of them are routing decisions — some live in the briefing layer
(prompt wording, file scope text, self-test blocks), some in the
post-dispatch verification layer (rebase, commit discipline), and
some are subagent-engine quirks (Claude `--bare` flag, reasoning-
effort FP-flood). The router **only absorbs the routing-relevant
subset**; the rest must be handled by the operator at briefing
or verification time.

This skill maps the 10 patterns that are genuinely routing
decisions. The remaining 8 are listed at the bottom as
"NOT routing concerns" so operators know to handle them
elsewhere.

| # | Anti-pattern | Router's response |
|---|---|---|
| #1 | Parallel-Scout + Fixer funktioniert NICHT | Router refuses "scout then fix" as two parallel batches — routes to kanban-swarm with serial stages, or single-fan-out (decision matrix step 4 / 5) |
| #4 | Race-Condition auf gemeinsamen Working-Tree | Native `hermes kanban swarm` uses scratch/runtime defaults; it exposes no `--workspace` option |
| #5 | Verifikations-Pfad muss MANDATORY sein | Kanban-swarm mandates `--verifier` and `--synthesizer`; router refuses kanban-swarm without both |
| #6 | "NICHT anfassen" Barrier-Constraint | Each kanban task body must declare its scope + NOT-list; router requires it in the body before dispatch |
| #7 | Independent Verification (queen-audit) | Kanban-swarm's verifier-step reads files; cross-ref to `worker-failure-discipline` |
| #9 | Cooperative Coverage Gap — pre-dispatch baseline | Router pre-flight asks "is baseline CI green?" before classifying as kanban-swarm |
| #13 | Subagent Root-Cause Right, Trigger Wrong | Router output marks verifier results as `needs-trigger-repro`; operator must rerun the trigger themselves |
| #14 | Cross-Agent File Destruction | Worktree isolation requires project/task workspace configuration outside the `kanban swarm` flags; the router does not create it automatically |
| #15 | Delegation Threshold — Cost-Benefit | Cost gate blocks this entirely |
| #18 | Circular Test-Implementation Loop | Router requires a real-distribution audit before accepting a worker that delivered both code + tests |

Workspace choice is therefore a project/operator configuration decision.
Use the native scratch/runtime defaults unless persistent `dir` or
`worktree` isolation has been configured at the project/task workspace
layer before dispatch; workspace isolation is not a swarm flag or an
automatic router effect.

**NOT routing concerns** (handle in briefing or post-verify):
#2 reasoning-effort FP-flood, #3 prompt length, #8 Claude `--bare`
flag, #10 intra-pattern file-affinity, #11 report-sentinel write
timing, #12 pre-push mergeable check, #16 worker self-commit/push,
#17 coverage-ausschluss. See `delegation-anti-patterns` for the
full text and mitigations.

## `/swarm` Slash Command (hermes-v2 Front-Door)

The kimi-mode plugin's `/swarm` is the **gate**, not the router.
Current syntax accepts only:

```bash
/swarm on       # enable the swarm router front door
/swarm off      # disable it
/swarm status   # show current gate state
```

The router is **not** invoked by free-form intent. Once `/swarm on`
is active, the operator states the work in plain language and the
router (a downstream component) classifies + dispatches via the
chosen primitive. The router then returns a one-line
classification trace:

```
swarm-router: classify(parallel-reads) → 5 workers, batch, ~2 min
swarm-router: classify(kanban-swarm)   → board=hermes-v2, root+5 children
swarm-router: classify(persona-pipeline)→ chain: researcher → coder → verifier
swarm-router: classify(MoA-consensus)  → /moa prompt; slots set via `hermes moa configure`
swarm-router: classify(plan-first)      → use /plan on <intent>, then /plan approve
swarm-router: classify(trivial)        → just do it; not routed
```

The operator sees the classification before any worker spawns.

## Router Anti-Patterns

| Anti-pattern | Why it's rejected |
|---|---|
| Auto-classifying ambiguous requests as kanban-swarm | False positives waste cycles; kanban-swarm is the heaviest mode |
| Bypassing the cost gate for "urgent" requests | Urgency amplifies wasted work; the gate is what prevents 5-min tasks from becoming 20-min swarms |
| Routing to MoA-consensus when one perspective suffices | MoA is multi-LLM-per-turn; expensive and slow for no benefit |
| Treating every `/swarm` invocation as a new board | Boards accumulate; reuse the existing board unless task type changes |
| Routing to persona-pipeline when no verifier exists | A pipeline without a verifier is just sequential work; use kanban-swarm instead so the dispatcher enforces order |
| Inventing MoA invocation syntax (`moa run --preset ...`) | No such flag exists; `hermes moa` is configuration-only. Use `/moa <prompt>` after `hermes moa configure` |

## Worked Examples

**Operator:** "Read the 5 READMEs in our orgs/ directory and summarize the project layout."

- Step 1: Multi-step? No (5 reads in parallel).
- Step 5: "N identical tasks, parallel" → **parallel-reads** with
  5 workers, batch.

**Operator:** "Build feature X with proper code review."

- Step 1: Multi-step? Yes.
- Step 2: Multi-hour? Likely. Crash-recovery needed.
- → **kanban-swarm** via `hermes kanban swarm --worker coder:impl:skill_a
  --worker coder:impl:skill_b --verifier reviewer --synthesizer writer ...`

**Operator:** "What's the best way to implement auth — JWT, sessions, or OAuth?"

- Step 1: Multi-step? No, single decision.
- Step 3: "Best approach to X" → **MoA-consensus** via `/moa <prompt>`
  after `hermes moa configure` has set 3 reference slots + 1 aggregator.

**Operator:** "Refactor the auth flow to use JWT."

- Step 1: Multi-step? Yes.
- Step 6: Doesn't fit cleanly → **plan-first**: `/plan on`,
  write plan, `/plan approve` → kanban seed → kanban-swarm.

**Operator:** "Restart the gateway."

- Step 1: Single-step → **trivial**: just do it.

## Verification / Acceptance

A routing decision is "correct" iff:

1. The classification trace appears in the operator-visible output.
2. The chosen mode's primitive is invoked, not a different one
   (e.g. `hermes kanban swarm ...` for kanban-swarm, NOT `delegate_task`
   for long-running work).
3. Cost gate was applied (visible from the dispatch trace).
4. The board slug is explicit for kanban-swarm (no implicit default).
5. Output of the dispatched work is observable by the operator
   (webui for kanban, task results for parallel, MoA transcript for
   MoA).

A misclassification is recoverable: the operator can `archive`
the kanban tasks, abort the parallel batch via the delegate_task
handle, or skip the MoA round and pick from the reference outputs
directly. The router logs the routing decision in `hermes logs`
for audit.

## Failure Recovery / Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `/swarm on` returns "unknown subcommand" | `/swarm` plugin not loaded or version drift | Re-load the kimi-mode plugin; confirm `/swarm status` works |
| Router classifies as kanban-swarm but no board exists | Operator skipped `--board`; `hermes kanban init` not run | `hermes kanban --board <slug> init`, then re-dispatch with explicit `--board` |
| MoA-consensus route delivers identical outputs | Perspectives not actually distinct (cost-gate fail) | Drop to single-perspective, or restructure prompts to force diversity |
| Kanban-swarm verifier approves without reading files | Worker skipped self-audit (worker-failure-discipline #1) | Operator re-runs the verifier task with explicit read-before-approve mandate; cross-ref `worker-failure-discipline` |
| Worker self-committed and pushed without authorization | Briefing-Pitfall #16 not blocked at router level | Router cannot prevent this — handle in briefing; commit only after explicit human release |
| Router classifies "trivial" but operator insists on swarm | Cost-gate false negative | Override manually via the explicit primitive; do not change the matrix |

## Related Skills and References

- **`coding-pipeline-orchestrator`** (H-31): pipeline-spawn
  script is the dispatcher when kanban-swarm needs a
  `workflow_template_id=coding-pipeline` template. The router
  classifies; the orchestrator runs the canonical pipeline.
  Note: `spawn_pipeline.py` only builds the task graph (root +
  children); the orchestrator's convention-based sequencer and
  review reactions drive the run. H-53 will automate the
  sequencer end-to-end; until then, manual review reactions
  remain the source of truth.
- **`multi-agent-work`** (existing): handles the "persona pipeline"
  details (specialist handoff prompts, lane assignments).
- **`delegation`** (existing): the underlying `delegate_task`
  primitive for parallel-reads.
- **`queen-bee-schwarm-dispatch`** (existing, being absorbed): the
  router's kanban-swarm mode subsumes this skill's behaviour with
  the structured kanban pipeline.
- **`delegation-anti-patterns`**: full list of all 18 anti-patterns;
  this skill maps the routing-relevant subset and points operators
  to the briefing/post-verify layers for the rest.
- **`worker-failure-discipline`**: cross-reference for #7 (queen-
  audit) and #18 (circular test loop) — both depend on the worker
  self-test protocol.
