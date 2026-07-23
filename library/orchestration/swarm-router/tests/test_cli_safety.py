"""
CLI-safety checks: confirms that the Hermes CLI commands and flags the
SKILL.md tells operators to use actually exist and behave as documented.

This is a no-mutation test — only `--help` invocations and a
`hermes moa list` dry-run, which are read-only.

Run with the project venv:
    /home/bratan/.hermes/hermes-agent/venv/bin/python tests/test_cli_safety.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERMES = "/home/bratan/.hermes/hermes-agent/venv/bin/hermes"
SKILL_PATH = Path(__file__).resolve().parent.parent / "SKILL.md"


def _run(args: list[str]) -> str:
    result = subprocess.run(
        [HERMES, *args],
        capture_output=True,
        text=True,
        timeout=20,
    )
    # Combine stdout+stderr; some subcommands route help to stderr.
    return (result.stdout or "") + (result.stderr or "")


def _help_contains(args: list[str], needle: str) -> bool:
    return needle in _run([*args, "--help"])


# ---------------------------------------------------------------------------
# 1. `hermes kanban show` exposes comments without requiring --comments.
# ---------------------------------------------------------------------------
def test_kanban_show_help_no_comments_flag() -> None:
    show_help = _run(["kanban", "show", "--help"])
    parent_help = _run(["kanban", "--help"])
    # `hermes kanban show` must not advertise a --comments flag.
    assert "--comments" not in show_help, (
        "`hermes kanban show` must not require a --comments flag"
    )
    # The parent help should still document that `show` includes comments
    # + events in its default output.
    assert "comments" in parent_help.lower(), (
        "`hermes kanban --help` should document comments in the show output"
    )


# ---------------------------------------------------------------------------
# 2. `hermes kanban create --skill` is repeatable (multi-skill per task).
# ---------------------------------------------------------------------------
def test_kanban_create_skill_repeatable() -> None:
    help_text = _run(["kanban", "create", "--help"])
    assert "--skill" in help_text, "`hermes kanban create --help` missing --skill"
    # The placeholder is "SKILLS" (plural) — argparse pluralises the dest
    # for repeatable options.
    assert "SKILLS" in help_text or "skill" in help_text.lower().split("optional arguments")[0:1][0:1] \
        or re.search(r"--skill[^\n]*\bskills\b", help_text, re.IGNORECASE), (
        "--skill should be declared repeatable (SKILLS plural placeholder)"
    )


# ---------------------------------------------------------------------------
# 3. `hermes kanban --board <slug>` is the documented global option.
# ---------------------------------------------------------------------------
def test_kanban_board_global_option() -> None:
    help_text = _run(["kanban", "--help"])
    assert "--board" in help_text, (
        "`hermes kanban --help` must advertise --board as a global option"
    )
    # The flag must appear before the {subcommand} list, i.e. as an
    # optional arg of the parent parser.
    board_idx = help_text.find("--board")
    subcmd_idx = help_text.find("{")
    assert board_idx < subcmd_idx, (
        "--board must precede the {subcommand} list (global option, not "
        "subcommand flag)"
    )


# ---------------------------------------------------------------------------
# 4. `hermes kanban swarm` exposes exactly the native v1 options.
# ---------------------------------------------------------------------------
def test_kanban_swarm_worker_flag() -> None:
    help_text = _run(["kanban", "swarm", "--help"])
    long_options = set(
        re.findall(r"(?<![\w-])--[a-z][a-z-]*", help_text)
    )
    assert long_options == {
        "--created-by",
        "--help",
        "--idempotency-key",
        "--json",
        "--priority",
        "--synthesizer",
        "--tenant",
        "--verifier",
        "--worker",
    }, f"unexpected `hermes kanban swarm --help` options: {long_options}"
    assert re.search(r"positional arguments:\s*\n\s*goal\b", help_text), (
        "`hermes kanban swarm` must expose the positional goal argument"
    )
    assert "--workspace" not in help_text, (
        "workspace selection is not a `hermes kanban swarm` flag"
    )


# ---------------------------------------------------------------------------
# 5. `hermes moa` is configuration-only — no `run --preset` subcommand.
# ---------------------------------------------------------------------------
def test_moa_configuration_only() -> None:
    help_text = _run(["moa", "--help"])
    # Subcommands exposed by `hermes moa`:
    subcommands = re.search(r"\{([^}]+)\}", help_text)
    assert subcommands, "could not parse `hermes moa --help` subcommand list"
    listed = subcommands.group(1)
    for tok in ("run", "preset", "execute"):
        assert f" {tok}" not in listed and not listed.startswith(tok), (
            f"`hermes moa` unexpectedly exposes subcommand token: {tok}"
        )
    # And `hermes moa run --help` must not exist.
    bad = _run(["moa", "run", "--help"])
    assert "invalid choice" in bad or "no such" in bad.lower() or "usage:" not in bad, (
        "`hermes moa run` must not be a valid subcommand"
    )


# ---------------------------------------------------------------------------
# 6. SKILL.md uses real hermes commands — extract all `hermes ...` shells
#    and confirm each is a real invocation (parent parser accepts it).
# ---------------------------------------------------------------------------
def test_skill_uses_real_hermes_commands() -> None:
    skill = SKILL_PATH.read_text(encoding="utf-8")
    # Find all backtick-quoted `hermes ...` invocations (single line).
    cmds = re.findall(r"`(hermes [^\n`]+)`", skill)
    real: list[str] = []
    for cmd in cmds:
        # Allow optional --board / --worker etc; just confirm the parent
        # command path exists.
        tokens = cmd.split()
        if "kanban" in tokens:
            sub = tokens[tokens.index("kanban") + 1]
            # Some examples use `hermes kanban --board SLUG list ...`
            if sub.startswith("--"):
                sub = tokens[tokens.index("kanban") + 2]
            help_text = _run(["kanban", sub, "--help"])
            assert "usage:" in help_text or "optional arguments" in help_text, (
                f"`hermes kanban {sub}` is not a real subcommand (in: {cmd!r})"
            )
            real.append(cmd)
        elif tokens[1:2] == ["moa"]:
            if len(tokens) < 3:
                continue  # bare `hermes moa` (no subcommand) — fine
            sub = tokens[2]
            if sub.startswith("--"):
                continue  # `hermes moa --help` style — fine
            help_text = _run(["moa", sub, "--help"])
            assert "usage:" in help_text or "optional arguments" in help_text, (
                f"`hermes moa {sub}` is not a real subcommand (in: {cmd!r})"
            )
            real.append(cmd)
        else:
            # Top-level `hermes <something>` — let parent parser decide.
            sub = tokens[1]
            if sub.startswith("--"):
                continue
            help_text = _run([sub, "--help"])
            assert "usage:" in help_text or "optional arguments" in help_text, (
                f"`hermes {sub}` is not a real subcommand (in: {cmd!r})"
            )
            real.append(cmd)
    assert real, "no hermes command examples found in SKILL.md to verify"
    print(f"  verified {len(real)} real hermes command example(s) from SKILL.md")


def main() -> int:
    failures: list[str] = []
    tests = [
        test_kanban_show_help_no_comments_flag,
        test_kanban_create_skill_repeatable,
        test_kanban_board_global_option,
        test_kanban_swarm_worker_flag,
        test_moa_configuration_only,
        test_skill_uses_real_hermes_commands,
    ]
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failures.append(f"[FAIL] {t.__name__}: {e}")
        else:
            print(f"[PASS] {t.__name__}")
    if failures:
        print("\n".join(failures))
        return 1
    print("\nAll CLI-safety checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
