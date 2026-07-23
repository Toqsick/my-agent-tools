#!/usr/bin/env python3
"""
Quick validation script for frontend-design skill.
Checks frontmatter, structure, and file integrity.
"""

import os
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
REQUIRED_FILES = ['SKILL.md', '_meta.json']
REQUIRED_FRONTMATTER_KEYS = ['name', 'description']

def validate_frontmatter(skill_md_path):
    """Validate SKILL.md frontmatter format and required keys."""
    with open(skill_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check frontmatter starts at the very beginning
    if not content.startswith('---'):
        return False, "SKILL.md must start with frontmatter '---'"

    # Extract frontmatter
    parts = content.split('---', 2)
    if len(parts) < 3:
        return False, "Frontmatter incomplete - missing closing '---'"

    frontmatter = parts[1]

    # Check required keys exist
    for key in REQUIRED_FRONTMATTER_KEYS:
        if f'{key}:' not in frontmatter:
            return False, f"Missing required frontmatter key: {key}"

    return True, "Frontmatter valid"

def validate_meta(meta_path):
    """Validate _meta.json structure."""
    import json

    if not meta_path.exists():
        return False, "_meta.json not found"

    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"_meta.json JSON error: {e}"

    # Check required keys
    if 'id' not in meta:
        return False, "_meta.json missing 'id'"
    if 'version' not in meta:
        return False, "_meta.json missing 'version'"

    # Validate id is numeric
    if not isinstance(meta['id'], int) and not str(meta['id']).isdigit():
        return False, "_meta.json 'id' must be numeric"

    return True, "_meta.json valid"

def validate_structure():
    """Validate skill directory structure."""
    errors = []

    # Check required files
    for filename in REQUIRED_FILES:
        filepath = SKILL_ROOT / filename
        if not filepath.exists():
            errors.append(f"Missing required file: {filename}")

    # Check name matches folder name
    skill_md = SKILL_ROOT / 'SKILL.md'
    if skill_md.exists():
        valid, msg = validate_frontmatter(skill_md)
        if not valid:
            errors.append(msg)
        else:
            # Extract name and verify
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()
            parts = content.split('---', 2)
            frontmatter = parts[1]
            name_match = re.search(r'name:\s*(.+)', frontmatter)
            if name_match:
                frontmatter_name = name_match.group(1).strip()
                folder_name = SKILL_ROOT.name
                if frontmatter_name != folder_name:
                    errors.append(f"Frontmatter name '{frontmatter_name}' doesn't match folder name '{folder_name}'")

    # Check _meta.json
    meta_path = SKILL_ROOT / '_meta.json'
    if meta_path.exists():
        valid, msg = validate_meta(meta_path)
        if not valid:
            errors.append(msg)

    return errors

def main():
    """Run all validations."""
    print(f"Validating skill at: {SKILL_ROOT}")
    print("-" * 50)

    errors = validate_structure()

    if errors:
        print("VALIDATION FAILED:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("VALIDATION PASSED: All checks successful")
        sys.exit(0)

if __name__ == '__main__':
    main()
