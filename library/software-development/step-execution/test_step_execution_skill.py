"""Structural and CLI-safety tests for the step-execution SKILL.md.

These tests are deliberately small and rely only on the Python stdlib
plus ``pyyaml`` (already in the repo venv). They run in-process — no
network, no fixture sprawl, no test framework beyond ``unittest``.

What they check:

* The YAML frontmatter parses and ``description`` is one line of at
  most 60 characters.
* The required sections exist, in the canonical order documented in
  the swarm item instructions (When to Use → Quick Start → Workflow
  → Verification/Acceptance → Anti-Patterns → Failure Recovery →
  Related Skills).
* No real hermes kanban command documented here is fictional. We
  cross-check ``hermes kanban show --help`` to make sure the
  documented flag surface is real.
* The skill does not promise that the worker auto-commits.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

SKILL_PATH = Path(__file__).resolve().parent / "SKILL.md"
HERMES = "/home/bratan/.hermes/hermes-agent/venv/bin/hermes"


def _split_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text)."""
    assert text.startswith("---\n"), "SKILL.md must start with a YAML frontmatter"
    end = text.find("\n---", 4)
    assert end != -1, "Frontmatter must be closed by a second '---' line"
    fm_block = text[4:end]
    body = text[end + 4 :]
    fm = yaml.safe_load(fm_block)
    assert isinstance(fm, dict), "Frontmatter must parse as a mapping"
    return fm, body


def _section_headers(body: str) -> list[str]:
    """Return the ordered list of top-level (##) section headers."""
    return [line[3:].strip() for line in body.splitlines() if line.startswith("## ")]


class FrontmatterTests(unittest.TestCase):
    def test_description_is_single_line(self):
        text = SKILL_PATH.read_text(encoding="utf-8")
        fm, _ = _split_frontmatter(text)
        desc = fm.get("description")
        self.assertIsInstance(desc, str, "description must be a string")
        self.assertNotIn("\n", desc, f"description must be one line, got: {desc!r}")
        self.assertLessEqual(
            len(desc),
            60,
            f"description must be <= 60 chars, got {len(desc)}: {desc!r}",
        )

    def test_required_frontmatter_keys(self):
        text = SKILL_PATH.read_text(encoding="utf-8")
        fm, _ = _split_frontmatter(text)
        for key in ("name", "description", "version"):
            self.assertIn(key, fm, f"frontmatter missing required key: {key}")


class SectionOrderTests(unittest.TestCase):
    REQUIRED_HEADERS = [
        "When to use",
        "Quick Start",
        "The micro-loop",
        "Verification discipline",
        "Acceptance",
        "Anti-patterns (rejected executions)",
        "Failure recovery / Troubleshooting",
        "Related skills",
    ]

    def test_required_sections_present(self):
        text = SKILL_PATH.read_text(encoding="utf-8")
        _, body = _split_frontmatter(text)
        headers = _section_headers(body)
        for required in self.REQUIRED_HEADERS:
            self.assertIn(
                required,
                headers,
                f"missing required section: {required!r}; got {headers}",
            )

    def test_canonical_section_order(self):
        text = SKILL_PATH.read_text(encoding="utf-8")
        _, body = _split_frontmatter(text)
        headers = _section_headers(body)
        indices = [headers.index(h) for h in self.REQUIRED_HEADERS if h in headers]
        self.assertEqual(
            indices,
            sorted(indices),
            "sections must appear in canonical order: " + " -> ".join(self.REQUIRED_HEADERS),
        )


class CommandFidelityTests(unittest.TestCase):
    """Make sure we don't document hermes kanban flags that don't exist."""

    def test_no_documented_kanban_show_dash_dash_comments(self):
        text = SKILL_PATH.read_text(encoding="utf-8")
        self.assertNotRegex(
            text,
            r"hermes\s+kanban\s+show\s+\S+\s+--comments",
            "hermes kanban show does not accept --comments; remove the flag",
        )

    def test_hermes_kanban_show_help_confirms_no_comments_flag(self):
        """Cross-check the actual hermes CLI to make sure --comments is not real."""
        result = subprocess.run(
            [HERMES, "kanban", "show", "--help"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertNotIn(
            "--comments",
            result.stdout,
            "hermes kanban show --help must not advertise a --comments flag",
        )


class CommitDisciplineTests(unittest.TestCase):
    """The worker must not auto-commit. Hermes agents defer commits to the human."""

    def test_no_implies_auto_commit(self):
        text = SKILL_PATH.read_text(encoding="utf-8").lower()
        # Acceptable phrasings: "do not auto-commit", "no auto-commit",
        # "the human runs git commit". Reject anything that sounds like the
        # worker itself does the commit.
        forbidden = [
            r"workers?\s+auto-?commit",
            r"auto-?commit\s+(is\s+)?(done|performed|run)\s+by\s+the\s+worker",
            r"the\s+worker\s+commits",
            r"commit\s+per\s+green\s+step",  # old phrasing from earlier draft
        ]
        for pattern in forbidden:
            self.assertNotRegex(
                text,
                pattern,
                f"skill must not promise auto-commit (matched {pattern!r})",
            )

    def test_step5_documents_human_approval(self):
        text = SKILL_PATH.read_text(encoding="utf-8")
        self.assertIn("## Step 5", text)  # guard against numbering drift
        # Find the Step 5 block (between Step 5 and Step 6 markers).
        m = re.search(
            r"###\s+Step\s+5\b.*?(?=###\s+Step\s+6\b)",
            text,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "Step 5 section not found")
        block = m.group(0).lower()
        self.assertIn("human", block, "Step 5 must mention the human approval gate")


if __name__ == "__main__":
    unittest.main(verbosity=2)