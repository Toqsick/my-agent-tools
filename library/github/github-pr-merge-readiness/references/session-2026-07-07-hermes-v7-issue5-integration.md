# Session Reference — 2026-07-07 — Toqsick/hermes-v7 Issue #5 → Unrelated-Histories Merge Assessment

Concrete data captured during an unrelated-histories merge assessment triggered by Issue #5 (V7.1 Plugin-Registry planning closure). Use as a worked example when you need to assess whether to merge branches that share **zero** common ancestors, or when a planning-tracking issue's work turns out to be already delivered on a separate branch.

## Situation

| Aspect | Value |
|---|---|
| **Repo** | `Toqsick/hermes-v7` |
| **Source (closing)** | Issue #5: "V7.1 Plugin-Registry — QUEEN-PLAN, Repository-Struktur, MCP × Skill Integration" |
| **Delivery branch** | `feature/hermes-v7.1-mcp-skill-integration` (21 commits, V7.1 + V7.2 + V7.3 planning) |
| **Target branch** | `feat/security-kernel` (1 commit, V7.3 security hardening) |
| **Merge outcome** | **Aborted** — 24 add/add conflicts across 7 layers → Issue #5 closed with summary → Issue #11 created for integration |

## Pre-Merge Assessment (step-by-step)

### 1. Ancestry check

```bash
# Exit code 1 + empty output = no shared ancestor
git merge-base main feature/hermes-v7.1-mcp-skill-integration
git merge-base main feat/security-kernel
```

The V7.1 branch was created via `git replace` / an import from a different upstream (`b4e2529` re-rooted from `04af48a` → `683dd72` "Initial commit"). The security-kernel branch was forked from a different `main` history (`c07b058` "feat(skills): import 21 MiniMax Hub skills").

**Diagnosis:** zero common ancestors. `--allow-unrelated-histories` required.

### 2. Conflict-surface dry-run

```bash
cd ~/30-Library/hermes-v7
git merge --no-commit --no-ff --allow-unrelated-histories origin/feature/hermes-v7.1-mcp-skill-integration
# → 24 add/add conflicts across 24 files
git merge --abort
```

### 3. Layer-by-layer categorization

| Layer | File | Risk | Notes |
|---|---|---|---|
| Workflow | `.github/workflows/ci.yml` | 🟡 medium | CI pipeline overlap — merge both workflow files |
| Git | `.gitignore` | 🟢 low | Additive merge, easy |
| Config | `config/hermes.config.json` | 🟡 medium | Runtime config — both branches added different options |
| Config | `config/v7.skill-schema.json` | 🟡 medium | Schema evolution — check breaking changes |
| Deps | `package.json` | 🟢 low | Jest scripts + coverage threshold vs. security-kernel deps — merge both |
| Core | `src/core/audit-log.js` | 🔴 high | V7.1 adds plugin audit-log consumers; security-kernel may have changed the interface |
| Core | `src/core/types.ts` | 🔴 high | Core type overlap |
| Dashboard | `src/dashboard/html-export.ts` | 🟡 medium | Low risk — both branches touch it |
| Depp | `src/depp/depp-worker.ts` | 🟡 medium | |
| Depp | `src/depp/types.ts` | 🟡 medium | |
| Modules | `src/modules/cronjob-adapter/__tests__/cronjob-adapter.test.js` | 🟢 low | Test file — additive merge |
| Modules | `src/modules/tool-use/index.js` | 🟡 medium | |
| Roles | `src/roles/orchestrator.ts` | 🔴 high | Role orchestration — cross-cutting |
| Roles | `src/roles/reviewer-a.ts` | 🟡 medium | |
| Runtime | `src/runtime/tool-runtime.ts` | 🟡 medium | |
| Security | `src/security/index.ts` | 🔴 high | V7.3 security work vs. V7.1 plugin audit hooks |
| Security | `src/security/startup-guard.ts` | 🔴 high | Startup guard — security-critical |
| Security | `src/security/tool-profiles.ts` | 🔴 high | Tool profiles — security-critical |
| Security | `src/security/types.ts` | 🔴 high | Security types — security-critical |
| Storage | `src/storage/mnemosyne-store.ts` | 🟡 medium | |
| Storage | `src/storage/split-brain-resolver.ts` | 🟡 medium | New in V7.1 — V7.3 should consume it for hash-chain |
| Docs | `CHANGELOG.md` | 🟢 low | Both have entries — merge |
| Docs | `README.md` | 🟢 low | Both have changes — merge |

**Count:** 4 🔴 high (security), 3 🔴 high (core+roles), 10 🟡 medium, 6 🟢 low

### 4. Go/No-Go decision

**Verdict: NO-GO (abort, create tracking issue)**

Rationale:
- **4 security-layer conflicts** (`src/security/*`) — V7.1 adds plugin audit-log consumers; security-kernel may have changed audit interfaces. Resolving blind risks creating a security bypass.
- **24 total conflicts** → exceeds the 10-conflict threshold for safe blind merge.
- **Missing integration contract:** no test exists for "V7.1 plugin invoke() → V7.3-compliant audit-log entry". Would need one before merge anyway.
- **Both branches are self-contained and tested separately** — no urgency to merge.

### 5. Issue closure + Follow-up creation

**Closed Issue #5** with a detailed resolution comment (1,500 words) that:
1. Listed all 21 commits on the delivery branch by category (V7.1 core, V7.2 polish, planning artifacts)
2. Documented the merge abort with conflict counts per layer
3. Explained why each of the 5 "Nächste Schritte" from the issue body was already done on the branch
4. Linked to the follow-up tracking issue (#11)

**Created Issue #11** ("Integrate V7.1 plugin-registry into feat/security-kernel (resolve 24 add/add conflicts)") with:
- Per-file conflict table (the one above)
- Security-risk callouts for `src/security/*` and `src/core/audit-log.js`
- Sub-task checklist (7 items)
- Done-when criteria (3 items: tests green, integration test covers audit-log contract, CHANGELOG updated)
- Related branches and commit references

### Why NOT Option A (literal merge + 4 new issues)

The task brief's Option A assumed the V7.2 items from the issue body ("Nächste Schritte") were incomplete. Reality: all 5 were already implemented on the branch. Creating issues for completed work would be noise. The real un-done work was the integration into `feat/security-kernel` (24 genuine conflicts) — a single tracking issue captures that accurately.

## Concrete Commands Used

```bash
# Ancestry check
cd ~/30-Library/hermes-v7
git merge-base main origin/feature/hermes-v7.1-mcp-skill-integration  # exit 1

# Dry-run merge to surface conflict count
git merge --no-commit --no-ff --allow-unrelated-histories origin/feature/hermes-v7.1-mcp-skill-integration 2>&1 | tail -80
# Count conflicts: grep -c "KONFLIKT\|CONFLICT"

# Abort after inspection
git merge --abort

# Branch state after abort — clean status
git status    # back to original tip, no pending changes

# Preview the delivery branch scope
git log --oneline origin/feature/hermes-v7.1-mcp-skill-integration | head -21
git ls-tree --name-only -r origin/feature/hermes-v7.1-mcp-skill-integration src/plugins/
```

## Key Insight

The **conflict surface itself is the signal**. 24 conflicts across security, core, storage, and config layers doesn't mean "this merge is hard but doable" — it means "these two branches evolved in parallel with different design intent, and merging them blind will produce a buggy result." The correct response is to **step back**, document the situation, and create a tracking issue for a human-guided integration that resolves each layer in the right order (config → core → security → storage).

## Pitfalls Confirmed in This Session

1. **`git merge-base` exit code 1 = no ancestor.** This is not an error — it's a detection signal. Always check exit code explicitly, not just stdout.
2. **GitHub's `mergeable: MERGEABLE` is meaningless for unrelated histories.** GitHub only checks fast-forward or same-root scenarios. The real conflict surface only appears via `--allow-unrelated-histories` locally.
3. **Checkout of planning files from the remote branch can block the merge.** Before the dry-run, 4 planning files were checked out from the V7.1 branch for inspection (`QUEEN-PLAN.md`, `RETROSPECTIVE.md`, `lane-3-architecture.md`, `src-plugins-README.md`). These were counted as "local changes" by `git merge`. Always `git checkout -- docs/` before attempting the merge.
4. **User/agent task briefs can be dangerously wrong about what's actually done.** The brief assumed V7.2 items were incomplete; in reality the branch had all 5 plus V7.3 planning. Always verify the actual branch state before accepting the brief's assumptions.
