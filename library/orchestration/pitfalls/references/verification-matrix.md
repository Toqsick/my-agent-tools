# 3-Step Verifikations-Matrix

For each subagent, parent runs **three tiers** of verification — proven pattern from the 2026-07-02 demo session.

## Tier 1: Datei-Existenz

```bash
for i in 1 2 3; do
  FILE=~/docs/system/<audit>-expert$i-<scope>.md
  [ -f "$FILE" ] && echo "✅ Expert $i: exists ($(wc -l < $FILE) lines)" || echo "❌ Expert $i: MISSING"
done
```

## Tier 2: Content-Validierung

```bash
# Minimum sections, minimum table rows, concrete file:line references
grep -c "^## " <file>     # sections
grep -c "^| " <file>      # table rows
grep -cE "\| .*\.src \| [0-9]+" <file>   # concrete file:line refs in bug reports
```

## Tier 3: Realitäts-Check (CRITICAL — Pitfall #5 defense)

**Do not trust the report content — re-derive the answer independently:**

- Counts (lines, files): `wc -l` on actual file vs. claim
- Build outputs: re-run the build, compare numbers
- Bug findings: spot-check 3 random claims with `grep -n`

## Master-Report Pflicht-Section

```markdown
## Verifikations-Matrix

| Subagent | Datei | Lines | Sections | Realitäts-Check | Status |
|---|---|---|---|---|---|
| Expert 1 | path | N | N | check / N | OK / PARTIAL / FAIL |
| Expert 2 | path | N | N | check / N | OK / PARTIAL / FAIL |
| Expert 3 | path | N | N | check / N | OK / PARTIAL / FAIL |
```

**If any Tier fails, mark the corresponding finding as "PARTIAL — UNVERIFIED" in the synthesis.**

## The 3 "Always Verify" Patterns

After every subagent run, parent MUST check:

1. **File-existence check:** `ls -la <OUTPUT_PATH>` + `wc -l <OUTPUT_PATH>` — file actually written?
2. **Content check:** `grep -c "<Expert N>:" <OUTPUT_PATH>` — all 3 experts' content present?
3. **Claim verification:** For every "fixed" claim, run `read_file` / `terminal` / `hermes config get` to confirm.

**If any check fails → treat as unproven, parent executes the fix directly.**