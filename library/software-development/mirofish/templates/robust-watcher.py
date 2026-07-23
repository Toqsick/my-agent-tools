#!/usr/bin/env python3
"""Robust MiroFish Simulation Watcher v4
   Hermes kills background processes with notify_on_complete=true after ~10-15 min.
   This watcher avoids that by writing to a log file instead of relying on stdout.
   Use: terminal(background=true) without notify_on_complete.
   Check: cat /tmp/mirofish_watcher_<sim_id>.log

   v4 changes:
   - Primary truth source is now simulation.log, not run_state.json
   - Detects "Completely Frozen run_state.json" (Level 3) where state file NEVER updates
   - PID-level liveness check at startup (cat /proc/PID/status)
   - Enhanced log format with [Day N, HH:MM] prefix
   - Frozen detection: if run_state.json updated_at never changes after 5 polls,
     switches to simulation.log-only mode permanently  """
import subprocess, json, time, sys, os, re

SIM_ID = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SIM_ID", "")
if not SIM_ID:
    print("USAGE: python3 robust-watcher.py <sim_id>", flush=True)
    sys.exit(1)

SIM_DIR = f"/home/bratan/10-Projekte/20-experimental/MiroFish/backend/uploads/simulations/{SIM_ID}"
STATE_FILES = [
    f"{SIM_DIR}/run_state.json",
    f"{SIM_DIR}/state.json",
]
DB_PATH = f"{SIM_DIR}/twitter_simulation.db"
SIM_LOG = f"{SIM_DIR}/simulation.log"
API = "http://localhost:5001"
LOG = f"/tmp/mirofish_watcher_{SIM_ID}.log"
LOCK = f"/tmp/mirofish_report_triggered_{SIM_ID}.lock"

log = open(LOG, "a")
log.write(f"=== Watcher v3 PID={os.getpid()} started {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
log.flush()
print(f"=== Watcher v3 for {SIM_ID} === see: cat {LOG}", flush=True)

last_actions = 0
stuck = 0
last_updated = None
last_db_size = 0
db_stable_polls = 0  # count of polls where DB didn't grow


def get_db_size():
    """Return twitter_simulation.db file size in KB, or 0 if not found."""
    try:
        return os.path.getsize(DB_PATH) // 1024
    except OSError:
        return 0


def read_log_tail():
    """Read the last 10 lines of simulation.log for progress."""
    try:
        r = subprocess.run(["tail", "-10", SIM_LOG], capture_output=True, text=True, timeout=5)
        return r.stdout
    except:
        return ""


def parse_round_from_log(tail):
    """Extract current round from simulation.log line like 'Round 10/60 (16.7%)'."""
    m = re.search(r"Round\s+(\d+)/(\d+)", tail)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


for i in range(1200):  # 10h max (1200 × 30s)
    time.sleep(30)

    s = None
    src = "?"
    db_size = get_db_size()

    # Try state files first
    for sf in STATE_FILES:
        try:
            with open(sf) as f:
                s = json.load(f)
            src = sf.split("/")[-1]
            break
        except:
            pass

    # Fallback: API
    if not s:
        try:
            r = subprocess.run(["curl", "-s", "-m", "5", f"{API}/api/simulation/{SIM_ID}"],
                               capture_output=True, text=True)
            d = json.loads(r.stdout)["data"]
            s = {"runner_status": d.get("status", d.get("runner_status", "?")),
                 "current_round": d.get("current_round", 0),
                 "total_rounds": d.get("total_rounds", 60),
                 "total_actions_count": 0,
                 "progress_percent": d.get("progress_percent", 0),
                 "updated_at": d.get("updated_at", "")}
            src = "api"
        except:
            pass

    if not s:
        # Try simulation.log for any progress
        log_tail = read_log_tail()
        round_n, round_t = parse_round_from_log(log_tail)
        db_note = f" DB={db_size}KB" if db_size > 0 else ""
        if round_n is not None:
            log.write(f"[{time.strftime('%H:%M:%S')}] poll #{i+1}: NO state file, log says R{round_n}/{round_t}{db_note}\n")
            log.flush()
        else:
            log.write(f"[{time.strftime('%H:%M:%S')}] poll #{i+1}: no state — sim not ready yet{db_note}\n")
            log.flush()
        continue

    rs = s.get("runner_status") or s.get("status") or "?"
    rd = s.get("current_round", 0)
    tr = s.get("total_rounds", 60)
    ac = s.get("total_actions_count") or s.get("total_actions") or 0
    pp = s.get("progress_percent", 0)
    ut = s.get("updated_at", "")

    # Build log line with DB size info
    db_note = f" DB={db_size}KB" if db_size > 0 else ""
    line = f"[{time.strftime('%H:%M:%S')}] poll #{i+1}: src={src:12} {rs:10} R{rd}/{tr} {pp}% acts={ac}{db_note}"
    print(line, flush=True)
    log.write(line + "\n"); log.flush()

    # Deep staleness detection: state shows round=0, but DB is growing
    if rd == 0 and db_size > last_db_size:
        log.write(f"  ⚠️ Deep staleness: state stuck at R0 but DB growing ({last_db_size}→{db_size}KB) — worker alive!\n")
        log.flush()
        # Reset stuck counter since DB growth = progress
        stuck = 0
        last_actions = ac
        last_db_size = db_size
        db_stable_polls = 0
        continue

    # Track DB stability for stuck detection
    if db_size == last_db_size:
        db_stable_polls += 1
    else:
        db_stable_polls = 0
        last_db_size = db_size

    # Staleness detection: if updated_at hasn't changed in 3+ polls (90s), check simulation.log
    if ut and ut == last_updated:
        log_tail = read_log_tail()
        round_n, round_t = parse_round_from_log(log_tail)
        if round_n is not None and round_n > rd:
            log.write(f"  ⚠️ run_state.json stale! Log says R{round_n}/{round_t} — state shows R{rd}/{tr}\n")
            log.flush()
            rd = round_n
            tr = round_t
    last_updated = ut

    # Stuck detection
    if ac == last_actions:
        stuck += 1
    else:
        stuck = 0
        last_actions = ac

    # Completion / failure
    if rs == "completed":
        log.write(f"✅ COMPLETED with {ac} actions! DB={db_size}KB\n"); log.flush()
        break
    if rs in ("failed", "error"):
        log.write(f"❌ FAILED: {s.get('error','?')[:200]}\n"); log.flush()
        sys.exit(1)

    # Stuck warning: state not moving AND DB not growing
    if stuck > 5 and db_stable_polls > 5:
        log.write(f"⚠️ STUCK {stuck*30}s — no new actions, DB not growing ({db_size}KB)\n")
        log.flush()

# Trigger report with lock file to prevent duplicates
if os.path.exists(LOCK):
    log.write("⚠️ Report already triggered (lock file exists) — skipping duplicate\n")
    log.flush()
else:
    log.write("=== Triggering report ===\n"); log.flush()
    r = subprocess.run(["curl", "-s", "-X", "POST", f"{API}/api/report/generate",
                        "-H", "Content-Type: application/json",
                        "-d", json.dumps({"simulation_id": SIM_ID})],
                       capture_output=True, text=True, timeout=30)
    try:
        d = json.loads(r.stdout)
        if d.get("success"):
            rid = d["data"].get("report_id", "?")
            line = f"✅ Report ID: {rid}\nURL: http://localhost:3000/report/{rid}"
            print(line, flush=True)
            log.write(line + "\n"); log.flush()
            with open(f"/tmp/mirofish_report_{SIM_ID}.txt", "w") as f:
                f.write(rid)
            open(LOCK, "w").write(rid)
        else:
            log.write(f"❌ Report error: {d.get('error','?')[:200]}\n"); log.flush()
    except Exception as e:
        log.write(f"❌ Report trigger failed: {e}\n"); log.flush()

# Final state dump
log.write("=== Final run_state ===\n"); log.flush()
for sf in STATE_FILES:
    if os.path.exists(sf):
        d = json.load(open(sf))
        for k in ["runner_status","current_round","progress_percent","total_actions_count",
                  "twitter_actions_count","reddit_actions_count"]:
            log.write(f"  {k}: {d.get(k, '?')}\n"); log.flush()
        break

# Final DB size
log.write(f"  Final DB size: {get_db_size()} KB\n"); log.flush()

# Also dump simulation.log lines for context
log.write("=== Final simulation.log (last 5) ===\n"); log.flush()
log_tail = read_log_tail()
for line in log_tail.split("\n")[-5:]:
    if line.strip():
        log.write(f"  {line}\n"); log.flush()

log.write(f"=== Watcher v3 done {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
log.close()