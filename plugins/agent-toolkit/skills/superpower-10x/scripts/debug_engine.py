#!/usr/bin/env python3
"""
debug_engine.py - Systematic debugging automation engine

Part of Superpower-10x framework
Features:
- Automated root cause tracing
- Pattern matching against known issues
- Hypothesis testing framework
- Fix verification pipeline
"""

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase(Enum):
    """Debugging phases."""
    ROOT_CAUSE = "root_cause"
    PATTERN_ANALYSIS = "pattern_analysis"
    HYPOTHESIS = "hypothesis"
    IMPLEMENTATION = "implementation"


class Severity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"  # Blocks progress
    HIGH = "high"          # Major impact
    MEDIUM = "medium"      # Moderate impact
    LOW = "low"            # Minor impact


@dataclass
class DebugEvidence:
    """Evidence gathered during investigation."""
    timestamp: datetime
    phase: Phase
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""  # file, command, stack trace, etc.
    tags: List[str] = field(default_factory=list)


@dataclass
class DebugIssue:
    """Represents a bug or issue being debugged."""
    title: str
    description: str
    severity: Severity
    evidence: List[DebugEvidence] = field(default_factory=list)
    current_phase: Phase = Phase.ROOT_CAUSE
    root_cause: Optional[str] = None
    hypothesis: Optional[str] = None
    fix_attempts: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def add_evidence(self, phase: Phase, description: str, data: Any = None,
                    source: str = "", tags: List[str] = None) -> None:
        """Add evidence to the issue."""
        evidence = DebugEvidence(
            timestamp=datetime.now(),
            phase=phase,
            description=description,
            data={"content": data} if data else {},
            source=source,
            tags=tags or []
        )
        self.evidence.append(evidence)


@dataclass
class FixAttempt:
    """Record of a fix attempt."""
    timestamp: datetime
    description: str
    hypothesis: str
    verification_test: str
    result: str  # "success", "failed", "partial"
    side_effects: List[str] = field(default_factory=list)
    files_changed: List[str] = field(default_factory=list)


class KnownPattern:
    """Known bug pattern for quick reference."""

    def __init__(self, name: str, symptoms: List[str], patterns: List[str],
                 fix_strategy: str, examples: List[str] = None):
        self.name = name
        self.symptoms = symptoms
        self.patterns = patterns
        self.fix_strategy = fix_strategy
        self.examples = examples or []


class DebugEngine:
    """
    Systematic debugging with automated evidence gathering.

    Implements the 4-phase debugging methodology:
    1. Root Cause Investigation
    2. Pattern Analysis
    3. Hypothesis and Testing
    4. Implementation and Verification
    """

    # Known bug patterns
    KNOWN_PATTERNS = [
        KnownPattern(
            name="race_condition",
            symptoms=["intermittent", "flaky", "timing-dependent", "random",
                     "sometimes works", "inconsistent"],
            patterns=["setTimeout", "async", "concurrent", "parallel",
                      "Promise.all", "race", "simultaneous"],
            fix_strategy="Add locking, use await, sequentialize operations, "
                        "add retry logic",
            examples=["setTimeout in production", "multiple async calls"]
        ),
        KnownPattern(
            name="memory_leak",
            symptoms=["growing", "heap", "out of memory", "increasing",
                     "memory usage", "leak"],
            patterns=["addEventListener", "global", "cache", "closure",
                      "setInterval", "subscribing"],
            fix_strategy="Clean up listeners, use weak references, implement "
                        "cleanup functions, remove subscriptions",
            examples=["event listeners not removed", "global variables accumulating"]
        ),
        KnownPattern(
            name="null_undefined",
            symptoms=["cannot read", "undefined", "null", "not a function",
                     "is not defined", "undefined property"],
            patterns=["undefined", "null", "optional chaining missing",
                      "destructuring", "async await"],
            fix_strategy="Add null checks, use optional chaining (?.)",
            fix_strategy="Add null checks, use optional chaining (?.)",
            examples=["object.property", "array[0]", "function()"]
        ),
        KnownPattern(
            name="circular_dependency",
            symptoms=["cannot import", "cyclic", "circular", "stack overflow",
                     "Maximum call stack"],
            patterns=["import", "require", "from", "export"],
            fix_strategy="Reorganize imports, use dependency injection, "
                        "move shared code to separate module",
            examples=["A imports B imports A", "mutual dependencies"]
        ),
        KnownPattern(
            name="stale_state",
            symptoms=["old value", "previous", "not updating", "stale",
                     "outdated", "reflects changes"],
            patterns=["setState", "state", "this.state", "useState"],
            fix_strategy="Use functional updates, ensure proper state immutability, "
                        "check React batching behavior",
            examples=["setState called multiple times", "state not updating"]
        )
    ]

    def __init__(self):
        self.issues: List[DebugIssue] = []
        self.current_issue: Optional[DebugIssue] = None
        self.working_directory: str = "."

    def create_issue(self, title: str, description: str, severity: Severity) -> DebugIssue:
        """Create a new debug issue."""
        issue = DebugIssue(title=title, description=description, severity=severity)
        self.issues.append(issue)
        self.current_issue = issue
        logger.info(f"Created issue: {title} (severity: {severity.value})")
        return issue

    def set_working_directory(self, path: str) -> None:
        """Set the working directory for commands."""
        self.working_directory = path

    def add_evidence(self, phase: Phase, description: str, data: Any = None,
                    source: str = "", tags: List[str] = None) -> None:
        """Add evidence to current issue."""
        if not self.current_issue:
            raise ValueError("No current issue set - create an issue first")

        self.current_issue.add_evidence(phase, description, data, source, tags)

        logger.info(f"Added evidence ({phase.value}): {description}")

    def gather_error_context(self, error_output: str) -> Dict[str, Any]:
        """Parse error output and extract key information."""
        context = {
            "error_type": None,
            "message": None,
            "file": None,
            "line": None,
            "column": None,
            "function": None,
            "stack_trace": [],
            "hints": []
        }

        # Extract error type and message
        error_match = re.search(r"(\w+Error|Exception|Error): (.+)", error_output)
        if error_match:
            context["error_type"] = error_match.group(1)
            context["message"] = error_match.group(2)

        # Extract file and line (multiple formats)
        patterns = [
            r"at\s+(.+?)\s+\((.+?):(\d+):(\d+)\)",  # at func (file:line:col)
            r"at\s+(.+?):(\d+):(\d+)",              # at file:line:col
            r"(.+?):(\d+):(\d+)",                  # file:line:col
            r"line\s+(\d+)",                         # line N
        ]

        for pattern in patterns:
            match = re.search(pattern, error_output)
            if match:
                groups = match.groups()
                if len(groups) == 4:
                    context["function"] = groups[0]
                    context["file"] = groups[1]
                    context["line"] = int(groups[2])
                    context["column"] = int(groups[3])
                elif len(groups) == 3:
                    context["file"] = groups[0]
                    context["line"] = int(groups[1])
                    context["column"] = int(groups[2])
                break

        # Extract stack trace
        stack_matches = re.findall(
            r"at\s+(.+?)\s+\((.+?):(\d+):(\d+)\)",
            error_output
        )
        context["stack_trace"] = [
            {
                "function": m[0],
                "file": m[1],
                "line": int(m[2]),
                "column": int(m[3])
            }
            for m in stack_matches
        ]

        # Generate hints based on error type
        error_lower = error_output.lower()
        if "undefined" in error_lower or "null" in error_lower:
            context["hints"].append("Check for null/undefined before accessing properties")
        if "async" in error_lower or "await" in error_lower:
            context["hints"].append("Verify async/await is properly handled")
        if "permission" in error_lower or "access" in error_lower:
            context["hints"].append("Check file/directory permissions")
        if "timeout" in error_lower or "timed out" in error_lower:
            context["hints"].append("Consider increasing timeout or checking network")

        return context

    def detect_pattern(self, evidence: str) -> Optional[Dict[str, Any]]:
        """Detect known bug patterns in evidence."""
        evidence_lower = evidence.lower()

        for pattern in self.KNOWN_PATTERNS:
            # Check if any symptom keywords match
            symptom_matches = [
                symptom for symptom in pattern.symptoms
                if symptom.lower() in evidence_lower
            ]

            pattern_matches = [
                p for p in pattern.patterns
                if re.search(rf"\b{re.escape(p)}\b", evidence_lower)
            ]

            if len(symptom_matches) >= 2 or len(pattern_matches) >= 2:
                return {
                    "pattern": pattern.name,
                    "confidence": min(1.0, (len(symptom_matches) + len(pattern_matches)) /
                                    (len(pattern.symptoms) + len(pattern.patterns)) * 2),
                    "suggestion": pattern.fix_strategy,
                    "matched_symptoms": symptom_matches,
                    "matched_patterns": pattern_matches,
                    "examples": pattern.examples
                }

        return None

    def run_command(self, command: str, timeout: int = 60) -> Tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.working_directory
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", str(e)

    def run_test_isolated(self, test_command: str) -> Tuple[bool, str]:
        """Run a test command and return success status and output."""
        exit_code, stdout, stderr = self.run_command(test_command)
        return exit_code == 0, stdout + stderr

    def check_recent_changes(self, count: int = 10) -> List[Dict[str, str]]:
        """Check recent git changes that might have introduced the bug."""
        exit_code, stdout, _ = self.run_command(
            f"git log --oneline -{count} --no-walk"
        )

        if exit_code != 0:
            logger.warning("Could not get git history")
            return []

        return [
            {"commit": line.split()[0], "message": " ".join(line.split()[1:])}
            for line in stdout.strip().split("\n")
            if line.strip()
        ]

    def analyze_data_flow(self, error_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Trace data flow to find where bad values originate."""
        if not error_context.get("stack_trace"):
            return []

        trace_points = []
        for frame in error_context["stack_trace"]:
            trace_points.append({
                "file": frame.get("file"),
                "function": frame.get("function"),
                "line": frame.get("line"),
                "analysis": "needs_review"
            })

        return trace_points

    def form_hypothesis(self, root_cause: str, evidence: List[DebugEvidence]) -> str:
        """Form a hypothesis based on root cause and evidence."""
        hypothesis = f"Root cause: {root_cause}\n\nEvidence:\n"

        for e in evidence:
            hypothesis += f"- [{e.phase.value}] {e.description}"
            if e.source:
                hypothesis += f" (source: {e.source})"
            hypothesis += "\n"

        hypothesis += "\nThis hypothesis explains the observed behavior because..."

        return hypothesis

    def create_failing_test(self, test_code: str, test_name: str) -> bool:
        """Create a failing test case for the bug."""
        # Ensure test directory exists
        test_dir = "tests/debug"
        subprocess.run(f"mkdir -p {test_dir}", shell=True)

        test_file = f"{test_dir}/bug_{test_name.replace(' ', '_').replace('/', '_')}.test.py"

        with open(test_file, 'w') as f:
            f.write(test_code)

        logger.info(f"Created test file: {test_file}")

        # Verify test fails
        success, output = self.run_test_isolated(f"pytest {test_file} -v")

        if success:
            logger.warning("Test passed - it doesn't reproduce the bug")
            return False

        return True

    def apply_fix(self, fix_code: str, file_path: str, dry_run: bool = False) -> bool:
        """Apply a fix to the codebase."""
        if dry_run:
            logger.info(f"[DRY RUN] Would apply fix to: {file_path}")
            return True

        try:
            with open(file_path, 'r') as f:
                existing_content = f.read()

            with open(file_path, 'w') as f:
                f.write(existing_content)
                f.write(f"\n# Fix applied: {datetime.now()}\n")
                f.write(fix_code)

            logger.info(f"Applied fix to: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")
            return False

    def verify_fix(self, verification_command: str) -> bool:
        """Verify the fix works."""
        success, output = self.run_test_isolated(verification_command)

        if success:
            logger.info("Fix verified - test passes")
        else:
            logger.error("Fix failed - test still failing")
            logger.debug(f"Output: {output}")

        return success

    def record_fix_attempt(self, description: str, hypothesis: str,
                          verification_test: str, result: str,
                          side_effects: List[str] = None,
                          files_changed: List[str] = None) -> None:
        """Record a fix attempt for analysis."""
        if not self.current_issue:
            return

        attempt = FixAttempt(
            timestamp=datetime.now(),
            description=description,
            hypothesis=hypothesis,
            verification_test=verification_test,
            result=result,
            side_effects=side_effects or [],
            files_changed=files_changed or []
        )

        self.current_issue.fix_attempts.append(attempt.__dict__)

        logger.info(f"Recorded fix attempt: {result}")

    def generate_report(self) -> str:
        """Generate a debugging report."""
        if not self.current_issue:
            return "No issues debugged"

        issue = self.current_issue

        report = f"""
================================================================================
DEBUGGING REPORT
================================================================================

Issue: {issue.title}
Severity: {issue.severity.value}
Created: {issue.created_at}
Current Phase: {issue.current_phase.value}

--------------------------------------------------------------------------------
DESCRIPTION
--------------------------------------------------------------------------------
{issue.description}

--------------------------------------------------------------------------------
EVIDENCE GATHERED
--------------------------------------------------------------------------------
"""

        for phase in Phase:
            phase_evidence = [e for e in issue.evidence if e.phase == phase]
            if phase_evidence:
                report += f"\n### {phase.value.replace('_', ' ').title()}\n"
                for e in phase_evidence:
                    report += f"- [{e.timestamp}] {e.description}\n"
                    if e.source:
                        report += f"  Source: {e.source}\n"
                    if e.tags:
                        report += f"  Tags: {', '.join(e.tags)}\n"

        if issue.root_cause:
            report += f"""
--------------------------------------------------------------------------------
ROOT CAUSE
--------------------------------------------------------------------------------
{issue.root_cause}

"""

        if issue.hypothesis:
            report += f"""
--------------------------------------------------------------------------------
HYPOTHESIS
--------------------------------------------------------------------------------
{issue.hypothesis}

"""

        if issue.fix_attempts:
            report += """
--------------------------------------------------------------------------------
FIX ATTEMPTS
--------------------------------------------------------------------------------
"""
            for i, attempt in enumerate(issue.fix_attempts, 1):
                report += f"""
### Attempt {i}
- Time: {attempt['timestamp']}
- Description: {attempt['description']}
- Hypothesis: {attempt['hypothesis']}
- Result: {attempt['result']}
"""
                if attempt.get('side_effects'):
                    report += f"- Side Effects: {', '.join(attempt['side_effects'])}\n"
                if attempt.get('files_changed'):
                    report += f"- Files Changed: {', '.join(attempt['files_changed'])}\n"

        report += """
================================================================================
"""

        return report

    def export_report(self, output_file: str) -> None:
        """Export report to JSON file."""
        if not self.current_issue:
            logger.warning("No issue to export")
            return

        data = {
            "issue": {
                "title": self.current_issue.title,
                "description": self.current_issue.description,
                "severity": self.current_issue.severity.value,
                "root_cause": self.current_issue.root_cause,
                "hypothesis": self.current_issue.hypothesis,
                "fix_attempts": self.current_issue.fix_attempts
            },
            "evidence": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "phase": e.phase.value,
                    "description": e.description,
                    "source": e.source,
                    "tags": e.tags
                }
                for e in self.current_issue.evidence
            ]
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Report exported to: {output_file}")


def interactive_debug():
    """Interactive debugging session."""
    engine = DebugEngine()

    print("\n" + "="*60)
    print("SUPERPOWER-10X DEBUGGING ENGINE")
    print("="*60 + "\n")

    # Get issue info
    title = input("Issue title: ").strip()
    if not title:
        print("Title required")
        return

    description = input("Issue description: ").strip()
    if not description:
        print("Description required")
        return

    severity_input = input("Severity [critical/high/medium/low]: ").strip().lower()
    severity_map = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW
    }
    severity = severity_map.get(severity_input, Severity.MEDIUM)

    # Create issue
    issue = engine.create_issue(title, description, severity)

    # Gather error info
    error_input = input("\nPaste error output (or press Enter to skip): ").strip()
    if error_input:
        engine.add_evidence(
            Phase.ROOT_CAUSE,
            "Error output received",
            error_input,
            "user_input",
            ["error"]
        )

        # Analyze error
        context = engine.gather_error_context(error_input)
        print(f"\nError Analysis:")
        print(f"  Type: {context.get('error_type', 'Unknown')}")
        print(f"  Message: {context.get('message', 'Unknown')}")
        if context.get('file'):
            print(f"  Location: {context['file']}:{context['line']}")

        # Check for patterns
        pattern = engine.detect_pattern(error_input)
        if pattern:
            print(f"\n⚠️  Detected pattern: {pattern['pattern']}")
            print(f"   Suggestion: {pattern['suggestion']}")

    # Root cause
    root_cause = input("\nIdentified root cause (or Enter to continue): ").strip()
    if root_cause:
        issue.root_cause = root_cause
        issue.current_phase = Phase.PATTERN_ANALYSIS

        # Form hypothesis
        hypothesis = engine.form_hypothesis(root_cause, issue.evidence)
        print("\nGenerated Hypothesis:")
        print(hypothesis)

        issue.hypothesis = hypothesis
        issue.current_phase = Phase.HYPOTHESIS

    # Generate report
    print("\n" + engine.generate_report())

    # Export option
    export = input("\nExport report to JSON? [y/N]: ").strip().lower()
    if export == 'y':
        filename = input("Filename [debug_report.json]: ").strip() or "debug_report.json"
        engine.export_report(filename)
        print(f"Report exported to: {filename}")


def main():
    """CLI interface for the debug engine."""
    import argparse

    parser = argparse.ArgumentParser(description="Systematic Debugging Engine")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Run interactive debugging session")
    parser.add_argument("--title", help="Issue title")
    parser.add_argument("--error", help="Error output file")
    parser.add_argument("--output", "-o", help="Output report file")
    parser.add_argument("--working-dir", "-w", default=".",
                       help="Working directory")

    args = parser.parse_args()

    engine = DebugEngine()
    engine.set_working_directory(args.working_dir)

    if args.interactive:
        interactive_debug()
    elif args.title:
        # Simple single-issue mode
        issue = engine.create_issue(args.title, "", Severity.MEDIUM)

        if args.error:
            with open(args.error, 'r') as f:
                error_content = f.read()

            engine.add_evidence(
                Phase.ROOT_CAUSE,
                "Error from file",
                error_content,
                args.error,
                ["error"]
            )

            context = engine.gather_error_context(error_content)
            print(f"Error Type: {context.get('error_type', 'Unknown')}")
            print(f"Message: {context.get('message', 'Unknown')}")

            pattern = engine.detect_pattern(error_content)
            if pattern:
                print(f"\nDetected Pattern: {pattern['pattern']}")
                print(f"Suggestion: {pattern['suggestion']}")

        if args.output:
            engine.export_report(args.output)
        else:
            print(engine.generate_report())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
