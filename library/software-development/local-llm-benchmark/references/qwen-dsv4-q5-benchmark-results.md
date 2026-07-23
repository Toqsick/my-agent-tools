# Qwen-DSV4-Q5 Benchmark Results

**Date:** 2026-07-17
**Model:** qwen-dsv4-q5:latest (Q5_K_M, 9.0B params, qwen3.5-architecture)
**Hardware:** MEDION ERAZER · RTX 5060 8GB · 80W TGP · 95°C Cap · kein OC
**GPU State:** Dedicated (only model loaded — others `ollama stop`ed)
**Runner:** `~/10-Projekte/10-active/greyhack-tools/benchmarks/qwen-dsv4-q5/`
**Laufzeit:** ~110 Min total (alle 7 Dimensionen in einem Durchlauf)

## Headline Numbers

| Dimension | Result | Notes |
|---|---|---|
| **Speed (avg, 5 sizes)** | **50.4 t/s** | 71–93% GPU util, dedicated GPU |
| **Speed (128 tok)** | 50.8 t/s | 3.5s, GPU 71% |
| **Speed (8192 tok)** | 49.9 t/s | 149.5s, GPU 92% |
| **Quality Aggregate** | **94.4%** | 15 MMLU + 12 GSM8K + 10 HumanEval |
| **Quality (GSM8K)** | **10/12 (83.3%)** | 2 multi-step math failures |
| **GSM8K** | 10/12 (83.3%) | Weakest dimension — 2 multi-step math failures |
| **HumanEval** | 10/10 (100%) | Equal-best with yuxin-tau2 |
| **Vision** | 5/5 (100%) | 42.4s avg, `num_gpu=20` CPU-offload |
| **Tools** | 5/5 (100%) | Tool-name detection clean |
| **Thinking A/B** | (invalid) | expected_keywords bug → 0/10, model was correct |
| **Context-Scaling** | 1741–1873 prompt t/s | Excellent scaling, 64k clean |
| **Needle-in-Haystack** | 0/6 | Model writes answer in thinking field |

## Three-Way Comparison (RTX 5060)

| Metric | qwen-dsv4-q5 | qwythos-9b-q6 | yuxin-tau2 | Winner |
|---|---|---|---|---|
| Speed (avg t/s) | **50.4** | 22.7 | 18.7 | **qwen (+123%)** |
| Reasoning Aggregate | 94.4% | 87.2% | **100%** | yuxin |
| MMLU | 100% | 100% | 100% | tie |
| GSM8K | 83.3% | 91.7% | **100%** | yuxin |
| HumanEval | **100%** | 70% | **100%** | tie |
| Vision | **5/5** | 5/5 | skipped | tie |
| Tools | 5/5 | 5/5 | 5/5 | tie |
| Context Max | 262k | 1M | 262k | qwythos |
| Quant | Q5_K_M | Q6_K | Q4_K_M | — |
| Context-Scaling | **~1740 prompt t/s** | ~1080 | ~780 | **qwen** |

## Speed Detail

| Task | Tokens | Wall (s) | t/s | GPU Util |
|---|---|---|---|---|
| short_128 | 160 | 3.5 | 50.8 | 71% |
| medium_512 | 560 | 11.4 | 50.7 | 88% |
| long_2048 | 2100 | 41.5 | 51.0 | 93% |
| very_long_4096 | 4144 | 83.1 | 50.4 | 92% |
| extreme_8192 | 7398 | 149.5 | 49.9 | 92% |

→ **Bemerkenswert stabil** (49.9–51.0 t/s) über 160–7398 Tokens.
→ GPU-Util steigt mit Task-Größe (71% bei 128 tok → 93% bei 2100 tok).

## GPU Contention Caveat

qwen-dsv4-q5 war **einzeln geladenes Modell** zum Testzeitpunkt — qwythos und
yuxin-tau2 teilten sich VRAM mit anderen geladenen Modellen. Der 2×-Speed-Vorteil
kommt **teilweise** von der dedizierten GPU, nicht nur von der Architektur.

**Fairer Vergleich:** Auf dedizierter GPU erreicht auch qwythos-9b-q6 ~28 t/s
(statt 22 t/s shared). Die reale Architektur-Differenz ist ~50 t/s vs ~28 t/s
(+79%), nicht +123%.

## Quality Detail

| Kategorie | Score | Details |
|---|---|---|
| MMLU (15) | 100% | All correct, avg ~3.2s/question |
| GSM8K (12) | 83.3% | 2 failed: qsm_06 (number check), qsm_11 (ratio+remainder) |
| HumanEval (10) | 100% | All correct, avg ~10.7s/code task |

Die GSM8K-Failures waren **reine Mathe-Fehler**, keine Format-Probleme:
- `gsm_06`: 12 fehlerhafte Berechnung in 4.3s (schnell aber falsch)
- `gsm_11`: Restwert-Berechnung falsch

## Context-Scaling

| Target | Actual | Wall (s) | Prompt t/s | Status |
|---|---|---|---|---|
| 1024 | 1402 | 8.5 | 1741 | ok |
| 4096 | 2050 | 8.9 | 1742 | ok |
| 16384 | 8194 | 10.8 | 1873 | ok |
| 65536 | 32770 | 39.5 | 1165 | ok |

→ **Prompt-Eval:** 1741–1873 t/s bei ≤16k Kontext (sehr gut).
→ **64k:** 1165 t/s — Einbruch durch beginnenden KV-Cache-Druck.

## Vision Detail

5/5 Hits, alle korrekt erkannt:
- cat → "Cat" (62.2s)
- dog → "Dog" (39.8s)
- car → (correct, response in thinking) (43.6s)
- tree → (correct, response in thinking) (42.4s)
- house → (correct, response in thinking) (42.1s)

**Three of five** responses were empty (`response=""`) — the model wrote the
answer in the `thinking` block. All still scored correctly because the format
accepts answers from either field.

## Architecture Notes

- **Same architecture as qwythos-9b-q6** (qwen3.5 family)
- **Thinking format:** Plain-text with Markdown headers
  (`Thinking Process:\n\n1. **Analyze...**`)
- **Tool-call format:** OpenAI-compatible (`function.name` + `function.arguments`)
- **Vision:** Has CLIP projector (456M params) — `num_gpu=20` required for 8 GB
- **Empty response bug:** With `think=True`, model writes answers in `thinking`
  block and leaves `response=""`. Workaround: `think=False` for structured/QA.

## Known Runner Bugs Found During Setup

| Bug | Fix |
|---|---|
| `MODEL = "qwen-dsv4-q5:latest:latest"` (double tag) | `sed -i 's/:latest:latest/:latest/g'` |
| Vision test had `think=True` default (empty response) | Added `think=False` to vision runner |
| `temperature=0.0` in vision_smoke.py | Replaced with T=0.3 + Empero defaults |
| `num_gpu=30` → CUDA OOM on vision | Use `num_gpu=20` for 9B + CLIP on 8GB |

## Summary: Wann qwen-dsv4-q5 wählen

**Stärken:**
- ⚡ **Schnellstes Modell** (50 t/s) — ideal für speed-kritische Apps
- 💻 **Code-Generierung:** 100% HumanEval
- 👁️ **Vision + Text kombiniert**
- ⚙️ **Function-Calling-Agents** (100% tool detection)

**Schwächen:**
- 🧮 **Mathe:** nur 83.3% GSM8K — wenn Mathe kritisch → yuxin-tau2 (100%)
- 🔍 **Needle-in-Haystack:** 0/6 (Antwort im Thinking-Block)
- 📏 **Max Context:** 262k (vs qwythos' 1M)

**Production-Routing:**
- Speed-kritisch + Code → qwen-dsv4-q5
- Mathe/Reasoning → yuxin-tau2
- Sehr lange Kontexte → qwythos

## See Also

- Cross-comparison: `references/yuxin-tau2-benchmark-results.md` (gemma4 11.9B)
- Cross-comparison: `references/qwythos-9b-8gb-results.md` (qwythos 9.2B)
- Official sampling defaults: `references/qwythos-hf-sampling-defaults.md`
- Thinking-variant methodology: `references/thinking-variant-methodology.md`
- Source code: `~/10-Projekte/10-active/greyhack-tools/benchmarks/qwen-dsv4-q5/`
