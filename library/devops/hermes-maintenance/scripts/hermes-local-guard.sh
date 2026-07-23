#!/usr/bin/env bash
# Template: hermes-local-guard.sh
# Config-Drift Watchdog (Tier 3) — prüft alle 5min ob Hermes auf lokalem qwen3.5-9b läuft
# Bei Drift: Auto-Repair (yaml.safe_dump) + Alert via Cron deliver
#
# Cron: hermes cron create "*/5 * * * *" --name hermes-local-guard --script hermes-local-guard.sh --no-agent --deliver local
#
# Pitfall 26: Cron alleine reicht NICHT wenn ein anderes Script aktiv Config überschreibt.
# DIESER Watchdog ist Tier 3 — er fängt Drift ab, auch wenn Tier 1 (Cron pausieren) +
# Tier 2 (Script umschreiben) versagen.
set -euo pipefail

CONFIG="$HOME/.hermes/config.yaml"
DESIRED_PROVIDER="ollama"
DESIRED_MODEL="pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2:hermes"
ALERTS=""

# === 1. Config-Provider/Model prüfen ===
CURRENT_PROVIDER=$(python3 -c "
import yaml
with open('$CONFIG') as f: cfg = yaml.safe_load(f)
print(cfg.get('model', {}).get('provider', ''))
" 2>/dev/null || echo "ERROR")
CURRENT_MODEL=$(python3 -c "
import yaml
with open('$CONFIG') as f: cfg = yaml.safe_load(f)
print(cfg.get('model', {}).get('default', ''))
" 2>/dev/null || echo "ERROR")

if [ "$CURRENT_PROVIDER" != "$DESIRED_PROVIDER" ] || [ "$CURRENT_MODEL" != "$DESIRED_MODEL" ]; then
    ALERTS+="🟡 Config-Drift: provider=$CURRENT_PROVIDER, default=$CURRENT_MODEL
"
    # Auto-Repair
    python3 << PYEOF
import yaml
with open('$CONFIG') as f: cfg = yaml.safe_load(f)
if 'model' not in cfg: cfg['model'] = {}
cfg['model']['provider'] = '$DESIRED_PROVIDER'
cfg['model']['default'] = '$DESIRED_MODEL'
cfg['model']['model'] = '$DESIRED_MODEL'
with open('$CONFIG', 'w') as f:
    yaml.safe_dump(cfg, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
PYEOF
    ALERTS+="   ✓ Auto-Repair: qwen3.5-9b@ollama wiederhergestellt
"
fi

# === 2. Auxiliary-Provider auf cloud prüfen (Datenschutz-Indikator) ===
NOUS_AUX=$(python3 -c "
import yaml
with open('$CONFIG') as f: cfg = yaml.safe_load(f)
aux = cfg.get('auxiliary', {})
print(sum(1 for v in aux.values() if v.get('provider') in ('nous', 'openrouter', 'auto')))
" 2>/dev/null || echo "0")
if [ "$NOUS_AUX" -gt 0 ]; then
    ALERTS+="🔴 $NOUS_AUX Auxiliary-Provider noch auf cloud (nous/openrouter/auto) — Datenschutz-Leak!
"
fi

# === 3. Fallback-Chain auf cloud prüfen ===
FALLBACK_CLOUD=$(python3 -c "
import yaml
with open('$CONFIG') as f: cfg = yaml.safe_load(f)
fb = cfg.get('fallback_providers', [])
print(sum(1 for f in fb if f.get('provider') in ('nous', 'openrouter')))
" 2>/dev/null || echo "0")
if [ "$FALLBACK_CLOUD" -gt 0 ]; then
    ALERTS+="🔴 Fallback-Chain hat $FALLBACK_CLOUD cloud-Provider — Datenschutz-Leak!
"
fi

# === 4. Ollama erreichbar? ===
if ! curl -sf --max-time 3 "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
    ALERTS+="🔴 Ollama DOWN — qwen3.5-9b nicht erreichbar!
   Bitte ollama.service starten: systemctl --user start ollama
"
fi

# === Output: silent wenn OK, alert wenn was faul ist ===
if [ -n "$ALERTS" ]; then
    echo "=== hermes-local-guard ALERTS $(date -Iseconds) ==="
    echo -e "$ALERTS"
    exit 1
fi
exit 0
