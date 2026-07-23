"""Structural + CLI-verified checks for todo-kanban-promotion SKILL.md.

Pins:
  - YAML `description` is a single line, max 60 characters.
  - Section ordering matches the modern hermes-v2 layout.
  - `hermes todo` is **not** a real subcommand — the skill must say so
    explicitly and never suggest invoking it.
  - The promoted task is created via the real
    `hermes kanban --board <slug> create ...` command (with documented
    `--idempotency-key` for crash-safe retries). No invented flags.
  - No `--comments` or `--cleanup` flag is documented on
    `hermes kanban create`; these flags do not exist.

Run with the project venv:
    /home/bratan/.hermes/hermes-agent/venv/bin/python tests/test_todo_kanban_promotion_skill.py
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
    "Promotion Workflow",
    "Verification / Acceptance",
    "Anti-Patterns",
    "Failure Recovery / Troubleshooting",
    "Related Skills / References",
]


def test_section_ordering() -> None:
    text = _read()
    positions: list[tuple[str, int]] = []
    for needle in REQUIRED_SECTIONS:
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
# 3. `hermes todo` is NOT a real subcommand. The skill must declare that
#    `todo` is a native session tool, not a `hermes` CLI subcommand.
# ---------------------------------------------------------------------------
def test_hermes_todo_is_not_a_real_subcommand() -> None:
    text = _read()
    # The skill must state the negative.
    lower = text.lower()
    assert (
        "native session tool" in lower
        or "native `todo` tool" in lower
        or "native todo tool" in lower
    ), "skill must declare that `todo` is a native session tool, not a hermes CLI subcommand"
    # The skill must forbid invoking it.
    forbidden_invocations = [
        "hermes todo show",
        "hermes todo complete",
        "hermes todo list",
        "hermes todo add",
    ]
    # These may appear only inside anti-pattern rows; allow if surrounded by
    # an explicit "must not" / "do not" / "not a real" window.
    body = text.split("---\n", 2)[-1]
    cleaned_lines = []
    in_strip_zone = False
    for line in body.splitlines():
        if line.startswith("## "):
            in_strip_zone = "anti-pattern" in line.lower() or "failure recovery" in line.lower()
        cleaned_lines.append("" if in_strip_zone else line)
    cleaned = "\n".join(cleaned_lines)
    for inv in forbidden_invocations:
        assert inv not in cleaned, (
            f"skill must not document `{inv}` as a real invocation; "
            f"`hermes todo` is not a subcommand"
        )

    # Hermetic check: the real hermes CLI exposes no `todo` subcommand.
    parent_help = subprocess.run(
        [HERMES, "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    combined = (parent_help.stdout or "") + (parent_help.stderr or "")
    subcommands = re.search(r"\{([^}]+)\}", combined)
    assert subcommands, "could not parse `hermes --help` subcommand list"
    listed = subcommands.group(1)
    for tok in ("todo",):
        assert not re.search(rf"(?:^|\s|,){re.escape(tok)}(?:$|\s|,)", listed), (
            f"`hermes --help` must not expose `{tok}` as a subcommand; "
            f"`todo` is a native session tool, not a hermes CLI subcommand"
        )
    print("OK `hermes todo` is documented as not a real subcommand")


# ---------------------------------------------------------------------------
# 4. The real `hermes kanban create --help` exposes --idempotency-key
#    (the documented idempotency mechanism) and DOES NOT advertise
#    --comments / --cleanup (both are invented).
# ---------------------------------------------------------------------------
def test_real_kanban_create_flags() -> None:
    help_out = subprocess.run(
        [HERMES, "kanban", "create", "--help"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    # Idempotency key — the documented crash-safe retry mechanism.
    assert "--idempotency-key" in help_out, (
        "real `hermes kanban create --help` must advertise --idempotency-key"
    )
    # Forbidden: --comments / --cleanup flags do not exist on create.
    assert "--comments" not in help_out, (
        "`hermes kanban create --help` must not advertise --comments"
    )
    assert "--cleanup" not in help_out, (
        "`hermes kanban create --help` must not advertise --cleanup"
    )
    print("OK real `hermes kanban create` flags agree with SKILL.md")


# ---------------------------------------------------------------------------
# 5. The skill documents the real `hermes kanban --board SLUG create ...`
#    invocation, not invented subcommands.
# ---------------------------------------------------------------------------
def test_documents_real_kanban_create_invocation() -> None:
    text = _read()
    # The Quick Start / Promotion Workflow must use the real command.
    assert re.search(r"hermes\s+kanban\s+(?:--board\s+\S+\s+)?create\b", text), (
        "skill must document `hermes kanban [--board SLUG] create ...`"
    )
    # And must mention the idempotency-key (real flag).
    assert "--idempotency-key" in text, (
        "skill must document --idempotency-key for crash-safe retries"
    )
    # And must NOT mention invented flags like --comments / --cleanup.
    bad_flags = [
        "hermes kanban create --comments",
        "hermes kanban create --cleanup",
    ]
    body = text.split("---\n", 2)[-1]
    cleaned_lines = []
    in_strip_zone = False
    for line in body.splitlines():
        if line.startswith("## "):
            in_strip_zone = "anti-pattern" in line.lower()
        cleaned_lines.append("" if in_strip_zone else line)
    cleaned = "\n".join(cleaned_lines)
    for bad in bad_flags:
        assert bad not in cleaned, (
            f"skill must not document invented flag: {bad!r}"
        )
    print("OK documented `hermes kanban --board SLUG create` invocation")


if __name__ == "__main__":
    failures: list[str] = []
    tests = [
        test_description_one_line_under_60_chars,
        test_section_ordering,
        test_hermes_todo_is_not_a_real_subcommand,
        test_real_kanban_create_flags,
        test_documents_real_kanban_create_invocation,
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
    print(f"\nAll {len(tests)} todo-kanban-promotion checks passed.")
    sys.exit(0)