# Qwythos-9B — Official Empero Sampling Defaults

Source: https://huggingface.co/empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF
Extracted: 2026-07-17

## Why This Matters

Using wrong sampling defaults (especially `temperature=0.0` or `repeat_penalty=1.0`)
causes two distinct failure modes on qwen35-family models:

1. **Empty response with think=True:** The model writes the answer inside the
   `thinking` block only — `response=""`. Occurs when `num_predict` is too small
   or `temperature` is too low.
2. **Repetition loops with think=False:** Empero officially warns `T≤0.3` causes
   repetition loops on the qwen35 architecture. The model cycles over the same
   reasoning path without producing a response.

Both failures are configuration bugs, not model quality issues.

## Official Defaults

| Parameter | Value | Notes |
|---|---|---|
| `temperature` | **0.6** | Never ≤0.3 unless think=False + short output |
| `top_p` | 0.95 | Standard nucleus sampling |
| `top_k` | 20 | Truncates to top 20 logits |
| `repeat_penalty` | 1.05 | Mild (1.0 = none, 0.0 disables) |
| `repeat_last_n` | 64 | Tokens to scan for repetition |
| `min_p` | 0.02 | Low-probability tokens threshold (Empero default) |

## Per-Task Recommendations

| Task | think | temperature | num_predict | Expected latency (8GB GPU) |
|---|---|---|---|---|
| Multiple-choice / QA | `false` | **0.3** (mind.!) | 80–200 | 2–7s |
| Code completion | `false` | 0.3 | 500 | 15–18s |
| Light reasoning | `true` | 0.6 | 1500 | ~30s |
| Deep reasoning | `true` | 0.6 | 8000 | ~60s |
| Max reasoning | `true` | 0.6 | 16000 | ~90s (1000 tok avg) |

## Verification

```bash
# Check current tag settings
ollama show qwythos-9b-q6:latest | grep -E "(temperature|top_k|top_p|repeat|num_predict)"

# Apply defaults via Modelfile (if creating a custom tag)
cat <<'EOF' | ollama create qwythos-9b-q6:empero -f -
FROM qwythos-9b-q6:latest
PARAMETER temperature 0.6
PARAMETER top_p 0.95
PARAMETER top_k 20
PARAMETER repeat_penalty 1.05
PARAMETER repeat_last_n 64
EOF
```

## Key Lesson for Benchmarks

1. **Always pull official sampling defaults from the HF card** before writing
   any benchmark code. One extra read step prevents 2–3 wasted re-run iterations.
2. **Empero-style defaults** (T≥0.6, moderate repeat_penalty) are more
   conservative than typical Ollama defaults (T=0.8, repeat=1.1). Trust the
   model author's guidance.
3. **Test think=True AND think=False** with official defaults separately — the
   optimal choice depends on your task type, not on the model's general capability.
