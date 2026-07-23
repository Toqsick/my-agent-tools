# Vault Architecture Guide — Worked Example (2026-07-05)

> This file documents the exact vault-build methodology used in the 2026-07-05 session. It serves as a reusable template for future vault expansions. All paths are examples; adapt them to the target vault.

## Starting Point

- Location: `/home/bratan/Dokumente/Obsidian Vault`
- Initial state: ~10 notes, 8 empty folders (Julian-Ivanov skeleton), no MOCs, no wiki-links
- Goal: 50+ notes, dense wiki-linking, MOC in every folder, Knowledge Graph visualisation

## Phase 1 Execution

### 1. Folder audit

```bash
cd "/home/bratan/Dokumente/Obsidian Vault"
for d in "01 Kontext" "02 Inbox" "03 Projekte" "04 Bereiche" "05 Ressourcen" "06 Daily Notes" "07 Archiv" "08 Anhaenge"; do
  echo "$d: $(find "$d" -name '*.md' 2>/dev/null | wc -l) Notes"
done
```

### 2. Read existing notes first

Read every note already in the vault before creating new ones. This ensures:
- Consistent tone/structure with existing content
- No duplicate coverage
- Wiki-links that actually resolve to real notes

Use `read_file` with `offset=1` and `limit=500` for each note. Batch parallel reads when possible.

### 3. Write cluster by cluster

Write notes in logical clusters, not alphabetically. Recommended order:

| Phase | Cluster | Why first |
|---|---|---|
| 1a | Kontext | Identity — defines everything else |
| 1b | Bereiche | Domains — scopes the projects below |
| 1c | Daily Notes | Timeline — anchors the knowledge |
| 1d | Ressourcen | Tooling — references for projects |
| 1e | Projekte | Active work — richest, most detail |
| 1f | Inbox | Open items, quick-capture template |
| 1g | Anhaenge | _README, conventions |
| 1h | Archiv | Existing history |
| 1i | MOC-Home + Knowledge Graph | Final integration hub |

### 4. Wiki-link every note

Every note must have at least 3 visible `[[Wiki-Links]]` in a `## Verbindet zu` or `## Wiki-Links` section at the bottom. MOC notes get 10+.

### 5. Vault inventory

After writing all notes, run the density check:

```python
import os, re
from pathlib import Path

vault = "/home/bratan/Dokumente/Obsidian Vault"
results = []
for root, dirs, files in os.walk(vault):
    if ".obsidian" in root or ".trash" in root:
        continue
    for f in files:
        if not f.endswith(".md"):
            continue
        full = os.path.join(root, f)
        with open(full) as fh:
            content = fh.read()
        wikilinks = len(set(re.findall(r"\[\[([^\]|#]+)", content)))
        lines = len(content.splitlines())
        rel = os.path.relpath(full, vault)
        results.append((wikilinks, lines, rel))

results.sort(reverse=True)
print(f"{'LINKS':>6}  {'LINES':>5}  NOTE")
for links, lines, note in results:
    print(f"{links:>6}  {lines:>5}  {note}")
```

### 6. Knowledge Graph visualisation

Create `00 Knowledge Graph.md` with:
- ASCII cluster map of all 8 folders
- Cross-cluster hot paths (arrows connecting related notes across folders)
- Reading routes table (question → which note)
- Index snapshot (total notes, links, avg density, top hub)
- Phase plan for next expansion

## Target Metrics (from Julian-Ivanov methodology)

| Metric | Healthy Target | Achieved 2026-07-05 |
|---|---|---|
| Total notes | 50+ content notes | 44 content + 10 MOC/README = 54 |
| Avg wiki-links/note | ≥ 3.5 | 4.1 |
| Median wiki-links/note | ≥ 3 | 3 |
| Top hub links | ≥ 20 | 24 (MOC - Home) |
| MOC coverage | Every folder | 8/8 folders |
| Tags | Growing taxonomy | 111 unique tags |
| Orphan notes | ≤ 2 | 0 verified |

## Cross-Cluster Hot Paths

The most frequently traversed connections in a healthy vault:

```
Hardware ──► NVIDIA-Tuning ──► Perf-Tuning Project
Profil ──► Working Agreement ──► Agent-Identity
Julian-Lessons ──► KI-Betriebssystem ──► Vault-Konzept
System-Bereich ──► Cron-Infrastruktur ──► Working Agreement
Gaming-Bereich ──► GreyHack-Werkzeugkasten ──► GreyHack-Projekt
```

## Inbox Note Template

```markdown
---
tags:
  - inbox
  - <relevant-tag>
eingang: YYYY-MM-DD
ttl: YYYY-MM-DD+7
---

# YYYY-MM-DD - <Title>

## Idee / Notiz

...
```

## Phase 2 Planning (suggested follow-ups)

| Option | Effort | Value |
|---|---|---|
| A) Templater automatisieren (Auto-Daily-Note) | 1h | ⭐⭐⭐ |
| B) Projekt-Stubs füllen aus echten READMEs | 1.5h | ⭐⭐⭐ |
| C) Themen-MOCs (Gaming-Performance, KI-Modell-Mapping, Cron-Ops) | 45min | ⭐⭐ |
| D) Verwaiste-Notes-Audit + Backlinks-Chain-Check | 30min | ⭐⭐⭐ |
| E) Subagent-Cluster: 3 Spawns parallel | 1h | ⭐⭐⭐⭐ |

## Reusable Scripts

After this session, the following automation was extracted into `scripts/` under the `vault-architecture` skill:

| Script | Purpose | Invocation |
|---|---|---|
| `check-broken-wiki-links.py` | Scans vault for broken wiki-links + markdown links, with alias resolution and placeholder exclusion | `python3 scripts/check-broken-wiki-links.py <vault-path>` |
