# Skeleton B — Hierarchical Tree mit `role='orchestrator'`

**Pattern:** Zwei-Ebenen-Baum. Root Queen spawns L1 Sub-Orchestratoren; jeder L1 Sub-Orchestrator spawns seine eigenen Leaf-Worker. Direkte Abbildung auf Hermes `delegate_task(role='orchestrator', ...)` mit `max_spawn_depth: 2`. Enthält Correlation-IDs für Full-Tracing und einen harten Budget-Cap.

**Quelle:** Perplexity Deep Research 2026-07-15.

```python
"""
hierarchical_tree.py  —  Two-level Hierarchical Orchestrator.

Level 0  (Root Queen)    :  decomposes goal into domains
Level 1  (Sub-Orch)      :  role='orchestrator'  — each owns a sub-domain
Level 2  (Leaf workers)  :  role='leaf'           — do actual work

Hermes config required:
  delegation:
    max_spawn_depth: 2          # enables L1 -> L2 spawn
    max_concurrent_children: 3
    model: "google/gemini-flash-2.0"

Key safety rails:
  - correlation_id threads from Root -> L1 -> L2 (full trace)
  - per_subtree_token_budget: kills any sub-tree that overruns
  - max_depth guard: raises if depth > MAX_SAFE_DEPTH
  - context handoff packet: ONLY structured JSON crosses boundaries
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LOG_DIR = Path.home() / ".hermes" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("tree")

MAX_SAFE_DEPTH = 2
SUBTREE_TOKEN_BUDGET = 50_000


# ── Handoff packet: the ONLY thing that crosses level boundaries ──────────────

@dataclass
class HandoffPacket:
    """
    Structured context passed to every sub-orchestrator or leaf.
    Subagents start with ZERO knowledge of parent conversation.
    Keep it minimal: fat packets = context explosion at L2.
    """
    task_id: str
    correlation_id: str
    depth: int
    goal: str
    constraints: list[str]
    relevant_artifacts: list[str]
    output_schema: dict[str, str]
    parent_summary: str = ""


@dataclass
class SubtreeResult:
    task_id: str
    correlation_id: str
    depth: int
    status: str
    output: dict[str, Any]
    tokens_used: int = 0
    wall_clock: float = 0.0
    children: list["SubtreeResult"] = field(default_factory=list)
    error: str | None = None


# ── Stubs: replace with real Hermes / API calls ───────────────────────────────

async def _call_sub_orchestrator(packet: HandoffPacket) -> SubtreeResult:
    """
    TODO: Replace with Hermes delegate_task(role='orchestrator', ...).
    In Hermes (sync inside async via run_in_executor):
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(None, lambda: delegate_task(
            goal=packet.goal,
            context=json.dumps({
                "constraints": packet.constraints,
                "relevant_artifacts": packet.relevant_artifacts,
                "correlation_id": packet.correlation_id,
                "depth": packet.depth,
                "output_schema": packet.output_schema,
            }),
            role="orchestrator",     # allows L1 -> L2 delegation
            toolsets=["terminal", "file", "web"],
            max_iterations=30,
        ))
        return SubtreeResult(...)
    """
    await asyncio.sleep(1.0)
    return SubtreeResult(
        task_id=packet.task_id,
        correlation_id=packet.correlation_id,
        depth=packet.depth,
        status="success",
        output={"result": f"[L{packet.depth} stub: {packet.goal[:40]}]"},
        wall_clock=1.0,
    )


async def _call_leaf_worker(packet: HandoffPacket) -> SubtreeResult:
    await asyncio.sleep(0.8)
    return SubtreeResult(
        task_id=packet.task_id,
        correlation_id=packet.correlation_id,
        depth=packet.depth,
        status="success",
        output={"leaf_result": f"[L{packet.depth} leaf stub: {packet.goal[:40]}]"},
        wall_clock=0.8,
    )


# ── Token budget guard ────────────────────────────────────────────────────────

class BudgetExceeded(Exception):
    pass


class TokenBudget:
    def __init__(self, cap: int):
        self._cap = cap
        self._used = 0

    def charge(self, tokens: int, label: str):
        self._used += tokens
        if self._used > self._cap:
            raise BudgetExceeded(
                f"Token budget {self._cap} exceeded at '{label}' (cumulative: {self._used})"
            )

    @property
    def remaining(self) -> int:
        return max(0, self._cap - self._used)


# ── Hierarchical dispatcher ───────────────────────────────────────────────────

class HierarchicalOrchestrator:
    def __init__(self, max_concurrent_per_level: int = 3, subtree_token_budget: int = SUBTREE_TOKEN_BUDGET):
        self._sem = asyncio.Semaphore(max_concurrent_per_level)
        self._budget = TokenBudget(subtree_token_budget)

    def _make_correlation_id(self) -> str:
        return uuid.uuid4().hex[:12]

    async def _dispatch(self, packet: HandoffPacket) -> SubtreeResult:
        if packet.depth > MAX_SAFE_DEPTH:
            log.error("DEPTH GUARD  task_id=%s  depth=%d  MAX=%d", packet.task_id, packet.depth, MAX_SAFE_DEPTH)
            return SubtreeResult(
                task_id=packet.task_id, correlation_id=packet.correlation_id,
                depth=packet.depth, status="failed", output={},
                error=f"max_spawn_depth={MAX_SAFE_DEPTH} exceeded",
            )

        async with self._sem:
            t0 = time.monotonic()
            try:
                if packet.depth < MAX_SAFE_DEPTH:
                    log.info("SUB-ORCH  corr=%s  depth=%d  goal='%s'", packet.correlation_id, packet.depth, packet.goal[:50])
                    result = await asyncio.wait_for(_call_sub_orchestrator(packet), timeout=600.0)
                else:
                    log.info("LEAF      corr=%s  depth=%d  goal='%s'", packet.correlation_id, packet.depth, packet.goal[:50])
                    result = await asyncio.wait_for(_call_leaf_worker(packet), timeout=300.0)

                result.wall_clock = time.monotonic() - t0
                self._budget.charge(result.tokens_used, label=packet.goal[:40])
                return result
            except asyncio.TimeoutError:
                return SubtreeResult(task_id=packet.task_id, correlation_id=packet.correlation_id,
                    depth=packet.depth, status="timeout", output={},
                    wall_clock=time.monotonic() - t0, error="wall-clock timeout")
            except BudgetExceeded as e:
                log.error("BUDGET  %s", e)
                return SubtreeResult(task_id=packet.task_id, correlation_id=packet.correlation_id,
                    depth=packet.depth, status="failed", output={}, error=str(e))

    async def run(self, high_level_goal: str, subdomains: list[dict]) -> dict[str, Any]:
        """
        Entry point for two-level tree execution.
        subdomains from Root Queen's planning call. Each -> one L1 sub-orch -> N L2 leaves.

        Example (5-agent code-gen pipeline):
          subdomains = [
            {"domain": "research",   "goal": "Find best patterns for GreyHack missions",
             "artifacts": [], "output_schema": {"patterns": "list[str]"}},
            {"domain": "implement",  "goal": "Implement from research",
             "artifacts": ["/tmp/research.json"], "output_schema": {"files_created": "list[str]"}},
            {"domain": "review",     "goal": "Security review",
             "artifacts": ["/tmp/implement.json"], "output_schema": {"issues": "list[str]"}},
          ]
        """
        corr_id = self._make_correlation_id()
        t0 = time.monotonic()
        log.info("ROOT  corr=%s  goal='%s'  domains=%d", corr_id, high_level_goal[:60], len(subdomains))

        packets = [
            HandoffPacket(
                task_id=uuid.uuid4().hex[:8],
                correlation_id=corr_id,
                depth=1,
                goal=sd["goal"],
                constraints=sd.get("constraints", []),
                relevant_artifacts=sd.get("artifacts", []),
                output_schema=sd.get("output_schema", {"result": "str"}),
                parent_summary=f"Parent goal: {high_level_goal[:150]}",
            )
            for sd in subdomains
        ]

        l1_results: list[SubtreeResult] = await asyncio.gather(
            *[self._dispatch(p) for p in packets],
            return_exceptions=False,
        )

        successes = [r for r in l1_results if r.status == "success"]
        failures = [r for r in l1_results if r.status != "success"]

        log.info("ROOT DONE  corr=%s  ok=%d  fail=%d  elapsed=%.1fs",
                 corr_id, len(successes), len(failures), time.monotonic() - t0)

        trace_path = LOG_DIR / f"tree-{corr_id}.json"
        trace_path.write_text(json.dumps(
            [{"task_id": r.task_id, "status": r.status, "depth": r.depth, "wall_clock": r.wall_clock}
             for r in l1_results],
            indent=2,
        ))
        log.info("TRACE  -> %s", trace_path)

        return {
            "correlation_id": corr_id,
            "goal": high_level_goal,
            "subtrees_ok": len(successes),
            "subtrees_failed": len(failures),
            "total_wall_clock": round(time.monotonic() - t0, 2),
            "outputs": [r.output for r in successes],
            "failures": [{"task_id": r.task_id, "error": r.error} for r in failures],
        }


async def main():
    orch = HierarchicalOrchestrator(max_concurrent_per_level=3)
    subdomains = [
        {"domain": "research",   "goal": "Research GreyHack mission automation patterns; list 5 approaches",
         "artifacts": [], "output_schema": {"patterns": "list[str]", "recommended": "str"}},
        {"domain": "implement",  "goal": "Implement GreyScript mission runner using recommended pattern",
         "artifacts": ["/tmp/research.json"], "output_schema": {"files_created": "list[str]", "tests_pass": "bool"}},
        {"domain": "review",     "goal": "Security review the implemented mission runner for prompt-injection vectors",
         "artifacts": ["/tmp/implement.json"], "output_schema": {"issues": "list[str]", "severity": "str"}},
    ]
    result = await orch.run(
        high_level_goal="Build a GreyHack mission automation runner with security review",
        subdomains=subdomains,
    )
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
```

## Hermes Config für dieses Skeleton

```yaml
# ~/.hermes/config.yaml
delegation:
  max_concurrent_children: 3
  max_spawn_depth: 2            # enables role='orchestrator' children
  orchestrator_enabled: true
  child_timeout_seconds: 300
  model: "google/gemini-flash-2.0"
  provider: "openrouter"
```