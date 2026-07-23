# Glossary Enrichment Pattern

> Systematic technique for expanding a vault glossary into a densely cross-linked reference hub. Proven technique from the 2026-07-05 session: Glossar went from **4 → 98 wiki-links** (~95 % of terms linked).

## When to Enrich the Glossary

- During **Phase 3 Cluster 3** (Cross-Link-Tiefe) — enrich Glossary first, then use its terms as link targets for all other "Verbindet zu" patches
- When the vault has ≥ 20 distinct acronyms/terms that appear in 3+ other notes
- When users struggle to find definitions for terms used across the vault

## Phased Expansion

| Phase | Action | Expected result |
|---|---|---|
| **1 — Categorize** | Group existing terms into 3–5 thematic sections (e.g. "System & Security", "KI & Agenten", "Vault & Obsidian", "Workflows & Patterns") | Order emerges from flat list |
| **2 — Add Definitions** | Ensure every term has a clear 1–2 sentence definition. Standardize definition style across sections. | Every entry is self-contained |
| **3 — Cross-Link** | Add a "Siehe auch" column or section to every table entry linking to the relevant resource note | Each term has ≥ 1 wiki-link to a content note |

## "Siehe auch" Column Technique

For glossary tables with many rows, add a dedicated column:

```markdown
| Akronym | Bedeutung | Siehe auch |
|---|---|---|
| AAA | Authentication, Authorization, Accounting — Security-Framework | [[Cybersecurity-Audit - Workflow]], [[Glossar#SSH]] |
| MOC | Map of Content — Navigations-Hub im Vault | [[Vault - Konzept & Wissensdatenbank]], [[Glossar#KI]] |
```

Benefits:
- Each row can link to **multiple** target notes
- Visually scan-friendly — users see immediately which notes to open
- Works with single-table and multi-table layouts

## Cross-Link Targets per Category

| Glossary Section | Typical link targets |
|---|---|
| System & Security | [[Cybersecurity-Audit - Workflow]], [[System-Wartung - Linux & Security]], [[Hardware - ERAZER 17 P1]] |
| KI & Agenten | [[Yuno - Identität und Stil]], [[MOC - KI-Architektur]], [[Subagent-Patterns - Delegation & Routing]] |
| Vault & Obsidian | [[Vault - Konzept & Wissensdatenbank]], [[Vault-Health-Metrics]], [[Templater - Setup-Anleitung]] |
| Workflows & Patterns | [[Mnemosyne - Patterns]], [[Working Agreement - Yuno Basti]], [[Queen-Bee-Metapher]] |
| Projekte | [[Github-MCP-Server]], [[Yuno-Voice-Bot]], [[Yuno-Cleaner]] |

## Glossary Positioning within Cross-Link Work

The Glossar should be the **first** note enriched in a cross-link pass, because every other note's "Verbindet zu" section can then link to `[[Glossar]] (AAA, MOC, … Akronyme)` — giving those notes a valid cross-link target immediately.

**Recommended order for a cross-link pass:**
1. Expand Glossar with "Siehe auch" column + new sections → creates all link targets
2. Patch **Vault-Phase-N-Plan** with links to Glossar + new resources
3. Patch **Vault-Health-Metrics** with Phase-specific metrics
4. Patch **MOC - Home** with new section entries + version bump
5. Patch **00 Knowledge Graph** with new cluster/size snapshot
6. Batch-patch thin notes with "Verbindet zu" sections (read tail → assess → add 4–7 links from decision framework)

## Pitfalls

- **Don't link everything to the same note** — vary targets across sections so each glossary section connects to a different cluster
- **Don't overlink common infrastructure notes** — `[[Glossar]]` and `[[Working Agreement]]` appear in almost every note's "Verbindet zu" section; this is okay but verify no note has 8+ links all pointing at the same 3 notes
- **Keep definitions concise** — 1–2 sentences maximum. If a term needs more depth, the linked resource note is the right place
- **Table row conflicts with concurrent editors** — see `references/subagent-coordination.md` Example 1 for the recovery pattern