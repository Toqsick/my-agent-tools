# Worked Example: Qwythos vs Qwen Deep-Dive

> Session: 2026-07-14 · Model: deepseek/deepseek-v4-flash
> Full conversation stored in session DB.

## Task

Evaluate Qwythos-9B (all versions v1/v2/v3) vs Qwen3.5-9B and Qwen3.6 models. Produce German comparative reports with honest assessment, practical hardware advice, and download recommendations.

## Sources gathered (batch 1 — parallel)

| Source | URL | What it gave |
|---|---|---|
| v1 GGUF model card | huggingface.co/empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF | Downloads (2.01M), likes (2.13k), spike → huge popularity but controversial |
| v1 discussions #33, #34 | same repo | "Broken model — Walking Empero Advertising" + "is this a joke" = massive community backlash |
| v1 discussion #6 | same repo | "Fails at basic reasoning worse than original Qwen3.5-9B" with 13 comments |
| v2 model card | huggingface.co/empero-ai/Qwythos-9B-v2 | FTPO fix, looping 0%, GPQA regression, HumanEval regression, "not a capability jump" |
| v2 GGUF repo | huggingface.co/empero-ai/Qwythos-9B-v2-GGUF | 70k downloads, much calmer community, Q8_0 garbled issue |
| Empero blog | empero.org | FTPO explanation, honesty about v2 being hygiene not cap jump |

## Sources gathered (batch 2 — community + third-party)

| Source | URL | What it gave |
|---|---|---|
| v2 discussion #3 | HF discussions | Garbled Q8_0 → KV-cache quantization is culprit on Qwen3.5 hybrid arch |
| v2 discussion #1 | HF discussions | BF16 mmproj incompatibility with Pascal GPUs, F16 promised |
| v2 discussion #2 | HF discussions | README missing params llama-server |
| note.com zephel01 | note.com/zephel01 | **GOLD**: 5-run SWE-style coding evaluation. Single-run variance exposed (+12.5pt). MTP Q6_K crowned champion |
| YouTube Luke's Dev Lab | youtube.com/watch?v=aC5hhwXr72k | Head-to-head: Qwythos v3-export vs Qwen3.5-9B MTP. Qwen won coding tests, Qwythos won long-ctx needle and agency tools |
| Reddit r/SelfHostedAI | about v3 release | Chat template fix for agentic harnesses — "night and day difference" |

## Key findings that shaped the report

### Marketing vs reality traps identified

| Claim | Reality |
|---|---|
| v1 "+34 MMLU vs Qwen3.5 base" | Different harness, different CoT template — not a valid comparison |
| v2 "0% looping fixed" | Verified (greedy), but **task flakiness** (18-21/40 tasks run-dependent) remains at T=0.6 |
| "v3" version name | **Not a new training run** — template export hotfix on v1 weights |
| "Qwen3.6 9B" in YouTube description | Actual model used was **Qwen3.5-9B MTP** — 3.6 has no 9B open-weight |
| "Claude in 9B" | Marketing frame — 9B is 9B regardless of which traces were used |

### Single-run championship trap

zephel01 documented this perfectly:
- v1 champion MTP-Q8_0 scored 87.5% on 1-run → 75.0% on 5-run average (−12.5pt)
- Q6_K scored 75.0% on 1-run → 81.0% on 5-run average (+6pt stabilization)
- **Lesson: 1-run champion is NOT the 5-run champion**

### Hardware-specific findings for 8GB RTX 5060

| Config | Fits? | Context | Recommended |
|---|---|---|---|
| Q4_K_M (any) | ✅ | 8-16k | Yes — start here |
| MTP-Q4_K_M | ✅ | 8-16k with spec decode | Yes |
| Q5_K_M | ⚠️ tight | 8k only | Maybe |
| Q6_K | ❌ 7.5GB weights alone | Nope | No |
| Anything with BF16/Q8 | ❌ | Nope | No |
| KV-cache quantization | **breaks Qwen3.5 hybrid arch** | → garbled | Never use with Qwen3.5-class models |

### Community sentiment arc

| Version | Tone | Signal |
|---|---|---|
| v1 | "broken model", "advertising", "fails basic reasoning" | Toxic, distrust |
| v2 | Calm, "works great with MTP", "Q8 garbled but Q6 works" | Pragmatic, usable product |
| v3 (template fix) | "night and day for agents" — Empero claim | Quiet acceptance |

## Report structure used

1. **TL;DR** — single sentence with raw verdict
2. **Lineage & Architecture** — table with params, context, MTP, vision, license
3. **Benchmarks** — internal table + official Qwen table + caveats
4. **Third-party Real-World Testing** — zephel01 (5-run) + Luke's Dev Lab (head-to-head)
5. **Community Findings** — garbled Q8, KV-cache sens, mmproj issue
6. **Version Comparison Matrix** — v1 vs v2 vs v3 vs base, scored per dimension
7. **Hardware Guide** — 8GB specific recommendations
8. **Honesty/Marketing Score** — 9/10 for v2 honesty in blog post
9. **Scoring Table** — 8 dimensions rated 1-10
10. **Download Recommendations** — Option A/B/C with ⭐ ratings

## Practical tips for future evaluations

- **Batch independent reads** — model card + search + community all in one tool call
- **Always check: is "v3" a real training iteration or a re-export?** Look for new safetensors in the non-GGUF repo
- **When YouTube testing exists, note the sample size** — 3 tasks of test is not statistically significant
- **For 8GB-targeted evaluations, always include exact quant + context size + speed estimate**
- **Never take a model card's "beats base" claim at face value** — cross-reference official base model benchmarks
- **Prefer 5-run (or more) evals for stability assessment** — single runs are deceptive
- **Document naming confusion** explicitly — future sessions will thank you when the conversation mentions "v3"