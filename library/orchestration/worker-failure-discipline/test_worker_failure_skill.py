"""Structural + CLI-safe checks for worker-failure-discipline SKILL.md.

Run with the repo venv:

    /home/bratan/.hermes/hermes-agent/venv/bin/python \\
        /home/bratan/.hermes/skills/orchestration/worker-failure-discipline/test_skill.py

Tests:
  - YAML `description` is a single line, max 60 characters
    (checks the parsed value, not the raw YAML source line).
  - Section order matches the modern hermes-v2 layout
    (When to Use -> Quick Start -> ... -> Anti-Patterns ->
     Failure Recovery -> Related Skills).
  - No fake kanban flags are documented (`show --comments`,
    `complete --cleanup`, comma-list `--skill a, b`).
  - The only canonical verdict strings are `VERDICT: APPROVE`
    and `VERDICT: REQUEST_CHANGES` — no `SPEC_OK` /
    `QUALITY_OK` / `LOOP_OK` / bare `APPROVED` tokens.
  - Documented `hermes kanban` subcommands actually exist
    in `hermes kanban --help` (CLI-safe).
  - The `verify_worker_output` example runs the artifact check
    BEFORE `return SUCCESS` (no unreachable code after early
    return) and guards `output_dir` with `is_dir()`.
  - SKILL.md explicitly states that hermes `complete_task` does
    NOT validate `output/result.json` — the four-point check
    stays the verifier's job (no engine-enforced runtime check).
  - SKILL.md does NOT make the false "runtime guarantee" claim
    that the dispatcher writes `result.json` on the worker's
    behalf before declaring the task done.
  - SKILL.md frames the worker-side contract as a convention /
    contract, not a runtime guarantee.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml  # PyYAML is in the repo venv
except ImportError as exc:  # pragma: no cover - guarded for environments without it
    print(f"PyYAML required for test_skill.py: {exc}", file=sys.stderr)
    sys.exit(2)

SKILL_PATH = Path(__file__).parent / "SKILL.md"
HERMES = Path("/home/bratan/.hermes/hermes-agent/venv/bin/hermes")

EXPECTED_SECTIONS_IN_ORDER = [
    "When to Use",
    "Quick Start",
    "The Rule",
    "Orchestrator-side Checks",
    "Worker-side Contract",
    "Worker-side Scaffold",
    "LaneResult Contract (Rich Worker Report)",
    "Verifier Step (H-50 Blackboard Convention)",
    "Failure Escalation",
    "Acceptance / Verification",
    "Anti-Patterns (Rejected Orchestrators)",
    "Failure Recovery",
    "Related Skills",
]


def test_yaml_description_is_one_line_under_60_chars() -> None:
    text = SKILL_PATH.read_text()
    fm_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert fm_match, "frontmatter block not found"
    frontmatter = yaml.safe_load(fm_match.group(1))
    assert isinstance(frontmatter, dict), "frontmatter must be a YAML mapping"
    assert "description" in frontmatter, "frontmatter missing `description`"
    desc = frontmatter["description"]
    assert isinstance(desc, str), "description must be a string"
    assert "\n" not in desc, f"description must be a single line, got: {desc!r}"
    assert len(desc) <= 60, (
        f"description too long ({len(desc)} chars, max 60): {desc!r}"
    )
    print(f"OK description is {len(desc)} chars: {desc!r}")


def test_section_order_matches_modern_layout() -> None:
    text = SKILL_PATH.read_text()
    found = re.findall(r"^## (.+)$", text, re.MULTILINE)
    print("sections in order:", found)
    # The expected sequence must appear as a contiguous subsequence.
    cursor = 0
    for expected in EXPECTED_SECTIONS_IN_ORDER:
        try:
            cursor = found.index(expected, cursor) + 1
        except ValueError:
            raise AssertionError(
                f"section {expected!r} not found in expected order after "
                f"index {cursor}; sections present: {found}"
            )
    print("OK section ordering matches modern layout")


def test_no_fake_kanban_flags_in_docs() -> None:
    text = SKILL_PATH.read_text()
    forbidden = [
        ("kanban show --comments", "kanban show has no --comments flag"),
        ("kanban complete --cleanup", "kanban complete has no --cleanup flag"),
        ("--skill A, --skill B", "document --skill as repeatable, not comma list"),
        ("--skill A,B", "document --skill as repeatable, not comma list"),
        ("hermes kanban show --comments", "hermes kanban show has no --comments flag"),
    ]
    for needle, why in forbidden:
        assert needle not in text, f"forbidden fragment {needle!r} present: {why}"
    print("OK no fake kanban flags documented")


def _strip_inline_code(text: str) -> str:
    """Strip `` `…` `` and ``` ```…``` ``` spans so warning prose that
    names a forbidden token inside backticks (e.g. `` "`SPEC_OK`" ``) is
    not mistaken for an actual verdict declaration."""
    no_fenced = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    no_inline = re.sub(r"`[^`]*`", "", no_fenced)
    return no_inline


def test_canonical_verdict_only() -> None:
    raw = SKILL_PATH.read_text()
    # Use the stripped text so warning prose that mentions the forbidden
    # tokens inside backticks (anti-pattern tables) is not flagged.
    text = _strip_inline_code(raw)
    forbidden_tokens = [
        "SPEC_OK",
        "QUALITY_OK",
        "LOOP_OK",
        " APPROVED ",
        " approved ",
    ]
    for tok in forbidden_tokens:
        assert tok not in text, f"fake verdict token used as declaration: {tok!r}"
    assert "VERDICT: APPROVE" in raw, "canonical VERDICT: APPROVE missing"
    assert "VERDICT: REQUEST_CHANGES" in raw, (
        "canonical VERDICT: REQUEST_CHANGES missing"
    )
    print("OK only canonical verdict strings present")


def test_hermes_kanban_subcommands_exist() -> None:
    if not HERMES.exists():
        raise AssertionError(f"hermes binary not found at {HERMES}")
    result = subprocess.run(
        [str(HERMES), "kanban", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"hermes kanban --help failed: rc={result.returncode}\n"
        f"stderr: {result.stderr}"
    )
    out = result.stdout
    for sub in ["create", "show", "comment", "archive", "diagnostics"]:
        assert re.search(rf"\b{sub}\b", out), (
            f"kanban subcommand {sub!r} not advertised in `hermes kanban --help`"
        )
    # create must advertise --skill as repeatable
    create_help = subprocess.run(
        [str(HERMES), "kanban", "create", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert create_help.returncode == 0
    assert "repeatable" in create_help.stdout.lower() or "--skill" in create_help.stdout, (
        "--skill flag not documented for `hermes kanban create`"
    )
    print("OK hermes kanban subcommands documented and real")


def test_example_artifact_check_precedes_success_return() -> None:
    text = SKILL_PATH.read_text()
    match = re.search(
        r"```python\n(.*?def verify_worker_output.*?)\n```",
        text,
        re.DOTALL,
    )
    assert match, "verify_worker_output code block not found"
    code = match.group(1)
    artifact_pos = code.find('result.get("artifacts"')
    success_pos = code.rfind("return WorkerOutcome.SUCCESS")
    assert artifact_pos > 0, "artifact loop not found in example"
    assert success_pos > 0, "return SUCCESS not found in example"
    assert artifact_pos < success_pos, (
        "artifact check appears AFTER return SUCCESS — unreachable code "
        "violates the worker-failure discipline"
    )
    print("OK artifact check precedes return SUCCESS")


def test_example_guards_missing_output_dir() -> None:
    text = SKILL_PATH.read_text()
    match = re.search(
        r"```python\n(.*?def verify_worker_output.*?)\n```",
        text,
        re.DOTALL,
    )
    code = match.group(1)
    assert "output_dir.is_dir()" in code, (
        "verify_worker_output must guard output_dir with is_dir() before "
        "iterdir() — otherwise the H-00 trap crashes the orchestrator"
    )
    print("OK example guards missing output directory")


def test_skill_documents_complete_task_does_not_validate_result_json() -> None:
    """Pin the contract: hermes `complete_task` does NOT validate
    `output/result.json`; the verifier / orchestrator must re-run the
    four-point check before accepting done."""
    text = SKILL_PATH.read_text()
    # Phrase variants the skill uses to express this.
    required_phrases = [
        "complete_task",
        "output/result.json",
    ]
    for phrase in required_phrases:
        assert phrase in text, (
            f"skill must mention {phrase!r} when documenting the engine "
            f"vs. skill split for result.json validation"
        )
    # The negation must be explicit, not implied. Search for the canonical
    # "does not validate" / "never reads" / "never inspects" claim.
    claim_patterns = [
        r"complete_task[^.\n]*\b(does not|never)\b[^.\n]*\b(validate|read|inspect)\b",
        r"\b(does not|never)\b[^.\n]*\b(validate|read|inspect)\b[^.\n]*output/result\.json",
    ]
    matches = sum(
        1 for pat in claim_patterns if re.search(pat, text, re.IGNORECASE)
    )
    assert matches >= 1, (
        "skill must explicitly state that complete_task does NOT validate / "
        "read / inspect output/result.json — the four-point check stays the "
        "verifier's responsibility"
    )
    print("OK skill pins: complete_task does not validate result.json")


def test_skill_does_not_claim_runtime_writes_result_json() -> None:
    """Pin the negative: the dispatcher / runtime does NOT write
    `result.json` on the worker's behalf. Phrases that imply an engine
    guarantee must be absent."""
    text = SKILL_PATH.read_text()
    forbidden_phrases = [
        # Old, false claim — the "runtime guarantee" framing.
        "runtime guarantee is the key",
        "the dispatcher MUST write",
        "the dispatcher writes",
        "runtime writes output/result.json",
        # The whole "MUST write ... before declaring the task done" pattern
        # implies an engine guarantee that does not exist in code.
        "before declaring the task done",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in text, (
            f"forbidden runtime-guarantee claim present: {phrase!r} — "
            f"result.json is a worker/skill contract, not something the "
            f"dispatcher or complete_task writes automatically"
        )
    print("OK skill does not claim the runtime writes result.json")


def test_skill_frames_worker_contract_as_convention_not_guarantee() -> None:
    """Pin the positive reframing: the worker-side contract is explicitly
    labelled as a contract / convention, not a runtime guarantee."""
    text = SKILL_PATH.read_text()
    patterns = [
        r"contract,\s*not a runtime guarantee",
        r"contract,\s*not a runtime",
        r"worker- and skill-level contract",
        r"skill-level obligation",
    ]
    matches = sum(1 for pat in patterns if re.search(pat, text, re.IGNORECASE))
    assert matches >= 1, (
        "skill must explicitly frame the worker-side contract as a "
        "convention / contract, not a runtime guarantee"
    )
    print("OK skill frames the worker contract as a convention")


def test_skill_does_not_claim_complete_inspects_workspace() -> None:
    """Anti-pattern check: there must be no wording that suggests
    `hermes kanban complete` opens the worker's workspace, parses
    `output/result.json`, or auto-verifies the four-point check."""
    text = SKILL_PATH.read_text()
    forbidden_patterns = [
        # Old phrasing that implied the engine enforces the check.
        r"complete_task\s+(auto[ -]?validates|auto[ -]?verifies|automatically (validates|verifies|checks))",
        r"complete_task\s+(reads|parses|inspects)\s+output/result\.json",
    ]
    for pat in forbidden_patterns:
        assert not re.search(pat, text, re.IGNORECASE), (
            f"forbidden pattern {pat!r}: skill must not claim complete_task "
            f"auto-validates or inspects output/result.json"
        )
    print("OK skill does not claim complete_task auto-validates result.json")


def test_lane_result_contract_section_exists() -> None:
    """Verify the LaneResult Contract section is present and documents
    the rich schema from state_management.md."""
    text = SKILL_PATH.read_text()
    assert "## LaneResult Contract" in text, (
        "LaneResult Contract section missing — skill must document the "
        "richer LaneResult schema from state_management.md as a template "
        "for structured worker reports"
    )
    # The six LaneResult fields must all appear in the schema example
    for field in ["lane_id", "status", "summary", "evidence",
                   "open_risks", "unverified_claims", "confidence"]:
        assert field in text, (
            f"LaneResult field {field!r} missing from SKILL.md — the "
            f"contract schema must document all seven fields"
        )
    # The extended status set must be documented
    for status_val in ["pass", "retry", "blocked", "failed"]:
        assert f'"{status_val}"' in text or f"| `{status_val}`" in text or f"status: \"{status_val}\"" in text, (
            f"LaneResult status value {status_val!r} not documented"
        )
    print("OK LaneResult Contract section with all 7 fields + 4 statuses")


def test_lane_result_evidence_check_precedes_success() -> None:
    """The verify_lane_result example must check evidence on disk
    BEFORE returning SUCCESS — same invariant as the flat contract."""
    text = SKILL_PATH.read_text()
    match = re.search(
        r"```python\n(.*?def verify_lane_result.*?)\n```",
        text,
        re.DOTALL,
    )
    assert match, "verify_lane_result code block not found"
    code = match.group(1)
    evidence_pos = code.find('result.get("evidence"')
    success_pos = code.rfind("return WorkerOutcome.SUCCESS")
    assert evidence_pos > 0, "evidence check loop not found in verify_lane_result"
    assert success_pos > 0, "return SUCCESS not found in verify_lane_result"
    assert evidence_pos < success_pos, (
        "LaneResult evidence check appears AFTER return SUCCESS — "
        "unreachable code violates the worker-failure discipline"
    )
    print("OK LaneResult evidence check precedes return SUCCESS")


def test_lane_result_field_mapping_table_exists() -> None:
    """The skill must include a mapping table showing how the flat
    contract fields map to LaneResult fields."""
    text = SKILL_PATH.read_text()
    assert "Flat" in text and "LaneResult" in text, (
        "Field mapping table between flat contract and LaneResult missing"
    )
    # artifacts → evidence mapping must be documented
    assert "evidence" in text and "artifact" in text, (
        "artifacts→evidence field mapping not documented"
    )
    print("OK LaneResult field mapping table present")


def test_lane_result_references_state_management() -> None:
    """The skill must reference state_management.md as the source of
    the LaneResult contract."""
    text = SKILL_PATH.read_text()
    assert "state_management" in text, (
        "Skill must cite state_management.md as the source of the "
        "LaneResult contract"
    )
    print("OK LaneResult references state_management.md")


def main() -> int:
    tests = [
        test_yaml_description_is_one_line_under_60_chars,
        test_section_order_matches_modern_layout,
        test_no_fake_kanban_flags_in_docs,
        test_canonical_verdict_only,
        test_hermes_kanban_subcommands_exist,
        test_example_artifact_check_precedes_success_return,
        test_example_guards_missing_output_dir,
        test_skill_documents_complete_task_does_not_validate_result_json,
        test_skill_does_not_claim_runtime_writes_result_json,
        test_skill_frames_worker_contract_as_convention_not_guarantee,
        test_skill_does_not_claim_complete_inspects_workspace,
        test_lane_result_contract_section_exists,
        test_lane_result_evidence_check_precedes_success,
        test_lane_result_field_mapping_table_exists,
        test_lane_result_references_state_management,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}", file=sys.stderr)
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {t.__name__}: {e!r}", file=sys.stderr)
            failed += 1
    if failed:
        print(f"\n{failed} test(s) failed", file=sys.stderr)
        return 1
    print(f"\nAll {len(tests)} tests passed")  # 15 tests total
    return 0


if __name__ == "__main__":
    sys.exit(main())
