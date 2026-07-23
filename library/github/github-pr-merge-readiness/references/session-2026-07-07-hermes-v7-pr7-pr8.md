# Session Reference — 2026-07-07 — Toqsick/hermes-v7 PR #7 & #8 Merge-Readiness Review

Concrete data captured during a merge-readiness assessment of two open PRs on `Toqsick/hermes-v7`. Use as a worked example when reviewing merge-decisions on this repo, or as a template for other cross-PR reviews.

> **Status note (re-verified 2026-07-07 by Yuno / Biene #2):** Earlier version of this file described PR #8 as an active WIP conflicting with PR #7 on the toolchain. By 2026-07-07, PR #8's intended content was **already merged into `main` via PR #9 (`claude/featureplugin-registry-polish-skill-health`) and PR #10 (`codex/featurev7-2-plugin-registry-polish`)**. The PR #8 branch itself is an aborted copilot-swe-agent run (`892b564 "Changes before error encountered"`). The merge-order analysis and recommended actions in this file have been rewritten accordingly — the original conflict narrative no longer applies.

## The Two PRs at a Glance (verified 2026-07-07, main HEAD `6c0b603`)

| | PR #7 | PR #8 |
|---|---|---|
| **Title** | feat(security): SecurityKernel – verdrahtet 4 Ebenen + Rollen-Phasen-Audit | [WIP] Update plugin-registry and clean up dead-skills |
| **Branch** | `feat/security-kernel` | `copilot/featureplugin-registry-polish-skill-health` |
| **Base** | `main` | `main` |
| **Author** | Toqsick | `app/copilot-swe-agent` (bot) |
| **Created** | 2026-07-04 | 2026-07-05 |
| **Additions / Deletions** | +4.550 / −7 | **+19.439 / −19** |
| **Files changed** | 8 | **66** |
| **State** | OPEN | OPEN (but obsolete — see below) |
| **Draft** | No | No (`isDraft: false` per `gh pr view`) |
| **Reviews** | 0 | 0 |
| **Branch ahead of main** | 1 commit (`f704ff1`) | 3 commits — `892b564`, `b3fdcd0`, `17f1e23` |

## Why PR #7's CI is RED — Root Cause (re-verified)

The Typecheck failures are pre-existing TS errors in `main`. They became visible because PR #8 (now merged via #9/#10) added `tsconfig.json` + `@types/node`, and PR #7 added the `ts-jest` toolchain that actually runs `tsc --noEmit`. Reproduced directly on `main` with `npx tsc --noEmit`:

```
src/depp/depp-worker.ts(102,13): error TS2367:
  This comparison appears to be unintentional because the types
  '"ACCEPT" | "ESCALATE" | "REJECT"' and '"RETRY_REDUCED_SCOPE"' have no overlap.

src/depp/truncation-detector.ts(384,36): error TS2367:
  '"ABRUPT_JSON_END" | "MISSING_SENTINEL" | "REQUIRED_KEY_ABSENT" | "LAST_TOKEN_MID_WORD"
   | "LOW_CHAR_COUNT" | "INCOMPLETE_CODE_BLOCK" | "MISSING_SECTION"
   | "TRUNCATION_KEYWORD" | "INTENTIONALLY_SHORT" | "FINISH_REASON_LENGTH"'
   and '"STRUCTURALLY_INVALID"' have no overlap.

src/roles/depp-orchestrator.ts(23,33): error TS2307:
  Cannot find module './audit-log.js' or its corresponding type declarations.
src/roles/depp-orchestrator.ts(24,28): error TS2307:
  Cannot find module './depp-worker.js' or its corresponding type declarations.
src/roles/depp-orchestrator.ts(30,8):  error TS2307:
  Cannot find module './types.js' or its corresponding type declarations.
src/roles/depp-orchestrator.ts(56,8):  error TS7006:
  Parameter 'model' implicitly has an 'any' type.
```

**Diagnostic note:** the `depp-orchestrator.ts` import errors are because the file lives at `src/roles/depp-orchestrator.ts` but imports from `./audit-log.js` etc. — those exist in `src/depp/`, not `src/roles/`. The fix is `from '../depp/audit-log.js'` etc. The file itself is a **duplicate** (see Architecture section below).

**Correction vs prior version of this reference:** an earlier note suggested PR #8 contained partial depp-fixes that PR #7's CI was choking on, implying "merge #8 first". That's now superseded — PR #8 is already merged (via #9/#10) and the pre-existing TS errors are still in `main`. The blocker is the 6 errors above, not the PR-#8-vs-#7 toolchain conflict.

## Why PR #8 is Functionally Obsolete (verified 2026-07-07)

PR #8's body checklist has 9 items. Cross-checking each against `main` HEAD `6c0b603`:

| PR #8 Claim | Status in main | Evidence |
|---|---|---|
| Fix TypeScript CI: add `@types/node`, update `tsconfig.json` | ✅ merged | `tsconfig.json` exists, `package.json` has `@types/node` |
| Fix Jest TypeScript parsing: add babel transform for `.ts` | ✅ merged | `babel.config.js` + `babel-jest` in devDeps |
| Create `src/plugins/registry.js` (health scoring) | ✅ merged | `5f4bbd8 feat(v7.1): Plugin Registry Node.js + MCP Transport` |
| Create `src/plugins/mcp-github/index.js` | ✅ merged | present at HEAD |
| Create `src/plugins/mcp-todoist/index.js` (with audit-log) | ✅ merged | `a80c4c2 feat(v7.1): Todoist MCP-Plugin` |
| 18 plugin tests in `__tests__/registry.test.js` | ✅ merged | present at HEAD |
| 10 todoist tests in `__tests__/todoist.test.js` | ✅ merged | present at HEAD |
| Dead-skills archive to `.archive/` | ✅ merged | `7809a6c feat(v7.2): P1 Polish — Dead-Skills Cleanup + Jest-Suite + Health-Score` |
| `set -euo pipefail` in SKILL.md | ✅ merged | 11 `skills/hub-imported/*/SKILL.md` files contain the edits |

**The PR-#8 branch is also broken:** its 3 commits are `17f1e23 Initial plan`, `b3fdcd0 Initial plan: V7.2 plugin registry polish + skill health`, and `892b564 Changes before error encountered` — the last is a copilot-swe-agent aborted run (`copilot-swe-agent[bot] <198982749+Copilot@users.noreply.github.com>`, 2026-07-05 21:28 UTC). All 66 files in the diff are either already in `main` (via #9/#10) or are working-tree hygiene violations (`coverage/lcov-report/*`, `logs/audit.jsonl`) that shouldn't be committed at all.

**Recommendation:** close PR #8 as "Superseded by #9 and #10" with a comment listing the 9 checklist items and their merged status. See "Recommended Actions" section below.

## Cross-PR Conflict: Re-Assessed

The earlier version of this reference argued a direct Babel-vs-ts-jest conflict. **That conflict was resolved when #9/#10 merged — they chose babel-jest.** PR #7's `ts-jest` is now stacking on top of an already-merged babel-jest setup. There is no active merge conflict on `main`; there is only a stack-decision question.

| Aspect | PR #7 (proposed) | Main post-#9/#10 (current) | Active conflict? |
|---|---|---|---|
| TS compiler runner | `ts-jest` preset | `babel-jest` default (no preset) | No — would only clash on PR #7 merge |
| `@types/node` version | `^20.14.0` | `^26.1.0` | No — already in main |
| `tsconfig.json` | not added | present | No — already in main |
| `babel.config.js` | not added | present | No — already in main |
| `jest.preset` | `"ts-jest"` | absent | Would set on merge; babel still functional but bypassed |

**What actually happens on PR #7 merge:** `ts-jest` becomes the preset, `.test.ts` becomes matchable, `.test.js` continues to run (ts-jest handles `.js` via its TS pipeline). `babel.config.js` stays in tree but is unused. This is acceptable but mildly wasteful — see "Stack-decision options" in the strategy doc that triggered this session.

## PR #8 Scope-vs-Body Audit (file-level)

PR #8's 66-file diff, categorized:

| Category | Count | Notes |
|---|---|---|
| `coverage/lcov-report/**` (HTML + assets) | 41 | Generated coverage artifacts — should be `.gitignore`d |
| `logs/audit.jsonl` | 1 | Local runtime log — should be `.gitignore`d |
| `package.json` / `package-lock.json` | 2 | Already merged content; duplicate here |
| `babel.config.js` | 1 | Already merged |
| `tsconfig.json` | 1 | Already merged |
| `src/plugins/**` (impls + tests) | 8 | Already merged |
| `src/depp/**` (5+3 LOC) | 2 | Already merged |
| `src/roles/depp-orchestrator.ts` (6 LOC) | 1 | Already merged |
| `skills/hub-imported/*/SKILL.md` (1-line edits) | 11 | Already merged |

**Pattern (re-confirmed):** WIP PRs drift from their body checklist. Coverage + log files account for ~63% of the file count without being mentioned in scope. The "quick win" recommended at the end of the strategy doc — `.gitignore` for `coverage/` and `logs/*.jsonl` — prevents re-occurrence.

## Pre-Existing Duplicated File (Architecture Finding)

`src/depp/depp-orchestrator.ts` and `src/roles/depp-orchestrator.ts` are **byte-identical** (6766 bytes each, same modification timestamp `Jul 7 13:03` / `13:04`). PR #7 only modifies `src/roles/depp-orchestrator.ts` (Kernel integration). The duplication is a pre-existing problem, flagged in PR #7's body as Issue #1, and explicitly **out of scope** for this PR. Separate ticket required.

## Architecture Note Worth Preserving

PR #7's `src/roles/orchestrator.ts` documents a real subtlety in its JSDoc:

> *"Die für die Audit-/Tool-Profile-Prüfung verwendete Rolle ist die PHASEN-ROLLE (aus PHASE_ROLE_MAP), NICHT task.owner. task.owner beschreibt nur die Queen-Zuständigkeit (typischerweise 'orchestrator' bzw. nach Übergang 'implementer'), während die Kernel-Sequenz unter der Rolle laufen muss, die das Pseudo-Tool der jeweiligen Phase tatsächlich ausführen darf."*

The `PHASE_ROLE_MAP` is the single source of truth:

```ts
const PHASE_ROLE_MAP: Record<string, Role> = {
  plan:      'planner',
  implement: 'implementer',
  'review-a': 'reviewerA',
  'review-b': 'reviewerB',
  verify:    'verifier',
};
```

And `TOOL_PROFILES` (in `src/security/tool-profiles.ts`) has matching pseudo-tools `orchestrator-phase:{plan,implement,review-a,review-b,verify}`. This coupling is the kind of thing future security-PRs need to know about.

## Two parallel orchestrator implementations (in main, not from either PR)

Discovered in PR #7's "Architektur-Funde" section:
- `src/roles/orchestrator.ts` (TypeScript, Kernel-integrated) — what PR #7 modified
- `src/modules/orchestrator/index.js` (CommonJS, lane-dispatcher, does NOT go through Kernel)

This is pre-existing technical debt. Both exist in main; only the TS one is being Kernel-integrated. The JS one will need to be either migrated or explicitly deprecated in a future ticket.

## Recommended Actions (verified plan, 2026-07-07)

In order, ~55 minutes total:

1. **Close PR #8 as superseded.** Comment with the 9-item checklist mapped to merged PRs (#9, #10), then `gh pr close 8 --comment "Superseded by #9 and #10"`. Don't try to merge or split — content already in main.
2. **Open small `.gitignore` PR:** append `coverage/` and `logs/*.jsonl` (with `!logs/.gitkeep` exception). Prevents re-occurrence of the 42-file PR #8 hygiene violation. ~5 min.
3. **Fix the 6 pre-existing TS errors as a separate PR:**
   - `src/depp/depp-worker.ts:102` — remove dead comparison vs `RETRY_REDUCED_SCOPE`
   - `src/depp/truncation-detector.ts:384` — remove dead comparison vs `STRUCTURALLY_INVALID`
   - `src/roles/depp-orchestrator.ts:23,24,30` — sed-fix imports `./X.js` → `../depp/X.js`
   - `src/roles/depp-orchestrator.ts:56` — add `model: DeppModelConfig` annotation
   - Verify with `npx tsc --noEmit` (must be 0 errors) and `npx jest` (must stay green).
   - Squash-merge to main. ~20 min.
4. **Rebase PR #7 onto the now-clean main** (`gh pr checkout 7 && git rebase main && git push --force-with-lease`). Should be trivial — PR #7's diff is orthogonal to the depp fixes.
5. **Squash-merge PR #7.** `gh pr merge 7 --squash --delete-branch`. ~5 min.
6. **File a separate issue** for the duplicated `src/depp/depp-orchestrator.ts` × `src/roles/depp-orchestrator.ts` and the JS-vs-TS orchestrator split. Out of scope for this swarm.

**Do NOT** fold the pre-existing TS fixes into PR #7 — PR #7's body explicitly says "Was bewusst NICHT gemacht wurde" and a focused rebase-friendly diff is easier to review.

## Reproduction Recipe (for future re-review)

```bash
# Verify auth
gh auth status

# Capture both PRs (compact JSON, all fields in one call)
gh pr view 7 -R Toqsick/hermes-v7 --json \
  title,state,isDraft,mergeable,mergeStateStatus,additions,deletions,changedFiles,\
  headRefName,baseRefName,reviews,statusCheckRollup,body
gh pr view 8 -R Toqsick/hermes-v7 --json \
  title,state,isDraft,mergeable,mergeStateStatus,additions,deletions,changedFiles,\
  headRefName,baseRefName,reviews,statusCheckRollup,body

# Fetch PR branches locally for diff analysis (works even when GitHub MCP is down)
git fetch origin "refs/pull/7/head:pr7" "refs/pull/8/head:pr8"

# Get file lists
gh pr diff 7 -R Toqsick/hermes-v7 --name-only
gh pr diff 8 -R Toqsick/hermes-v7 --name-only

# Read the full diff of #8 (large)
gh pr diff 8 -R Toqsick/hermes-v7 > /tmp/pr8.diff
csplit -z -f /tmp/pr8- -b '%03d.diff' /tmp/pr8.diff '/^diff --git /' '{*}'

# Reproduce the pre-existing TS errors on main
git checkout main && npm install && npx tsc --noEmit
# Expected: 6 errors as listed above

# Reproduce on PR #7 branch (also 6 errors, plus PR #7-specific TS via ts-jest)
git checkout pr7 && npm install && npx tsc --noEmit

# Check what was actually merged into main from PR #8's checklist
git log main --oneline -- src/plugins/ src/depp/ tsconfig.json babel.config.js \
  package.json skills/hub-imported/ | head -30
```

## Pitfalls Confirmed in This Session

1. **GitHub MCP unreachable is a real and recurring failure mode.** `mcp__github__*` returned both `401 Bad credentials` and `MCP server is unreachable after 4 consecutive failures` on the first attempt. Do not retry — switch to `gh` CLI immediately (this session verified the fallback path works in full).
2. **The user's brief can be wrong about file names.** This session's brief named `depp-truncation-detector.ts` and `depp-orchestrator.ts` as the files with TS errors. Real names are `src/depp/truncation-detector.ts` (no `depp-` prefix) and `src/roles/depp-orchestrator.ts` (not in `src/depp/`). **Always verify file names against the actual repo before trusting them**, especially when the brief was written from memory or from an earlier session.
3. **The user's brief can be wrong about PR state.** This brief assumed PR #8 was active and conflicting with PR #7. Reality: PR #8 was functionally obsolete (content already merged via #9/#10). **Always run `gh pr view N --json state,mergeStateStatus,mergeable`** before assuming two PRs are "active and conflicting".
4. **An aborted CI-bot PR can look legitimate at first glance.** PR #8's last commit `892b564 "Changes before error encountered"` is a real copilot-swe-agent commit. It's easy to miss the "Changes before error encountered" message. **Always inspect the last 1-3 commits on a bot-authored PR's head branch** before recommending merge/split/close actions — `git log --format='%H %s' prN | head -3`.
5. **Duplicate files between directories are a common source of "phantom" TS errors.** The `depp-orchestrator.ts` × 2 situation caused 4 of the 6 TS errors in this session, because the kernel-integrated copy at `src/roles/` imported from `./` but the real implementation lives at `src/depp/`. The fix is in one place, but the symptom shows in another.
6. **`npx tsc --noEmit` is the fastest way to verify pre-existing TS errors.** No need to wait for CI to see the same failures. Works locally in 1-2 seconds once `npm install` is done.