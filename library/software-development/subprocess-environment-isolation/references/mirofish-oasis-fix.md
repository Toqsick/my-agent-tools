# MiroFish/OASIS — PYTHONPATH Isolation Fix (2026-07-11)

## Symptom

After setting up MiroFish (OASIS social simulation backend) under `20-experimental`,
starting a simulation with `max_rounds=3` immediately failed:

```
进程退出码: 1, 错误: 已加载环境配置: /home/bratan/10-Projekte/20-experimental/MiroFish/.env
错误: 缺少依赖 tokenizers>=0.22.0,<=0.23.0 is required…
```

## Root Cause Chain

1. Hermes starts with `PYTHONPATH` pointing to `hermes-agent/venv/` (Python 3.11, tokenizers 0.23.1)
2. `terminal(npm run dev)` starts backend via `env -u PYTHONPATH` workaround — **Flask server gets clean env**
3. Flask starts, receives `POST /api/simulation/start`, calls `SimulationRunner.start_simulation()`
4. `simulation_runner.py` calls `subprocess.Popen(cmd, env=os.environ.copy())` to spawn OASIS worker
5. **Child inherits Hermes' original `PYTHONPATH`** (not the stripped terminal env — Flask re-inherited it)
6. OASIS worker resolves `tokenizers` from `hermes-agent/venv/` (0.23.1) instead of project `.venv` (0.22.1)
7. `transformers.dependency_versions_check` rejects the version mismatch

## Verification

```bash
# Before fix — child would inherit Hermes' PYTHONPATH
.venv/bin/python -c "import os; print(repr(os.environ.get('PYTHONPATH')))"
# → '/home/bratan/.hermes/hermes-agent:/home/bratan/.hermes/hermes-agent/venv/lib/python3.11/site-packages'

# After fix — clean child
cat /proc/$WORKER_PID/environ | tr '\0' '\n' | grep PYTHONPATH
# → (nothing)
```

## Applied Patch

File: `backend/app/services/simulation_runner.py`, lines ~432–448

```python
env = os.environ.copy()
env['PYTHONUTF8'] = '1'
env['PYTHONIOENCODING'] = 'utf-8'
# --- FIX ---
env.pop('PYTHONPATH', None)
env.pop('PYTHONHOME', None)
backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
venv_bin = os.path.join(backend_root, '.venv', 'bin')
venv_python = os.path.join(venv_bin, 'python')
if os.path.isfile(venv_python):
    cmd[0] = venv_python
    env['VIRTUAL_ENV'] = os.path.join(backend_root, '.venv')
    path_parts = [venv_bin]
    for part in env.get('PATH', '').split(os.pathsep):
        if not part: continue
        if 'hermes-agent' in part and 'venv' in part: continue
        if part == venv_bin: continue
        path_parts.append(part)
    env['PATH'] = os.pathsep.join(path_parts)
# --- END FIX ---
```

## Result After Fix

- Simulation `sim_d8e8c59b76cf` completed successfully
- 16 actions (8 Twitter + 8 Reddit initial posts)
- 3 rounds in ~3 seconds
- No python env errors

---

## Appendix: OASIS Worker Survival Pattern (2026-07-12)

### Behaviour

When the Flask backend is killed (e.g. `pkill -9 -f "backend/run.py"`) while a simulation is running, the OASIS simulation worker **survives independently** because:

1. `simulation_runner.py` spawns it via `subprocess.Popen(cmd, env=env, start_new_session=True)` — this creates a **new process group** (the worker is NOT a child of the Flask process in the traditional sense)
2. The parent Flask process flushes its file descriptors and terminates, but the OASIS worker is a standalone Python process that keeps running
3. Killing the parent only orphans the worker — it still has open file handles to the simulation's `run_state.json` and SQLite databases
4. The worker continues writing actions, advancing rounds, and updating `run_state.json` even with the backend dead

### Verification

```bash
# After killing backend, check if worker still writes
cat backend/uploads/simulations/*/run_state.json | python3 -c "
import json,sys; d=json.load(sys.stdin)
print(f'Runner: {d.get(\"runner_status\")}, Round: {d.get(\"current_round\")}, Actions: {d.get(\"total_actions_count\")}')"

# Wait 30s, check again — if Round increased, worker survived
```

### Recovery

1. Restart the backend: `unset PYTHONPATH PYTHONHOME && backend/.venv/bin/python backend/run.py`
2. The new Flask process finds the existing simulation data on disk
3. The API endpoint reflects the state from the still-running worker
4. The watcher continues polling and triggers report when the worker completes

### Clean Shutdown

To kill everything cleanly:

```bash
# 1. Find the worker
ps aux | grep -E "[r]un_parallel_simulation|[o]asis"
# 2. Kill worker first (graceful)
kill $WORKER_PID
# 3. Kill backend
pkill -f "backend/run.py"
# 4. Verify ports free
ss -tlnp | grep -E "5001|3000"
```