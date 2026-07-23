# Hardware & VRAM Deep Dive

Comprehensive guide to choosing hardware for local LLM inference, why
VRAM matters, and what to expect from CPU offloading.

## Why VRAM >> DDR5 for LLMs

Viele fragen: "Warum kann man nicht einfach DDR5 RAM nutzen? Der ist groß
genug!" Hier die Architektur-Erklärung:

| Komponente             | Speicherbandbreite | Rechenleistung           |
|------------------------|--------------------|--------------------------|
| **RTX 5060 (GDDR7)**   | **~320 GB/s**      | **~15 TFLOPS (2560 CUDA)** |
| **DDR5-6000 (dual)**   | **~48 GB/s**       | **~0.5 TFLOPS (16 CPU)** |

Ein LLM zu inferencen bedeutet: **Jedes einzelne Wort muss das GEWICHT des
gesamten Modells durch alle Neuronen jagen.**

- **VRAM-only:** Modell liegt direkt auf der GPU. Jeder Token = 1 Durchlauf
  durch alle Parameter. GPU macht 2560 Matrix-Multiplikationen gleichzeitig
  → **~50-80 Tok/s**
- **CPU + DDR5:** Gleiche Rechnung, aber:
  1. CPU muss die Mathe machen → **50x langsamer pro Operation** (16 Kerne
     statt 2560 CUDA Cores)
  2. Jeder Layer der nicht im VRAM ist, wird via PCIe nachgeladen →
     **Latenz-Flaschenhals**
  3. Das bremst **linear** mit dem Anteil der CPU-Layer

**DDR5 ist für LLMs nicht geeignet** weil:

- CPU hat nicht genug parallel Cores (16 vs 2560)
- DDR5-Bandbreite (48 GB/s) reicht nicht für die Gewichts-Matrix-Durchläufe
  (braucht >200 GB/s für flüssige Inferenz)
- Jeder CPU-Offload-Layer kostet ~50ms extra Latenz (PCIe-Transfer + CPU-Berechnung)

## CPU-Offloading Performance

Wenn ein Modell nicht vollständig in VRAM passt, wird ein Teil via PCIe
nachgeladen:

```
GPU (8GB):   ████████░░  <-- 8 von 9 GB im VRAM (schnell)
CPU (DDR5):  ░░░░░░░░█  <-- 1 GB via PCIe (50x langsamer pro Layer)
→ Result: ~4-7 tok/s statt ~60-80 tok/s
```

Der Bottleneck ist PCIe-Bandbreite (~32 GB/s) vs VRAM-Bandbreite (~320 GB/s) —
roughly 10x slower, und CPU compute ist ~30x slower per operation als GPU
CUDA cores. Kombiniert: ~4-7 tok/s für ein 14B-Modell auf 8GB VRAM.

**PCIe 5.0 advantage:** Karten wie die RTX 5060 haben einen schnelleren
PCIe-Bus, was RAM-Swap spürbar glatter macht als PCIe 4.0 Karten. Trotzdem
langsamer als native GPU-Inferenz.

## Sizing Rule of Thumb

| Parameter Count | Quantized Size (Q4) | Fits in VRAM?                        |
|-----------------|---------------------|--------------------------------------|
| 7-8B            | ~4-5 GB             | Yes (4-8 GB VRAM)                    |
| 14B             | ~9 GB               | Tight (needs 8GB+ VRAM)              |
| 32B             | ~19 GB              | No — needs RAM swap (16GB+ system RAM) |
| 70B             | ~30-40 GB           | No — heavy RAM swap (32GB+ system RAM) |

## Quantization Trade-offs

| Format | Size Factor | Quality vs FP16 | Use Case                       |
|--------|-------------|------------------|--------------------------------|
| FP16   | 2.0×        | 100% (baseline)  | Research, max quality          |
| Q8_0   | 1.0×        | ~99.5%           | Marginal quality gain, +50% size |
| Q4_K_M | 0.6×        | ~98%             | **Default, best balance**      |
| Q3_K_M | 0.45×       | ~95%             | Tight VRAM, noticeable loss    |
| Q2_K   | 0.35×       | ~90%             | Emergency only, broken output  |

## MoE Models (Mixture of Experts)

Models with "aXb" in the name (e.g., `qwen3.6-35b-a3b`) activate only the
smaller number of parameters per token. Beispiel: 35B total params but only
3B active → fast like 3B, smart like 35B. Diese sind oft die beste Wahl
wenn über einen Cloud-Provider verfügbar.

**Caveat:** Auch MoE muss den Basis-Speicher allokieren können — die
"aktiven" 3B werden zur Laufzeit aus dem Gesamt-Pool selektiert, aber
alle 35B müssen resident sein.

## GPU Compatibility Checklist

Bevor du Ollama installierst:

- [ ] NVIDIA GPU mit CUDA-Support (RTX-Serie ab 2018, alle funktionieren)
- [ ] Aktueller NVIDIA-Treiber (`nvidia-smi` muss funktionieren)
- [ ] Mindestens 4 GB VRAM (8 GB empfohlen für 7B/8B in voller Geschwindigkeit)
- [ ] 32 GB freier Festplattenspeicher für Modelle
- [ ] 16 GB+ System-RAM wenn du CPU-Offload nutzen willst

## RTX 5060 Laptop (8GB VRAM) — Real-World Benchmarks

Siehe `references/rtx-5060-benchmarks.md` für konkrete Messungen mit
DeepSeek R1 Distill Varianten. Kurzfassung:

| Modell           | VRAM-Nutzung | Geschwindigkeit  | Qualität           |
|------------------|--------------|------------------|--------------------|
| deepseek-r1:7b   | ~5 GB        | ~80-100 tok/s    | ⭐⭐⭐              |
| deepseek-r1:8b   | ~5.2 GB      | ~30-50 tok/s     | ⭐⭐⭐⭐            |
| deepseek-r1:14b  | 8GB+1GB swap | ~4-7 tok/s       | ⭐⭐⭐⭐⭐          |
| qwen2.5:7b       | ~5 GB        | ~80-100 tok/s    | ⭐⭐⭐              |
| qwen3.5:9b       | ~6 GB        | ~50-70 tok/s     | ⭐⭐⭐⭐            |