# Subagent Coordination — Concurrent Vault Editing (2026-07-05)

> Two worked examples from the 2026-07-05 vault expansion sessions. Both illustrate the sibling-subagent conflict pattern, but at different scales and with different recovery strategies.

---

## Example 1: Phase 2 — Table-Row Conflict (Bereiche/Ressourcen MOCs)

### Setup

Parent agent read both MOCs (`04 Bereiche/_MOC.md`, `05 Ressourcen/_MOC.md`), then began patching. A sibling subagent (`sa-0-affa5f8d`) modified both MOCs in between, restructuring table columns and adding content.

### The Signal

```
_warning: /.../04 Bereiche/_MOC.md was modified by sibling subagent 'sa-0-affa5f8d' at 16:41:15 — after this agent's last read at 16:39:30. Re-read the file before writing.
```

**Crucial insight:** The `_warning` is advisory — the patch may still *succeed* against outdated content, producing unintended results (broken tables, deleted rows, duplicate rows).

### The Bug

After re-reading the Bereiche MOC, the parent patched with:
```
old_string: <original Dev-Work row + System-Wartung row + duplicate Dev-Work row>
new_string: <merged single Dev-Work row with new links>
```

This **deleted the entire System-Wartung row** because the sibling's table had different structure. The patch "succeeded" but data was lost. Fixing it required adding the row back in a second patch.

### Recovery Pattern (Phase 2)

```
1. PATCH fails or warns ──►
2. RE-READ the full file ──►
3. RE-IDENTIFY targets (sibling changed column count/headings/table format) ──►
4. RE-PATCH against fresh content ──►
5. VERIFY row/line count == expected ──► DONE
```

### Verification Checklist

| Check | What to look for |
|---|---|
| Expected row count | Table has same number of data rows as before + new rows, minus any you intended to remove |
| No orphan data | All existing references to the row you edited are gone (they shouldn't be) |
| Cross-reference integrity | Wiki-links from other resources to this file still resolve |
| Sibling didn't delete your writes | Check `write_file` results from earlier in session still exist |

---

## Example 2: Phase 3 — Section-Merge + Frontmatter Conflict (MOC-Home + Knowledge Graph)

### Setup

Parent agent was building Phase 3 Cluster 2 (new Themen-MOC "Lernen & Orchestration" + 4 satellites + 4 MOC patches). A sibling subagent (`sa-0-ad43d966`) was simultaneously working on another vault task.

Two files were hit by both agents:

| File | Parent edit | Sibling edit |
|---|---|---|
| `MOC - Home.md` | Version bump v3→v4, new MOC row, new Bereich row, Phase-3-status table | Various section improvements (not visible to parent at read time) |
| `00 Knowledge Graph.md` | v2.1→v3.0, 4th Themen-MOC, expanded cluster map | Merged Phase 2 + Phase 3 sections into unified "Phase 2 + 3" block, added new content rows, expanded frontmatter |

### The Signal

The `patch` tool did NOT warn for most targets — the sibling had already modified the file, but the file's on-disk content hadn't changed between parent's `read_file` and `patch` because the sibling's writes happened *before* the parent's first read. The damage emerged later as **structural duplication** — the patch matched an older section structure that no longer existed in its original form.

### The Damage

1. **Duplicate frontmatter in 00 Knowledge Graph.md**: The file had `---` ... `---` with 4 YAML lines (`zweck`, `version`, `themen-mocs`, `letzter-review`), and then a second `---` block with the same 4 lines (v2.1 line + v3.0 line side by side). Result: 3 `---` delimiters instead of 2.

2. **Missing Phase 3 status table**: The sibling had merged `## Phase 2 (Status)` and `## Phase 3 (Status)` into a single `## Phase 2 + 3 (Status)` with ~8 rows. Parent's patch targeted the old 2-section structure and deleted the sibling's new merged table.

3. **Duplicate Bereiche entry in 00 Knowledge Graph.md**: The ASCII cluster map showed a duplicate `Dev-Work` entry where `Lernen — Orchestration` should be — parent's patch matched a stale line number reference.

4. **Duplicate "Verbindet zu" entries**: Sibling added `[[MOC - Lernen & Orchestration]]` to the Verbindet-zu list; parent's patch targeting the old (shorter) list duplicated it.

### Full Recovery Sequence (Step by Step)

```python
# After each suspicious patch, this was the workflow:

# Step 1: Re-read full file
with open("MOC - Home.md") as f:
    content = f.read()
    
# Step 2: Count frontmatter delimiters
delimiter_count = content.count("---")
# If 3+ on a file that should have 2 → frontmatter is duplicated

# Step 3: Identify the section merge
for line in sorted(content):
    if line.startswith("## "): print(line)
# If expected sections are missing or renamed → sibling restructured

# Step 4: Plan multi-pass recovery
# Frontmatter fix:
#   old: <v2.1 lines> + <v3.0 lines> → new: <v3.0 lines only>

# Section fix:
#   old: Phase 2 section header + Phase 3 section header + old rows
#   new: merged Phase 2 + 3 header + all rows (parent + sibling + original)

# Row fix:
#   old: ASCII map with wrong cluster entry
#   new: ASCII map with correct 4-cluster set (Gaming, Dev, System, Lernen)

# Step 5: Patch in strict order
#   1 → Frontmatter
#   2 → Section header + table
#   3 → ASCII cluster map
#   4 → Verbindet-zu list
#   5 → Index size table

# Step 6: Re-verify after EACH patch
# Check: total_lines, line content at key positions
```

### Lessons Learned

| Lesson | Why it matters |
|---|---|
| **The absence of a `_warning` does NOT mean no conflict** | The sibling may have written before your first read. The stale data is in your cache, not on disk. |
| **Frontmatter is the most fragile part of a Markdown vault file** | Two agents adding YAML lines can easily produce 3+ `---` delimiters. Always check `---` count after the first patch. |
| **Section-merge is harder to detect than table-row conflict** | A merged section has a different `##` header. The old header no longer exists — but your patch's `old_string` may match a substring of the new merged header, producing a partial match and weird output. Always verify the full header line. |
| **Repair in order: frontmatter → sections → rows → footer** | Frontmatter issues cascade into every subsequent patch (wrong line numbers). Fix it first. |
| **Never trust a single-pass repair** | The 00 Knowledge Graph needed **5 patches** to recover fully. Expect multiple passes. |
| **Don't batch-read before patching** | Reading all target files first and then patching them sequentially increases the stale-read window. Read, patch, verify, then move to next file. |

### Root Cause

The parent and sibling were NOT spawned by the same orchestrator — they were **independent concurrent Hermes sessions** both operating on Basti's vault. There was no coordination mechanism between them.

This is the natural operational mode of Hermes's parallel agent system: agents are isolated but share a filesystem. The vault should be treated as a **shared resource with optimistic concurrency** — expect conflicts and design for detection/recovery, not prevention.

---

## Prevention Strategies Comparison

| Strategy | Cost | Protection Level | Notes |
|---|---|---|---|
| Sequential: parent writes first, then spawns subagent | High (serial) | Complete (no concurrent edits) | Only works within a single orchestrated multi-agent task |
| Path isolation: assign each subagent a non-overlapping folder set | Medium | High | Best for Phase 2/3 clusters with clear separation |
| Read-last: subagent reads on start, never mid-point | Low | Medium | Avoids stale-cache but not mid-air collisions |
| Post-hoc audit: re-read all touched files, verify integrity | Low | Medium-plus | Recommended as minimum — catches most structural damage |
| Multi-pass repair with in-order section verification | Medium (tool cost) | High | Require this in recovery spec; see Example 2 |

For Basti's vault (8 folders, ~70 notes): **path isolation for large operations + full post-hoc audit** is the best trade-off. For independent concurrent sessions (not orchestrated): **assume conflicts will happen and document the recovery pattern**.
