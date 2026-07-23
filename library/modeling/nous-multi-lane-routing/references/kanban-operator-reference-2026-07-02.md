# Kanban Operator Reference — Multi-Lane Swarms

**Datum:** 2026-07-02
**Status:** Validated

## Scripts

| Script | Pfad | Zweck |
|---|---|---|
| kanban-daemon.sh | `~/.hermes/scripts/kanban-daemon.sh` | Persistent Worker-Dispatcher |
| lane-health.sh | `~/.hermes/scripts/lane-health.sh` | Periodic Health-Check |
| swarm-templates.sh | `~/.hermes/scripts/swarm-templates.sh` | 5 fertige Swarm-Templates |

## Daemon-Kommandos

```bash
bash ~/.hermes/scripts/kanban-daemon.sh start
bash ~/.hermes/scripts/kanban-daemon.sh stop
bash ~/.hermes/scripts/kanban-daemon.sh status
bash ~/.hermes/scripts/kanban-daemon.sh restart
```

## Health-Check

```bash
bash ~/.hermes/scripts/lane-health.sh
# Erwarteter Output: OK alle Lanes healthy
```

## Cron-Watchdog

Job-ID: `c92caed46597`
Schedule: every 10m
Deliver: Telegram → `7222661188`

## Stress-Test-Muster (3 Swarms parallel)

```bash
hermes kanban swarm \
  --worker yuno-coder:"Task":skill-name \
  --verifier yuno-coder \
  --synthesizer yuno-coder \
  "Task..." &

hermes kanban dispatch --max 10
hermes kanban boards
```

## Known Issues

1. **Kanban-Spawn skill-loader bug** — lokale Skills werden in Worker-Spawn nicht gefunden. Workaround: nur builtin Skills nutzen.
2. **StepFun Free rate-limits** — automatischer Fallback auf V4-Flash bei Bursts. Akzeptiert.
3. **Skill-Duplikate** — Bundle-Top-Level + Category-Subdir kollidieren. Coverage 100% erzwingen.

## Persistenz

```bash
systemctl --user enable hermes-kanban   # optional
```
