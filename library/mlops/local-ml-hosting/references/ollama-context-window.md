# Ollama Context Window — Corrected Guide

## The Core Problem

Ollama **ignores** `OLLAMA_CONTEXT_LENGTH` env var AND `~/.ollama/config.yaml` `context_window` when it detects limited VRAM. It silently falls back to a VRAM-based default (often 4096 on 8GB GPUs).

**Log evidence:**
```
msg="vram-based default context" total_vram="7.5 GiB" default_num_ctx=4096
```

This means: setting env vars or config.yaml alone WILL NOT WORK on memory-constrained GPUs.

## The Fix: Custom Modelfile

The only reliable way to set context on a GPU with limited VRAM is a per-model Modelfile:

```bash
# 1. Create Modelfile
cat > ~/.ollama/custom-models/my-model.modelfile << 'EOF'
FROM <base-model>
PARAMETER num_ctx 65536
PARAMETER num_batch 4
EOF

# 2. Create custom model
ollama create my-model -f ~/.ollama/custom-models/my-model.modelfile

# 3. Verify
ollama show my-model | grep context
# → context length: 131072

# 4. Test
echo "Say hello" | ollama run my-model
```

### Why `num_batch 4` is required

Without it, large contexts crash with:
```
Error: 500 Internal Server Error: llama-server process has terminated:
  GGML_ASSERT(n_inputs < GGML_SCHED_MAX_SPLIT_INPUTS) failed
```

The GGML scheduler cannot handle the default batch size at large context lengths. `num_batch 4` (or lower) prevents this assertion failure.

## VRAM Budget with CPU Offload

When context exceeds VRAM capacity, Ollama offloads layers to CPU RAM. This works but is slower.

| GPU VRAM | Max practical context | Notes |
|----------|----------------------|-------|
| 8 GB | 32768-65536 | CPU offload required above ~16K |
| 12 GB | 65536 | Partial offload |
| 16 GB | 131072 | May need offload for 7B+ models |
| 24 GB | 131072 | Full GPU for most 7B-14B models |

**CPU offload needs free RAM:** 65K context on a 7B BF16 model needs ~8-12 GB RAM for offloaded layers + KV cache.

## Hermes Integration

### Step 1: Set context_window in Hermes config
```yaml
# ~/.hermes/config.yaml → providers.ollama-launch
providers:
  ollama-launch:
    context_window: 131072   # Must match Modelfile num_ctx
```

### Step 2: Set default_model to custom model
```yaml
    default_model: my-model:latest
    models:
      - my-model:latest
```

### Step 3: Hermes config is PROTECTED from patch()
The `patch()` tool REFUSES to write `~/.hermes/config.yaml`. You must use:
```bash
hermes config set providers.ollama-launch.default_model my-model:latest
```
Or edit the file manually with an editor.

## systemd Service Config

The Ollama service can still set an env var, but it will be IGNORED on low-VRAM GPUs. Keep it for completeness:

```ini
# ~/.config/systemd/user/ollama.service
Environment="OLLAMA_CONTEXT_LENGTH=65536"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_NUM_PARALLEL=1"
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `vram-based default context` in logs | Ollama ignoring env/config | Use custom Modelfile with `PARAMETER num_ctx` |
| `GGML_ASSERT(n_inputs < GGML_SCHED_MAX_SPLIT_INPUTS)` | Batch size too large for context | Add `PARAMETER num_batch 4` to Modelfile |
| `context_length: 4096` despite config | Same as above | Modelfile is the only reliable lever |
| Slow inference at 65K+ context | CPU offload | Expected on 8GB GPU. Reduce context or accept speed |
| Port 11434 already in use after restart | systemd auto-restarted old process | `fuser -k 11434/tcp` then restart |
