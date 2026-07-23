# Security Hardening Checklist

**Kurzfassung** aller Härtungs-Schritte aus dem Deep-Research vom 06.06.2026.

> Detaillierte Anleitung mit Befunden siehe: `~/docs/system/hermes-deep-research-2026-06-06.md`

## Permissions (sofort umsetzbar)

| Pfad | Soll | War |
|------|------|-----|
| `~/.hermes/state.db` | 600 | 644 |
| `~/.hermes/kanban.db` | 600 | 644 |
| `~/.hermes/.hermes_history` | 600 | 644 |
| `~/.hermes/logs/agent.log` | 600 | 664 |
| `~/.hermes/logs/errors.log` | 600 | 664 |
| `~/.hermes/state-snapshots/` | 700 | 775 |
| `~/.hermes/state-snapshots/*.db` | 600 | 644 |
| `~/.hermes/config.yaml.bak.*` | 600 | 664 |

**Quick-Apply:**
```bash
chmod 600 ~/.hermes/state.db ~/.hermes/kanban.db ~/.hermes/.hermes_history
chmod 600 ~/.hermes/state.db-wal ~/.hermes/state.db-shm
chmod 600 ~/.hermes/logs/agent.log ~/.hermes/logs/errors.log
chmod 700 ~/.hermes/state-snapshots/
find ~/.hermes/state-snapshots/ -type f -exec chmod 600 {} \;
chmod 600 ~/.hermes/config.yaml.bak.* 2>/dev/null
```

## Config-Härtung

```bash
# Fail-Closed (Tool-Ausfall = Ablehnung)
hermes config set tirith_fail_open false

# DM-Policy (nur bekannte User)
hermes config set telegram.dm_policy closed

# Gateway Strict
hermes config set gateway.strict true

# Media-Delivery-Pfade einschränken
hermes config set gateway.media_delivery_allow_dirs '[~/Downloads, ~/Pictures, ~/docs]'

# Session Hygiene
hermes config set session_reset.mode idle
hermes config set session_reset.auto_prune true
hermes config set reasoning.effort medium
hermes config set destructive_slash_confirm true
```

## Dead Fields entfernen

```python
import yaml
c = yaml.safe_load(open('config.yaml'))
dead = ['agent_takes_rejections', 'hard_stop_indicators',
        'hard_stop_max_consecutive_same_tool', 'strict_gateway_routing']
for k in dead:
    if k in c:
        del c[k]
yaml.dump(c, open('config.yaml','w'),
          default_flow_style=False, sort_keys=False, allow_unicode=True)
```

## Nach allen Änderungen

```bash
cp ~/.hermes/.env ~/.hermes/.env.pre-$(date +%s)  # Backup!
systemctl --user restart hermes-gateway.service
journalctl --user -u hermes-gateway.service --no-pager -n 20
```

## Request-Dumps aufräumen

```bash
find ~/.hermes/ -name 'request_dump_*.json' -delete
```

## Verifikation

```bash
# Prüfe state.db Permissions
stat -c '%a %n' ~/.hermes/state.db ~/.hermes/logs/agent.log

# Prüfe Config
hermes config get tirith_fail_open
hermes config get telegram.dm_policy
hermes config get gateway.strict
hermes config get session_reset.mode
hermes config get reasoning.effort

# Prüfe Gateway
systemctl --user is-active hermes-gateway.service
