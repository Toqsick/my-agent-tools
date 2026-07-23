#!/usr/bin/env python3
"""
Extract paired cmd_X blocks from a monolithic GreyScript source for modular splitting.

When splitting a large GreyScript source (e.g. 78KB Yuno V6) into multiple
independent modules under the ~12KB //command: ceiling, each command function
needs BOTH the init declaration (cmd_X = {}) AND the body (cmd_X.run = function ... end function).
This script finds both parts and outputs them paired.

Usage:
    python3 extract-paired-blocks.py <source.src> [--module-assign JSON_FILE]
    
    --module-assign JSON_FILE: optional JSON mapping module_name -> [cmd_names]
                                If omitted, prints all found blocks for manual assignment.

Example JSON for --module-assign:
    {
        "yuno_recon": ["targets", "use", "back", "nmap", "exploitscan", "deepscan"],
        "yuno_attack": ["exploit", "hack", "loot", "defend", "bank", "ssh"]
    }
"""

import re
import sys
import json
import os

def find_paired_blocks(source_text):
    """
    Find ALL cmd_X = {} declarations AND cmd_X.run = function...end function blocks.
    Returns a dict: { "cmd_name": {"init_line": N, "body_start": N, "body_end": N} }
    """
    lines = source_text.split('\n')
    blocks = {}

    # Phase 1: Find all cmd_X = {} declarations (init lines)
    for i, line in enumerate(lines, 1):
        m = re.match(r'^cmd_(\w+)\s*=\s*\{\}\s*$', line)
        if m:
            name = m.group(1)
            blocks.setdefault(name, {})
            blocks[name]['init_line'] = i

    # Phase 2: Find all cmd_X.run = function(...) ... end function blocks
    in_block = False
    func_name = None
    func_start = 0
    brace_depth = 0

    for i, line in enumerate(lines, 1):
        m = re.search(r'cmd_(\w+)\.run\s*=\s*function', line)
        if m and not in_block:
            in_block = True
            func_name = m.group(1)
            func_start = i
            brace_depth = 0

        if in_block:
            brace_depth += line.count('{') - line.count('}')
            if brace_depth <= 0 and 'end function' in line:
                blocks.setdefault(func_name, {})
                blocks[func_name]['body_start'] = func_start
                blocks[func_name]['body_end'] = i
                in_block = False
                func_name = None

    return blocks

def build_module(source_text, cmd_names, blocks, module_header=""):
    """
    Build a module source by extracting paired init+body for each cmd.
    Returns the module as a string.
    """
    lines = source_text.split('\n')
    output_parts = []

    if module_header:
        output_parts.append(module_header)

    for cmd in cmd_names:
        if cmd not in blocks:
            print(f"  ⚠️ WARNING: cmd_{cmd} not found in source!")
            continue

        p = blocks[cmd]
        if 'init_line' in p:
            # cmd_X = {}
            output_parts.append(lines[p['init_line'] - 1])
        if 'body_start' in p and 'body_end' in p:
            # cmd_X.run = function ... end function
            output_parts.append(
                '\n'.join(lines[p['body_start'] - 1:p['body_end']])
            )

    return '\n'.join(output_parts)

def detect_cmds_in_source(source_text):
    """Simple detection: find all cmd_ names referenced anywhere.

    ⚠️ FALSE POSITIVE WARNING — cmd_freq inside cmd_suggest.run:
    The unanchored regex cmd_(\w+)\s*=\s*\{ matches 'cmd_freq = {}' even
    when it's a LOCAL variable indented inside cmd_suggest.run. This is
    NOT a top-level command. Use the anchored find_paired_blocks() which
    uses ^cmd_ to only match top-level declarations.

    The unanchored version here is fine for discovery/displays, but
    don't use it for module assignment without human review.
    """
    names_init = set(re.findall(r'cmd_(\w+)\s*=\s*\{', source_text))
    names_run = set(re.findall(r'cmd_(\w+)\.run\s*=\s*function', source_text))
    all_names = names_init | names_run

    # Warn about likely local variables (indented cmd_X = {})
    for line in source_text.split('\n'):
        if line.lstrip().startswith('cmd_') and '= {}' in line:
            if line.startswith((' ', '\t')):
                m = re.match(r'\s*cmd_(\w+)\s*=\s*\{', line)
                if m and m.group(1) in all_names:
                    print(f"   ⚠️  INDENTED LOCAL: cmd_{m.group(1)} on line "
                          f"'{line.strip()[:50]}' — likely inside a function "
                          f"body, NOT a top-level command!")

    return all_names


# ============================================================
# CLI
# ============================================================
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    source_path = sys.argv[1]
    if not os.path.exists(source_path):
        print(f"❌ Source not found: {source_path}")
        sys.exit(1)

    with open(source_path, 'r') as f:
        source = f.read()

    blocks = find_paired_blocks(source)
    all_cmds = detect_cmds_in_source(source)
    print(f"📊 Source: {source_path}")
    print(f"   Lines: {len(source.split(chr(10)))}")
    print(f"   Unique cmd_ names: {len(all_cmds)}")
    print(f"   Paired blocks (init + body): {len(blocks)}")

    # Check for orphans
    init_only = {n for n, p in blocks.items() if 'init_line' in p and 'body_start' not in p}
    body_only = {n for n, p in blocks.items() if 'body_start' in p and 'init_line' not in p}
    orphan_end = {n for n, p in blocks.items() if 'body_start' not in p and 'init_line' not in p}

    if init_only:
        print(f"   ⚠️ Init-only (no body): {init_only}")
    if body_only:
        print(f"   ⚠️ Body-only (no init): {body_only}")

    # Module assignment
    if len(sys.argv) >= 3 and sys.argv[2].startswith('--module-assign='):
        assign_json = sys.argv[2].split('=', 1)[1]
        with open(assign_json, 'r') as f:
            assignment = json.load(f)

        print(f"\n📦 Building {len(assignment)} modules...")
        for mod_name, cmd_list in assignment.items():
            module_source = build_module(source, cmd_list, blocks)
            out_path = f"{mod_name}.src"
            with open(out_path, 'w') as f:
                f.write(module_source)
            print(f"   ✅ {out_path}: {len(module_source)}B ({len(cmd_list)} cmds)")
    else:
        # Print all blocks for manual review
        print(f"\n📋 All blocks ({len(blocks)} total):")
        for name in sorted(blocks.keys()):
            p = blocks[name]
            parts = []
            if 'init_line' in p:
                parts.append(f"init L{p['init_line']}")
            if 'body_start' in p:
                parts.append(f"body L{p['body_start']}-{p['body_end']}")
            print(f"   cmd_{name}: {', '.join(parts)}")

        print(f"\n💡 Tip: pass --module-assign=assignments.json to auto-build modules")
