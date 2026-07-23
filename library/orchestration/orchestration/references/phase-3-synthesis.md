# Phase 3: Synthesis — Detailed Procedures

Phase 3 sub-procedures: 3.5 Critical-Cross-Check and 3.6 User-Anker Decision.
Loaded from `multi-agent-orchestration` SKILL.md §"Phase 3".

## Base Synthesis (Phase 3)

1. Deduplicate overlapping recommendations
2. Conflict-check fixes
3. Verify subagent claims (re-run measurements)
4. Identify blocking dependencies
5. Prioritize: P0 (today), P1 (this week), P2 (next week), P3 (nice-to-have)

---

## Phase 3.5: Critical-Cross-Check (PROVEN 2026-06-30)

**Wann:** Nachdem die 3 Scout-Reports eingetroffen sind, **BEVOR** du irgendwas fixest oder Optionen anbietest.

**Was:** Cross-Checke die kritischsten Self-Reports der Scouts gegen deine eigenen Quellen — `grep`, `cat`, `file_read`, `terminal`. Pitfall #5 sagt "verify EVERY claim" aber zeigt nicht WIE.

### Bewährter Workflow (proven mit Hermes-V7-SSE Meta-Eval 2026-06-30)

```bash
# 1. Scouts returnten (owl-alpha, ~5min)
# 2. Parent empfängt 3 Reports gleichzeitig

# 3. KRITISCHSTE 3-5 Claims pro Scout rauspicken (P0-Bugs mit konkretem Fix)
#    NICHT alle — Fokus auf was du WIRKLICH fixen willst
#    NICHT nur Summary — P0 sind die detaillierten Behauptungen

# 4. PRO CLAIM: Single-grep-Verifikation im echten Code
grep -nE 'id="filterAll"' packages/hermes-sse/dashboard/hermes-sse-dashboard.html
# → Scout-1 behauptete "Doubled-IDs" → verifiziert: filterAll in Z.759+929 = echt

# 5. Synthese-Tabelle bauen mit Verifikations-Status
#    ┌───────────────────────────────┬──────────┐
#    │ Scout-Claim                   │ Verified │
#    ├───────────────────────────────┼──────────┤
#    │ Filter-Pills Doubled-IDs      │ ✅ grep  │
#    │ Theme ohne Persist            │ ✅ grep  │
#    │ Sidebar kein Mobile-MQ        │ ✅ grep  │
#    │ hookSSE Race alle 500ms       │ 📋 skip  │  ← zeitaufwendig, defer
#    │ PUT lanes ohne Validation     │ ✅ grep  │
#    └───────────────────────────────┴──────────┘

# 6. Erst dann entscheiden welche 3-5 echten Fixes du anbietest
#    User sieht: 3 verifiziert + 2 später relevant
```

### Wichtig (Lesson 2026-06-30)

- **Nicht alle Claims verifizieren** — nur die P0-P1 die du wirklich umsetzen willst. Andere Scout-Insights landen in `~/docs/system/<eval>.md` als spätere-Backlog-Items
- **Snapshot-Pattern**: 3-5 parallele greps vor dem Fix, dann Fix, dann Verify dass der gleiche grep jetzt anderes zeigt
- **Bei AMBIGUOUS scout claims** (z.B. "Polling-Race" — komplexer zu greppen): zurückstellen mit "📋 später" statt raten
- **Phantom-Fix-Pattern vermeiden**: Wenn du einen Scout-Claim nicht verifizieren kannst, aber trotzdem fixen "musst" — wahrscheinlich Phantom-Fix. Lieber mit User-Rückfrage entscheiden.

### Parent-Direct-Cross-Check als eigene Phase anerkennen

Die Phase 2 ("Immediate Fixes") bleibt, aber wenn Scouts liefern sollte Phase 3.5 (Cross-Check) **IMMER** zwischen Phase 3 und 4 stattfinden. Direkt zwischen "Reports kommen rein" und "Fixes anwenden".

---

## Phase 3.6: User-Anker vs Scout-Fix-Decision (PROVEN 2026-06-30)

Bei "Was als nächstes?" nach Scout-Synthese NICHT 5+ Fixes vorschlagen, sondern:

1. **2-4 Cross-Check-erfüllte Fixes mit Aufwand/Nutzen-Score**
2. **1-2 "verifiziert später"-Items aus Cross-Check**
3. **User entscheidet** was als nächstes (oder "Phase X angehen")

### Beispiel aus 2026-06-30 Hermes-V7-SSE Meta-Eval

- 3 echt-verifizierte Frontend-Bugs (Filter-Doubled, Theme-Persist, Sidebar-MQ)
- 1 zurückgestellt: trust-proxy (eigener Sprint QF-5)
- 1 zurückgestellt: PUT-Validation (Lane-Route-Refactor, größer)
- 1 ergebnis-offen: hookSSE Race (komplexer, C-4 SSE-Refactor)

User pickt QF-4 (die 3 verifizierten Fixes) → 1 Stunde Sprint. Sauberer als "mach mal alle 5".

---

## Verifikations-Matrix (Pflicht-Section im Master-Report)

For each subagent, parent runs **three tiers** of verification — proven pattern from the 2026-07-02 demo session:

### Tier 1: Datei-Existenz

```bash
for i in 1 2 3; do
  FILE=~/docs/system/<audit>-expert$i-<scope>.md
  [ -f "$FILE" ] && echo "✅ Expert $i: exists ($(wc -l < $FILE) lines)" || echo "❌ Expert $i: MISSING"
done
```

### Tier 2: Content-Validierung

```bash
# Minimum sections, minimum table rows, concrete file:line references
grep -c "^## " <file>     # sections
grep -c "^| " <file>      # table rows
grep -cE "\| .*\.src \| [0-9]+" <file>   # concrete file:line refs in bug reports
```

### Tier 3: Realitäts-Check (CRITICAL — Pitfall #5 defense)

**Do not trust the report content — re-derive the answer independently:**
- Counts (lines, files): `wc -l` on actual file vs. claim
- Build outputs: re-run the build, compare numbers
- Bug findings: spot-check 3 random claims with `grep -n`

### Master-Report Pflicht-Section

```markdown
## Verifikations-Matrix

| Subagent | Datei | Lines | Sections | Realitäts-Check | Status |
|---|---|---|---|---|---|
| Expert 1 | path | N | N | check / N | OK / PARTIAL / FAIL |
| Expert 2 | path | N | N | check / N | OK / PARTIAL / FAIL |
| Expert 3 | path | N | N | check / N | OK / PARTIAL / FAIL |
```

If any Tier fails, mark the corresponding finding as **"PARTIAL — UNVERIFIED"** in the synthesis.

---

## Aborted-Delegation Recovery (NEW 2026-07-02)

When 1+ subagent times out (Pitfall #19/#30), the parent has **4 recovery options** instead of "re-spawn with same briefing":

| Option | When | Pro | Con |
|--------|------|-----|-----|
| **1. Parent-direct targeted calls** (RECOMMENDED) | Small scope (3-5 calls worth) | Better context visibility, can bail early | Parent context bloats |
| **2. Re-spawn with reduced briefing** | Medium scope with depth needed | Lower timeout risk | May miss depth |
| **3. Hand off to different model** | Critical scope worth re-attempting | Different failure mode | Token cost + extra coordination |
| **4. Skip and document** | Large scope, low ROI for retry | Fast | Incomplete audit |

**Default:** Option 1 (parent-direct) if the scope is small. Option 4 if the scope is large. Document the choice in the master report.

### Master-Report Section

```markdown
## Delegation Recovery Log
- Expert 2: completed in 4min 12s
- Expert 1: completed in 5min 47s
- Expert 3: TIMED OUT at 600s, 14 API calls, no file → PARENT OVERTOOK (Option 1)
  - Parent direct calls: 4 calls, 1min 23s, output integrated into this report
```