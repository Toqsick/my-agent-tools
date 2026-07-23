---
name: quality-over-quantity
description: "Choose quality over quantity in artifacts and code."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags:
    - Quality
    - Decision-Framework
    - Skill-Authoring
    - Orchestration
license: MIT
trigger_keywords: ['choose', 'quality', 'over', 'quantity', 'artifacts']
keywords: ['choose', 'quality', 'over', 'quantity', 'artifacts']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

# Quality Over Quantity

A decision principle for when "more" competes with "better". Apply it to skill creation, agent dispatch, documentation, code, and research. It does NOT mean "always go slow" — it means "ship one excellent artifact instead of five mediocre ones, then stop." The stance is stdlib-only: no tools required, just judgment.

## When to Use

- Before saving a skill, memory, or doc: "is this tight and verified, or am I padding?"
- Before dispatching subagents: "2 well-briefed workers or 10 vague ones?"
- When a task grows scope creep: "am I adding value or volume?"
- After receiving review feedback (M3-subagent, critic-gate): fix before shipping, do not hand-wave.
- When tempted to ship a stub, plan, or promise instead of a working artifact.
- When facing "add more features" vs "polish what exists".

## Prerequisites

None. This is a principle, not a script. Pair it with `ki-murks-verhindern` (code quality gates), `critic-gate` (deliverable audit), and `context-diet` (token hygiene) when applying it to concrete work.

## How to Run

Invoke the decision check mentally before any "save / ship / dispatch / publish" action. If the check fails, iterate before proceeding — do not ship and hope.

## Quick Reference

- One excellent artifact beats five mediocre ones.
- Gates green before save: size, frontmatter, description, triggers, walkthrough.
- Fix review findings before shipping, never after.
- Trim bloat: shorter is better when nothing is lost.
- Reject scope creep that adds volume without value.
- A working artifact beats a perfect plan.

## Procedure

1. **Define "done" before starting.** State the artifact, its acceptance criteria, and the quality gates it must pass. Without a done-definition, "more" always feels safer.
2. **Build the smallest thing that meets the criteria.** Not the smallest stub — the smallest complete artifact. Stubs and plans are quantity, not quality.
3. **Run objective quality gates before shipping.**
   - Skills: size 4-7 KB, 13 frontmatter keys, description ≤60 chars, 0 mid-line bold, ≤1 em-dash, trigger-test hit/no-hit, walkthrough pass.
   - Code: tests green, `read_file` diff verified, no phantom-fixes (see `ki-murks-verhindern`).
   - Docs: every claim sourced, no padding, scannable in 30 seconds.
   - Subagents: clear goal + context + constraints + deliverable shape before dispatch.
4. **Get independent review for non-trivial work.** Dispatch an M3-subagent or critic-gate. If review finds FAILs, fix them before saving — do not save-then-fix.
5. **Trim after review, not before substance.** First write complete, then cut to size limits. Cutting first produces thin artifacts. Cutting after preserves substance.
6. **Stop when done.** Resist "while I'm at it, let me also...". Each addition must clear the done-definition from step 1 or it is scope creep.

## Pitfalls

- **False quality signal**: "it compiles" or "gates pass" does not mean "it is good". Gates are necessary, not sufficient. Walkthrough and trigger-test catch what static gates miss.
- **Trimming into thinness**: cutting substance to hit a size limit produces a hollow artifact. If you cannot trim without losing substance, the scope is too broad — split, do not shrink.
- **Save-then-fix**: shipping a known-broken artifact and promising to fix later is quantity behavior. The fix never comes, or comes in a rush.
- **Review theater**: dispatching a subagent review but ignoring FAILs is worse than no review — it creates false confidence. Every FAIL must be resolved or explicitly waived with a reason.
- **"More skills = better library"**: a 500-skill library where half are stale, oversized, or untagged is worse than 200 tight, current, well-routed skills. Prune before adding.
- **Perfectionism trap**: quality-over-quantity is not "never ship". It is "ship excellent, then stop." Endless polishing without new gates to clear is procrastination wearing a quality mask.

## Verification

Before declaring done, answer in one sentence: "Does this artifact meet every gate in step 3, pass independent review, and contain nothing I would cut?" If yes — ship. If no — iterate. The proof is the green gate output, not the claim.
