#!/usr/bin/env python3
"""
greyhack-bug-scan.py — Static + build-verification scan for GreyScript repos.

Companion to the greyhack-greyscript SKILL.md "Systematic Bug-Scanning for
Non-Compiling Sources" section. Identical to the script used in the
2026-07-07 audit of ~/10-Projekte/10-active/greyhack-tools (78 files).

Usage:
    python3 greyhack-bug-scan.py --repo <path> [--build-sample N] [--out <json>]

What it does:
    1. Static scan for 14 known build-breaker / runtime-bug patterns.
    2. Optional: greybel build -dbf on top N files (default 5) to verify
       that the static findings reproduce.
    3. Writes JSON + human-readable markdown to <out>.

Exit codes:
    0  scan completed (bugs may still be present!)
    1  repo not found / greybel missing
    2  scan completed but >0 bugs found (CI-friendly)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

PATTERNS = {
    "(a) one-line-if/then/end if":  re.compile(r"\bif\b.*\bthen\b.*\bend\s+if\b"),
    "(b) ternary X if C else Y":    re.compile(r"\bif\b.*\belse\b"),
    "(c) \\n statt char(10)":        re.compile(r"\\n"),
    "(d) single-quote 'text'":       re.compile(r"'(?:[^'\\]|\\.)*'"),
    "(e) inline-if assignment":      re.compile(r"=\s*\(.*\bif\b.*\belse\b"),
}

# Patterns that need per-line special handling (print() exemption, etc.)
PATTERN_D_EXEMPT_PRINT = True  # skip (d) if inside print()-message

LIBRARY_INDICATORS = (
    "lib_core", "listlib", "util.src", "core/", "recon_lite", "tests/",
    "tests/test_", "cli_core", "libcore", "buildcore", "netcore",
    "debugcore", "filecore", "cliFeedback", "lzw/", "xmem",
    "minitest/", "examples/", "fix_perms", "attack_tiers",
    "install", "ransomeware", "scp_upload", "htop",
)

EXCLUDE_DIRS = (
    "backups/", "build/", "bin/", "imports/",
    "greybel-vs/test-workspace/", ".ci-build/", ".git/",
)


def is_library(filepath: str) -> bool:
    """True if this file is a library/test/sub-module that does NOT need //command: marker."""
    return any(ind.lower() in filepath.lower() for ind in LIBRARY_INDICATORS)


def should_skip(filepath: str) -> bool:
    """True if this file should be excluded from the scan entirely."""
    return any(d in filepath for d in EXCLUDE_DIRS)


def scan_file(filepath: str) -> dict:
    """Run all 14 patterns against a single .src file.

    Returns a dict {pattern_name: count} for the patterns that fired.
    """
    try:
        with open(filepath) as fh:
            lines = fh.readlines()
    except (OSError, IOError):
        return {}

    code_lines = [l for l in lines if not l.strip().startswith("//")]
    findings = {}

    # Patterns (a)-(e): line-by-line regex
    for pname, regex in PATTERNS.items():
        count = 0
        for line in code_lines:
            if not regex.search(line):
                continue
            # (b) special: skip `else if` and `if-then-else` (already multi-line)
            if pname == "(b) ternary X if C else Y":
                if re.search(r"\belse\s+if\b", line):
                    continue
                if re.search(r"\bif\b.*\bthen\b.*\belse\b", line):
                    continue
            # (d) special: skip user-facing print() messages
            if pname == "(d) single-quote 'text'" and PATTERN_D_EXEMPT_PRINT:
                if re.search(r"if\s+\S+\s*[!=]=\s*'", line):
                    pass  # code-comparison — flag
                elif "print(" in line or "style(" in line:
                    continue
            count += 1
        if count:
            findings[pname] = count

    # (f) backslash in string (needs char(34) workaround)
    f_count = sum(
        1 for l in code_lines if '\\"' in l and "char(34)" not in l
    )
    if f_count:
        findings["(f) \\ in string"] = f_count

    # (g) === separator line
    if any(re.match(r"^=+\s*$", l) for l in lines):
        findings["(g) === separator"] = sum(
            1 for l in lines if re.match(r"^=+\s*$", l)
        )

    # (h) [^N] negative index
    h_count = sum(1 for l in code_lines if re.search(r"\[\^-?\d+\]", l))
    if h_count:
        findings["(h) [^N] negative index"] = h_count

    # (i) .strip() / .trim()
    i_count = sum(1 for l in code_lines if re.search(r"\.(strip|trim)\b", l))
    if i_count:
        findings["(i) .strip()/.trim()"] = i_count

    # (j) str_repeat / (k) get_system_time / (l) HTTP.Request
    for label, pat in [
        ("(j) str_repeat",       r"\bstr_repeat\b"),
        ("(k) get_system_time",  r"\bget_system_time\b"),
        ("(l) HTTP.Request",     r"\bHTTP\.Request\b"),
    ]:
        c = sum(1 for l in code_lines if re.search(pat, l))
        if c:
            findings[label] = c

    # (m) recursive require_shell
    m_count = sum(
        1 for l in code_lines if re.search(r"pc\s*=\s*require_shell\s*\(", l)
    )
    if m_count > 1:
        findings["(m) require_shell recursion"] = m_count

    # (n) //command: marker
    first = lines[0].strip() if lines else ""
    if first and not first.startswith("//command:"):
        findings["(n) NO //command: marker"] = 1

    return findings


def greybel_build_sample(files: list[str], top_n: int = 5) -> dict:
    """Run greybel build -dbf on the top-N highest-finding files. Returns
    {filepath: (status, error_first_line)}."""
    greybel = (
        "greybel"
        if subprocess.run(["which", "greybel"], capture_output=True).returncode == 0
        else None
    )
    if not greybel:
        return {"_error": "greybel not installed"}

    out = {}
    for f in files[:top_n]:
        target = Path("/tmp/greybel-test") / Path(f).stem / "build"
        target.mkdir(parents=True, exist_ok=True)
        try:
            proc = subprocess.run(
                [greybel, "build", f, str(target), "-dbf"],
                capture_output=True, text=True, timeout=20,
            )
            if proc.returncode == 0:
                out[f] = ("OK", "")
            else:
                err = (proc.stderr or proc.stdout or "").strip()
                first_line = err.split("\n")[0][:120] if err else "unknown"
                out[f] = ("FAIL", first_line)
        except subprocess.TimeoutExpired:
            out[f] = ("TIMEOUT", "")
        except Exception as e:
            out[f] = ("ERROR", str(e)[:120])
    return out


def discover_files(repo_path: str) -> list[str]:
    """Find all .src files in repo_path, excluding EXCLUDE_DIRS."""
    repo = Path(repo_path)
    if not repo.is_dir():
        sys.exit(f"repo not found: {repo_path}")
    files = []
    for src in repo.rglob("*.src"):
        rel = str(src.relative_to(repo))
        if any(d in rel for d in EXCLUDE_DIRS):
            continue
        files.append(rel)
    return sorted(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True, help="Path to greyhack-tools-style repo")
    parser.add_argument("--out", default="/tmp/bug-scan-results.json", help="Output JSON path")
    parser.add_argument("--build-sample", type=int, default=0, help="Verify top-N files with greybel build")
    args = parser.parse_args()

    files = discover_files(args.repo)
    print(f"Scanning {len(files)} files in {args.repo}...")

    repo = Path(args.repo).resolve()
    findings_per_file: dict[str, dict] = {}
    total_per_pattern: dict[str, int] = defaultdict(int)
    compiler_bug_files: dict[str, dict] = {}
    missing_marker_commands: list[str] = []

    for f in files:
        full_path = str(repo / f)
        pats = scan_file(full_path)
        if not pats:
            continue
        findings_per_file[f] = pats
        for p, c in pats.items():
            total_per_pattern[p] += c

        # Separate compiler-killer patterns from soft (n)
        compiler_pats = {p: c for p, c in pats.items() if not p.startswith("(n)")}
        if compiler_pats:
            compiler_bug_files[f] = compiler_pats

        if "(n) NO //command: marker" in pats and not is_library(f):
            missing_marker_commands.append(f)

    print(f"\nFiles with findings: {len(findings_per_file)} / {len(files)}")
    print(f"Files with real compiler bugs: {len(compiler_bug_files)}")
    print(f"Commands missing //command: marker: {len(missing_marker_commands)}")
    print(f"\nTotal per pattern:")
    for p, c in sorted(total_per_pattern.items(), key=lambda x: -x[1]):
        print(f"  {p}: {c}")

    # Build verification (optional)
    build_results: dict = {}
    if args.build_sample > 0:
        # Top-N highest-finding files
        top_files = sorted(
            compiler_bug_files.keys(),
            key=lambda f: -sum(compiler_bug_files[f].values()),
        )[: args.build_sample]
        print(f"\nVerifying top {len(top_files)} files via greybel build...")
        # Build absolute paths for subprocess
        abs_top = [str(repo / f) for f in top_files]
        # Map abs paths back to relative
        build_results = greybel_build_sample(abs_top, len(abs_top))
        for abs_f, (status, err) in build_results.items():
            rel_f = str(Path(abs_f).relative_to(repo))
            marker = "OK" if status == "OK" else "FAIL"
            print(f"  [{marker}] {rel_f}: {err}")

    # Write JSON
    out_data = {
        "repo": args.repo,
        "files_scanned": len(files),
        "total_per_pattern": dict(total_per_pattern),
        "files_with_findings": findings_per_file,
        "compiler_bug_files": compiler_bug_files,
        "missing_marker_commands": missing_marker_commands,
        "build_verification": build_results,
    }
    with open(args.out, "w") as f:
        json.dump(out_data, f, indent=2)
    print(f"\nResults saved → {args.out}")

    # Exit code 2 if any real compiler bugs (CI-friendly)
    return 2 if compiler_bug_files else 0


if __name__ == "__main__":
    sys.exit(main())