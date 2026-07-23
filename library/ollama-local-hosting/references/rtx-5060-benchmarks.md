# RTX 5060 Laptop Benchmarks (8GB VRAM)

Real-world performance measurements for Ollama on a Basti RTX 5060 Laptop
with 8GB GDDR7 VRAM. Tests use temperature=0 (deterministic mode) unless
stated. Updated: 2026-07-16 (6-way comparative benchmark).

## Hardware Specs

- **GPU:** NVIDIA GeForce RTX 5060 Laptop (8GB GDDR7)
- **VRAM:** 8 GB (compute 12.0)
- **System RAM:** 32 GB DDR5
- **CPU:** Intel i7-13620H (10c/16t)
- **PCIe:** Gen 5 (laptop slot, x8 effective)
- **VRAM split:** ~6.5-6.6 GB reserved by Ollama, ~1.0-1.4 GB free
- **OS:** Zorin OS 18.1 (Ubuntu 24.04), NVIDIA driver 570+

## 6-Way Comparative Benchmark (2026-07-16)

### Test-Protokoll
- **Prompt T1:** "Write Python code that sorts a list of integers. No comments."
- **Prompt T2:** Bug-Diagnose (division by zero in avg(nums))
- **Settings:** `temperature=0.0, max_tokens=2000` (T2: 1500)
- **API:** Ollama `/v1/chat/completions` via Python requests

### T1: Python sort

| Rang | Modell | Größe | Lat | tok/s | Reasoning | Answer |
|---|---|---|---|---|---|---|
| 🥇 | **Qwythos Q4_K_M** | 6.81 GB | 24.5s | **16.6** | 1615c | 37c |
| 🥈 | **Ornith Q5_K_M** | 6.55 GB | 27.4s | 11.6 | 886c | 72c |
| 🥉 | Qwen3.5-DSV4 Q5 | 7.39 GB | 29.4s | 10.0 | 1193c | 54c |
| #4 | yuxin-tau2 (12B Q4) | 7.39 GB | 29.9s | 3.9 | 351c | 60c |
| #5 | yuxin-coder-v1 (12B Q4) | 7.39 GB | 62.4s | 2.5 | 493c | 60c |
| #6 | xentriom 12B Q8_0 | 12.6 GB | 75.4s | 2.0 | 508c | 60c |

### T2: Bug-Diagnose (avg(nums))

| Rang | Modell | Lat | tok/s | Reasoning | Answer |
|---|---|---|---|---|---|
| 🥇 | **Qwythos Q4_K_M** | 25.7s | **16.9** | 2200c | 280c |
| 🥈 | **Ornith Q5_K_M** | 21.5s | 20.2 | 808c | 830c |
| 🥉 | Qwen3.5-DSV4 Q5 | ~30s | ~10 | ~1200c | ~300c |
| #4 | yuxin-tau2 (12B Q4) | 34.6s | 5.1 | 250c | 297c |
| #5 | yuxin-coder-v1 (12B Q4) | 41.4s | 4.6 | 258c | 305c |
| #6 | xentriom 12B Q8_0 | 77.4s | 2.5 | 365c | 310c |

### Aggregate

| Rang | Modell | Avg tok/s | Wins |
|---|---|---|---|
| **🥇** | **Qwythos Q4_K_M** | **16.8** | 2/2 |
| **🥈** | **Ornith Q5_K_M** | 15.9 | 1/2 |
| **🥉** | Qwen3.5-DSV4-Flash Q5 | 10.0 | 0/2 |
| #4 | yuxin-tau2 (12B Q4) | 4.5 | 0/2 |
| #5 | yuxin-coder-v1 (12B Q4) | 3.5 | 0/2 |
| #6 | xentriom 12B Q8_0 | 2.3 | 0/2 |

**Key finding: 12B models are 4-7× slower than 9B on 8GB VRAM due to
mandatory layer-split. All 9B models (Q4 or Q5) fit entirely in VRAM.**

## 12B-on-8GB Penalty Analysis

VRAM allocation for each model class:

| Class | Quant | Model VRAM | GPU Layers | Layer-Split |
|---|---|---|---|---|
| 9B Q4_K_M | ~5.2 GB | Ollama ~6.6 GB used | 33/33 = full GPU | ❌ Keiner |
| 9B Q5_K_M | ~6.5 GB | Ollama ~6.6 GB used | 31-33/33 = full GPU | ❌ Keiner |
| 12B Q4_K_M | ~7.4 GB | Ollama ~7.0 GB used | ~24/33 GPU | ✅ Starker Split |
| 12B Q8_0 | ~12 GB | Ollama ~6.6 GB used | ~16/33 GPU | ✅ Sehr starker Split |

**Why 12B fails on 8GB VRAM:**
- Every layer that fits in VRAM → GPU inference (fast)
- Every layer that spills to CPU → slow RAM inference + PCIe transfer
- Each forward pass = 33 layers × (split penalty)
- The more layers offloaded, the more CPU↔GPU transfers per token

**Conclusion:** Layer-split halves the effective GPU budget. A 12B Q4 that
nominally fits in 8GB still spills because Ollama's CUDA allocator reserves
overhead (KV cache, intermediate buffers). Only models that fit with ≥20%
VRAM headroom avoid the split entirely.

## Model Ranking for 8GB VRAM (aktuell)

| Rank | Modell | Family | Speed | Reasoning | Notes |
|---|---|---|---|---|---|
| 🥇 | Qwythos Q4_K_M | Qwen3.5 9B | 16-17 tok/s | 1200-2500c | Champion — 1M context, R1-like |
| 🥈 | Ornith Q5_K_M | Qwen3.5 9B | 12-20 tok/s | 800-1600c | Stable backup, Mamba layers |
| 🥉 | Qwen3.5-DSV4-Flash Q5 | Qwen3.5 9B | 10 tok/s | 1000-1200c | DeepSeek-V4 SFT, Reasoning |
| #4 | yuxin-tau2 (12B) | Gemma-4 12B | 4-5 tok/s | 250c | Tool-use trained; slow |
| #5 | yuxin-coder-v1 (12B) | Gemma-4 12B | 2-5 tok/s | 250-500c | Coding focused; very slow |
| #6 | xentriom 12B Q8_0 | Gemma-4 12B | 2-3 tok/s | 350-500c | Highest quality; unusable |

## Quant Comparison (Ornith 9B, T=0)

| Quant | Size | tok/s | Quality |
|---|---|---|---|
| Q5_K_M | 6.55 GB | 10-20 | Referenz (mit RENDERER qwen3.5 Fix) |
| Q4_K_M | ~5.2 GB | 16+ | Schneller, leichtere Qualitätseinbusse |

**Q8_0** (6.5-12 GB je nach Modellklasse): Nicht empfohlen für 8GB VRAM.
Der doppelte Layer-Split-Overhead wiegt schwerer als rein GPU-inferierter
Q4_K_M. Auf 16+ GB VRAM ist Q8_0 die richtige Wahl.

## Qwen35-9b Family: RENDERER Fix Notwendig

Alle Qwen3.5-basierten GGUFs (Ornith, Qwythos, DSV4-Flash) benötigen diesen
Fix im Modelfile, sonst leere Responses:

```dockerfile
FROM hf.co/<ns>/<model>:<quant>
RENDERER qwen3.5
PARSER qwen3.5
```

**Verifiziert (2026-07-16):**
- Ornith: Reasoning von 836c (ohne Fix) → 2598c (mit Fix)
- Qwythos: Voll funktionsfähig mit 1M Context
- Qwen3.5-Original (ohne SFT): Nicht produktiv — Reasoning-Loop trotz Fix
  (14K+ chars, nie zur Antwort kommend)

## Performance Settings (Recommended)

```ini
OLLAMA_VULKAN=false        # CUDA on NVIDIA
OLLAMA_FLASH_ATTENTION=true
OLLAMA_MAX_LOADED_MODELS=1 # critical for 8GB
OLLAMA_KEEP_ALIVE=15m
OLLAMA_NUM_PARALLEL=1
```

Verify CUDA picked:
```bash
journalctl -u ollama --since="1 minute ago" --no-pager | grep "library="
# library=CUDA compute=12.0 name="NVIDIA GeForce RTX 5060 Laptop"
```

## Context Length Overhead (gemessen)

With `OLLAMA_CONTEXT_LENGTH=64000`:

| num_ctx | VRAM overhead | Speed impact |
|---|---|---|
| 4096 | minimal | none |
| 32768 | ~500 MB | 10-15% |
| 64000 | ~1 GB | 15-25% |

## Qwythos Special: 1M Kontext

Qwythos-9B-Claude-Mythos-5-1M unterstützt laut Author 1M Context-Length.
Realistisch auf 8GB VRAM bei ~32K Context (VRAM-Limit). Die 1M Option ist
nur auf 24+ GB VRAM oder CPU-offloaded nutzbar.
