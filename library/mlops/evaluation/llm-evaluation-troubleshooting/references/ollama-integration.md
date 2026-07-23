# Ollama / Local Model Integration with lm-eval-harness

## Problem Summary

Running lm-eval-harness against local Ollama models via the OpenAI-compatible API (`local-chat-completions`, `local-completions`) has several integration friction points.

---

## Issue 1: Colon in Model Name Breaks HuggingFace Tokenizer

### Error

```
OSError: Repo id must use alphanumeric chars, '-', '_' or '.'. The name cannot start or end with '-' or '.' and the maximum length is 96: 'deepseek-r1:8b'.
```

### Root Cause

Ollama model names use `model:tag` format (e.g., `deepseek-r1:8b`, `llama3.1:8b`, `qwen2.5:7b`). The HF `AutoTokenizer.from_pretrained()` validates the repo ID and rejects colons.

The lm-eval code path:
1. `local-completions` / `local-chat-completions` model init
2. Calls `transformers.AutoTokenizer.from_pretrained(model_name)` 
3. HF validator rejects the colon

### Workarounds

**Option A: Pass a known HF tokenizer (recommended)**
```bash
lm-eval run --model local-chat-completions \
  --model_args model=deepseek-r1:8b,base_url=http://localhost:11434/v1,tokenizer=gpt2 \
  --tasks gsm8k
```

**Option B: Use a tokenizer from a similar model family**
```bash
# For Llama models
--model_args ...,tokenizer=meta-llama/Llama-3.1-8B

# For Qwen models  
--model_args ...,tokenizer=Qwen/Qwen2.5-7B

# For DeepSeek models
--model_args ...,tokenizer=deepseek-ai/deepseek-coder-6.7b-base
```

**Option C: Use `local-completions` (not chat) with tokenizer**
```bash
lm-eval run --model local-completions \
  --model_args model=deepseek-r1:8b,base_url=http://localhost:11434/v1,tokenizer=gpt2 \
  --tasks gsm8k
```

---

## Issue 2: Chat Template Required for `local-chat-completions`

### Error

```
AssertionError: LocalChatCompletion expects messages as list[dict]. If you see this error, ensure --apply_chat_template is set or upstream code formats messages correctly.
```

### Root Cause

The `local-chat-completions` model expects the task prompt to be formatted as a chat conversation (list of `{"role": "...", "content": "..."}` dicts). Without `apply_chat_template=true`, the raw prompt string is passed directly to the API, which expects chat format.

### Fix

Add `apply_chat_template=true` to model_args:
```bash
lm-eval run --model local-chat-completions \
  --model_args model=deepseek-r1:8b,base_url=http://localhost:11434/v1,apply_chat_template=true,tokenizer=gpt2 \
  --tasks gsm8k,hellaswag,mmlu
```

---

## Issue 3: EOS String for Stop Sequences

### Warning

```
WARNING: Cannot determine EOS string to pass to stop sequence. Manually set by passing `eos_string` to model_args.
```

### Fix

Add the model's stop token:
```bash
# For GPT-2 tokenizer (used as fallback)
--model_args ...,eos_string="<|endoftext|>"

# For Llama tokenizer
--model_args ...,eos_string="<|eot_id|>"

# For Qwen tokenizer  
--model_args ...,eos_string="<|endoftext|>"
```

---

## Complete Working Command Templates

### Chat model (instruct/chat tuned)
```bash
lm-eval run --model local-chat-completions \
  --model_args model=deepseek-r1:8b,base_url=http://localhost:11434/v1,apply_chat_template=true,tokenizer=gpt2,eos_string="<|endoftext|>" \
  --tasks gsm8k,hellaswag,mmlu \
  --num_fewshot 5 \
  --batch_size 1
```

### Completion model (base/non-chat)
```bash
lm-eval run --model local-completions \
  --model_args model=deepseek-r1:8b,base_url=http://localhost:11434/v1,tokenizer=gpt2,eos_string="<|endoftext|>" \
  --tasks gsm8k,hellaswag \
  --num_fewshot 0 \
  --batch_size 1
```

---

## Model-Specific Notes

| Ollama Model | Recommended Tokenizer | Chat Template | EOS String |
|--------------|----------------------|---------------|------------|
| `deepseek-r1:8b` | `gpt2` or `deepseek-ai/deepseek-coder-6.7b-base` | Required | `<|endoftext|>` |
| `llama3.1:8b` | `meta-llama/Llama-3.1-8B` | Required | `<|eot_id|>` |
| `qwen2.5:7b` | `Qwen/Qwen2.5-7B` | Required | `<|endoftext|>` |
| `gemma2:9b` | `google/gemma-2-9b` | Required | `<eos>` |
| `phi3:14b` | `microsoft/Phi-3-medium-4k-instruct` | Required | `<|end|>` |

---

## Alternative: Use HF Model Directly (if GPU available)

For better performance and fewer integration issues, run the model via HF `hf` or `vllm` backend:
```bash
# HF backend (CPU/GPU)
lm-eval run --model hf \
  --model_args pretrained=deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B,dtype=bfloat16 \
  --tasks gsm8k,hellaswag,mmlu \
  --batch_size auto

# vLLM backend (GPU, 5-10x faster)
lm-eval run --model vllm \
  --model_args pretrained=deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B,tensor_parallel_size=1 \
  --tasks gsm8k,hellaswag,mmlu \
  --batch_size auto
```

---

## Debugging Tips

1. **Test tokenizer loading first**:
```python
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("gpt2")  # Should work
tok = AutoTokenizer.from_pretrained("deepseek-r1:8b")  # Will fail
```

2. **Check Ollama API is responding**:
```bash
curl http://localhost:11434/v1/models
curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-r1:8b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 10}'
```

3. **Enable verbose logging**:
```bash
lm-eval run --model local-chat-completions \
  --model_args model=deepseek-r1:8b,base_url=http://localhost:11434/v1,apply_chat_template=true,tokenizer=gpt2 \
  --tasks gsm8k \
  --limit 2 \
  --verbosity DEBUG
```