# Kimi K3 — API Eval Plan & Research Briefing

> Generated: 2026-07-19 | Source: Kimi K3 launch (July 16, 2026), Kie.ai spec sheet, Simon Willison, HuggingFace community article, NxCode benchmark guide, Artificial Analysis

## TL;DR (for the eval plan)

Kimi K3 is the first open-weight model to reach frontier-tier coding performance. It leads SWE Marathon (42.0) and Program Bench (77.8), matches Opus 4.8 on general intelligence, and trails only Fable 5 + GPT-5.6 Sol overall. At **$3/$15 per MTok** it's 2× K2.6 — the most expensive model ever from a Chinese lab. Open weights promised July 27, 2026; ~1.4 TB weight storage means self-hosting requires 8+ node clusters.

## Core Specs

| Attribute | Value |
|---|---|
| Developer | Moonshot AI (Beijing, $20B valuation, Alibaba+Tencent backed) |
| Architecture | 2.8T MoE, 16/896 experts active (~50B active) |
| Context | 1M tokens |
| Modalities | Text + Vision (native) |
| Quantization | MXFP4 weights + MXFP8 activations (QAT — trained-in, not post-hoc) |
| Reasoning | Always-on thinking mode (no effort levels yet — only "max") |
| Release | API: July 16, 2026 · Weights: by July 27, 2026 |
| License | Open weights (details pending weight release; K2 used Modified MIT) |
| API Pricing | $3/MTok input, $15/MTok output (cached input: $0.30/MTok) |

## Architecture Innovations

- **Kimi Delta Attention (KDA)** — hybrid linear attention replaces quadratic in some layers for 1M-ctx efficiency
- **Attention Residuals (AttnRes)** — layers can selectively retrieve from arbitrary earlier layers (drop-in replacement for standard residual connections)
- **Stable LatentMoE** — 896 experts, 16 active, Quantile Balancing, soft dropping
- **Activation:** Sigmoid Tanh Unit (SiTU) replacing GeLU/SwiGLU
- **KV-cache:** Gated Multi-head Latent Attention (MLA)

## Key Benchmarks (vendor-reported, unless stated)

| Benchmark | K3 | Best competitor |
|---|---|---|
| Program Bench | **77.8** 🥇 | Fable 5: 76.8 |
| SWE Marathon | **42.0** 🥇 | Fable 5: 35.0 |
| Terminal-Bench 2.1 | 88.3 | GPT-5.6 Sol: 88.8 |
| DeepSWE (mini-SWE-agent) | 67.3 | GPT-5.6 Sol: 73 |
| FrontierSWE | 81.2 | Fable 5: 86.6 |
| AA Intelligence Index | 57 | #4/189 models (behind Fable 5, Sol, Opus 4.8) |
| BrowseComp | 91.2 | — |
| GPQA-Diamond | 93.5 | — |
| MathVision | 94.3 | — |

**Artificial Analysis independent:** Cost per task $0.94 (vs Opus 4.8 $1.80). Uses 21% fewer output tokens than K2.6. Long-horizon knowledge work: Elo 1547 (+732 vs K2.6), behind only Fable 5.

**Moonshot's own note:** Still trails Fable 5/GPT-5.6 Sol overall, but **performs competitively or beats them on coding-specific benchmarks** (Program Bench, SWE Marathon, Terminal-Bench 2.1).

## Pricing Comparison

| | K3 | K2.6 | Opus 4.8 |
|---|---|---|---|
| Input / MTok | $3.00 | $0.95 | — |
| Output / MTok | $15.00 | $4.00 | — |
| Cost/task (AA) | $0.94 | — | $1.80 |
| Reasoning | Always-on max | Configurable | Configurable |

## What Phase 9 should measure

For a comparison against Basti's stack (MiniMax-M3, GLM 5.2, DeepSeek V4 Flash):

1. **Correctness:** Does K3 actually fix issues better on real codebases, or does it just excel on benchmarks that reward long-form reasoning at any cost?
2. **Cost-per-accepted-change:** $15/MTok output means a single long coding session could hit $1-3 easily. How does this amortize vs M3 ($4-ish/MTok) or locally-free Ollama models?
3. **1M-context delta:** Is the 1M-ctx window actually usable for full-repo tasks, or does quality degrade >100K tokens like most long-context models?
4. **Reasoning token overhead:** With always-on reasoning, what percentage of K3's output is chain-of-thought vs actual code? Simon Willison's pelican test: 16,658 output tokens, 13,241 reasoning (79% reasoning!).

## Task Design Guidance for Eval (Basti-specific)

| Task | Specific scope | Good test of |
|---|---|---|
| Greyscript refactor | Split 200-line .src file modularly | Domain knowledge, size limit (~12KB), tool semantics |
| Python CLI feature | New subcommand with argparse + pytest | Framework convention, error handling, testability |
| Bash fix | Race condition in `~/50-System/bin/` script | System-level debugging, edge cases |
| Multi-file refactor | Class extraction across 3-5 files | Cross-file consistency, imports, test expectations |
| 1M-ctx doc synthesis | Concatenate entire repo → summary + refactor plan | Long-context coherence, attention decay |

## Known Limitations (from Moonshot)

1. **Thinking history sensitivity:** Harness dropping/changing chain-of-thought causes significant quality loss
2. **Excessive proactiveness:** Acts rather than asks for clarification on ambiguous tasks
3. **UX gap:** Subjective quality still trails Fable 5/GPT-5.6 Sol despite benchmark parity

## Self-Hosting Requirements

- ~1.4 TB weight storage (MXFP4 vs ~5.6 TB FP16)
- Minimum: 8-node cluster × 8× 80GB GPUs (5.12 TB total — headroom for KV-cache + activations)
- Mooncake disaggregated inference (prefill/decode separate node pools)
- 90% cache hit rate on coding workloads reported by Moonshot

**Not feasible on Basti's RTX 5060 8GB setup.** K3 is API-only for this workstation.

## Sources

- Kie.ai spec sheet: https://kie.ai/blog/what-is-kimi-k3
- Simon Willison: https://simonwillison.net/2026/Jul/16/kimi-k3/
- Forbes: https://www.forbes.com/sites/tylerroush/2026/07/17/
- HuggingFace community: https://huggingface.co/blog/ResterChed/kimi-k3-model-overview-mxfp4-quantization-open-wei
- NxCode benchmark guide: https://www.nxcode.io/resources/news/kimi-k3-benchmarks-coding-agent-evaluation-guide-2026
- OpenRouter: https://openrouter.ai/moonshotai/kimi-k3
