#!/usr/bin/env bash
# Template: ~/bin/hermes-network-switch.sh
# Prüft Internet-Verfügbarkeit und schaltet Hermes Provider um
# AKTUALISIERT 2026-06-06: Ollama entfernt (Sicherheit), Python YAML-Editing
# ACHTUNG: Ollama wurde restlos entfernt — es gibt KEINEN lokalen Fallback.
# Usage: crontab @reboot oder manuell aufrufen

CONFIG="$HOME/.hermes/config.yaml"
BACKUP_DIR="$HOME/.hermes/config-backups"
DESIRED_PROVIDER="nous"
DESIRED_MODEL="moonshotai/kimi-k2.6"

# Ping-Check (schnell + zuverlässig)
if ping -c 1 -W 2 1.1.1.1 >/dev/null 2>&1 || \
   curl -s --max-time 3 "https://inference-api.nousresearch.com/v1/models" >/dev/null 2>&1; then
    STATUS="online"
else
    STATUS="offline"
fi

mkdir -p "$BACKUP_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Netzwerk-Status: $STATUS"

if [ "$STATUS" = "online" ]; then
    # Python-YAML für sicheres Editing (sed matcht ALLE provider:-Zeilen!)
    CURRENT_PROVIDER=$(python3 -c "
import yaml
with open('$CONFIG') as f:
    cfg = yaml.safe_load(f)
print(cfg.get('model', {}).get('provider', ''))
")
    CURRENT_MODEL=$(python3 -c "
import yaml
with open('$CONFIG') as f:
    cfg = yaml.safe_load(f)
print(cfg.get('model', {}).get('default', ''))
")

    if [ "$CURRENT_PROVIDER" != "$DESIRED_PROVIDER" ] || [ "$CURRENT_MODEL" != "$DESIRED_MODEL" ]; then
        cp "$CONFIG" "$BACKUP_DIR/config-$(date +%s).yaml"
        echo "→ Backup erstellt: $BACKUP_DIR/config-$(date +%s).yaml"
        python3 -c "
import yaml
with open('$CONFIG') as f:
    cfg = yaml.safe_load(f)
if 'model' not in cfg:
    cfg['model'] = {}
cfg['model']['provider'] = '$DESIRED_PROVIDER'
cfg['model']['default'] = '$DESIRED_MODEL'
cfg['model']['model'] = '$DESIRED_MODEL'
with open('$CONFIG', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
"
        echo "→ Umgeschaltet auf NOUS PORTAL ($DESIRED_MODEL)"
    else
        echo "→ Bereits auf Nous Portal ($DESIRED_MODEL) — kein Update nötig"
    fi
else
    echo "⚠ OFFLINE — Kein lokaler Fallback verfügbar (Ollama wurde entfernt)"
    echo "  Bitte Internetverbindung herstellen, um Hermes zu nutzen."
fi
