# Multi-Agent-Code-Audit Pattern for GreyScript Files

**Trigger:** Single-file GreyScript audit needed (P0-bug scan, refactor opportunities, optimization).

**Proven:** 2026-07-03 on YUNO V3 (52KB, 1 file, 1686 lines, 51 commands).

---

## Decision Tree

| Scope | Recommended Approach | Why |
|-------|---------------------|-----|
| **1 file, well-known patterns** (e.g. GreyScript src with .strip(), inline-then-return) | **Parent Pre-Scan + Parent-direct fix** | Subagent context-burn + dispatch overhead exceeds 5-10 focused calls |
| 1 file, unknown scope | Subagent with reduced briefing (1-2 questions, ≤5min) | Pre-Scan would miss edge cases |
| 3+ files | Subagent parallel (Hybrid Pre-Scan pattern) | Wall-clock savings from dispatch |
| Audit across whole project (50+ files) | Hybrid Pre-Scan + Subagent verifies | Pitfall #25 in action |

**Default for "audit this one .src file" = Parent Pre-Scan + Parent fix.** Subagents are overhead.

---

## Phase 0: Parent Pre-Scan (5-30 sec, deterministic)

```bash
FILE=/path/to/yuno_v3.src

# Size + structure baseline
wc -l "$FILE"
wc -c "$FILE"
greybel build "$FILE" -u  # baseline: must be exit 0

# Pattern-scan (3-5 grep calls max)
grep -cE "^cmd_(\w+)\s*=\s*\{\}" "$FILE"  # command count
grep -nE "\.strip\(\)" "$FILE"           # P0: .strip() bug
grep -nE "if .+ then return\b.*end if" "$FILE"  # P0: inline-then-return
grep -nE "exit\(\"" "$FILE"              # P0: exit() with msg in then
grep -cE "if not main_session\." "$FILE"  # P1: repeated patterns
grep -nE "indexOf\(.*\)" "$FILE"          # P1: indexOf pitfall (MiniScript returns index, not -1)
grep -cE "\t" "$FILE"                    # P2: tab/space mixing

# Save hit-list
mkdir -p ~/docs/system/
cat <<EOF > ~/docs/system/yuno-v3-prescan-2026-07-03.md
# Pre-Scan Results
- File: $FILE
- Lines: $(wc -l < "$FILE")
- Size: $(wc -c < "$FILE") bytes
- Build: $(greybel build "$FILE" -u 2>&1 | tail -1)
- cmd_X count: $(grep -cE "^cmd_" "$FILE")
- P0 patterns: [list from above]
- Repeated patterns: [list from above]
EOF
```

## Phase 1: Apply P0 Fixes (if any)

```bash
# Example: .strip() → manual trim-loop
# Patch via `patch` tool or targeted edit
# Build verify
greybel build "$FILE" -u  # must be exit 0
```

## Phase 2: Optional Subagent (only if scope unknown)

**ONLY if** Pre-Scan reveals more than ~5 P0/P1 findings OR scope is unknown.

```markdown
Briefing template (max 5 min time-budget):
- File: /path/to/file.src
- Pre-Scan: ~/docs/system/<pre-scan>.md (READ FIRST)
- Specific questions: [1-2 max, no "audit the whole thing"]
- Output: ~/docs/system/<scope>-expert.md
- MAX 5 calls. If you're not done in 5min, write what you have.
- AUTHORIZED EXCEPTION: greybel build (writes to /tmp/build/)
- DO NOT modify the source file — only report
```

**If subagent times out → Option 1 (Parent-direct)**, not re-spawn.

## Phase 3: Verify + Master-Report

```bash
# Build verify
greybel build "$FILE" -u

# DB verify (if DB was touched)
sqlite3 DB.db "PRAGMA integrity_check"  # must be "ok"

# Master-Report (3-Tier Verification)
cat > ~/docs/system/<scope>-multi-agent-2026-07-03.md <<EOF
## Verifikations-Matrix

| Step | Datei | Status |
|------|-------|--------|
| Parent Pre-Scan | prescan.md | OK (N findings) |
| P0-Fix (if any) | <file> | OK (build exit 0) |
| Subagent (if any) | expert.md | OK / TIMED OUT |
| Build | <file> | OK |
| DB | DB.db | OK |

## Findings Summary
- P0: N (all fixed)
- P1: N (cataloged for V2)
- P2: N (cataloged for V2)

## Wall-Clock
- Pre-Scan: 30 sec
- Fix: 1 min
- Verify: 30 sec
- TOTAL: 2 min
EOF
```

---

## YUNO V3 Audit — Real Numbers (2026-07-03)

| Metric | Subagent Approach | Parent-Direct Approach |
|--------|-------------------|------------------------|
| **Subagent dispatch** | 2 dispatched, 8Q + 5Q briefings | 0 subagents |
| **Wall-clock** | 70+ min (TIMED OUT, never completed) | 30 min total |
| **Findings** | 0 (no file written) | 18 findings in JSON |
| **P0-bug fixed** | No | Yes (.strip() → manual trim) |
| **Build verified** | No | Yes (exit 0) |
| **DB updated** | No | Yes (GreyHackDB.db) |
| **Master-Report** | No | Yes (6506 bytes) |

**Lesson:** When the scope is "find issues in this 50KB file" and parent can run `grep`, **parent wins**. Subagents add 70+ min of waiting for the same result in 30 min of focused parent work.

---

## Common GreyScript Audit Patterns (Phase 0 Cheat-Sheet)

| Pattern | Grep | Risk | Fix |
|---------|------|------|-----|
| `.strip()` not in MiniScript | `grep -nE "\.strip\(\)"` | P0 (real-game crash) | Manual trim-loop |
| Inline `if X then return Y end if` | `grep -nE "if .+ then return\b"` | P1 (greybel parser) | Multi-line block |
| `exit("msg")` in then-clause | `grep -nE "exit\(\""` | P1 (parser crash) | Separate `exit` line |
| `indexOf` returns null/-1 confusion | `grep -nE "indexOf"` | P1 (logic bug) | Use `hasIndex` for existence |
| Tab/space mixing | `grep -cE "^\t" FILE` | P2 (style) | Convert to consistent indent |
| Magic numbers (50, 1222, etc.) | `grep -nE "[0-9]{3,}"` | P2 (refactor) | Extract constants |
| `obj = main_session.object` repeated | `grep -c "obj = main_session.object"` | P2 (refactor) | Helper function |
| `is_folder` unreliable | `grep -nE "is_folder"` | P1 (off-by-one) | Use `is_binary == false` instead |

---

## Related

- See `greyhack-sandbox` SKILL.md Pitfall 16 (this pattern) and Pitfall 11/12 (the specific GreyScript bugs)
- `multi-agent-pitfalls-cheatsheet` Pitfall #30, #34 (the underlying principles)
- Master-Report template: see `references/savegame-storage-cleanup.md` for similar structure
