# Foreground-Watcher Pattern

> Reusable technique for creating durable background monitoring processes
> when Hermes' `terminal(background=true)` reaps detached child processes.

## Problem

When Hermes spawns a script via `terminal(background=true, ...)`, any subprocesses
that the script forks/detaches (`&`, `nohup`, `disown`) are **reaped** when the
parent shell exits. This makes traditional daemonisation impossible within a
Hermes-managed shell — the subprocesses get SIGHUP/SIGTERM alongside the parent.

Standard approaches that **do NOT work** reliably in Hermes' shell backend:
```bash
cmd &             # killed when parent exits
nohup cmd &       # same — Hermes backend doesn't forward TTY to children
cmd & disown      # same — shell exits, children reaped
setsid cmd &      # same — process group not preserved
```

## Solution: Foreground-Watcher

Run the monitoring loop **in the foreground of a dedicated process** and let
it self-terminate on a STOP signal:

```
terminal(background=true) ──► cmd_start ──► cmd_watch (foreground loop)
                                                │
                                                ├── loops every N seconds
                                                ├── checks STOP marker file
                                                └── writes output + state
```

### Architecture

| Component | Behaviour |
|-----------|-----------|
| `cmd_start` | Sources `cmd_watch` as a foreground function call. Writes a STOP marker file for stop signalling. **Does NOT fork or detach.** |
| `cmd_watch` | The infinite loop: probe → log → sleep → check STOP. Runs in the foreground of the Hermes background shell. |
| STOP marker | A file (`/tmp/grok-monitor-state/<session>.stop`) that `cmd_watch` checks every iteration. Created by `cmd_stop`. |
| `cmd_stop` | Writes the STOP marker. The watcher exits on its next iteration. May optionally SIGTERM the PID as a hard fallback. |
| State directory | `/tmp/grok-monitor-state/<session>.info` (PID, session tag) + `.log` (live output). |
| `cmd_status` | Reads the latest `.info` file, checks if the PID is alive, shows log tail. |

### Key design decisions

1. **No shell-level backgrounding.** The loop runs in the Hermes-managed process. Hermes keeps it alive as long as the background shell lives.
2. **STOP marker over signaling.** Writing a file is race-condition-free and avoids PID collisions. The loop checks for the file every iteration.
3. **Self-termination.** The loop exits cleanly when it sees the STOP marker — no forced kill needed. Ensures log files are flushed.
4. **PID file for status checks.** A companion `status` command reads the `.info` file to check if the watcher is alive.

### When to use this pattern

- **Live network monitoring** (`ss`/`tcpdump`-based connection tracking)
- **File system watchers** (inotify-like polling)
- **Resource usage trackers** (periodic GPU/memory/disk sampling)
- **Any daemon that runs inside a Hermes-managed shell**

### When NOT to use this pattern

- For truly long-running servers (HTTP, SSE, WebSocket) — use Hermes' `cronjob(action='create')` or a systemd user service instead
- For one-shot tasks — use foreground `terminal()` directly
- For tasks needing complex process management (process trees, parallel children) — use a dedicated scripting language (Python with `subprocess`)

## Implementation template

```bash
#!/usr/bin/env bash
# Template: Foreground-Watcher for Hermes background processes
set -uo pipefail

SESSION_TAG="${1:-$(date -u +%Y%m%dT%H%M%SZ)}"
STATE_DIR="/tmp/monitor-state"
STOP_FILE="$STATE_DIR/$SESSION_TAG.stop"
INFO_FILE="$STATE_DIR/$SESSION_TAG.info"
LOG_FILE="$STATE_DIR/$SESSION_TAG.log"
SAMPLE_INTERVAL=2

mkdir -p "$STATE_DIR"

# === cmd_watch — the foreground loop ===
cmd_watch() {
  echo "pid=$$" > "$INFO_FILE"
  echo "session=$SESSION_TAG" >> "$INFO_FILE"
  echo "log=$LOG_FILE" >> "$INFO_FILE"
  
  while true; do
    # Check for STOP marker
    if [ -f "$STOP_FILE" ]; then
      rm -f "$STOP_FILE"
      echo "[$(date -Is)] STOP signal received — exiting" >> "$LOG_FILE"
      exit 0
    fi
    
    # === YOUR PROBE HERE ===
    echo "--- $(date -Is) ---" >> "$LOG_FILE"
    ss -tlnp 2>/dev/null >> "$LOG_FILE"  # example probe
    
    sleep "$SAMPLE_INTERVAL"
  done
}

# === cmd_start — runs watcher in foreground ===
cmd_start() {
  echo "Starting Foreground-Watcher (session=$SESSION_TAG)..."
  touch "$STOP_FILE"  # pre-create so stop before start works
  rm -f "$STOP_FILE"
  cmd_watch  # runs forever in this shell
}

# === cmd_stop — signals watcher to stop ===
cmd_stop() {
  if [ -f "$INFO_FILE" ]; then
    echo "Stopping watcher (session=$SESSION_TAG)..."
    touch "$STOP_FILE"
    sleep 0.5
    rm -f "$INFO_FILE" "$LOG_FILE" "$STOP_FILE" 2>/dev/null
    echo "Stopped."
  else
    echo "No active watcher for session=$SESSION_TAG"
  fi
}

# === cmd_status — check if watcher is alive ===
cmd_status() {
  if [ ! -f "$INFO_FILE" ]; then
    echo "[inactive] No INFO file for session=$SESSION_TAG"
    return
  fi
  cat "$INFO_FILE"
  local pid; pid=$(awk -F= '/^pid=/ {print $2}' "$INFO_FILE" 2>/dev/null)
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    echo "[active] PID $pid is alive"
  else
    echo "[inactive] PID $pid not found"
  fi
}

# === auto-discovery for status ===
_auto_discover_session() {
  local latest
  latest=$(ls -t "$STATE_DIR"/*.info 2>/dev/null | head -1)
  if [ -n "$latest" ]; then
    SESSION_TAG=$(basename "$latest" .info)
    INFO_FILE="$latest"
    LOG_FILE="$STATE_DIR/$SESSION_TAG.log"
    STOP_FILE="$STATE_DIR/$SESSION_TAG.stop"
  fi
}

# Routing
case "${2:-start}" in
  start)  cmd_start ;;
  stop)   cmd_stop ;;
  status) 
    if [ -z "${SESSION_TAG_FROM_CLI:-}" ] && [ -d "$STATE_DIR" ]; then
      _auto_discover_session
    fi
    cmd_status ;;
  *)      echo "Usage: $0 <session> (start|stop|status)" >&2; exit 1 ;;
esac
```

## Deployment pattern for Hermes

Scripts using this pattern should live in:
- **Source:** `~/50-System/bin/<tool-name>` (canonical copy)
- **Symlink:** `~/bin/<tool-name>` → `~/50-System/bin/<tool-name>` (PATH access)

Test with:
```bash
# Start in Hermes background
terminal(background=true, command='~/bin/<tool> start')

# Wait a few seconds, then check
terminal(command='~/bin/<tool> status')

# Stop
terminal(command='~/bin/<tool> stop')
```

## Pitfalls

| # | Problem | Fix |
|---|---------|-----|
| 1 | `status` shows no session without `--session` tag | Add auto-discovery that reads the most recent `.info` file |
| 2 | `pkill -f` kills Hermes process too | Use exact PID from INFO file, never `pkill -f <pattern>` |
| 3 | STOP marker + sleep means up to 1× interval delay before exit | Acceptable trade-off — set shorter interval for faster stop |
| 4 | Log files accumulate in `/tmp` | Add cleanup in `cmd_stop` or periodic TMP watch |
| 5 | Hermes background shell may exit after task timeout | Use `timeout=0` (infinite) or long enough timeout for the expected session duration |

## Real-world example

The `grok-monitor` tool (in `~/50-System/bin/`) uses this pattern:
- Session: `20260714T214248Z`
- 2-second sampling interval via `ss -tlnp`
- Log grows ~50 KB per 12 seconds during desktop use
- Stop-marker-based lifecycle
- Auto-discovers latest session for status checks

## See also

- `linux-system/templates/self-service-fix.sh` — companion template for fix scripts
- `hermes-agent` — Hermes-specific background process lifecycle details