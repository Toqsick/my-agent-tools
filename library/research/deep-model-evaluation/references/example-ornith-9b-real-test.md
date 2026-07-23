# Worked Example: Ornith-1.0-9B Real-World GGUF Test

> Session: 2026-07-16 · Model: deepseek/deepseek-v4-flash
> Hardware: MEDION ERAZER, RTX 5060 Laptop 8 GB VRAM (7.5 GB nutzbar), i7-13620H, 15 GB RAM
> Full conversation stored in session DB.

## Task

Evaluate Ornith-1.0-9B-GGUF from deepreinforce-ai. Verify source → download Q5_K_M (6.02 GiB) and Q8_0 (8.87 GiB) → real coding + tool-use tests → side-by-side vs Unsloth-Qwen3.5-9B.

## Multi-Source Verification (parallel batch)

| Source | Command | Result |
|---|---|---|
| HF API | `curl -s "https://huggingface.co/api/models/deepreinforce-ai/Ornith-1.0-9B-GGUF" \| jq '{id,sha,private,gated,license}'` | `id: deepreinforce-ai/Ornith-1.0-9B-GGUF, sha: 3296bc7a..., gated: false, license: mit` ✅ |
| HF Tree | `curl -s "https://huggingface.co/api/models/deepreinforce-ai/Ornith-1.0-9B-GGUF" \| python3 -c "...tree..."` | Q4_K_M 5.24 GiB, Q5_K_M 6.02 GiB, Q8_0 8.87 GiB ✅ |
| config.json | `hf download deepreinforce-ai/Ornith-1.0-9B-GGUF --local-dir /tmp/v/ && cat /tmp/v/config.json` | **Qwen3_5ForConditionalGeneration**, 32 layers, 4096 hidden, 262k ctx, 8 full + 24 linear attention ✅ |
| Ollama Registry | `curl -s "https://registry.ollama.ai/v2/library/ornith-1.0-9b"` | 404 → NOT registered, needs Modelfile |
| SHA256 verify | `sha256sum ornith-1.0-9b-Q5_K_M.gguf` vs HF Tree `lfs.oid` | `d1b36095636c...` matched ✅ |

**Key discovery:** Ornith-9B is Qwen3.5-9B post-trained with Mamba-2 linear attention (75% of layers). 32 layers total: 8 full_attention + 24 linear_attention (1-in-4 pattern).

## Ollama Setup (non-registered model)

```bash
# Modelfile approach (not ollama pull — registry doesn't have it)
cat > /tmp/ornith-q5.modelfile <<'EOF'
FROM hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q5_K_M
PARAMETER temperature 0.6
PARAMETER top_p 0.95
PARAMETER top_k 20
PARAMETER num_ctx 12288
PARAMETER repeat_penalty 1.05
EOF
ollama create ornith-9b-q5 -f /tmp/ornith-q5.modelfile
```

**Note:** `ollama pull hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q8_0` silently stalled for >8 min with active Cloudflare connections. Must kill and use manual `hf download` + local Modelfile as fallback.

## Real Performance Data (Ollama logs, verified)

| Metric | Q5_K_M |
|---|---|
| VRAM geladen | 6,295 MB (6.15 GiB) |
| VRAM frei | 1,414 MB (1.4 GB headroom) |
| Prompt eval | 234.52 tok/s |
| Generation | **49.99 tok/s** (konsistent) |
| Graphs reused | 215 (Flash-Attention aktiv) |
| Cold start warm-up | ~1 Runde (60s für ersten Prompt inkl. Laden) |

## Coding Task Results (6 diverse tasks)

| Task | Correct? | Latenz | Tok/s | Notes |
|---|---|---|---|---|
| `is_prime(n)` type hints | ✅ | 15.7s | ~45 | Korrekt, knapp |
| FizzBuzz 1-15 | ✅ | 8.6s | 48 | Korrekte Modulo-Logik (initialer "Fail" war max_tokens=400 Truncation!) |
| `clamp(x,lo,hi)` | ✅ | 7.0s | ~50 | Einzeiler, korrekt |
| Quicksort + Partition | ✅ | 12.2s | 49 | Korrekt, 2354 chars Reasoning |
| SQL Recursive CTE + Depth | ✅ | 34.4s | 17 | Strukturiert (Table Schema + Query) |
| Email Regex RFC 5322 lite | ✅ | 26.6s | 23 | Inkl. Test Cases |
| Bug Detection | ✅ | <10s | ~50 | `ZeroDivisionError` erkannt + Fix |
| German Decorators (3 Sätze) | ✅ | — | — | Grammatisch perfekt |

## Tool-Use Tests

### Single Tool Call (2.33s)
```json
{"finish_reason": "tool_calls", "tool_calls": [{"function": {"name": "calculator", "arguments": "{\"expr\":\"2+2\"}"}}]}
```
Reasoning erklärt Strategie, Tool-Call wohlgeformt.

### Multi-Turn Agent Loop
1. Model calls `read_file(/home/bratan/.bashrc)`
2. Mock file content injected as tool result
3. Model synthesizes structured Markdown table + identifies `prime-run`/`intel` as PRIME-Render-Offload

### ⚠️ Reasoning Field Naming
Card says `reasoning_content` (OpenAI standard). Ollama v0.30 returns **`reasoning`** in message object. Important for Hermes/OpenCode integration.

## Side-by-Side: Ornith-9B Q5_K_M vs Unsloth-Qwen3.5-9B Q4_K_M

| Task | Ornith Q5_K_M | Unsloth Q4_K_M | Winner |
|---|---|---|---|
| Quicksort | 12.2s, 49 tok/s | 39.3s, 15 tok/s | 🏆 Ornith 3× |
| SQL CTE | 34.4s, 17 tok/s | 32.1s, 19 tok/s | 🟰 |
| Email Regex | 26.6s, 23 tok/s | 30.3s, 18 tok/s | 🏆 Ornith |
| Avg Generation | ~30 tok/s | ~17 tok/s | 🏆 Ornith |

**Schlüssel:** Ornith ist deutlich schneller auf RTX 5060 bei vergleichbarer Code-Qualität. Reasoning fokussierter (kürzere Chains). Mamba-Linear-Attention scheint VRAM-effizienter zu sein.

## Verdict
**Adoptiere Ornith-9B-Q5 als lokalen Coding-Co-Pilot.** ✅

### Q8_0 Layer-Split Test (Nachtrag)

Q8_0 (8.87 GiB) **passt** in 8 GB VRAM — mit Layer-Split 25/33 auf GPU (6.9 GB):
```
GPU: 6291 MiB (25/33 layers inkl. output layer)
CPU: 2784 MiB (8 repeating + Embedding)
KV-Cache: 192 MiB total (144 GPU + 48 CPU)
Mamba State: 50 MiB
Graph Splits: 130 (bs=512), 14 (bs=1)
```

**Performance:** 14.3 tok/s (vs Q5_K_M 49 tok/s = 3.4× langsamer)
**Quality:** Identisch zu Q5_K_M in allen Coding-Tests
**Fazit:** Auf 8 GB VRAM lohnt sich Q8_0 nicht — die höhere Bit-Tiefe wird durch CPU-Offload aufgefressen. Q5_K_M ist der Sweet Spot. Q6_K wäre als Mittelweg testbar, aber der Speed-Verlust durch CPU-Split setzt bereits bei ~7 GB GGUF ein (Q6_K = 6.85 GiB → 24/32 auf GPU → ca. 18 tok/s erwartet).
