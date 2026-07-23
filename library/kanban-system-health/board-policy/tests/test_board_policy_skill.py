"""Structural + CLI-verified checks for board-policy SKILL.md.

Pins:
  - YAML `description` is a single line, max 60 characters.
  - Section ordering matches the modern hermes-v2 layout.
  - The schema documents only the real CLI choices for
    `--initial-status` (``blocked | running``); ``ready`` is forbidden.
  - SKILL.md is **declarative-only**: there is no real
    `apply-policy` subcommand on the hermes CLI, and the docs must
    not claim one exists.
  - The `Failure Recovery / Troubleshooting` section is canonical.
  - Documented `hermes kanban create --initial-status` choices match
    the real CLI (``blocked`` or ``running`` only).

Run with the project venv:
    /home/bratan/.hermes/hermes-agent/venv/bin/python tests/test_board_policy_skill.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml  # PyYAML ships in the repo venv
except ImportError as exc:  # pragma: no cover - guarded for environments without it
    print(f"PyYAML required: {exc}", file=sys.stderr)
    sys.exit(2)


SKILL_PATH = Path(__file__).resolve().parent.parent / "SKILL.md"
HERMES = "/home/bratan/.hermes/hermes-agent/venv/bin/hermes"


def _read() -> str:
    assert SKILL_PATH.is_file(), f"SKILL.md missing at {SKILL_PATH}"
    return SKILL_PATH.read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert m, "SKILL.md must start with YAML front-matter delimited by ---"
    return yaml.safe_load(m.group(1))


# ---------------------------------------------------------------------------
# 1. description: one line, <= 60 chars
# ---------------------------------------------------------------------------
def test_description_one_line_under_60_chars() -> None:
    fm = _frontmatter(_read())
    desc = fm.get("description")
    assert isinstance(desc, str), "description must be a string (no block scalar)"
    assert "\n" not in desc, f"description must be one line, got: {desc!r}"
    assert 0 < len(desc) <= 60, f"description length {len(desc)} not in (0, 60]"
    print(f"OK description is {len(desc)} chars: {desc!r}")


# ---------------------------------------------------------------------------
# 2. Section ordering matches the modern hermes-v2 layout.
# ---------------------------------------------------------------------------
REQUIRED_SECTIONS = [
    "When to Use",
    "Quick Start",
    "Procedure",
    "Verification and Acceptance",
    "Anti-Patterns",
    "Failure Recovery / Troubleshooting",
    "Related Skills and References",
]
# The exact order Anti-Patterns → Failure Recovery is canonical for the
# hermes-v2 layout (matches coding-pipeline-orchestrator,
# worker-failure-discipline, swarm-workspace-isolation, swarm-router).


def test_section_ordering() -> None:
    text = _read()
    positions: list[tuple[str, int]] = []
    for needle in REQUIRED_SECTIONS:
        # Match `## Foo` or `## Foo (something)` etc.
        pattern = re.compile(rf"^## [^\n]*{re.escape(needle)}[^\n]*$", re.MULTILINE)
        m = pattern.search(text)
        assert m, f"required section heading not found: {needle!r}"
        positions.append((needle, m.start()))
    sorted_positions = sorted(positions, key=lambda x: x[1])
    order = [p[0] for p in positions]
    sorted_order = [p[0] for p in sorted_positions]
    assert order == sorted_order, (
        f"section order mismatch.\n  got:      {order}\n  expected: {sorted_order}"
    )


# ---------------------------------------------------------------------------
# 3. schema `initial_status` documents only real CLI choices (blocked | running).
#    `ready` is forbidden except as an explicit anti-pattern reference.
# ---------------------------------------------------------------------------
def test_initial_status_only_blocked_or_running() -> None:
    text = _read()
    # Allowed phrasing: the choice must be `blocked | running` (or `blocked or running`).
    # The forbidden value `ready` must NOT appear as a documented schema value.
    assert re.search(r"blocked\s*[|,]\s*running", text) or re.search(
        r"blocked\s+or\s+running", text
    ), "skill must document initial_status as `blocked | running` (or equivalent)"
    # `initial_status: ready` is forbidden as a *schema value*. It may
    # appear inside the Anti-Patterns row that calls out the trap.
    bad = re.compile(r"^\s*initial_status\s*:\s*ready\b", re.IGNORECASE | re.MULTILINE)
    assert not bad.search(text), (
        "skill must NOT document `initial_status: ready` as a schema value; "
        "real CLI choices are only `blocked` and `running`"
    )
    # And the explicit anti-pattern row must call out ready as not-real.
    assert "ready" in text.lower(), "skill must reference `ready` (to negate it)"
    print("OK initial_status documented only as blocked|running")


def test_initial_status_matches_real_cli_choices() -> None:
    """Hermetic check: the real `hermes kanban create --help` exposes only
    {blocked, running} for --initial-status. The skill must agree."""
    help_out = subprocess.run(
        [HERMES, "kanban", "create", "--help"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    # argparse renders the choices as `--initial-status {blocked,running}`.
    assert "{blocked,running}" in help_out or (
        "blocked" in help_out and "running" in help_out and "ready" not in help_out
    ), (
        "real `hermes kanban create --initial-status` must be {blocked,running} "
        "(no `ready`); got:\n" + help_out
    )
    print("OK real CLI exposes --initial-status {blocked,running}")


# ---------------------------------------------------------------------------
# 4. SKILL.md is declarative-only; no `apply-policy` claim.
# ---------------------------------------------------------------------------
def test_no_apply_policy_claim() -> None:
    text = _read()
    lower = text.lower()
    # The skill is declarative-only. There is no `apply-policy` subcommand.
    # Pinning the negative: phrases that imply a runtime apply hook must
    # not appear.
    forbidden_phrases = [
        "apply-policy",
        "apply_policy",
        "hermes kanban apply-policy",
        "hermes board apply-policy",
        "apply the policy automatically",
        "BOARD.md is applied automatically",
        "BOARD.md is loaded automatically",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in lower, (
            f"forbidden auto-apply phrasing present: {phrase!r}; BOARD.md is "
            f"declarative-only — values transfer only via real task flags"
        )
    # Positive: the docs must declare declarative-only behaviour.
    assert "declarative only" in lower or "declarative-only" in lower, (
        "skill must declare BOARD.md is declarative-only"
    )
    print("OK no apply-policy claim; declarative-only documented")


# ---------------------------------------------------------------------------
# 5. Real `hermes kanban create --help` advertises --initial-status and
#    --max-retries (the two supported flag mappings referenced by the schema).
# ---------------------------------------------------------------------------
def test_supported_flag_mappings_exist_on_real_cli() -> None:
    help_out = subprocess.run(
        [HERMES, "kanban", "create", "--help"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "--initial-status" in help_out, (
        "`hermes kanban create --help` must advertise --initial-status"
    )
    # --max-retries is the canonical mapping for max_retries.
    assert "--max-retries" in help_out, (
        "`hermes kanban create --help` must advertise --max-retries"
    )
    print("OK real CLI advertises --initial-status and --max-retries")


if __name__ == "__main__":
    failures: list[str] = []
    tests = [
        test_description_one_line_under_60_chars,
        test_section_ordering,
        test_initial_status_only_blocked_or_running,
        test_initial_status_matches_real_cli_choices,
        test_no_apply_policy_claim,
        test_supported_flag_mappings_exist_on_real_cli,
    ]
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failures.append(f"[FAIL] {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failures.append(f"[ERROR] {t.__name__}: {e!r}")
        else:
            print(f"[PASS] {t.__name__}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        sys.exit(1)
    print(f"\nAll {len(tests)} board-policy structure checks passed.")
    sys.exit(0)