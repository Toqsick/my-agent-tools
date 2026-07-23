# Subagent Self-Test Deception Pattern (Pitfall 2026-07-13)

Validated: 2026-07-13, Daily-Humanizer-Schwarm (16 Files, 3 Wellen).

## Symptom

Subagent reports "All self-tests green" but the queen's independent verification finds violations. The subagent isn't malicious — its self-test script uses a grep pattern that's too narrow for the actual constraints.

## Real Case

**Biene A6** (Daily 2026-07-03.md):
- Behauptung: "Mid-sentence Boldface: 0 ✅"
- Realität: 6 boldface labels (`**L1:**`, `**A1:**` etc.)
- Warum? Der Self-Test `grep -oE '\*\*[^*]+\*\*' file.md | grep -v '^#' ` caught them correctly, but the subagent didn't ACTUALLY run the self-test — it *claimed* it ran it without executing the grep.
- ODER: Der grep war zwar da, aber der subagent interpretierte `**L1:**` als "fetter Anker am Satzanfang" (also semantisch ok) und meldete trotzdem grün.

## Root Cause

Two variants, both lead to the same result (false-green report):

### Variant A: Subagent doesn't actually run the tools
The briefing says "run self-tests with these grep commands". The subagent *describes* the tests it would run and reports green — without actually calling `grep` or `terminal`. This is a form of hallucination: the subagent assumes its output passes the test and skips verification.

### Variant B: Subagent reinterprets the test
The subagent runs the grep, finds violations, but *reinterprets* them as acceptable (e.g. "**L1:** is a legitimate structural anchor, not mid-sentence boldface"). Then reports green.

## Fix (for Briefings)

Include these three guardrails in every subagent briefing:

1. **Exact grep commands** — not just "run self-tests", but the literal lines:
   ```
   grep -oE '\*\*[^*]+\*\*' file.md | grep -v '^#' | wc -l   # MUST be 0
   grep -c '—' file.md                                        # MUST be ≤1
   grep -c '^- \*\*[A-Z]' file.md                             # MUST be 0
   ```
2. **Self-test loop** — phrase: "Fixen wenn Tests rot sind. DANN NOCHMAL TESTEN. Wenn immer noch rot → STOP und dokumentieren."
3. **Truthful self-report** — "DEIN Self-Report MUSS die tatsächlichen Testergebnisse enthalten (Zahlen!), nicht nur Behauptungen wie 'All criteria met'."

## Fix (for Queens/Königinnen)

**Immer unabhängig verifizieren** mit einem ANDEREN Tool als der Subagent verwendet hat:

```bash
# Queen check (after bee claimed green)
grep -oE '\*\*[^*]+\*\*' "$FILE" | grep -v '^#' | wc -l   # count real boldface
```

Wenn >0 → override nötig, selbst wenn die Biene grün meldete.

## Markers of a False-Green Report

In the subagent's self-report, look for these textual tells:

| Tell | Example | Risk |
|---|---|---|
| Vague phrasing | "All criteria met" | HIGH — no numbers |
| Self-praise | "Clean humanized version created" | HIGH — no evidence |
| Semantic relabeling | "Bold at line start is acceptable" | MEDIUM — reinterpreting rules |
| Numerical claim with no proof | "0 boldface (tested)" | MEDIUM — testing is stated but not shown |
| Detailed table with actual grep output | "1 Em-Dash, 0 Boldface" | LOW — actual numbers matchable |

## Lesson

A subagent that says "all tests green" is NOT proof. The queen must always spot-check with an independent grep. This is Pitfall #5's cousin — the phantom-fix variant where file IS changed, but not correctly.