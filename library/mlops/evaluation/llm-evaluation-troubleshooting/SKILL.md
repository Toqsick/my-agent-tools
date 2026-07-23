---
name: llm-evaluation-troubleshooting
description: >-
  Use when user asks for debugging lm-evaluation-harness failures, fixing Python or dependency incompatibilities in lm-eval, resolving Ollama or local-model evaluation errors, or diagnosing subprocess environment conflicts. NOT for running a routine benchmark suite or fine-tuning a model. Maps common evaluation errors to tested fixes for dependencies, tokenizer names, chat templates, stop sequences, and host isolation.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms:
- linux
- macos
metadata:
  hermes:
    tags:
    - lm-eval
    - lm-evaluation-harness
    - benchmarking
    - troubleshooting
    - python-compat
    - ollama
    - huggingface
    related_skills:
    - mlops/evaluation/lm-evaluation-harness
trigger_keywords: ['evaluation', 'errors', 'llm-evaluation-troubleshooting', 'debugging', 'lm-evaluation-harness']
keywords: ['evaluation', 'model', 'errors', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['evaluating-llms-harness', 'local-ml-hosting']
---


# LLM Evaluation Troubleshooting

Practical fixes and workarounds encountered when setting up and running **lm-evaluation-harness** (EleutherAI) for model benchmarking. Companion to the main `mlops/evaluation/lm-evaluation-harness` skill.

## Python 3.12+ Compatibility Fix

**Problem**: lm-eval-harness v0.4.12 uses `extra_items` in `TypedDict` which was removed in Python 3.12.

**Error**:
```

set -euo pipefail
TypeError: _TypedDictMeta.__new__() got an unexpected keyword argument 'extra_items'
```

**Location**: `/home/bratan/.local/lib/python3.12/site-packages/lm_eval/result_schema.py` lines 110 and 163.

**Fix**: Patch both `TypedDict` declarations to use `total=False` instead:

```python
# Line 110: _TaskMetrics
class _TaskMetrics(TypedDict, Generic[T], total=False):  # was: extra_items=T

# Line 163: SampleResult
class SampleResult(TypedDict, total=False):  # was: extra_items=float
```

set -euo pipefail
**Applied via**:
```bash
patch /home/bratan/.local/lib/python3.12/site-packages/lm_eval/result_schema.py << 'EOF'
--- a/result_schema.py
+++ b/result_schema.py
@@ -107,7 +107,7 @@
 )
 
 
-class _TaskMetrics(TypedDict, Generic[T], extra_items=T):
+class _TaskMetrics(TypedDict, Generic[T], total=False):
     """Per-task metric dict passed through evaluation and display.
 
@@ -160,7 +160,7 @@
     fewshot_seed: int
 
 
-class SampleResult(TypedDict, extra_items=float):
+class SampleResult(TypedDict, total=False):
     """Per-document result written to ``samples_*.jsonl`` when ``log_samples=True``.
EOF
```

set -euo pipefail
**Note**: Install from GitHub main branch (`pip install git+https://github.com/EleutherAI/lm-evaluation-harness.git`) may already include this fix in newer versions.

---

## Dependency Chain for HF Models

**Required packages** (install in order):
```bash
pip install tenacity --break-system-packages
pip install transformers --break-system-packages
pip install torch --index-url https://download.pytorch.org/whl/cpu --break-system-packages
pip install accelerate --break-system-packages
pip install lm-eval --break-system-packages  # or git+https://github.com/EleutherAI/lm-evaluation-harness.git
```

set -euo pipefail
**Why each is needed**:
- `tenacity` — required by `openai_completions.py` for API retry logic
- `transformers` — tokenizer loading for HF models
- `torch` — model inference (CPU or CUDA)
- `accelerate` — device mapping and model loading utilities

---

## Ollama / Local Model Integration Issues

### 1. Colon in model name breaks HF tokenizer

**Problem**: Ollama model names like `deepseek-r1:8b` contain colons, which HF's `AutoTokenizer.from_pretrained()` rejects as invalid repo IDs.

**Error**:
```
OSError: Repo id must use alphanumeric chars, '-', '_' or '.': 'deepseek-r1:8b'
```

set -euo pipefail
**Workaround**: Pass a known HF tokenizer via `tokenizer` argument:
```bash
lm-eval run --model local-chat-completions \
  --model_args model=deepseek-r1:8b,base_url=http://localhost:11434/v1,tokenizer=gpt2 \
  --tasks gsm8k
```

set -euo pipefail
### 2. Chat template required for chat models

**Problem**: `local-chat-completions` expects messages formatted as `list[dict]` with `role`/`content`. Without chat template, raw prompts are sent as strings, causing assertion errors.

**Error**:
```
AssertionError: LocalChatCompletion expects messages as list[dict]. If you see this error, ensure --apply_chat_template is set
```

set -euo pipefail
**Fix**: Add `apply_chat_template=true` to model_args:
```bash
lm-eval run --model local-chat-completions \
  --model_args model=deepseek-r1:8b,base_url=http://localhost:11434/v1,apply_chat_template=true,tokenizer=gpt2 \
  --tasks gsm8k
```

set -euo pipefail
### 3. EOS string for stop sequences

**Warning**:
```
WARNING: Cannot determine EOS string to pass to stop sequence. Manually set by passing `eos_string` to model_args.
```

set -euo pipefail
**Fix**: Add `eos_string` matching the model's stop token:
```bash
--model_args ...,eos_string="<|endoftext|>"
```

set -euo pipefail
---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: tenacity` | Missing API retry dep | `pip install tenacity` |
| `ModuleNotFoundError: transformers` | Missing tokenizer dep | `pip install transformers` |
| `ModuleNotFoundError: torch` | Missing inference backend | `pip install torch --index-url https://download.pytorch.org/whl/cpu` |
| `ModuleNotFoundError: accelerate` | Missing device map dep | `pip install accelerate` |
| `ValueError: Tasks not found: list` | Old CLI syntax | Use `lm-eval ls tasks` not `lm_eval --tasks list` |
| `NotImplementedError: Loglikelihood not supported` | Chat completions API doesn't support loglikelihood | Use `local-completions` model or HF `hf` model |
| `HFValidationError: Repo id must use alphanumeric` | Colon in Ollama model name | Pass `tokenizer=gpt2` (or any valid HF model ID) |
| `AssertionError: expects messages as list[dict]` | Missing chat template | Add `apply_chat_template=true` to model_args |
| `Left truncation applied` warnings | Context > model max length | Increase `max_length` in model_args or reduce `--num_fewshot` |
| `ImportError: No module named 'numpy._core._multiarray_umath'` | Mixed-Python-Env: Hermes PYTHONPATH (3.11) vs tool (3.12) | Use `env -i` wrapper (see Agent/Subprocess section) |

---

## Performance Notes

- **CPU inference is slow**: GPT-2 (124M) on CPU ~3.6s/sample for GSM8K with 5-shot
- **Truncation warnings** indicate few-shot context exceeds model's max length (GPT-2: 768 tokens). Use `--model_args max_length=2048` or reduce `--num_fewshot`
- **vLLM backend** (`--model vllm`) is 5-10x faster for HF models but requires GPU
- **Batch size**: Use `--batch_size auto` for HF/vLLM; `--batch_size 1` for CPU debugging

---

## Agent/Subprocess Environment Conflicts (Hermes Desktop)

**Problem**: When `lm-eval` (or any tool installed in a different Python version) is run from within an agent context like Hermes Desktop, the inherited `PYTHONPATH` can point to the **wrong Python version's site-packages** and crash.

**Root cause**: Hermes Desktop's subprocess wrapper sets:
```
PYTHONPATH=/home/bratan/.hermes/hermes-agent:/home/bratan/.hermes/hermes-agent/venv/lib/python3.11/site-packages
```
If `lm-eval` was installed via `pip3.12 install lm-eval --user`, its numpy C-extensions were compiled for Python 3.12. But the inherited `PYTHONPATH` loads Python 3.11 numpy first → **Mixed-Python-Env import crash**.

**Symptom**:
```
ImportError: No module named 'numpy._core._multiarray_umath'
```
Yet `python3.12 -m lm_eval --help` works fine in a clean terminal.

**Diagnosis**:
```bash
# Check which Python version the tool actually resolves to
python3 -c "import sys; print(sys.version)"
# If this shows 3.11 but lm-eval is in 3.12, PYTHONPATH is the culprit
```

**Fix**: `env -i` wrapper that strips PYTHONPATH/PYTHONHOME and only keeps essential variables:

```bash
# Create wrapper at ~/.local/bin/lm-eval-clean
cat > ~/.local/bin/lm-eval-clean << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
KEPT_VARS=(PATH HOME USER SHELL LANG LC_ALL TERM DISPLAY
    HTTP_PROXY HTTPS_PROXY NO_PROXY
    XDG_RUNTIME_DIR XDG_CONFIG_HOME XDG_DATA_HOME XDG_CACHE_HOME
    TZ TMPDIR EDITOR PAGER HF_TOKEN)
clean_env=()
for var in "${KEPT_VARS[@]}"; do
    [[ -n "${!var:-}" ]] && clean_env+=("${var}=${!var}")
done
exec env -i "${clean_env[@]}" python3.12 -m lm_eval "$@"
SCRIPT
chmod +x ~/.local/bin/lm-eval-clean

# Use it:
lm-eval-clean run --model hf --model_args pretrained=gpt2 --tasks gsm8k --limit 3
```

**Why `env -i` and not just `unset`**: The PYTHONPATH comes from the **Hermes Desktop subprocess wrapper** (`/tmp/hermes-snap-*.sh`), not from `~/.bashrc`. It's injected by the agent runtime and can't be controlled by user shell config. The wrapper is the only reliable isolation.

**General pattern**: For any system tool installed in a different Python version than the active Hermes agent venv:
1. Create a wrapper with `env -i KEPT_VARS pythonX.Y -m toolname "$@"`
2. Pin the exact Python version that owns the tool
3. Keep only PATH, HOME, locale vars, and auth tokens (like HF_TOKEN)

See `skill_view(name="subprocess-environment-isolation")` for the related *server-spawns-children* pattern.

---

## Quick Test Command

Verify installation works with a minimal HF model:
```bash
lm-eval run --model hf \
  --model_args pretrained=gpt2,dtype=float \
  --tasks gsm8k \
  --limit 10 \
  --batch_size 1
```

Expected output: ~0.1 exact_match on GSM8K (baseline for GPT-2).

---

## References

- [lm-evaluation-harness GitHub](https://github.com/EleutherAI/lm-evaluation-harness)
- Main benchmarking skill: `skill_view(name="mlops/evaluation/lm-evaluation-harness")`