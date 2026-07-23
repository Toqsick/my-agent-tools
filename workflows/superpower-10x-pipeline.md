---
id: superpower-10x-pipeline
name: Superpower-10x development pipeline
when_to_use: Building, extending, or debugging software where quality matters — the default end-to-end coding workflow.
agents: [zc-general, zc-coder, zc-debug, zc-verify, zc-gate]
skills:
  - superpowers-brainstorming
  - superpowers-writing-plans
  - superpowers-subagent-driven-development
  - superpowers-test-driven-development
  - superpowers-systematic-debugging
  - superpowers-verification-before-completion
  - superpowers-finishing-a-development-branch
  - superpower-10x
phases:
  - phase: Brainstorm
    owner_agent: zc-general
    skills: [superpowers-brainstorming]
    exit_criteria: Intent, constraints, and a chosen approach are written down and user-approved.
    failure_modes: Jumping to code before the problem is understood; unstated assumptions.
  - phase: Plan
    owner_agent: zc-general
    skills: [superpowers-writing-plans]
    exit_criteria: A bite-sized, verifiable task list with file paths exists.
    failure_modes: Tasks too coarse to verify; missing spec references.
  - phase: Execute (TDD)
    owner_agent: zc-coder
    skills: [superpowers-test-driven-development, superpowers-subagent-driven-development]
    exit_criteria: Each task lands red→green→refactor with a passing test.
    failure_modes: Code before test; batching unrelated changes.
  - phase: Debug
    owner_agent: zc-debug
    skills: [superpowers-systematic-debugging]
    exit_criteria: Any failure is root-caused (not patched at the symptom) and re-verified.
    failure_modes: Guess-and-check fixes that mask the real cause.
  - phase: Verify & finish
    owner_agent: zc-verify
    skills: [superpowers-verification-before-completion, superpowers-finishing-a-development-branch]
    exit_criteria: Tests/lint/types pass; branch closed out cleanly; done is proven, not assumed.
    failure_modes: Declaring done without running the checks.
---

# Superpower-10x development pipeline

The canonical build workflow: **Brainstorm → Plan → Execute (TDD) → Debug → Verify & finish**.
Amplifies a coding agent through enforced process instead of ad-hoc coding. Pairs the
`superpowers-*` methodology skills (installed) with the ZCode lane agents (`zc-*`) for delegation.

**Route in:** any "build / implement / fix / refactor" task. For a heavier multi-lane swarm, escalate to
[`zcode-6lane-pipeline`](zcode-6lane-pipeline.md).

Each phase has a hard exit criterion — never skip verification regardless of perceived simplicity.
See the `superpower-10x` skill for the automation scripts (plan generator, TDD enforcer, quality gate).
