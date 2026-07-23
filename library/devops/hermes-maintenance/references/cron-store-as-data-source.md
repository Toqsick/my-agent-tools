---
title: Hermes Cron-Store als Datenquelle für externe Konsumenten
date: 2026-07-10
verified: ja (yuno-dashboard /api/cron-status, 13 Jobs erfolgreich gelesen)
---

# Kontext

Der Cron-Job-State von Hermes wird von **mehreren unabhängigen Konsumenten** gelesen:

- `hermes cron list` (CLI, nur human-readable Text)
- `cronjob(action='list')` Model-Tool (gibt JSON zurück, aber nur innerhalb einer Hermes-Session nutzbar)
- `cron/jobs.py:list_jobs()` (Python-API, gleiche Einschränkung — braucht `HERMES_HOME`)
- **Externe Daemons / Dashboards**, die NICHT Teil von Hermes sind (z.B. `yuno-dashboard` auf Port 8767, parallel zum Hermes-Dashboard auf :9119)

Für den letzten Fall — ein externer Python-/Node-/Go-Prozess, der Cron-Status
für ein separates Web-UI aggregieren will — gibt es **keinen öffentlichen
HTTP-Endpoint**. Man MUSS den Store direkt lesen.

# Wo Hermes den Cron-State speichert

**Kanonischer Pfad:** `~/.hermes/cron/jobs.json`

```json
{
  "jobs": [ {...}, {...} ],
  "updated_at": "2026-07-10T..."
}
```

Verifiziert per:

- `cron/jobs.py:70-71` — `CRON_DIR = HERMES_HOME / "cron"`, `JOBS_FILE = CRON_DIR / "jobs.json"`
- `agent/curator_backup.py:80` — `return get_hermes_home() / "cron" / "jobs.json"` (vom Curator selbst so referenziert)
- Live-Existenz-Check: `ls -la ~/.hermes/cron/jobs.json` (typisch 10-30 KB, 5-50 Jobs)

# Was NICHT der State-Store ist (false friends)

| Pfad / Datei                                | Was es IST                          | Warum nicht der State |
|---------------------------------------------|-------------------------------------|------------------------|
| `~/.hermes/cron/db` (oder `.db`)            | existiert in der Doku, **nicht auf Platte** | Hermes nutzt JSON, kein SQLite für Cron |
| `~/.hermes/cron/output/<job_id>/<ts>.md`   | Run-Artefakte (LLM-Output, Script-stdout) | Output, nicht State — kein next_run_at, kein schedule |
| `~/.hermes/cron/ticker_heartbeat`           | 18-Byte-File, vom Ticker jede Loop berührt | nur "ist der Ticker alive", keine Job-Liste |
| `~/.hermes/cron/ticker_last_success`        | wie heartbeat, aber nur bei erfolgreichem Tick | dito |
| `~/.hermes/cron/.jobs.lock`                 | fcntl-Advisory-Lock (leer) | nicht der State |
| `~/.hermes/cron/README.md`                  | Doku für `hermes cron` CLI-Befehle | nicht der State |
| `~/.hermes/cron-output/<job>.md`           | wie `cron/output/` (siehe oben)     | Output, nicht State |

**Was NICHT funktioniert für externe Konsumenten:**

1. `hermes cron list --json` — gibt's nicht. `--all` ist der einzige Flag, Output ist immer text-formatiert mit `Colors.YELLOW` etc. (`hermes_cli/cron.py:99-183`).
2. `hermes cron list | jq` — würde gehen, ist aber fragil (Output-Format ändert sich, Locale-abhängige Unicode-Box-Drawing-Chars).
3. `cronjob(action='list')` Tool-Aufruf — nur in einer Hermes-Agent-Session verfügbar, nicht von außerhalb.

# jobs.json — Shape pro Job (alle Felder, Stand 2026-07-10)

Top-Level:
- `id`: 12-hex (z.B. `"fb4d5e448c51"`), UUID4-Short
- `name`: string, menschenlesbar
- `enabled`: bool
- `state`: `"scheduled"` | `"paused"` | `"completed"`
- `schedule_display`: string (z.B. `"0 8 * * *"`)
- `schedule`: dict mit `kind`/`expr`/`display`
- `repeat`: `{"times": N|null, "completed": N}` — null times = ∞
- `next_run_at`: ISO-8601 mit TZ
- `last_run_at`: ISO-8601 mit TZ oder null
- `last_status`: `"ok"` | `"error"` | string | null
- `last_error`: string | null
- `last_delivery_error`: string | null
- `paused_at`, `paused_reason`: ISO-8601 + string | null
- `deliver`: string (`"local"` | `"telegram:<chat_id>"` | `"origin"`)
- `skills`: list[str], `skill`: erstes Element (Legacy-Compat)
- `script`: string | null (für `no_agent=true`-Jobs)
- `no_agent`: bool (script-only, kein LLM)
- `workdir`: Pfad | null
- `model`, `provider`, `base_url`: string | null (LLM-Pinning, siehe Section 11)
- `context_from`: list[str] | null (Pipeline-Chaining)
- `enabled_toolsets`: list[str] | null (Per-Job Tool-Allowlist)

# Robuster Reader für externe Daemons

Minimal-Pattern (Python, ~60 Zeilen, ohne Hermes-Dependencies):

```python
from pathlib import Path
import json

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))

def _schedule_display(job):
    display = str(job.get("schedule_display") or "").strip()
    if display:
        return display
    schedule = job.get("schedule")
    if isinstance(schedule, dict):
        for key in ("display", "value", "expr", "run_at"):
            v = str(schedule.get(key) or "").strip()
            if v:
                return v
    return str(schedule or "?")

def get_cron_status():
    jobs_file = HERMES_HOME / "cron" / "jobs.json"
    payload = {"jobs": [], "summary": {...}, "source": str(jobs_file)}
    if not jobs_file.exists():
        payload["missing"] = True
        return payload
    with jobs_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    raw_jobs = data.get("jobs", []) if isinstance(data, dict) else data
    # ... loop, normalize, summary counts
    return payload
```

**Was du NICHT brauchst:**
- `fcntl`-Lock — externer Reader ist read-only, kein Lock-Race
- `cron/scheduler.py` Imports — die brauchen Hermes-Env und scheitern in einem non-Hermes-Python
- `_normalize_job_record()` — die Felder sind in jobs.json bereits normalisiert

**Was du TROTZDEM tun solltest:**
- `try/except` um `json.load` — Datei kann mid-write halb-konsistent sein (sehr selten, aber möglich)
- `Cache-Control: no-store` im HTTP-Response (siehe yuno-dashboard Pattern) — sonst zeigen Browser 5-Minuten-Stale-Daten
- Read-only Lock? **Nein**, denn: (a) du machst kein write, (b) Hermes' eigener `_jobs_lock()` ist `LOCK_NB` mit 30s timeout, du könntest den Scheduler blocken

# Caveats für externe Konsumenten

1. **`HERMES_HOME` korrekt setzen.** Per-profile Cron-Stores leben unter
   `~/.hermes/profiles/<profile>/cron/jobs.json` (per-profile Isolation #4707).
   Der externe Daemon sieht nur den Pfad, den `HERMES_HOME` zeigt.

2. **Kein Real-Time.** `jobs.json` wird synchron bei `cronjob(action='update')`
   geschrieben, aber asynchron via `_jobs_lock()` + `fcntl`. Im worst case siehst
   du 1-50 ms alte Daten — für Dashboard-Zwecke egal.

3. **PII im Output-Feld.** `last_error` und `last_delivery_error` können
   volle Prompt-Texte oder Telegram-Usernames enthalten. Im Dashboard
   ggf. truncaten oder redacten (`security.redact_secrets: true` greift hier
   nicht, weil du nicht durch Hermes' Output-Pipeline gehst).

4. **Kein `cronjob`-Tool-Surface verfügbar.** Externe Konsumenten können nur
   **lesen**. Mutations (`pause`, `resume`, `update`, `run`) müssen via
   `hermes cron …` CLI gehen oder eine Hermes-Session involvieren.

5. **Backwards-Kompat der Schedule-Form.** Ältere Jobs hatten `schedule`
   als dict `{kind, expr, value}`, neuere als dict `{display}`. Beide Shapes
   werden vom Reader-Pattern oben toleriert.

# Verifikation (2026-07-10, yuno-dashboard /api/cron-status)

Live-Aufruf nach Implementation:

```python
import importlib.util, json
spec = importlib.util.spec_from_file_location('yd', 'server.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
p = mod.get_cron_status()
print(p['summary'])
# {'total': 13, 'active': 13, 'ok': 11, 'error': 1, 'unknown': 1, 'paused_counts': 0}
```

13 Jobs (alle aktiv, 11 ok, 1 error, 1 noch nie gelaufen) — passt zu
`hermes cron list --all`.

# Siehe auch

- **§11 Cron Provider-Drift (#44585)** in `hermes-maintenance/SKILL.md` — das `model`/`provider`-Pinning-Problem, das nur LLM-Crons betrifft (kein Issue für reine Script-Crons)
- `hermes_cli/cron.py:cron_status()` (Zeile 192-291) — die **interne** Status-Logik mit Ticker-Heartbeat-Staleness (STALE_AFTER = 200s). Externer Konsument könnte das **nicht** ohne großen Aufwand replizieren, weil es `find_gateway_pids()` + `get_ticker_heartbeat_age()` braucht. Für die meisten Dashboards reicht die jobs.json-Sicht.
- `cron/jobs.py:_normalize_job_record()` (Zeile 370-402) — die Source-of-Truth-Normalisierung, die auch der externe Reader imitiert (state-default aus `enabled`).