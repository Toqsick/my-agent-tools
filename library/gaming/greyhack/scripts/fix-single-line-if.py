#!/usr/bin/env python3
"""
P0 Auto-Fixer für GreyScript single-line if/then/end if Pattern.

Erkennt:   if COND then BODY end if
Formatiert um zu:
            if COND then
                BODY
            end if

Außerdem: ersetzt print(\"...\") mit Escape-Sequenzen → print mit Single-Quotes
um greybel-js Build-Errors zu vermeiden (siehe setup.src-Workaround).

VERWENDUNG:
    python3 fix-single-line-if.py <file1.src> [file2.src ...]

ODER über die Skill (greyhack):
    siehe SKILL.md → "Python Auto-Fixer for single-line if/then/end if"

VALIDIERUNG (2026-06-25):
    81 Fixes über 13 .src-Files in PR #29, 15/15 Build-Erfolg danach.

LIMITATIONEN:
    - Kein Multi-Statement-Body (if X then A; B end if)
    - Kein inline-if expression ("X" if cond else "Y")
    - Keine fehlende end if (separate manuelle Fix nötig)
"""
import re
import sys
from pathlib import Path

# Pattern: [ \t]+ if ... then ... end if  (single line)
# Wichtig: [ \t]+ nicht nur \t+ — manche Files (grsa_v2, hardening) nutzen 4-Space-Indent
SINGLE_LINE_IF = re.compile(
    r'^([ \t]+)(if\b.+?\bthen\b)(.+?)(\bend if\b)\s*$',
    re.IGNORECASE
)

def fix_file(path: Path) -> int:
    """Return Anzahl Fixes."""
    text = path.read_text(encoding='utf-8-sig')
    lines = text.split('\n')
    out = []
    fixes = 0

    for line in lines:
        m = SINGLE_LINE_IF.match(line)
        if not m:
            out.append(line)
            continue

        indent = m.group(1)
        head = m.group(2).strip()        # "if COND then"
        body = m.group(3).strip()        # "BODY"
        tail = m.group(4).strip()        # "end if"

        new_block = (
            f"{indent}{head}\n"
            f"{indent}\t{body}\n"
            f"{indent}{tail}"
        )
        out.append(new_block)
        fixes += 1

    if fixes:
        path.write_text('\n'.join(out), encoding='utf-8')
    return fixes


def fix_setup_escape(path: Path) -> int:
    """tools/setup.src: print(\"...\\\"...\\\"...\") → print(\"...'...'...\")"""
    text = path.read_text(encoding='utf-8-sig')
    repls = [
        ('print("  importcode(\\"bin/libcore.src\\")")',
         "print(\"  importcode('bin/libcore.src')\")"),
        ('print("  importcode(\\"bin/cliFeedback.src\\")")',
         "print(\"  importcode('bin/cliFeedback.src')\")"),
        ('print("  importcode(\\"bin/buildcore.src\\")")',
         "print(\"  importcode('bin/buildcore.src')\")"),
        ('print("  importcode(\\"bin/netcore.src\\")")',
         "print(\"  importcode('bin/netcore.src')\")"),
        ('print("  importcode(\\"bin/filecore.src\\")")',
         "print(\"  importcode('bin/filecore.src')\")"),
    ]
    new = text
    n = 0
    for old, repl in repls:
        if old in new:
            new = new.replace(old, repl)
            n += 1
    if n:
        path.write_text(new, encoding='utf-8')
    return n


def main():
    if len(sys.argv) < 2:
        print("Usage: fix-single-line-if.py <file1.src> [file2.src ...]")
        print()
        print("Beispiel:")
        print("  python3 fix-single-line-if.py src/buildcore.src src/debugcore.src")
        sys.exit(2)

    total = 0
    for arg in sys.argv[1:]:
        p = Path(arg)
        if not p.exists():
            print(f"  ⚠ {arg} existiert nicht")
            continue
        n = fix_file(p)
        if p.name == 'setup.src':
            n += fix_setup_escape(p)
        if n:
            print(f"  ✅ {p}: {n} Fixes")
            total += n
        else:
            print(f"  ·  {p}: nichts zu tun")
    print(f"Total: {total} Fixes")


if __name__ == '__main__':
    main()
