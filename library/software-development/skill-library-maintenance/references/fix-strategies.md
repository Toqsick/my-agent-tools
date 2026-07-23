# Fix Strategies for Health Audit Findings

## Broken Markdown Links

**1-3 broken refs in workflow-linked inline text** → create the target file with minimal stub content

**4+ broken refs in pure "Siehe auch" / "Related" bullet-lists** → block-replace the entire list with `> **Note:**` line

**Broken refs inside Markdown tables** → create stub files (table structure must be preserved)

**Placeholder example paths** (e.g. `path/to/script.py`, `exact/path/to/file.py`) → convert to plain text, remove markdown link syntax

**Dangling absolute-system paths** (e.g. older vault references to `01-hardware/gpu-tuning.md`) → convert to plain text

## Missing +x on Shell Scripts

```bash
find ~/.hermes/skills -path "*/scripts/*.sh" -type f | grep -v ".archive" | xargs -I{} chmod +x {}
```

Idempotent and always safe.

## Manifest Orphans

Renamed skills: update old name → new name in manifest

Truly removed skills: remove line from manifest

Regenerate SHA manifest afterwards (see "Provenance Integrity" section)

## Manifest SHA Regeneration

```python
manifest_names = set()
for line in (SKILLS / ".bundled_manifest").read_text().splitlines():
    if ":" in line: manifest_names.add(line.split(":", 1)[0])
lines = []
for name in sorted(manifest_names):
    for skill_md in SKILLS.rglob(f"**/{name}/SKILL.md"):
        if _ok(skill_md):
            h = hashlib.sha256(skill_md.read_bytes()).hexdigest()
            lines.append(f"{h}  {name}")
            break
(SKILLS / ".bundled_manifest.sha256").write_text("\n".join(lines) + "\n")
```

## Fix Classification

| Finding | Default Action | Approval Needed? | Reversible? |
|---|---|---|
| Shell script without +x | `chmod +x` | No | Yes (backup) |
| Broken markdown link | Convert to plain text | No | Yes (git revert) |
| Manifest orphan | Remove/rename entry | No | Yes (backup) |
| SHA desync | Regenerate SHA | No | Yes (backup) |
| Real API key/secret | Report + mask | **YES** | Depends on leak scope |

## Report Template

```markdown
# 🔧 Hermes-Skills Audit Report — YYYY-MM-DD
**Scope:** `~/.hermes/skills/` (N active + M archived)
**Audit-Logik:** Read-only Diagnose + idempotente Fixes

## 📊 State Before Fixes
| Metrik | Wert |
|---|---|
| Frontmatter-Fehler | X von N |
| Permission-Probleme | X |
| Echte Secrets | X |
| Skill-Duplikate | X |
| Broken Symlinks | X |
| Broken Links | X |
| Manifest Orphans | X |
| Storage Total | X MB |

## 🟢 Befunde: ✅ Sauber (already healthy)
## 🟡 Behobene Issues
| Prio | Issue | Vor | Nach | Fix |
|---|---|---|---|---|
| 🟠 P2 | ... | X | 0 | `chmod +x` |

## 📂 Backups
## 📊 Post-Fix Status
```