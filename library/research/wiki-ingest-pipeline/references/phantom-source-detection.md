# PHANTOM/404 Source Detection — Raw-Article Pattern

> How to handle source files that reference URLs returning HTTP 404 (dead
> models, renamed repos, deactivated resources). Learned from ingesting
> `ollama_moe_tuning_complete` with Ornith-35B PHANTOM files (2026-07-17).

## Problem

You find source files (Modelfiles, startup scripts) that reference a
HuggingFace model or external resource that returns HTTP 404. Example:

| Field | Value |
|---|---|
| Source file | `Modelfile.ornith-35b-q5-full` + `start-ornith-35b.sh` |
| Claimed URL | `maxwell1500/ornith-35b` on HuggingFace |
| Reality | ❌ 404 — model does not exist on HF |
| Version | Both `q5_full` quantisation variants — same 404 |
| Probable cause | Model was private/renamed at source, Ollama Modelfiles lack HF-side verification |

Naively ignoring such files creates wiki pages with broken external
references. The wiki should capture **that the sources exist locally**
(they're real files on disk) and **that their external dependency is dead**.

## Pattern: Dual Raw Article

### Step 1 — Verify the URL

Use `web_extract` to check the URL:

```python
# Pseudo-tool-call sequence:
result = web_extract(urls=["https://huggingface.co/maxwell1500/ornith-35b"])
# If "404" in result or "not found" in content.lower() → PHANTOM
```

### Step 2 — Create the raw article with `status: deactivated`

```yaml
---
title: "Modelfile — Ornith-35B (PHANTOM)"
source_url: local://ollama_moe_tuning_complete/Modelfile.ornith-35b-q5-full
source_type: ollama-modelfile
ingested: 2026-07-17
sha256: 95c93884ab6b96159107e58efd5ae3405dbfbe93b1170da24454ed96f047031b
status: deactivated
reason: |
  References `maxwell1500/ornith-35b` on HuggingFace.
  HTTP 404 — model does not exist.
  Both q5_full variants (Ornith-35B) are affected.
---
```

**Required frontmatter fields for PHANTOM files:**

| Field | Purpose | Always required? |
|---|---|---|
| `status: deactivated` | Signal to lint/synthesis that external dependency is dead | ✅ Yes |
| `reason:` | Why — 404, renamed, insufficient detail (e.g., missing q parameter) | ✅ Yes |
| `confidence:` | Override — should match `status: deactivated` | ✅ Yes (`low`) |
| `source_type:` | What kind of file (ollama-modelfile, bash-script, etc.) | ✅ Yes (same as normal) |

### Step 3 — Create a 404-audit summary raw article

When multiple files reference the same dead resource, create a separate raw
article documenting the audit:

```yaml
---
title: "Ornith-35B 404-Audit — ollama_moe_tuning_complete"
ingested: 2026-07-17
sha256: ...
status: audit
---
# 404-Audit: Ornith-35B in ollama_moe_tuning_complete

## Files affected (2)

1. `Modelfile.ornith-35b-q5-full` → `status: deactivated`
2. `start-ornith-35b.sh` → `status: deactivated`

## All references to `maxwell1500/ornith-35b`

- In Modelfile.ornith-35b-q5-full: `FROM maxwell1500/ornith-35b:q5_full`
- In start-ornith-35b.sh: `ollama pull maxwell1500/ornith-35b`

## Verdict

✅ Sources exist locally (real files on disk).
❌ External dependency returns 404 — model cannot be pulled.
🟡 Pages referencing these files note the deactivated status.
```

Do NOT create content pages (entities/concepts) for PHANTOM-only material
unless the raw files document something useful despite the dead URL.

### Step 4 — In synthesis pages, reference PHANTOM with caveat

```markdown
Auch vorhanden: Modelfiles für **Ornith-35B** (q5_full), jedoch
❌ deaktiviert — die HF-Referenz `maxwell1500/ornith-35b` gibt HTTP 404¹.
Die Modelfiles selbst liegen lokal vor, sind aber nicht pullbar.
```

With a provenance marker: `¹ ^[raw/articles/ollama-moe-modelfile-ornith-35b-phantom.md]`

## When to use this pattern

| Situation | Action |
|---|---|
| External URL returns 404 | ✅ PHANTOM pattern — `status: deactivated` |
| External URL returns 200 but model name differs | ⚠️ Document redirect, normal ingest |
| URL missing entirely from source (no FROM line) | ⚠️ Document gap, flag for user review |
| Local file references another local file that doesn't exist | ❌ This is a broken reference, not a 404 — flag as integrity issue |
| Source references a model that exists but is private/gated | ⚠️ `status: restricted` — different frontmatter field |

## Pitfalls

- **Don't skip the raw article entirely** — even dead-source files on disk
  are real artifacts that another ingest might reference. A zero-raw-article
  for a real file = missing provenance anchor for future ingests.
- **Don't create entity pages for PHANTOM-only material** — the entity
  (model) doesn't exist on HF. A wiki page for a non-existent entity pollutes
  coherence. Only create concept-level mentions noting the deactivated status.
- **Don't silently ignore** — if you skip PHANTOM files without documenting
  why, a future agent session will re-find the files, re-verify, and waste
  time re-discovering the same 404. Document once, verify never again.
- **Confidence cascade** — when PHANTOM raw articles are referenced from
  concept pages, the concept page's confidence should drop by at least one
  level (`high → medium`, `medium → low`). A claim backed partly by dead
  references is weaker.
