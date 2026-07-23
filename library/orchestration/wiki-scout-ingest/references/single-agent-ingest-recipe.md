# Single-Agent Ingest Recipe

> Real session recipe: 6 Obsidian sources → 16 wiki pages, all in one agent.
> Session date: 2026-07-17 | Domain: ai-ml
> Sources: 3 Obsidian MOC notes + 2 system-doku notes + 1 00-Meta review
> Result: 8 entities + 8 concepts + 6 raw articles → index/log updated

## Why Single-Agent

The multi-agent scout swarm is optimal for 5+ sources spanning 2+ domains.
This session was **1 domain (ai-ml), 6 sources** — too small for dispatch
overhead. The `delegate_task` calls for Phase 2 wouldn't save enough context
to justify the token cost of parallel orchestrator orchestration.

## Phase 1: Recon

```
read:  ~/wiki/SCHEMA.md       # conventions, tag taxonomy
read:  ~/wiki/index.md         # page count, existing structure
read:  ~/Dokumente/Obsidian Vault/MOC - KI-Architektur.md   # hub MOC
read:  ~/Dokumente/Obsidian Vault/01 Kontext/KI-Betriebssystem (Julian Ivanov).md
read:  ~/Dokumente/Obsidian Vault/09 System-Doku/KI-Architektur/{grok-4.5-modelleinschatzung,hermes-vs-odysseus-synthesis,mnemosyne-phase3-report}.md
read:  ~/00-Meta/hermes-architecture-review-2026-07-11.md
```

Key insight: the MOC note links to ~15 child notes via [[wikilinks]].
**1-hop depth** is enough — don't chase every link, just the MOC + directly
referenced documents.

## Phase 2: Raw Article Pipeline

The critical technique: **strip vault frontmatter before computing sha256**.

```python
# sha256 over body-only (strip Obsidian YAML frontmatter)
import hashlib
with open('/tmp/__content.txt', 'r') as f:
    content = f.read()
if content.startswith('---'):
    parts = content.split('---', 2)
    body = parts[2].strip() if len(parts) >= 3 else content
else:
    body = content
sha = hashlib.sha256(body.encode()).hexdigest()
print(sha[:12])
```

This was used because Obsidian vault notes have YAML frontmatter (title,
created, updated, tags) that changes when the vault metadata is modified.
Computing sha256 over the **whole file** would produce different hashes
for the same content on different days. Stripping frontmatter → stable hash.

**6 raw articles created:**
| File | Source | sha256 prefix |
|---|---|---|
| `moc-ki-architektur.md` | MOC - KI-Architektur | `13af44fce3f3` |
| `hermes-architecture-review-2026-07-11.md` | 00-Meta review | `385096ad64bc` |
| `grok-4.5-modelleinschatzung-2026-07-13.md` | Obsidian system-doku | `ef8263048006` |
| `hermes-vs-odysseus-synthesis-2026-06-28.md` | Obsidian system-doku | `0cf1b1451f17` |
| `ki-betriebssystem-julian-ivanov.md` | Obsidian 01-Kontext | `7391425e16a1` |
| `mnemosyne-phase3-report.md` | Obsidian system-doku | `32d6583a9143` |

Verification: `grep sha256 raw/articles/*.md` → confirm prefixes match.

## Phase 3: Wiki Page Creation

Distillation order: **Entities → Concepts → Cross-domain**.

### Entities (8 pages)
Each entity got its own page with the full SOUL.md pattern:
- `hermes-agent.md` — Framework, Provider-Hierarchie, Skill-Stack (9 wikilinks)
- `mnemosyne.md` — 4-Tier, Sleep-Cycle, Phasen (11 wikilinks)
- `odysseus.md` — Selbstgehosteter Workspace, Vergleich Hermes (6 wikilinks)
- `ollama.md` — Lokaler Stack, Modelle, Q4_K_M (5 wikilinks)
- `qwen-3.5-9b.md` — Standard-Ollama-Modell (5 wikilinks)
- `claude-code.md` — Anthropic Coding-Agent (6 wikilinks)
- `grok-4.5.md` — xAI Modell, 7.5/10 (3 wikilinks, `contested: true`)
- `mcp-model-context-protocol.md` — Tool-Interface Standard (6 wikilinks)

### Concepts (8 pages)
- `transformer-architecture.md` — Encoder-Decoder, Tokenizer, Skalierung (13 wikilinks)
- `attention-mechanism.md` — Self-Attention, MHA, GQA, KV-Cache (8 wikilinks)
- `mixture-of-experts.md` — Sparse-MoE, MoE-ify, Top-K (8 wikilinks)
- `rlhf-dpo-grpo.md` — Alignment-Methoden, Tabelle (9 wikilinks)
- `memory-tiering.md` — 4-Tier: Working/Episodic/Facts/Scratchpad (7 wikilinks)
- `queen-worker-pattern.md` — Queen-Agent, Worker-Pool, Lern-Loop (6 wikilinks)
- `lancedb.md` — Columnar Vector-DB, Vergleichstabelle (6 wikilinks)
- `ki-betriebssystem-julian-ivanov.md` — 4-Bausteine cross-domain (8 wikilinks)

### Provenance markers
Every synthesis statement that combined or interpreted source material got:
```
^[raw/articles/moc-ki-architektur.md]
^[raw/articles/hermes-vs-odysseus-synthesis-2026-06-28.md]
```

### Confidence flags
- `confidence: high` — multiple independent sources agree
- `confidence: medium` — single source, plausible
- `contested: true` — Grok-4.5 (Trust=4 vs Coding=8.3, Adversarial-Trust-Gap)

## Phase 4: Quality Gate Verification

After writing all 16 pages, ran systematic checks:

```bash
# Wikilink count — minimum 2 per page
for f in entities/*.md concepts/*.md; do
    count=$(grep -oE '\[\[[^]]+\]\]' "$f" | wc -l)
    echo "$count wikilinks : $f"
done
# Result: range 3-13, all ≥2 ✓

# Frontmatter completeness
for f in entities/*.md concepts/*.md; do
    has_title=$(head -10 "$f" | grep -c "^title:")
    has_type=$(head -10 "$f" | grep -c "^type:")
    has_domain=$(head -15 "$f" | grep -c "^domain:")
    echo "$f  title=$has_title  type=$has_type  domain=$has_domain"
done
# Result: 16/16 complete ✓

# Total pages
find ~/wiki -type f -name "*.md" | wc -l
# Before: ~8-12 pages (from previous ingests)
# After: 47 files (including meta, raw, templates)
```

## Index/Log Race

A sibling subagent from a parallel dispatch task was writing to index.md
and log.md at the same time. The `patch` warning system caught it:

```
_warning: "...was modified by sibling subagent '20260717_113509_51d219'
at 11:42:13 — after this agent's last read at 11:38:25"
```

Resolution: re-read the file, confirmed sibling already indexed the new pages,
skipped redundant write. For log.md, the append-succeeded despite the race.

## Key Takeaways

1. **Single-agent ingest needs explicit raw-article-first ordering.**
   Without it, you'll write wiki pages against unverified source content.

2. **sha256 body-only is non-negotiable for Obsidian sources.**
   Vault frontmatter changes (updated timestamps) would invalidate hashes.

3. **Quality gate loop catches what you think you did but didn't.**
   The shell loops revealed a missing `domain:` tag on one page.

4. **Sibling-agent races on index/log are survivable.**
   Re-read → re-evaluate → skip if duplicated. Don't force-write.

5. **16 pages in one session ≈ natural single-agent ceiling.**
   Beyond this, the context window becomes the bottleneck and multi-agent
   dispatch would have been faster despite overhead.
