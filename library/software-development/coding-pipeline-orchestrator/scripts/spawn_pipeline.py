#!/usr/bin/env python3
"""Spawn a hermes-v2 coding-pipeline on a Kanban board.

Used by the coding-pipeline-orchestrator skill (H-31 in the
hermes-v2 plan, 2026-07-20). Creates a 5-step pipeline (implement →
spec-review → quality-review → fix → re-review) with workflow metadata
so `hermes kanban list --workflow-template-id coding-pipeline` can
filter the whole family.

This script is deliberately thin — it composes the existing
``hermes_cli.kanban_db`` primitives (``create_task``, ``link_tasks``,
``add_attachment``) rather than introducing a new engine. The
pipeline is **convention, not engine**: the steps are normal Kanban
tasks linked by ``task_links`` rows, with
``workflow_template_id='coding-pipeline'`` and ``current_step_key``
set as metadata columns.

All tasks are created with ``assignee=None`` (H-00 dispatcher
guard at ``kanban_db.py:8188`` blocks spawning until the operator
explicitly assigns a worker). The orchestrator (the calling agent)
prints the resulting task-id tree so the operator can ``assign`` +
``promote`` step-by-step.

Usage:

    ~/.hermes/hermes-agent/venv/bin/python3 spawn_pipeline.py \\
        --title "Add idempotency-key to webhook handler" \\
        --body  "Plan body / spec text" \\
        --board hermes-v2 \\
        --priority 5

Optional:

    --plan-file PATH    Read --body from this file (UTF-8)
    --created-by NAME   Stamped on all tasks
    --json              Emit a JSON object with the task-id tree instead
                        of the human-readable form

Refs: H-31 (hermes-v2 plan), kanban_db.py:8188 (assignee guard).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# Make the hermes-agent tree importable so we can reach the kanban
# module. The skill lives at ~/.hermes/skills/... and the orchestrator
# script is invoked from a venv interpreter.
_HERMES_AGENT = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))) / "hermes-agent"
if str(_HERMES_AGENT) not in sys.path:
    sys.path.insert(0, str(_HERMES_AGENT))


# ── Pipeline shape (mirrors SKILL.md table) ───────────────────────────

PIPELINE_STEPS: List[Dict[str, Any]] = [
    {
        "key": "implement",
        "title": "implement",
        "skills": ["test-driven-development", "coding-specialist", "verify-before-fix"],
    },
    {
        "key": "spec-review",
        "title": "spec-review",
        # H-50: spec-review validates against plan/spec, not code style —
        # so it loads writing-plans (to read the source of truth) +
        # test-driven-development (to check the test plan is honoured),
        # in addition to the reviewer toolkit.
        "skills": ["writing-plans", "test-driven-development", "requesting-code-review", "critic-gate"],
    },
    {
        "key": "quality-review",
        "title": "quality-review",
        "skills": ["simplify-code", "critic-gate", "output-validator"],
    },
    {
        "key": "fix",
        "title": "fix",
        # H-50: the fix step's job is to address reviewer comments
        # posted on its parent task (the blackboard convention). It
        # also re-loads test-driven-development so the fix doesn't
        # silently regress coverage.
        "skills": ["verify-before-fix", "test-driven-development", "simplify-code"],
    },
    {
        "key": "re-review",
        "title": "re-review",
        "skills": ["requesting-code-review", "critic-gate"],
    },
]


def _set_workflow_metadata(
    conn: Any,
    task_id: str,
    workflow_template_id: str,
    current_step_key: str,
) -> None:
    """Patch ``workflow_template_id`` + ``current_step_key`` after create_task.

    The kanban_db.create_task() Python API doesn't currently expose
    these columns as kwargs (schema has them; engine is v1-unused).
    Per the hermes-v2 plan §H-31, the pipeline is **convention, not
    engine**: we set the metadata via a direct UPDATE rather than
    patching create_task. The columns exist since migration 0274
    (see kanban_db.py:1927) so this is purely a Python-side gap.
    """
    conn.execute(
        "UPDATE tasks SET workflow_template_id = ?, current_step_key = ? WHERE id = ?",
        (workflow_template_id, current_step_key, task_id),
    )


def spawn(
    *,
    title: str,
    body: str,
    board: Optional[str],
    priority: int,
    created_by: Optional[str],
    plan_file: Optional[str],
) -> Dict[str, Any]:
    """Create the root task + 5 children + (optional) plan attachment.

    Returns ``{"root_id": str, "step_ids": {step_key: task_id}}``.
    """
    # Lazy import — keeps the script CLI-runnable from a venv even if
    # the hermes_agent package has heavy native deps that aren't
    # importable from a shell context.
    from hermes_cli import kanban_db as kb

    root_body = body
    plan_path_for_attach: Optional[Path] = None
    if plan_file:
        p = Path(plan_file)
        root_body = p.read_text(encoding="utf-8")
        plan_path_for_attach = p

    step_ids: Dict[str, str] = {}
    # Pin the DB connection to the requested board — when the operator
    # passes ``--board foo`` we MUST write to foo's kanban.db, not the
    # default board. Without ``board=board`` here the connection would
    # honour ``HERMES_KANBAN_BOARD`` / ``<root>/kanban/current`` /
    # ``default``, which silently places the pipeline root on the
    # wrong board when those disagree with ``args.board`` (H-22).
    with kb.connect_closing(board=board) as conn:
        root_id = kb.create_task(
            conn,
            title=title,
            body=root_body,
            assignee=None,
            created_by=created_by,
            priority=priority,
            initial_status="blocked",
            board=board,
        )
        # Patch workflow metadata (see _set_workflow_metadata docstring).
        if root_id:
            _set_workflow_metadata(conn, root_id, "coding-pipeline", "root")
        if root_id and plan_path_for_attach:
            # Attachments live under the *same* board's root so the
            # operator sees them via ``hermes kanban show`` regardless
            # of which board they ``switch`` to later.
            attachments_dir = kb.task_attachments_dir(root_id, board=board)
            attachments_dir.mkdir(parents=True, exist_ok=True)
            stored = attachments_dir / plan_path_for_attach.name
            stored.write_text(plan_path_for_attach.read_text(encoding="utf-8"), encoding="utf-8")
            kb.add_attachment(
                conn,
                root_id,
                filename=plan_path_for_attach.name,
                stored_path=str(stored),
                uploaded_by=created_by,
            )

        for step in PIPELINE_STEPS:
            child_id = kb.create_task(
                conn,
                title=f"{step['title']}: {title}",
                body=(
                    f"**Pipeline step:** {step['key']}\n"
                    f"**Parent root:** `{root_id}`\n"
                    f"**Skills:** {', '.join(step['skills'])}\n\n"
                    f"{root_body}"
                ),
                assignee=None,
                created_by=created_by,
                parents=(root_id,),
                priority=priority,
                initial_status="blocked",
                skills=step["skills"],
                board=board,
            )
            if child_id:
                _set_workflow_metadata(conn, child_id, "coding-pipeline", step["key"])
            step_ids[step["key"]] = child_id

    return {"root_id": root_id, "step_ids": step_ids}


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Spawn a hermes-v2 coding-pipeline on a Kanban board.",
    )
    p.add_argument("--title", required=True, help="Pipeline root task title")
    p.add_argument(
        "--body",
        default=None,
        help="Spec / plan body text. If --plan-file is also given, "
             "--plan-file wins.",
    )
    p.add_argument(
        "--plan-file",
        default=None,
        help="Read body from this file path; also attach the file to the root task.",
    )
    p.add_argument(
        "--board",
        default=None,
        help="Kanban board slug. Defaults to the active board.",
    )
    p.add_argument(
        "--priority",
        type=int,
        default=5,
        help="Initial priority for all tasks (default 5 = B-tier).",
    )
    p.add_argument(
        "--created-by",
        default="coding-pipeline-orchestrator",
        help="Author stamped on every created task.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON with the task-id tree instead of human-readable text.",
    )
    args = p.parse_args(argv)

    if not args.body and not args.plan_file:
        p.error("provide --body or --plan-file")

    body = args.body or ""
    if args.plan_file and not Path(args.plan_file).exists():
        print(f"spawn_pipeline: --plan-file not found: {args.plan_file}", file=sys.stderr)
        return 2

    try:
        result = spawn(
            title=args.title,
            body=body,
            board=args.board,
            priority=args.priority,
            created_by=args.created_by,
            plan_file=args.plan_file,
        )
    except Exception as exc:  # noqa: BLE001 — boundary
        print(f"spawn_pipeline: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Pipeline root: {result['root_id']}")
        print("Steps:")
        for step in PIPELINE_STEPS:
            print(f"  {step['key']:18s} {result['step_ids'][step['key']]}")
        print("\nNext: assign + promote each step when ready:")
        for step in PIPELINE_STEPS:
            sid = result["step_ids"][step["key"]]
            print(f"  hermes kanban assign {sid} <lane>  # implement→worker-heavy, review→gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
