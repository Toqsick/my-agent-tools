"""Hermetic structural tests for the code-review-checklist skill.

These tests pin the frontmatter, section order, canonical verdict values,
and the real `hermes kanban comment` CLI usage. They reject invented
tokens or flags that don't exist in `hermes kanban comment --help`.
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

import yaml

SKILL_PATH = Path(__file__).resolve().parent.parent / "SKILL.md"
MAX_DESCRIPTION_LEN = 60
EXPECTED_VERDICT_VALUES = {"APPROVE", "REQUEST_CHANGES"}
REQUIRED_SECTIONS = [
    "When to Use",
    "Quick Start",
    "Workflow",
    "Verification and Acceptance",
    "Anti-Patterns",
    "Failure Recovery",
    "Related Skills and References",
]


def _read_skill() -> tuple[dict, str]:
    text = SKILL_PATH.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise AssertionError("SKILL.md missing YAML frontmatter delimiters")
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2]
    if not isinstance(meta, dict):
        raise AssertionError("SKILL.md frontmatter is not a mapping")
    return meta, body


class FrontmatterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.meta, _ = _read_skill()

    def test_description_within_sixty_chars(self) -> None:
        desc = self.meta.get("description")
        self.assertIsInstance(desc, str, "description must be a string")
        self.assertLessEqual(
            len(desc),
            MAX_DESCRIPTION_LEN,
            f"description length {len(desc)} > {MAX_DESCRIPTION_LEN}: {desc!r}",
        )

    def test_name_matches_skill_slug(self) -> None:
        self.assertEqual(self.meta.get("name"), "code-review-checklist")


class SectionOrderTests(unittest.TestCase):
    def setUp(self) -> None:
        _, self.body = _read_skill()
        # Track first occurrence of each H2 heading.
        self.positions: list[tuple[int, str]] = []
        for match in re.finditer(r"^## (.+?)\s*$", self.body, re.MULTILINE):
            self.positions.append((match.start(), match.group(1).strip()))

    def test_required_sections_present(self) -> None:
        present = {name for _, name in self.positions}
        for required in REQUIRED_SECTIONS:
            self.assertIn(required, present, f"missing section: {required!r}")

    def test_sections_appear_in_canonical_order(self) -> None:
        order = [name for _, name in self.positions]
        # Filter to required sections and confirm relative ordering.
        indices = [order.index(s) for s in REQUIRED_SECTIONS]
        self.assertEqual(
            indices,
            sorted(indices),
            f"sections out of order: {order}",
        )


class VerdictTests(unittest.TestCase):
    def setUp(self) -> None:
        _, self.body = _read_skill()

    def test_only_canonical_verdict_values_present(self) -> None:
        # Capture the value following every `VERDICT:` token on its own line.
        verdict_lines = re.findall(
            r"^[ \t]*VERDICT:[ \t]*([A-Z_]+)[ \t]*$",
            self.body,
            re.MULTILINE,
        )
        for value in verdict_lines:
            self.assertIn(
                value,
                EXPECTED_VERDICT_VALUES,
                f"non-canonical verdict value: {value!r}",
            )

    def test_no_invented_verdict_tokens(self) -> None:
        # Negative guard: no "VERDICT: APPROVED", "VERDICT: REJECT", etc.
        bad_tokens = re.findall(
            r"VERDICT:\s*([A-Za-z_]+)",
            self.body,
        )
        for token in bad_tokens:
            self.assertIn(
                token,
                EXPECTED_VERDICT_VALUES,
                f"invented verdict token: {token!r}",
            )


class CliUsageTests(unittest.TestCase):
    """Pin the real `hermes kanban comment` CLI."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.help_text = subprocess.run(
            ["hermes", "kanban", "comment", "--help"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout

    def test_real_subcommand_is_present(self) -> None:
        self.assertIn("task_id", self.help_text)
        self.assertIn("text", self.help_text)

    def test_skill_references_kanban_comment_subcommand(self) -> None:
        _, body = _read_skill()
        self.assertRegex(
            body,
            r"hermes\s+kanban\s+comment\b",
            "skill must reference `hermes kanban comment`",
        )

    def test_no_invented_flags(self) -> None:
        """Reject tokens that don't exist in `hermes kanban comment --help`."""
        _, body = _read_skill()
        # Allowed flags come straight from `hermes kanban comment --help`.
        allowed_flags = {"--author", "--max-len", "--help"}
        offending: list[str] = []
        for line in body.splitlines():
            if "kanban comment" not in line:
                continue
            for token in re.findall(r"--[a-z][a-z0-9-]*", line):
                if token not in allowed_flags:
                    offending.append(token)
        self.assertEqual(
            offending,
            [],
            f"invented or unsupported flags in comment invocation: "
            f"{offending!r}; allowed={sorted(allowed_flags)}",
        )


if __name__ == "__main__":
    unittest.main()
