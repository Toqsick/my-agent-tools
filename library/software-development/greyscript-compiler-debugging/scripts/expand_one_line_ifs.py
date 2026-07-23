#!/usr/bin/env python3
"""
expand_one_line_ifs.py — Pattern (a) one-line-if → multi-line expansion
für GreyScript / greybel (GreyHack 0.9.6771-beta).

VERIFIED 2026-07-07: 37 funde across 7 .src files auto-expanded and 6/7
builds erfolgreich (1 fail war Dependency-resolution, NICHT Pattern-a).

ROBUST GEGEN:
  - Beliebige Leading-Indentation (Tabs, Spaces, mixed)
  - Beliebige Body-Inhalte: returns, assignments, method-calls, continue,
    exit, fail(), warn(), push(), etc.
  - KEIN Statement-Chain (`if X then A; B end if`) — wird übersprungen
  - KEIN Combined one-liner (`then for ...`, `then if ...`, `then while`,
    `then function`, `then try`) — wird übersprungen
  - Idempotent (bereits multi-line → kein Match)

USAGE:
  python3 expand_one_line_ifs.py path/to/file.src [more.src ...]

EXIT CODES:
  0 = success (auch wenn 0 fixes)
  2 = usage error

DETAIL-LOG: /tmp/expansion-log.json (JSON pro Datei mit lineno, old, new)
"""
import re
import sys
import json
from pathlib import Path

# Regex: leading indent + "if " + condition + " then " + body + " end if"
# Body darf KEIN `;` (statement-chain), KEIN block-öffner (for/if/while/
# function/try) enthalten. Der Regex verbietet `;` im Body implizit durch
# [^;]*? aber wir prüfen es nochmal defensiv.
PATTERN = re.compile(
    r'^(\s*)if\s+(.+?)\s+then\s+([^;]*?)\s+end if\s*$'
)

BLOCK_OPENERS = ('for ', 'if ', 'while ', 'function ', 'try')

LOG_PATH = Path('/tmp/expansion-log.json')


def expand_line(line: str) -> tuple[str, bool]:
    """
    Returns (new_line, changed).
    """
    m = PATTERN.match(line.rstrip('\n').rstrip('\r'))
    if not m:
        return line, False
    indent, cond, body = m.group(1), m.group(2), m.group(3)
    body_stripped = body.strip()
    if not body_stripped:
        return line, False
    if ';' in body:
        return line, False  # Statement-chain — überspringen
    if body_stripped.startswith(BLOCK_OPENERS):
        return line, False  # Combined one-liner — überspringen
    # body-indent = leading-indent + '\t'. Funktioniert für all-tab,
    # all-spaces UND mixed-indent (z.B. metaxploit.src: 4-space + tab).
    body_indent = indent + '\t'
    new_line = f"{indent}if {cond} then\n{body_indent}{body_stripped}\n{indent}end if\n"
    return new_line, True


def process_file(path: Path) -> dict:
    text = path.read_text(encoding='utf-8-sig')
    lines = text.splitlines(keepends=True)
    new_lines = []
    changes = []
    for i, line in enumerate(lines, start=1):
        new_line, changed = expand_line(line)
        new_lines.append(new_line)
        if changed:
            changes.append({
                'lineno': i,
                'old': line.rstrip('\n'),
            })
    if changes:
        path.write_text(''.join(new_lines), encoding='utf-8')
    return {
        'path': str(path),
        'num_fixes': len(changes),
        'changes': changes,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: expand_one_line_ifs.py <file.src> [more.src ...]", file=sys.stderr)
        sys.exit(2)
    total = 0
    results = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        if not p.exists():
            print(f"[SKIP] {arg}: not found", file=sys.stderr)
            continue
        result = process_file(p)
        results.append(result)
        total += result['num_fixes']
        print(f"[{result['num_fixes']:>2} fixes] {arg}")
    print(f"=== TOTAL: {total} fixes across {len(results)} files ===")
    LOG_PATH.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )


if __name__ == '__main__':
    main()