# Sibling-Agent Race — Defensive Write Strategy

> Real session transcript: two parallel wiki-ingest agents collided on
> index.md / log.md writes.
> Session date: 2026-07-17 | Context: Hermes-V7 architecture scout

## What Happened

Two independent wiki-ingest processes ran concurrently:

- **This agent (Hermes-V7 scout):** Read 7 raw files → wrote 4 wiki pages → 
  attempted to update index.md and log.md
- **Sibling subagent `sa-0-64f68347` (Wave 2 scout):** Reading Perplexity
  research → writing entities (hermes-agent, mnemosyne, ollama, etc.) →
  also updating index.md and log.md

Both targeted the **same two files** at the **same time**.

## Timeline

```
T0  Agent A reads index.md, log.md (old state, 8 pages)
T0  Agent B reads index.md, log.md (old state, 8 pages)
    [both agents write their 4 wiki pages — no conflict, different paths]
T1  Agent B writes index.md — expands from 8 to 15+ page entries
T1  Agent B writes log.md — adds Wave 2 entry
T2  Agent A writes log.md — PATCH succeeds at top (appends to start)
T2  Agent A writes index.md — PATCH FAILS: "modified by sibling subagent 'sa-0-64f68347'"
T3  Agent A re-reads index.md — sees Agent B's content already there
T3  Agent A re-evaluates: "my 4 pages are already indexed by sibling → no-op"
```

## Key Observations

| Observation | Implication |
|---|---|
| `log.md` patch succeeded despite race | Appends-to-beginning are **append-safe** even during concurrent writes — the patch tool verified its `old_string` matched the original top of file |
| `index.md` patch failed because sibling changed the full structure | Full-section replacements are **fragile** — Agent B added entities, concepts, lessons sections that changed the file shape entirely |
| Re-read → re-evaluate → confirmed sibling already did the work | The correct response is NOT to force the write, but to accept the conflict and move on |
| Both agents produced valid, non-overlapping content | The race was on **index/log metadata only**, not on wiki page content — because each agent wrote to different page paths |

## Defensive Write Checklist

When `patch` returns a sibling-agent warning on index.md or log.md:

- [ ] **Do not retry blindly** — the sibling's content may already subsume yours
- [ ] **Re-read the file** — `read_file(~path/to/file)`
- [ ] **Re-evaluate**: does my update still need to happen?
  - If sibling already added an entry pointing to your page: **skip** (done)
  - If sibling's content overlaps but misses details: re-patch with fresh anchor
- [ ] **For log.md**: append is usually safe — check if the entry actually landed
  (my log entry landed successfully even during the race)
- [ ] **For index.md**: prefer single-line inserts near a stable section header
  over full-section replacements to reduce collision surface
- [ ] **Verify final state**: read the file one more time after resolving

## Prevention (for future orchestrators)

- Pin index.md writes to **Phase 4 only** (already in SKILL.md)
- **Stagger** parallel agents that share write targets — add a 5-second
  random jitter before index/log writes
- Use a **write-token**: a marker comment line like `<!-- Lock: ingesting -->`
  at the top of index.md that agents check before touching
- When running N parallel scouts: let ONE designated agent (the slowest or
  the one with the most pages) own the merge
