# Local LLM via Ollama — Primary Model (not Fallback)

> Session: 2026-06-08 · User symptom: `ollama launch hermes --model X` loads
> the model into Hermes, but the first prompt returns "token limit überschritten"
> and only the error output is shown.

This is the **opposite** use case from `ollama-provider-security.md`. That
reference covers Ollama as a *fallback* (provider = `custom:ollama-local` in
`fallback_providers`). This reference covers Ollama as the *primary* model —
the model the user actually wants to talk to.

The two use cases have completely different failure modes. Treating a primary-
Ollama problem as a fallback-Ollama problem leads to dead ends.

## Symptom catalogue (verbatim error strings)

Each one points to a different layer of the fix:

| Error string | Layer | Real cause |
|--------------|-------|-----------|
| `Response remained truncated after 3 continuation attempts` | num_ctx + max_tokens | Thinking model burned all `max_tokens` in reasoning; no content produced |
| `Model X has a context window of N tokens, which is below the minimum 64,000 required by Hermes Agent` | MINIMUM_CONTEXT_LENGTH | Hermes hardcoded floor, 9B Q4_K_M physically cannot hit 64k on 8GB |
| `Unknown provider 'ollama-launch'` | provider name | "ollama-launch" is just a launcher CLI, not a real provider name in Hermes |
| `Unknown provider 'custom:ollama-local'` | provider name | Validation rejects this even when `custom_providers.ollama-local` exists |
| `finish_reason: length` with `content_len: 0` and `reasoning_len: 5000+` | max_tokens | Default `max_tokens` (256) cuts thinking models mid-reasoning |
| `context_length: 16384` in `/api/ps` but `architecture: qwen35` advertises 256k | num_ctx | Modelfile has no `PARAMETER num_ctx`; Ollama uses `-c` from launcher |
| `Total message size: ~11,926 tokens` exceeds `num_ctx: 16384` | num_ctx + tool-set | 35 tools × ~340 tokens = 12k just for tool schemas |

## The 4-layer problem (all active simultaneously)

```
                ┌─────────────────────────────────────────────┐
                │  Hermes system prompt = ~12k tokens          │
                │  (35 tool schemas + 4.5k memory + hints)    │
                └─────────────────────┬───────────────────────┘
                                      │
        ┌─────────────────────────────┴─────────────────────────────┐
        │                                                            │
   Layer 1: Ollama num_ctx     Layer 2: System prompt  Layer 3: max_tokens
   default 2048 / launch 16k   12k for 35 tools        default 256 → thinking cut
   modelfile override needed   profile tool-set cut    max_tokens 4096+
        │                                                            │
        └─────────────────────────────┬──────────────────────────────┘
                                      │
                          Layer 4: MINIMUM_CONTEXT_LENGTH = 64_000
                          hardcoded in agent/model_metadata.py:133
                          rejects anything < 64k
```

Fixing any single layer in isolation won't work. You need all four.

## Why 64k is impossible on 8GB VRAM (the VRAM math)

Qwen3 9B Q4_K_M, GQA 4:1 (head_count=16, head_count_kv=4), 32 layers, head_dim=256:

- **Weights:** 9B × 4 bits = 4.5GB. With metadata + overhead: ~5.5GB
- **KV cache (fp16, K+V):** 2 layers × 4 heads × 256 dim × 2 bytes × 32 layers
  × N_tokens = N_tokens × 65536 bytes
  - 8k: 0.5GB
  - 16k: 1.0GB
  - 24k: 1.5GB
  - 32k: 2.1GB
  - 64k: 4.2GB
- **Activation memory + overhead:** ~0.5GB

For 8GB GPU (RTX 4060 mobile-ish):
- 24k context: 5.5 + 1.5 + 0.5 = 7.5GB ← tight but viable
- 32k context: 5.5 + 2.1 + 0.5 = 8.1GB ← OOM/swap risk
- 64k context: 5.5 + 4.2 + 0.5 = 10.2GB ← impossible

The hardcoded 64k minimum is **unreachable** for 9B on 8GB. For 14B on 12GB
it's marginally reachable only with aggressive KV cache quantization. For 70B
on 24GB+ it's fine.

## Why thinking models break at low max_tokens

Qwen3 / DeepSeek-R1 style models emit a `reasoning` field that can run 4-7k
tokens before any `content`. The OpenAI-compat API returns `reasoning` as a
separate field on the assistant message; Ollama and vLLM count these against
`max_tokens` (some implementations don't — but Ollama does).

- `max_tokens: 256` → model produces 256 reasoning tokens, gets cut, no content
- `max_tokens: 1024` → model produces 1024 reasoning, gets cut, no content
- `max_tokens: 4096` → model produces ~3000 reasoning, ~200 content, finish=stop ✓
- `max_tokens: 8192` → model produces ~3000 reasoning, ~500 content, finish=stop ✓

The "3 continuation attempts" failure mode in Hermes is its retry logic for
`finish_reason=length` — it asks the model to "continue", gets another
truncated thinking response, retries 3 times, then gives up with the
"Response remained truncated" error.

## Reproduction recipe (the exact sequence that fails)

```bash
# 1. Modelfile has NO num_ctx (the default state for HF models)
ollama show pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2 | head -20
#   Parameters
#       temperature         1
#       top_k               20
#       top_p               0.95
#       presence_penalty   1.5
#       repeat_penalty     1.1
#   # NO num_ctx line

# 2. ollama launch hermes --model X starts a llama-server with -c 16384
ollama launch hermes --model X
#   /usr/lib/ollama/llama-server --model ... -c 16384 ...
#   Even though ollama show says "context length: 262144"

# 3. /api/ps confirms runtime context
curl -s http://127.0.0.1:11434/api/ps | python3 -m json.tool
#   {
#     "models": [{
#       "name": "X:latest",
#       "context_length": 16384,  ← THIS is what matters, not 262144
#       "size_vram": 5318000000
#     }]
#   }

# 4. Hermes with default config loads 35 tools = 12k token system prompt
#    At num_ctx 16384, only 4k tokens left for input + reasoning + output
hermes chat -q "sag hallo auf deutsch" --model X
#   Initializing agent...
#   ⚠️  Response truncated (finish_reason='length') - model hit max output tokens
#   ⚠️  Response truncated (finish_reason='length') - model hit max output tokens
#   ⚠️  Response truncated (finish_reason='length') - model hit max output tokens
#    ─  ⚕ Hermes  ─
#       Error: Response remained truncated after 3 continuation attempts
```

## The fix (copy-pasteable)

### Step 1: Modelfile + ollama create

```bash
cat > /tmp/qwen3-9b-modelfile <<'EOF'
FROM pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2:latest

PARAMETER num_ctx 24576
PARAMETER temperature 1
PARAMETER top_k 20
PARAMETER top_p 0.95
PARAMETER presence_penalty 1.5
PARAMETER repeat_penalty 1.1
PARAMETER stop <|im_start|>
PARAMETER stop <|im_end|>
EOF

ollama create pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2:hermes \
    -f /tmp/qwen3-9b-modelfile
```

The `:hermes` tag is custom — it doesn't overwrite the upstream `:latest` tag.

### Step 2: Profile

```bash
hermes profile create local-9b
```

`~/.hermes/profiles/local-9b/config.yaml` — see the umbrella SKILL.md
"Local Ollama as Primary Model" section for the full template.

Key values:
- `model.context_length: 24576` (must match modelfile)
- `model.max_tokens: 4096` (must be ≥ thinking model's reasoning budget)
- `model.provider: ollama` (NOT `ollama-launch`, NOT `custom:ollama-local`)
- `model.default: pdurugyan/...:hermes` (use the custom tag, not `:latest`)
- 16 `agent.disabled_toolsets` (keep 8 essentials)
- `compression.threshold: 0.3` (default 0.5 is too late for 24k)

### Step 3: Patch the hardcoded 64k floor

`agent/model_metadata.py:133`:

```python
# Before
MINIMUM_CONTEXT_LENGTH = 64_000
# After (with a clear comment block)
MINIMUM_CONTEXT_LENGTH = 16_000
```

Use the `patch` tool (not sed) for the edit — see the script template
`scripts/hermes-min-context-patch.sh` in this skill for the restore pattern
after `hermes update`.

### Step 4: Test

```bash
# A. num_ctx actually changed?
curl -s http://127.0.0.1:11434/api/ps | python3 -c "
import json, sys
for m in json.load(sys.stdin).get('models', []):
    print(f\"{m['name']}: ctx={m['context_length']}, vram={m['size_vram']/1e9:.1f}GB\")
"
# → ...:hermes: ctx=24576, vram=4.8GB  ✓

# B. Provider resolves?
local-9b chat -q "sag hallo auf deutsch"
# → Hallo! Ich bin Hermes Agent...  ✓

# C. Tool use works?
local-9b chat -q "lies /etc/hostname und sag mir was drin steht"
# → tool_use successful, content returned  ✓

# D. Verbose log shows the right config
local-9b chat -q "test" -v 2>&1 | grep -E "num_ctx|context_length|provider|model="
# → provider=custom base_url=http://127.0.0.1:11434/v1 model=...:hermes
# → Ollama num_ctx: will request 24576 tokens
# → Context compressor: context_length=24576 threshold=16000 (30%)
```

## What goes in which file

This is a multi-file setup. Don't try to put everything in `config.yaml`:

| What | Where | Why |
|------|-------|-----|
| `num_ctx` (runtime) | Modelfile (`PARAMETER num_ctx 24576`) | Tells Ollama how much KV cache to allocate |
| `num_ctx` (display) | `model.context_length` in profile | Tells Hermes what to print + what to cap auto-detected values at |
| `num_ctx` (cap) | `model.ollama_num_ctx` in profile | Cap on auto-detected GGUF value (GGUF metadata lies — see "Context Length Scam" below) |
| `max_tokens` (per-request) | `model.max_tokens` in profile | Output budget; must be ≥ thinking model's reasoning budget |
| `MINIMUM_CONTEXT_LENGTH` | `agent/model_metadata.py` patch | Hardcoded floor — Hermes refuses to init below this |
| `disabled_toolsets` | `agent.disabled_toolsets` in profile | Shrink system prompt; only matters for small num_ctx |
| Compression | `compression.threshold` / `target_ratio` in profile | When to compress — for 24k, compress at 30% not 50% |
| Restore cron | `~/.hermes/scripts/hermes-min-context-patch.sh` | Re-apply the patch after every `hermes update` |

## Context Length Scam: GGUF metadata lies

The "Qwen3.5 9B" model on HuggingFace has a `general.context_length: 262144`
field in its GGUF metadata. This is a **lie** for marketing reasons — 9B
parameters cannot effectively attend across 256k tokens, and no consumer GPU
can hold the KV cache. Ollama dutifully reports this number in `ollama show`'s
"Model > context length" line, which is misleading.

The real number to trust is what `/api/ps` reports after the model is loaded
— that's what Ollama actually allocated based on the Modelfile or `-c` flag.

**Always check `/api/ps.context_length` to verify your `num_ctx` is applied.**

## The "ollama-launch" confusion

`ollama launch hermes --model X` is a **launcher CLI** that:
1. Starts an `ollama serve` if not already running
2. Spawns a `llama-server` with the specified model + `-c 16384`
3. Loads the model into VRAM

It is **not** a Hermes provider. In Hermes config, `provider: ollama-launch`
is invalid and rejected at startup. The correct provider name is just
`ollama` (which is mapped to the `custom` API mode internally — see
`hermes_cli/providers.py:355`).

If you want a custom `base_url` (e.g. llama-server on a non-default port),
use a `custom_providers` entry, not `provider: ollama-launch`.

## When NOT to do this

This fix is for users who **deliberately** want a local model. Don't do it
because:
- The free/cheap API providers are down (use `fallback_providers` instead)
- You want to save money on long sessions (a 9B Q4_K_M at 24k context is
  dramatically slower + dumber than any cloud model — moonshotai/kimi-k2.6
  is way better at the same task)
- You want one-time offline use (run `hermes setup` then disconnect; no
  need to fight the local model setup)

Local models make sense when:
- You need strict data privacy (medical, legal, confidential)
- You're in a network-isolated environment
- You want to learn / experiment with model behavior hands-on
- You're doing development on hermes-agent itself (need reproducible runs)

## See also

- Umbrella SKILL.md → "Local Ollama as Primary Model" section (high-level fix)
- `references/ollama-provider-security.md` (the opposite use case — Ollama as fallback)
- `scripts/hermes-min-context-patch.sh` (idempotent restore after `hermes update`)
- `~/docs/system/hermes-local-9b-setup.md` (long-form user-facing writeup)
