# Batch Humanizer Swarm Pattern (2026-07-13)

16 Obsidian Daily-Notes humanisiert in ~5 Min Wall-Clock via 3-Wellen-Subagent-Swarm.
(3 Wellen x 6+6+3 = 15 Dateien, 1 parent-direct, 2 Overrides nötig)

Standalone reference — kombiniert humanizer + subagent dispatch.

## When

- 6+ files, same constraints (Em-Dash ≤1, Boldface=0, Inline-Header=0)
- Files are independent, 3–10 KB each
- Identical constraint set per file

## When NOT

- 1–2 files (parent-direct faster)
- Different constraint sets per file
- Shared content across files (parent-direct safer)

## Protocol

Phase 0 Scout: size + violation count per file
Phase 1 Dispatch: 3 waves a 6 tasks, identical briefing structure
Phase 2 Queen Verify: independent grep (DIFFERENT from bee's test)
Phase 3 Override: targeted patches for 🔴 files
Phase 4 Report: table with before/after

## Briefing Template (per bee)

```
Domain: <file-path> (<size> KB, <N> viol.)
Task: read_file → write_file → self-test → fix → re-test → report
Self-tests: grep -oE '\\*\\*[^*]+\\*\\*' file | grep -v '^#' | wc -l (=0)
            grep -c '—' (=1)  grep -c '^- \\*\\*[A-Z]' (=0)
Constraints: 0 Boldface, 1 Em-Dash, 0 Inline-Header, 0 Neg-Parallelism
```

## Verified Metrics (2026-07-13)

- 16 files in ~5 min (vs ~30 min sequential = 6x ROI)
- Bee pass rate: 14/16 (88%)
- Override rate: 2/16 (12%)
- Cost: 0 Euro (MiniMax-M3)
- Key failure: 1 bee claimed green but had 6 bold labels (see subagent-self-test-deception.md)