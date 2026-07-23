# Session-Referenz: Ollama "Stealth" systemd-Teardown

## Ausgangslage
Nutzer: "Habe ollama aus sicherheitsgründen gelöscht das hat nicht ganz geklappt."

Verifikation zeigte:
- `which ollama` → `~/.local/bin/ollama` existierte noch
- `systemctl --user status ollama` → **active (running) seit 1h 28min**
- `~/.ollama` → existierte noch
- Hermes Config hatte Ollama an 3 Stellen:
  - `fallback_providers` mit `provider: custom:ollama-local`
  - `custom_providers` mit `name: ollama-local`
  - `model.api_key` war bereits `''` (bereinigt aus vorheriger Session)

## Kritisches Learning: systemd user service
Der Nutzer dachte Ollama sei gelöscht, weil er die Modelle oder das Binary entfernt hatte. Aber der **systemd user service** (`~/.config/systemd/user/ollama.service`) war weiter aktiv mit `enabled` — er wärde bei jedem Login neu starten.

## Durchgeführte Schritte

### 1. Systemd Service stoppen & entfernen (ZUERST!)
```bash
systemctl --user stop ollama
systemctl --user disable ollama
rm -f ~/.config/systemd/user/ollama.service
systemctl --user daemon-reload
```

### 2. Binary & Libs
```bash
rm -f ~/.local/bin/ollama
rm -rf ~/.local/lib/ollama
```

### 3. Modelle & Daten
```bash
rm -rf ~/.ollama
rm -rf ~/.local/share/ollama
```

### 4. Hermes Config via Python YAML (Listen/Dicts)
```python
import yaml

with open('/home/bratan/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)

# custom_providers: Listenelement entfernen
cfg['custom_providers'] = [
    cp for cp in cfg.get('custom_providers', [])
    if cp.get('name') != 'ollama-local'
]

# fallback_providers: Listenelement entfernen
cfg['fallback_providers'] = [
    fp for fp in cfg.get('fallback_providers', [])
    if 'ollama' not in str(fp.get('provider', ''))
]

with open('/home/bratan/.hermes/config.yaml', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
```

**Warum nicht `hermes config set`?** `hermes config set key value` kann nur flache Keys setzen. Listen wie `fallback_providers` und `custom_providers` müssen direkt im YAML bearbeitet werden.

### 5. Default auf Nous Portal + Kimi K2.6
```python
cfg['model']['provider'] = 'nous'
cfg['model']['default'] = 'moonshotai/kimi-k2.6'
cfg['model']['model'] = 'moonshotai/kimi-k2.6'
```

## Verifikation
```bash
$ which ollama
# (keine Ausgabe → ✓)

$ grep -n "ollama" ~/.hermes/config.yaml
# (keine Treffer → ✓)

$ systemctl --user status ollama 2>/dev/null | grep Active
# (keine Ausgabe → ✓)

$ ls -d ~/.ollama 2>/dev/null
# (keine Ausgabe → ✓)
```

## Plattgespart
- ~5 GB Modell-Daten (deepseek-r1:8b)
- ~1 GB Binary/Lib
- Sicherheit: Kein lokaler Service mehr, keine offenen Ports
