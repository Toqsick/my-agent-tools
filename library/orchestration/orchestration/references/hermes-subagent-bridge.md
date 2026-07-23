# Hermes Subagent Bridge — Patterns & Code

> **Companion reference for `multi-agent-orchestration`.** How to dispatch
> workers as Hermes Subagenten via `hermes_tools.delegate_task()`, plus
> the safe fallback when the bridge is unavailable.

## Quickstart

```python
# Detect bridge availability (Hermes runtime vs. sandbox/manual mode)
try:
    from hermes_tools import delegate_task
    HERMES_AVAILABLE = True
except ImportError:
    HERMES_AVAILABLE = False

# Always have a fallback ready
def dispatch_worker(role, task_packet):
    if not HERMES_AVAILABLE:
        return run_inline(role, task_packet)        # Parent-direct fallback
    try:
        return delegate_task(
            goal=WORKER_PROMPTS[role] + str(task_packet),
            toolsets=WORKER_TOOLSETS[role],
            role="leaf",                              # no further delegation
        )
    except Exception as e:
        log(f"Bridge failed for {role}: {e}")
        return run_inline(role, task_packet)        # Pitfall #11 fallback
```

## Worker Role → Toolset Mapping (tested 2026-06-27)

| Role | Toolsets | Why |
|------|----------|-----|
| planner | `terminal, file, web` | Read state, write plans, query docs |
| researcher | `web, search, file` | Browse + search + cache findings |
| writer | `file` | Just write artifacts |
| coder | `terminal, file, web` | Run builds, edit code, fetch deps |
| reviewer | `terminal, file` | Inspect outputs without distractions |
| summarizer | `file` | Pure text compression |
| abstraction | `file` | Pattern extraction, no live data |
| control | `terminal, file` | Audit worker outputs |
| retrospective | `terminal, file` | Analyze run artifacts + metrics |
| improvement_agent | `terminal, file` | Apply heuristics to skill configs |
| generic_worker | `terminal, file, web` | Default everything-allrounder |

## Worker Contract (returned by every worker)

```json
{
  "role": "writer",
  "task": "Beschreibung des Subproblems",
  "result": { "summary": "...", "details": "..." },
  "assumptions": ["explizite Annahme 1", "..."],
  "uncertainties": ["Bekannte Unbekannte"],
  "risks": ["Identifizierte Risiken"],
  "confidence": 0.0,
  "recommended_next_step": "Handoff-Hinweis"
}
```

**Hard requirement**: `assumptions`, `uncertainties`, `risks` MUST be
non-empty lists. Control rejects otherwise.

## Pitfalls

1. **`model` param in `delegate_task` is silently IGNORED** (Pitfall #10).
   The only knob is `~/.hermes/config.yaml → delegation.model`. Currently
   `openrouter/owl-alpha` (0$/Token, 1M Context) on Basti's setup.

2. **Model changes need Hermes restart** — `delegation.model` changes don't
   take effect until the session is restarted. Plan ahead.

3. **Dispatch failure fallback** (Pitfall #11) — `delegate_task` may fail
   with `base_prompt is empty`, provider-gate errors, or HTTP 404/429.
   Don't loop-retry; switch to parent-direct mode (run the worker inline
   in the parent context) and clearly document the fallback in the
   final report.

4. **Subagent self-reports are NOT facts** (Pitfall #5). "I built it" ≠
   "It works". Always verify with terminal/file inspection before
   accepting claims.

5. **Free-model rate limits** — Owl Alpha can 429 after bursts of 5-10
   subagents. Plan for graceful degradation: parent-direct fallback or
   smaller batches.

6. **Subagent output parsing** — `delegate_task` returns a summary string,
   not a structured Worker-Contract. Parse defensively:
   ```python
   try:
       data = json.loads(raw)
       if isinstance(data, dict) and "role" in data:
           return data
   except (json.JSONDecodeError, ValueError):
       pass
   return {
       "role": role, "task": objective,
       "result": {"raw_text": raw},
       "assumptions": ["Raw output, not parsed"],
       "uncertainties": ["Structured parsing failed"],
       "risks": [],
       "confidence": 0.6,
       "recommended_next_step": "Review raw output manually"
   }
   ```

7. **Token-Plan-getrennte Provider statt Universal-Provider** (PROVEN 2026-07-02) —
   **Grundregel:** Jedes Modell hat einen spezifischen Provider der seinen Token-Plan abbildet.
   `delegation.provider=nous` ist NICHT universell gültig — nur Modelle die über Nous Portal
   abgerechnet werden (DeepSeek, StepFun) gehören unter `nous`. GLM gehört unter `zai`,
   MiniMax unter `minimax`. Beispiel-Struktur:
   ```yaml
   # FALSCH (vor 2026-07-02):
   delegation.provider: nous
   # → GLM und MiniMax werden fälschlich über Nous Portal abgerechnet

   # RICHTIG (seit 2026-07-02):
   # → Profile mit eigenem provider/model für jeden Token-Plan
   # → MoA-Presets mit korrekten provider-Strings
   ```
   **Workaround:** Token-Plan-Check VOR Deployment (siehe Haupt-Skill).

## Configuration (Hermes-side)

```bash
# Verify current delegation routing
hermes config get delegation.model
hermes config get delegation.provider

# Basti's Bienenschwarm setup (2026-06-27)
hermes config set delegation.model openrouter/owl-alpha
hermes config set delegation.provider openrouter
```

## When to use this pattern

- **Use when**: Task can be split into 3-7 independent subproblems, each
  worker has a clear role, and parallel execution gives meaningful speedup.
- **Don't use when**: Task needs strict serial dependencies, or it's a
  single-step trivial operation. Just inline.
- **Don't use when**: Single quick verification — over-orchestration
  wastes more time than it saves.

## Related skills

- `hermes-orchestration` (orchestration/) — V2.1 implements this bridge
  pattern with full Control/Retrospective/Improvement loop. Reference
  implementation.
- `the-dmz-transfer` — GreyHack specialization using same bridge.
- `multi-agent-work` — 6-phase workflow with this bridge as execution layer.