#!/usr/bin/env python3
"""
Pre-Scan-Script für GreyHack Multi-Agent-Audit (Phase 0).

Deterministischer Pattern-Scan über alle aktiven .src-Files im GreyHack-Toolbase.
Output: Markdown-Report mit Pattern-Cross-Tab + Per-File-Hits + Detailed-Findings.

Pitfall-Rationale (siehe multi-agent-orchestration / multi-agent-pitfalls-cheatsheet):
- Pitfall #25: Batch-Validation > Subagents bei >20 Files
- Pitfall #15: Output-Limits verhindern 600s Timeouts
- Pitfall #6: Expliziter Output-Pfad statt random

Proven 2026-07-02 mit 102 aktiven Files → 236 Matches → 36 P0 + 200 P1.

Usage:
    python3 pre-scan-np-patterns.py [--repo /home/bratan/greyhack-tools] [--output /tmp/pre-scan.md]

    # Default: scannt ~/greyhack-tools und schreibt nach ~/docs/system/pre-scan-YYYY-MM-DD.md
"""

import argparse
import os
import re
import pathlib
from collections import defaultdict
from datetime import datetime

REPO = pathlib.Path("/home/bratan/greyhack-tools")
DEFAULT_OUTPUT_DIR = pathlib.Path.home() / "docs" / "system"

# Pattern-Set: (pattern_id, regex, severity, description)
# Initial-Set: die häufigsten NP-Patterns aus Round 7-11 (2026-06-18/19) + 2026-07-02 Live-Scan
# Erweiterung: weitere NP-Patterns nach Bedarf hinzufügen
NP_PATTERNS = [
    # === P0 — Compile-Breakers / Hard-Bugs ===
    ("NP-21",  r'is_folder', 'P0', 'is_folder unreliable — use is_binary for type check'),
    ("NP-49",  r'"char\(10\)"', 'P0', '"char(10)" string literal instead of char(10)'),
    ("NP-N2",  r'HTTP\.Request', 'P0', 'HTTP.Request does not exist in vanilla GreyScript'),
    ("NP-X1",  r'get_shell\s*\(\s*[^)]+\)', 'P0', 'get_shell takes NO parameters — xmem-bug-pattern'),
    ("NP-N7",  r'=======', 'P0', '======= separator breaks greybel parser'),
    ("NP-N8",  r'"\s*if\s+.*\s+else\s+', 'P0', 'Inline ternary "(X if cond else Y)" not valid GreyScript'),

    # === P1 — Logic-Bugs / Style-Issues ===
    ("NP-30",  r'is_binary', 'P1', 'is_binary as folder detector — check intent'),
    ("NP-19",  r"'[^']*'", 'P1', 'Single quotes in strings (use double quotes)'),
    ("NP-63",  r'range\s*\([^)]*\.len\s*-\s*1\s*\)', 'P1', 'range(0, len-1) off-by-one — skips last element'),
    ("NP-51",  r'password.*=.*argv|args\[', 'P1', 'Password as CLI parameter'),
    ("NP-1",   r'indexOf\s*\([^)]*\)\s*==\s*null', 'P1', 'indexOf compared to null (use == -1)'),
    ("NP-7",   r'get_shell\.host_computer', 'P1', 'Repeated get_shell.host_computer — cache once'),
    ("NP-N1",  r'\.wget', 'P1', 'GreyScript has no wget — copy-paste instead'),
    ("NP-N3",  r'get_system_time', 'P1', 'get_system_time not available in GreyScript'),
    ("NP-N4",  r'str_repeat', 'P1', 'str_repeat not available — define own spacer'),
    ("NP-N5",  r'list\.applyFunction', 'P1', 'list.applyFunction off-by-one'),
    ("NP-N6",  r'\.format\s*\(', 'P1', '.format() with {} — verify semantics (works but check args)'),

    # === P2 — Minor / Smell ===
    ("NP-64",  r'map\.count\s*=\s*function', 'P2', 'map.count returns str(value).len, not occurrence count'),
    ("NP-66",  r'join\s*\(\s*"char\(10\)"\s*\)', 'P2', '.join("char(10)") literal instead of char(10)'),
]

# Files to EXCLUDE from scan
EXCLUDE_DIRS = ['backups', 'installer', 'tests', '.git', 'node_modules', '.claude', 'build', '.ci-build']
EXCLUDE_FILE_PATTERNS = [r'\.py$', r'\.sh$', r'\.md$', r'\.txt$', r'\.json$', r'\.yml$', r'\.yaml$']


def is_excluded(path: pathlib.Path) -> bool:
    """Check if file should be excluded from scan."""
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    for pat in EXCLUDE_FILE_PATTERNS:
        if re.search(pat, str(path)):
            return True
    return False


def get_active_src_files(repo: pathlib.Path) -> list:
    """Get all .src files in repo, excluding backups/installer/tests."""
    files = []
    for f in repo.rglob("*.src"):
        if not is_excluded(f):
            files.append(f)
    return sorted(files)


def scan_file(file_path: pathlib.Path, patterns: list) -> list:
    """Scan a single file for all NP-pattern matches."""
    matches = []
    try:
        content = file_path.read_text(encoding='utf-8-sig', errors='ignore')
    except Exception as e:
        return [("READ_ERROR", 0, "P2", f"Could not read: {e}", "")]

    for line_num, line in enumerate(content.split('\n'), start=1):
        for pid, regex, severity, desc in patterns:
            if re.search(regex, line):
                matches.append((pid, line_num, severity, desc, line.strip()[:120]))

    return matches


def main():
    parser = argparse.ArgumentParser(description="GreyHack NP-Pattern Pre-Scan")
    parser.add_argument("--repo", type=pathlib.Path, default=REPO, help="Repo root to scan")
    parser.add_argument("--output", type=pathlib.Path, default=None, help="Output file (default: ~/docs/system/pre-scan-YYYY-MM-DD.md)")
    parser.add_argument("--severity", choices=['P0', 'P1', 'P2', 'all'], default='all', help="Filter output by minimum severity")
    args = parser.parse_args()

    output = args.output or (DEFAULT_OUTPUT_DIR / f"pre-scan-{datetime.now().strftime('%Y-%m-%d')}.md")
    output.parent.mkdir(parents=True, exist_ok=True)

    files = get_active_src_files(args.repo)
    print(f"Scanning {len(files)} active .src files in {args.repo}...")

    # Aggregate matches
    by_pattern = defaultdict(list)
    by_file = defaultdict(list)
    severity_count = {'P0': 0, 'P1': 0, 'P2': 0}
    total_matches = 0

    for f in files:
        matches = scan_file(f, NP_PATTERNS)
        for pid, line, sev, desc, snippet in matches:
            by_pattern[pid].append({
                'file': str(f.relative_to(args.repo)),
                'line': line,
                'snippet': snippet,
            })
            by_file[str(f.relative_to(args.repo))].append((pid, line, sev, desc))
            severity_count[sev] += 1
            total_matches += 1

    # Severity filter
    sev_order = {'P0': 0, 'P1': 1, 'P2': 2}
    min_sev = sev_order.get(args.severity, 2) if args.severity != 'all' else 2

    # Write output
    today = datetime.now().strftime("%Y-%m-%d")
    with open(output, 'w') as out:
        out.write(f"# GreyHack Pre-Scan Results — {today}\n\n")
        out.write(f"**Generated:** {datetime.now().isoformat()}\n")
        out.write(f"**Files scanned:** {len(files)}\n")
        out.write(f"**Total matches:** {total_matches}\n")
        out.write(f"**Severity filter:** {args.severity}\n\n")

        out.write("## Severity Summary\n\n")
        out.write("| Severity | Count |\n|---|---|\n")
        for sev in ['P0', 'P1', 'P2']:
            out.write(f"| {sev} | {severity_count[sev]} |\n")
        out.write("\n")

        out.write("## Pattern-Cross-Tab\n\n")
        out.write("| Pattern-ID | Severity | Description | File-Count | Total-Matches |\n")
        out.write("|---|---|---|---|---|\n")
        for pid, _regex, sev, desc in NP_PATTERNS:
            if sev_order[sev] > min_sev:
                continue
            file_count = len(set(m['file'] for m in by_pattern[pid]))
            match_count = len(by_pattern[pid])
            if match_count > 0:
                out.write(f"| {pid} | {sev} | {desc} | {file_count} | {match_count} |\n")
        out.write("\n")

        out.write("## Per-File Hits (sorted by hit-count, top 30)\n\n")
        out.write("| File | Hit-Count | Pattern-IDs |\n|---|---|---|\n")
        sorted_files = sorted(by_file.items(), key=lambda x: -len(x[1]))[:30]
        for file_path, matches in sorted_files:
            pids = sorted(set(m[0] for m in matches))
            out.write(f"| {file_path} | {len(matches)} | {', '.join(pids)} |\n")
        out.write("\n")

        # Detailed per-pattern breakdown (only patterns with matches)
        out.write("## Detailed Pattern Findings\n\n")
        for pid, _regex, sev, desc in NP_PATTERNS:
            if sev_order[sev] > min_sev:
                continue
            if pid not in by_pattern:
                continue
            matches = by_pattern[pid]
            out.write(f"### {pid} — {desc} ({sev})\n\n")
            out.write(f"**Total matches:** {len(matches)} in {len(set(m['file'] for m in matches))} files\n\n")
            out.write("| File | Line | Snippet |\n|---|---|---|\n")
            for m in matches[:20]:
                snippet_safe = m['snippet'].replace('|', '\\|')
                out.write(f"| {m['file']} | {m['line']} | `{snippet_safe}` |\n")
            if len(matches) > 20:
                out.write(f"| ... | ... | *({len(matches) - 20} more matches truncated)* |\n")
            out.write("\n")

        out.write("## Files-Clean (no matches)\n\n")
        clean = [f for f in files if str(f.relative_to(args.repo)) not in by_file]
        if clean:
            for f in clean:
                out.write(f"- `{f.relative_to(args.repo)}`\n")
        else:
            out.write("*None — all files have at least one pattern match.*\n")

    print(f"Pre-scan complete: {output}")
    print(f"  Files: {len(files)}")
    print(f"  Matches: {total_matches}")
    print(f"  P0: {severity_count['P0']}, P1: {severity_count['P1']}, P2: {severity_count['P2']}")


if __name__ == "__main__":
    main()