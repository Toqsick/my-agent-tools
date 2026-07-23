"""Tests for the coding-pipeline-orchestrator skill's spawn_pipeline.py.

The script is invoked as ``python3 spawn_pipeline.py --title ...`` —
these tests exercise the underlying :func:`spawn` function directly,
using the standard ``fresh_home`` fixture pattern from
``tests/hermes_cli/test_kanban_boards.py`` so the kanban DB is
isolated per-test.

Refs: H-31 (hermes-v2 plan, 2026-07-20).
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path("/home/bratan/.hermes/skills/software-development/coding-pipeline-orchestrator/scripts/spawn_pipeline.py")


# ── module loader ──────────────────────────────────────────────────────


def _load_spawn_module():
    """Load spawn_pipeline.py as a module so we can call :func:`spawn`."""
    spec = importlib.util.spec_from_file_location("spawn_pipeline", SCRIPT_PATH)
    assert spec and spec.loader, f"could not load {SCRIPT_PATH}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules["spawn_pipeline"] = mod
    spec.loader.exec_module(mod)
    return mod


# ── fixture ────────────────────────────────────────────────────────────


@pytest.fixture
def fresh_home(tmp_path, monkeypatch):
    """Isolated HERMES_HOME (mirrors tests/hermes_cli/test_kanban_boards.py)."""
    home = tmp_path / "hermes_home"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    for var in (
        "HERMES_KANBAN_DB",
        "HERMES_KANBAN_WORKSPACES_ROOT",
        "HERMES_KANBAN_HOME",
        "HERMES_KANBAN_BOARD",
    ):
        monkeypatch.delenv(var, raising=False)
    try:
        import hermes_constants
        hermes_constants._cached_default_hermes_root = None  # type: ignore[attr-defined]
    except Exception:
        pass
    from hermes_cli import kanban_db as kb
    kb._INITIALIZED_PATHS.clear()
    return home


# ── tests ──────────────────────────────────────────────────────────────


class TestPipelineShape:
    def test_six_steps_defined(self) -> None:
        mod = _load_spawn_module()
        assert len(mod.PIPELINE_STEPS) == 5
        keys = [s["key"] for s in mod.PIPELINE_STEPS]
        assert keys == ["implement", "spec-review", "quality-review", "fix", "re-review"]

    def test_each_step_has_skills(self) -> None:
        mod = _load_spawn_module()
        for step in mod.PIPELINE_STEPS:
            assert isinstance(step["skills"], list)
            assert len(step["skills"]) >= 1, f"{step['key']} has no skills"

    def test_implement_loads_tdd_and_coding_specialist(self) -> None:
        mod = _load_spawn_module()
        impl = mod.PIPELINE_STEPS[0]
        assert impl["key"] == "implement"
        assert "test-driven-development" in impl["skills"]
        assert "coding-specialist" in impl["skills"]

    def test_spec_review_loads_writing_plans(self) -> None:
        """H-50 wiring: spec-review validates against the plan, so
        writing-plans must be in its skill set."""
        mod = _load_spawn_module()
        spec = next(s for s in mod.PIPELINE_STEPS if s["key"] == "spec-review")
        assert "writing-plans" in spec["skills"], (
            "spec-review must load writing-plans to read the source-of-truth plan"
        )

    def test_fix_loads_verify_before_fix(self) -> None:
        """H-50 wiring: fix must load verify-before-fix (no silent
        regression on review feedback)."""
        mod = _load_spawn_module()
        fix = next(s for s in mod.PIPELINE_STEPS if s["key"] == "fix")
        assert "verify-before-fix" in fix["skills"]

    def test_review_steps_load_critic_gate(self) -> None:
        mod = _load_spawn_module()
        review_keys = {"spec-review", "quality-review", "re-review"}
        for step in mod.PIPELINE_STEPS:
            if step["key"] in review_keys:
                assert "critic-gate" in step["skills"], (
                    f"{step['key']} must load critic-gate"
                )


class TestSpawnIntegration:
    def test_creates_root_and_five_children(self, fresh_home) -> None:
        from hermes_cli import kanban_db as kb

        mod = _load_spawn_module()
        result = mod.spawn(
            title="Add idempotency-key",
            body="Plan body.",
            board=None,
            priority=5,
            created_by="test",
            plan_file=None,
        )
        assert result["root_id"].startswith("t_")
        assert set(result["step_ids"].keys()) == {
            "implement", "spec-review", "quality-review", "fix", "re-review",
        }

        with kb.connect_closing() as conn:
            root = kb.get_task(conn, result["root_id"])
            children = [kb.get_task(conn, sid) for sid in result["step_ids"].values()]
        assert root.workflow_template_id == "coding-pipeline"
        assert root.current_step_key == "root"
        assert root.assignee is None
        assert root.status == "blocked"

    def test_children_have_workflow_metadata(self, fresh_home) -> None:
        from hermes_cli import kanban_db as kb

        mod = _load_spawn_module()
        result = mod.spawn(
            title="Foo",
            body="Bar.",
            board=None,
            priority=5,
            created_by="test",
            plan_file=None,
        )
        with kb.connect_closing() as conn:
            for step in mod.PIPELINE_STEPS:
                child = kb.get_task(conn, result["step_ids"][step["key"]])
                assert child.workflow_template_id == "coding-pipeline", (
                    f"{step['key']} missing workflow_template_id"
                )
                assert child.current_step_key == step["key"]

    def test_children_force_load_skills(self, fresh_home) -> None:
        from hermes_cli import kanban_db as kb

        mod = _load_spawn_module()
        result = mod.spawn(
            title="Foo",
            body="Bar.",
            board=None,
            priority=5,
            created_by="test",
            plan_file=None,
        )
        with kb.connect_closing() as conn:
            for step in mod.PIPELINE_STEPS:
                child = kb.get_task(conn, result["step_ids"][step["key"]])
                # Skills are stored as JSON; the kanban API may return
                # them as a list or string depending on backend version.
                loaded = child.skills
                if isinstance(loaded, str):
                    import json as _json
                    loaded = _json.loads(loaded)
                assert isinstance(loaded, list), (
                    f"{step['key']} skills should be a list, got {type(loaded)}"
                )
                for expected in step["skills"]:
                    assert expected in loaded, (
                        f"{step['key']} must load {expected}; loaded {loaded}"
                    )

    def test_children_are_unassigned_and_blocked(self, fresh_home) -> None:
        """H-00 dispatcher guard: every seeded task is unassigned."""
        from hermes_cli import kanban_db as kb

        mod = _load_spawn_module()
        result = mod.spawn(
            title="Foo",
            body="Bar.",
            board=None,
            priority=5,
            created_by="test",
            plan_file=None,
        )
        with kb.connect_closing() as conn:
            root = kb.get_task(conn, result["root_id"])
            for step in mod.PIPELINE_STEPS:
                child = kb.get_task(conn, result["step_ids"][step["key"]])
                assert child.assignee is None, f"{step['key']} assigned!"
                assert child.status == "blocked", f"{step['key']} status={child.status}"
        assert root.assignee is None

    def test_plan_file_attached_to_root(self, fresh_home, tmp_path) -> None:
        from hermes_cli import kanban_db as kb

        mod = _load_spawn_module()
        plan = tmp_path / "plan.md"
        plan.write_text("# Plan\n\nSpec body for the pipeline.")
        result = mod.spawn(
            title="Foo",
            body="ignored — --plan-file wins",
            board=None,
            priority=5,
            created_by="test",
            plan_file=str(plan),
        )
        with kb.connect_closing() as conn:
            attachments = kb.list_attachments(conn, result["root_id"])
        assert len(attachments) == 1
        assert attachments[0].filename == "plan.md"


class TestListByTemplate:
    def test_pipeline_filterable_by_workflow_template_id(self, fresh_home) -> None:
        """``hermes kanban list --workflow-template-id coding-pipeline``
        must see the whole family."""
        from hermes_cli import kanban_db as kb

        mod = _load_spawn_module()
        result = mod.spawn(
            title="Foo",
            body="Bar.",
            board=None,
            priority=5,
            created_by="test",
            plan_file=None,
        )
        with kb.connect_closing() as conn:
            all_coding = list(conn.execute(
                "SELECT id FROM tasks WHERE workflow_template_id = ?",
                ("coding-pipeline",),
            ).fetchall())
        assert len(all_coding) == 6  # root + 5 steps
        ids = {r["id"] for r in all_coding}
        assert result["root_id"] in ids
        for step_id in result["step_ids"].values():
            assert step_id in ids


# ── explicit-board binding + sticky block (H-22 / H-31) ───────────────


class TestExplicitBoardBinding:
    def test_explicit_board_pins_db_path(self, fresh_home) -> None:
        """[hermes-v2] H-22/H-31: passing ``board=`` must pin both the
        DB the pipeline reads/writes AND the attachment path under that
        board's directory — never the default board."""
        from hermes_cli import kanban_db as kb

        mod = _load_spawn_module()
        # Pre-create the board so kanban_db_path() can resolve it
        # without falling back to default.
        kb.create_board("explicit-board")

        plan = fresh_home / "plan.md"
        plan.write_text("# pipeline plan\n")

        result = mod.spawn(
            title="With explicit board",
            body="ignored",
            board="explicit-board",
            priority=5,
            created_by="test",
            plan_file=str(plan),
        )
        with kb.connect_closing(board="explicit-board") as conn:
            rows = list(conn.execute("SELECT id FROM tasks").fetchall())
        ids = {r["id"] for r in rows}
        assert result["root_id"] in ids, (
            "root task must be on the explicit board's DB"
        )

        # Attachments live under <root>/kanban/boards/explicit-board/attachments/<id>/.
        att_dir = kb.task_attachments_dir(result["root_id"], board="explicit-board")
        assert att_dir.exists(), (
            f"attachments dir must be on the explicit board; got {att_dir}"
        )
        assert (att_dir / "plan.md").exists()

    def test_root_task_stays_blocked_after_recompute_ready(self, fresh_home) -> None:
        """[CORE-PATCH] H-22/H-31: the root task created with
        ``initial_status='blocked'`` must NOT auto-promote to ``ready``
        on subsequent dispatcher ticks — the new emit-blocked-event path
        in ``create_task`` makes the sticky guard fire. Otherwise the
        dispatcher would happily promote an operator-parked root to
        ``ready`` and assign it to a worker before the operator was
        ready."""
        from hermes_cli import kanban_db as kb

        mod = _load_spawn_module()
        result = mod.spawn(
            title="Stick me",
            body="body",
            board=None,
            priority=5,
            created_by="test",
            plan_file=None,
        )
        with kb.connect_closing() as conn:
            for _ in range(5):
                promoted = kb.recompute_ready(conn)
                assert promoted == 0
                root = kb.get_task(conn, result["root_id"])
                assert root.status == "blocked", (
                    f"root auto-promoted: status={root.status}"
                )


class TestSkillDocumentation:
    @staticmethod
    def _text() -> str:
        return (SCRIPT_PATH.parent.parent / "SKILL.md").read_text(encoding="utf-8")

    def test_description_is_one_line_and_at_most_60_characters(self) -> None:
        import re

        descriptions = re.findall(r"^description: (.+)$", self._text(), re.MULTILINE)
        assert len(descriptions) == 1
        assert descriptions[0] != "|"
        assert len(descriptions[0]) <= 60

    def test_top_level_sections_follow_modern_order(self) -> None:
        import re

        headings = re.findall(r"^## (.+)$", self._text(), re.MULTILINE)
        assert headings == [
            "When to Use",
            "Quick Start",
            "Workflow",
            "Verification and Acceptance",
            "Anti-Patterns",
            "Failure Recovery",
            "Related Skills",
        ]

    def test_documented_kanban_syntax_is_canonical(self) -> None:
        import re

        text = self._text()
        normalized = " ".join(text.split())
        assert "--comments" not in text
        assert not re.search(r"--skill\s+[^\s`]+,[^\s`]+", text)
        assert "--skill test-driven-development --skill coding-specialist" in normalized
        assert "hermes kanban --board hermes-v2 list" in normalized
        assert "hermes kanban --board hermes-v2 show" in normalized
        assert not re.search(
            r"hermes kanban (?:list|create|show|assign|promote|comment)[^\n`]*--board",
            text,
        )

    def test_review_verdicts_use_only_canonical_tokens(self) -> None:
        import re

        verdicts = set(re.findall(r"VERDICT: ([A-Z_]+)", self._text()))
        assert verdicts == {"APPROVE", "REQUEST_CHANGES"}

    def test_helper_is_documented_as_scaffold_only(self) -> None:
        text = self._text()
        assert "creates only the blocked task scaffold" in text
        assert "no functioning automated end-to-end review loop today" in text
        assert "H-53" in text


class TestParentGateAndManualStart:
    """Hermetic checks that the SKILL.md pins the real behavior of the
    parent-gate machinery:

      * the root and children land at status='blocked' (sticky);
      * a normal ``hermes kanban promote`` on the implement child is
        refused because the parent (root) is not done/archived;
      * the documented manual v1 start uses ``--force`` as a
        deliberate operator override (not a default) and points at the
        real ``hermes kanban --board SLUG promote STEP_ID --force`` shape.
    """

    @staticmethod
    def _text() -> str:
        return (SCRIPT_PATH.parent.parent / "SKILL.md").read_text(encoding="utf-8")

    def test_docs_call_out_sticky_blocked_scaffold(self) -> None:
        text = self._text()
        # The behaviour must be named explicitly so an operator reading
        # the SKILL.md is not surprised by it.
        assert "sticky" in text.lower(), (
            "manual v1 start section must call the scaffold 'sticky'"
        )
        # The dedicated subsection must live under "## Workflow" as a
        # level-3 heading so it does not break the top-level ordering
        # assertion in test_top_level_sections_follow_modern_order.
        assert re.search(
            r"^###\s+Manual v1 Start",
            text,
            re.MULTILINE,
        ), "expected a `### Manual v1 Start` subsection (not a top-level ## heading)"
        # Initial status wording (root+children blocked).
        assert "initial_status='blocked'" in text, (
            "skill must document initial_status='blocked' as the scaffold default"
        )

    def test_docs_quote_real_parent_gate_error(self) -> None:
        text = self._text()
        # The CLI returns a literal "(use --force to override)" hint; the
        # docs must mention that exact wording so an operator searching
        # the file for it lands on the right section.
        assert "(use --force to override)" in text, (
            "SKILL.md must quote the real CLI error message so operators "
            "can recognise the parent-gate refusal"
        )
        # And must explain *why* it refuses.
        assert "parent" in text.lower() and "gate" in text.lower(), (
            "section must explain that the parent-gate refuses normal promotion"
        )

    def test_docs_document_force_as_deliberate_override(self) -> None:
        text = self._text()
        # The exact CLI form must appear verbatim with --force.
        assert re.search(
            r"hermes\s+kanban\s+--board\s+\S+\s+promote\s+\S+\s+--force",
            text,
        ), (
            "manual v1 start must show "
            "`hermes kanban --board SLUG promote STEP_ID --force`"
        )
        # And the warning that --force is an override, not a default.
        lower = text.lower()
        assert "deliberate" in lower or "override" in lower, (
            "--force must be framed as a deliberate operator override"
        )
        assert "auditable" in lower, (
            "must mention that --force records an audit-trail event"
        )

    def test_docs_promote_help_advertises_force_flag(self) -> None:
        """Hermetic check: the documented --force override matches the
        real `hermes kanban promote --help` flag. Catches a docs drift
        where someone invents a flag or rewrites the spelling."""
        result = subprocess.run(
            [
                "/home/bratan/.hermes/hermes-agent/venv/bin/hermes",
                "kanban", "promote", "--help",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        help_text = result.stdout
        assert "--force" in help_text, (
            "hermes kanban promote --help must advertise --force"
        )
        # argparse may wrap the description; collapse whitespace and
        # look for the parent-override phrasing semantically.
        norm = re.sub(r"\s+", " ", help_text)
        assert (
            "Promote even if parent dependencies are not yet done/archived"
            in norm
        ), (
            "real --force help text must document the parent-override "
            f"semantics; got: {norm!r}"
        )

    def test_docs_require_root_left_as_blackboard(self) -> None:
        text = self._text()
        lower = text.lower()
        # The root must explicitly NOT be promoted — it is the blackboard.
        assert (
            "do not promote the root" in lower
            or "do **not** promote the root" in lower
            or "do not promote the root" in lower
        ), (
            "skill must warn operators NOT to promote the root"
        )
        assert "blackboard" in lower, (
            "root must be described as the park / blackboard task"
        )

    def test_normal_promote_refused_force_succeeds_hermetic(self) -> None:
        """End-to-end hermetic test of the parent-gate on a fresh
        spawn_pipeline run: normal promote of the implement child MUST
        be refused (parent root is blocked); promote --force MUST put
        implement to status='ready' and emit a forced audit event.
        """
        import subprocess

        from hermes_cli import kanban_db as kb

        mod = _load_spawn_module()

        # We need a fresh home; reuse the existing fixture indirectly
        # by constructing one inline so the class test can run as a
        # pytest method (the fixture is per-method anyway).
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_home:
            os.environ["HERMES_HOME"] = tmp_home
            for var in (
                "HERMES_KANBAN_DB",
                "HERMES_KANBAN_WORKSPACES_ROOT",
                "HERMES_KANBAN_HOME",
                "HERMES_KANBAN_BOARD",
            ):
                os.environ.pop(var, None)
            try:
                import hermes_constants
                hermes_constants._cached_default_hermes_root = None  # type: ignore[attr-defined]
            except Exception:
                pass
            kb._INITIALIZED_PATHS.clear()

            result = mod.spawn(
                title="Parent-gate probe",
                body="ignored",
                board=None,
                priority=5,
                created_by="test",
                plan_file=None,
            )
            root_id = result["root_id"]
            implement_id = result["step_ids"]["implement"]

            # Sanity: root + implement both blocked.
            with kb.connect_closing() as conn:
                root = kb.get_task(conn, root_id)
                impl = kb.get_task(conn, implement_id)
                assert root.status == "blocked"
                assert impl.status == "blocked"

                # 1. Normal promote MUST be refused (parent root is blocked).
                ok, reason = kb.promote_task(
                    conn, implement_id, actor="test", force=False, reason=None
                )
                assert ok is False, (
                    "promote_task should refuse when parent is not done/archived"
                )
                assert reason and "unsatisfied parent" in reason, (
                    f"unexpected refusal reason: {reason!r}"
                )
                # And the implement status must remain 'blocked'.
                impl = kb.get_task(conn, implement_id)
                assert impl.status == "blocked"

                # 2. promote --force MUST succeed and flip status='ready'.
                ok, reason = kb.promote_task(
                    conn, implement_id, actor="test", force=True, reason="v1 start"
                )
                assert ok is True, (
                    f"--force override should succeed; got refusal: {reason!r}"
                )
                impl = kb.get_task(conn, implement_id)
                assert impl.status == "ready", (
                    f"force-promote should set status=ready, got {impl.status}"
                )

                # 3. The override must be auditable (forced=True on the
                #    promoted_manual task_event). task_events schema uses
                #    ``kind`` + ``payload`` (JSON-encoded) columns, not
                #    ``event_type`` + ``payload_json``.
                ev_rows = list(conn.execute(
                    "SELECT kind, payload FROM task_events "
                    "WHERE task_id = ? AND kind = 'promoted_manual'",
                    (implement_id,),
                ).fetchall())
                assert ev_rows, "expected a promoted_manual event row"
                import json as _json
                payload = _json.loads(ev_rows[-1]["payload"])
                assert payload.get("forced") is True, (
                    f"promoted_manual payload must record forced=True; got {payload!r}"
                )
