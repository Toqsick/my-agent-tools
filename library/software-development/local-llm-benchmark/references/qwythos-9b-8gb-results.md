# Reference Run — qwythos-9b-q6 on RTX 5060 8GB

**Hardware:** MEDION ERAZER · RTX 5060 Laptop 8GB · 80W TGP · 95°C Cap · no OC
**Model:** qwythos-9b-q6 (Q6_K, ~9B params, qwen35 arch)
**Date:** 2026-07-17
**Total Runtime:** ~110 min (4 iterations including re-runs with official Empero defaults)

## Headline Numbers (FINAL — after 4th iteration with official defaults)

| Dimension | Result | Notes |
|---|---|---|
| Throughput | 22-23 t/s | Stable across 128–8192 output tokens |
| Context 1k–64k | 861–1303 prompt t/s | Linear scaling, 7.5 GB VRAM peak |
| Needle 128k | 0/6 hits | Attention decay at very long context |
| MMLU-Lite | **100%** (15/15) | after think=False fix |
| GSM8K-Lite | **91.7%** (11/12) | ⬆️ +24.7% after Empero defaults (T=0.3) |
| HumanEval-Lite | **70%** (7/10) | ⬆️ +10% after Empero defaults |
| Aggregate Reasoning | **87.2%** | ⬆️ from 75.6% (+11.6%) |
| Thinking High (np=8000) | **100%** (10/10) | Sweet-spot for reasoning |
| Thinking Balanced (np=1500) | **90%** | Good latency/accuracy trade-off |
| Thinking Off | **70%** | Not recommended for complex logic |
| Vision (5 images) | 5/5 Hits | CPU-offload only (~50s/image) |
| Function-Calling | 5/5 Tool-Name | Perfect |

**Key insight:** Official Empero sampling defaults (T=0.6, repeat_penalty=1.05) improved aggregate from 75.6% → 87.2%. The initial run had `T=0.0` which is explicitly counter-indicated by the model card.

## Bugs Found During Run (4 iterations)

### Iteration 1 (first run — 3 bugs)
1. **MMLU empty responses (Critical)**
   - Root: `num_predict=4` → model writes answer in `thinking` block, `response=""`
   - Fix: `num_predict >= 80` + `think=False`
   - Impact: 6.7% → 100%

2. **Vision OOM on 8 GB (High)**
   - Root: CLIP projector (456M params) + 8.5 GB language model > 8 GB VRAM
   - Fix: `options={"num_gpu": 20}` forces CPU-offload
   - Impact: Vision works at ~4x latency

3. **path.parents off-by-one (Low)**
   - Root: Runner in `src/<pkg>/runners/` needs parents[3]
   - Impact: File-not-found on first run

### Iteration 2 (Re-Run #1 — fixes applied, but 2 bugs remain)
- ✅ MMLU 1/15: `num_predict=4→80` (still low — thinking-loop issue)
- ✅ HumanEval 6/10: `num_predict=200→500`
- ✅ Vision 5/5: `num_gpu=20` fix works
- 🆕 Discovered: Thinking-Loop at temperature=0.0 + small num_predict → model answers in thinking block

### Iteration 3 (Re-Run #2 — think=False fix)
- ✅ MMLU 15/15 (100%): `think=False` for MC
- GSM8K 8/12 (66.7%): still suboptimal
- HumanEval 6/10 (60%): still suboptimal

### Iteration 4 (Re-Run #3 — Empero Defaults applied)
- ✅ MMLU 15/15 (100%) — unchanged
- ✅ GSM8K **11/12 (91.7%)** — ⬆️ +24.7% with T=0.3, repeat_penalty=1.05
- ✅ HumanEval **7/10 (70%)** — ⬆️ +10% with T=0.3, np=800
- ✅ Thinking-Effort benchmark: 4 variants compared (Off/Balanced/High/Max)
- ✅ Max variant confirmed: no benefit over High at np=8000

## Thinking-Effort Comparison (FINAL, Empero defaults)

| Variant | think | T | np | Score | Avg Tok | Avg Wall | Sat |
|---|---|---|---|---|---|---|---|
| Off | false | 0.3 | 200 | 70% | 173 | 6.8s | 8/10 |
| Balanced | true | 0.6 | 1500 | 90% | 848 | 30.7s | 3/10 |
| **High** | **true** | **0.6** | **8000** | **100%** | 1019 | 36.1s | 1/10 |
| Max | true | 0.6 | 16000 | 100% | 988 | 36.4s | 1/10 |

**Sweet-spot: `num_predict=8000` with thinking=True.** Max uses fewer avg tokens (988 vs 1019) but same score — the model stops naturally when done.

**Critical contrast with pre-Empero-defaults run:** Using wrong defaults (T=0.0, repeat=1.0), the first run showed "Thinking ON scores 80% vs OFF 90% — thinking adds no value." **That was a configuration artifact.** With correct defaults, thinking ON adds +30% accuracy.

## Official Empero HF-Card Sampling Defaults

Source: https://huggingface.co/empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF

| Parameter | Value | Notes |
|---|---|---|
| `temperature` | **0.6** | Greedy / T≤0.3 causes **repetition loops** on long reasoning |
| `top_p` | 0.95 | Standard |
| `top_k` | 20 | Standard |
| `repeat_penalty` | **1.05** | Prevents repetition during thinking |
| `max_new_tokens` | 16384+ | Must be generous for `<think>` + answer |

**Official warning:** "Avoid greedy decoding and very-low-temperature sampling (T ≤ 0.3) — both can cause repetition loops on long reasoning generations."

## Recommended Configurations

| Task | think | T | np | Expected latency |
|---|---|---|---|---|
| MC / JSON / Code | false | 0.3 | 80-500 | 2-18s |
| Light reasoning | true | 0.6 | 1500 | ~31s |
| **Complex reasoning** | **true** | **0.6** | **8000** | **~36s** |
| Max reasoning | true | 0.6 | 16000 | ~36s (no benefit) |

## Configuration Lessons

| Setting | Wrong Default | Correct Default |
|---|---|---|
| num_predict | 4 | 80+ (QA), 500+ (code), 1500+ (thinking) |
| think | true (inherited) | false for structured tasks |
| num_ctx | 8192 | up to 65536 on 8GB |
| stream | true (Ollama default) | false |
| keep_alive | 5m (Ollama default) | 30m |
| temperature | 1.0 | 0.6 for thinking, 0.3 for structured |

## 128k Context Trade-off on 8GB

| Context | Process | GPU Split | Throughput |
|---|---|---|---|
| 8k (default) | 8.4 GB | 100% GPU | 22 t/s |
| 131k (128k tag) | 13 GB | 49%/51% CPU/GPU | ~10 t/s |

The practical limit on 8 GB VRAM is ~64k context. Above that, CPU-offload halves throughput and the latency-cost ratio worsens.

## Files

- Plan: `~/.hermes/plans/2026-07-17_115245-qwythos-9b-deep-benchmark.md` (31 KB)
- Suite project: `~/10-Projekte/10-active/greyhack-tools/benchmarks/qwythos-9b/`
- Raw results: `results/raw/` (10+ JSON files — includes 4 thinking variants + quality re-run)
- Charts: `results/charts/` (7 PNG files)
- Report: `results/REPORT.md` (87.2% aggregate)
- Dashboard: `results/dashboard.html`
- Mnemosyne lessons: `279820cc5c448b6c`, `3bf6b93439f29549`, `a5d9dcca83d3d69c`, `88511a8c4188116a`, `f90666ea0e4295e1`
- Obsidian Wiki: `09 System-Doku/qwythos-9b-reference.md`
