# Cron Duplicate-Guard Pattern

When a shell script auto-registers workflows (`register-workflows.sh`), running it twice creates 2-3x identical crons — and removing them later is error-prone (wrong ID → wrong job removed). Use this **idempotent guard pattern**:

## Main Guard Pattern

```bash
# In register-workflows.sh: ALWAYS pre-check before creating
set -euo pipefail

EXISTING_JOBS=$(hermes cron list 2>&1)  # capture list
for JOB_NAME in daily-briefing greyhack-ci-watch greyhack-tool-builder greyhack-db-watcher; do
  if echo "$EXISTING_JOBS" | grep -q "$JOB_NAME"; then
    echo "[SKIP] $JOB_NAME already exists"
  else
    echo "[CREATE] $JOB_NAME"
    hermes cron create "30m" --name "$JOB_NAME" --prompt "..."
  fi
done
```

## Safety layer — dry-run mode:

```bash
# Accept --dry-run to show what WOULD be created without actually creating
DRY_RUN=false
if [[ "$*" == *"--dry-run"* ]]; then
  DRY_RUN=true
fi

for JOB_NAME in ...; do
  if echo "$EXISTING_JOBS" | grep -q "$JOB_NAME"; then
    echo "[SKIP] $JOB_NAME (already registered)"
  else
    if $DRY_RUN; then
      echo "[DRY-RUN] Would create: $JOB_NAME — schedule \"$SCHEDULE\""
    else
      hermes cron create "$SCHEDULE" --name "$JOB_NAME" --prompt "..."
    fi
  fi
done
```

## Removal guard — never guess job IDs:

```bash
# NEVER hardcode job IDs. Always list first, then identify by NAME + SCHEDULE:
hermes cron list | grep -E "(duplicate-name|wrong-schedule)" | head -1 | awk '{print $1}'
# Then verify with a second list before removing:
# cronjob(action='remove', job_id='<verified-id>')
```

## Pitfall

The list display may show the wrong provider (display bug), so checking by **name** is safer than by provider. If two jobs have the same name (the exact duplicate scenario), `hermes cron list` shows both — the first match is usually the older one.