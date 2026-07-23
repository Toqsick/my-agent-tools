"""Structural and CLI-verified checks for swarm-workspace-isolation SKILL.md.

These are minimal, repo-venv-runnable guards. They do not exercise the
hermes runtime end-to-end; they pin the documented contracts against the
real `hermes kanban ... --help` output and the SKILL.md structure.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_DIR / "SKILL.md"
HERMES = "/home/bratan/.hermes/hermes-agent/venv/bin/hermes"

EXPECTED_SECTIONS = [
    "## When to Use",
    "## Quick Start",
    "## Workspace layout",
    "## Read-only input mount",
    "## Per-worker scratch",
    "## Output contract",
    "## Cleanup policy",
    "## Cross-worker file sharing",
    "## Worker-side startup",
    "## Interaction with coding-pipeline-orchestrator (H-31)",
    "## Verification / Acceptance",
    "## Anti-patterns",
    "## Failure recovery",
    "## Related skills",
]


def _read_skill() -> str:
    assert SKILL_MD.is_file(), f"SKILL.md missing at {SKILL_MD}"
    return SKILL_MD.read_text(encoding="utf-8")


def _load_front_matter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert m, "SKILL.md must start with YAML front-matter delimited by ---"
    return yaml.safe_load(m.group(1))


def _run_hermes_help(args: list[str]) -> str:
    """Run `<hermes> <args> --help` and return stdout."""
    result = subprocess.run(
        [HERMES, *args, "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


# --- Front-matter shape ---------------------------------------------------


def test_description_is_single_line_and_within_60_chars():
    text = _read_skill()
    fm = _load_front_matter(text)
    desc = fm.get("description")
    assert isinstance(desc, str), "description must be a string (no block scalar)"
    assert "\n" not in desc, f"description must be one line, got: {desc!r}"
    assert 0 < len(desc) <= 60, f"description length {len(desc)} not in (0, 60]"


def test_required_front_matter_fields():
    text = _read_skill()
    fm = _load_front_matter(text)
    for field in ("name", "description", "version"):
        assert field in fm, f"missing front-matter field: {field}"
    assert fm["name"] == "swarm-workspace-isolation"


# --- Section ordering -----------------------------------------------------


@pytest.mark.parametrize("section", EXPECTED_SECTIONS)
def test_section_present(section: str):
    text = _read_skill()
    assert section in text, f"missing section: {section}"


def test_section_order_matches_modern_convention():
    text = _read_skill()
    positions = []
    for s in EXPECTED_SECTIONS:
        idx = text.find(s)
        assert idx != -1, f"missing section: {s}"
        positions.append(idx)
    assert positions == sorted(positions), (
        "sections must appear in modern order: "
        "When to Use → Quick Start → Workflow → Verification → "
        "Anti-patterns → Failure recovery → Related skills"
    )


# --- Real Hermes commands documented --------------------------------------


def test_no_fake_cleanup_flag_on_complete():
    """`hermes kanban complete` must not be documented as accepting --cleanup.

    Mentions of `kanban complete --cleanup` are allowed only when the
    surrounding sentence explicitly calls it out as a non-existent flag
    (e.g. inside an Anti-patterns row that documents the trap).
    """
    text = _read_skill()
    pat = re.compile(r"kanban\s+complete[^.\n]*--cleanup", re.IGNORECASE)
    violations: list[str] = []
    for m in pat.finditer(text):
        # Allow only when the surrounding line(s) explicitly negate the flag.
        start = max(0, m.start() - 200)
        end = min(len(text), m.end() + 200)
        window = text[start:end].lower()
        if any(
            phrase in window
            for phrase in (
                "does not exist",
                "doesn't exist",
                "non-existent",
                "no `--cleanup`",
                "no --cleanup",
                "not a real flag",
            )
        ):
            continue
        violations.append(m.group(0))
    assert not violations, (
        "SKILL.md presents `kanban complete --cleanup` as a real flag, but the "
        "flag does not exist on `hermes kanban complete`. Document cleanup "
        "via `kanban archive` / `kanban gc` instead. Offending matches: "
        f"{violations!r}"
    )


def test_no_fake_comments_flag_on_show():
    """`hermes kanban show` has no `--comments` flag; comments are default."""
    text = _read_skill()
    bad = re.compile(r"kanban\s+show[^`\n]*--comments")
    assert not bad.search(text), (
        "SKILL.md documents a non-existent `kanban show --comments` flag; "
        "`show` prints comments by default."
    )


def test_hermes_kanban_complete_help_has_no_cleanup_flag():
    """Verify against the real CLI: `complete --help` must not advertise --cleanup."""
    help_out = _run_hermes_help(["kanban", "complete"])
    assert "--cleanup" not in help_out, (
        "hermes kanban complete --help unexpectedly advertises --cleanup"
    )
    # It should advertise the real flags.
    assert "--result" in help_out
    assert "--summary" in help_out
    assert "--metadata" in help_out


def test_hermes_kanban_show_help_has_no_comments_flag():
    help_out = _run_hermes_help(["kanban", "show"])
    assert "--comments" not in help_out, (
        "hermes kanban show --help unexpectedly advertises --comments"
    )


def test_hermes_kanban_archive_help_documents_rm_flag():
    help_out = _run_hermes_help(["kanban", "archive"])
    assert "--rm" in help_out, (
        "hermes kanban archive --help should advertise --rm for purge"
    )


def test_hermes_kanban_gc_help_documents_retention_flags():
    help_out = _run_hermes_help(["kanban", "gc"])
    assert "--event-retention-days" in help_out
    assert "--log-retention-days" in help_out


def test_global_board_flag_is_supported():
    """`hermes kanban --board SLUG <sub>` is the documented way to pin a board."""
    help_out = subprocess.run(
        [HERMES, "kanban", "--help"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "--board <slug>" in help_out, (
        "hermes kanban --help must document the global --board option"
    )


# --- Workspace path layout contract ---------------------------------------


def test_workspace_layout_pinned():
    text = _read_skill()
    # Pinned substrings that any future edit must preserve.
    for needle in [
        "<board_root>/workspaces/<task_id>/",
        "input/",
        "output/",
        "cache/",
        "logs/",
        "result.json",
    ]:
        assert needle in text, f"layout contract missing: {needle!r}"


# --- Convention vs. lifecycle: input/output/cache/logs, MD5, chmod ------


def test_convention_vs_lifecycle_callout_present():
    """The skill must state that input/output/cache/logs, MD5 guards,
    and chmod are worker / orchestrator conventions — NOT something
    the dispatcher bootstraps."""
    text = _read_skill()
    for needle in [
        "convention",
        "lifecycle",
        "_cleanup_workspace",
    ]:
        assert needle.lower() in text.lower(), (
            f"convention-vs-lifecycle callout missing token: {needle!r}"
        )
    # Explicitly: the lifecycle does NOT mkdir input/output/cache/logs.
    assert "does not create these subdirs" in text or "does NOT mkdir" in text, (
        "skill must declare that subdirs and MD5/chmod are worker-side,"
        " not lifecycle-created"
    )


def test_cleanup_policy_pins_cleanup_workspace():
    """Cleanup policy must reflect real kanban lifecycle:
    ``_cleanup_workspace`` removes scratch dirs on ``complete_task``;
    worktree/dir are preserved; archive only touches task rows; gc is
    event/log retention, NOT workspace retention."""
    text = _read_skill()
    needle_pairs = [
        ("_cleanup_workspace", "_cleanup_workspace is the documented runtime path"),
        ("complete_task", "completion drives the cleanup hook"),
        ("workspace_kind='scratch'", "scoped to scratch workspaces only"),
        ("worktree", "worktree workspaces preserved by design"),
        ("dir", "dir workspaces preserved by design"),
    ]
    for needle, why in needle_pairs:
        assert needle in text, f"Cleanup policy missing: {needle!r} ({why})"

    # The false claims must no longer appear:
    forbidden_false_claims = [
        ("After 30 days idle",
         "30-day workspace retention is fiction; gc is event/log retention"),
        ("automatic archive (compressed, kept)",
         "no automatic compressed-archive retention exists for scratch workspaces"),
        ("workspace is moved to the archive area",
         "archive does NOT move workspace dirs; only task rows are archived"),
    ]
    for phrase, why in forbidden_false_claims:
        assert phrase not in text, (
            f"False runtime claim leaked into Cleanup policy: {phrase!r} ({why})"
        )


def test_archive_and_gc_not_workspace_retention():
    """Documented separation: `archive` only flips task rows to
    archived (does NOT move workspace); `gc` only prunes
    task_events rows + worker log files."""
    text = _read_skill()
    assert "archive" in text and "does NOT move the workspace" in text, (
        "must document that archive does not move workspace dirs"
    )
    assert "gc" in text and ("not" in text) and ("workspace retention" in text), (
        "must document that gc is not a workspace retention mechanism"
    )


def test_helper_verify_workspace_cleanup():
    """Hermetic check: the docs must point at ``_cleanup_workspace`` as
    the function that scrubs scratch workspaces, and ``complete_task``
    as the only call-site. Avoids claiming a CLI flag that does not exist."""
    text = _read_skill()
    # The function name appears by documentation, not by import.
    assert "_cleanup_workspace(conn, task_id)" in text, (
        "skill must quote the real call signature `_cleanup_workspace(conn, task_id)`"
    )
    assert "complete_task" in text, (
        "skill must reference complete_task as the call site"
    )
    # Any `complete --cleanup` mention must live in a window that
    # explicitly says the flag does not exist (anti-pattern row).
    pat = re.compile(r"complete[^.\n]*--cleanup", re.IGNORECASE)
    for m in pat.finditer(text):
        window = text[max(0, m.start() - 120): m.end() + 120].lower()
        assert any(
            phrase in window
            for phrase in (
                "does not exist",
                "doesn't exist",
                "non-existent",
                "no `--cleanup`",
                "no --cleanup",
                "never a completion flag",
            )
        ), (
            "`complete --cleanup` appears outside an explicit does-not-exist "
            f"window at offset {m.start()}"
        )

    # And verify against the real binary the helper would call: there is
    # no --cleanup flag on `hermes kanban complete --help`.
    help_out = _run_hermes_help(["kanban", "complete"])
    assert "--cleanup" not in help_out
    # gc must advertise the event/log retention flags, not workspace ones.
    gc_help = _run_hermes_help(["kanban", "gc"])
    assert "--event-retention-days" in gc_help
    assert "--log-retention-days" in gc_help
    assert "workspace" not in gc_help.lower(), (
        "hermes kanban gc --help must not mention workspace retention"
    )


# --- Verdict-protocol sanity (this skill does not issue verdicts) --------


def test_no_fabricated_review_verdict_protocol():
    text = _read_skill()
    # The skill may legitimately mention `VERDICT: APPROVE` / `REQUEST_CHANGES`
    # as a reference, but it must not define a separate machine-readable verb.
    forbidden_verbs = [
        "SPEC_OK",
        "QUALITY_OK",
        "APPROVED",  # bare token, not part of a sentence
        "VERDICT_OK",
    ]
    for token in forbidden_verbs:
        assert token not in text, (
            f"SKILL.md invents a non-canonical review-verdict token: {token}"
        )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
