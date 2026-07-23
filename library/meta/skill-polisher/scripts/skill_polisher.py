#!/usr/bin/env python3
"""skill_polisher.py — Single entry-point for all skill maintenance tasks.

Subcommands:
  audit             Dry-run all checks, print report (no modifications)
  fix-bom           Migrate utf-8 → utf-8-sig in read-mode operations
  fix-chmod         Make shebang-scripts executable (+x)
  fix-description   Trim SKILL.md descriptions to <=60 chars (Hermes-index limit)
  find-duplicates   Find byte-identical scripts across skills
  validate-fm       Validate SKILL.md frontmatter (name/version/author/etc.)

Exit codes: 0 = no issues found, 1 = issues found or operation succeeded with findings.

Usage:
  python3 skill_polisher.py audit
  python3 skill_polisher.py fix-bom [--dry-run]
  python3 skill_polisher.py fix-chmod [--dry-run]
  python3 skill_polisher.py fix-description [--dry-run]
  python3 skill_polisher.py find-duplicates
  python3 skill_polisher.py validate-fm
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

SKILLS_ROOT = Path.home() / ".hermes" / "skills"


# ════════════════════════════════════════════════════════════════════
# Shared utilities
# ════════════════════════════════════════════════════════════════════

def is_excluded(path: Path) -> bool:
    """Return True for paths in .archive/ (historical snapshots)."""
    return ".archive" in path.parts


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Extract YAML frontmatter from a SKILL.md file. Returns (parsed_dict, body).

    Note: Uses utf-8-sig to auto-strip BOM. This is a BOM-stripping read, which
    is exactly the case we want — the BOM is never passed to YAML parser.
    """
    text = path.read_text(encoding="utf-8-sig")  # utf-8-sig = BOM-safe
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    import yaml
    try:
        return yaml.safe_load(parts[1]) or {}, parts[2]
    except yaml.YAMLError:
        return {}, text


# ════════════════════════════════════════════════════════════════════
# Subcommand: audit (dry-run of all checks)
# ════════════════════════════════════════════════════════════════════

def cmd_audit(args) -> int:
    """Run all checks in dry-run mode and print a summary report."""
    print("=== Skill-Polisher Audit Report ===\n")
    findings = []

    # Check 1: BOM
    bom_files = []
    SELF_PATH = "meta/skill-polisher/scripts/skill_polisher.py"  # BOM-stripping tool — exclude
    for py in SKILLS_ROOT.rglob("scripts/*.py"):
        if is_excluded(py):
            continue
        rel = py.relative_to(SKILLS_ROOT)
        if str(rel) == SELF_PATH:
            continue  # This IS the BOM-fixing tool, its utf-8-sig reads are correct
        try:
            text = py.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        # Find read_text(encoding="utf-8") or open(..., "r", encoding="utf-8")
        if re.search(r'read_text\(\s*encoding="utf-8"', text):
            bom_files.append(py)
        elif re.search(r'open\([^)]*"r"[^)]*encoding="utf-8"', text):
            bom_files.append(py)
    if bom_files:
        findings.append((f"BOM: {len(bom_files)} file(s) read utf-8 instead of utf-8-sig", bom_files))
    else:
        print("✓ BOM: All scripts BOM-safe")

    # Check 2: chmod
    chmod_files = []
    for py in SKILLS_ROOT.rglob("scripts/*"):
        if is_excluded(py) or not py.is_file():
            continue
        if not py.suffix in (".py", ".sh"):
            continue
        if py.stat().st_mode & 0o100:  # already +x
            continue
        try:
            first_line = py.read_text(encoding="utf-8-sig", errors="replace").split("\n", 1)[0]
        except Exception:
            continue
        if first_line.startswith("#!"):
            chmod_files.append(py)
    if chmod_files:
        findings.append((f"chmod: {len(chmod_files)} CLI tool(s) missing +x", chmod_files))
    else:
        print("✓ chmod: All CLI scripts executable")

    # Check 3: Description length
    desc_files = []
    for skill_md in SKILLS_ROOT.rglob("SKILL.md"):
        if is_excluded(skill_md):
            continue
        fm, _ = parse_frontmatter(skill_md)
        desc = str(fm.get("description", ""))
        if len(desc) > 60:
            desc_files.append((skill_md, len(desc)))
    if desc_files:
        findings.append((f"description: {len(desc_files)} SKILL.md(s) with >60-char description", [f for f, _ in desc_files]))
    else:
        print("✓ description: All SKILL.md descriptions <=60 chars")

    # Check 4: Duplicates
    hash_to_paths: dict[str, list[Path]] = {}
    for py in SKILLS_ROOT.rglob("scripts/*.py"):
        if is_excluded(py):
            continue
        try:
            h = md5(py)
            hash_to_paths.setdefault(h, []).append(py)
        except Exception:
            continue
    duplicates = {h: paths for h, paths in hash_to_paths.items() if len(paths) > 1}
    if duplicates:
        dups_count = sum(len(paths) for paths in duplicates.values()) - len(duplicates)
        findings.append((f"duplicates: {len(duplicates)} group(s), {dups_count} redundant file(s)", [p for paths in duplicates.values() for p in paths[1:]]))
    else:
        print("✓ duplicates: No production duplicates")

    # Check 5: Frontmatter
    fm_issues = []
    for skill_md in SKILLS_ROOT.rglob("SKILL.md"):
        if is_excluded(skill_md):
            continue
        fm, _ = parse_frontmatter(skill_md)
        if not fm:
            fm_issues.append((skill_md, "no frontmatter"))
            continue
        if "name" not in fm:
            fm_issues.append((skill_md, "missing name"))
        if "description" not in fm:
            fm_issues.append((skill_md, "missing description"))
        if "version" not in fm:
            fm_issues.append((skill_md, "missing version"))
    if fm_issues:
        findings.append((f"frontmatter: {len(fm_issues)} SKILL.md(s) with issues", [f for f, _ in fm_issues]))
    else:
        print("✓ frontmatter: All SKILL.md have valid frontmatter")

    # Print findings
    if findings:
        print()
        for desc, files in findings:
            print(f"⚠️  {desc}")
            for f in files[:5]:  # show first 5
                rel = f.relative_to(SKILLS_ROOT) if isinstance(f, Path) else f
                print(f"    - {rel}")
            if len(files) > 5:
                print(f"    ... and {len(files) - 5} more")
            print()
        print(f"=== Total: {len(findings)} issue category(s) ===")
        print("Run `skill_polisher.py fix-<category>` to remediate.")
        return 1
    print("\n=== All checks passed ✓ ===")
    return 0


# ════════════════════════════════════════════════════════════════════
# Subcommand: fix-bom
# ════════════════════════════════════════════════════════════════════

BOM_PATTERNS = [
    (re.compile(r'(\.read_text\(\s*encoding=)"utf-8"'), r'\1"utf-8-sig"'),
    (re.compile(r'(open\([^)]*?)("r"|"rt"|mode="r"|mode="rt")([^)]*?encoding=)"utf-8"'),
     r'\1\2\3"utf-8-sig"'),
]


def cmd_fix_bom(args) -> int:
    """Migrate utf-8 → utf-8-sig in read-mode operations."""
    files_changed = 0
    total_replacements = 0
    SELF_PATH = "meta/skill-polisher/scripts/skill_polisher.py"
    for py in SKILLS_ROOT.rglob("scripts/*.py"):
        if is_excluded(py):
            continue
        rel = py.relative_to(SKILLS_ROOT)
        if str(rel) == SELF_PATH:
            continue  # Don't self-modify BOM-stripping code
        text = py.read_text(encoding="utf-8-sig")
        original = text
        for pattern, replacement in BOM_PATTERNS:
            text, count = pattern.subn(replacement, text)
            total_replacements += count
        if text != original:
            files_changed += 1
            if args.dry_run:
                rel = py.relative_to(SKILLS_ROOT)
                print(f"[DRY-RUN] Would update: {rel}")
            else:
                py.write_text(text, encoding="utf-8-sig")
                rel = py.relative_to(SKILLS_ROOT)
                print(f"✓ Updated: {rel}")
    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Summary: {files_changed} files, {total_replacements} replacements")
    return 0 if files_changed == 0 else 1


# ════════════════════════════════════════════════════════════════════
# Subcommand: fix-chmod
# ════════════════════════════════════════════════════════════════════

def cmd_fix_chmod(args) -> int:
    """Make shebang-scripts executable."""
    fixed = 0
    for path in SKILLS_ROOT.rglob("scripts/*"):
        if is_excluded(path) or not path.is_file():
            continue
        if path.suffix not in (".py", ".sh"):
            continue
        if path.stat().st_mode & 0o100:  # already executable
            continue
        try:
            first_line = path.read_text(encoding="utf-8-sig", errors="replace").split("\n", 1)[0]
        except Exception:
            continue
        if first_line.startswith("#!"):
            if args.dry_run:
                print(f"[DRY-RUN] Would chmod +x: {path.relative_to(SKILLS_ROOT)}")
            else:
                path.chmod(path.stat().st_mode | 0o111)
                print(f"✓ chmod +x: {path.relative_to(SKILLS_ROOT)}")
            fixed += 1
    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Summary: {fixed} script(s) made executable")
    return 0 if fixed == 0 else 1


# ════════════════════════════════════════════════════════════════════
# Subcommand: fix-description
# ════════════════════════════════════════════════════════════════════

def cmd_fix_description(args) -> int:
    """Trim SKILL.md descriptions to <=60 chars.

    Strategy: Replace the verbose description with a short one derived from
    the existing keywords. We do NOT auto-invent descriptions — we suggest
    a truncation based on the first sentence or comma-separated keywords.

    The user MUST review the new description before committing.
    """
    fixed = 0
    for skill_md in SKILLS_ROOT.rglob("SKILL.md"):
        if is_excluded(skill_md):
            continue
        fm, body = parse_frontmatter(skill_md)
        desc = str(fm.get("description", ""))
        if len(desc) <= 60:
            continue
        # Heuristic: extract the first short phrase that captures the essence
        # Try first sentence first, then first phrase before colon
        first_sentence = re.split(r'[.!?]', desc)[0].strip()
        # Strip "Trigger phrases:" etc.
        first_sentence = re.split(r'Triggers? (when |on )', first_sentence)[0].strip()
        # If too long, try before first colon
        if len(first_sentence) > 60:
            first_sentence = desc.split(":")[0].strip()
        # Still too long? Just truncate to 57 + "..."
        if len(first_sentence) > 60:
            first_sentence = desc[:57].rstrip(",.- ") + "..."
        # Final guard
        if len(first_sentence) > 60:
            first_sentence = first_sentence[:60]
        # Ensure ends with period
        if not first_sentence.endswith("."):
            first_sentence = first_sentence.rstrip(". ") + "."

        new_fm = dict(fm)
        new_fm["description"] = first_sentence
        if args.dry_run:
            print(f"[DRY-RUN] Would trim {skill_md.relative_to(SKILLS_ROOT)}")
            print(f"  Old ({len(desc)}): {desc[:80]}...")
            print(f"  New ({len(first_sentence)}): {first_sentence}")
            print()
        else:
            import yaml
            new_yaml = yaml.safe_dump(new_fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
            new_text = f"---\n{new_yaml}---\n{body}"
            skill_md.write_text(new_text, encoding="utf-8-sig")
            print(f"✓ Trimmed: {skill_md.relative_to(SKILLS_ROOT)}")
            print(f"  New: {first_sentence}")
        fixed += 1
    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Summary: {fixed} description(s) trimmed")
    return 0 if fixed == 0 else 1


# ════════════════════════════════════════════════════════════════════
# Subcommand: find-duplicates
# ════════════════════════════════════════════════════════════════════

def cmd_find_duplicates(args) -> int:
    """Find byte-identical scripts across skills."""
    hash_to_paths: dict[str, list[Path]] = {}
    for py in SKILLS_ROOT.rglob("scripts/*.py"):
        if is_excluded(py):
            continue
        try:
            h = md5(py)
            hash_to_paths.setdefault(h, []).append(py)
        except Exception:
            continue
    duplicates = {h: paths for h, paths in hash_to_paths.items() if len(paths) > 1}
    if not duplicates:
        print("✓ No production duplicates found")
        return 0
    print(f"=== Found {len(duplicates)} duplicate group(s) ===\n")
    for h, paths in sorted(duplicates.items(), key=lambda x: x[1][0].name):
        skills = [p.relative_to(SKILLS_ROOT).parts[0] for p in paths]
        print(f"{paths[0].name} (md5: {h[:8]}...):")
        for p in paths:
            print(f"  - {p.relative_to(SKILLS_ROOT)}")
        print()
    return 1


# ════════════════════════════════════════════════════════════════════
# Subcommand: fix-fm (auto-fix simple frontmatter issues)
# ════════════════════════════════════════════════════════════════════

def cmd_fix_fm(args) -> int:
    """Auto-fix simple frontmatter issues via targeted string replacement.
    Nutzt String-Patching statt yaml.safe_dump, um Quoting und Formatierung zu erhalten.

    - description missing trailing period → add "."
    - missing 'author' → set to "Hermes Agent"
    - missing 'version' → set to "1.0.0"
    - invalid 'name' (with slashes) → use last path segment, lowercase
    """
    fixed = 0
    categories = {"period": 0, "author": 0, "version": 0, "name": 0}
    errors = []

    for skill_md in SKILLS_ROOT.rglob("SKILL.md"):
        if is_excluded(skill_md):
            continue
        text = skill_md.read_text(encoding="utf-8-sig")
        if not text.startswith("---"):
            continue

        # Frontmatter-Block als Rohtext extrahieren (kein YAML-Roundtrip!)
        fm_end = text.find("\n---", 3)
        if fm_end == -1:
            continue
        fm_text = text[3:fm_end]
        body = text[fm_end:]  # inklusive \n---
        changes = []
        new_fm = fm_text

        # 1. Description: Punkt anhängen wenn unquoted und kein Punkt am Ende
        desc_match = re.search(r'^(description:\s*)(.+)$', new_fm, re.M)
        if desc_match:
            prefix = desc_match.group(1)
            desc_val = desc_match.group(2).rstrip()
            # Multiline-YAML überspringen (| oder >)
            if not desc_val.startswith("|") and not desc_val.startswith(">"):
                # Prüfe ob quoted
                is_quoted = (desc_val.startswith("'") and desc_val.endswith("'")) or \
                            (desc_val.startswith('"') and desc_val.endswith('"'))
                inner = desc_val[1:-1] if is_quoted else desc_val
                inner_clean = inner.rstrip()
                if not inner_clean.endswith("."):
                    new_inner = inner_clean + "."
                    new_val = f"'{new_inner}'" if is_quoted else new_inner
                    old_line = desc_match.group(0)
                    new_line = f"{prefix}{new_val}"
                    new_fm = new_fm.replace(old_line, new_line, 1)
                    changes.append("description += '.'")
                    categories["period"] += 1

        # 2. Missing author → hinzufügen (vor dem schließenden --- via Zeilen-Insert)
        if not re.search(r'^author:', new_fm, re.M):
            # Einfügen nach der letzten vorhandenen Zeile
            new_fm = new_fm.rstrip("\n") + "\nauthor: Hermes Agent"
            changes.append("author = Hermes Agent")
            categories["author"] += 1

        # 3. Missing version → hinzufügen
        if not re.search(r'^version:', new_fm, re.M):
            new_fm = new_fm.rstrip("\n") + "\nversion: 1.0.0"
            changes.append("version = 1.0.0")
            categories["version"] += 1

        # 4. Invalid name (slashes) → last segment lowercase
        name_match = re.search(r'^name:\s*(.+)$', new_fm, re.M)
        if name_match:
            name_val = name_match.group(1).strip().strip('"').strip("'")
            if "/" in name_val:
                fixed_name = name_val.split("/")[-1].lower()
                fixed_name = re.sub(r"[^a-z0-9-]", "-", fixed_name)
                fixed_name = re.sub(r"-+", "-", fixed_name).strip("-")
                old_line = name_match.group(0)
                new_line = f"name: {fixed_name}"
                new_fm = new_fm.replace(old_line, new_line, 1)
                changes.append(f"name: {name_val} → {fixed_name}")
                categories["name"] += 1

        if not changes:
            continue

        fixed += 1
        if args.dry_run:
            print(f"[DRY-RUN] Would fix: {skill_md.relative_to(SKILLS_ROOT)}")
            for c in changes:
                print(f"  - {c}")
            print()
        else:
            # Write back: --- + new_fm + body
            new_text = f"---{new_fm}{body}"
            skill_md.write_text(new_text, encoding="utf-8-sig")
            print(f"✓ Fixed: {skill_md.relative_to(SKILLS_ROOT)}")
            for c in changes:
                print(f"  - {c}")
            print()

    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Summary: {fixed} SKILL.md(s) fixed")
    for cat, count in categories.items():
        if count > 0:
            print(f"  {cat}: {count}")
    if errors:
        print(f"  errors: {len(errors)}")
        for e in errors[:5]:
            print(f"    {e}")
    return 0


# ════════════════════════════════════════════════════════════════════
# Subcommand: validate-fm
# ════════════════════════════════════════════════════════════════════

def cmd_validate_fm(args) -> int:
    """Validate SKILL.md frontmatter (name/version/author/description)."""
    issues = []
    for skill_md in SKILLS_ROOT.rglob("SKILL.md"):
        if is_excluded(skill_md):
            continue
        fm, _ = parse_frontmatter(skill_md)
        rel = skill_md.relative_to(SKILLS_ROOT)
        if not fm:
            issues.append((rel, "no frontmatter"))
            continue
        if "name" not in fm:
            issues.append((rel, "missing 'name'"))
        elif not re.match(r"^[a-z][a-z0-9-]*$", str(fm["name"])):
            issues.append((rel, f"invalid 'name': {fm['name']}"))
        if "description" not in fm:
            issues.append((rel, "missing 'description'"))
        else:
            desc = str(fm["description"])
            if len(desc) > 60:
                issues.append((rel, f"description {len(desc)} chars (>60 limit)"))
            if not desc.endswith("."):
                issues.append((rel, "description missing trailing period"))
        if "version" not in fm:
            issues.append((rel, "missing 'version'"))
        if "author" not in fm:
            issues.append((rel, "missing 'author'"))

    if issues:
        print(f"=== {len(issues)} frontmatter issue(s) ===\n")
        for rel, issue in issues[:50]:
            print(f"  {rel}: {issue}")
        if len(issues) > 50:
            print(f"\n  ... and {len(issues) - 50} more")
        return 1
    print("✓ All SKILL.md frontmatter valid")
    return 0


# ════════════════════════════════════════════════════════════════════
# Main entry-point
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Skill-Polisher — single entry-point for skill maintenance tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # audit
    sub.add_parser("audit", help="Dry-run all checks, print report")

    # fix-bom
    p = sub.add_parser("fix-bom", help="Migrate utf-8 → utf-8-sig")
    p.add_argument("--dry-run", action="store_true")

    # fix-chmod
    p = sub.add_parser("fix-chmod", help="Make shebang-scripts executable")
    p.add_argument("--dry-run", action="store_true")

    # fix-description
    p = sub.add_parser("fix-description", help="Trim SKILL.md descriptions to <=60 chars")
    p.add_argument("--dry-run", action="store_true")

    # find-duplicates
    sub.add_parser("find-duplicates", help="Find byte-identical scripts")

    # validate-fm
    sub.add_parser("validate-fm", help="Validate SKILL.md frontmatter")

    # fix-fm
    p = sub.add_parser("fix-fm", help="Auto-fix simple frontmatter issues (period, author, version, name)")
    p.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    commands = {
        "audit": cmd_audit,
        "fix-bom": cmd_fix_bom,
        "fix-chmod": cmd_fix_chmod,
        "fix-description": cmd_fix_description,
        "fix-fm": cmd_fix_fm,
        "find-duplicates": cmd_find_duplicates,
        "validate-fm": cmd_validate_fm,
    }

    handler = commands.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main() or 0)