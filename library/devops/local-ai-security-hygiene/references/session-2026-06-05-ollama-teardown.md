# Session-Referenz: Ollama Komplett-Entfernung + 401-Fix

## Ausgangslage
- Nutzer hatte Ollama aus Sicherheitsgründen "gelöscht", aber es war unvollständig
- `which ollama` zeigte noch: `/home/bratan/.local/bin/ollama` (Symlink)
- `~/.ollama/models` enthielt noch 20 GB Modelldaten
- Hermes Config hatte 3 Referenz-Stellen:
  1. `providers.ollama-launch` Block
  2. `model.api_key: ollama` (verursachte 401!)
  3. `custom_providers` mit `name: ollama-local`

## Durchgeführte Schritte

### 1. Binary-Alias entfernen
```bash
rm /home/bratan/.local/bin/ollama       # Symlink
rm -rf /home/bratan/.local/lib/ollama   # tatsächliche Binaries/Libs
```

### 2. Modelle & Runtime-Daten
```bash
du -sh /home/bratan/.ollama             # → 20G
rm -rf /home/bratan/.ollama             # models/, manifests/, blobs/ alles weg
```

### 3. Hermes Config bereinigt (Python YAML)
```python
import yaml
with open('/home/bratan/.hermes/config.yaml') as f:
    data = yaml.safe_load(f)

# Entfernen
data['providers'].pop('ollama-launch', None)
data['custom_providers'] = [cp for cp in data['custom_providers'] if cp.get('name') != 'ollama-local']
data['fallback_providers'] = [fp for fp in data['fallback_providers'] if fp.get('provider') != 'custom:ollama-local']

# API Key fix (Magic-String!)
data['model']['api_key'] = ''

with open('/home/bratan/.hermes/config.yaml', 'w') as f:
    yaml.dump(data, f, ...)
```

### 4. Auxiliary Service Fix (401-Root-Cause)
- Vorher: `title_generation.provider: auto` → versuchte toten Ollama
- Nachher: `title_generation.provider: openrouter`

```bash
hermes config set auxiliary.title_generation.provider openrouter --profile default
```

## Verifikation danach
```bash
which ollama                         # → leer
grep -c "ollama" ~/.hermes/config.yaml  # → 0
head -5 ~/.hermes/config.yaml        # → api_key: ''
```

## Plattgespart: 20 GB + sicheres Setup
