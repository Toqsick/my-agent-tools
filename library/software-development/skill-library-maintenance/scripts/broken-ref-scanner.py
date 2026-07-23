#!/usr/bin/env python3
"""
broken-ref-scanner.py — run via `python3 scripts/broken-ref-scanner.py`

Scans ~/.hermes/skills/ for broken references and categorises them:
  BUNDLE_MISSING      — skill has no references/ or scripts/ dir but mentions paths there
  FILE_MISSING        — dir exists, specific file missing
  TEMPLATE_PLACEHOLDER — reference is a generic example/placeholder

Output: stdout summary + optional JSON file (--json).
"""
import argparse, json, os, re, sys
from pathlib import Path

# Regex: bare-path refs and markdown links to references/ scripts/ etc.
BARE_REF = re.compile(
    r'(?<!\w)'
    r'((?:references|scripts|templates|assets)/'
    r'[A-Za-z0-9._/\-]+\.[A-Za-z0-9]+)'
)
MD_LINK = re.compile(
    r'\[[^\]]*\]\(((?:references|scripts|templates|assets)/[A-Za-z0-9._/\-]+)\)'
)
PLACEHOLDER_FILE = re.compile(
    r'(?:example|EXAMPLE|sample|SAMPLE|todo|TODO|placeholder|PLACEHOLDER)'
)

ROOT = Path.home() / ".hermes" / "skills"


def scan_skill(md_path: Path):
    """Return list of (ref, category, somewhere) for every broken ref found."""
    skill_dir = md_path.parent
    try:
        text = md_path.read_text(errors="ignore")
    except OSError:
        return []

    candidates = set()
    for m in BARE_REF.finditer(text):
        candidates.add(m.group(1))
    for m in MD_LINK.finditer(text):
        candidates.add(m.group(1))

    broken = []
    for ref in sorted(candidates):
        target = skill_dir / ref
        if target.exists():
            continue

        # TEMPLATE_PLACEHOLDER?
        placeholder = bool(PLACEHOLDER_FILE.search(ref))

        # Check if file exists elsewhere in the skills library
        elsewhere = list(ROOT.rglob(target.name))
        remote_hit = any(
            str(p.relative_to(ROOT)).replace("\\", "/").endswith(
                ref.rsplit("/", 1)[0] + "/" + target.name
            )
            for p in elsewhere
        )

        cat = "TEMPLATE_PLACEHOLDER" if placeholder else (
            "BUNDLE_MISSING" if not target.parent.exists() else "FILE_MISSING"
        )
        broken.append((ref, cat, remote_hit))
    return broken


def categorize(skills: list[Path]) -> dict:
    """Run scan across all skills, return categorised results."""
    out = {"skills": [], "categories": {
        "BUNDLE_MISSING": 0, "FILE_MISSING": 0, "TEMPLATE_PLACEHOLDER": 0
    }}
    for md in skills:
        refs = scan_skill(md)
        if not refs:
            continue
        rel = str(md.relative_to(ROOT))
        by_cat = {"BUNDLE_MISSING": 0, "FILE_MISSING": 0, "TEMPLATE_PLACEHOLDER": 0}
        for _, cat, _ in refs:
            by_cat[cat] += 1
            out["categories"][cat] += 1
        out["skills"].append({
            "path": rel,
            "total": len(refs),
            "by_cat": by_cat,
            "refs": [(r, c) for r, c, _ in refs]
        })
    out["skills"].sort(key=lambda s: -s["total"])
    out["total_skills_scanned"] = len(skills)
    out["total_skills_with_broken"] = len(out["skills"])
    return out


def fast_json_repr(o):
    """Compact helper for json.dump."""
    return json.dumps(o, indent=2, ensure_ascii=False)


def main():
    p = argparse.ArgumentParser(description="Scan skill library for broken references")
    p.add_argument("--json", metavar="FILE", help="Write full results as JSON")
    p.add_argument("--top", type=int, default=20, help="How many top skills to show (default 20)")
    p.add_argument("--no-archive", action="store_true", default=True,
                   help="Exclude .archive/ paths (default on)")
    args = p.parse_args()

    # Collect active skills
    all_skills = []
    for md in ROOT.rglob("SKILL.md"):
        parts = md.relative_to(ROOT).parts
        if args.no_archive and any(p in (".archive", ".curator_backups", ".hub", "hub-imported") for p in parts):
            continue
        all_skills.append(md)
    all_skills.sort()

    print(f"Active SKILL.md files: {len(all_skills)}")
    print(f"Scanning...", flush=True)

    result = categorize(all_skills)

    # Print summary
    cats = result["categories"]
    total = sum(cats.values())
    print(f"\nSkills with broken refs: {result['total_skills_with_broken']}")
    print(f"Total broken references: {total}")
    print()
    print(f"  BUNDLE_MISSING:       {cats['BUNDLE_MISSING']:4d}  "
          f"(skill has no bundle dir, ref cannot resolve)")
    print(f"  FILE_MISSING:         {cats['FILE_MISSING']:4d}  "
          f"(bundle dir exists, specific file missing)")
    print(f"  TEMPLATE_PLACEHOLDER:  {cats['TEMPLATE_PLACEHOLDER']:3d}  "
          f"(ref is example/placeholder, never meant to resolve)")
    print(f"  {'─' * 42}")
    print(f"  TOTAL:               {total:4d}")

    # Top-N table
    print(f"\n--- Top {args.top} skills with most broken refs (B=BUNDLE / F=FILE / T=TEMPLATE) ---")
    top = result["skills"][:args.top]
    print(f" {'Cnt':>3s}  {'B':>2s} {'F':>2s} {'T':>2s}  Skill")
    print(f" {'─'*3}  {'─'*2} {'─'*2} {'─'*2}  {'─'*50}")
    for s in top:
        b = s["by_cat"]["BUNDLE_MISSING"]
        f = s["by_cat"]["FILE_MISSING"]
        t = s["by_cat"]["TEMPLATE_PLACEHOLDER"]
        print(f" {s['total']:3d}  {b:2d} {f:2d} {t:2d}  {s['path']}")

    # Write JSON
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        print(f"\nFull results written to {args.json}")


if __name__ == "__main__":
    main()
