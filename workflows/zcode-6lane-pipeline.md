---
id: zcode-6lane-pipeline
name: ZCode 6-lane subagent swarm
when_to_use: Large or cross-cutting implementation/debug work worth decomposing across a staged multi-agent swarm with an independent quality gate.
agents: [zc-general, zc-vision, zc-coder, zc-debug, zc-verify, zc-gate, zc-impact, zc-changeset, zc-patch, zc-selftest, zc-repro, zc-trace, zc-hypothesis, zc-fixvalidate]
skills: [zcode-subagent-team]
phases:
  - phase: General (research + plan)
    owner_agent: zc-general
    skills: [zcode-subagent-team]
    exit_criteria: Context gathered, task decomposed into work packages with a plan.
    failure_modes: Planning without reading the affected code first.
  - phase: Vision (optional)
    owner_agent: zc-vision
    skills: []
    exit_criteria: Any UI/screenshot/diagram/code-diff-as-image finding is captured before coding.
    failure_modes: Skipping a visual check when the task is visual.
  - phase: Coder (implement)
    owner_agent: zc-coder
    skills: []
    exit_criteria: Minimal change-set implemented in isolated patches (zc-impact → zc-changeset → zc-patch → zc-selftest).
    failure_modes: Writing beyond the approved change-set; no self-test.
  - phase: Debug (conditional)
    owner_agent: zc-debug
    skills: []
    exit_criteria: On NEEDS_DEBUG, root cause found via zc-repro → zc-trace → zc-hypothesis → zc-fixvalidate.
    failure_modes: Spawned as a guess rather than on a real failure signal.
  - phase: Verify (7 checks)
    owner_agent: zc-verify
    skills: []
    exit_criteria: Syntax, tests, lint, types, diff-review, security quick-check, regression all pass.
    failure_modes: Changing logic during verification.
  - phase: Quality Gate
    owner_agent: zc-gate
    skills: []
    exit_criteria: Independent PASS / RETRY / BLOCK decision with scored justification.
    failure_modes: Gate acting as first reviewer instead of final arbiter.
---

# ZCode 6-lane subagent swarm

A Hermes-Kanban orchestrator: a Queen (orchestrator/verifier) delegates bulk work to workers across
six lanes — **General → Vision → Coder → Debug → Verify → Quality Gate** — with micro-workers feeding
the coder and debug leads. Heavier than [`superpower-10x-pipeline`](superpower-10x-pipeline.md); use it
when the work genuinely benefits from parallel decomposition and an independent gate.

**Route in:** "orchestrate / swarm / large refactor / multi-file feature with review." The
`zcode-subagent-team` skill documents the runtime, profiles, and the Hermes-CLI reality corrections;
the `zc-*` agents are the lanes and micro-workers.
