#!/usr/bin/env python3
"""
finish_pipeline.py - Automated completion workflow

Part of Superpower-10x framework
Features:
- Test verification
- Branch cleanup options
- PR creation with auto-generated content
- Changelog updates
- Deployment triggers
"""

import argparse
import subprocess
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional
import sys


class FinishOption(Enum):
    """Branch completion options."""
    MERGE_LOCAL = "merge_local"
    CREATE_PR = "create_pr"
    KEEP_BRANCH = "keep_branch"
    DISCARD = "discard"


@dataclass
class FinishResult:
    """Result of a finish operation."""
    option: FinishOption
    success: bool
    message: str
    artifacts: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class FinishPipeline:
    """
    Handles branch completion workflow.

    Workflow:
    1. Verify tests pass
    2. Present completion options
    3. Execute chosen workflow
    4. Generate summary
    """

    def __init__(self, branch_name: str = None, base_branch: str = "main"):
        self.branch_name = branch_name or self._get_current_branch()
        self.base_branch = base_branch
        self.results: List[FinishResult] = []
        self.worktree_path: Optional[str] = None

    def _get_current_branch(self) -> str:
        """Get current git branch."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def _run_command(self, cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command."""
        return subprocess.run(cmd, capture_output=True, text=True, check=check)

    def verify_tests(self, test_command: str = None) -> bool:
        """Run test suite and verify all pass."""
        print("\n" + "="*50)
        print("Running Test Suite")
        print("="*50)

        # Auto-detect test command
        if not test_command:
            test_commands = [
                ["npm", "test"],
                ["pytest"],
                ["cargo", "test"],
                ["go", "test", "./..."],
                ["make", "test"]
            ]

            for cmd in test_commands:
                if self._is_command_available(cmd[0]):
                    test_command = " ".join(cmd)
                    break

        if not test_command:
            print("No test command detected - skipping test verification")
            return True

        print(f"Running: {test_command}\n")

        try:
            result = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                print("❌ Tests Failed:")
                print(result.stderr)
                print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
                return False

            print("✅ All tests passed")
            return True

        except subprocess.TimeoutExpired:
            print("❌ Tests timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False

    def _is_command_available(self, cmd: str) -> bool:
        """Check if a command is available."""
        try:
            subprocess.run(
                ["which", cmd],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def get_base_branch(self) -> str:
        """Detect the base branch."""
        for branch in ["main", "master", "develop", "develop"]:
            try:
                self._run_command(
                    ["git", "merge-base", "HEAD", branch],
                    check=True
                )
                print(f"Detected base branch: {branch}")
                self.base_branch = branch
                return branch
            except subprocess.CalledProcessError:
                continue

        return self.base_branch

    def merge_locally(self) -> FinishResult:
        """Merge branch into base locally."""
        print(f"\n{'='*50}")
        print(f"Merging {self.branch_name} into {self.base_branch}")
        print("="*50)

        try:
            # Checkout base
            print(f"Checking out {self.base_branch}...")
            self._run_command(["git", "checkout", self.base_branch])

            # Pull latest
            print("Pulling latest changes...")
            self._run_command(["git", "pull"])

            # Merge
            print(f"Merging {self.branch_name}...")
            merge_result = self._run_command(
                ["git", "merge", self.branch_name],
                check=False
            )

            if merge_result.returncode != 0:
                if "conflict" in merge_result.stderr.lower():
                    print("⚠️  Merge conflict detected")
                    print("Please resolve conflicts and commit, then run finish again")
                    return FinishResult(
                        option=FinishOption.MERGE_LOCAL,
                        success=False,
                        message="Merge conflict - manual resolution required"
                    )
                else:
                    return FinishResult(
                        option=FinishOption.MERGE_LOCAL,
                        success=False,
                        message=f"Merge failed: {merge_result.stderr}"
                    )

            # Verify tests on merged result
            if not self.verify_tests():
                return FinishResult(
                    option=FinishOption.MERGE_LOCAL,
                    success=False,
                    message="Tests failed after merge - reverting"
                )

            # Delete local branch
            print(f"Deleting local branch {self.branch_name}...")
            self._run_command(["git", "branch", "-d", self.branch_name])

            # Cleanup worktree
            self.cleanup_worktree()

            return FinishResult(
                option=FinishOption.MERGE_LOCAL,
                success=True,
                message=f"Successfully merged into {self.base_branch}",
                artifacts=["merged commits"]
            )

        except Exception as e:
            return FinishResult(
                option=FinishOption.MERGE_LOCAL,
                success=False,
                message=f"Error: {e}"
            )

    def create_pr(self, title: str = None, body: str = None) -> FinishResult:
        """Create a pull request."""
        print(f"\n{'='*50}")
        print(f"Creating PR for {self.branch_name}")
        print("="*50)

        try:
            # Check if gh is available
            if not self._is_command_available("gh"):
                return FinishResult(
                    option=FinishOption.CREATE_PR,
                    success=False,
                    message="GitHub CLI (gh) not installed"
                )

            # Push branch
            print("Pushing branch to origin...")
            self._run_command([
                "git", "push", "-u", "origin", self.branch_name
            ])

            # Get commits for description
            log_result = self._run_command(
                ["git", "log", f"{self.base_branch}..{self.branch_name}", "--oneline"],
                check=False
            )
            commits = [
                line.strip()
                for line in log_result.stdout.strip().split('\n')
                if line.strip()
            ]

            # Generate PR body
            pr_body_lines = [
                "## Summary",
                ""
            ]

            if commits:
                for commit in commits:
                    pr_body_lines.append(f"- {commit}")
            else:
                pr_body_lines.append("- No commits (WIP)")

            pr_body_lines.extend([
                "",
                "## Test Plan",
                "- [ ] All tests pass locally",
                "- [ ] Manual testing completed",
                "- [ ] Documentation updated",
                "",
                "## Verification",
                "_Built with [Superpower-10x](https://github.com/superpowers/superpower-10x)_"
            ])

            default_body = "\n".join(pr_body_lines)
            final_body = body or default_body

            # Determine title
            default_title = f"feat: {self.branch_name}"
            if title:
                pass  # Use provided title
            else:
                # Try to extract from first commit
                if commits and ":" in commits[0]:
                    parts = commits[0].split(":", 1)
                    if parts[0] in ["feat", "fix", "chore", "docs", "refactor", "test"]:
                        title = parts[1].strip()

            final_title = title or default_title

            # Create PR
            print("Creating pull request...")
            pr_result = self._run_command([
                "gh", "pr", "create",
                "--title", final_title,
                "--body", final_body,
                "--base", self.base_branch
            ], check=False)

            if pr_result.returncode != 0:
                return FinishResult(
                    option=FinishOption.CREATE_PR,
                    success=False,
                    message=f"PR creation failed: {pr_result.stderr}"
                )

            pr_url = pr_result.stdout.strip()

            return FinishResult(
                option=FinishOption.CREATE_PR,
                success=True,
                message=f"PR created successfully: {pr_url}",
                artifacts=[pr_url]
            )

        except Exception as e:
            return FinishResult(
                option=FinishOption.CREATE_PR,
                success=False,
                message=f"Error: {e}"
            )

    def keep_branch(self) -> FinishResult:
        """Keep branch for later work."""
        print(f"\n{'='*50}")
        print(f"Keeping branch {self.branch_name} for later")
        print("="*50)

        return FinishResult(
            option=FinishOption.KEEP_BRANCH,
            success=True,
            message=f"Branch {self.branch_name} preserved. Worktree kept.",
            artifacts=[f"branch: {self.branch_name}"]
        )

    def discard(self, confirm: str = None) -> FinishResult:
        """Discard all work on this branch."""
        print(f"\n{'='*50}")
        print(f"⚠️  WARNING: Discarding branch {self.branch_name}")
        print("="*50)

        # Get commits to be deleted
        log_result = self._run_command(
            ["git", "log", "--oneline", "-10"],
            check=False
        )

        commits = log_result.stdout.strip().split('\n')

        print("\nCommits that will be deleted:")
        for commit in commits[:5]:
            print(f"  - {commit}")
        if len(commits) > 5:
            print(f"  ... and {len(commits) - 5} more")

        if confirm != "discard":
            print("\n⚠️  This action cannot be undone!")
            confirm = input("Type 'discard' to confirm: ").strip()

        if confirm != "discard":
            return FinishResult(
                option=FinishOption.DISCARD,
                success=False,
                message="Discard cancelled"
            )

        try:
            # Checkout base branch
            print(f"Checking out {self.base_branch}...")
            self._run_command(["git", "checkout", self.base_branch])

            # Delete branch
            print(f"Deleting branch {self.branch_name}...")
            self._run_command(["git", "branch", "-D", self.branch_name])

            # Cleanup worktree
            self.cleanup_worktree()

            return FinishResult(
                option=FinishOption.DISCARD,
                success=True,
                message=f"Branch {self.branch_name} deleted",
                artifacts=commits
            )

        except Exception as e:
            return FinishResult(
                option=FinishOption.DISCARD,
                success=False,
                message=f"Error: {e}"
            )

    def cleanup_worktree(self) -> None:
        """Remove associated worktree."""
        if not self.worktree_path:
            # Try to find worktree
            list_result = self._run_command(
                ["git", "worktree", "list"],
                check=False
            )

            if list_result.returncode == 0:
                for line in list_result.stdout.strip().split('\n'):
                    if self.branch_name in line:
                        self.worktree_path = line.split()[0]
                        break

        if self.worktree_path:
            print(f"Removing worktree: {self.worktree_path}")
            try:
                self._run_command([
                    "git", "worktree", "remove", self.worktree_path
                ])
            except Exception as e:
                print(f"Could not remove worktree: {e}")

    def update_changelog(self) -> bool:
        """Update changelog with new changes."""
        changelog_path = Path("CHANGELOG.md")

        if not changelog_path.exists():
            return False

        try:
            with open(changelog_path, 'r') as f:
                content = f.read()

            # Find version header
            today = datetime.now().strftime("%Y-%m-%d")
            new_entry = f"\n## [{today}] - {self.branch_name}\n\n### Added\n- Implementation from {self.branch_name}\n"

            # Insert after first header
            lines = content.split('\n')
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('#'):
                    insert_idx = i + 1
                elif insert_idx > 0:
                    break

            lines.insert(insert_idx, new_entry)

            with open(changelog_path, 'w') as f:
                f.write('\n'.join(lines))

            print(f"Updated changelog: {changelog_path}")
            return True

        except Exception as e:
            print(f"Could not update changelog: {e}")
            return False

    def present_options(self) -> FinishOption:
        """Present completion options to user."""
        print("\n" + "="*50)
        print("BRANCH COMPLETION OPTIONS")
        print("="*50)
        print(f"Current branch: {self.branch_name}")
        print(f"Base branch: {self.base_branch}")
        print()

        options = [
            ("1", "Merge locally into {base}", FinishOption.MERGE_LOCAL),
            ("2", "Create Pull Request", FinishOption.CREATE_PR),
            ("3", "Keep branch for later", FinishOption.KEEP_BRANCH),
            ("4", "Discard all changes", FinishOption.DISCARD),
        ]

        for num, desc, _ in options:
            print(f"  {num}. {desc.format(base=self.base_branch)}")

        print()

        while True:
            choice = input("Select option [1-4]: ").strip()
            for num, _, option in options:
                if choice == num:
                    return option
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

    def execute(self, option: FinishOption = None, **kwargs) -> FinishResult:
        """Execute the finish workflow."""
        # Verify tests first
        if not self.verify_tests(kwargs.get("test_command")):
            print("\n❌ Cannot proceed - tests failing")
            return FinishResult(
                option=FinishOption.MERGE_LOCAL,
                success=False,
                message="Tests failing - fix before completing branch"
            )

        # Get base branch
        self.get_base_branch()

        # Present options if not specified
        if not option:
            option = self.present_options()

        # Execute selected option
        if option == FinishOption.MERGE_LOCAL:
            result = self.merge_locally()
        elif option == FinishOption.CREATE_PR:
            result = self.create_pr(
                title=kwargs.get("pr_title"),
                body=kwargs.get("pr_body")
            )
        elif option == FinishOption.KEEP_BRANCH:
            result = self.keep_branch()
        elif option == FinishOption.DISCARD:
            result = self.discard(kwargs.get("confirm"))
        else:
            result = FinishResult(
                option=option,
                success=False,
                message="Unknown option"
            )

        self.results.append(result)

        # Update changelog if successful
        if result.success and kwargs.get("update_changelog"):
            self.update_changelog()

        # Print result
        print("\n" + "="*50)
        print("RESULT")
        print("="*50)
        if result.success:
            print(f"✅ {result.message}")
        else:
            print(f"❌ {result.message}")

        if result.artifacts:
            print("\nArtifacts:")
            for artifact in result.artifacts:
                print(f"  - {artifact}")

        return result


def main():
    """CLI interface."""
    parser = argparse.ArgumentParser(description="Branch Completion Pipeline")

    parser.add_argument(
        "--branch", "-b",
        help="Branch name (default: current branch)"
    )
    parser.add_argument(
        "--base", "-B",
        default="main",
        help="Base branch (default: main)"
    )
    parser.add_argument(
        "--option", "-o",
        choices=["merge", "pr", "keep", "discard"],
        help="Completion option (default: prompt)"
    )
    parser.add_argument(
        "--test-command", "-t",
        help="Test command to run"
    )
    parser.add_argument(
        "--pr-title",
        help="Pull request title"
    )
    parser.add_argument(
        "--no-changelog",
        action="store_true",
        help="Skip changelog update"
    )
    parser.add_argument(
        "--confirm",
        help="Auto-confirm discard (use 'discard')"
    )

    args = parser.parse_args()

    # Map option string to enum
    option_map = {
        "merge": FinishOption.MERGE_LOCAL,
        "pr": FinishOption.CREATE_PR,
        "keep": FinishOption.KEEP_BRANCH,
        "discard": FinishOption.DISCARD
    }

    pipeline = FinishPipeline(
        branch_name=args.branch,
        base_branch=args.base
    )

    result = pipeline.execute(
        option=option_map.get(args.option),
        test_command=args.test_command,
        pr_title=args.pr_title,
        update_changelog=not args.no_changelog,
        confirm=args.confirm
    )

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
