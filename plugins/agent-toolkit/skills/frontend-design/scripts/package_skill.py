#!/usr/bin/env python3
"""
Package skill for distribution.
Creates a .skill archive with proper structure.
"""

import os
import json
import shutil
import sys
from pathlib import Path
import tempfile

def get_skill_meta(skill_path):
    """Read skill metadata."""
    meta_path = skill_path / '_meta.json'
    if not meta_path.exists():
        raise FileNotFoundError("_meta.json not found")

    with open(meta_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_for_packaging(skill_path):
    """Validate skill is ready for packaging."""
    errors = []

    # Check required files
    for filename in ['SKILL.md', '_meta.json']:
        if not (skill_path / filename).exists():
            errors.append(f"Missing: {filename}")

    # Check meta has id
    try:
        meta = get_skill_meta(skill_path)
        if 'id' not in meta or 'version' not in meta:
            errors.append("_meta.json missing id or version")
    except Exception as e:
        errors.append(f"Cannot read _meta.json: {e}")

    return errors

def package_skill(skill_path, output_dir=None):
    """Package skill into .skill file."""
    skill_path = Path(skill_path)

    if not skill_path.exists():
        print(f"Error: Skill path does not exist: {skill_path}")
        sys.exit(1)

    # Validate
    errors = validate_for_packaging(skill_path)
    if errors:
        print("Packaging validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    # Get metadata
    meta = get_skill_meta(skill_path)
    skill_name = skill_path.name
    skill_id = meta['id']
    version = meta['version']

    # Output path
    if output_dir is None:
        output_dir = skill_path.parent
    output_dir = Path(output_dir)

    output_file = output_dir / f"{skill_name}_{skill_id}.skill"

    # Create package
    print(f"Packaging {skill_name} (id: {skill_id}, version: {version})")

    # Use shutil to create archive
    shutil.make_archive(
        str(output_file.with_suffix('')),  # archive name without .zip
        'zip',
        root_dir=skill_path.parent,
        base_dir=skill_path.name
    )

    # Rename .zip to .skill
    zip_file = output_file.with_suffix('.zip')
    if zip_file.exists():
        shutil.move(str(zip_file), str(output_file))

    print(f"Package created: {output_file}")
    print(f"Full path: {output_file.absolute()}")

    return output_file

def main():
    # Get skill path from args or use default
    if len(sys.argv) > 1:
        skill_path = Path(sys.argv[1])
    else:
        # Default to parent of scripts dir
        script_dir = Path(__file__).parent
        skill_path = script_dir.parent

    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    package_skill(skill_path, output_dir)

if __name__ == '__main__':
    main()
