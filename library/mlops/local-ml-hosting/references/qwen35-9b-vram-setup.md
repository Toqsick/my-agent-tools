# Qwen3.5-9B on 8GB VRAM — Konkrete Setup-Referenz

> **Stand:** 2026-07-14 · **GPU:** NVIDIA RTX 5060 Laptop 8GB (7684 MiB free)
> **Ollama:** system-service (User=ollama), Version 0.30.11
> **Modell:** `qwen35-9b-local` (custom) · **Base:** `hf.co/unsloth/Qwen3.5-9B-MTP-GGUF:Q4_K_M`

## Warum custom Modelfile zwingend ist

Ollama ignoriert `OLLAMA_CONTEXT_LENGTH` und `~/.ollama/config.yaml` auf GPUs mit ≤8 GB VRAM.
Es fällt still auf ein VRAM-basiertes Default zurück (oft nur 4096 Kontext).

**Einziger Fix:** Custom Modelfile mit explizitem `PARAMETER num_ctx`.

## Produktions-Modelfile

```bash
# ~/.ollama/custom-models/qwen35-9b-local.modelfile
FROM hf.co/unsloth/Qwen3.5-9B-MTP-GGUF:Q4_K_M

PARAMETER num_ctx 16384
PARAMETER num_batch 4
PARAMETER num_predict 8192
PARAMETER temperature 0.6
PARAMETER top_p 0.95
PARAMETER top_k 20
PARAMETER repeat_penalty 1.05
```

Erstellen:
```bash
ollama create qwen35-9b-local -f ~/.ollama/custom-models/qwen35-9b-local.modelfile
```

## VRAM-Budget (real gemessen für Qwen3.5-9B Q4_K_M MTP)

| Komponente | Größe | Erklärung |
|------------|-------|-----------|
| **Model weights** | ~5.9 GB | Q4_K_M ≈ 4.5 bpw, 9B Parameter |
| **KV Cache bei 16k** | ~1.7 GB | MTP head braucht etwas mehr |
| **Gesamt bei 16k** | ~7.6 GB | Passt auf 8 GB (7684 MiB frei) |
| **Gesamt bei 32k** | ~9.3 GB | → CPU-Offload oder OOM |
| **Gesamt bei 128k** | ~18+ GB | Marketing — unmöglich auf 8 GB |

**Realistisches Maximum auf RTX 5060 8GB:** 24k Kontext (Swap-Risiko), 16k komfortabel.

## Qwen3.5-Spezifische Fallstricke

### ⚠️ KV-Cache-Quantisierung NICHT verwenden

Qwen3.5-MTP **unterstützt keine KV-Cache-Quantisierung** (`OLLAMA_KV_CACHE_TYPE=q8_0`).
Das Setzen dieser Option produziert **garbled output** (wirre Zeichen, Sprachmüll).

**Fix:** Kein `OLLAMA_KV_CACHE_TYPE` setzen. Default (FP16) funktioniert korrekt.

### ⚠️ num_batch 4 verhindert GGML_ASSERT-Crash

Ohne `num_batch 4` bei Kontext ≥ 8k:
```
GGML_ASSERT(n_inputs < GGML_SCHED_MAX_SPLIT_INPUTS) failed
```
→ Server-Prozess terminiert mit 500 Internal Server Error.

### ⚠️ num_predict zu niedrig

Ollama-Default `num_predict=128` → Modell hört nach 128 Tokens auf.
Qwen3.5 gibt dann leere `<think>`-Blöcke oder verstümmelte Antworten.
**Fix:** Mindestens `num_predict 4096`, empfohlen `8192`.

### Vergleich: Qwen3.5-MTP vs plain

| Feature | MTP (Multi-Token-Prediction) | Plain |
|---------|------------------------------|-------|
| Dateigröße | ~5.9 GB (Q4_K_M) | ~5.7 GB |
| Inference-Speed | **~20-25% schneller** (parallelisiert) | Standard |
| Qualität | identisch bis besser | Baseline |
| Verfügbarkeit | `hf.co/unsloth/Qwen3.5-9B-MTP-GGUF` | separate Tags |

→ **MTP ist klar zu bevorzugen** auf 8 GB VRAM.

## Ollama als System-Service

```bash
# Status
systemctl status ollama
# → User=ollama, Group=ollama, ExecStart=/usr/local/bin/ollama serve

# Start/Stop
sudo systemctl start ollama
sudo systemctl stop ollama

# Alias in ~/50-System/bin/lokalDS-on:
# → sudo systemctl start ollama
# (nicht systemctl --user — das funktioniert nicht, da ollama system-service ist)
```

## Test-Workflow

```bash
# 1. Modell starten
sudo systemctl start ollama
sleep 2

# 2. CLI-Chat-Test (kurz)
ollama run qwen35-9b-local "Sag kurz Hallo"

# 3. API-Test (OpenAI-kompatibel)
curl -s http://127.0.0.1:11434/api/generate \
  -d '{"model":"qwen35-9b-local","prompt":"1+1=","stream":false}' | \
  jq -r '.response'

# 4. GPU-Auslastung prüfen
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv -l 1
# → 60-95% GPU util, ~7400-7600 MiB VRAM bei 16k Kontext

# 5. VRAM nach Stop freigeben
sudo systemctl stop ollama
nvidia-smi | grep -E "RTX|Memory"
# → unter 200 MiB (Ollama entladen)
```

## Community-Meinung zu Qwen3.5-9B auf 8 GB

**Bottom Line:** Qwen3.5-9B MTP Q4_K_M ist **DER sweet spot** für 8-GB-GPUs im Juli 2026.
- Besser als DeepSeek-R1-Distill-14B (zu groß, CPU-offload dominant)
- Besser als Llama 3.1-8B (kleinerer Kontext, schwächeres Reasoning)
- Besser als Qwythos-9B v1/v2 (Marketing-hype, instabil bei Reasoning)
- Qwen3.6 14B (A2.2B MoE) wäre theoretisch besser, aber zu groß für 8 GB