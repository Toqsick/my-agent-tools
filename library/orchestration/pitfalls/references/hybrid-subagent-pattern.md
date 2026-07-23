# Hybrid Subagent Pattern: Parent Pre-Scans, Subagent Verifies

**Key insight:** For tasks where the parent can do a **deterministic pre-scan** before spawning, do it. Don't make subagents do work the parent can do in seconds with `execute_code`.

## Pattern (proven with GreyHack bug-scan, Expert 3)

```
Phase 0: PARENT runs Python via execute_code → deterministic pattern-scan
         → produces curated hit-list (10-30 files) → ~/docs/.../pre-scan-results.md

Phase 1: PARENT spawns Expert 3 with briefing that REFERENCES pre-scan-results.md
         → Subagent reads the hit-list, does NOT scan from scratch
         → Subagent verifies 3-5 random findings, produces bug report

Phase 2: PARENT cross-checks subagent's verifications against own scan
```

## Why This Works

- Subagent scope drops from "118 files × 12 patterns" to "verify 20 pre-filtered hits"
- API-call budget for Expert 3: ~8 calls (vs. 50+ if scanning from scratch)
- Pitfall #25 (Batch > Subagents bei >20 Files) is the underlying principle
- Subagent provides **judgment** (false-positive vs. real bug), parent provides **measurement**

## When to Apply This Pattern

- Bug scans across many files (parent does regex, subagent verifies)
- Documentation completeness checks (parent lists files, subagent evaluates)
- Coverage audits (parent enumerates, subagent assesses quality)
- Dependency audits (parent runs `npm ls`, subagent prioritizes)

## When NOT to Apply

- Tasks requiring source-code reasoning (parent can't replace subagent's LLM)
- Single-file deep dives (no need for parent pre-work)
- Tasks where scope is unknown until explored (subagent must discover)

## Proven Impact

Validated on YUNO V3 (52KB, 1 file): pre-scan found P0-bug in 5 sec, applied fix in 1 patch, build verified in 30 sec. Total: 30 min wall-clock vs 70+ min and counting for 2 subagents.