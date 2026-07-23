"""
Structural and CLI-safety checks for swarm-router SKILL.md.

These tests are intentionally small and self-contained — they validate
that the SKILL.md frontmatter and body stay aligned with the project's
shared acceptance rules (description length, section ordering, no
invented Hermes CLI flags, canonical verdict protocol).

Run with the project venv (no third-party deps required):
    /home/bratan/.hermes/hermes-agent/venv/bin/python \\
        tests/test_skill_structure.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL_PATH = Path(__file__).resolve().parent.parent / "SKILL.md"


def _read() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _frontmatter_and_body() -> tuple[str, str]:
    content = _read()
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not m:
        raise AssertionError("No YAML frontmatter found at top of SKILL.md")
    return m.group(1), content[m.end():]


# ---------------------------------------------------------------------------
# 1. YAML frontmatter description must be a single line, <= 60 chars.
# ---------------------------------------------------------------------------
def test_description_single_line_under_60_chars() -> None:
    fm, _ = _frontmatter_and_body()
    desc_match = re.search(
        r"^description:\s*(.+?)(?=\n[a-zA-Z]|\Z)", fm, re.MULTILINE | re.DOTALL
    )
    assert desc_match, "description key missing from frontmatter"
    desc = desc_match.group(1).strip()
    assert "\n" not in desc, "description must not span multiple lines"
    assert not desc.startswith("|") and not desc.startswith(
        ">"
    ), "description must not be a YAML block scalar"
    assert len(desc) <= 60, f"description is {len(desc)} chars, must be <= 60"
    assert len(desc) > 10, "description is suspiciously short"
    assert desc.startswith("Routes "), (
        "description must use the grammatical `Routes...` form"
    )


# ---------------------------------------------------------------------------
# 2. Section ordering follows the shared template.
# ---------------------------------------------------------------------------
REQUIRED_SECTIONS_IN_ORDER = [
    "When to Use",
    "Quick Start",
    "Routing Modes",
    "Decision Matrix",
    "Cost Gate",
    "Anti-Patterns Absorbed",
    "Slash Command",
    "Router Anti-Patterns",
    "Worked Examples",
    "Verification / Acceptance",
    "Failure Recovery / Troubleshooting",
    "Related Skills and References",
]


def test_section_ordering() -> None:
    _, body = _frontmatter_and_body()
    positions: list[tuple[str, int]] = []
    for needle in REQUIRED_SECTIONS_IN_ORDER:
        # Match the heading line regardless of surrounding backticks/spaces.
        pattern = re.compile(rf"^## [^\n]*{re.escape(needle)}[^\n]*$", re.MULTILINE)
        m = pattern.search(body)
        assert m, f"required section heading not found: {needle!r}"
        positions.append((needle, m.start()))
    sorted_positions = sorted(positions, key=lambda x: x[1])
    order = [p[0] for p in positions]
    sorted_order = [p[0] for p in sorted_positions]
    assert order == sorted_order, (
        f"section order mismatch.\n  got:      {order}\n  expected: {sorted_order}"
    )


# ---------------------------------------------------------------------------
# 3. Only real Hermes CLI flags and subcommands are documented.
#    Fragile CLI references inside anti-pattern tables (where the skill
#    explicitly forbids the syntax) are excluded from this check.
# ---------------------------------------------------------------------------
INVENTED_OR_FORBIDDEN_TOKENS = [
    # forged moa invocation
    "moa run --preset",
    # fake front-door claim
    "/swarm <free-form intent>",
    # legacy / non-existent kanban flags
    "kanban show --comments",
    "kanban complete --cleanup",
    # non-existent hermes todo command
    "hermes todo show",
    "hermes todo complete",
    # fake policy command
    "apply-policy",
]


def test_no_invented_hermes_flags() -> None:
    content = _read()
    # Identify anti-pattern tables so the test ignores "do not use X"
    # entries that explicitly list forbidden syntax.
    body = content.split("---\n", 2)[-1]
    # Strip lines that live inside any "## " anti-pattern or troubleshooting
    # table by replacing them with blanks. We keep the tables because the
    # policy is: anti-pattern rows are allowed to reference forbidden tokens.
    cleaned_lines = []
    in_strip_zone = False
    for line in body.splitlines():
        if line.startswith("## "):
            heading = line.lower()
            in_strip_zone = (
                "anti-pattern" in heading
                or "troubleshooting" in heading
                or "failure recovery" in heading
            )
        cleaned_lines.append("" if in_strip_zone else line)
    cleaned = "\n".join(cleaned_lines)

    for token in INVENTED_OR_FORBIDDEN_TOKENS:
        assert token not in cleaned, (
            f"forbidden / invented Hermes syntax still present: {token!r}"
        )


# ---------------------------------------------------------------------------
# 4. "All 18 absorbed" overclaim is removed.
# ---------------------------------------------------------------------------
def test_no_all_18_absorbed_overclaim() -> None:
    content = _read().lower()
    assert "all 18 absorbed" not in content, (
        "must not claim 'all 18 absorbed'; the router only absorbs the "
        "routing-relevant subset of delegation-anti-patterns"
    )


# ---------------------------------------------------------------------------
# 5. Workspace behavior matches the native swarm CLI contract.
# ---------------------------------------------------------------------------
def test_workspace_claim_matches_native_swarm_contract() -> None:
    content = _read()
    assert "Native `hermes kanban swarm` uses scratch/runtime defaults" in content
    assert "it exposes no `--workspace` option" in content
    assert (
        "project/task workspace configuration outside the `kanban swarm` flags"
        in content
    )
    assert "the router does not create it automatically" in content
    assert "workspace isolation is not a swarm flag or an" in content
    assert "automatic router effect" in content
    assert "forces `--workspace worktree`" not in content
    assert "worktree isolation (one worktree per parallel card)" not in content.lower()


# ---------------------------------------------------------------------------
# 6. /swarm front-door reflects actual on|off|status semantics.
# ---------------------------------------------------------------------------
def test_swarm_front_door_real_semantics() -> None:
    content = _read()
    # The new wording must declare the on/off/status gate.
    assert "/swarm on" in content, "front-door on-state missing"
    assert "/swarm off" in content, "front-door off-state missing"
    assert "/swarm status" in content, "front-door status missing"
    # And must NOT claim free-form intent dispatch via /swarm.
    assert "/swarm <intent>" not in content
    assert "/swarm <free-form intent>" not in content


# ---------------------------------------------------------------------------
# 7. MoA-consensus route uses the real /moa invocation.
# ---------------------------------------------------------------------------
def test_moa_route_uses_real_invocation() -> None:
    content = _read()
    # Outside anti-pattern context, the documented MoA route must use /moa.
    assert "/moa <prompt>" in content, "/moa <prompt> invocation missing"
    assert "hermes moa configure" in content, (
        "must point operators at `hermes moa configure` for slot setup"
    )


# ---------------------------------------------------------------------------
# 8. Verdict protocol stays canonical.
# ---------------------------------------------------------------------------
def test_verdict_protocol_canonical() -> None:
    content = _read()
    for invented in ["SPEC_OK", "QUALITY_OK", "APPROVED", "LOOP_OK"]:
        assert f"VERDICT: {invented}" not in content, (
            f"non-canonical verdict token leaked into SKILL.md: VERDICT: {invented}"
        )
    # Canonical verdicts are tolerated in plain text (not asserted because
    # this skill does not own a gate of its own).


# ---------------------------------------------------------------------------
# 9. SKILL.md does NOT claim `kanban swarm` forces `--workspace worktree`.
#    Native Swarm CLI uses scratch/runtime defaults; worktree isolation
#    needs project/task workspace configuration outside the swarm flags.
# ---------------------------------------------------------------------------
def test_no_swarm_workspace_worktree_claim() -> None:
    content = _read()
    lower = content.lower()
    # The forbidden phrasing would imply the swarm CLI forces worktree
    # workspace kind via a flag. The real CLI has no --workspace flag at
    # all (pinned in test_cli_safety.py).
    forbidden_phrases = [
        "kanban swarm --workspace",
        "swarm --workspace worktree",
        "kanban swarm --workspace worktree",
        "hermes kanban swarm --workspace",
        "swarm ... --workspace worktree",
    ]
    for phrase in forbidden_phrases:
        assert phrase.lower() not in lower, (
            f"SKILL.md falsely claims swarm forces --workspace; remove: {phrase!r}"
        )
    # And the corrected wording must be present: native swarm CLI uses
    # scratch/runtime defaults; worktree isolation is project/task level.
    assert "scratch/runtime defaults" in lower or "runtime defaults" in lower, (
        "must document that native swarm CLI uses scratch/runtime defaults"
    )
    assert "outside" in lower and "kanban swarm" in lower, (
        "must document that worktree isolation is configured outside the "
        "kanban swarm flags"
    )


def main() -> int:
    failures: list[str] = []
    tests = [
        test_description_single_line_under_60_chars,
        test_section_ordering,
        test_no_invented_hermes_flags,
        test_no_all_18_absorbed_overclaim,
        test_workspace_claim_matches_native_swarm_contract,
        test_swarm_front_door_real_semantics,
        test_moa_route_uses_real_invocation,
        test_verdict_protocol_canonical,
        test_no_swarm_workspace_worktree_claim,
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
    print("\nAll structural checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
