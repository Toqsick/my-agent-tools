# Skeleton A — Generic Master/Worker (Queen-Bee Fan-out)

**Pattern:** Queen-Bee Fan-out. Queen plant + aggregiert; N Leaf-Worker laufen parallel. Uses `asyncio.Semaphore` für Rate-Control und `asyncio.wait_for` für Wall-Clock-Kill. Idempotency-Keys verhindern Double-Charge auf Retry.

**Quelle:** Perplexity Deep Research 2026-07-15 (Anthropic Engineering Post June 2025 + Hermes delegation docs).

```python
"""
master_worker.py  —  Production-grade Queen-Bee / Master-Worker orchestrator.

Wires together:
  - asyncio fan-out (parallel workers)
  - per-task wall-clock timeout
  - exponential-backoff retry with jitter
  - idempotency keys (prevent double-execution on retry)
  - structured AgentResult dataclass (validated, not raw LLM string)
  - Semaphore-based rate limiter (prevents API storm)
  - Audit trail: every dispatch + result appended to ~/.hermes/logs/

Replace _run_leaf_agent() with your real API call
(Hermes delegate_task, Claude claude-3-5-haiku, OpenAI, etc.)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── logging ──────────────────────────────────────────────────────────────────
LOG_DIR = Path.home() / ".hermes" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s  %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "orchestrator.log"),
    ],
)
log = logging.getLogger("queen")


# ── Data contracts ────────────────────────────────────────────────────────────

@dataclass
class WorkerTask:
    """What the Queen hands to each leaf worker."""
    goal: str
    context: str
    toolsets: list[str]
    # Idempotency key: same task_id -> skip if already completed in this session
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    max_iterations: int = 20
    timeout_seconds: float = 300.0   # wall-clock kill

@dataclass
class AgentResult:
    task_id: str
    status: str                  # "success" | "failed" | "timeout" | "skipped"
    output: dict[str, Any]       # structured — validated before use
    wall_clock_seconds: float
    tokens_used: int = 0
    retries: int = 0
    error: str | None = None


# ── Idempotency store (in-process; swap for Redis in multi-process) ───────────

_completed: dict[str, AgentResult] = {}   # task_id -> result


def _idempotency_key(task: WorkerTask) -> str:
    """Stable key = sha256(goal + context).  Same content -> same key."""
    raw = f"{task.goal}||{task.context}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── Stub: replace with your real agent call ───────────────────────────────────

async def _run_leaf_agent(task: WorkerTask) -> dict[str, Any]:
    """
    TODO: Replace this stub with your real implementation.

    For Hermes delegate_task (sync wrapper in async context):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: delegate_task(
                goal=task.goal,
                context=task.context,
                toolsets=task.toolsets,
                max_iterations=task.max_iterations,
            )
        )
        return result

    For direct Anthropic API (claude-3-5-haiku):
        import anthropic
        client = anthropic.AsyncAnthropic()
        msg = await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2048,
            messages=[{"role": "user", "content": f"{task.context}\n\n{task.goal}"}]
        )
        return {"output": msg.content.text, "stop_reason": msg.stop_reason}
    """
    await asyncio.sleep(random.uniform(0.5, 2.0))   # simulate latency
    return {"output": f"[stub result for: {task.goal[:40]}]", "files_modified": []}


# ── Core retry wrapper ────────────────────────────────────────────────────────

async def _dispatch_with_retry(
    task: WorkerTask,
    max_retries: int = 3,
    base_backoff: float = 1.0,
) -> AgentResult:
    """
    Single-task dispatcher:  timeout  +  exponential backoff  +  idempotency.

    Key rules from production audits:
      - Never retry a semantic failure (schema invalid, goal impossible).
      - Always retry transient failures (timeout, rate-limit 429, network).
      - Add jitter: backoff *= random(0.5, 1.5)  to prevent thundering herd.
    """
    idem_key = _idempotency_key(task)
    if idem_key in _completed:
        log.info("SKIP (idempotent)  task_id=%s  key=%s", task.task_id, idem_key)
        result = _completed[idem_key]
        result.status = "skipped"
        return result

    last_err: Exception | None = None
    t0 = time.monotonic()

    for attempt in range(max_retries + 1):
        if attempt > 0:
            backoff = base_backoff * (2 ** (attempt - 1)) * random.uniform(0.5, 1.5)
            log.warning("RETRY  task_id=%s  attempt=%d  backoff=%.1fs", task.task_id, attempt, backoff)
            await asyncio.sleep(backoff)

        try:
            raw = await asyncio.wait_for(
                _run_leaf_agent(task),
                timeout=task.timeout_seconds,
            )

            # ── Schema validation: NEVER trust raw LLM output directly ────────
            if not isinstance(raw, dict):
                raise ValueError(f"Expected dict from agent, got {type(raw)}")

            result = AgentResult(
                task_id=task.task_id,
                status="success",
                output=raw,
                wall_clock_seconds=time.monotonic() - t0,
                retries=attempt,
            )
            _completed[idem_key] = result   # register for idempotency
            log.info("SUCCESS  task_id=%s  retries=%d  elapsed=%.1fs",
                     task.task_id, attempt, result.wall_clock_seconds)
            return result

        except asyncio.TimeoutError:
            last_err = asyncio.TimeoutError(
                f"task_id={task.task_id} timed out after {task.timeout_seconds}s"
            )
            log.error("TIMEOUT  task_id=%s  attempt=%d", task.task_id, attempt)
            # Timeouts ARE retried (transient)

        except ValueError as e:
            # Semantic failure — DON'T retry
            log.error("SCHEMA_FAIL  task_id=%s  %s", task.task_id, e)
            return AgentResult(
                task_id=task.task_id,
                status="failed",
                output={},
                wall_clock_seconds=time.monotonic() - t0,
                error=str(e),
            )

        except Exception as e:
            last_err = e
            log.error("ERROR  task_id=%s  attempt=%d  %s", task.task_id, attempt, e)

    return AgentResult(
        task_id=task.task_id,
        status="failed",
        output={},
        wall_clock_seconds=time.monotonic() - t0,
        retries=max_retries,
        error=str(last_err),
    )


# ── Queen Orchestrator ────────────────────────────────────────────────────────

class QueenOrchestrator:
    """
    Queen-Bee pattern:
      1. Queen PLANS -> produces WorkerTask list (she never does leaf work)
      2. Queen FANS-OUT -> N parallel workers, concurrency-capped
      3. Queen AGGREGATES -> structured results, failures handled

    Model tiering:
      Queen:   expensive model (Opus / Sonnet) — planning + synthesis
      Workers: cheap model   (Haiku / Flash)   — leaf execution
    """

    def __init__(
        self,
        max_concurrent_workers: int = 4,
        default_worker_timeout: float = 300.0,
    ):
        self._sem = asyncio.Semaphore(max_concurrent_workers)
        self._default_timeout = default_worker_timeout
        self._audit: list[dict] = []

    async def plan(self, high_level_goal: str) -> list[WorkerTask]:
        """
        TODO: Replace with real Queen planning call.
        For Hermes: Queen agents calls delegate_task(tasks=[...]) directly.
        For direct API: call planner_llm and parse response.
        """
        log.info("PLAN  goal='%s'", high_level_goal[:60])
        return [
            WorkerTask(
                goal=f"Subtask {i+1}: process aspect {i+1} of '{high_level_goal[:30]}'",
                context=f"Parent goal: {high_level_goal}. Focus on aspect {i+1}.",
                toolsets=["web"] if i == 0 else ["terminal", "file"],
                timeout_seconds=self._default_timeout,
            )
            for i in range(3)
        ]

    async def _guarded_dispatch(self, task: WorkerTask) -> AgentResult:
        """Semaphore-guarded dispatch: enforces max_concurrent_workers."""
        async with self._sem:
            result = await _dispatch_with_retry(task)
            self._audit.append({
                "ts": time.time(),
                "task_id": result.task_id,
                "status": result.status,
                "elapsed": result.wall_clock_seconds,
            })
            return result

    async def run(self, high_level_goal: str) -> dict[str, Any]:
        t0 = time.monotonic()
        tasks = await self.plan(high_level_goal)
        log.info("FANOUT  tasks=%d", len(tasks))

        results: list[AgentResult] = await asyncio.gather(
            *[self._guarded_dispatch(t) for t in tasks],
            return_exceptions=False,
        )

        successes = [r for r in results if r.status in ("success", "skipped")]
        failures  = [r for r in results if r.status not in ("success", "skipped")]

        log.info(
            "AGGREGATE  success=%d  fail=%d  elapsed=%.1fs",
            len(successes), len(failures), time.monotonic() - t0,
        )

        audit_path = LOG_DIR / f"run-{int(time.time())}.json"
        audit_path.write_text(json.dumps(self._audit, indent=2))

        # TODO: call your Queen/synthesis model here with successes[].output
        synthesis = {
            "goal": high_level_goal,
            "tasks_total": len(tasks),
            "tasks_ok": len(successes),
            "tasks_failed": len(failures),
            "wall_clock": round(time.monotonic() - t0, 2),
            "worker_outputs": [r.output for r in successes],
            "failures": [{"task_id": r.task_id, "error": r.error} for r in failures],
        }
        return synthesis


async def main():
    queen = QueenOrchestrator(max_concurrent_workers=4)
    result = await queen.run("Research and summarise the top 3 GreyHack mission patterns")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
```

## Hermes Config für dieses Skeleton

```yaml
# ~/.hermes/config.yaml
delegation:
  max_concurrent_children: 4      # tune to your OpenRouter rate limit
  max_spawn_depth: 1              # flat — workers cannot re-delegate
  child_timeout_seconds: 300
  model: "google/gemini-flash-2.0"  # cheap model for leaf workers
  provider: "openrouter"
```