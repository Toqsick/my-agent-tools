---
name: local-ml-hosting
description: >-
  Use when user asks for hosting and evaluating models on local hardware, selecting an Ollama model for available VRAM, troubleshooting model pulls or GPU offload, or comparing local inference backends. NOT for deploying a public cloud API or fine-tuning model weights. Combines practical Ollama installation, model sizing, service operation, compatibility warnings, and local evaluation guidance.
version: 1.2.0
author: Hermes Agent (curator consolidation)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - ollama
    - local-models
    - self-hosted
    - llm-evaluation
    - lm-eval
    - vram
    - gguf
    related_skills:
    - deep-model-evaluation
    - hermes-admin
    - security-audit
lane: worker-heavy
reasoning_effort: xhigh
trigger_keywords: ['model', 'local', 'and', 'ollama', 'local-ml-hosting']
keywords: ['model', 'local', 'ollama', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['ollama-local-hosting', 'local-llm-benchmark', 'deep-model-evaluation']
---



# Local ML Hosting & Evaluation

Covers: Ollama installation, model selection, Hermes integration, context-length pitfalls, and LLM evaluation benchmarks.

## Ollama Installation & Model Selection

See `references/ollama-local-hosting.md` for full guide.

### Quick Reference
```bash

set -euo pipefail
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Model selection by VRAM
# 4-6 GB:  deepseek-r1:7b, llama3.1:8b, qwen2.5:7b
# 8 GB:   deepseek-r1:8b (fast), deepseek-r1:14b (slow, CPU-offload)
# 12 GB:  qwen2.5:32b (partial), llama3.1:70b (heavy swap)
# 16+ GB: llama3.1:70b, qwen2.5:32b

# Pull model
ollama pull deepseek-r1:8b

# List installed
ollama list
```

### VRAM Budget (Q4_K_M) — gemittelt über 7B-9B Modelle
| num_ctx | weights | KV cache | total | 8GB GPU | Modellbeispiel |
|---------|---------|----------|-------|---------|----------------|
| 8k | 5.5 GB | 1.0 GB | 6.5 GB | ✓ | DeepSeek-R1:8b |
| 16k | 5.5 GB | 2.1 GB | 7.6 GB | ✓ tight | Qwen3.5-9B **MTP** = ~7.6 GB |
| 24k | 5.5 GB | 3.2 GB | 8.7 GB | ⚠ swap risk | Qwen3.5-9B plain |
| 32k | 5.5 GB | 4.2 GB | 9.7 GB | ❌ OOM | — |

**⚠️ VRAM-Angaben sind modellabhängig.** Qwen3.5-9B MTP Q4_K_M = ~5.9 GB weights (vs ~5.5 GB für 7B). Die MTP-Variante braucht etwas mehr VRAM durch den Prediction-Head. Siehe `references/qwen35-9b-vram-setup.md` für konkrete Messungen.

## Top-Empfehlung für 8-GB-GPUs (Q4_K_M)

| Modell | Ranking | Begründung |
|--------|---------|------------|
| **Qwen3.5-9B MTP** | 🥇 | Sweet Spot: schnell, 32k+ native ctx, starkes Reasoning. Keine KV-Cache-Quantisierung (garbled output). |
| **Ornith-1.0-9B Q5_K_M** | 🥇 | Qwen3.5-9B post-trained mit Mamba-2 Linear Attention (75% Layer). **49-50 tok/s** auf RTX 5060, 6.3 GB VRAM, MIT-Lizenz. Reasoning fokussierter als plain Qwen3.5. ⚠️ **NUR über Ollama** — selbst gebauter llama.cpp crasht bei Mamba-Kernels. Siehe `deep-model-evaluation` Phase 4. |
| DeepSeek-R1-Distill-8B | 🥈 | Gut, aber R1-Reasoning-Trace kostet Output-Tokens. Besser als 14B (zu groß für 8 GB). |
| Llama 3.1-8B | 🥉 | Solide, aber kleinerer Kontext, schwächeres Reasoning als Qwen. |
| Qwythos-9B v1/v2 | ❌ | Marketing-Hype. Instabil bei Reasoning-Tasks, mixed Community-Evidence. Siehe Session 2026-07-14. |

## Ollama als System-Service
Auf Basti's Setup: **system-service** (User=ollama). Scripte wie `lokalDS-on` müssen
dann `sudo systemctl` statt `systemctl --user` verwenden.

## Ollama Pull Troubleshooting

### Silent Pull Hang (Cloudflare CDN)

`ollama pull hf.co/<org>/<repo>:<quant>` zeigt keine Progress-Bar mehr, aber `ss -tlnp` zeigt 8+ ESTAB connections zu `54.230.x.x:443` (Cloudflare). Die Verbindung lebt, aber kein Datenfortschritt.

**Diagnose:**
```bash
pgrep -a ollama           # Pull-Prozess aktiv?
du -sh .ollama/models/blobs/*.incomplete  # Blob angefangen?
ss -tnp | grep 11434      # ESTAB-Verbindungen
```
Keine neuen Blobs (>5 Min) bei ESTAB → Pull hängt.

**Fix:** `pkill -f "ollama pull"`, dann `hf download <org>/<repo> <file>.gguf --local-dir ~/models/<name>` (5-11 MB/s). Lokales Modelfile erstellen und `ollama create`.

**Pitfall (Rate-Limit Cascade):** Direkter Wechsel von hängendem `ollama pull` zu `hf download` kann ebenfalls drosseln. 30s warten nach kill.

### Q8_0 Layer-Split auf 8 GB VRAM — nicht empfohlen

Q8_0 eines 9B Modells (8.87 GiB) passt **nicht** vollständig in 8 GB VRAM. Ollama splitet automatisch:
- GPU: ~25/33 Layer (6.9 GB)
- CPU: ~8 Layer + Embedding (2.8 GB)

**Performance:** 14 vs 49 tok/s (Q5_K_M Full-GPU) bei identischer Code-Qualität. Verifiziert mit Ornith-1.0-9B auf RTX 5060 8 GB.
**Empfehlung:** Full-GPU Q5_K_M bleibt Sweet Spot für 9B auf 8 GB. Q8_0 erst ab 12+ GB VRAM sinnvoll.

**⚠️ Mamba / Linear-Attention Modelle erleiden EXTREMEN CPU-Offload-Penalty:**
Bei Mamba-Linear-Attention-Architektur (z.B. Ornith-9B: 24/32 Layer sind linear-attention) generiert CPU-Offload **130 graph splits bei batch_size=512** vs 14 bei bs=1 durch GPU↔CPU-Sync. Full-Attention-Transformer degradieren deutlich graziler. Verifiziert auf RTX 5060 8 GB mit Ollama 0.30.11.

### 🚨 Wichtig: Selbst gebauter llama.cpp vs Ollama Binary (Mamba-Kompatibilität)

**Self-built llama.cpp (git clone, cmake) CRASHT bei Mamba-Modellen** in der CUDA-Kernel-Operation `ggml_cuda_op_rms_norm_fused`. Der Upstream-Code hat keine eigenständige Implementierung der Mamba-Linear-Attention-CUDA-Kernels, weshalb er beim ersten Token-Decode crasht.

**Ollama's binary (llama-server aus dem Ollama-Paket) funktioniert** weil es zusätzliche Patches/Commits enthält die diese Kernels korrekt handhaben.

**Erkennung Mamba-Architektur:** Vor dem Download `config.json` des Modells prüfen:
```bash
hf download <org>/<repo> --local-dir /tmp/check 2>/dev/null
grep -o '"model_type": "[^"]*"' /tmp/check/config.json
```
Wenn der Wert `qwen3.5_mtp`, `mamba2`, oder ein anderer Mamba-Hybrid-Type ist → **Muss Ollama sein, kein self-build**.

**Faustregel:**
- ✅ Mamba-Hybrid-Modelle → **Ollama's binary verwenden** (installiert per `curl -fsSL https://ollama.com/install.sh | sh`)
- ✅ Reine Transformer (Llama, Gemma, Phi) → Self-built or Ollama, beides ok
- ❌ **Kein self-built llama.cpp für Ornith, Qwen3.5-MTP, oder andere Mamba-Hybride**

Siehe `deep-model-evaluation` Skill Step 7 für den vollständigen Testing-Workflow (Quant-Comparison, Layer-Split, Dual-GPU Detection).

## Hermes Integration

### Config Format (providers dict, recommended)
```yaml
providers:
  ollama-local:
    base_url: http://127.0.0.1:11434/v1
    request_timeout_seconds: 300

fallback_providers:
  - model: deepseek-r1:8b
    provider: custom:ollama-local
```

set -euo pipefail
### Config Format (custom_providers list, legacy)
```yaml
custom_providers:
  - name: ollama-local
    base_url: http://127.0.0.1:11434/v1
    api_key: ollama
    models:
      - deepseek-r1:8b
```

set -euo pipefail
### Provider Name Pitfalls
- `provider: ollama` → Ollama Cloud (NOT local!)
- `provider: ollama-local` → not recognized
- `provider: custom:ollama-local` → CORRECT

### R1 Reasoning Models: max_tokens
R1 models produce reasoning traces before content. `max_tokens < 1000` → empty content.
**Fix:** `max_tokens >= 2000` for R1 calls. In Hermes profile: `max_tokens: 4096`.

### Reasoning Field Name: Ollama vs OpenAI

When reading reasoning output from Ollama's OpenAI-compatible endpoint:

| Environment | Field Name | Example |
|---|---|---|
| OpenAI API | `choices[0].message.reasoning_content` | Standard |
| Ollama ≥0.30 | `choices[0].message.reasoning` | `msg.get("reasoning")` |
| Ollama raw chat | In `response` metadata | Less structured |

**Pitfall:** If Hermes/OpenCode expects `reasoning_content` but Ollama returns `reasoning`, the reasoning trace is silently dropped. Map explicitly:
```python
reasoning = msg.get("reasoning") or msg.get("reasoning_content", "")
```

Verified on Ollama v0.30.11 with Ornith-9B (Qwen3.5-9B architecture). Applies to any model that emits `reasoning_content` in the OpenAI format — Ollama renames it to `reasoning` in the message body.

### Qwen3.5-9B MTP: Konkretes Setup auf 8 GB VRAM

Siehe `references/qwen35-9b-vram-setup.md` für vollständige Referenz inkl. VRAM-Budget,
Test-Workflow und Troubleshooting.

**Produktions-Modelfile:**
```
FROM hf.co/unsloth/Qwen3.5-9B-MTP-GGUF:Q4_K_M
PARAMETER num_ctx 16384
PARAMETER num_batch 4
PARAMETER num_predict 8192
PARAMETER temperature 0.6
PARAMETER top_p 0.95
PARAMETER top_k 20
PARAMETER repeat_penalty 1.05
```

**⚠️ Qwen3.5-MTP: Keine KV-Cache-Quantisierung!**
`OLLAMA_KV_CACHE_TYPE=q8_0` produziert **garbled output** bei Qwen3.5-MTP.
Default FP16 KV-Cache belassen. (Erkannt 2026-07-14.)

**Qwen3.5-9B MTP vs Plain:** MTP ist ~20-25% schneller bei identischer Qualität.
Source-Tag: `hf.co/unsloth/Qwen3.5-9B-MTP-GGUF:Q4_K_M` (~5.9 GB).

### Qwen3.5-Hermes: num_predict Default 128
Ollama default `num_predict=128` silently breaks thinking models.
**Fix:** Recreate model with Modelfile:
```
FROM qwen3.5-9b-hermes
PARAMETER num_ctx 24576
PARAMETER num_batch 4
PARAMETER num_predict 16384
```

set -euo pipefail
Note: `PARAMETER num_batch 4` prevents GGML_ASSERT crash at large contexts.

## Context Window Configuration

**CRITICAL:** Ollama ignores `OLLAMA_CONTEXT_LENGTH` env var AND `~/.ollama/config.yaml` `context_window` when it detects limited VRAM. It silently falls back to a VRAM-based default (often 4096 on 8GB GPUs). The **only reliable fix** is a custom Modelfile.

See `references/ollama-context-window.md` for the full corrected guide.

### Quick Fix (custom Modelfile)
```bash
# ~/.ollama/custom-models/my-model.modelfile
FROM <base-model>
PARAMETER num_ctx 65536
PARAMETER num_batch 4    # REQUIRED to avoid GGML_ASSERT crash
```

set -euo pipefail
```bash
ollama create my-model -f ~/.ollama/custom-models/my-model.modelfile
```

set -euo pipefail
### Per-model context limits (do not exceed these without quality loss)
| Model | Native trained context | Recommended max |
|-------|----------------------|-----------------|
| Gemma 4 E4B | 128K | 131072 |
| Qwen3.5 9B | 32K-128K | 65536-131072 |
| DeepSeek R1 8B | 64K | 65536 |
| Nemotron 3 Super 120B | 8K-32K | 32768 |

**Pitfall:** Setting context_window beyond the model's trained context → hallucinations, forgotten instructions, degraded quality. Stay at or below the trained limit.

**Pitfall:** `OLLAMA_CONTEXT_LENGTH` env var and `~/.ollama/config.yaml` are IGNORED on low-VRAM GPUs. Use custom Modelfile with `PARAMETER num_ctx`.

**Pitfall:** Forgetting `PARAMETER num_batch 4` → `GGML_ASSERT(n_inputs < GGML_SCHED_MAX_SPLIT_INPUTS)` crash at large contexts.

**Pitfall:** Hermes `patch()` blocks writes to `~/.hermes/config.yaml`. Use `hermes config set` or edit manually.

## Qwen3.5-9B Prompt Engineering Patterns

See `references/qwen35-9b-prompt-patterns.md` for the full reference.

When creating task-specific system prompts for a local 9B model, use these reusable patterns:

- **Model patch header** — proven sampling parameters (temperature 0.6, top_p 0.95, top_k 20, repeat_penalty 1.05), thinking mode requirements, and language stack convention.
- **Anti-pattern table** — explicit ban-table with inline-verify commands (`rg` pattern + expected output per row). More effective than prose for 9B models.
- **Reply skeleton** — structured output format: Situation → Assumptions → Code → Audit → Verification → Watch-out.
- **User template** — fill-in template at bottom so the user knows what context to provide.

Provenance: first used 2026-07-15 for B1 GreyScript + B2 Bash-Audit prompts on Basti's `qwen35-9b-local` model.

## LLM Evaluation

See `references/llm-evaluation.md` for full guide.

### Quick Reference
```bash
# Install
pip install lm-eval

# Run benchmark
lm_eval --model hf --model_args pretrained=meta-llama/Llama-3.1-8B \
  --tasks mmlu,gsm8k --batch_size auto

# With Ollama
lm_eval --model ollama --model_args model=deepseek-r1:8b \
  --tasks mmlu
```

set -euo pipefail
### OpenAI-compatible custom helper pattern

For custom bots or helper modules that need a provider-neutral LLM call, prefer an OpenAI-compatible `/v1/chat/completions` abstraction instead of wiring directly to one provider SDK.

Typical env shape:

```yaml
LLM_API_BASE_URL: https://api.nousresearch.com/v1   # cloud default
LLM_API_KEY: optional                                # required for cloud, omitted for local Ollama
LOCAL_LLM_MODEL: deepseek-r1:8b
```

set -euo pipefail
For local Ollama:

```yaml
LLM_API_BASE_URL: http://127.0.0.1:11434/v1
LLM_API_KEY: ""
LOCAL_LLM_MODEL: deepseek-r1:8b
```

Important implementation rules:

- Detect local Ollama by endpoint (`http://127.0.0.1:11434/v1` or `http://localhost:11434/v1`).
- Do not require an API key when the endpoint is local Ollama.
- Do not send an `Authorization: Bearer ...` header to local Ollama unless explicitly configured.
- Switch the default model based on backend:
  - cloud/Nous: use the cloud model name, e.g. `qwen/qwen3.6-35b-a3b`
  - local Ollama: use `LOCAL_LLM_MODEL`, e.g. `deepseek-r1:8b`
- Use Ollama `/api/tags` for a lightweight health check.

Pitfall: if the base URL changes to local Ollama but the model name remains a cloud model, Ollama returns `model not found` instead of falling back automatically.

See `references/openai-compatible-endpoint-patterns.md` for a compact integration checklist.

## References

- `references/ollama-local-hosting.md` — Full Ollama guide (install, config, pitfalls, removal)
- `references/ollama-context-window.md` — Corrected context window guide (Modelfile fix, GGML pitfalls, Hermes integration)
- `references/openai-compatible-endpoint-patterns.md` — Provider-neutral helper pattern for cloud LLMs and local Ollama.
- `references/llm-evaluation.md` — LLM evaluation benchmarks (lm-eval-harness, troubleshooting)
- `references/qwen35-9b-prompt-patterns.md` — Prompt engineering patterns for Qwen3.5-9B: model patch header, anti-pattern table technique, reply skeleton, user template. Reusable for creating task-specific system prompts against a local 9B model.
