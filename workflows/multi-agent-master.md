---
id: multi-agent-master
name: Multi-agent master (fan-out → synthesis)
when_to_use: A task with several independent facets that benefit from parallel specialist lenses converging into one synthesized result.
agents: [zc-general, zc-gate]
skills:
  - multi-agent-master-workflow
  - queen-bee-schwarm-dispatch
  - yuno-team-orchestrator
  - yuno-team-routing
phases:
  - phase: Decompose
    owner_agent: zc-general
    skills: [yuno-team-routing, multi-agent-master-workflow]
    exit_criteria: Task split into orthogonal sub-tasks, each with an owner lens and acceptance criteria.
    failure_modes: Overlapping sub-tasks that duplicate work or race on the same files.
  - phase: Fan-out (parallel lenses)
    owner_agent: zc-general
    skills: [queen-bee-schwarm-dispatch, yuno-team-orchestrator]
    exit_criteria: Independent agents run concurrently, each blind to the others, returning structured findings.
    failure_modes: Shared mutable state across parallel workers; context bleed.
  - phase: Synthesize
    owner_agent: zc-general
    skills: [multi-agent-master-workflow]
    exit_criteria: Findings deduped and merged into one coherent result.
    failure_modes: Concatenating outputs instead of reconciling them.
  - phase: Gate
    owner_agent: zc-gate
    skills: []
    exit_criteria: Independent PASS / RETRY / BLOCK on the synthesized result.
    failure_modes: Accepting the synthesis without an adversarial check.
---

# Multi-agent master (fan-out → synthesis)

**Decompose → Fan-out → Synthesize → Gate.** A master controller splits work into orthogonal lenses,
runs them in parallel (each independent), then reconciles into one result behind an independent gate.
Uses `multi-agent-master-workflow` and `queen-bee-schwarm-dispatch` (installed), with `yuno-team-*`
for routing/orchestration decisions.

**Route in:** "orchestrate / parallel audit / multiple perspectives / decompose this." Use only when
sub-tasks are genuinely independent — otherwise a single-agent workflow is cheaper and safer.
