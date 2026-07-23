# lm-eval-clean Wrapper — Drop-in Template

This is the verified wrapper that solved the Mixed-Python-Env crash between
Hermes Desktop (Python 3.11 venv) and `lm-eval` (Python 3.12 install) on
2026-07-13.

## Symptom It Solves

```
$ lm-eval --help
Traceback (most recent call last):
  ...
  File ".../python3.11/site-packages/numpy/_core/__init__.py", line 24, in <module>
ModuleNotFoundError: No module named 'numpy._core._multiarray_umath'
```

Direct `python3.12 -m lm_eval --help` works fine in a clean shell.
The crash only happens when Hermes Desktop's `PYTHONPATH` leaks in.

## Verified Wrapper (`~/.local/bin/lm-eval-clean`)

```bash
#!/usr/bin/env bash
# ============================================================================
# lm-eval-clean — Hermes-isolierter Wrapper für lm-evaluation-harness
# ============================================================================
# Das echte `lm-eval` CLI ist in python3.12 installiert, aber die Hermes-Venv
# (python3.11) setzt PYTHONPATH und PATH so, dass Subprozesse die python3.12
# numpy-C-Extensions nicht mehr finden (Mixed-Python-Env-Crash).
#
# Workaround: Subprozess mit komplett sauberer Env starten, nur das Notwendigste
# (PATH + HOME) behalten, PYTHONPATH/PYTHONHOME strippen.
#
# Usage:
#   lm-eval-clean <args...>     # alle lm-eval args durchreichen
#
# Author: Yuno (2026-07-13 nach Subprocess-Env-Isolation Diagnose)
# ============================================================================

set -euo pipefail

# Saubere Env: alles behalten außer PYTHONPATH/PYTHONHOME und Hermes-spezifische Venv-Hinweise
declare -a KEEP_VARS=(
    PATH HOME USER SHELL LANG LC_ALL TERM DISPLAY
    HTTP_PROXY HTTPS_PROXY NO_PROXY
    XDG_RUNTIME_DIR XDG_CONFIG_HOME XDG_DATA_HOME XDG_CACHE_HOME
    TZ TMPDIR EDITOR PAGER
)

# Saubere Env bauen
clean_env=()
for var in "${KEEP_VARS[@]}"; do
    if [[ -n "${!var:-}" ]]; then
        clean_env+=("${var}=${!var}")
    fi
done

# Spezielle: HF_TOKEN falls vorhanden (für höhere HF-Hub-Rate-Limits)
if [[ -n "${HF_TOKEN:-}" ]]; then
    clean_env+=("HF_TOKEN=${HF_TOKEN}")
fi

# Echte lm-eval-Python finden
LM_EVAL_PYTHON="$(command -v python3.12 || command -v python3.11 || echo python3)"

# lm-eval via python -m aufrufen (Shebang-Probleme umgehen)
exec env -i "${clean_env[@]}" "$LM_EVAL_PYTHON" -m lm_eval "$@"
```

## Installation in 3 Steps

```bash
# 1. File anlegen + executable
install -m 755 /dev/null ~/.local/bin/lm-eval-clean
# (paste the wrapper content above with write_file or heredoc)

# 2. Smoke-Test
lm-eval-clean --help | head -5
# Should print usage, NOT crash

# 3. Real quick-test
lm-eval-clean run --model hf --model_args pretrained=gpt2,dtype=float \
    --tasks gsm8k --limit 3 --batch_size 1 2>&1 | tail -10
# Expected: exact_match 0.0 ± 0 (GPT-2 baseline)
```

## Pattern to Reuse for Other Tools

To make a similar wrapper for ANY system tool that's stuck in another
Python version:

| Replacement | New Tool |
|---|---|
| `lm-eval` | any other `python3.12 -m XYZ` |
| `python3.12` | whatever Python that tool lives in |
| `lm_eval` | the module name to run via `python -m` |

Save each one as `~/.local/bin/<tool>-clean` and add to `KEEP_VARS` only
what that tool needs (most need nothing extra).

## Validation Date

2026-07-13 01:53 — Wrapper ran end-to-end despite Hermes-PYTHONPATH active,
GPT-2 gsm8k baseline = `exact_match 0.0 ± 0` (5-shot, 11 sec for 3 samples).