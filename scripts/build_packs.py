#!/usr/bin/env python3
"""build_packs.py — validate packs/manifest.json and emit routing/bundles/*.yaml.

The 8 skill packs are the *installed*-skill grouping layer over the 129 skills of
the ``agent-toolkit`` plugin. The canonical source of truth is the hand-curated
``plugins/agent-toolkit/packs/manifest.json``; this script:

  1. validates it — every installed skill dir is in exactly one pack, no dupes,
     every referenced skill exists on disk, and the union == the installed set;
  2. emits one ``routing/bundles/<pack>.yaml`` per pack (same schema as the legacy
     hand-written bundles: name / description / skills / instruction), replacing
     the stale bundles that referenced non-installed library skills.

Invoked from ``scripts/build_index.py`` so a single ``python3 scripts/build_index.py``
rebuilds INDEX.json, NAVIGATION.md, routing/registry/*, AND routing/bundles/*.

Exits non-zero on any validation error so CI catches a broken partition.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "agent-toolkit"
MANIFEST = PLUGIN / "packs" / "manifest.json"
INSTALLED_DIR = PLUGIN / "skills"
BUNDLES_DIR = REPO / "routing" / "bundles"


def installed_skill_dirs() -> set[str]:
    if not INSTALLED_DIR.exists():
        return set()
    return {p.name for p in INSTALLED_DIR.iterdir()
            if p.is_dir() and (p / "SKILL.md").exists()}


def validate(manifest: dict) -> list[str]:
    """Return a list of human-readable errors (empty == valid)."""
    errors: list[str] = []
    installed = installed_skill_dirs()
    seen: dict[str, str] = {}
    packs = manifest.get("packs", [])
    if not packs:
        errors.append("manifest has no packs")
        return errors
    names = [p.get("name", "?") for p in packs]
    if len(names) != len(set(names)):
        errors.append(f"duplicate pack names: {names}")
    for pack in packs:
        pname = pack.get("name", "<unnamed>")
        if not pack.get("name"):
            errors.append("a pack is missing its 'name'")
            continue
        skills = pack.get("skills", [])
        if not isinstance(skills, list) or not skills:
            errors.append(f"pack '{pname}' has no skills")
            continue
        # entries may be {name, description} objects or bare strings
        skill_names = []
        for s in skills:
            sn = s["name"] if isinstance(s, dict) else str(s)
            skill_names.append(sn)
            if sn in seen:
                errors.append(f"skill '{sn}' appears in both '{seen[sn]}' and '{pname}'")
            seen[sn] = pname
            if sn not in installed:
                errors.append(f"pack '{pname}' references skill '{sn}' not on disk")
        if len(skill_names) != len(set(skill_names)):
            errors.append(f"pack '{pname}' has duplicate skill entries")
    missing = installed - set(seen)
    extra = set(seen) - installed
    if missing:
        errors.append(f"{len(missing)} installed skill(s) not in any pack: {sorted(missing)}")
    if extra:
        errors.append(f"{len(extra)} pack skill(s) not on disk: {sorted(extra)}")
    return errors


def _yaml_escape(s: str) -> str:
    """Minimal YAML scalar escaping for the bundle fields we emit."""
    s = s.replace('"', '\\"')
    return f'"{s}"'


def emit_bundles(manifest: dict) -> None:
    """Write routing/bundles/<pack>.yaml for each pack; remove stale bundles."""
    BUNDLES_DIR.mkdir(parents=True, exist_ok=True)
    keep = set()
    for pack in manifest["packs"]:
        pname = pack["name"]
        keep.add(pname)
        skills = [s["name"] if isinstance(s, dict) else str(s) for s in pack["skills"]]
        title = pack.get("title", pname)
        desc = pack.get("description", "")
        # instruction: a short routing hint, generated from the skill names.
        hint_skills = ", ".join(skills[:6]) + ("…" if len(skills) > 6 else "")
        instruction = (f"Tasks in the {title} domain route to the {pname} pack. "
                       f"Representative skills: {hint_skills}. "
                       f"See packs/{pname}/README.md for the full roster and triggers.")
        lines = [
            f"name: {pname}",
            f"description: {desc}",
            "skills:",
        ]
        for s in skills:
            lines.append(f"  - {s}")
        lines.append("instruction: |")
        for ln in instruction.splitlines() or [instruction]:
            lines.append(f"  {ln}")
        (BUNDLES_DIR / f"{pname}.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    # remove stale bundles that are no longer packs (legacy hand-written set)
    for old in BUNDLES_DIR.glob("*.yaml"):
        if old.stem not in keep:
            old.unlink()
            print(f"  removed stale bundle: {old.name}")


def main() -> int:
    if not MANIFEST.exists():
        print(f"ERROR: {MANIFEST} not found", file=sys.stderr)
        return 2
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors = validate(manifest)
    if errors:
        print("❌ packs/manifest.json validation failed:", file=sys.stderr)
        for e in errors:
            print(f"   - {e}", file=sys.stderr)
        return 1
    counts = {p["name"]: len(p["skills"]) for p in manifest["packs"]}
    total = sum(counts.values())
    print(f"✅ packs/manifest.json valid: {total} skills across "
          f"{len(counts)} packs ({counts})")
    emit_bundles(manifest)
    print(f"   wrote {len(counts)} bundle(s) to routing/bundles/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())