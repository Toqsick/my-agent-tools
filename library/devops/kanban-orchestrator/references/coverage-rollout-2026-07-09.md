# Kanban Coverage Rollout — 2026-07-09 Session Notes

> Session-specific detail backing the **Pitfalls** section in SKILL.md.
> Read this when you're about to do a multi-phase Kanban rollout on a setup where the system has been dormant (stale daemon, stranded ready tasks, missing profile descriptions).

## The Setup We Started With

- **51 historical tasks** across 6 boards (`routing-lanes`, `hermes`, `system`, `voice`, `dashboard`, `greyhack`)
- **25 ready tasks, all `(unassigned)`** — the silent-stranding signature
- **0 of 6 profiles had descriptions** — auto-decompose would have been blind
- **`daemon.pid`/`daemon.log` from 2026-07-02** still on disk even though the dispatcher moved into the gateway
- **0 worktrees ever created** — every task was `workspace_kind=scratch`
- **No notifications configured** — `notification_sources` key absent

## The 4-Phase Rollout Pattern (Reusable)

| Phase | Goal | One-Liner |
|---|---|---|
| **0. Baseline** | Stale-files cleanup + diagnostics snapshot | `rm daemon.pid` + backup + `hermes kanban diagnostics` per board |
| **1. Unblock the queue** | Set profile descriptions + assign or block-with-reason every stranded ready task | Loop `boards switch; for tid in $(ready): assign or block` |
| **2. Worker maturity** | Worktrees, max_runtime, skills, idempotency_keys on new tasks | Best-Practices doc + 3 demo tasks (worktree / cron / goal-mode) |
| **3. Advanced patterns** | Auto-decompose + swarm + cross-profile notifications | Config: orchestrator_profile + default_assignee + notification_sources; demo with swarm + triage task |
| **4. Bienen-Dispatch** | 2-wellen fan-out of focused audit/cleanup tasks | 3 + 3 = 6 parallel workers, each with single concrete deliverable |

Coverage progression on the rollout: **40% → 52% → 62% → 73% → 88%**.

## Why The Worktree Pitfall Is Sneaky

When `default_workdir` is set to a **parent directory containing multiple git repos** (e.g. `~/10-Projekte/10-active`), the spawn fails with:

```
workspace: task <id> has workspace_kind=worktree but board '<slug>' default_workdir
'<path>' is not inside a git repo
```

Two-character fix: point `default_workdir` at a specific sub-repo:

```bash
hermes kanban boards set-default-workdir routing-lanes ~/10-Projekte/10-active/github-mcp-server
```

Then `hermes kanban unblock <id> --reason "default-workdir now inside a real git repo"` triggers a re-dispatch on the next 60-second tick.

## Why `hermes config set` Breaks Lists

The CLI uses `argparse` with `--key value` semantics — lists become string scalars. The fix is to either:

1. Edit `~/.hermes/config.yaml` directly (write_file works because the file path is in the user's home, not the security-blocklisted path)
2. Or write the YAML list inline if the editor allows it: `notification_sources: ['*']`

The tell: when you grep the config and see `notification_sources: '["*"]'` with single quotes wrapping the brackets, that's a **string**, not a list, and the dispatcher will silently ignore it.

## The Bienen-Dispatch Recipe (Basti's Favorite)

For sessions where the user wants parallel progress on N related tasks, fan out in **2 waves of 3** (or whatever the concurrency budget supports):

**Wave 1 (simultaneous):**
- One discovery/audit task (`yuno-coder` for code/system audits)
- One cleanup/consolidation task (`yuno` for memory-cleanup-style work)
- One mapping task (`yuno-coder` with grep/file-scanning)

**Wave 2 (5-10 seconds later, after Wave 1 settles into running):**
- One planning task (designs a migration or refactor based on audit findings)
- One coverage-gap task (cross-checks the inventory against expectations)
- One read-only safety task (secrets audit, schema audit, no mutations)

Each Biene gets:
- `--assignee <profile>` matched to the work domain
- `--max-runtime <seconds>` set to a realistic bound (1800-3600 for code audits, 900-1500 for read-only)
- `--workspace scratch|worktree` based on whether changes are expected
- A short **deliverable path** in the body (e.g. "Output: `~/docs/system/X.md`") so the worker knows where to write and the user knows where to look

Result of this rollout's 6 Bienen: 5/6 ran immediately, 1 needed 2 retries due to the worktree pitfall, all 6 delivered actual files (Memory cleanup, Skill-Migration-Plan, Tool-Coverage-Audit, Secrets-Audit, greyhack-Coverage-Map, Kanban-Health-Audit).

## Skill-Map Doku as Goal-Mode Proof

One of the Phase 2 demo tasks was a Goal-Mode Langläufer: "Dokumentiere alle Hermes-Skill-Sets". The worker produced `~/docs/system/hermes-profile-skill-map-2026-07-09.md` (378 lines, 16KB) in 14 iterations / 236 seconds. Key finding embedded in that doc: **the canonical skill counts per profile are 72 / 129 / 72 / 72 / 72 / 96**, which contradicts naive `ls ~/.hermes/profiles/<name>/skills/` lookups for the non-yuno profiles (those directories contain only category-bridges, not the actual installed skill files which live in a shared per-version pool).

This matters for Phase 1 Skill-Fix decisions: the "Unknown skill" crashes we reassigned around were real, but the reassigns were conservative safety moves, not strictly necessary — most pinned skills would have resolved correctly in the shared pool. Keep the Skill-Map doc as the source of truth for "which profile has which skills."