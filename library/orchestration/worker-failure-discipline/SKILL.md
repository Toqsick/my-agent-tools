---
name: worker-failure-discipline
description: |
  Use when you need to use the worker-failure-discipline workflow and its documented procedures.
  NOT for unrelated tasks outside the worker-failure-discipline workflow.
  Provides focused guidance for worker-failure-discipline.
version: 1.3.0
author: Hermes Agent (hermes-v2 plan, H-42, 2026-07-20)
license: MIT
platforms:
  - linux
  - macos
metadata:
  hermes:
    tags: ['worker', 'failure', 'discipline', 'orchestration', 'verification', 'hermes-v2']
    related_skills:
      - swarm-router
      - swarm-workspace-isolation
      - coding-pipeline-orchestrator
      - queen-bee-schwarm-dispatch
      - verify-before-fix
lane: koenigin
reasoning_effort: xhigh
agent: Orchestrator
routing_hint: |
  **Agent-Scope:** Defining what counts as worker success/failure. Off-scope: workers themselves, pipelines, plans.
trigger_keywords: ['worker', 'failure', 'discipline', 'workflow', 'need']
keywords: ['worker', 'failure', 'discipline', 'workflow', 'need']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['voice-clone', 'github-workflow', 'multi-agent-pitfalls-cheatsheet']
---

# Worker Failure Discipline (hermes-v2, H-42)

The hermes-v2 plan was kicked off by an incident where workers
that produced **no output** were marked as done by the dispatcher
(see H-00 in `~/hermes-v2-baseline-dbs/`). The orchestrator had no
discipline to distinguish "worker ran and succeeded" from
"worker ran, hit a silent failure, and produced nothing".

This skill defines that discipline. Apply it to any orchestrator
that aggregates worker results.

## When to Use

Load this skill when **any** of the following is true:

- You are building or auditing an orchestrator / verifier /
  pipeline step that aggregates worker results.
- You are defining a worker contract or runtime that decides
  when a task is "done".
- You are diagnosing an H-00-class silent-failure bug where a
  worker claimed success but produced nothing usable.

**Off-scope:** building the workers themselves (use
`coding-specialist`), spawning pipelines (use
`coding-pipeline-orchestrator`), drafting plans (use `navigator`
or `writing-plans`).

## Quick Start

A worker run is **compliant** iff **all** of the following hold:

1. `output/result.json` exists in the workspace.
2. It parses as JSON with at minimum a `status` field.
3. If `status: "ok"`, every path listed in `artifacts` exists
   on disk.
4. If `status: "failed"`, an `error` field is present.

An orchestrator is **disciplined** iff it **never** marks a task
done on `exit_code == 0` alone — it must verify the four points
above AND surface verifier verdicts using only the canonical
strings `VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES`
(gate/step decisions go in body or metadata, never as fake
tokens like `SPEC_OK` / `QUALITY_OK` / `APPROVED` / `LOOP`).
Escalate to a human gate after 2 consecutive failures.

**What the runtime does NOT do:** `result.json` is a skill- and
worker-level output contract. Hermes `complete_task` accepts a
free-form `--result` / `--summary` string and never reads,
parses, or validates `output/result.json` in the worker's
workspace; it only checks `--created_cards` for hallucinated
ids. The discipline check is therefore the verifier / pipeline
orchestrator's responsibility, not the engine's — accepting
`done` without re-running the four checks above leaves the
H-00 trap in place.

A minimal CLI-safe check is wired up in `test_skill.py` next to
this file — it parses the YAML, walks the section order, greps
the example code for the artifact-check / `SUCCESS`-return
ordering, and shells out to `hermes kanban --help` to confirm
the documented subcommands exist.

## The Rule

> **An empty result is a failure.**

Specifically:

1. Every worker run MUST produce one of:
   - `output/result.json` with `status: "ok"` (success), OR
   - `output/result.json` with `status: "failed"` (declared failure),
     OR
   - A non-zero process exit (uncaught exception, crash, OOM,
     timeout).
2. **Missing `result.json` + zero exit code** = orchestrator treats
   this as a **hard failure**, never as "nothing to do".
3. Missing `result.json` + non-zero exit = obviously failure.
4. **Non-empty `output/` directory but missing `result.json`** =
   also failure (the worker started but didn't finalise).
5. **`status: "ok"` but an artifact path in `artifacts` is missing
   on disk** = failure (don't trust declarations alone).

## Orchestrator-side Checks

The orchestrator (Queen / pipeline runner / swarm-router) MUST
apply this verification before marking a task done. The artifact
check MUST run **before** any `return SUCCESS`, never as
unreachable code after an early return, and the `output/`
directory must be guarded so the helper never crashes with
`FileNotFoundError` when a worker produced literally nothing.

```python
from enum import Enum
import json
from pathlib import Path

class WorkerOutcome(Enum):
    SUCCESS = "success"
    FAILED_NO_OUTPUT = "failed_no_output"            # H-00 trap
    FAILED_UNFINALISED = "failed_unfinalised"        # started, no result.json
    FAILED_MALFORMED = "failed_malformed"            # result.json unparseable
    FAILED_DECLARED = "failed_declared"              # status == "failed"
    FAILED_UNKNOWN_STATUS = "failed_unknown_status"
    FAILED_ARTIFACT_MISSING = "failed_artifact_missing"

def verify_worker_output(workspace_path: str) -> WorkerOutcome:
    workspace = Path(workspace_path)
    output_dir = workspace / "output"
    result_json = output_dir / "result.json"

    # Step 0: does the output directory exist at all? Without this
    # guard, `output_dir.iterdir()` below would raise FileNotFoundError
    # on a worker that produced literally nothing.
    if not output_dir.is_dir():
        return WorkerOutcome.FAILED_NO_OUTPUT  # the H-00 trap

    # Step 1: did the worker finalise result.json?
    if not result_json.exists():
        # Step 1a: did the worker at least produce something?
        if not any(output_dir.iterdir()):
            return WorkerOutcome.FAILED_NO_OUTPUT  # the H-00 trap
        return WorkerOutcome.FAILED_UNFINALISED  # started but no result.json

    # Step 2: parse the result
    try:
        result = json.loads(result_json.read_text())
    except json.JSONDecodeError:
        return WorkerOutcome.FAILED_MALFORMED

    # Step 3: check declared status (failed short-circuits; unknown
    # is its own failure — never silently fall through to SUCCESS).
    status = result.get("status")
    if status == "failed":
        return WorkerOutcome.FAILED_DECLARED
    if status != "ok":
        return WorkerOutcome.FAILED_UNKNOWN_STATUS

    # Step 4: verify every declared artifact exists on disk BEFORE
    # returning SUCCESS — this catches the "claimed success but
    # artifact missing" trap. Never trust declarations alone.
    # NOTE: this loop must come BEFORE the SUCCESS return below,
    # never as unreachable code after an early return.
    for artifact in result.get("artifacts", []):
        if not (workspace / "output" / "artifacts" / artifact).exists():
            return WorkerOutcome.FAILED_ARTIFACT_MISSING

    return WorkerOutcome.SUCCESS
```

The 6 failure outcomes (`FAILED_*`) each carry a distinct message
that the orchestrator can log. This prevents both the
"silent no-output" trap AND the "claimed success but artifact
missing" trap.

## Worker-side Contract

Every worker that's part of a hermes-v2 swarm or pipeline MUST
adhere to the H-43 workspace contract, specifically:

- On entry: `cd` into the workspace, verify input MD5.
- On success: write `output/result.json` with `status: "ok"` and a
  list of produced artifacts (paths relative to
  `output/artifacts/`).
- On failure: write `output/result.json` with `status: "failed"`
  and an `error` field describing what went wrong.
- On uncaught exception: the **worker itself** is responsible for
  writing `output/result.json` with `status: "failed"` and the
  traceback before exiting (the scaffold below does this in
  `except` / `finally`).
- Keep `result.json` a **flat, literal JSON object** (plain strings,
  flat arrays) — never a Python-repr string like `"['a','b']"`. This
  matters most for GLM workers (`koenigin`/`worker-heavy`/`gate`
  lanes), which occasionally emit repr-lists that `coerce_tool_args`
  has to repair; a clean literal object parses identically no matter
  which model wrote it. (MiniMax-M3 workers are strong native callers
  and rarely trip this — but the contract is model-blind on purpose.)

**This is a worker- and skill-level contract, not a runtime
guarantee.** The hermes dispatcher does not write `result.json`
on the worker's behalf, and `complete_task` does not inspect the
worker's workspace at all. If the worker omits `result.json`
(crash before the `except` block, OOM kill, SIGKILL from the
runtime cap, early `sys.exit`), the orchestrator MUST detect the
absence via the four-point check and treat it as failure — see
`Orchestrator-side Checks` below. Trusting exit code 0 in that
case re-opens the H-00 trap.

## Worker-side Scaffold

For workers built without a framework, this minimal scaffold
prevents the H-00 trap:

```python
import json
import sys
import traceback
from pathlib import Path

def finalize_workspace(workspace: Path, status: str, **kwargs):
    """Write result.json no matter what — even on exception."""
    output = workspace / "output"
    output.mkdir(parents=True, exist_ok=True)
    result = {"status": status, **kwargs}
    (output / "result.json").write_text(json.dumps(result, indent=2))

def main(workspace: Path):
    try:
        # ... actual work ...
        result_data = do_work(workspace)
        finalize_workspace(workspace, "ok", **result_data)
    except Exception as exc:
        finalize_workspace(
            workspace,
            "failed",
            error=str(exc),
            traceback=traceback.format_exc(),
        )
        sys.exit(1)
```

Use `try/finally` if the worker has cleanup that must run:

```python
def main(workspace: Path):
    try:
        setup()
        result_data = do_work(workspace)
        finalize_workspace(workspace, "ok", **result_data)
    except Exception as exc:
        finalize_workspace(workspace, "failed", error=str(exc))
    finally:
        cleanup()
```

The `finally` block ensures `result.json` is written even on
interpreter shutdown (KeyboardInterrupt, etc.). OOM kill and
SIGKILL from the runtime cap (`hermes kanban create
--max-runtime`) can still escape the scaffold — in those cases
the orchestrator MUST detect the missing `result.json` via the
four-point check (or a missing exit-code check) and treat the
task as failure. The scaffold is a worker-side convention; the
runtime does not back it up.

## LaneResult Contract (Rich Worker Report)

The flat `result.json` schema (`status`, `artifacts`, `error`) is the
**minimum viable contract** — enough to detect the H-00 trap. For complex
multi-lane orchestrations (queen-bee dispatch, pipeline steps, research
swarms), the richer **LaneResult** contract from `state_management.md`
should be used instead. It captures what the flat schema cannot:
open risks, unverified claims, and a confidence score.

### LaneResult Schema

```json
{
  "lane_id": "lane-01",
  "status": "pass|retry|blocked|failed",
  "summary": "One-paragraph summary of what the worker produced.",
  "evidence": ["artifact://output/report.md", "artifact://output/data.json"],
  "open_risks": ["Risk: model used for code generation was not verified against test suite"],
  "unverified_claims": ["Worker claims API throughput improved 2x but no benchmark artifact was produced"],
  "confidence": 0.85
}
```

### Field Mapping: Flat Contract → LaneResult

| Flat `result.json` | LaneResult | Notes |
|---|---|---|
| `status: "ok"` | `status: "pass"` | LaneResult renames to match lane vocabulary |
| `status: "failed"` | `status: "failed"` | Same semantics |
| — (no equivalent) | `status: "retry"` | Worker hit a transient issue (rate limit, timeout) and should be re-spawned |
| — (no equivalent) | `status: "blocked"` | Worker needs a human decision before proceeding |
| `artifacts: [...]` | `evidence: [...]` | LaneResult uses `artifact://` URIs pointing into `output/` |
| `error: "..."` | `summary` contains the error context | For `failed` status, `summary` carries the error narrative |
| — | `open_risks` | Known risks the worker couldn't resolve (e.g., "test coverage at 60%") |
| — | `unverified_claims` | Things the worker asserts but couldn't verify on disk |
| — | `confidence` | 0.0–1.0 self-assessment; orchestrator uses this to gate whether to auto-merge or send to review |

### When to Use Which Schema

- **Flat contract** (`status`/`artifacts`/`error`): single-worker tasks,
  simple pipelines, quick prototyping. The four-point check in
  Orchestrator-side Checks operates on this schema.
- **LaneResult contract**: multi-lane dispatches (queen-bee, swarm),
  research/review tasks where the parent needs to triage open risks,
  any task where downstream consumers make routing decisions based on
  `confidence` or `open_risks`.

### Discipline Rules for LaneResult

The four-point compliance check extends naturally:

1. `output/result.json` exists (same as flat).
2. Parses as JSON with a `status` field from the set
   `{pass, retry, blocked, failed}`.
3. If `status: "pass"`: every URI in `evidence` resolves to a file
   on disk under `output/`. This replaces the flat `artifacts` check.
4. If `status: "failed"`: `summary` must be non-empty (carries the
   error narrative). `confidence` should be 0.0.
5. If `status: "retry"`: `summary` should explain the transient issue.
   Orchestrator re-spawns once, then escalates.
6. If `status: "blocked"`: `summary` should state what decision is
   needed. Orchestrator routes to a human gate (same as
   `kanban_block`).
7. `confidence < 0.5` → orchestrator should NOT auto-merge even if
   `status: "pass"`. Route to review instead.

### Example: LaneResult Worker Scaffold

```python
import json
import sys
import traceback
from pathlib import Path

def finalize_lane_result(workspace: Path, status: str, summary: str,
                         evidence: list[str] | None = None,
                         open_risks: list[str] | None = None,
                         unverified_claims: list[str] | None = None,
                         confidence: float = 0.0) -> None:
    """Write result.json with the LaneResult contract."""
    output = workspace / "output"
    output.mkdir(parents=True, exist_ok=True)
    result = {
        "lane_id": workspace.name,
        "status": status,
        "summary": summary,
        "evidence": evidence or [],
        "open_risks": open_risks or [],
        "unverified_claims": unverified_claims or [],
        "confidence": confidence,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2))

def main(workspace: Path):
    try:
        report_path, data_path = do_work(workspace)
        finalize_lane_result(
            workspace, "pass",
            summary="Generated report with 3 benchmarks verified on disk.",
            evidence=[
                f"artifact://output/{report_path.name}",
                f"artifact://output/{data_path.name}",
            ],
            open_risks=["Benchmark suite covers 12/15 edge cases; 3 untested"],
            unverified_claims=[],
            confidence=0.85,
        )
    except Exception as exc:
        finalize_lane_result(
            workspace, "failed",
            summary=f"Worker crashed: {exc}\n{traceback.format_exc()}",
            confidence=0.0,
        )
        sys.exit(1)
```

### Orchestrator-side LaneResult Verification

```python
LANERESULT_STATUSES = {"pass", "retry", "blocked", "failed"}

def verify_lane_result(workspace_path: str) -> WorkerOutcome:
    workspace = Path(workspace_path)
    output_dir = workspace / "output"
    result_json = output_dir / "result.json"

    if not output_dir.is_dir():
        return WorkerOutcome.FAILED_NO_OUTPUT

    if not result_json.exists():
        if not any(output_dir.iterdir()):
            return WorkerOutcome.FAILED_NO_OUTPUT
        return WorkerOutcome.FAILED_UNFINALISED

    try:
        result = json.loads(result_json.read_text())
    except json.JSONDecodeError:
        return WorkerOutcome.FAILED_MALFORMED

    status = result.get("status")
    if status not in LANERESULT_STATUSES:
        return WorkerOutcome.FAILED_UNKNOWN_STATUS
    if status == "failed":
        return WorkerOutcome.FAILED_DECLARED
    if status == "retry":
        return WorkerOutcome.FAILED_DECLARED  # orchestrator re-spawns
    if status == "blocked":
        return WorkerOutcome.FAILED_DECLARED  # orchestrator routes to human

    # status == "pass": verify evidence on disk BEFORE returning SUCCESS
    for uri in result.get("evidence", []):
        rel = uri.replace("artifact://", "")
        if not (workspace / rel).exists():
            return WorkerOutcome.FAILED_ARTIFACT_MISSING

    # Low-confidence pass should not auto-merge — but that's a routing
    # decision, not a discipline failure. Return SUCCESS and let the
    # orchestrator decide.
    return WorkerOutcome.SUCCESS
```

## Verifier Step (H-50 Blackboard Convention)

In the coding-pipeline (H-31), every implement step has a paired
review step. The review step's job is to apply the
worker-failure-discipline check independently:

```
verifier_prompt = f"""
You are verifying the output of task {task_id}.

1. cd into {workspace_path}/output
2. Check result.json exists and parses as JSON
3. Check every artifact in result.json['artifacts'] exists on disk
4. Run the verify: command from the original task spec
5. Report VERDICT: APPROVE or VERDICT: REQUEST_CHANGES
   with - bullets for every check that failed

Do NOT trust result.json alone. Always check the disk.
"""
```

The verifier reads the disk (per H-43 layout) and reports its own
verdict. The orchestrator only marks the original task done when
both `result.json` says `status: "ok"` AND the verifier prints
`VERDICT: APPROVE`. The verdict string is the only
machine-readable outcome — gate/step decisions are surfaced
separately in the body or task metadata, never as fake tokens
like `SPEC_OK` / `QUALITY_OK` / `APPROVED` / `LOOP`.

## Failure Escalation

When a worker fails the discipline check:

1. **Re-queue once**: increase the retry counter, re-spawn with
   the same input (workers often succeed on retry; transient
   issues like rate limits resolve). The per-task retry budget
   is configurable via `hermes kanban create --max-retries N`.
2. **After retry exhaustion**: surface as a top-level failure in
   the kanban task body. Don't silently re-queue forever.
3. **After 2 consecutive failures**: route to a human gate
   (Telegram ping or `hermes kanban diagnostics` alert). The
   worker is likely stuck on something the operator needs to
   look at.

## Acceptance / Verification

A worker run is **compliant** iff:

1. `output/result.json` exists.
2. It parses as JSON with at minimum a `status` field.
3. If `status: "ok"`, every artifact in `artifacts` exists on
   disk.
4. If `status: "failed"`, an `error` field exists.

An orchestrator is **disciplined** iff:

1. It NEVER marks a task done without first checking
   `output/result.json` exists and parses.
2. It NEVER marks a task done on `exit_code == 0` alone.
3. It surfaces verifier verdicts to the operator, not silently
   accepts worker claims.
4. It escalates to a human gate after 2 consecutive failures.

**Engine vs. skill split:** the four-point compliance check is
a **skill-level obligation** of the verifier / pipeline
orchestrator. Hermes `complete_task` (`hermes kanban complete`)
accepts a free-form `--result` / `--summary` string from the
worker and never inspects the workspace's `output/result.json`;
the runtime performs no automatic validation. A disciplined
orchestrator therefore re-runs the four checks above before
flipping a task to `done`, regardless of what the worker or
dispatcher reported.

A runnable structural check lives in `test_skill.py` next to
this file — it pins the description length, section ordering,
canonical verdict strings, the no-fake-flag set, and the
artifact-check-before-`SUCCESS`-return invariant.

## Hermes CLI Pitfalls (Workers MÜSSEN kennen)

**STATUS-UPDATE (2026-07-21):** Patch 3.2 in `hermes_cli/main.py:15418` fixt
das Top-Level `args.func(args)`-Returncode-Schlucken. Damit ist
`hermes kanban` jetzt Exitcode-korrekt (1 bei Fehler, 0 bei Erfolg).
Workers können sich ab jetzt auf den Exitcode verlassen — Pitfall 1
unten bleibt aber als generelle Worker-Hygiene wertvoll für andere
Subcommands die noch nicht auditiert sind.

**Behoben:** Pitfall 1 für `hermes kanban` via Patch 3.2. Verbleibend:
Pitfall 2 (Workspace-Löschung) — noch nicht gefixt, vorsichtig bleiben.



**Pflicht-Wissen für jeden Worker der `hermes kanban` benutzt.**

### Pitfall 1: Exitcodes vom Hermes-CLI sind NICHT vertrauenswürdig

**Symptom:** `hermes kanban complete <id>` auf done-task gibt
`cannot complete (unknown id or terminal state)` auf stderr aus, aber
**Exitcode = 0**. Worker denken Task war erfolgreich → Endlos-Loop bis
60-Iteration-Timeout.

**Verifiziert 2026-07-21 (R-1.5 Vorfall):**
```
$ hermes kanban complete t_e2d1fb50 --summary "test"
cannot complete t_e2d1fb50 (unknown id or terminal state)
$ echo $?
0
```

**Betroffene Befehle (alle Subcommands von `hermes kanban`):**
- `complete` - gibt 0 zurück auch bei "cannot complete" Fehler
- `block` - gibt 0 zurück auch bei "unknown task" Fehler
- `create` - gibt 0 zurück auch bei Validierungsfehlern

**Worker-Regel:** NIE auf `$?` verlassen. Stattdessen:
1. **stdout/stderr parsen** auf Error-Marker (`cannot complete`, `unknown task`)
2. **`Completed <task_id>` Marker suchen** in stdout für Success
3. **Bei Fehler:** neu parsen und Retry mit anderer Strategie (z.B. `--result` Flag)
4. **Nach 3 Retries:** `hermes kanban block <task_id> "cannot complete after N retries: <details>"`

### Pitfall 2: Workspace wird nach complete() gelöscht

**Symptom:** Worker erstellen Spec-Files im Workspace, rufen
`hermes kanban complete` auf → alle Deliverables futsch.

**Verifiziert 2026-07-21 (R-1.5 Vorfall):** 4 Spec-Files (40+ KB) im
Workspace erstellt, NICHT via `hermes kanban attach` angehängt, alle verloren
nach complete().

**Worker-Pflicht:** VOR `hermes kanban complete` MÜSSEN alle Deliverables
explizit via `hermes kanban attach` angehängt werden.

```bash
# Falsch (R-1.5 hat das gemacht):
echo "Spec-Inhalt" > workspace/spec.md
hermes kanban complete $TASK_ID   # Workspace weg, Spec weg

# Richtig (immer):
echo "Spec-Inhalt" > workspace/spec.md
hermes kanban attach $TASK_ID workspace/spec.md  # zuerst attachen
hermes kanban complete $TASK_ID   # complete löscht NUR workspace, attachments bleiben
```

**Verifikation:** nach complete prüfen ob `attachments/<task_id>/` nicht leer ist.

## Anti-Patterns (Rejected Orchestrators)

| Anti-pattern | Why it's rejected |
|---|---|
| Marking a task done because `kanban worker_exit_code == 0` | Worker can exit 0 without producing anything (H-00 trap) |
| Assuming `hermes kanban complete` validates `output/result.json` | `complete_task` accepts a free-form `--result` / `--summary` string and never reads the worker's workspace; the four-point check stays the verifier's job |
| Trusting `output/result.json` status without checking disk | Worker can lie (bug, prompt injection, llm hallucination); verifier must check |
| Treating "no output" as "nothing to do" | Always a failure; the worker was supposed to do something |
| Routing a failure to "try again" forever | Need human escalation after N failures |
| Asking the worker "did you finish?" instead of reading the disk | Workers can claim "yes" without proof; trust the disk |
| Putting the artifact-existence check **after** an early `return SUCCESS` | Unreachable code; the trap survives the refactor |
| Calling `output_dir.iterdir()` without an `is_dir()` guard | Crashes with `FileNotFoundError` when worker produced nothing |
| Inventing verdict tokens (`SPEC_OK`, `QUALITY_OK`, `LOOP_OK`, etc.) | Breaks downstream parsers; only `VERDICT: APPROVE` / `VERDICT: REQUEST_CHANGES` are canonical |

## Failure Recovery

If a worker run is found non-compliant AFTER it's been marked
done (e.g. discovered by a later audit):

1. Mark the task `archived` (not `done` — distinguishes from
   clean completions) via `hermes kanban archive <task_id>`.
2. Re-spawn with the same input but with the original worker's
   workspace archived for forensics.
3. Add a comment to the original task via
   `hermes kanban comment <task_id> "..."`. Comments are shown
   by `hermes kanban show <task_id>` directly — there is **no**
   `--comments` flag on `show`; do not invent one.
4. Surface in `hermes kanban diagnostics` as a discipline
   violation so the operator can audit.

## Related Skills

- **`swarm-workspace-isolation`** (H-43): defines the layout
  (`output/result.json` location). This skill defines what goes
  IN that file.
- **`verify-before-fix`** (loaded by fix-step in H-50): the
  per-bullet verifier loop that catches
  "claimed-success-but-missing-artifact".
- **`coding-pipeline-orchestrator`** (H-31): the runtime that
  calls `verify_worker_output` at the end of every step.
- **`swarm-router`** (H-40): the kanban-swarm mode applies this
  discipline to every worker it spawns.
- **`state_management.md`** (Spec-Bundle): defines the LaneResult
  contract (status, summary, evidence, open_risks, unverified_claims,
  confidence) that the LaneResult Contract section above implements
  as the rich-schema extension of the flat `result.json`.
