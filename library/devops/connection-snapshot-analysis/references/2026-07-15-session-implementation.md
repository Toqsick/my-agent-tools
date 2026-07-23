# Session 2026-07-15 — Reference Implementation

Source log: `grok-monitor-ss-20260714T214248Z.log` (17,6 MB, 3091 Snapshots, ~105 min)
Working dir: `/tmp/wire-analysis/`

## Flow

```
parse_log.py  →  (timestamp, connections[]) generator
    ↓
analyze.py  →  analysis.json (windows, bursts, idle, heatmap)
    ↓
render.py  →  wire-capture-sequence-analysis.md (Markdown report)
```

## Architecture of `analyze.py`

### Snapshot → 5-min windows

```python
start_ts = min(ts for ts, _ in snaps)
n_windows = int((end_ts - start_ts).total_seconds() / 300) + 1
windows = [Window(i, start_ts + timedelta(seconds=i*300)) for i in range(n_windows)]
```

### "New" connection logic

```python
prev_conns = {}  # proc -> set of (proto, local, remote, pid, fd)
for snapshot in snapshots:
    for proc, conn_set in group_by_proc(snapshot.connections):
        new_conns[proc] = len(conn_set - prev_conns.get(proc, set()))
        prev_conns[proc] = conn_set
```

### Burst detection (per-process, not global)

```python
# Global: hides sparse processes
# Correct: per-process median, 2× threshold
for proc in top_procs:
    med = median(series[proc])
    thresh = med * 2 if med > 0 else 0  # med=0 => any >0 is burst
    is_burst = [v > thresh for v in series[proc]]
    # find contiguous runs
```

### Idle run detection

```python
https_out_snapshots = [
    (ts, set(c['proc'] for c in conns
             if c['rport'] == 443 and c['proto'] == 'tcp'))
    for ts, conns in snaps
]
# For each proc: find runs where proc not in https_out_set
# Sum consecutive snapshots until total idle >= 300s
```

## Key values from analysis

| Metric | Value |
|--------|-------|
| Snapshots | 3091 |
| Max gap | 3.0 s |
| Median gap | 2.0 s |
| Zero-conn snapshots | 0 |
| 5-min windows | 21 |
| Distinct procs | 18 |
| Hermes spike (window 17+18) | 53+50 = 103 in 10 min (2.4× median 22) |
| Brave spike (window 20) | 60 in 5 min (4.3× median 14) |
| Simplexity peak (window 5) | 14 in 5 min (14× median 1), onset 00:02:46 |
| claude-desktop range | 16–25/5 min, 0 bursts, 0 idle runs |
| gnome-software idle | 103.9 min idle of 105 min capture |

## JSON schema (analysis.json)

```json
{
  "meta": {
    "snapshots": 3091,
    "time_start": "ISO8601",
    "time_end": "ISO8601",
    "duration_seconds": 6284.0,
    "top_procs": ["brave", "hermes", ...],
    "baseline_new_per_5min": 61,
    "burst_threshold": 122
  },
  "windows": [
    {
      "idx": 0,
      "start": "ISO8601",
      "end": "ISO8601",
      "total_new_top": 92,
      "new_per_proc": {"brave": 30, "hermes": 40, ...}
    }
  ],
  "bursts_top5": ["ranked list of burst objects"],
  "idle_phases_top_procs": {
    "gnome-software": [
      {"start": "...", "end": "...", "duration_seconds": 2321, "snapshots": 1140}
    ]
  },
  "heatmap_hour_x_proc": {
    "0": {"brave": 20877, "hermes": 13986, ...}
  },
  "first_seen": {"brave": "...", "simplexity": "..."},
  "last_seen": {"brave": "...", "simplexity": "..."}
}
```

## Files

Working code preserved at `/tmp/wire-analysis/`:
- `parse_log.py` — Parser for `ss -tlnp` log with `---` separators
- `analyze.py` — Full analysis pipeline (windows, bursts, idle, heatmap)
- `render.py` — Markdown report generator
- `analysis.json` — Intermediate result

Report delivered to:
- `/home/bratan/.hermes/wire-captures/analysis/wire-capture-sequence-analysis.md`