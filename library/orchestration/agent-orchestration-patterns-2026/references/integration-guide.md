# Integration-Guide — Skeletons in dein Projekt einbauen

**Ziel:** Die 3 Skeletons aus `~/10-Projekte/10-active/agent-orchestration-patterns/` in dein eigenes Projekt kopieren und produktiv nutzen.

## Setup-Schritte (5-10 Min)

### Schritt 1: Skeleton kopieren

```bash
# Wähle die Skeletons die du brauchst (alle oder einzeln)
cp ~/10-Projekte/10-active/agent-orchestration-patterns/master_worker.py \
   ~/mein-projekt/orchestration/

cp ~/10-Projekte/10-active/agent-orchestration-patterns/hierarchical_tree.py \
   ~/mein-projekt/orchestration/

cp ~/10-Projekte/10-active/agent-orchestration-patterns/critic_loop.py \
   ~/mein-projekt/orchestration/
```

### Schritt 2: Hermes-Config prüfen

```bash
# Für Skeleton B (Tree) ist depth=2 Pflicht!
grep "max_spawn_depth" ~/.hermes/config.yaml

# Wenn nicht da oder =1:
hermes config set delegation.max_spawn_depth 2
hermes config set delegation.max_concurrent_children 3
hermes config set delegation.model google/gemini-flash-2.0
```

### Schritt 3: Tests importieren + anpassen

```bash
# Tests kopieren (als Living Documentation + Verifikation)
mkdir -p ~/mein-projekt/tests/orchestration/
cp ~/10-Projekte/10-active/agent-orchestration-patterns/tests/test_*.py \
   ~/mein-projekt/tests/orchestration/

# Pfad-Adjustierung in den Tests:
# ALT: sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# NEU: sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
```

### Schritt 4: Lokal verifizieren

```bash
cd ~/mein-projekt
python3 -m pytest tests/orchestration/ -v
# → 27 passed

python3 orchestration/master_worker.py --dry-run "Test"
python3 orchestration/hierarchical_tree.py --dry-run
python3 orchestration/critic_loop.py --dry-run "Test"
```

### Schritt 5: Im Code verwenden

```python
# In deinem Projekt-Modul
from orchestration.master_worker import QueenOrchestrator
from orchestration.hierarchical_tree import HierarchicalOrchestrator
from orchestration.critic_loop import CriticLoop, EvaluationRubric

async def my_research_pipeline():
    queen = QueenOrchestrator(max_concurrent_workers=4)
    result = await queen.run(
        "Researche die 3 besten GreyHack-Mission-Automation-Patterns"
    )
    return result["synthesis"]
```

## Anpassungs-Patterns

### Pattern 1: Stub-Methoden mit echten LLM-Calls ersetzen

Jedes Skeleton hat eine Stub-Methode (z.B. `QueenOrchestrator.plan()`) die TODO-markiert ist:

```python
async def plan(self, high_level_goal: str, dry_run: bool = False) -> list[WorkerTask]:
    # TODO: Replace with real Queen planning call
    if dry_run:
        return [...]   # Stub für Tests
    raise NotImplementedError("...")
```

**Ersetze mit echtem Call:**

```python
async def plan(self, high_level_goal: str, dry_run: bool = False) -> list[WorkerTask]:
    if dry_run:
        return [...]   # behalte Stub für Tests

    # ECHTER LLM-Call
    from hermes_tools import delegate_task
    loop = asyncio.get_event_loop()
    raw = await loop.run_in_executor(None, lambda: delegate_task(
        goal=f"Decompose into 3-5 parallel subtasks: {high_level_goal}",
        context="Return JSON: {tasks: [{goal, context, toolsets}, ...]}",
        toolsets=[],
        model=self._queen_model,
    ))
    # Parse JSON → list[WorkerTask]
    return [WorkerTask(**t) for t in raw["tasks"]]
```

### Pattern 2: Audit-Trail anpassen

Default: Logs nach `~/.hermes/logs/agent-orchestration-patterns/`.

**Anpassung:**

```python
# In jedem Skeleton: LOG_DIR anpassen
LOG_DIR = Path.home() / "mein-projekt" / "logs" / "orchestration"
LOG_DIR.mkdir(parents=True, exist_ok=True)
```

### Pattern 3: Model-Tiering customizen

Default-Tiering:
- **Queen/Orchestrator/Critic:** `anthropic/claude-sonnet-4-5` (fähig)
- **Worker/Leaf:** `google/gemini-flash-2.0` (günstig)

**Anpassung für dein Stack:**

```python
# In deinem Projekt
queen = QueenOrchestrator(
    queen_model="anthropic/claude-sonnet-4-5",  # fähig für Planung
    worker_model="google/gemini-flash-2.0",     # günstig für Execution
)

# Oder mit Ollama (lokal, gratis):
queen = QueenOrchestrator(
    queen_model="ollama/qwen35-9b-local",
    worker_model="ollama/qwen35-9b-local",
)
```

### Pattern 4: Subdomains für Tree anpassen

Default-Subdomains sind GreyHack-spezifisch. Für deinen Use-Case:

```python
MY_SUBDOMAINS = [
    {
        "domain": "data-collection",
        "goal": "Fetch latest data from API X",
        "artifacts": [],
        "output_schema": {"data": "list[dict]"},
    },
    {
        "domain": "analysis",
        "goal": "Analyze data with statistical methods",
        "artifacts": ["/tmp/data-collection.json"],   # upstream artifact
        "output_schema": {"insights": "list[str]"},
    },
    {
        "domain": "report",
        "goal": "Write final report combining insights",
        "artifacts": ["/tmp/analysis.json"],
        "output_schema": {"report": "str"},
    },
]

result = await orch.run("Run data pipeline", MY_SUBDOMAINS)
```

### Pattern 5: Rubric für Critic-Loop customizen

```python
MY_RUBRIC = EvaluationRubric(
    required_criteria=[
        "Python syntax is valid",
        "All pytest tests pass",
        "No hardcoded credentials",
        "Code follows PEP 8 style guide",
    ],
    preferred_criteria=[
        "Type hints on all functions",
        "Docstrings on public functions",
        "Inline comments for complex logic",
    ],
    unrecoverable_signals=[
        "contains hardcoded api key",
        "imports os.system",
        "uses subprocess.run with shell=True and user input",
    ],
)

loop = CriticLoop(max_rounds=3)
result = await loop.run(
    task_id="my-code-review",
    task_goal="Write a Python function that fetches GitHub issues",
    task_context="Use the `requests` library. Handle rate limits.",
    rubric=MY_RUBRIC,
)
```

## Production-Patterns (aus realem Einsatz)

### Pattern: Cron-Job mit Skeleton A

```bash
# In crontab:
0 */6 * * * cd ~/mein-projekt && python3 orchestration/master_worker.py "Daily research digest" >> logs/cron.log 2>&1
```

### Pattern: Multi-Stage-Pipeline (B outer + C inner)

```python
async def code_pipeline():
    # Outer: Tree für Routing (research → implement → review)
    orch = HierarchicalOrchestrator()
    subdomains = [
        {"domain": "research", "goal": "Research best patterns for X"},
        {"domain": "implement", "goal": "Implement based on research"},
        {"domain": "review", "goal": "Security + style review"},
    ]
    tree_result = await orch.run("Build X", subdomains)

    # Inner: Critic pro Stage für Verification
    if tree_result["subtrees_ok"] > 0:
        critic = CriticLoop(max_rounds=3)
        rubric = EvaluationRubric(required_criteria=["x", "y", "z"])
        for stage_output in tree_result["outputs"]:
            review = await critic.run(
                task_id=f"review-{stage_output['domain']}",
                task_goal=f"Review: {stage_output['domain']}",
                task_context=str(stage_output),
                rubric=rubric,
            )
            if review.final_status != "passed":
                log.warning(f"Stage {stage_output['domain']} failed review")
```

### Pattern: Hybrid Queen-Bee + Tree

```python
async def hybrid_orchestration(high_level_goal: str):
    # Queen plant N Sub-Domains
    queen = QueenOrchestrator(max_concurrent_workers=1)  # Queen allein
    plan_result = await queen.plan(high_level_goal, dry_run=False)

    # Tree führt Sub-Domains aus
    tree = HierarchicalOrchestrator(max_concurrent_per_level=3)
    return await tree.run(high_level_goal, plan_result, dry_run=False)
```

## Häufige Fehler

| Fehler | Symptom | Fix |
|---|---|---|
| `max_spawn_depth=1` mit Skeleton B | L1 Sub-Orchestrators können nicht L2 spawnen | `hermes config set delegation.max_spawn_depth 2` |
| Subdomain-`artifacts` mit Inhalt statt Pfad | L2-Leaves bekommen kein Zugriff auf Daten | Immer absolute File-Pfade, nie Inline-Daten |
| Critic ohne Rubric | Critic rät, terminiert früh | IMMER Rubric definieren mit `required_criteria` |
| max_rounds > 5 | Cost-Explosion ohne Qualitäts-Gewinn | max_rounds=3 ist Sweet-Spot empirisch |
| Tree ohne correlation_id-Tracking | Trace-Verlust in Multi-Level-Runs | `correlation_id` ist im Code, einfach nutzen |
| Worker-Toolset `["everything"]` | Subagent macht zu viel | Toolset eng definieren pro Worker |

## Performance-Tipps

| Tipp | Wirkung |
|---|---|
| Cheap-Worker (Flash/Haiku) | 40-60% Cost-Reduction |
| `max_concurrent_workers` auf Rate-Limit tunen | Vermeidet 429-Errors |
| Idempotency-Cache nutzen | Vermeidet Doppel-API-Calls bei Retry |
| Audit-Trail persistieren | Debugging + Replay-Möglichkeit |
| HandoffPacket ≤ 200 Token Parent-Summary | Verhindert Context-Explosion auf L2 |
| max_rounds=3 + Sycophancy-Guard | Verhindert Critic-Loop-Runaway |

## Testing in deinem Projekt

```bash
# In CI/CD:
cd ~/mein-projekt
python3 -m pytest tests/orchestration/ -v
# → 27 passed (deine angepasste Version)

# Smoke-Test in Production-Deployment:
python3 orchestration/master_worker.py --dry-run "Production smoke test" --output /tmp/smoke.json
# → exit 0 wenn ok, 1 wenn Failures
```

## Migration-Pfad (von Ad-Hoce-Delegate-Task zu Skeleton)

**Schritt 1:** Identifiziere wo du aktuell `delegate_task` direkt aufrufst:

```bash
grep -rn "delegate_task" ~/mein-projekt/
```

**Schritt 2:** Klassifiziere die Aufrufe nach Pattern:
- Parallelisierbar, unabhängig → Skeleton A
- Multi-Domain, strukturiert → Skeleton B
- Verifikations-bedürftig → Skeleton C

**Schritt 3:** Refactor schrittweise (eine Pipeline nach der anderen):

```python
# ALT:
result = delegate_task(goal="...", context="...", toolsets=["..."])

# NEU (Skeleton A):
from orchestration.master_worker import QueenOrchestrator
queen = QueenOrchestrator()
result = await queen.run("...")
```

**Schritt 4:** Tests für die neue Pipeline schreiben (analog zu den 27 vorhandenen)

**Schritt 5:** In Production deployen + Monitor (Audit-Trail inspizieren)

## Support-Patterns (aus der Praxis)

| Pattern | Wo nachschauen |
|---|---|
| Race-Conditions auf geteilten Files | `multi-agent-cluster-patterns` Skill → Pattern 1+2 |
| Subagent erfindet Tech-Details | `multi-agent-cluster-patterns` Skill → Pattern 3 |
| YAML-Korruption durch Subagent | `multi-agent-pitfalls-cheatsheet` Skill → Pitfall #11 |
| Subagent gibt "done" zurück aber file fehlt | `multi-agent-pitfalls-cheatsheet` Skill → Pitfall #29 |
| HTTP 429 "Insufficient balance" | `multi-agent-pitfalls-cheatsheet` Skill → Pitfall #35 |

## Live-Validierung (was schon läuft)

| Datum | Was | Status |
|---|---|---|
| 2026-07-16 | 3 Skeletons + 27 Tests im Repo `agent-orchestration-patterns/` | ✅ |
| 2026-07-16 | Dry-Run aller 3 Skeletons (echte Execution) | ✅ alle success |
| 2026-07-16 | Skill-Wiederverwendbarkeit dokumentiert | ✅ (dieser Skill) |

**Maintainer:** Basti + Yuno (2026-07-16)
**Lizenz:** MIT