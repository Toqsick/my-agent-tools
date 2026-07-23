# Hermes Config Integration (Deep Dive)

Detailed Hermes `config.yaml` patterns for Ollama providers, fallback chains,
Critic-Gate setup, context-length, and runtime verification.

## Config Formats

Es gibt **zwei kompatible Formate**:

### Format A: `providers:` dict (v12+, empfohlen)

```yaml
providers:
  ollama-local:
    base_url: http://127.0.0.1:11434/v1
    request_timeout_seconds: 300
    stale_timeout_seconds: 900

fallback_providers:
  - model: deepseek/deepseek-v4-flash
    provider: nous
  - model: deepseek-r1:8b
    provider: custom:ollama-local
```

`provider: custom:ollama-local` nutzt das Suffix nach `custom:` als Key im
`providers`-Block.

### Format B: `custom_providers:` list (Legacy)

```yaml
custom_providers:
  - name: ollama-local
    base_url: http://127.0.0.1:11434/v1
    api_key: ollama
    models:
      - deepseek-r1:8b
```

Als Default-Provider nutzen:

```bash
hermes config set model.provider custom:ollama-local
hermes config set model.default deepseek-r1:8b
```

**WICHTIG:** NICHT `model.provider: ollama` (Ollama Cloud!) oder bare
`ollama-local` ohne `custom:`-Prefix verwenden.

- `model.provider: ollama` → verweist auf **Ollama Cloud**
- `model.provider: ollama-local` → nicht erkannt, fällt auf `auto`
- `model.provider: custom:ollama-local` → **korrekt**

**Beide Formate sind valide** — Hermes merged beide zur Laufzeit via
`get_compatible_custom_providers()`. Das `providers:` dict-Format wird für
Neukonfigurationen empfohlen (weniger Boilerplate).

## PITFALL: `hermes config set` speichert komplexe Werte als String

`hermes config set custom_providers '[{...}]'` speichert den Wert als
**YAML-String** statt als Liste. Das zerstört die Config-Struktur:

```yaml
# FALSCH (hermes config set produziert das):
custom_providers: '[{"name":"ollama-local",...}]'

# RICHTIG (YAML-Liste):
custom_providers:
  - name: ollama-local
    base_url: http://127.0.0.1:11434/v1
```

**Fix:** Python mit PyYAML nutzen:

```python
python3 -c "
import yaml
with open('/home/bratan/.hermes/config.yaml', 'r') as f:
    config = yaml.safe_load(f)
config['custom_providers'] = [{
    'name': 'ollama-local',
    'base_url': 'http://127.0.0.1:11434/v1',
    'api_key': 'ollama',
    'models': ['deepseek-r1:8b']
}]
with open('/home/bratan/.hermes/config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
"
```

Danach verifizieren: `grep -A 5 "custom_providers" ~/.hermes/config.yaml`

## Automatischer Fallback bei Nous-Ausfall

Wenn Nous/DeepSeek der Default bleibt und Ollama automatisch bei
Verbindungsproblemen einspringen soll:

```yaml
fallback_providers:
  - provider: "custom:ollama-local"
    model: "qwen3.5:9b"
    base_url: "http://127.0.0.1:11434/v1"
  - provider: "anthropic"
    model: "claude-sonnet-4-20250514"

agent:
  api_max_retries: 1   # Schnelles Failover: 1 Retry statt 3, dann sofort Fallback
```

**Wichtig:** `base_url` muss im fallback-Eintrag mit angegeben werden bei
custom-Providern. Format: `provider: "custom:<name>"` (name muss mit
`custom_providers[].name` übereinstimmen).

Failover-Kette: Nous → Ollama lokal → Anthropic Claude als letzter Ausweg.

Per Session manuell wechseln: `hermes chat --provider custom:ollama-local --model qwen3.5:9b`

## Offline-Fallback Strategien

Vollständige Strategien, Wrapper-Scripte und Diagnose-Checks:
**`references/offline-fallback-strategy.md`**

Hermes hat keine automatische Offline-Erkennung. Die Umsetzung erfordert
einen manuellen Workflow, ein Pre-flight Script, oder den Hermes-Fallback-
Mechanismus (langsam, da erst nach Retry auslöst).

**Schnell-Check: Läuft Ollama wirklich?**

```bash
# 1. systemd Service
systemctl --user status ollama --no-pager | head -3

# 2. Port belegt?
ss -tlnp | grep 11434

# 3. Binary vorhanden?
ls -la ~/.local/bin/ollama 2>/dev/null || echo "Keine User-Installation"
```

**Wichtig:** `ollama ps` zeigt nur *geladene Modelle* — ein leerer Output
bedeutet **nicht**, dass Ollama beendet ist. Der systemd-Service kann
weiterlaufen ohne geladenes Modell.

## Critic-Gate Integration

Der lokale `deepseek-r1:8b` wird auch vom **Critic-Gate** genutzt
(Quality-Gate für `multi-agent-work`/`multi-agent-research`):

**Script:** `~/.hermes/scripts/critic-gate-ollama.py`
- Ruft `http://localhost:11434/api/generate` mit `model: deepseek-r1:8b`
- Parameter: `num_ctx: 16384`, `temperature: 0.6`, `timeout: 300s`
- Exit-Codes: 0=PASS, 1=RETRY, 2=FAIL

Der Critic läuft **nicht als Hermes-Subagent**, sondern als direktes
Ollama-Script — kein API-Token-Verbrauch, kein Netzwerk-Latenz, 100% lokal.
Einzige Einschränkung: 1 GPU = 1 Critic gleichzeitig (RTX 5060, 8GB VRAM).

**Bei Änderungen am lokalen Modell** (z.B. Update auf r1:14b): Auch die
`MODEL`-Variable im Script und die `fallback_providers`-Config aktualisieren.

**WICHTIG:** Config-Änderungen wirken erst in einer **neuen Session**.
Nach Änderungen `/new` starten.

**Quick-Check vor `/new`:**

```bash
curl -s http://localhost:11434/api/tags | python3 -c "import json,sys; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]"
```

## Context-Length (KRITISCH für Hermes)

Hermes braucht mindestens 64000 Token Context. Ollama nutzt standardmäßig
nur 4096 bei <24GB VRAM!

**Im systemd User-Service setzen** (empfohlen):

```ini
# ~/.config/systemd/user/ollama.service
[Service]
Environment="OLLAMA_CONTEXT_LENGTH=64000"
```

Dann: `systemctl --user daemon-reload && systemctl --user restart ollama`

Verifizierung: `journalctl --user -u ollama --since="1 minute ago" | grep OLLAMA_CONTEXT_LENGTH`
Sollte anzeigen: `OLLAMA_CONTEXT_LENGTH:64000`

## Custom-Provider verifizieren (Runtime-Check)

`grep` auf die YAML bestätigt nur die statische Config. Für eine echte
Verifikation, dass Hermes den Provider zur Laufzeit auflöst:

```bash
cd ~/.hermes/hermes-agent && source venv/bin/activate && python3 -c "
import sys; sys.path.insert(0, '.')
import logging; logging.disable(logging.WARNING)
from hermes_cli.runtime_provider import resolve_runtime_provider
r = resolve_runtime_provider(requested='custom:ollama-local', target_model='deepseek-r1:8b')
print(f'provider:    {r.get(\"provider\")}')
print(f'base_url:    {r.get(\"base_url\")}')
print(f'api_mode:    {r.get(\"api_mode\")}')
print(f'source:      {r.get(\"source\")}')
print(f'api_key_set: {bool(r.get(\"api_key\"))} (len={len(r.get(\"api_key\") or \"\")})')
"
```

Erwartet für korrekten Setup:

```
provider:    custom
base_url:    http://localhost:11434/v1
api_mode:    chat_completions
source:      custom_provider:ollama-local
api_key_set: True (len=15)   # "no-key-required" - Ollama-Placeholder, kein echter Key
```

**Was die Felder bedeuten:**

- `source='custom_provider:ollama-local'` → wurde aus dem `providers:` Dict aufgelöst
- `api_key='no-key-required'` → Default-Placeholder wenn keine `api_key`/`key_env`
  konfiguriert. Ollama akzeptiert das (kein Auth-Header-Check), andere Endpoints
  würden 401 geben.
- Wenn `source` etwas anderes ist oder `base_url` leer → Konflikt zwischen
  mehreren `providers:`-Einträgen mit ähnlichem Namen.

**End-to-End-Test (löst einen echten Call aus):**

```bash
timeout 90 hermes chat -q "Sage Hallo in einem Wort" \
  --provider custom:ollama-local \
  --model deepseek-r1:8b \
  --quiet
# Erwartet: "session_id: ...\nHallo"
```

## Mehrfach-Installationen (Snap + Native)

Wenn Snap-Ollama UND manuell installierte Ollama gleichzeitig existieren:

**Diagnose:**

```bash
ps aux | grep "ollama serve" | grep -v grep
ss -tlnp | grep 11434
snap list ollama 2>/dev/null
which ollama 2>/dev/null
```

**Lösung:** Entweder Snap deinstallieren + manuelle Version nutzen
(`sudo snap remove ollama`) oder systemd-Dienst deaktivieren + Snap
laufen lassen (`sudo systemctl disable ollama`). Snap-Version kann älter
sein — check mit `snap list ollama` (Revision-Ausgabe zeigt Version).

Vollständige Migration: **`references/snap-to-native-migration.md`**