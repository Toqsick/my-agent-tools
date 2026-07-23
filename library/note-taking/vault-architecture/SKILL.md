---
name: vault-architecture
description: >-
  Use when user asks for structuring or expanding an Obsidian vault, creating Maps of Content, improving cross-links and note discoverability, running broad vault health checks, or designing daily-note or template workflows. NOT for editing one note or performing only a backlink-orphan audit. Applies folder schemas, MOC patterns, graph checks, phase workflows, content gates, glossary enrichment, and conflict-safe coordination.
platforms:
- linux
- macos
- windows
version: 1.9.0
author: Yuno (Basti)
lane: worker-flash
reasoning_effort: high
license: MIT
trigger_keywords: ['note', 'vault', 'content', 'checks', 'workflows']
keywords: ['note', 'vault', 'content', 'checks', 'workflows']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['obsidian-vault-cluster-operations', 'vault-skill-derivation', 'obsidian']
---


# Vault Architecture

> Architectural counterpart of the `obsidian` skill (file-tool operations). Covers **design and methodology**: what goes where, how to wire notes together, how to measure health.

## Trigger Conditions

- "Build/restructure/fill my vault"
- "Create MOCs" / "Maps of Content"
- "Connect my notes better" / "More wiki-links"
- "Vault inventory" / "Vault health check"
- "Phase 2/3/7/8/10/11/15" of vault expansion
- "Templates" / "Templater" / "Vorlagen"
- "Setup guide" / "Anleitung" / "Style Settings" for Obsidian plugins
- "Cross-link cleanup" / "Backlink audit"
- "Daily note workflow"

## Core Principles

1. **Every note earns its place** — no empty stubs; each note has ≥ 3 outgoing wiki-links
2. **Every folder has an MOC** — `_MOC.md` or `MOC - <topic>.md` at root lists contents
3. **MOC-Home as central hub** — `MOC - Home.md` links to every folder-MOC
4. **Link density ≥ 3** — target 3–5 outgoing wiki-links per content note; MOCs get 10+
5. **Inbox has 7-day TTL** — process into Projekte/Bereiche/Ressourcen or Archived
6. **Waben-Metapher (kanonisch seit 2026-07-09)** — Das Vault ist ein **Bienenstock**, die strukturierten Speicher-Zellen sind **Waben** (MOCs, Folder-Schema, Wiki-Link-Graph), der **Honig** ist die verdichtete Information. Die **Bienenkönigin + Schwarm** (Yuno + Subagenten) arbeiten im Stock: füllen Waben mit Honig, sorgen für Verbund. Jede neue Note muss fragen: "Bin ich Honig in einer Wabe, oder ein Fremdkörper?"

## Julian-Ivanov 8-Folder Schema

```
01 Kontext/      — Identity: user profile, agent identity, hardware, working agreements
02 Inbox/        — Transient: new ideas, open items, quick-capture (7-day TTL)
03 Projekte/     — Active projects: one subfolder per project
04 Bereiche/     — Life domains: gaming, dev-work, system-wartung
05 Ressourcen/   — Knowledge base: tool guides, references, glossars
06 Daily Notes/  — Timeline: one YYYY-MM-DD.md per day + _MOC
07 Archiv/       — History: completed projects, stale reports
08 Anhaenge/     — Binary assets: _README with linking conventions
```

## MOC Pattern

Every MOC file contains:
- Title: `# _MOC — <Folder Name>`
- Purpose: Map of Contents for this folder
- Notes list: Dataview query or manual table
- Key connections: Links to `[[MOC - Home]]` and related MOCs

## Quick Health Checks

| Check | Tool | Target |
|---|---|---|
| Total notes | `find . -name '*.md' \| wc -l` | Growing |
| Wiki-link density | See → [Wiki-Link Density](references/wiki-link-density-python.md) | Avg ≥ 3.5 |
| Top hub | MOC-Home links count | ≥ 20 links |
| MOC coverage | Every folder has `_MOC.md` | 8/8 |
| Orphan notes | Notes with 0 inbound links | ≤ 2 |
| Inbox age | Oldest untriaged Inbox note | ≤ 7 days |
| Broken links | `[[Non-Existent Note]]` count | 0 |

## Knowledge Graph Visualisation

Create `00 Knowledge Graph.md` (root) with:
- ASCII cluster map showing 8 folders
- Hot path arrows for most-traversed connections
- Reading routes table (question → which note to open)
- Index size snapshot (notes, links, avg density, top hub)
- Phase plan for next expansion

## Vault Phases (Quick Reference)

| Phase | Focus | Key Actions | Reference |
|---|---|---|---|
| **1** | Skeleton | Build 8 folders, MOCs, basic templates | - |
| **2** | Templater + Subagents | Create templates, dispatch 3 parallel subagents | [Phase 2 Verification](references/phase2-verification.md) |
| **3** | Content Depth | Fill thin notes, new Themen-MOCs, densify links | [Phase 3 Workflow](references/phase3-workflow.md) |
| **4** | Plugin Prerequisites | Check `.obsidian/` config, Dataview status | [Phase 10](references/phase10-workflow.md) |
| **5** | CSS Visual Theming | Create snippets, Yuno color palette, Style-Settings integration | [Phase 10](references/phase10-workflow.md) · [Style-Settings](references/style-settings-integration.md) |
| **5.5** | Graph + Sanctum | Fix graph.json colors, CSS override | [Phase 5.5](references/phase55-workflow.md) |
| **7** | Gemini Cross-Link | Automated wiki-link expansion via `--yolo` | [Phase 7](references/phase7-workflow.md) |
| **8** | Design Rework | CSS snippets, MOC standardization | [Phase 8](references/phase8-workflow.md) |
| **10** | Infrastructure | Backup discipline, plugin management, Yuno-Dashboard | [Phase 10](references/phase10-workflow.md) |
| **11** | Cron Automation | Daily notes, weekly digests, Mnemosyne-Sleep | [Phase 11](references/phase11-workflow.md) |
| **15** | External Import | Systematic `.md` import + networking | [Phase 15](references/phase15-workflow.md) |

## Daily Notes

- **Format**: See → [Daily Note Format](references/daily-note-format.md)
- **Rich Format (emojis, Sektionen, Reflexion)**: See → [Rich Daily Note Template](references/rich-daily-note-template.md)
- **Reconstruction**: See → [Daily Note Reconstruction](references/daily-note-reconstruction.md)
- **Anti-AI-Tells**: Before finishing, audit for AI writing patterns (inline-header bullets, boldface overuse, em-dash overuse, negative parallelism). See → [Anti-AI Tells in Daily Notes](references/anti-ai-tells-daily-notes.md)
- **Conversion**: Move durable insights to permanent locations (Ressourcen/Bereiche/Projekte)
- **Berlin Timezone**: All daily notes use `zeitzone: Europe/Berlin` in frontmatter since 2026-07-09

## Subagent Coordination

### Conflict Avoidance

- **File-scope partitioning**: Each subagent owns non-overlapping files
- **Additive patches only**: Never `write_file` on existing notes
- **"Siehe auch" footer**: Append at end to avoid sibling conflicts
- **Pattern 7 verification**: Always verify after multi-subagent work

### Common Pitfalls

See → [Pitfalls](references/pitfalls.md) for detailed coverage of:
- `_warning` field from `patch` tool (sibling conflicts)
- `replace_all=true` corruption risk
- Advisory voice hallucinations
- Inline comment placeholder filtering
- Post-expansion verification

## Common Workflows

### Wiki-Link Density Check

- **Python**: See → [Wiki-Link Density (Python)](references/wiki-link-density-python.md)
- **Bash**: See → [Wiki-Link Density (Bash)](references/wiki-link-density-bash.md)

### Cross-Link Cleanup

See → [Cross-Link Cleanup](references/cross-link-cleanup.md) for:
- Broken-link audit script
- Fix strategies (add alias, convert to wiki-link, create missing file)
- Verification checklist

### Bulk Cross-Link Patching

See → [Bulk Cross-Link Patching](references/bulk-cross-link-patching.md) for:
- Automated multi-file wiki-link insertion into existing cross-reference sections
- Section-end detection algorithm (handle `###` sub-headers correctly)
- Dedup across entire file, not just within section
- Backup-restore-recovery pattern
- Grep-based verification protocol
- Proven: 38 patches in 7 files (2026-07-14, GreyHack cluster)

### Content Quality Gate

See → [Content Quality Gate](references/content-quality-gate.md) for:
- Pre-defined quality criteria for large vault notes (0 Em-Dashes, 0 inline-headers, ≥ 5 wiki-links)
- Grep-based validation commands (grep -c, grep -o, sort -u)
- Systematic fix workflow (patch → re-validate → iterate)
- Abgrenzung zu `anti-ai-tells-daily-notes.md` (Stil) und `obsidian-vault-quality-audit` (Struktur-Audit)

### Glossary Enrichment

See → [Glossary Enrichment](references/glossary-enrichment.md) for:
- Phased expansion (Categorize → Add Definitions → Cross-Link)
- "Siehe auch" column technique
- Cross-link targets per category

### Project README Template

See → [Project README Template](references/project-readme-expansion.md) for:
- Full README structure (180–220 lines)
- Anti-halluzination verification workflow
- Stale-data marking protocol

### Style-Settings Integration

See → [Style-Settings Integration](references/style-settings-integration.md) for:
- `@settings`-Annotation-Grammatik (YAML-in-CSS-Comment)
- Setting-Types: `variable-themed-color`, `variable-number-slider`, `variable-select`, `class-toggle`, `heading`
- Aktivierungs-Workflow (Toggle-Trick bei bestehenden Snippets)
- Session-Beispiel: Yuno Palette (7 Farb-Picker in yuno-variables.css)

### MOC-Patch Verification

See → [MOC-Patch Verification](references/moc-patch-verification.md) for:
- Verifying ALL wiki-links in a single MOC after editing it (frontmatter, new links, tables, maintenance-log)
- Extraction methodology: `grep -oP '\[\[\K[^\]]+(?=\])'` + `sort -u` + `find` basename match
- Verification table format (✅/❌ with relative paths)
- Sub-bee briefing template for automated verification via delegate_task
- Pre-existing dead link vs. new typo disambiguation
- Proven: 2026-07-14 GreyHack MOC, 17 links, 16 ✅ / 1 ❌ (pre-existing dead link detected)

## Vault Improvement Bundling

See → [Vault Improvement Bundling](references/vault-improvement-bundling.md) for:
- Ground-truth recon before analysis
- 3-package sizing model (A/B/C)
- Gate before implementation

## Monitoring

### Vault Health Metrics Note

Create `05 Ressourcen/Vault-Health-Metrics.md` with:
- Target metrics table (proven achievable values)
- Dataview queries (see → [Dataview Queries](references/dataview-queries.md))
- Monthly review checklist

### Post-Expansion Verification

Run after every expansion phase:
- Note count check
- Broken-link audit
- Wiki-link density verification
- Orphan detection
- Memory save

## Related Skills

- `obsidian` — File-tool operations (read, search, create, edit notes)
- `obsidian-vault-cluster-operations` — Subagent patterns for vault work
- `gemini-vault-cluster-worker` — Gemini-CLI as vault subagent
- `obsidian-vault-quality-audit` — Backlink roundtrip + orphan detection
- `vault-skill-derivation` — Extract patterns from vault into skills