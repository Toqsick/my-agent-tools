# Qwen3.5-Family Reasoning-Loop Bug & 5-Way Benchmark

**Captured:** 2026-07-16  
**Hardware:** RTX 5060 Laptop 8 GB VRAM, Intel i7-13620H  
**Ollama:** v0.30.x systemd-service, CUDA backend  
**Models tested:** Qwen3.5-9B (Original), Qwythos-9B (Claude-Mythos-5 SFT), Ornith-1.0-9B (DeepReinforce RL), Qwen3.5-9B-DeepSeek-V4-Flash (distill SFT), Gemma 4 E4B-it

---

## 1. The Loop Bug

### Symptom
When a Qwen3.5-9B base model (without SFT/RL post-training) runs on Ollama, it generates **14.000+ characters of reasoning** content via the `reasoning` field and **never produces a final `content` answer**. The response hits `finish_reason='length'` and returns empty.

### Original (qwen35-9b-local, T=0, max_tokens=4096, FizzBuzz):
- Reasoning: **14.869 chars** (filled with repetitive self-correction)
- Answer: **0 chars** — never reached the final output
- Finish: `length` (truncated)

### Same model with RENDERER qwen3.5 + PARSER qwen3.5 fix applied:
- Reasoning: 3.631 chars (at max_tokens=2048)
- Answer: 72 chars — got through **sometimes** with small prompts
- Still vulnerable to loop at larger contexts

### Qwythos (SFT post-training, same architecture):
- Reasoning: 1.238 chars (FizzBuzz), 1.615 chars (Python sort)
- Answer: 57c → sauber ✅

### Root Cause
The Qwen3.5 base model's chat template has insufficient stop-token discipline for Ollama's GGUF pipeline. The `RENDERER qwen3.5` fix is necessary but not sufficient — it fixes blank-output but the base model itself was not post-trained to **stop reasoning and answer**. SFT/RL training teaches the model to transition from thinking → answering. Without it, the model loops in reasoning indefinitely.

---

## 2. 5-Way Speed Benchmark (Python sort, T=0, max_tokens=2048)

| Rang | Modell | tok/s | Reasoning (chars) | Answer (chars) | Quality |
|---|---|---|---|---|---|
| 🥇 | **Qwen3.5-Original** (mit Fix) | 26.5 | 3.631c ⚠️ | 72c | Korrekt, aber Loop-Trap |
| 🥈 | **Qwythos Q4_K_M** | 22.2 | 1.615c | 37c | ✅ Sweet-Spot |
| 🥉 | **Qwen-DSV4-Flash Q5_K_M** | 14.7 | 1.193c | 54c | ✅ Stabil |
| #4 | **Ornith Q5_K_M** | 14.7 | 886c | 72c | ✅ Effizient |
| #5 | **Gemma 4 E4B-it Q4_K_M** | 10.3 | 972c | 97c | ✅ Korrekt |

### Additional test: FizzBuzz (T=0, max_tokens=4096)

| Modell | tok/s | Reasoning | Answer | Finish |
|---|---|---|---|---|
| Qwen3.5-Orig (mit Fix) | 54.3 (raw) | **14.869c ❌** | 0c | length |
| Qwythos Q4_K_M | 19.9 | 1.238c | 57c | stop ✅ |
| Ornith Q5_K_M | 15.0 | 836c | 57c | stop ✅ |

---

## 3. Family Analysis

All four Qwen3.5-9B based models share the same architecture. The difference is **post-training**:

| Model | Post-Training | Effect on Reasoning | Effect on Speed | Production-Ready? |
|---|---|---|---|---|
| **Qwen3.5-Original** | None (base) | 3.6K-14.8K chars (looping) | 26.5 tok/s (fastest raw) | ❌ Not without loop control |
| **Qwythos** | SFT on 500M Claude-Reasoning traces | 1.2K-1.6K chars (focused) | 22.2 tok/s (fast) | ✅ Yes |
| **Ornith** | DeepReinforce RL (Mamba-2 hybrid) | 836-886 chars (concise) | 14.7 tok/s (stable) | ✅ Yes |
| **DSV4-Flash** | Distill SFT from DeepSeek-V4 | 1.1K-1.2K chars (analytical) | 14.7 tok/s (stable) | ✅ Yes |

---

## 4. Recommendations for 8GB VRAM (RTX 5060)

| Use Case | Best Model | Quant | Size | Speed | Why |
|---|---|---|---|---|---|
| **Coding Co-Pilot** | **Qwythos Q4_K_M** | Q4_K_M | 6.8 GB | 22.2 tok/s | Best speed/quality, 1M ctx option |
| **Reasoning Specialist** | **DSV4-Flash Q5_K_M** | Q5_K_M | 7.4 GB | 14.7 tok/s | Deep analytical thinking |
| **Stable Backup** | **Ornith Q5_K_M** | Q5_K_M | 6.5 GB | 14.7 tok/s | MIT, etabliert, Mamba-effizient |
| **Raw Speed (toy only)** | Qwen3.5-Original Q4_K_M | Q4_K_M | 6.8 GB | 26.5 tok/s | Loop-Bug makes it risky |
| **Don't use** | Gemma 4 E4B | Q4_K_M | 6.0 GB | 10.3 tok/s | MoE cost, slowest |

---

## 5. Setup Notes

### Modelfile Pattern (ALL Qwen3.5-based models)
```dockerfile
FROM hf.co/<org>/<repo>:<quant>
RENDERER qwen3.5        # CRITICAL — ohne fix sind Antworten leer
PARSER qwen3.5           # CRITICAL — ohne fix parst Ollama falsch
PARAMETER temperature 0.6
PARAMETER top_p 0.95
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"
```

### Quick Loop Test
```bash
ollama run <model> "Print FizzBuzz from 1 to 15. One per line."
# Wenn Modell >30s denkt ohne Output → Loop. Abbruch + nur Fine-Tuned nutzen.
```

### Ollama Create-Race Workaround
DSV4-Flash Q4_K_M hängt reproduzierbar beim `ollama create`. Workaround:
- **Q5_K_M Quant verwenden** umgeht den Bug
- Oder: `pkill -f "ollama create"` + einzeln neu starten

---

## 6. Errata

- DSV4-Flash Q4_K_M Create-Bug: reproduzierbarer Ollama-Race auf v0.30.x
  - Workaround: Q5_K_M Quant (6.5 GB statt 5.6 GB, funktioniert)
  - Memory ID `1fa89d6720ab16c3` — recurred in this session
- Qwen3.5-Original wird fälschlicherweise als "schnellstes" Modell bewertet
  - Das stimmt nur für raw tok/s — mit Loop-Bug ist es unbrauchbar für Production
