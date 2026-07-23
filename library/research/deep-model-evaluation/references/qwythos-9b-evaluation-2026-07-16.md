# Qwythos-9B Real-Test — 3-Wege-Benchmark (2026-07-16)

## Setup

| Metrik | Wert |
|---|---|
| Hardware | RTX 5060 Laptop 8 GB VRAM (7.5 GB nutzbar) |
| Ollama | v0.30.11, systemd-service, `OLLAMA_FLASH_ATTENTION=1` |
| Modelfile-Fix | `RENDERER qwen3.5` + `PARSER qwen3.5` (alle Modelle) |
| Temperatur | `temperature=0.0` (deterministisch) |
| max_tokens | 1000 (Tasks 1-3), 2000 (Task 4) |
| Warmup | `"Reply only: OK"` vor jedem Modell, 1. Response verwerfen |

## Modelle unter Test

| Modell | File-Größe | VRAM | Parameter |
|---|---|---|---|
| **Qwythos-9B-Claude-Mythos-5-1M** Q4_K_M | 6.81 GB | 6.2 GB | 9B, Qwen3.5-Basis |
| **Ornith-1.0-9B** Q5_K_M | 6.47 GB | 6.3 GB | 9B, Qwen3.5-Basis |
| **Gemma 4 E4B-it** Q4_K_M | 6.0 GB | 4.6 GB | 8B, MoE 3.6B-active |

## 4 Tasks

### T1: FizzBuzz (Python, deterministisch)

| Modell | Lat | tok/s | Reasoning | Answer | Korrekt? |
|---|---|---|---|---|---|
| **🏆 Qwythos** | 15.5s | **27.2** | 1238c | 57c | ✅ |
| Ornith | 25.6s | 14.9 | 836c | 57c | ✅ |
| Gemma | 20.1s | 1.7 | 0c | 57c | ✅ |

### T2: Python Sort (Quicksort mit Type Hints)

| Modell | Lat | tok/s | Reasoning | Answer |
|---|---|---|---|---|
| **🏆 Qwythos** | 14.4s | **28.4** | 1615c | 37c |
| Ornith | 22.5s | 14.2 | 886c | 72c |
| Gemma | 24.2s | 12.2 | 972c | 97c |

### T3: Bug-Diagnose (`avg(nums)` Division by Zero)

| Modell | Lat | tok/s | Reasoning | Answer |
|---|---|---|---|---|
| **🏆 Qwythos** | 20.2s | **33.8** | 2463c | 295c |
| Gemma | 33.7s | 25.7 | 1950c | 1134c |
| Ornith | 21.5s | 20.2 | 808c | 830c |

### T4: German Explain (Decorators auf Deutsch)

| Modell | Lat | tok/s | Reasoning | Answer |
|---|---|---|---|---|
| **🏆 Ornith** | 28.0s | **22.9** | 2388c | 291c |
| Qwythos | 16.4s | 17.9 | 960c | 280c |
| Gemma | 28.1s | 16.7 | 1612c | 324c |

## Aggregate

| Rang | Modell | Wins | Avg tok/s | Avg Reasoning |
|---|---|---|---|---|
| **🥇 #1** | **Qwythos-9B Q4_K_M** | 3/4 | **27.0** | 1569c |
| **🥈 #2** | Ornith-1.0-9B Q5_K_M | 1/4 | 18.1 | 1230c |
| **🥉 #3** | Gemma 4 E4B-it Q4_K_M | 0/4 | 14.1 (variable) | 1134c |

## Warum Qwythos schneller trotz tieferem Reasoning

1. **Tieferes Reasoning** (avg 1569c vs 1230c Ornith) — Modell "denkt" mehr
2. **Aber kürzere Output-Direct-Tokens** (avg 167c vs 313c Ornith) — kürzere Latenz
3. **Vermutlich bessere Token-Effizienz** durch Claude-Reasoning-Trace-Training
4. **YaRN-Rope-Scaling (1M ctx)** könnte Attention-Efficiency verbessern

## Tool-Use Test

- **Single Tool Call:** Qwythos → sauberes `tool_calls` mit `run_shell`
- **Multi-Turn:** Qwythos → verarbeitet Tool-Result, synthetisiert Antwort
- **Reasoning-Field:** Ollama v0.30 verwendet `reasoning` (nicht OpenAI's `reasoning_content`)

## Qwythos-Modelfile-Template

```dockerfile
FROM hf.co/empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF:Q4_K_M
RENDERER qwen3.5
PARSER qwen3.5
PARAMETER temperature 1.0
PARAMETER top_p 0.95
PARAMETER top_k 20
PARAMETER num_ctx 8192
PARAMETER repeat_penalty 1.0
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"
```
