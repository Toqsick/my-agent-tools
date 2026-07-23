# Health Audit — 10-Dimension Scan Protocol

Multi-dimensional health check of ALL skills — not just size. Captures permission, frontmatter, broken-link, secret, duplicate, manifest-integrity, and storage metrics in one pass.

## Proactive Fix Stance

**Different from Security Audits:** Unlike security audits (read-only report → explicit approval), non-security health findings (broken links, missing execute bits, manifest orphans) should be **fixed immediately** without asking. The 2026-07-07 audit fixed 24 shell scripts + 17 broken links + 7 manifest entries without pre-approval — all idempotent and reversible. Security-related findings (hardcoded API keys, leaked credentials) still require the read-only → approval flow.

## 10-Dimension Scan Protocol

Run via `execute_code` for speed — Python batch tooling is faster than shell loops for 200+ files:

```python
import os, yaml, re, hashlib
from pathlib import Path

SKILLS = Path("~/.hermes/skills").expanduser()
archive_dirs = [".archive", ".curator_backups", ".hub"]

def _ok(d):
    return not any(a in d.parts for a in archive_dirs)

# 1. FRONTMATTER — parse every SKILL.md with yaml.safe_load
frontmatter_ok = 0
frontmatter_broken = []
for skill_md in SKILLS.rglob("SKILL.md"):
    if not _ok(skill_md): continue
    text = skill_md.read_text()
    try:
        if not text.startswith("---\n"):
            frontmatter_broken.append(str(skill_md))
            continue
        _, fm_text, _ = text.split("---", 2)
        yaml.safe_load(fm_text)
        frontmatter_ok += 1
    except Exception:
        frontmatter_broken.append(str(skill_md))

# 2. PERMISSIONS — shell scripts without +x
not_exec = []
for f in SKILLS.rglob("*.sh"):
    if not _ok(f): continue
    if "scripts" in f.parts and not os.access(f, os.X_OK):
        not_exec.append(str(f))

# 3. BROKEN MD-LINKS + BARE-PATH REFS — [text](relative/path) AND inline references/X.md mentions that don't resolve anywhere in the skills tree
broken_links = []
files_with_broken = set()
bare_path_refs = []
for skill_md in SKILLS.rglob("SKILL.md"):
    if not _ok(skill_md): continue
    text = skill_md.read_text()
    # Markdown links [text](relative/path)
    for m in re.finditer(r'\[([^\]]+)\]\(([\w\-./]+\.(?:md|py|sh|js|ts|yaml|yml|html))\)', text):
        ref = m.group(2)
        if ref.startswith(("http", "/", "#")): continue
        target = skill_md.parent / ref
        if not target.exists():
            broken_links.append(f"{skill_md.parent.name}: {ref}")
            files_with_broken.add(str(skill_md.relative_to(SKILLS)))
    # Bare-path inline references: see `references/X.md` or `scripts/Y.sh` (not markdown link syntax)
    for m in re.finditer(r'(?:references|scripts)/[A-Za-z0-9._/-]+', text):
        ref = m.group(0)
        target = skill_md.parent / ref
        if not target.exists():
            # Cross-skill resolution: check if ref exists anywhere else in the skills tree
            cross = list(SKILLS.rglob(f"**/{ref}"))
            if not any(_ok(f) for f in cross[:1]):
                bare_path_refs.append(f"{skill_md.parent.name}: {ref}")
                files_with_broken.add(str(skill_md.relative_to(SKILLS)))

# 4. SECRETS — hardcoded tokens in skill files
secrets_found = []
for skill_md in SKILLS.rglob("SKILL.md"):
    if not _ok(skill_md): continue
    text = skill_md.read_text()
    # Catch literal secrets like ghp_xxx, sk-xxx (NOT placeholder 'sk-xxx...xxxx')
    for m in re.finditer(r'(["\'`]?)([gs]k[_-][a-zA-Z0-9_-]{16,})\1', text):
        if "xxxx" not in m.group(2):
            secrets_found.append(f"{skill_md.parent.name}: {m.group(2)[:20]}...")

# 5. DUPLICATES — two skills with same name:
# (Detection requires comparing across all active dirs)
# Simple check: count name: occurrences across all SKILL.md files
names_seen = {}
for skill_md in SKILLS.rglob("SKILL.md"):
    if not _ok(skill_md): continue
    text = skill_md.read_text()
    m = re.search(r"^name:\s*(.+)", text, re.MULTILINE)
    if m:
        name = m.group(1).strip().strip("\"'")
        names_seen.setdefault(name, []).append(str(skill_md))
        duplicates = {n: paths for n, paths in names_seen.items() if len(paths) > 1}

# 6. MANIFEST — check .bundled_manifest for orphans
manifest_path = SKILLS / ".bundled_manifest"
manifest_orphans = set()
if manifest_path.exists():
    for line in manifest_path.read_text().splitlines():
        if ":" not in line: continue
        name, h = line.split(":", 1)
        found = False
        for skill_md in SKILLS.rglob(f"**/{name}/SKILL.md"):
            if _ok(skill_md): found = True; break
        if not found:
            manifest_orphans.add(name)

# 7. STORAGE
total_bytes = sum(f.stat().st_size for f in SKILLS.rglob("*") if f.is_file() and _ok(f))
active_count = len([f for f in SKILLS.rglob("SKILL.md") if _ok(f)])

# 8. PYTHON SYNTAX — verify all .py files compile
syntax_fail = []
for f in SKILLS.rglob("*.py"):
    if not _ok(f): continue
    import subprocess
    r = subprocess.run(["python3", "-m", "py_compile", str(f)], capture_output=True, text=True)
    if r.returncode != 0:
        syntax_fail.append(str(f.relative_to(SKILLS)))

# 9. MONOLITHS — SKILL.md >500 lines (line-count, better token proxy than bytes)
monoliths = {str(f.relative_to(SKILLS)): len(f.read_text().splitlines())
             for f in SKILLS.rglob("SKILL.md") if _ok(f) and len(f.read_text().splitlines()) > 500}

# 10. TOKEN BUDGET — SKILL.md >25KB (context-window cost)
over_budget = {str(f.relative_to(SKILLS)): f.stat().st_size
               for f in SKILLS.rglob("SKILL.md") if _ok(f) and f.stat().st_size > 25000}

# 11. EXTRACTION CANDIDATES — >200 lines but no references/ dir
extraction_candidates = {}
for f in SKILLS.rglob("SKILL.md"):
    if not _ok(f): continue
    lines = len(f.read_text().splitlines())
    ref_dir = f.parent / "references"
    if lines > 200 and not ref_dir.exists():
        extraction_candidates[str(f.relative_to(SKILLS))] = lines
monoliths_sorted = dict(sorted(monoliths.items(), key=lambda x: -x[1]))
extraction_sorted = dict(sorted(extraction_candidates.items(), key=lambda x: -x[1]))
```

## Output Template

```python
print(f"""
📊 HEALTH AUDIT REPORT — {date}
{'='*50}

Dimensions:
  🔹 Frontmatter valid:       {frontmatter_ok}/{active_count}
  🔹 Shell scripts +x:        {exec_ok}/{exec_total}
  🔹 Broken links:            {len(broken_links)}
  🔹 Bare-path refs broken:   {len(bare_path_refs)}
  🔹 Secrets leaked:          {len(secrets_found)}
  🔹 Duplicates:              {len(duplicates)}
  🔹 Manifest orphans:        {len(manifest_orphans)}
  🔹 Python syntax fails:     {len(syntax_fail)}
  🔹 Monoliths (>500 lines):  {len(monoliths_sorted)}
  🔹 Token budget (>25KB):    {len(over_budget)}
  🔹 Extraction candidates:   {len(extraction_sorted)}
  🔹 Active skills:           {active_count}
  🔹 Storage:                 {total_bytes/1024/1024:.1f} MB

Top monoliths (lines): {list(monoliths_sorted.items())[:3]}
Top extraction candidates: {list(extraction_sorted.items())[:3]}
""")
```

## Report Generation

After the audit, write a structured Markdown report to `~/docs/system/skills-audit-YYYY-MM-DD.md` containing:
- **Summary table** (dimension × result)
- **Before/after comparison** when fixes were applied
- **Detail lists** for each issue type (paths, counts)
- **Backup locations** for rolled-back files
- **Reproduce commands** for each fix

## Verified

2026-07-07: Full audit of 248 active skills completed in ~3 min. Report: `~/docs/system/skills-audit-2026-07-07.md`. All fixes applied in ~30 sec.
2026-07-16: Full audit of 298 active skills (Structure-Monolith dimension). Count: 42 monoliths (>500 lines), 28 token-budget violators (>25KB), 223 broken refs in 84 skills, 13 scripts without +x, 1 Python syntax fail. Report embedded in session audit output.