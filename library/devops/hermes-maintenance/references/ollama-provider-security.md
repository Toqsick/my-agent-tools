# Ollama-Fallback Integration & Config-Sicherheit

> **AKTUALISIERT 2026-06-06:** Ollama wurde restlos entfernt (Sicherheitsgründe).
> Es gibt KEINEN lokalen Fallback mehr. Dieser Abschnitt dokumentiert den historischen
> Stand für Systeme, die Ollama noch nutzen. Siehe Abschnitt
> **"Nach Ollama-Entfernung: Tote Script-Pfade prüfen"** weiter unten für die
> aktuelle Situation.

## Problem: `sed` auf YAML matcht ALLE provider:-Zeilen (18 statt 1!)

### Symptom
Ein `sed -i 's/^  provider:.*/  provider: nous/' config.yaml` ändert **alle**
`provider:`-Einträge, nicht nur `model.provider`. Zerstört auxiliary-Vision,
-compression, -web_extract und andere Sections.

### Ursache
YAML hat identische Key-Namen auf verschiedenen Ebenen. `sed` ist
zeilenbasiert und unterscheidet nicht zwischen `model.provider`,
`auxiliary.vision.provider`, `fallback_providers[].provider` etc.

### Lösung: Immer Python-YAML für Config-Editing verwenden

```python
import yaml
with open('config.yaml') as f:
    cfg = yaml.safe_load(f)

# Gezielt NUR model.provider ändern
cfg['model']['provider'] = 'nous'

with open('config.yaml', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
```

**Im Script (bash):**
```bash
python3 -c "
import yaml
with open('\$CONFIG') as f:
    cfg = yaml.safe_load(f)
cfg['model']['provider'] = 'nous'
cfg['model']['default'] = 'moonshotai/kimi-k2.6'
cfg['model']['model'] = 'moonshotai/kimi-k2.6'
with open('\$CONFIG', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
"
```

Siehe `scripts/hermes-network-switch.sh` für das vollständige Live-Beispiel.

## Nach Ollama-Entfernung: Tote Script-Pfade prüfen

Wenn Ollama entfernt wurde, müssen alle Scripts und Configs auf
tote Referenzen geprüft werden:

- `~/bin/hermes-network-switch.sh` — Offline-Fallback auf Ollama (aktualisiert)
- `~/.hermes/skills/devops/hermes-maintenance/scripts/hermes-network-switch.sh` — Template (aktualisiert)
- `fallback_providers` in config.yaml — Eintrag mit `custom:ollama-local`
- `custom_providers` in config.yaml — Eintrag mit `name: ollama-local`

Tote Pfade entfernen oder durch Warnung ersetzen. Siehe aktuelles Template.

## Problem: Falsche api_key Referenzen führen zu 401

### Symptom
```
⚠ Auxiliary title generation failed: HTTP 401: Missing Authentication header
```

### Ursache
Falsche `api_key: ollama` Einträge in `model:` Block oder `custom_providers`.
Wenn Hermes' Auxiliary-Dienste (Titel-Generierung, Triage, Kanban-Decomposer) versuchen,
gegen einen nicht laufenden Ollama-Server zu authentifizieren, kommt 401.

### Lösung: Provider-Trennung

**Online-Modus (Standard):**
```yaml
model:
  provider: nous
  api_key: ''                    # Aus .env via Hermes Credential Store
  base_url: https://inference-api.nousresearch.com/v1
  default: qwen3.7-plus
  model: qwen3.7-plus            # Muss identisch mit default sein!
```

**Offline-Modus (Fallback, nur wenn Ollama installiert):**
```yaml
custom_providers:
  - name: ollama-local
    api_key: ollama              # Ollama braucht keinen echten Key
    base_url: http://127.0.0.1:11434/v1
    models:
      - deepseek-r1:14b
      - deepseek-r1:8b
      - qwen3.5:9b
```

**WICHTIG:** `ollama-local` gehört in `custom_providers:`, niemals als `model.provider` im Hauptblock!

## Automatisches Netzwerk-Switching

Ein Cron-Job prüft alle 5 Minuten den Internet-Status und schaltet um.
Siehe Skill `hermes-maintenance` → Abschnitt "Offline/Online Provider Switching".

## Config-Audit Checkliste

Vor/nach jeder Provider-Änderung diese Prüfungen durchführen:

```bash
# 1. Keine "ollama" im Model-Block (außer leer)
grep -n "api_key" ~/.hermes/config.yaml | head -5
# Erwartet: model.api_key = ''

# 2. Keine ollama Referenzen im Haupt provider-Feld
grep "^  provider:" ~/.hermes/config.yaml | head -1
# Erwartet: provider: nous  (oder gewünschter Online-Provider)

# 3. Custom provider korrekt strukturiert
grep -A10 "^custom_providers:" ~/.hermes/config.yaml

# 4. Keine ollama in fallback_providers
grep "fallback_providers:" ~/.hermes/config.yaml -A5

# 5. Auxiliary services nutzen gültigen Provider
grep "title_generation:" ~/.hermes/config.yaml -A3
# Erwartet: provider: openrouter oder provider: nous

# 6. Model und default identisch
grep -E "^  (default|model):" ~/.hermes/config.yaml
# Erwartet: Beide gleicher Wert
```

## Häufige Fehler

| Fehler | Auswirkung | Fix |
|--------|-----------|-----|
| `model.api_key: ollama` | 401 bei Titel-Generierung | `hermes config set model.api_key ''` |
| `fallback_providers` enthält ollama-local | Crash wenn Ollama nicht läuft | Entfernen |
| `model: deepseek/deepseek-v4-flash` bei `provider: nous` | Modell nicht gefunden | Pfad korrigieren: `deepseek-v4-flash` |
| `model` ≠ `default` | Inkonsistente Modellwahl | Gleichsetzen |
| ollama-binary gelöscht, aber custom_providers besteht | Offline-Crash | Entscheiden: reinstallieren oder custom_providers entfernen |
