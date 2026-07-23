# 3-Model Cross-Comparison — Routing-Table Example

> **Date:** 2026-07-17
> **Hardware:** NVIDIA RTX 5060 Laptop 8 GB, 80W TGP, 95°C temp cap
> **Session:** 3 models benchmarked in ~110 min total GPU time

## Headline Comparison

| Metrik | qwythos-9b-q6 (qwen35·9.2B·Q6) | yuxin-tau2 (gemma4·11.9B·Q4) | qwen-dsv4-q5 (qwen35·9.0B·Q5) |
|---|---|---|---|
| **Speed (t/s, 160 tok)** | 22.5 | 18.0 | **50.7** |
| **MMLU** | 100% | 100% | 100% |
| **GSM8K** | 91.7% | **100%** | 83.3% |
| **HumanEval** | 70% | **100%** | **100%** |
| **Thinking A (Off)** | 80% | 80% | 80% |
| **Thinking B (On)** | 100% | 90% | 100% |
| **Vision** | 5/5 (CPU-offload) | N/A (no CLIP) | 5/5 (CPU-offload) |
| **Tools** | 5/5 | 5/5 | 5/5 |
| **Context max** | 1M tokens | 128k tokens | 128k tokens |
| **Architecture** | qwen3.5 | gemma4 | qwen3.5 |
| **VRAM (4096 ctx)** | 7.2 GB | 7.9 GB | 6.4 GB |

## Production Routing Table

| Use-Case | Empfehlung | Score | Begründung |
|---|---|---|---|
| **Speed-kritische Apps** | Qwen-DSV4-Q5 | 50.6 t/s | 2× schneller als nächstbeste |
| **Code-Generierung** | Yuxin-Tau2 **oder** Qwen-DSV4-Q5 | 100% HumanEval | Beide perfekt, nach Speed wählen |
| **Mathe/Reasoning** | Yuxin-Tau2 | 100% GSM8K | Einziger mit 100% Reasoning-Durchschnitt |
| **Sehr lange Kontexte (>128k)** | Qwythos-9B-Q6 | 1M Context | einziger mit >128k support |
| **Vision + Speed** | Qwen-DSV4-Q5 | 5/5 + 50 t/s | Einziger mit beidem |
| **Function-Calling** | Alle 3 | 5/5 Tie | Beliebige Wahl |

## Benchmark-Setup Notes

### GPU Load State (valid for the day's numbers)

The speed comparison has a subtle but important confound: qwen-dsv4-q5 was the
**only loaded model** during its speed tests, while qwythos and yuxin were
loaded alongside other models (shared VRAM). If qwen-dsv4-q5 were measured
with 2 other models loaded, expect its speed to drop ~20%.

### Key Architectural Differences

| Eigenschaft | qwythos (qwen35) | yuxin (gemma4) | qwen-dsv4 (qwen35) |
|---|---|---|---|
| **Thinking Format** | XML-tags (`<|im_start|>think`) | Plain-text Markdown | XML-tags (`<|im_start|>think`) |
| **Tool-Call Streaming** | Final chunk | Penultimate chunk | Final chunk |
| **Vision (CLIP)** | 456M projector | None | 456M projector |
| **`think=False` Bug** | response="" wenn think=True | N/A | response="" wenn think=True |
| **SFT** | Empero | S1 | Base (DSV4) |

## Template for N-Model Comparison

When adding model N+1 to this comparison, produce exactly this structure:

```markdown
## Model-N — Key Results on RTX 5060 8GB

| Dimension | Score | Speed | Notes |
|---|---|---|---|
| Speed (160 tok) | XX t/s | — | |
| MMLU | XX% | — | |
| GSM8K | XX% | — | |
| HumanEval | XX% | — | |
| Vision | X/5 | — | CPU-offload? |
| Tools | X/5 | — | |

## Updated Routing Table (N models)

| Use-Case | Best Model | Score | Runner-up |
|---|---|---|---|
| Speed | ... | ... | ... |
| Code | ... | ... | ... |
| ... | ... | ... | ... |
```

### Commit Workflow

Each model gets its own commit sequence:
1. `model-X: add benchmark project + tests`
2. `model-X: add runner config + test prompts`
3. `model-X: add results + reference wiki`
4. `docs: update cross-comparison routing table`

Use `git log --oneline` at the end to produce a clean commit timeline in the
final cross-comparison document.
