# Atomic Write Race Prevention

> Concrete example of escaping the patch tool entirely for race-safe index.md
> and log.md updates. Proven during the Morpheus News Agent + Claude Design
> System Templates ingest (2026-07-17), where index.md and log.md were being
> edited by sibling subagents within a 16-second window.

## Problem

The `patch` tool is **read-then-write**: it reads the file, finds the
`old_string`, replaces it, and writes back. If a sibling subagent writes to
the same file between the read and the write, the patch lands on stale
content. The tool warns about this, but it still happens.

## Solution: Atomic Write via mkstemp + os.replace

Replace the patch-tool workflow with a Python script that:

1. **Reads** the file fresh
2. **Computes** the new content entirely in memory
3. **Writes to a temporary file** on the same filesystem (`tempfile.mkstemp`)
4. **Atomically replaces** the target via `os.replace` (which is `rename(2)`
   on Linux — atomic within the same filesystem)

Because the file is only **replaced once** at the end, there's no race window
between read and write. A sibling writing their own atomic write at the same
moment will produce last-write-wins semantics at the OS level, but neither
write will land on stale content.

```python
import os
import tempfile
from pathlib import Path

def atomic_write(path: Path, text: str) -> None:
    """Write text to path atomically. On Linux, os.replace is rename(2)
    which is atomic within the same filesystem. The temp file is created
    on the same filesystem as the target so rename doesn't cross devices."""
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",   # hidden file, same filesystem
        dir=path.parent,
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())  # force flush to disk
        os.replace(tmp_name, path)     # atomic swap
    finally:
        # Clean up temp file if os.replace failed
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
```

### Why this works

| Property | patch tool | atomic write |
|---|---|---|
| Read vs write | Separate calls, race window between them | Single call, no gap |
| Sibling detection | Warns post-hoc, requires re-read | Never sees stale state |
| Atomicity | File overwrite (non-atomic on Linux) | `rename(2)` atomic |
| Temp-file cleanup | N/A | `try/finally` unlink |

## Worked Example: Index + Log Update

This pattern was used during the Morpheus/Claude-DS ingest to update both
`index.md` and `log.md` without patch-tool races:

```python
def update_index(new_entries: list[str], marker_section: str) -> None:
    """Add entries under a section marker, recompute page count from filesystem."""
    text = INDEX.read_text(encoding="utf-8")

    # Add each entry if not already present
    for entry in new_entries:
        slug = re.search(r"\[\[([^|\]]+)", entry).group(1)
        if f"[[{slug}" in text:
            continue  # sibling already added it
        marker = f"\n### {marker_section}\n"
        if marker not in text:
            raise SystemExit(f"Marker not found: {marker.strip()}")
        text = text.replace(marker, f"\n{entry}\n{marker}", 1)

    # Count pages from filesystem (sidesteps sibling race on counter)
    count = curated_count()
    text = re.sub(
        r"> Last updated: \d{4}-\d{2}-\d{2} \| Total curated pages: \d+",
        f"> Last updated: {datetime.date.today()} | Total curated pages: {count}",
        text,
        count=1,
    )
    atomic_write(INDEX, text.rstrip() + "\n")


def update_log(marker: str, entry: str) -> None:
    """Append entry to log.md if marker not already present."""
    text = LOG.read_text(encoding="utf-8")
    if marker in text:
        return  # sibling already logged it
    atomic_write(LOG, text.rstrip() + entry + "\n")
```

### The `curated_count()` function

Instead of `old_count + new_pages = total` (which goes stale when a sibling
has already bumped the counter), count actual files on disk:

```python
def curated_count() -> int:
    """Real page count from filesystem — immune to sibling race on counter."""
    excluded_names = {"SCHEMA.md", "index.md", "log.md", "README.md"}
    count = 0
    for p in WIKI.rglob("*.md"):
        rel = p.relative_to(WIKI)
        if "raw" in rel.parts or ".git" in rel.parts or ".obsidian" in rel.parts:
            continue
        if p.name in excluded_names:
            continue
        count += 1
    return count
```

This returns `173` even when a sibling just bumped it from 60 to 173 while
you were computing your increment. It's always correct.

## When to Use vs When to Avoid

| Use atomic write when... | Use patch tool when... |
|---|---|
| Updating computed values (page counts, dates) | Simple string replacement in unique location |
| Adding multiple entries under different sections | One small text fix |
| Any write where the content is computed, not literal | Editing where old_string must be verified unique |
| File is shared with sibling subagents | File is exclusively owned by this agent |

## Signal That You Need Atomic Write

If you see any of these during consolidation:

```
⚠️ "modified by sibling subagent 'sa-...' at HH:MM:SS"
⚠️ "was last read with offset/limit pagination (partial view)"
💥 patch reported "Found 2 matches" — sibling inserted content nearby
```

That's the cue: switch to an atomic-write Python script for the rest of the
consolidation phase. Keep using `patch` for single-file, non-shared edits
(individual wiki pages), but route all shared-file writes (`index.md`,
`log.md`) through the atomic pattern.

## Comparison with Patch-Tool Race Recovery

The existing workflow (detection → re-read → retry patch) works but has a
diagnostic gap: the race is detected AFTER the patch is attempted. Atomic
writes **prevent** the race entirely rather than detecting and repairing it.
Use both strategies:

1. **Default to patch** for simplicity
2. **On first race warning, switch to atomic write** for all remaining
   shared-file updates in this consolidation phase
3. **Keep the detection loop** for cases where using patch is easier
   (single-entry log append)
