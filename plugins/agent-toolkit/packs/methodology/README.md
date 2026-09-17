# Pack: Engineering Methodology

**Category:** development · **Skills:** 2

2 multi-agent orchestration skills — the ZCode SubAgent Team (GLM Queen + MiniMax-M3 workers across General/Vision/Coder/Debug/Verify lanes) and Queen-Bee swarm dispatch.

The multi-agent orchestration layer: the ZCode SubAgent Team for staged, multi-lane coding/debugging pipelines, and Queen-Bee swarm dispatch for parallel subagents with affinity-safe briefs. Use these when orchestrating multiple agents. The former Superpowers workflow forks and the multi-agent master workflow were removed — the canonical Superpowers set lives in the official plugin.

## When to use this pack

See the trigger words in each skill's description. This pack is the right starting point when the task falls in this domain; the `/toolkit <pack>` command lists these skills interactively.

## Skills

| Skill | What it does |
|---|---|
| `zcode-subagent-team` | ZCode SubAgent Team — a Hermes-Kanban multi-lane agent swarm where a Queen (GLM ZCode orchestrator/verifier) delegates bulk work to MiniMax-M3 workers… |
| `queen-bee-schwarm-dispatch` | Use when user asks to orchestrate parallel subagents, dispatch a Queen-Bee swarm, run orthogonal scouts, or audit separate artifacts concurrently. NOT… |
