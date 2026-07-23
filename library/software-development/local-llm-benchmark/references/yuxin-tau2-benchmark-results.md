# Reference Run — yuxin-tau2 (gemma4 11.9B Q4_K_M) on RTX 5060 8GB

**Hardware:** MEDION ERAZER · RTX 5060 Laptop 8GB · 80W TGP · 95°C Cap · no OC
**Model:** yuxin-tau2:latest (gemma4 11.9B, Q4_K_M)
**Date:** 2026-07-17 (in-progress — first run)
**Prequel:** Suite cloned from qwythos-9b benchmark, adapted for gemma4 architecture

## Architecture Comparison: gemma4 vs qwen3.5 (qwythos)

This table captures the key differences between the two model architectures,
critical for anyone adapting a benchmark between them:

| Property | gemma4 (yuxin-tau2) | qwen3.5 (qwythos-9b) | Impact |
|---|---|---|---|
| **Params** | 11.9B | 9.2B | +29% model size → more VRAM |
| **Ollama size** | 8.0 GB | 6.5 GB | Tighter fit on 8 GB GPU |
| **Quant** | Q4_K_M | Q6_K | Smaller quant → faster but more noise |
| **Context default** | 4096 | 8192 | Must set `num_ctx` explicitly for large context |
| **Default tag size** | 8.0 GB | 6.5 GB | 1.5 GB more VRAM baseline |
| **Score-from** | `response` | `response + thinking` | qwen35 writes answers in thinking block |
| **Thinking format** | Plain-Text | XML-tags (`<|im_start|>`) | Parser must not strip what isn't there |
| **Tool-call format** | OpenAI-compat (penultimate chunk) | OpenAI-compat (final chunk) | Accumulator pattern needed for stream mode |
| **Empty content** | `content: ""` when tool-calls | N/A — always has text | Must check `tool_calls`, not `content` |
| **Vision** | None (no CLIP) | Yes (CLIP, works with CPU-offload) | Must skip vision runner |
| **Stop token** | `<turn|>` (Ollama handles) | `<|im_end|>` | Transparent — Ollama normalizes |
| **Speed (short)** | ~20.5 t/s (160 tok) | ~23.5 t/s (160 tok) | 13% slower — expected for larger model + Q4 |

## Headline Numbers (First Run — preliminary)

> ⚠️ **This is a first-run snapshot.** Re-runs with official gemma4 sampling defaults
> have NOT been completed yet. Expect 10-15% improvement after default-tuning.

| Dimension | Result | Notes |
|---|---|---|
| Throughput (short 128) | **20.5 t/s** | vs qwythos 23.5 t/s — 13% slower as expected |
| Context 4k (num_ctx=4096) | ~20 t/s eval | gemma4 default context; smallest safe benchmark size |
| Thinking-Variants (High) | **100%** (10/10) | With `num_predict=16000, T=0.6, think=True` |
| Thinking Max (np=30000) | ⚠️ **Reflection loop** | Model ran 18+ min per prompt — see pitfall below |
| Quality | *(in progress)* | MMLU, GSM8K, HumanEval — awaiting completion |

## Key Differences from qwythos Benchmark

### 1. Speed Profile

yuxin-tau2 is consistently **~13% slower** than qwythos on the same hardware:

| Output Size | qwythos (Q6_K) | yuxin-tau2 (Q4_K_M) | Δ |
|---|---|---|---|
| 160 tokens | 23.5 t/s | 20.5 t/s | -13% |
| *larger* | *22-23 t/s* | *pending* | |

Expected causes: 11.9B vs 9.2B params (+29%), Q4_K_M has different memory bandwidth
profile than Q6_K, and gemma4 uses a larger KV-cache per token.

### 2. VRAM Pressure

yuxin-tau2 at default (4096 context) uses **8.0 GB** — that's **6.7 GB on GPU**
(83% GPU / 17% CPU split) with only **~1 GB free**.

**Implications on 8 GB GPU:**
- Needle-Haystack at 128k: **must skip** — VRAM will OOM
- Context >16k: expect CPU-offload splitting at smaller thresholds than qwythos
- Vision: N/A (no CLIP, but even if it had one, OOM would be guaranteed)
- ollama_ps shows `17%/83%` CPU/GPU even at 4k context — the model is at the
  very edge of fitting entirely in GPU memory

### 3. Max-Variant Ceiling (Critical Discovery)

**`num_predict=30000` causes reflection loops.** During the yuxin-tau2
benchmark, the Max variant (np=30000, T=0.6, think=True) ran **18+ minutes**
on a single logic prompt (12-ball problem). The model entered a reflection
loop inside the thinking block, re-evaluating its own reasoning instead of
converging.

**Mitigation:** The actual prompt only needs ~4045 tokens. Set
`num_predict=16000` as the practical ceiling — the model stops naturally
when done and doesn't waste the extra budget.

**Why this happens:** Unlike qwythos (qwen35 family, which stops naturally
at ~1000 tok regardless of budget), gemma4 with `think=True` and very large
`num_predict` can enter meta-cognitive loops. This may be architecture-specific
(gemma4's training regime) or quantization-specific (Q4_K_M introduces
noise that triggers re-evaluation).

**If you encounter this again:**
1. Set a timeout of `max(300, num_predict / 8 * 1.5)` per prompt
2. Drop `num_predict` to 16000 for the Max variant
3. Monitor `done_reason` — if it's never `"stop"`, increase the timeout
   and check if `eval_count` exceeds `num_predict / 2`

### 4. Empty Content on Tool-Only Responses

This is architecture-correct behavior for gemma4 (see
`references/gemma4-architecture-notes.md`), but it differs from qwen35
models which always return a natural-language wrapper around tool calls.

**Benchmark impact:** The tools runner must score from `tool_calls` presence,
not `response` non-emptiness. A passing test is:
```python
d["message"]["tool_calls"] is not None and len(d["message"]["tool_calls"]) > 0
```
NOT:
```python
len(d["message"]["content"]) > 0  # False positive for gemma4!
```

## Sampling Defaults (Ollama defaults — not yet tuned)

Until a gemma4 HF card is found with official defaults, the benchmark uses
sensible defaults derived from the qwythos re-run:

```python
{
    "temperature": 0.3,
    "top_p": 0.95,
    "top_k": 20,
    "repeat_penalty": 1.05,
    "num_ctx": 4096,     # gemma4 default — keeps GPU at full speed
    "stream": False,
    "keep_alive": "30m",
}
```

**VS qwythos defaults (Empero official):**
| Parameter | qwythos (Empero) | yuxin-tau2 (initial) | Notes |
|---|---|---|---|
| temperature | 0.6 | 0.3 | gemma4 may tolerate lower T better |
| top_p | 0.95 | 0.95 | Same |
| top_k | 20 | 20 | Same |
| repeat_penalty | 1.05 | 1.05 | Same |
| num_ctx | 8192 | 4096 | gemma4 default is smaller |

## Files

- Suite project: `~/10-Projekte/10-active/greyhack-tools/benchmarks/yuxin-tau2/`
- Source: `src/yuxin_tau2_bench/` (adapted from qwythos_bench)
- Prompts: `prompts/` (shared with qwythos suite — same test set)
- Commits: `ce19806` (skeleton), `eae6785` (tests), `11d07b2` (runners), `c0f5d43` (titles)
- Gemma4 format guide: `references/gemma4-architecture-notes.md` (in this skill)
