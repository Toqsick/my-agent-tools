#!/usr/bin/env bash
# MiroFish Simulation Watcher
# Polls until runner completes, then triggers report generation.
# Uses run_state.json as fallback when API returns stale None values.
# Usage: bash mirofish-watcher.sh <simulation_id> [project_id] [api_base]

set -uo pipefail

SIM_ID="${1:?Usage: $0 <simulation_id> [project_id] [api_base]}"
PROJECT_ID="${2:-}"
API="${3:-http://localhost:5001}"
SIM_DIR="${4:-$HOME/10-Projekte/20-experimental/MiroFish/backend/uploads/simulations/$SIM_ID}"

echo "=== MiroFish Simulation Watcher ==="
echo "Simulation: $SIM_ID"
echo "Sim dir: $SIM_DIR"
echo "Started: $(date -Iseconds)"
echo ""

# Polling: 5 min interval, max 6h (72 polls)
MAX_POLLS=72
POLL_INTERVAL=300

for i in $(seq 1 "$MAX_POLLS"); do
  # Try API endpoint first
  STATUS=$(curl -s --max-time 15 "$API/api/simulation/$SIM_ID" 2>/dev/null)

  if [[ -z "$STATUS" ]]; then
    echo "[$(date +%H:%M:%S)] poll #$i: no response from backend"
    sleep 30
    continue
  fi

  # Try to parse from API. If fields are None, fall back to run_state.json
  RUNNER=$(echo "$STATUS" | python3 -c "
import json, sys, os
d = json.load(sys.stdin)['data']
runner = d.get('runner_status', '?')
cr = d.get('current_round')
tr = d.get('total_rounds')
ac = d.get('total_actions_count')
pp = d.get('progress_percent')

# If all fields are None, try run_state.json fallback
if cr is None and os.path.exists('$SIM_DIR/run_state.json'):
    try:
        with open('$SIM_DIR/run_state.json') as f:
            r = json.load(f)
        runner = r.get('runner_status', runner)
        cr = r.get('current_round', cr)
        tr = r.get('total_rounds', tr)
        ac = r.get('total_actions_count', ac)
        pp = r.get('progress_percent', pp)
    except: pass

print(f'status={runner} | round={cr}/{tr} | actions={ac} | progress={pp}%')
" 2>/dev/null)

  echo "[$(date +%H:%M:%S)] poll #$i: $RUNNER"

  # Check terminal states
  if echo "$RUNNER" | grep -qE "completed"; then
    echo ""
    echo "✅ Simulation completed!"
    break
  fi

  if echo "$RUNNER" | grep -qE "failed|error"; then
    echo "❌ Simulation failed!"
    # Show full detail from run_state.json if available
    if [[ -f "$SIM_DIR/run_state.json" ]]; then
      python3 -m json.tool "$SIM_DIR/run_state.json" 2>&1 | head -30
    fi
    exit 1
  fi

  sleep "$POLL_INTERVAL"
done

# Final status
echo ""
echo "=== Final Status ==="
if [[ -f "$SIM_DIR/run_state.json" ]]; then
  python3 -c "
import json
with open('$SIM_DIR/run_state.json') as f:
    d = json.load(f)
for k in ['runner_status','current_round','total_rounds',
          'total_actions_count','progress_percent',
          'twitter_actions_count','reddit_actions_count',
          'simulated_hours','started_at']:
    print(f'  {k}: {d.get(k)}')
" 2>/dev/null
else
  curl -s "$API/api/simulation/$SIM_ID" | python3 -c "
import json, sys
d = json.load(sys.stdin)['data']
for k in ['runner_status','current_round','total_rounds',
          'total_actions_count','progress_percent',
          'twitter_actions_count','reddit_actions_count',
          'simulated_hours']:
    print(f'  {k}: {d.get(k)}')
" 2>/dev/null
fi

# If completed, trigger report
RUNNER_FINAL=""
if [[ -f "$SIM_DIR/run_state.json" ]]; then
  RUNNER_FINAL=$(python3 -c "import json; print(json.load(open('$SIM_DIR/run_state.json')).get('runner_status',''))" 2>/dev/null)
fi
if [[ -z "$RUNNER_FINAL" ]]; then
  RUNNER_FINAL=$(curl -s "$API/api/simulation/$SIM_ID" | python3 -c "
import json,sys; print(json.load(sys.stdin)['data'].get('runner_status',''))" 2>/dev/null)
fi

if [[ "$RUNNER_FINAL" = "completed" ]]; then
  echo ""
  echo "=== Triggering Report Generation ==="
  REPORT_RESP=$(curl -s -X POST "$API/api/report/generate" \
    -H "Content-Type: application/json" \
    -d "{\"simulation_id\": \"$SIM_ID\"}")
  echo "$REPORT_RESP" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(json.dumps(d, indent=2)[:600])
" 2>&1
  REPORT_ID=$(echo "$REPORT_RESP" | python3 -c "import json, sys; d=json.load(sys.stdin); print(d.get('data', {}).get('report_id', ''))" 2>/dev/null)
  if [[ -n "$REPORT_ID" ]]; then
    echo "📄 Report URL: http://localhost:3000/report/$REPORT_ID"
  fi
fi

echo ""
echo "Done: $(date -Iseconds)"