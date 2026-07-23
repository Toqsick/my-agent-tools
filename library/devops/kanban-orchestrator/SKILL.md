---
name: kanban-orchestrator
description: |
  Use when you need to use the kanban-orchestrator workflow and its documented procedures.
  NOT for unrelated tasks outside the kanban-orchestrator workflow.
  Provides focused guidance for kanban-orchestrator.
version: 3.1.0
platforms:
- linux
- macos
- windows
environments:
- kanban
metadata:
  hermes:
    tags:
    - kanban
    - multi-agent
    - orchestration
    - routing
    related_skills:
    - kanban-worker
author: Hermes Agent
license: MIT
lane: worker-heavy
reasoning_effort: xhigh
trigger_keywords: ['kanban', 'orchestrator', 'workflow', 'need', 'documented']
keywords: ['kanban', 'orchestrator', 'workflow', 'need', 'documented']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['voice-clone', 'github-workflow', 'hermes-admin']
---


# Kanban Orchestrator — Decomposition Playbook

> The **core worker lifecycle** (including the `kanban_create` fan-out pattern and the "decompose, don't execute" rule) is auto-injected into every kanban process via the `KANBAN_GUIDANCE` system-prompt block. This skill is the deeper playbook when you're an orchestrator profile whose whole job is routing.

## Profiles are user-configured — not a fixed roster

Hermes setups vary widely. Some users run a single profile that does everything; some run a small fleet (`docker-worker`, `cron-worker`); some run a curated specialist team they've named themselves. There is **no default specialist roster** — the orchestrator skill does not know what profiles exist on this machine.

Before fanning out, you must ground the decomposition in the profiles that actually exist. The dispatcher silently fails to spawn unknown assignee names — it doesn't autocorrect, doesn't suggest, doesn't fall back. So a card assigned to `researcher` on a setup that only has `docker-worker` just sits in `ready` forever.

**Step 0: discover available profiles before planning.**

Use one of these:

- `hermes profile list` — prints the table of profiles configured on this machine. Run it through your terminal tool if you have one; otherwise ask the user.
- `kanban_list(assignee="<some-name>")` — sanity-check a single name. Returns an empty list (rather than an error) for an unknown assignee, so this only confirms a name you're already considering.
- **Just ask the user.** "What profiles do you have set up?" is a fine first turn when the goal needs more than one specialist.

Cache the result in your working memory for the rest of the conversation. Re-asking every turn wastes a tool call.

## When to use the board (vs. just doing the work)

Create Kanban tasks when any of these are true:

1. **Multiple specialists are needed.** Research + analysis + writing is three profiles.
2. **The work should survive a crash or restart.** Long-running, recurring, or important.
3. **The user might want to interject.** Human-in-the-loop at any step.
4. **Multiple subtasks can run in parallel.** Fan-out for speed.
5. **Review / iteration is expected.** A reviewer profile loops on drafter output.
6. **The audit trail matters.** Board rows persist in SQLite forever.

If *none* of those apply — it's a small one-shot reasoning task — use `delegate_task` instead or answer the user directly.

## The anti-temptation rules

Your job description says "route, don't execute." The rules that enforce that:

- **Do not execute the work yourself.** Your restricted toolset usually doesn't even include terminal/file/code/web for implementation. If you find yourself "just fixing this quickly" — stop and create a task for the right specialist.
- **For any concrete task, create a Kanban task and assign it.** Every single time.
- **Split multi-lane requests before creating cards.** A user prompt can contain several independent workstreams. Extract those lanes first, then create one card per lane instead of bundling unrelated work into a single implementer card.
- **Run independent lanes in parallel.** If two cards do not need each other's output, leave them unlinked so the dispatcher can fan them out. Link only true data dependencies.
- **Never create dependent work as independent ready cards.** If a card must wait for another card, pass `parents=[...]` in the original `kanban_create` call. Do not create it first and link it later, and do not rely on prose like "wait for T1" inside the body.
- **If no specialist fits the available profiles, ask the user which profile to create or which existing profile to use.** Do not invent profile names; the dispatcher will silently drop unknown assignees.
- **Decompose, route, and summarize — that's the whole job.**

## Decomposition playbook

### Step 1 — Understand the goal

Ask clarifying questions if the goal is ambiguous. Cheap to ask; expensive to spawn the wrong fleet.

### Step 2 — Sketch the task graph

Before creating anything, draft the graph out loud (in your response to the user). Treat every concrete workstream as a candidate card:

1. Extract the lanes from the request.
2. Map each lane to one of the profiles you discovered in Step 0. If a lane doesn't fit any existing profile, ask the user which to use or create.
3. Decide whether each lane is independent or gated by another lane.
4. Create independent lanes as parallel cards with no parent links.
5. Create synthesis/review/integration cards with parent links to the lanes they depend on. A child created with unfinished parents starts in `todo`; the dispatcher promotes it to `ready` only after every parent is done.

Examples of prompts that should fan out (using placeholder profile names — substitute whatever exists on the user's setup):

- "Build an app" → one card to a design-oriented profile for product/UI direction, one or two cards to engineering profiles for implementation, plus a later integration/review card if the user has a reviewer profile.
- "Fix blockers and check model variants" → one implementation card for the blocker fixes plus one discovery/research card for config/source verification. A final reviewer card can depend on both.
- "Research docs and implement" → a docs-research card can run in parallel with a codebase-discovery card; implementation waits only if it truly needs those findings.
- "Analyze this screenshot and find the related code" → one card to a vision-capable profile for the visual analysis while another searches the codebase.

Words like "also," "finally," or "and" do not automatically imply a dependency. They often mean "make sure this is covered before reporting back." Only link tasks when one card cannot start until another card's output exists.

Show the graph to the user before creating cards. Let them correct it — including which actual profile name should own each lane.

### Step 3 — Create tasks and link

Use the profile names from Step 0. The example below uses placeholders `<profile-A>`, `<profile-B>`, `<profile-C>` — replace them with what the user actually has.

```python
t1 = kanban_create(
    title="research: Postgres cost vs current",
    assignee="<profile-A>",  # whichever profile handles research on this setup
    body="Compare estimated infrastructure costs, migration costs, and ongoing ops costs over a 3-year window. Sources: AWS/GCP pricing, team time estimates, current Postgres bills from peers.",
    tenant=os.environ.get("HERMES_TENANT"),
)["task_id"]

t2 = kanban_create(
    title="research: Postgres performance vs current",
    assignee="<profile-A>",  # same profile, run in parallel
    body="Compare query latency, throughput, and scaling characteristics at our expected data volume (~500GB, 10k QPS peak). Sources: benchmark papers, public case studies, pgbench results if easy.",
)["task_id"]

t3 = kanban_create(
    title="synthesize migration recommendation",
    assignee="<profile-B>",  # whichever profile does synthesis/analysis
    body="Read the findings from T1 (cost) and T2 (performance). Produce a 1-page recommendation with explicit trade-offs and a go/no-go call.",
    parents=[t1, t2],
)["task_id"]

t4 = kanban_create(
    title="draft decision memo",
    assignee="<profile-C>",  # whichever profile drafts user-facing prose
    body="Turn the analyst's recommendation into a 2-page memo for the CTO. Match the tone of previous decision memos in the team's knowledge base.",
    parents=[t3],
)["task_id"]
```

`parents=[...]` gates promotion — children stay in `todo` until every parent reaches `done`, then auto-promote to `ready`. No manual coordination needed; the dispatcher and dependency engine handle it.

If the task graph has dependencies, create the parent cards first, capture their returned ids, and include those ids in the child card's `parents` list during the child `kanban_create` call. Avoid creating all cards in parallel and linking them afterward; that creates a window where the dispatcher can claim a child before its inputs exist.

### Step 4 — Complete your own task

If you were spawned as a task yourself (e.g. a planner profile was assigned `T0: "investigate Postgres migration"`), mark it done with a summary of what you created:

```python
kanban_complete(
    summary="decomposed into T1-T4: 2 research lanes in parallel, 1 synthesis on their outputs, 1 prose draft on the recommendation",
    metadata={
        "task_graph": {
            "T1": {"assignee": "<profile-A>", "parents": []},
            "T2": {"assignee": "<profile-A>", "parents": []},
            "T3": {"assignee": "<profile-B>", "parents": ["T1", "T2"]},
            "T4": {"assignee": "<profile-C>", "parents": ["T3"]},
        },
    },
)
```

### Step 5 — Report back to the user

Tell them what you created in plain prose, naming the actual profiles you used:

> I've queued 4 tasks:
> - **T1** (`<profile-A>`): cost comparison
> - **T2** (`<profile-A>`): performance comparison, in parallel with T1
> - **T3** (`<profile-B>`): synthesizes T1 + T2 into a recommendation
> - **T4** (`<profile-C>`): turns T3 into a CTO memo
>
> The dispatcher will pick up T1 and T2 now. T3 starts when both finish. You'll get a gateway ping when T4 completes. Use the dashboard or `hermes kanban tail <id>` to follow along.

## Common patterns

**Fan-out + fan-in (research → synthesize):** N research-style cards with no parents, one synthesis card with all of them as parents.

**Parallel implementation + validation:** one implementer card makes the change while one explorer/researcher card verifies config, docs, or source mapping. A reviewer card can depend on both. Do not make the implementer own unrelated verification just because the user mentioned both in one sentence.

**Pipeline with gates:** `planner → implementer → reviewer`. Each stage's `parents=[previous_task]`. Reviewer blocks or completes; if reviewer blocks, the operator unblocks with feedback and respawns.

**Same-profile queue:** N tasks, all assigned to the same profile, no dependencies between them. Dispatcher serializes — that profile processes them in priority order, accumulating experience in its own memory.

**Human-in-the-loop:** Any task can `kanban_block()` to wait for input. Dispatcher respawns after `/unblock`. The comment thread carries the full context.

## Pitfalls

**Inventing profile names that don't exist.** The dispatcher silently fails to spawn unknown assignees — the card just sits in `ready` forever. Always assign to a profile from your Step 0 discovery; ask the user if you're unsure.

**Bundling independent lanes into one card.** If the user asks for two independent outcomes, create two cards. Example: "fix blockers and check model variants" is not one fixer task; create a fixer/engineer card for the fixes and an explorer/researcher card for the variant check, then optionally gate review on both.

**Over-linking because of wording.** "Finally check X" may still be parallel with implementation if X is static config, docs, or source discovery. Link it after implementation only when the check depends on the implementation result.

**Forgetting dependency links.** If the task graph says `research -> implement -> review`, do not create all tasks as independent ready cards. Use parent links so implement/review cannot run before their inputs exist.

**Reassignment vs. new task.** If a reviewer blocks with "needs changes," create a NEW task linked from the reviewer's task — don't re-run the same task with a stern look. The new task is assigned to the original implementer profile.

**Argument order for links.** `kanban_link(parent_id=..., child_id=...)` — parent first. Mixing them up demotes the wrong task to `todo`.

**Don't pre-create the whole graph if the shape depends on intermediate findings.** If T3's structure depends on what T1 and T2 find, let T3 exist as a "synthesize findings" task whose own first step is to read parent handoffs and plan the rest. Orchestrators can spawn orchestrators.

**Tenant inheritance.** If `HERMES_TENANT` is set in your env, pass `tenant=os.environ.get("HERMES_TENANT")` on every `kanban_create` call so child tasks stay in the same namespace.

**CLI quirk: `hermes kanban block` takes `kind` as a positional argument, NOT as `--kind` flag.** The correct invocation is `hermes kanban block <task_id> <kind> <reason...>` where `<kind>` is one of `capability|dependency|needs_input|transient`. Using `--kind` silently prints the help text and changes nothing — easy to miss because there's no error message, just no-op. Same goes for the help output being misinterpreted as success. Always verify with `hermes kanban show <id>` after a block call.

**CLI quirk: `hermes kanban archive` has no `--reason` flag.** The archive verb takes positional task ids only. To preserve the rationale for archiving, prepend the call with `hermes kanban comment <id> "ARCHIVE: <reason>"`. The comment is the durable annotation; the archive itself just flips status. Without the comment, future-you has no clue why the chain got nuked.

**Worker-spawn crash pattern: `skills=[...]` with non-installed skill names kills the worker immediately.** If a task body pins skills via `hermes kanban create --skill <name>` or the body's `skills=[...]` field, and any one of those names does not match an installed skill (run `hermes skills list` first), the dispatcher spawns the worker, the worker exits with code 1 within ~60 seconds, and the circuit breaker (`kanban.failure_limit`, default 2) auto-blocks the task. The crash signature in `~/.hermes/kanban/boards/<slug>/logs/<id>.log` is literally `Error: Unknown skill(s): <name>` repeated twice. Fix by either removing the skill pin, renaming to an installed skill, or using the full prefixed path (e.g. `gaming/greyhack-greyscript` instead of `greyhack-greyscript`). This is the #1 cause of "ready task silently blocked" diagnoses after assignment.

**Profile descriptions are a precondition for auto-decompose.** `kanban.auto_decompose: true` (the default) routes Triage-column tasks via the LLM decomposer, which reads profile `description` strings to decide routing. If profiles lack descriptions, the decomposer either picks the first profile alphabetically, falls back to `kanban.default_assignee`, or produces incoherent graphs. Set descriptions on every profile that should receive work: `hermes profile describe <name> --text "..."`. This belongs in Step 0 of the decomposition playbook, alongside the profile-discovery call.

**Skill pinning is per-profile, not global.** Skills live in `~/.hermes/profiles/<profile>/skills/` (with category folders like `gaming/`, `voice-assistant-bots/`), NOT in a shared global pool. A task that pins `skills=['yuno-cleaner']` and gets dispatched to a profile that lacks that skill will crash within 60 seconds with `Error: Unknown skill(s): yuno-cleaner` in the worker log. **Verify before pinning:**

```bash
find ~/.hermes/profiles/<target-profile>/skills -name "<skill-name>*"
```

If empty, either (a) use the full category-prefixed path (`gaming/greyhack-greyscript`, `voice-assistant-bots/discord-voice`), (b) reassign to a profile that has it, or (c) drop the pin entirely. The fastest recovery is `hermes kanban reassign <id> <profile-with-skill> --reclaim --reason "..."`.

**`hermes kanban diagnostics` is the first stop for any "why is this task still ready?" question.** Running it once per board reveals all `stranded_in_ready` warnings with severity (warning at 30 min, error at 1h, critical at 3h) plus the specific failure mode (no assignee, skill-pin crash, spawn_failed, repeated_crashes). Don't guess — read the diagnostics first, then act.

**Worktree workspaces need a Git-Repo default-workdir, not a parent directory.** `hermes kanban create --workspace worktree --branch feat/X` requires EITHER an explicit `worktree:/absolute/path/to/git-repo` OR the board's `default_workdir` must be set to an actual git repo via `hermes kanban boards set-default-workdir <slug> <path>`. Setting it to a multi-repo parent directory (e.g. `~/10-Projekte/10-active`) fails with `board default_workdir '/path' is not inside a git repo`. The error message is clear if you read it; the failure mode is `spawn_failed` x2 → auto-block via circuit breaker, requiring an unblock + retry after fixing the workdir.

**`hermes config set` flattens list-typed config keys into strings.** Calling `hermes config set kanban.notification_sources '["*"]'` produces a YAML scalar `notification_sources: '["*"]'` (single-quoted string), not the YAML list `notification_sources: ['*']`. For list-typed keys, edit `~/.hermes/config.yaml` directly. Round-trip the fix with `grep -E "notification_sources" ~/.hermes/config.yaml` to confirm the value is unquoted (or uses `[]` list syntax, not `''` string syntax).

**`hermes kanban edit` is BACKFILL-only — it does not mutate active task config.** The edit verb's only flags are `--result`, `--summary`, `--metadata` for already-completed tasks. To change `max_runtime`, `workspace`, `branch`, `skills`, or `idempotency_key` on a ready/blocked task, you must archive and re-create. For `assignee` changes specifically, use `hermes kanban reassign <id> <profile> [--reclaim] [--reason "..."]`. Knowing this saves you from debugging "why doesn't my edit command do anything."

**Run `hermes kanban gc` periodically to reclaim disk from done tasks.** Default retention is 30 days for both events and worker logs (`--event-retention-days N`, `--log-retention-days N`). On a busy board, run it after large dispatch waves — workspaces + logs can grow to hundreds of MB. The command is non-destructive: it only removes workspace dirs and log files for terminal tasks older than the retention window, never the SQLite rows.

## Goal-mode cards (persistent workers)

By default a dispatched worker gets **one shot** at its card: it does its work, calls `kanban_complete`/`kanban_block`, and exits. For open-ended cards where one turn rarely finishes the job, pass `goal_mode=True` to wrap that worker in a Ralph-style goal loop — the same engine behind the `/goal` slash command:

```python
kanban_create(
    title="Translate the full docs site to French",
    body="Acceptance: every page translated, no English left, links intact.",
    assignee="<translator-profile>",
    goal_mode=True,        # judge re-checks the card after each turn
    goal_max_turns=15,     # optional budget (default 20)
)["task_id"]
```

How it behaves:
- After each worker turn, an auxiliary judge evaluates the worker's response against the card's **title + body** (treated as the acceptance criteria).
- Not done + budget remains → the worker keeps going **in the same session** (full context retained — not a fresh respawn).
- Worker calls `kanban_complete`/`kanban_block` itself → loop stops, normal lifecycle.
- Budget exhausted without completion → the card is **blocked** for human review (sticky), never a silent exit.

When to use it: long, multi-step, or "keep going until X is true" cards. When NOT to: cheap one-shot cards (translation of a single string, a quick lookup) — the judge overhead isn't worth it, and the dispatcher's existing retry/circuit-breaker already handles transient worker failures.

Write the body as **explicit acceptance criteria** — the judge is only as good as the goal text. "Translate the README" is weaker than "Translate every section of the README to French; no English sentences remain."

## Recovering stuck workers

When a worker profile keeps crashing, hallucinating, or getting blocked by its own mistakes (usually: wrong model, missing skill, broken credential), the kanban dashboard flags the task with a ⚠ badge and opens a **Recovery** section in the drawer. Three primary actions:

1. **Reclaim** (or `hermes kanban reclaim <task_id>`) — abort the running worker immediately and reset the task to `ready`. The existing claim TTL is ~15 min; this is the fast path out.
2. **Reassign** (or `hermes kanban reassign <task_id> <new-profile> --reclaim`) — switch the task to a different profile (one that exists on this setup) and let the dispatcher pick it up with a fresh worker.
3. **Change profile model** — the dashboard prints a copy-paste hint for `hermes -p <profile> model` since profile config lives on disk; edit it in a terminal, then Reclaim to retry with the new model.

## Hallucination warnings

A worker's `kanban_complete(created_cards=[...])` claim can include card ids that don't exist or weren't created by the worker's profile — the gate blocks the completion, and an audit event is recorded. Similarly, free-form summary text that references `t_<hex>` ids that don't resolve triggers an advisory prose scan (non-blocking). Both events persist even after recovery actions, so the audit trail stays for debugging.

## See Also

- `references/diagnostics-recipes.md` — Session-tested recipes for diagnosing stranded tasks, worker crashes, circuit-breaker recovery, bulk-assigning backlogs, and coverage-map methodology. Pair with the **Pitfalls** section above (what goes wrong → how to verify and fix).
- `references/coverage-rollout-2026-07-09.md` — Concrete 4-phase rollout (Baseline → Unblock → Maturity → Advanced → Bienen-Dispatch) with the exact sequence that took a dormant 51-task system from 40% to 88% coverage in one session. Includes the Bienen-Dispatch recipe and the per-profile skill-map observation.
