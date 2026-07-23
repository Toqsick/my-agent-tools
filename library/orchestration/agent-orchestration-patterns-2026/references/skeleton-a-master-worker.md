# Skeleton A — Queen-Bee / Master-Worker

**Source:** `~/10-Projekte/10-active/agent-orchestration-patterns/master_worker.py` (459 LOC, 17 KB)
**Pattern:** Queen-Bee Fan-Out — N parallele Leaf-Worker
**Use-Case:** Tasks zerlegbar in ≥2 unabhängige Subtasks, parallel ausführbar

## Architektur-Übersicht

```
                    ┌─────────────┐
                    │   Queen     │  (teuer: Sonnet/Opus)
                    │   (plan +   │
                    │   aggregate)│
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │Worker 1 │  │Worker 2 │  │Worker 3 │  (günstig: Haiku/Flash)
        │(parallel│  │(parallel│  │(parallel│
        │ asyncio)│  │ asyncio)│  │ asyncio)│
        └────┬────┘  └────┬────┘  └────┬────┘
             │            │            │
             ▼            ▼            ▼
        [success]    [success]    [failed]
                           │
                           ▼
                    ┌─────────────┐
                    │  Queen      │
                    │  Aggregate  │
                    │  + Audit    │
                    └─────────────┘
```

## Wann nutzen

✅ **Ja:**
- Task hat ≥2 unabhängige Subtasks (z.B. "researche A, B, C parallel")
- Subtasks brauchen KEINE Verifikation
- Cost-Sensitivität hoch (cheap-Worker für Volume)
- Single-Domain (kein Cross-Domain-Routing nötig)

❌ **Nein:**
- Nur 1 Subtask → direkt ausführen, kein Overhead
- Subtasks haben Dependencies → Pipeline-Pattern (nicht hier)
- Multi-Domain mit Routing → Skeleton B (Tree)
- Korrektheit kritisch → Skeleton C (Critic-Loop)

## Kern-Komponenten

### 1. WorkerTask (Input-Datenstruktur)

```python
@dataclass
class WorkerTask:
    goal: str                    # Was der Worker tun soll
    context: str                 # Parent-Context (meist High-Level-Goal)
    toolsets: list[str]          # ["terminal", "file", "web"] etc.
    task_id: str                 # UUID-Prefix (8 chars)
    max_iterations: int          # Cap für Worker-Loop (default 20)
    timeout_seconds: float       # Wall-Clock-Cap (default 300s)
    model: str                   # "google/gemini-flash-2.0" (cheap default)
```

### 2. AgentResult (Output-Datenstruktur)

```python
@dataclass
class AgentResult:
    task_id: str
    status: str                  # "success" | "failed" | "timeout" | "skipped"
    output: dict[str, Any]       # strukturierte Output (NICHT raw LLM-String!)
    wall_clock_seconds: float
    tokens_used: int
    retries: int
    error: str | None
```

### 3. QueenOrchestrator (Hauptklasse)

```python
queen = QueenOrchestrator(
    max_concurrent_workers=4,           # Semaphore-Cap
    default_worker_timeout=300.0,
    queen_model="anthropic/claude-sonnet-4-5",
    worker_model="google/gemini-flash-2.0",
)

result = await queen.run(high_level_goal, dry_run=False)
```

**Queen-Methoden:**
- `plan(high_level_goal)` → list[WorkerTask] — TODO: LLM-Integration (aktuell Stub)
- `_guarded_dispatch(task)` → AgentResult — Semaphore-bewacht
- `run(high_level_goal)` → dict — Full-Cycle: plan → fan-out → aggregate

## 3-strategige Hermes-Bridge

Jeder Worker-Call durchläuft diese 3 Stufen:

```python
async def _call_leaf_worker(task: WorkerTask, dry_run: bool) -> dict:
    # 1. Dry-Run-Stub (schnell + deterministisch)
    if dry_run:
        await asyncio.sleep(random.uniform(0.3, 0.8))
        return {"output": "[DRY-RUN STUB]", "tokens_used": random.randint(800, 2500)}

    # 2. hermes_tools.delegate_task (echte Integration)
    if HERMES_TOOLS_AVAILABLE:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: _hermes_delegate(
                goal=task.goal,
                context=task.context,
                toolsets=task.toolsets,
                max_iterations=task.max_iterations,
                model=task.model,
            ),
        )
        return result

    # 3. Subprocess-Fallback auf `hermes chat -z`
    proc = await asyncio.create_subprocess_exec(
        "hermes", "chat", "-z", f"{task.context}\n\n{task.goal}",
        "--toolsets", ",".join(task.toolsets),
        "--model", task.model,
        ...
    )
```

**Warum 3 Stufen:** Kontext-unabhängig lauffähig. Funktioniert in Hermes-Session, als Cron, als Standalone.

## Sicherheitsschienen (in diesem Skeleton)

| Rail | Code-Stelle | Was es verhindert |
|---|---|---|
| **Idempotency-Cache** | `_dispatch_with_retry()` | Doppel-Execution bei Retry |
| **Exponential Backoff + Jitter** | `_dispatch_with_retry()` | Thundering-Herd auf Retries |
| **Timeout (asyncio.wait_for)** | `_dispatch_with_retry()` | Runaway-Worker |
| **Schema-Validation** | nach `_call_leaf_worker()` | Roher LLM-Output direkt genutzt |
| **Semaphore** | `QueenOrchestrator._sem` | API-Storm / Rate-Limit-Verletzung |
| **Audit-Trail (JSON)** | `run()` Methode | Nicht-replay-bare Runs |

## CLI

```bash
# Dry-Run (kein API-Verbrauch)
python3 master_worker.py --dry-run "Researche GreyHack Mission-Patterns"

# Echte LLM-Calls
python3 master_worker.py "Researche GreyHack Mission-Patterns"

# Custom-Parameter
python3 master_worker.py --workers 8 --timeout 60 --queen-model claude-opus-4 --worker-model gpt-4o-mini "..."

# Output in Datei
python3 master_worker.py --dry-run "..." --output /tmp/run.json

# Exit-Code: 0 wenn alle ok, 1 wenn Failures
```

## Echte Verifizierung (Dry-Run-Output)

```
$ python3 master_worker.py --dry-run "Researche GreyHack Mission-Patterns"
2026-07-16 04:29:01 [queen] INFO  PLAN  goal='Researche...'  model=anthropic/claude-sonnet-4-5
2026-07-16 04:29:01 [queen] INFO  FAN-OUT  tasks=3  concurrency_cap=4
2026-07-16 04:29:01 [queen] INFO  SUCCESS  task_id=4a859b01  retries=0  elapsed=0.4s
2026-07-16 04:29:02 [queen] INFO  SUCCESS  task_id=b028fc08  retries=0  elapsed=0.7s
2026-07-16 04:29:02 [queen] INFO  SUCCESS  task_id=9dc9fc75  retries=0  elapsed=0.8s
2026-07-16 04:29:02 [queen] INFO  AGGREGATE  success=3  fail=0  elapsed=0.8s
2026-07-16 04:29:02 [queen] INFO  AUDIT  → /home/bratan/.hermes/logs/agent-orchestration-patterns/run-*.json
```

**Wall-clock:** 0.79s für 3 parallel-stub-Workers (in echt: ~100s für 3 echte API-Calls)

## Integration in dein Projekt

```bash
# 1. Skeleton kopieren
cp ~/10-Projekte/10-active/agent-orchestration-patterns/master_worker.py \
   ~/mein-projekt/orchestration/

# 2. In deinem Code verwenden
from orchestration.master_worker import QueenOrchestrator, WorkerTask

async def run_my_research():
    queen = QueenOrchestrator(max_concurrent_workers=4)
    result = await queen.run("Research die 3 besten GreyHack-Mission-Patterns")
    return result["synthesis"]
```

## TODO (offene Punkte für Production-Use)

1. **`plan()` mit echtem LLM-Call** — derzeit Stub (3 fixed tasks). TODO: Sonnet-Call mit JSON-Schema-Output
2. **`run()` Synthese** — derzeit Stub. TODO: LLM-Call auf `queen_model` mit `successes[].output`
3. **Worker-Toolset-Validation** — derzeit nur declared, nicht geprüft

## Tests (7 Tests, alle grün)

```bash
cd ~/10-Projekte/10-active/agent-orchestration-patterns
python3 -m pytest tests/test_master_worker.py -v

# → 7 passed in ~6s
```

Coverage-Matrix:
- ✅ Dry-Run completes successfully
- ✅ Idempotency-Cache prevents double-execution
- ✅ Idempotency-Key is stable (sha256)
- ✅ Audit-Trail JSON is valid
- ✅ Concurrency-Cap is respected
- ✅ Retry on failure recovers
- ✅ CLI dry-run returns zero exit code

## Related

- Skeleton B (`hierarchical_tree.py`) — für Multi-Domain-Tasks
- Skeleton C (`critic_loop.py`) — wenn Korrektheit kritisch
- `multi-agent-cluster-patterns` Skill — Pattern 2 (Additive Patches) für sicheres Fan-Out
- `multi-agent-pitfalls-cheatsheet` — vor jedem Spawn laden