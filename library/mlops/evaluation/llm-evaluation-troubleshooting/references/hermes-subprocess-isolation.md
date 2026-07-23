# Hermes Subprocess Environment Isolation — lm-eval Reproduction

## Symptom

```
ImportError: No module named 'numpy._core._multiarray_umath'
```

When running `lm-eval` (or any tool) from Hermes Desktop agent context.

## Reproduction

```bash
# 1. Verify lm-eval is installed and works in clean terminal
python3.12 -m lm_eval --help
# → OK

# 2. Check what happens in Hermes-subprocess-context
# PYTHONPATH is set by the Hermes Desktop wrapper
echo "PYTHONPATH=$PYTHONPATH"
# → PYTHONPATH=/home/bratan/.hermes/hermes-agent:/home/bratan/.hermes/hermes-agent/venv/lib/python3.11/site-packages

# 3. Notice the conflict: python3.12 binary but PYTHONPATH points to python3.11 site-packages
python3 -c "import sys; print(sys.version)"
# → 3.11.15 (Hermes venv python)

# 4. Verify by unsetting PYTHONPATH
unset PYTHONPATH PYTHONHOME
lm-eval run --model hf --model_args pretrained=gpt2,dtype=float --tasks gsm8k --limit 3
# → Works!

python3.12 -c "import sys; print(sys.version)"
# → 3.12.x (tool's python)
```

## Root Cause

`/tmp/hermes-snap-*.sh` (Hermes Desktop per-command wrapper) injects:

```
PYTHONPATH=/home/bratan/.hermes/hermes-agent:/home/bratan/.hermes/hermes-agent/venv/lib/python3.11/site-packages
```

This is NOT in `~/.bashrc` — it's injected by the runtime and can't be controlled by shell config.

## Fix

Wrapper `~/.local/bin/lm-eval-clean`:

```bash
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
```

## Verification

```bash
lm-eval-clean run --model hf --model_args pretrained=gpt2,dtype=float --tasks gsm8k --limit 3 --batch_size 1
# → Runs cleanly even with PYTHONPATH still set in parent env
# → Expected: 0/3 exact_match (GPT-2 baseline on GSM8K)
```

## Date

Validated 2026-07-13 on Basti's MEDION ERAZER (Zorin OS 18.1, NVIDIA RTX 5060).
Hermes Desktop, model: deepseek/deepseek-v4-flash.