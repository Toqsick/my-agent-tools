---
name: subprocess-environment-isolation
description: "Use when a Hermes-launched server or CLI child process inherits polluted PYTHONPATH, PYTHONHOME, venv paths, or other environment state and imports the wrong packages. NOT for general virtual-environment setup or unrelated system environment tuning. Applies clean-env and direct-interpreter patterns for server-spawned workers and terminal-invoked tools, then verifies imports and paths."
trigger:
- tokenizers/transformers version mismatch from child process
- ImportError: tokenizers version conflict
- Child process imports from hermes-agent/venv instead of project venv
- Cryptic package conflict after start_simulation or run-worker
- Python tool that starts a server then spawns child workers under Hermes
- lm-eval crashes with ImportError: No module named 'numpy._core._multiarray_umath'
- System tool installed in a different Python version than the Hermes agent venv crashes
  when called via terminal()
author: Hermes Agent
version: 1.0.0
license: MIT
trigger_keywords: ['environment', 'server', 'paths', 'imports', 'hermes']
keywords: ['environment', 'server', 'paths', 'imports', 'hermes']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

# Subprocess Environment Isolation

## Problem

When Hermes starts a Python server via `terminal()`, the agent's own environment
leaks into the server process. If that server spawns **child subprocesses**
(via `subprocess.Popen`), those children inherit the same polluted environment:

| Inherited Var | Effect |
|---|---|
| `PYTHONPATH` | Imports resolve from `hermes-agent/venv/lib/python3.11/site-packages` first |
| `PYTHONHOME` | Overrides venv discovery for the child process |
| `PATH` with `hermes-agent/venv/bin` | May shadow the project venv's python |

**Symptom:**
```
ImportError: tokenizers>=0.22.0,<=0.23.0 is required, but found tokenizers==0.23.1
```
The parent has Hermes' version (0.23.1) while the project venv needs 0.22.1.

## Root Cause (verify)

```bash
# Check what a child process would inherit
.venv/bin/python -c "import os; print(repr(os.environ.get('PYTHONPATH')))"
# If this shows hermes-agent paths, the child will break.

# Check where tokenizers resolves
.venv/bin/python -c "import tokenizers; print(tokenizers.__file__)"
# Should be inside .venv/, not hermes-agent/
```

## Fix Patterns

### Pattern A: Server-spawns-worker (Python subprocess.Popen)

When spawning subprocesses from within a Python service that runs under Hermes,
**isolate the child environment** before calling `subprocess.Popen`:

```python
import os, subprocess

cmd = [sys.executable, worker_script]  # original command

env = os.environ.copy()

# 1. Strip parent contamination
env.pop('PYTHONPATH', None)
env.pop('PYTHONHOME', None)

# 2. Pin to project venv python directly
backend_root = os.path.dirname(os.path.dirname(__file__))  # adjust to your layout
venv_python = os.path.join(backend_root, '.venv', 'bin', 'python')
if os.path.isfile(venv_python):
    cmd[0] = venv_python  # replace sys.executable with venv python
    env['VIRTUAL_ENV'] = os.path.join(backend_root, '.venv')

    # 3. Clean PATH: put project venv/bin first, filter hermes-agent entries
    path_parts = [os.path.join(backend_root, '.venv', 'bin')]
    for part in env.get('PATH', '').split(os.pathsep):
        if not part:
            continue
        if 'hermes-agent' in part and 'venv' in part:
            continue
        if part == os.path.join(backend_root, '.venv', 'bin'):
            continue
        path_parts.append(part)
    env['PATH'] = os.pathsep.join(path_parts)

# 4. Fork the child
process = subprocess.Popen(
    cmd,
    env=env,
    start_new_session=True,
    # ... stdout, stderr, cwd, etc.
)
```

### Pattern B: Direct CLI tool invocation (Hermes terminal()-caller)

**Different scenario**: The agent itself calls a system tool via `terminal()`, and that tool is installed in a **different Python version** than the Hermes agent venv. The inherited PYTHONPATH causes Mixed-Python-Env import crashes.

**Symptom**:
```
ImportError: No module named 'numpy._core._multiarray_umath'
```
Yet `python3.12 -m tool --help` works fine in a clean terminal.

**Fix**: Shell wrapper using `env -i` that strips PYTHONPATH/PYTHONHOME and only keeps essential variables:

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
exec env -i "${clean_env[@]}" python3.12 -m tool_name "$@"
```

**Why `env -i` and not `unset`**: The PYTHONPATH comes from the Hermes Desktop subprocess wrapper (`/tmp/hermes-snap-*.sh`), not from `~/.bashrc`. It's injected by the agent runtime per-command and can't be controlled by shell config. The wrapper is the only reliable isolation.

**Real case**: `lm-eval` (Python 3.12) from Hermes Desktop (Python 3.11 venv). Wrapper `~/.local/bin/lm-eval-clean` created and verified.

**Comparison**: Pattern B handles the case where the **agent itself** calls the tool (one-shot `terminal()` call). Pattern A handles the case where a **Python server running under Hermes** spawns child worker processes. Different patterns, same root cause: Hermes' PYTHONPATH leaks into the wrong Python version's runtime.

## When to Apply
## When to Apply

### Pattern A (server-spawns-worker):
This pattern is needed whenever:
- A Python service runs under Hermes (`terminal()` spawn)
- That service uses `subprocess.Popen` to start worker processes
- The workers have their own `.venv` with potentially different package versions

### Pattern B (direct CLI tool):
This pattern is needed whenever:
- A system tool is installed in a different Python version than the Hermes agent venv (e.g. lm-eval in python3.12 while Hermes runs python3.11)
- The tool is called directly via `terminal()` (not through a subprocess.Popen chain)
- Symptom: `ImportError: No module named 'numpy._core._multiarray_umath'` or similar Mixed-Python-Env crashes

Real cases:
- **OASIS / MiroFish simulation runner** — `simulation_runner.py` spawns `run_parallel_simulation.py`
- **Celery / RQ workers** from Flask apps
- **ML serving workers** (vLLM worker processes, TGI shards)
- **Test runners** (pytest-xdist workers, unittest subprocess runners)
- **Any server that forks** via `subprocess` rather than threading

## Verification

```bash
# After applying fix:
WORKER_PID=$(pgrep -f "worker_script.py")
cat /proc/$WORKER_PID/environ | tr '\0' '\n' | grep PYTHONPATH
# Should be empty or none
cat /proc/$WORKER_PID/environ | tr '\0' '\n' | grep VIRTUAL_ENV
# Should point to project .venv, not hermes-agent
```

## See also

- `references/mirofish-oasis-fix.md` — Full error transcript, symptom timeline, and exact applied patch