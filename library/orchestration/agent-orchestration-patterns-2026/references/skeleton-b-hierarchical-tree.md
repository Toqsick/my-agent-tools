# Skeleton B — 2-Level Hierarchical Tree

**Source:** `~/10-Projekte/10-active/agent-orchestration-patterns/hierarchical_tree.py` (520 LOC, 19 KB)
**Pattern:** 2-Level Tree mit `role='orchestrator'` Sub-Orchestrators
**Use-Case:** Multi-Domain-Tasks (research→implement→review), strukturiertes Routing

## Architektur-Übersicht

```
                          ┌──────────────────┐
                          │   Root Queen     │  (teuer: Sonnet)
                          │   (decompose +   │
                          │   synthesize)    │
                          └────────┬─────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
                ▼                  ▼                  ▼
         ┌────────────┐    ┌────────────┐    ┌────────────┐
         │ Sub-Orch 1 │    │ Sub-Orch 2 │    │ Sub-Orch 3 │
         │ research   │    │ implement  │    │ review     │  (mittel: Sonnet/Haiku)
         │ depth=1    │    │ depth=1    │    │ depth=1    │
         └─────┬──────┘    └─────┬──────┘    └─────┬──────┘
               │                 │                  │
       ┌───────┴──────┐         ...          ┌─────┴───────┐
       ▼              ▼                       ▼             ▼
   ┌────────┐    ┌────────┐              ┌────────┐    ┌────────┐
   │Leaf 1.1│    │Leaf 1.2│              │Leaf 3.1│    │Leaf 3.2│ (günstig: Flash)
   │depth=2 │    │depth=2 │              │depth=2 │    │depth=2 │
   └────────┘    └────────┘              └────────┘    └────────┘
   (correlation_id = "abc123def456"      — threaded durch alle Levels)
```

## Wann nutzen

✅ **Ja:**
- Multi-Domain-Task (z.B. research→implement→review)
- Strukturiertes Routing nötig (jedes Sub-Domain eigene Strategie)
- Correlation-Tracking wichtig (z.B. Audit-Trail über alle Stufen)
- Sub-Domains brauchen eigene Worker (nicht alle gleich)

❌ **Nein:**
- Single-Domain → Skeleton A (Master/Worker)
- Sequenzielle Pipeline → Skeleton A als Pipeline
- Tiefer als depth=2 → aktuell nicht supported (hard cap)
- Korrektheit-Loop nötig → Skeleton C (Critic-Loop) pro Sub-Domain

## Kern-Komponenten

### 1. HandoffPacket (kritischste Datenstruktur)

```python
@dataclass
class HandoffPacket:
    task_id: str                    # UUID-Prefix
    correlation_id: str             # threaded durch alle Levels
    depth: int                      # aktuelle Spawn-Depth (1 oder 2)
    goal: str
    constraints: list[str]
    relevant_artifacts: list[str]   # FILE-PATHS, nicht Inhalte!
    output_schema: dict[str, str]
    parent_summary: str = ""        # ≤ 200 Token Parent-Context
```

**Warum HandoffPacket statt Raw-Context:**
- Verhindert Context-Explosion auf L2 (50k-Token-Parent → 200-Token-Summary)
- Strukturiert: jedes Feld ist explizit, keine versteckten Halluzinationen
- Validerbar: Schema kann geprüft werden
- **Halte es minimal — fette Packets = Context-Explosion auf L2**

### 2. TokenBudget (Hard-Cap-Guard)

```python
class TokenBudget:
    def __init__(self, cap: int):           # Default: 50_000
        self._cap = cap
        self._used = 0

    def charge(self, tokens: int, label: str):
        self._used += tokens
        if self._used > self._cap:
            raise BudgetExceeded(f"Token-Budget {self._cap} überschritten bei '{label}'")
```

**Verhindert:** Spawn-Storm bei runaway recursion (verbraucht endlos Tokens)

### 3. HierarchicalOrchestrator (Hauptklasse)

```python
orch = HierarchicalOrchestrator(
    max_concurrent_per_level=3,     # Semaphore-Cap pro Level
    subtree_token_budget=50_000,    # Hard-Cap
    max_safe_depth=2,               # DEFAULT, nicht überschreiten ohne Begründung
    orch_model="anthropic/claude-sonnet-4-5",
    leaf_model="google/gemini-flash-2.0",
)

subdomains = [
    {"domain": "research", "goal": "Recherche Patterns", "artifacts": []},
    {"domain": "implement", "goal": "Implementiere X", "artifacts": ["/tmp/..."]},
    {"domain": "review", "goal": "Security-Review", "artifacts": ["/tmp/..."]},
]

result = await orch.run("Build mission runner", subdomains, dry_run=False)
```

## Hermes-Config (Pflicht!)

```yaml
# ~/.hermes/config.yaml
delegation:
  max_spawn_depth: 2            # aktiviert L1 → L2 spawn (default ist 1)
  max_concurrent_children: 3
  model: "google/gemini-flash-2.0"   # cheap model for leaves
```

**Ohne `max_spawn_depth: 2` schlägt Nested-Delegation fehl**, auch mit `role='orchestrator'`!

## Sicherheitsschienen

| Rail | Code | Was es verhindert |
|---|---|---|
| `MAX_SAFE_DEPTH = 2` | `HierarchicalOrchestrator._max_depth` | Spawn-Storm (OpenCode-Incident: depth 18) |
| `TokenBudget` | Klasse | Endlos-Token-Verbrauch |
| `correlation_id` | threaded durch alle Levels | Trace-Verlust in Multi-Level-Trees |
| Per-Level-Semaphore | `self._sem` pro Level | API-Storm |
| `asyncio.wait_for` | pro `_dispatch()` Call | Runaway-Sub-Tree |
| HandoffPacket Schema | strukturiert | Verhindert Raw-History-Leak |
| Trace-JSON persistiert | `LOG_DIR / tree-<corr_id>.json` | Audit-Trail-Lücke |

## CLI

```bash
# Dry-Run mit GreyHack-Default-Subdomains
python3 hierarchical_tree.py --dry-run

# Custom Subdomains (JSON-File)
python3 hierarchical_tree.py --subdomains-file my-subdomains.json --dry-run

# Token-Budget + Depth-Cap override (advanced!)
python3 hierarchical_tree.py --token-budget 200000 --depth-cap 3 --dry-run

# Output in Datei
python3 hierarchical_tree.py --dry-run --output /tmp/tree-run.json
```

## Default-Subdomains (GreyHack-Use-Case)

```python
DEFAULT_SUBDOMAINS_GREYHACK_MISSION = [
    {
        "domain": "research",
        "goal": "Recherche GreyHack MMO Mission-Automation-Patterns; liste 5 Ansätze",
        "artifacts": [],
        "output_schema": {"patterns": "list[str]", "recommended": "str"},
    },
    {
        "domain": "implement",
        "goal": "Implementiere GreyScript Mission-Runner mit empfohlenem Pattern",
        "artifacts": ["/tmp/greyhack-research.json"],   # L2 Leaves holen das
        "output_schema": {"files_created": "list[str]", "tests_pass": "bool"},
    },
    {
        "domain": "review",
        "goal": "Security-Review des implementierten Mission-Runners auf Prompt-Injection",
        "artifacts": ["/tmp/greyhack-implement.json"],
        "output_schema": {"issues": "list[str]", "severity": "str"},
    },
]
```

## Echte Verifizierung (Dry-Run-Output)

```
$ python3 hierarchical_tree.py --dry-run
[tree] INFO  ROOT  corr=4c4c460318a1  goal='Build a GreyHack mission...'  domains=3
[tree] INFO  SUB-ORCH  corr=4c4c460318a1  depth=1  goal='Recherche GreyHack...'
[tree] INFO  SUB-ORCH  corr=4c4c460318a1  depth=1  goal='Implementiere GreyScript...'
[tree] INFO  SUB-ORCH  corr=4c4c460318a1  depth=1  goal='Security-Review...'
[tree] INFO  ROOT DONE  corr=4c4c460318a1  ok=3  fail=0  elapsed=1.0s  budget_used=9379
[tree] INFO  TRACE  → /home/bratan/.hermes/logs/agent-orchestration-patterns/tree-4c4c460318a1.json
```

**Wall-clock:** 0.96s für 3 stub-Sub-Orchestrators (in echt: ~200s für L1 + L2)

## Depth-Cap Override (mit Bedacht!)

```bash
# Warnung wird geloggt wenn depth_cap > 2
python3 hierarchical_tree.py --depth-cap 3 --dry-run
# [tree] WARNING  DEPTH-CAP=3 > DEFAULT=2 — nur mit expliziter Begründung verwenden!
```

**Faustregel:** Bleib bei 2 wenn möglich. Depth 3+ nur wenn:
- Du die Token-Kosten explizit gemessen hast
- Du einen klaren Plan für Depth-3-Use-Case hast
- Du bereit bist, OpenCode-Incident-ähnliche Debug-Sessions durchzustehen

## Integration in dein Projekt

```bash
# 1. Skeleton kopieren
cp ~/10-Projekte/10-active/agent-orchestration-patterns/hierarchical_tree.py \
   ~/mein-projekt/orchestration/

# 2. Hermes-Config anpassen
# ~/.hermes/config.yaml:
#   delegation:
#     max_spawn_depth: 2

# 3. In deinem Code
from orchestration.hierarchical_tree import HierarchicalOrchestrator

orch = HierarchicalOrchestrator()
result = await orch.run(
    high_level_goal="Build X",
    subdomains=[
        {"domain": "a", "goal": "..."},
        {"domain": "b", "goal": "..."},
    ],
)
```

## TODO (offene Punkte)

1. **L1-Orchestrator plant eigene L2-Leaves** — derzeit Stub: L2-Leaves werden NICHT gespawnt (nur L1-Stub). TODO: echt Sub-Orchestrator mit echtem L2-Fan-Out
2. **Subdomain-Schema-Validation** — JSON-Schema-Check für L1-Output
3. **Cross-Subdomain-Dependencies** — derzeit alle Subdomains parallel, kein Dependency-Management

## Tests (7 Tests, alle grün)

```bash
cd ~/10-Projekte/10-active/agent-orchestration-patterns
python3 -m pytest tests/test_hierarchical_tree.py -v

# → 7 passed in ~6s
```

Coverage-Matrix:
- ✅ Token-Budget raises on overflow
- ✅ Token-Budget used/remaining korrekt
- ✅ Depth-Guard refuses too-deep
- ✅ Dry-Run mit GreyHack-Default-Subdomains
- ✅ Correlation-ID ist unique pro Run
- ✅ Trace-JSON hat erwartete Struktur
- ✅ HandoffPacket-Defaults sinnvoll
- ✅ Depth-Cap-Override verhält sich korrekt

## Related

- **Skeleton A** (`master_worker.py`) — für Single-Domain-Fan-Out
- **Skeleton C** (`critic_loop.py`) — pro Sub-Domain als Verification-Stage
- `sub-sub-workflow` Skill — Pattern 12 (verifizierbare 2-Level-Delegation mit Side-Effect-Files)
- `multi-agent-cluster-patterns` Skill — Pattern 12 (Sub-Sub-Dispatch)
- `multi-agent-pitfalls-cheatsheet` — vor jedem Spawn laden (besonders #19/#30)