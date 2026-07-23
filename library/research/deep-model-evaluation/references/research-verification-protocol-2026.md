# Research Verification Protocol (July 2026)

Captured from the pre-research session on 2026-07-16. Documents the structured 3-URL verification methodology, hidden-gems identification approach, and specific API pitfalls discovered during a multi-model comparison for 8 GB VRAM.

---

## 1. Three-URL Structured Verification (URL1/URL2/URL3)

This is the most important methodology addition. Every model candidate needs **three independent source types** before it enters the final report:

| Column | Source type | What it verifies |
|---|---|---|
| **URL1** | HF model card / official vendor page | Architecture, size, license, benchmark claims, release date (via `lastModified` or card text) |
| **URL2** | Independent benchmark, Reddit, YouTube, third-party guide | Real-world performance, community sentiment, "works for me" vs "broken" controversy |
| **URL3** | Live download check (HF API JSON, Ollama library page, `ollama pull` dry-run) | Actual file availability, download counts, last updated timestamp |

**Requirement:** At least 2 of 3 URLs must be live-verified (web_extract, HF API call, terminal command during the session). Flag in the table which rows failed the live check and why (e.g. "HF API 401 — rate-limited, substituted 2+ corroborating sources").

**Verification level tags:**
- `[VERIFIED]` — you personally fetched the page/API response/terminal output during this session
- `[HF API JSON]` — called `huggingface.co/api/models/{repo}` directly
- `[Search snippet]` — from web_search only (lowest confidence, use as last resort)

### Recording format

```markdown
| # | URL1 — HF model card | URL2 — independent benchmark | URL3 — live download check |
|---|---|---|---|
| 1 | https://huggingface.co/org/model [VERIFIED] — full eval table | https://reddit.com/... (community thread, vs baseline); https://youtube.com/... (head-to-head) | Ollama library page [VERIFIED]: `tag:name` 5.2 GB / 40K ctx; HF API: 752K pulls, updated 2026-06-25 [VERIFIED] |
```

### Coverage target

- Minimum 60% of rows with URL3 = web_extract or terminal-captured live download proof
- Stretch target: 80%+ for the top 5 recommendations
- Log any failures explicitly (rate-limit, 404, no Ollama tag yet) — do NOT fabricate

---

## 2. Hidden-Gems Identification

Beyond the obvious "best of" list, look for models that satisfy ALL of:

1. **Under-advertised** — not on every blog's "Top 5 Local Models" but has strong community signal
2. **Constrained-fit** — excels specifically for 8 GB VRAM (not a scaled-down giant, not a 24 GB-oriented model that technically runs at Q2)
3. **Specific niche advantage** — e.g. "best true-7B coder Apr 2026" (Qwen3-Coder-7B), "best reasoning-per-byte on 8 GB tier" (Phi-4-mini), "native multimodal coder that fits 8 GB" (Gemma 4 E4B)
4. **MIT/Apache or permissive OSS** — no non-commercial gotchas
5. **GGUF available** — either from official repo, community mirror (unsloth/bartowski/mradermacher), or user can convert themselves

### When a model qualifies

- Ask: "Is this on every 'best local models' list?" — if yes, it's a mainstream pick, not a hidden gem.
- A hidden gem can be a runner-up on the main table if the number of slots exceeds top-tier candidates.
- Write a short paragraph per gem explaining WHY it's overlooked and WHY it wins in its niche.

---

## 3. Family Inventory Approach

When researching a family (e.g. Qwen 3.x, Gemma 4), compile:

| Property | What to capture |
|---|---|
| **Variants** | All known sizes and specializations (coder, thinking, instruct, base) |
| **2026 release dates** | From HF `lastModified`, arxiv paper id (e.g. `arxiv:2606.19348`), blog posts |
| **Licensing** | Apache-2.0 vs MIT vs Llama Community vs custom |
| **Ollama availability** | Which variants have first-party `ollama run` tags |
| **HF GGUF mirrors** | unsloth, bartowski, mradermacher — check `downloads` count for community adoption signal |

Release dates are critical. If the most authoritative source (HF `lastModified`) shows a model was updated in 2024, it's pre-2025 and should be flagged as legacy.

---

## 4. API Pitfalls (documented live)

### Ollama Registry v2 API

**Finding:** The `registry.ollama.ai/v2/library/{name}` JSON endpoint returns 404 for all model names tested (confirmed 2026-07-16). This API path is NOT the canonical availability check.

**Correct check:** Use:
1. `ollama.com/library/{name}` web page (web_extract) — shows tags, sizes, context window
2. `ollama pull {name}` terminal command (best signal — actually tries to download)
3. Search snippets referencing `ollama run {name}`

Do NOT cite `registry-api` failure as evidence a model is absent from Ollama — the registry API is defunct.

### Hugging Face API Rate-Limiting

**Finding:** Anonymous `api/models/{repo}` JSON calls return HTTP 401 when rate-limited. This does NOT mean the repo doesn't exist.

**Mitigation:**
1. Retry with `curl -s` after 30s cooldown
2. Fall back to `web_extract` of the HF model card page (slower but works)
3. If both fail, cite 2+ corroborating independent sources and flag the HF API as `401 (rate-limited)` in the verification log
4. Never fabricate HF metadata — if you can't verify it, document the gap

### Multi-Source Redundancy Goal

For the top recommendation specifically, target **3+ independently verified sources** (model card + Reddit + YouTube head-to-head + live download check). For other rows, 2 is acceptable but document which were thinner.
