---
name: code-review-checklist
description: "Use when user asks for a pre-merge code review, canonical reviewer checklist, spec-compliance assessment, or a standardized verdict for a coding pipeline. NOT for implementing the change or doing broad architecture design. Checks correctness, security, maintainability, operations, and emits the pipeline-readable verdict."
version: 1.0.0
author: Hermes Agent (hermes-v2 plan, H-51, 2026-07-20)
license: MIT
platforms:
  - linux
  - macos
  - windows
metadata:
  hermes:
    tags: ['code-review', 'checklist', 'verdict', 'gate', 'coding-pipeline', 'hermes-v2']
    related_skills:
      - critic-gate
      - requesting-code-review
      - verify-before-fix
      - simplify-code
      - output-validator
lane: gate
reasoning_effort: xhigh
agent: Verifier
routing_hint: |
  **Agent-Scope:** Code review per the canonical checklist. Off-scope: building, designing, writing — return to Yuno for re-route.

  Routing-Spec: `yuno-team-routing`.
trigger_keywords: ['verdict', 'the', 'code-review-checklist', 'pre-merge', 'code']
keywords: ['verdict', 'pipeline', 'user', 'asks', 'merge']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['coding-pipeline-orchestrator', 'critic-gate']
---

# Code Review Checklist (hermes-v2)

## When to Use

Use this skill when you are the **reviewer** in a coding-pipeline
(H-31) or when doing any pre-merge code review. It enforces the
canonical checklist and the standardized verdict format the pipeline
parses to drive the review step.

The skill complements, not replaces, `critic-gate`. Use them
together:

- **`critic-gate`** decides *whether* the artifact is evaluable
  (schema-valid, required sections present) and reports a gate status
  of PASS, RETRY, or FAIL.
- **`code-review-checklist`** (this skill) decides *whether the code
  is acceptable for merge* given it IS evaluable, and emits exactly
  `VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES`.

Keep gate status, review-step metadata, and review verdict separate:

```
Gate status: PASS
Review step: spec-review
VERDICT: APPROVE
```

If `critic-gate` reports RETRY or FAIL, fix the artifact before applying
this checklist.

## Quick Start

1. Read the task/specification and inspect the complete change.
2. Walk all five checklist sections and record concrete evidence.
3. Put exactly one canonical `VERDICT:` line in the review body.
4. Post it to the pipeline root with the verified CLI syntax:
   `hermes kanban comment "$ROOT_ID" "$REVIEW_BODY"`.

## Workflow

### Apply the checklist

Five sections, each with a pass/fail criterion. Mark each **FAIL** with
a concrete fix request — never with "LGTM except..." or "could be
better".

### 1. Spec compliance

- [ ] The implementation matches the task description (or the plan
      referenced by the parent task).
- [ ] All public functions/classes from the spec are present and have
      the documented signatures.
- [ ] No silent scope expansion (no extra features the spec didn't ask
      for).

### 2. Correctness

- [ ] Tests cover the happy path AND at least one failure path per
      public function.
- [ ] Edge cases called out in the spec are exercised by tests.
- [ ] No `TODO`/`FIXME`/placeholder code in the diff.
- [ ] No swallowed exceptions (`except: pass`, bare `except Exception`
      without re-raise or log).
- [ ] Async paths: cancellation / context-leak handled (no fire-and-
      forget tasks with no error sink).

### 3. Security

- [ ] No new shell-injection sinks (subprocess with `shell=True` and
      user input, or `os.system` with concatenated strings).
- [ ] No new SQL string-concatenation (must use parameterised queries).
- [ ] No secrets in plaintext (config, fixtures, logs). Use env vars
      or vault refs.
- [ ] New HTTP endpoints: input validated, output escaped or typed.
- [ ] New file paths: path-traversal-safe (no `..` acceptance).

### 4. Maintainability

- [ ] No function > 60 lines without a refactor justification.
- [ ] No copy-pasted blocks > 10 lines (DRY).
- [ ] Names are intent-revealing — no `data`, `temp`, `helper`
      without a domain qualifier.
- [ ] Comments explain WHY, not WHAT. (No "increment i by 1".)
- [ ] Public APIs have docstrings; private helpers do not need them
      but MUST be small enough to be obviously correct.

### 5. Operational

- [ ] No new debug prints / `console.log` left in production paths.
- [ ] No new blocking I/O in hot paths (use async equivalents where
      the runtime supports it).
- [ ] Logs at INFO level for the user-visible events, at DEBUG for
      internal trace.
- [ ] New env vars documented in the project's `README.md` or
      equivalent; defaults are safe.
- [ ] Backwards compatibility: existing callers / configs still work
      unless the change is explicitly breaking with a CHANGELOG note.

### Emit the canonical verdict

Your review **must** contain exactly one of these two verdict lines. Put
it on its own line in the review body and post that body to the
**pipeline root** with
`hermes kanban comment "$ROOT_ID" "$REVIEW_BODY"`:

```
VERDICT: APPROVE
```

or

```
VERDICT: REQUEST_CHANGES
- <section>.<item>: <concrete fix request>
- <section>.<item>: <concrete fix request>
```

The pipeline orchestrator parses the `VERDICT:` line and routes the
review step:

- `VERDICT: APPROVE` → mark the review step done and advance to the
  next gate.
- `VERDICT: REQUEST_CHANGES` → keep the review step open with the
  comment chain visible to the fix worker; the fix worker re-loads
  `verify-before-fix` to ensure each `-` line is addressed in code or
  explicitly explained in a reply comment.

Any other `VERDICT:` value requires a human gate; it must not trigger
automatic promotion.

### Worked Example

```
[reviewer=gate/yuno-coder, model=glm-5, step=spec-review]

Spec compliance: ✓ matches writing-plans §3.2.
Correctness: ✓ tests added for happy path; missing failure test on
              webhook receiver when POST body is malformed.
Security: ✓ no new injection sinks.
Maintainability: ✓ function sizes reasonable; one minor: parse_config
                  at L42 is 65 lines, consider extracting validation.
Operational: ✓ no debug prints.

VERDICT: REQUEST_CHANGES
- 2.Correctness: add a test that POST /webhook with invalid JSON
  returns 400 (not 500).
- 4.Maintainability: parse_config at L42 is 65 lines; split into
  parse_config() + validate_config().
```

The orchestrator reads `VERDICT: REQUEST_CHANGES`, keeps the
spec-review step open, and the fix worker reads the bullet list as
the work list.

## Verification and Acceptance

A review is correct only if:

1. All five checklist sections are walked (5.Operational may be N/A
   with explicit justification).
2. Exactly one `VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES` line is
   present.
3. `VERDICT: REQUEST_CHANGES` has at least one concrete `-` bullet.
4. The review is posted as a comment to the pipeline root, not the
   review-step task itself.
5. Every failed item cites evidence and a verifiable fix request.

## Anti-Patterns

| Anti-pattern | Why it's rejected |
|---|---|
| "LGTM 👍" | No checklist walked; the orchestrator cannot parse it |
| "Could use more error handling" | Vague — not actionable for the fix worker |
| "Style is a bit off" | Not on the checklist; route to `simplify-code` if needed |
| Multiple `VERDICT:` lines | Ambiguous; the review must be rejected |
| `VERDICT: REQUEST_CHANGES` without `- ` bullets | The fix worker has nothing concrete to address |

## Failure Recovery

- If the artifact gate reports RETRY or FAIL, stop the review and make
  the artifact evaluable before restarting the checklist.
- If a canonical verdict cannot be produced, leave the review step open
  for a human gate; never invent a fallback verdict.
- If a finding lacks evidence, rerun the focused inspection or test and
  update the finding before posting the review.

## Related Skills and References

- **`critic-gate`** (run first): reports PASS, RETRY, or FAIL for
  artifact structure.
- **`requesting-code-review`** (run before this): runs security and
  quality checks.
- **`simplify-code`** (load on `VERDICT: REQUEST_CHANGES` to suggest
  refactors): use it when 4.Maintainability fails.
- **`verify-before-fix`** (load on the fix worker): use it to ensure
  each verdict bullet is addressed.
- **Hermes CLI:** `hermes kanban comment --help` documents the verified
  `task_id text [text ...]` syntax.
