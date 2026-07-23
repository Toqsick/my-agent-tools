# Parallel Ingest Race Incident — 2026-07-17

> Concrete transcript of a real sibling-subagent race that occurred during
> parallel ingest of Hermes-Agent-Docs Cluster A alongside other cluster
> ingests into Basti's tri-domain wiki. Use as a troubleshooting reference.

## Timeline

| Time | Event |
|---|---|
| ~12:06:17 | Agent reads `log.md` — sees 357 lines, a clean view of the current state |
| ~12:06:33 | Sibling subagent `sa-4-41f0286d` writes to `log.md` (388 lines, new entry) |
| ~12:06:40 | Agent runs `patch` on `log.md` — tool warns: *"modified by sibling subagent 'sa-4-41f0286d' at 12:06:33 — after this agent's last read at 12:06:17"* |
| ~12:06:45 | Agent re-reads `log.md`, verifies the patch still applied correctly (it did, because the sibling added content *after* the patched region) |
| ~12:07:00 | Agent patches `index.md` page count — tool warns *"was last read with offset/limit pagination (partial view)"* because the initial read used offset=1, limit=35 |
| ~12:07:05 | Agent re-reads `index.md` fully, re-syncs page count to `127` (sibling had bumped from 40) |

## Root Cause

**Three concurrent race conditions stacked:**

1. **Shared-file race on `log.md`** — sibling wrote to the same file within a
   16-second window after the agent's read. The patch's `old_string` was above
   the insertion point so it survived, but the tool still flagged the stale read.

2. **Shared-file race on `index.md`** — sibling had already updated the page
   count from 40 to 127 while this agent cached the old value from the index
   orientation phase.

3. **Partial-read / pagination race on `index.md`** — the initial `read_file`
   with `offset=1, limit=35` triggered a "partial view" warning when `patch`
   was later called on the same file, even though no sibling had touched
   `index.md` in that specific window.

## How Each Was Resolved

| Race | Detection | Resolution |
|---|---|---|
| Shared-file (log.md) | Tool's sibling-modification warning | `read_file` again, confirm patch still valid, continue |
| Shared-file (index.md) | Page count was wrong (`40` vs real `127`) after reading stale cache | `read_file` full file → compute increment from actual current count |
| Partial-read (index.md) | Tool's `"was last read with offset/limit pagination"` warning | `read_file` full file (no offset/limit) → redo patch |

## Derived Lessons

### 1. Always re-read immediately before writing

```diff
- # Read at start of phase (BAD — goes stale)
- current = read_file("index.md")
- # ...20 minutes of ingestion work...
- patch("index.md", old_string="40", new_string="47")  # WRONG — sibling may have changed it

+ # Read immediately before first write (GOOD)
+ # ...20 minutes of ingestion work...
+ current = read_file("index.md")  # fresh snapshot
+ patch("index.md", old_string=str(old_count), new_string=str(new_count))
```

### 2. Offset/limit reads cannot be used as patch anchors

If you read `index.md` with `offset=1, limit=35`, the tool tracks that as a
partial view. A later `patch` on the same file fires the partial-view warning
regardless of whether siblings were involved. **Always do a full read before
writing**, even when the file is large.

### 3. Sibling races propagate silently

The `log.md` sibling race was detected immediately (tool warning). But the
`index.md` page-count race was **silent** — no tool warning, no error. The
wrong value made it into a `patch` call and was only caught because the
subsequent validation (`git diff --check`, final lint) revealed the mismatch.

### 4. `git diff --check` as an after-patch safety net

After all patches, the sibling's log.md entry had introduced a trailing
blank-line-at-EOF issue that `git diff --check` caught:

```
log.md:388: new blank line at EOF.
```

Fix: `p.read_text(); p.write_text(s.rstrip() + '\n')` normalizes EOF.

### 5. The 16-second window

The entire race window was **16 seconds** (12:06:17 → 12:06:33). During peak
ingest with 4+ parallel scouts, expect multiple such windows to overlap.
Treat index.md and log.md writes as **critical sections** — batch all changes
into the minimum number of patches and re-read between every batch.

## Prevention Checklist

Before the consolidation phase of any parallel ingest:

- [ ] Re-read `index.md` fully (no offset/limit)
- [ ] Re-read `log.md` fully
- [ ] Verify page count matches `find ... | wc -l`
- [ ] Batch all index changes into 1–2 patches (not one per entry)
- [ ] After consolidation, run `git diff --check`
- [ ] After consolidation, run `git add -A && git commit`

---

## Variant 2: Filename-Collision Overwrite (2026-07-17)

> Second race class discovered during Hermes-Agent-Docs parallel ingest.
> Unlike Variant 1 (shared-file collision on index.md/log.md), this is a
> **file-content overwrite** — sibling creates a STUB file with the exact
> same filename as your substantive page.

### How It Manifests

1. Agent writes a substantive file (6 KB, ~120 lines) at 12:02.
2. Sibling subagent working on a different domain cluster writes a stub file
   (1 KB, ~20 lines) with the SAME filename at 12:03.
3. The sibling's write happens AFTER the agent's write, so the sibling's
   version wins on disk. The agent's 6 KB content is gone.
4. `ls -la` shows one file with the sibling's timestamp:
   ```
   -rw------- 1 bratan bratan 1153 Jul 17 12:03 hermes-telegram-setup.md
   ```
   The agent's 6196-byte version from 12:02 is no longer on disk.

### Detection: Timestamp Comparison

```bash
# Compare birth time (%W) vs modification time (%Y)
stat --format='%W %Y %n' wiki/concepts/hermes-telegram-setup.md
# %W = original creation time (file birth)
# %Y = last modification time

# If birth time < mod time by more than 1 minute AND the file size
# is smaller than expected, the file was overwritten by a sibling:
if [ "$(stat -c%W file.md)" -lt "$(($(stat -c%Y file.md) - 60))" ]; then
    echo "SUSPECT: file was modified after creation"
fi
```

Alternatively, compare file sizes against what you wrote. If you wrote
~6 KB and the file is now ~1 KB, you've been overwritten.

### Recovery Strategy

1. **Detect early**: run `ls -la` on your output files after the initial
   write pass, before the consolidation phase. Note which ones got smaller.

2. **Rewrite once**: overwrite the stub with substantive content. Do NOT
   fight recursively — if you rewrite and the sibling rewrites again, you
   enter an escalation loop.

3. **Let the sibling's consolidation commit capture your content**: When
   the sibling agent runs `git add -A && git commit` at the end of its
   ingest pass, git picks up whatever is on disk at commit time. If your
   rewrite landed after the stub but before the commit, your content wins.
   This is the key insight: **last-write-wins at the file level** is
   resolved by the consolidation commit, not by fighting over intermediate
   patches.

4. **Verify**: after the sibling's commit, `git show HEAD:<path>` on each
   contested file — confirm the correct version landed.

### Why This Happens

The agents operate in parallel on disjoint domains but write to the SAME
directory tree. When both domains independently decide a page should exist
(e.g., both the Cluster C scout and the Cluster D scout create
`hermes-telegram-setup.md`), one will overwrite the other — regardless of
domain ownership.

### Prevention

- **Domain-aware filename prefixing**: add the cluster/domain tag to
  filenames when there's overlap risk (`cluster-c-telegram-setup.md`).
- **Check before write**: `if [ -f "$file" ] && [ "$(wc -c < "$file")" -gt 500 ]; then skip; fi`
- **Detect race in consolidation phase**, not in write phase: flag
  unexpected size reductions and re-verify during consolidation.
