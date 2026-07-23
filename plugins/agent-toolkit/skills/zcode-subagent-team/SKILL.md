---
name: zcode-subagent-team
description: ZCode SubAgent Team — a Hermes-Kanban multi-lane agent swarm where a Queen (GLM ZCode orchestrator/verifier) delegates bulk work to MiniMax-M3 workers across General / Vision / Coder / Debug / Verify / Quality-Gate lanes, all routed through Hermes. Use when orchestrating a staged, multi-lane coding or debugging pipeline; pairs with the zc-* subagents shipped in this toolkit.
---

# SKILL: ZCode SubAgent Team

A Hermes-Kanban runtime + orchestrator for a multi-lane agent swarm. Designed
for GLM ZCode (orchestrator/verifier) delegating bulk work to MiniMax-M3
workers, all routed through the locally-installed Hermes v0.19.0.

```
Queen (ZCode/GLM orchestrator)
    │
    ├── Lane 1: General       ← research, context, planning
    ├── Lane 2: Vision        ← screenshots, UI/code-diff, diagrams   [Phase 3]
    ├── Lane 3: Coder         ← implementation, refactoring, tests
    ├── Lane 4: Debug         ← root-cause debugging, minimal fixes   [Phase 2]
    ├── Lane 5: Verify        ← lint, tests, type-check, correctness
    └── Lane 6: Quality Gate  ← PASS / RETRY / BLOCK decision          [Phase 3]
```

## ZCode-native subagent mirrors

The 6 roles are also authored as **ZCode-native subagent Markdown files** at
`zcode-agents/{general,vision,coder,debug,verify,gate}.md`. These surface in
ZCode's Settings → Subagents tab for single-role dispatch from inside a ZCode
session. They ship as a **plugin package** under `plugin/` (manifest +
`agents/` symlinks → the canonical `zcode-agents/*.md`), because ZCode
discovers subagents only from an enabled plugin's `agents/` subdir
(`~/.zcode/agents/` is not scanned).

Prepare the package and install it via the Discover UI:

```bash
bash scripts/install_zcode_agents.sh   # prepares plugin/ + prints the UI steps
# Then: Discover → '+' → paste .../zcode-subagent-team/plugin → Install → restart
```

The `.md` files are synthesized from this same roster (`toolset_policy.py` +
`orchestrator.py` lane builders + `hermes_runtime.py` worker contract) — two
surfaces, one source of truth. See README.md § "ZCode Subagents integration"
for the format constraints (`model: inherit` since ZCode's model field only
accepts `inherit|sonnet|opus|haiku`, not `MiniMax-M3`; role temperatures travel
in the body as run guidance).

## Current status

**Phase 1 (live):** General → Coder → Verify, simulation runtime, corrected
Hermes adapter, 3 profiles, smoke test. Run:

```bash
cd /home/bratan/10-Projekte/10-active/zcode-subagent-team
python scripts/smoke_test.py --self-test          # 3-lane simulation
pytest -q                                          # full unit + smoke suite
bash scripts/setup_board.sh                        # create Hermes board + profiles
```

**Phase 2 (planned):** Debug lane + conditional dispatch (`should_spawn_debug`
logic is already implemented and tested; wiring into the default pipeline is
the remaining work).

**Phase 3 (planned):** Vision + Quality Gate lanes, Pydantic v2 shard
contracts (`src/zcode_swarm/contracts.py`).

## Reality vs. the design doc

This skill is the **implementation** of the design captured in
`~/Downloads/SubAgent Team _ General, Vison, Coder, Verify and.md`. That doc
was written from public Hermes docs and is **factually wrong in 5 places**
that this implementation corrects. Future agents: trust this code + the tests,
not the doc.

| Doc claim | Reality (verified on this machine) |
| :-- | :-- |
| `hermes profile create X --tools "a,b" --model M` | **`--tools` and `--model` do not exist.** Profiles are created via CLI, then configured by writing `<profile>/config.yaml` (`model.provider`/`model.default` + `toolsets:` list). |
| `hermes kanban ls --board X` | **`--board` is a GLOBAL flag BEFORE the subcommand:** `hermes kanban --board X ls`. Placing it after the subcommand fails. |
| task id field `id` / `task_id` (flat) | `show --json` wraps under `{"task": {...}}` → id is `task.id`. Flat `task_id` appears only in `diagnostics --json`. The adapter handles both. |
| status values `completed`/`complete`/`pass` | Verified vocab: `{archived, blocked, done, ready, review, running, scheduled, todo, triage}`. `done` is success. Legacy spellings are normalized. |
| `confidence` field on task/runs | **No native field exists.** Stuff via `kanban complete --metadata '{"confidence":N}'`; the adapter harvests it back from `runs[-1].metadata`. |
| timestamps ISO-8601 | **Epoch seconds** (int). Adapter converts. |
| `boards create --slug X` | **Positional slug:** `boards create X`. |
| summary at `task.summary` | Top-level `latest_summary` (show) or per-run `summary` (runs). |

## Architecture

- `src/zcode_swarm/toolset_policy.py` — 6-role roster: toolsets (coarse,
  enforced) + per-tool allow/deny rules (prompt-layer, best-effort) +
  generation tweaks.
- `src/zcode_swarm/profiles.py` — generates each profile's `config.yaml`
  overlay. Single source of truth for `scripts/setup_board.sh`.
- `src/zcode_swarm/hermes_runtime.py` — the corrected adapter: task
  create/show/runs, defensive schema-aware field extraction, shard
  materialization.
- `src/zcode_swarm/orchestrator.py` — lane builders, `should_spawn_debug`,
  simulation runtime, `execute_pipeline_for_subtask`.
- `scripts/setup_board.sh` — idempotent board + profile creation.
- `scripts/smoke_test.py` — Phase 1 exit-criteria check.
- `tests/` — unit tests for schema parsing, debug logic, and the 3-lane smoke.

## Tool gating policy

Hermes profiles gate by **toolsets** (coarse groups: `hermes-cli`, `web`),
not individual tools. The doc's per-agent fine-grained allowlists (Coder gets
`file_write`, Verify doesn't, etc.) are therefore enforced in **two layers**:

1. **Toolset assignment** in `config.yaml` (enforced by Hermes).
2. **Prompt rules** — `toolset_policy.render_tool_rules()` emits an explicit
   ALLOW/FORBIDDEN tool list into every worker contract body.

A hard PreToolUse-style enforcement layer is a documented Phase 2+ follow-up.

## Generation tuning

Temperature descends from General (0.30, planning) to Quality Gate (0.05,
deterministic judgment) — more creativity up front, more determinism at the
exit. Where Hermes config supports a key (`agent.max_turns`,
`agent.reasoning_effort`), it's pinned in `config.yaml`; unsupported keys
(`temperature`, `top_p`, `max_tokens`) travel in the worker contract body as
run guidance.
