# Ollama Local Hosting — Full Reference

Extracted from the `ollama-local-hosting` skill.

## Installation
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## Model Selection by VRAM
| VRAM | Models | Speed | Quality |
|------|--------|-------|---------|
| 4-6 GB | `deepseek-r1:7b`, `llama3.1:8b` | 🚀 ~80-100 tok/s | ⭐⭐⭐ |
| 8 GB | `deepseek-r1:8b` (~30-50 t/s), `deepseek-r1:14b` (~4-7 t/s) | Mixed | ⭐⭐⭐⭐ |
| 12 GB | `qwen2.5:32b` (partial) | 🐢 ~15-30 t/s | ⭐⭐⭐⭐⭐ |
| 16+ GB | `llama3.1:70b`, `qwen2.5:32b` | 🐢 ~8-20 t/s | ⭐⭐⭐⭐⭐ |

## Hermes Integration

### Config (providers dict — recommended)
```yaml
providers:
  ollama-local:
    base_url: http://127.0.0.1:11434/v1
    request_timeout_seconds: 300

fallback_providers:
  - model: deepseek/deepseek-v4-flash
    provider: nous
  - model: deepseek-r1:8b
    provider: custom:ollama-local
```

### Provider Name Pitfalls
- `provider: ollama` → Ollama Cloud (NOT local!)
- `provider: ollama-local` → not recognized
- `provider: custom:ollama-local` → CORRECT

### R1 max_tokens
R1 models need `max_tokens >= 2000`. In Hermes profile: `max_tokens: 4096`.

### Hermes config.yaml is protected
The `patch()` tool REFUSES to write `~/.hermes/config.yaml`. To change Hermes config:
```bash
hermes config set providers.ollama-launch.default_model my-model:latest
hermes config set providers.ollama-launch.context_window 131072
```
Or edit manually with an editor.

### Qwen3.5 num_predict Fix
Ollama default `num_predict=128` breaks thinking models. Recreate with Modelfile:
```
FROM qwen3.5-9b-hermes
PARAMETER num_ctx 24576
PARAMETER num_batch 4
PARAMETER num_predict 16384
```
Note: `PARAMETER num_batch 4` prevents GGML_ASSERT crash at large contexts.

## Context Window Configuration

**IMPORTANT:** This section is outdated. The corrected guide is in `references/ollama-context-window.md`.

Key correction: Ollama **ignores** both `OLLAMA_CONTEXT_LENGTH` env var AND `~/.ollama/config.yaml` `context_window` on low-VRAM GPUs. The only reliable fix is a custom Modelfile with `PARAMETER num_ctx <value>` and `PARAMETER num_batch 4`.

## Performance Tips
- `OLLAMA_VULKAN=false` → force CUDA on NVIDIA
- `OLLAMA_FLASH_ATTENTION=true` → faster inference
- `OLLAMA_MAX_LOADED_MODELS=1` → critical for 8GB VRAM
- `OLLAMA_KEEP_ALIVE=10m` → avoid reload overhead
- `OLLAMA_NUM_PARALLEL=1` → save VRAM

## Complete Removal
```bash
systemctl --user stop ollama && systemctl --user disable ollama
rm -f ~/.config/systemd/user/ollama.service
rm -f ~/.local/bin/ollama && rm -rf ~/.local/lib/ollama
rm -rf ~/.ollama ~/.local/share/ollama /usr/share/ollama
snap remove ollama 2>/dev/null
systemctl --user daemon-reload
```

## Troubleshooting
- **Slow inference:** Model swapping to RAM — use smaller model
- **"model not found":** Run `ollama pull <model>` first
- **Ollama not accessible:** `ollama serve` or check systemd service
- **Curl hangs (0% CPU):** Single-slot server, previous task owns slot
- **Multiple installations:** Check `snap list ollama` + `which ollama` — only one should exist
- **Context too small / truncated responses:** Check `~/.ollama/config.yaml` context_window and Hermes provider-level context_window setting
