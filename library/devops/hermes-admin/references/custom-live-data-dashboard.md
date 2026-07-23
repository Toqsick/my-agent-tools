# Custom Live Data Dashboard

When you build a **custom Python HTTP server** to serve live Hermes data (dashboard/health/metrics) as a systemd user service:

## Architecture

```
server.py (Python HTTP server with psutil + subprocess)
  ├── /api/data          — aggregated Hermes state (CPU/MEM/DISK/GPU, skills, cron)
  ├── /api/cron          — cron job list (parsed from `hermes cron list` output)
  ├── /api/cron/<name>   — drill-down detail (schedule, workdir, last-run, deliver)
  ├── /api/history       — ring-buffer of recent snapshots (up to 60 points)
  ├── /api/recall        — Mnemosyne memory search (via Hermes API HTTP endpoint)
  ├── /api/skill/run     — trigger a skill by name
  ├── /api/tokens        — aggregated token usage from log parsing (last 24h)
  ├── /api/logtail       — last lines of agent.log
  └──                  — static HTML/CSS/JS (dashboard frontend)
```

## Key components

- **BackgroundPoller** — thread that snapshots psutil metrics + hermes CLI every 3s, pushes to a RingBuffer
- **RingBuffer** — fixed-size list (default 60) that drops oldest entries; used for sparkline rendering
- **Cache** — dictionary with TTL for expensive Hermes CLI calls (`hermes cron list`, `hermes skills list`)
- **CORS** — `Access-Control-Allow-Origin: *` for headless browser screenshots

## Systemd service unit (verified, working)

```ini
[Unit]
Description=Yuno Operator Dashboard — Live Server (HTTP :8767)
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/bratan/10-Projekte/10-active/yuno-ui/server.py
WorkingDirectory=/home/bratan/10-Projekte/10-active/yuno-ui
Restart=on-failure
RestartSec=5
Environment=HOME=/home/bratan
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
```

## Systemd Timer for Telegram Snapshots (every 5 minutes, verified)

```ini
# Service: yuno-dashboard-snapshot.service
[Unit]
Description=Yuno Dashboard Snapshot — Telegram

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/bratan/10-Projekte/10-active/yuno-ui/snapshot.py
Environment=HOME=/home/bratan

# Timer: yuno-dashboard-snapshot.timer
[Unit]
Description=Dashboard Snapshot every 5min

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
```

## Snapshot script pattern (`snapshot.py`)

```python
#!/usr/bin/env python3
"""Dashboard snapshot → Telegram plain text."""
import subprocess, json, urllib.request

data = json.loads(urllib.request.urlopen("http://127.0.0.1:8767/api/data").read())
msg = f"CPU {data['cpu']}% · MEM {data['mem']}% · Disk {data['disk']}%\nGPU {data['gpu']}% · Cron {data['cron']['active']} active · Skills {data['skills']['enabled']}"

# Plain text only — no Markdown asterisks/backticks!
proc = subprocess.run(["hermes", "send", "-t", "telegram:7222661188", msg],
                      capture_output=True, timeout=15)
```

## Pitfalls discovered during implementation

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| `hermes cron list` uses `┃` (U+2503) box-drawing chars, not `│` | Regex `\|` matches zero | Parse with `┃` or use `hermes cron list --json` if available |
| `hermes send` needs plain text | Exit code 1 with Markdown `*text*` or `` `code` `` | Send plain text only, no formatting |
| Browser caches stale JS after file update | "Loading…" persists despite service restart | Hard refresh (Ctrl+Shift+R) or `?v=N` cache-busting param |
| `SupplementaryGroups=nvidia` crashes systemd | `status=216/GROUP` on start | Omit — `/dev/nvidia*` is world-readable (chmod 666) |
| Headless Chrome virtual-time-budget races with async JS | Screenshots show skeletons | Use `--virtual-time-budget=15000` + fallback polling or increase to 30s |
| Ring-buffer initially empty until poller collects | history_count=0 on first few fetches | Start poller thread before accepting connections, or add warm-up phase |

## Frontend

Single `index.html` with 4 CSS themes (Cozy/Dark/Cyber/HC), tab system (8 tabs with localStorage state persistence), sparkline SVG rendering from history data, cron drill-down modal, memory search via `api/recall`.

## Deployment

```bash
systemctl --user daemon-reload
systemctl --user enable --now yuno-dashboard.service
systemctl --user enable --now yuno-dashboard-snapshot.timer
# Verify
curl -s http://127.0.0.1:8767/api/data | python3 -m json.tool | head -5
systemctl --user status yuno-dashboard.service --no-pager | head -3
systemctl --user list-timers --no-pager | grep snapshot
```