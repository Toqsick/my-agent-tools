# Thin-Note Expansion Pattern

Systematic method for transforming stub notes (< 40 lines) into encyclopedia-quality entries (target: 130+ lines).

## Proven 2026-07-06

Two thin notes were successfully expanded in this session:
- `05 Ressourcen/Pattern - Read-Patch-Retry.md` (34 lines → **146 lines**, +112 lines, +330%)
- `05 Ressourcen/Pattern - Fable-Tier-2.md` (36 lines → **132 lines**, +96 lines, +267%)

Both notes had the same problem: excellent concept, but no runnable code and no visual structure.

## The 5-Building-Block Template

Every expanded note should contain **at least these 5 blocks** in this order:

### Block 1 — Frontmatter Audit (additive)
If missing, prepend a YAML block:
```yaml
---
tags:
  - <tag1>
  - <tag2>
  - <tag3>
importance: 7
created: YYYY-MM-DD
letzter-review: YYYY-MM-DD
---
```

If existing, only ADD missing fields — never overwrite tags.

### Block 2 — Numbered Section Structure (not just # Title)

Replace "Alles in einem Block" structure with numbered sections:

| Section | Purpose | Min Lines |
|---|---|---|
| `## 1. Problemstellung` | Concrete pain point | 15 |
| `## 2. Lösung / Die Kernidee` | Mental model + decision tree | 20 |
| `## 3. Best-Practice-Implementierung` | **Runnable code** | 40 |
| `## 4. Häufige Fehler & Pitfalls` | 3-5 numbered items with fixes | 25 |
| `## 5. Verbindet zu` | Cross-cluster wiki-links | 10 |

### Block 3 — Runnable Code (the difference between stub and resource)

For Python patterns: write code with these features:
- Type hints on all functions
- Inline-comments in German (Basti's convention)
- Real-world imports (not toy stdlib examples)
- Error handling / retry logic visible in the snippet
- A realistic output or expected behavior description

For non-code patterns: use **ASCII diagrams** with `┌──┐` `│` `└──┘` borders. Example:

```
┌──────────────────────────────────────────────────────────────┐
│  1. READ FILE CONTENT                                          │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  2. GENERATE PATCH                                             │
└──────────────────────────┬───────────────────────────────────────┘
```

### Block 4 — Comparison Table (where applicable)

Pattern notes that compare options MUST have a markdown table:

```markdown
| Eigenschaft | Option A | Option B |
|---|---|---|
| Kosten | $0.50 / 1M tokens | $3.00 / 1M tokens |
| Latenz | 2-5s | 20-60s |
| Use-Case | Triage, Routing | Deep Reasoning |
```

### Block 5 — "Verbindet zu" with 5-7 Wiki-Links

Always include wiki-links to:
1. The parent MOC (e.g. `[[MOC - KI-Architektur]]`)
2. 1-2 sibling patterns
3. The Working Agreement if it touches operational policy
4. A real-world example note (proves the pattern is used)
5. A glossary entry for acronyms

## Anti-Patterns in Thin-Note Expansion

| # | Anti-Pattern | Mitigation |
|---|---|---|
| 1 | Padding with generic intro ("In this article we will explore...") | Delete — start with `## 1. Problemstellung` directly |
| 2 | Adding markdown tables without substance | Tables MUST contain real numbers/comparisons, not placeholders |
| 3 | Code without comments | All code gets German inline comments explaining WHY, not WHAT |
| 4 | Just duplicating the English Wikipedia article | Add Basti's specific operational context (which tooling, which file paths) |
| 5 | Linking only to MOC and nothing else | 5-7 outbound links is the floor; under that the note is still thin |

## Expansion Success Metric

A note is considered successfully expanded when:
1. `wc -l` ≥ 130 (was: < 40)
2. Contains at least one runnable code block OR one detailed ASCII diagram
3. Has 5-7 outbound wiki-links
4. Frontmatter has at least 3 tags + creation date
5. Section count ≥ 5

Run this check after each expansion:
```bash
wc -l <note.md>                          # ≥ 130
grep -c '^```' <note.md>                 # ≥ 2 (open + close of at least one block)
grep -c '\[\[' <note.md>                 # ≥ 5 outbound links
```

## When NOT to Expand

Some notes SHOULD stay thin:
- Daily notes (single-day lifecycle, no expansion needed)
- Index/TOC notes (MOCs are thin by design — they're tables, not prose)
- Template files in `_templates/`
- Quick-capture inbox items (will be processed into full notes later)

The thin-note heuristic must exclude these by name (see Pattern 9 in SKILL.md).