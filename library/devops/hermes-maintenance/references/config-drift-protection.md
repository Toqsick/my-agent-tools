# Config-Drift Protection (3-Tier Pattern)

**Datum:** 2026-06-08
**Status:** Verified pattern — verwendet für 100% lokale Hermes-Migration
**Source:** `~/docs/system/hermes-offline-migration.md`

## TL;DR

Wenn dein `model.default` + `model.provider` regelmäßig auf einen alten Wert zurückspringt, ist es **nicht** ein Bug in `python yaml.safe_dump` oder in `hermes config set`. Es ist ein **Cron-gesteuertes Script** das aktiv die Config überschreibt. Der Fix ist **3-stufig**: Cron pausieren + Script umschreiben + Watchdog-Cron einrichten.

## Symptom-Diagnose

**Du hast gerade:**
```bash
hermes config set model.default "pdurugyan/qwen3.5-9b-...:hermes"
hermes config set model.provider ollama
# hermes status zeigt korrekt: qwen3.5-9b
```

**5-15 Minuten später:**
```bash
hermes status | grep "Model\|Provider"
# Model: moonshotai/kimi-k2.6
# Provider: Nous Portal
```

**Deine Config wurde zurückgesetzt.** Wer macht das?

## Root-Cause: "Active Config-Override Script" Pattern

**Der Schuldige ist fast immer ein Bash/Python-Script in `~/.hermes/scripts/` oder `~/bin/`, das via Cron regelmäßig läuft und `config.yaml` schreibt.**

Canonical Example (gefunden 2026-06-08 in Basti's Setup):
```bash
# ~/.hermes/scripts/hermes-network-switch.sh
# (Original — vor Fix)

DESIRED_PROVIDER="nous"
DESIRED_MODEL="moonshotai/kimi-k2.6"

if [ "$STATUS" = "online" ]; then
    CURRENT_PROVIDER=$(python3 -c "...")
    CURRENT_MODEL=$(python3 -c "...")

    if [ "$CURRENT_PROVIDER" != "$DESIRED_PROVIDER" ] || [ "$CURRENT_MODEL" != "$DESIRED_MODEL" ]; then
        # ⚠ Auto-DRIFT: Config wird auf "nous" + "kimi" zurückgesetzt
        python3 -c "
import yaml
with open('$CONFIG') as f: cfg = yaml.safe_load(f)
cfg['model']['provider'] = '$DESIRED_PROVIDER'
cfg['model']['default'] = '$DESIRED_MODEL'
with open('$CONFIG', 'w') as f: yaml.dump(cfg, f, ...)
"
    fi
fi
```

Cron-Aufruf: `hermes cron list | grep "hermes-network-monitor"` — Schedule `*/15 * * * *` (alle 15min).

**Kommentar im Script verriet es:**
> "ACHTUNG: Ollama wurde restlos entfernt (Sicherheitsgründe). Es gibt KEINEN lokalen Fallback mehr — nur noch Nous Portal."

→ Das Script war in einer früheren Setup-Phase absichtlich so gebaut worden, um Ollama zu deaktivieren. Als der User später auf 100% lokal wechseln wollte, hat das Script die Migration aktiv sabotiert.

## Detection Recipe

```bash
# 1. Welche Scripts schreiben model.default / model.provider?
grep -rn "model.*default\|model.*provider\|DESIRED_PROVIDER" \
  ~/.hermes/scripts/ ~/bin/ 2>/dev/null

# 2. Welche Scripts berühren config.yaml mit Schreibzugriff?
for f in $(grep -rln "config.yaml" ~/.hermes/scripts/ ~/bin/ 2>/dev/null); do
    if grep -qE "open\([^)]*'w'.*config|with open\([^)]*'w'.*config|yaml\.dump" "$f"; then
        echo "  ⚠ $f schreibt config.yaml"
    fi
done

# 3. Welche Crons rufen welche Scripts auf?
hermes cron list | grep -B 1 -A 5 "Script:" | grep -E "Name|Script"

# 4. In den letzten X Minuten wurde config.yaml modifiziert?
find ~/.hermes -name "config.yaml" -mmin -15 -ls

# 5. Cron-tick Log (welche Crons laufen JETZT)?
tail -200 ~/.hermes/logs/gateway.log 2>/dev/null | grep -iE "config|default" | tail -5
```

**Wenn du einen positiven Match findest, hast du den Übeltäter.** Springe direkt zur 3-Tier-Fix.

## 3-Tier Protection Pattern

**Eine Schutzebene allein reicht NICHT.** Du brauchst alle drei für garantierte Persistenz:

### Tier 1: Cron pausieren (verhindert die Auto-Drift-Quelle)

```bash
# Identifiziere den Cron
hermes cron list | grep "network-monitor"
# Job-ID: z.B. 3f8e7ee3cf3a

# Pausieren (nicht löschen — du willst evtl. später reaktivieren)
hermes cron pause 3f8e7ee3cf3a

# Verify
hermes cron list | grep "network-monitor"
# → "Schedule: */15 * * * *" + "active" sollte jetzt "paused" sein
```

**Vorteil:** Sofort, reversibel, kein Risiko.
**Nachteil:** Nützt nichts wenn jemand anderes (manueller Aufruf, anderer Cron) das Script startet.

### Tier 2: Script umschreiben (sodass es nicht den falschen Provider forciert)

**Original-Script (BÖSE für lokal-Setup):**
```bash
DESIRED_PROVIDER="nous"
DESIRED_MODEL="moonshotai/kimi-k2.6"
# ... prüft, setzt wenn nicht matched
```

**v2 (GUT für lokal-Setup):**
```bash
DESIRED_PROVIDER="ollama"
DESIRED_MODEL="pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2:hermes"

# 1. Ist Ollama erreichbar?
if ! curl -sf --max-time 3 "http://127.0.0.1:11434/api/tags" >/dev/null; then
    echo "🔴 OLLAMA DOWN — bitte starten"
    exit 1
fi

# 2. Stimmt die Config?
CURRENT_PROVIDER=$(python3 -c "...")
if [ "$CURRENT_PROVIDER" = "$DESIRED_PROVIDER" ] && [ "$CURRENT_MODEL" = "$DESIRED_MODEL" ]; then
    echo "🟢 Config OK"
    exit 0
fi

# 3. Auto-Repair
python3 << PYEOF
import yaml
with open('$CONFIG') as f: cfg = yaml.safe_load(f)
cfg['model']['provider'] = '$DESIRED_PROVIDER'
cfg['model']['default'] = '$DESIRED_MODEL'
cfg['model']['model'] = '$DESIRED_MODEL'
with open('$CONFIG', 'w') as f:
    yaml.safe_dump(cfg, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
PYEOF
```

**Vorteil:** Selbst wenn der Cron wieder aktiviert wird, schadet er nicht mehr — er repariert.
**Nachteil:** Erfordert das Original-Script zu finden und zu verstehen.

### Tier 3: Watchdog-Cron (eigener Cron der alle 5min prüft + repariert + alertet)

```bash
# Cron erstellen
hermes cron create "*/5 * * * *" --name hermes-local-guard \
  --script hermes-local-guard.sh --no-agent --deliver local
# Job-ID: z.B. f3f6915937b4
```

Das Watchdog-Script prüft:
1. `model.provider` + `model.default` stimmen — sonst **Auto-Repair** (yaml.safe_dump) + Alert
2. Keine Auxiliary-Provider auf `nous`/`openrouter`/`auto` — sonst Alert (Datenschutz-Indikator!)
3. Keine Cloud-Provider in `fallback_providers` — sonst Alert
4. Ollama erreichbar (curl `/api/tags`) — sonst Alert

Siehe `scripts/hermes-local-guard.sh` (Template im selben Skill).

**Vorteil:** Selbst wenn Tier 1 + 2 versagen, fängt Tier 3 die Drift ab.
**Nachteil:** Braucht ein zusätzliches Script, regelmäßiger 5min-Cron-Lauf.

## Verifikation (post-fix)

```bash
# 1. Config jetzt korrekt?
grep -A 9 "^model:" ~/.hermes/config.yaml | head -10
# → model.default: pdurugyan/qwen3.5-9b-...:hermes
# → model.provider: ollama

# 2. Hermes tatsächlich auf qwen?
hermes status | grep -E "Model|Provider"
# → qwen3.5-9b:hermes + Custom endpoint

# 3. Watchdog funktioniert (manueller Trigger)
bash ~/.hermes/scripts/hermes-local-guard.sh
# Silent exit 0 = alles OK
# Alert mit "Config-Drift" exit 1 = Auto-Repair lief

# 4. Warte 10 Minuten, prüfe erneut
sleep 600 && grep "^  default:" ~/.hermes/config.yaml
# → immer noch qwen3.5-9b:hermes ✓
```

## Mnemosyne 100% Local Config (Template)

Falls du **Hermes komplett offline** betreiben willst (100% lokal, keine Cloud-LLM-Calls), ist dies die **komplette** Config-Form. Inverse von "Ollama als Fallback":

```yaml
# === Main model (lokal) ===
model:
  api_key: ollama
  base_url: http://127.0.0.1:11434/v1
  context_length: 24576
  default: pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2:hermes
  model: <same>
  max_tokens: 4096
  ollama_num_ctx: 24576
  provider: ollama

# === Fallback-Chain (NUR lokal) ===
fallback_providers:
  - model: pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2:hermes
    provider: ollama        # Stufe 1: Retry mit gleichem Modell
  - model: deepseek-r1:8b
    provider: ollama        # Stufe 2: anderes Modell (deepseek-r1:8b lokal)
# KEIN cloud-fallback!

# === Auxiliary (10x ollama, 1x disabled) ===
auxiliary:
  approval:           { provider: ollama, model: qwen3.5-9b-...:hermes, ... }
  compression:        { provider: ollama, ... }
  curator:            { provider: ollama, ... }
  kanban_decomposer:  { provider: ollama, ... }
  mcp:                { provider: ollama, ... }
  profile_describer:  { provider: ollama, ... }
  skills_hub:         { provider: ollama, ... }
  title_generation:   { provider: ollama, ... }
  triage_specifier:   { provider: ollama, ... }
  vision:             { provider: none, model: '', ... }  # DISABLED
  web_extract:        { provider: ollama, ... }

# === Memory (lokal Mnemosyne, Multilingual-Embedding) ===
memory:
  provider: mnemosyne
  memory_char_limit: 2000
  user_char_limit: 1500
  mnemosyne:
    embedding_model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    auto_sleep: true
    sleep_threshold: 30
    vector_type: int8
```

**Set via PyYAML** (weil `hermes config set` keine Listen kann):
```python
import yaml
with open('/home/bratan/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)

cfg['model'] = {
    'api_key': 'ollama', 'base_url': 'http://127.0.0.1:11434/v1',
    'context_length': 24576, 'max_tokens': 4096, 'ollama_num_ctx': 24576,
    'default': 'pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2:hermes',
    'model': '<same>', 'provider': 'ollama',
}
cfg['fallback_providers'] = [
    {'model': 'pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2:hermes', 'provider': 'ollama'},
    {'model': 'deepseek-r1:8b', 'provider': 'ollama'},
]
# 10x auxiliary auf ollama
for slot in ['approval','compression','curator','kanban_decomposer','mcp',
             'profile_describer','skills_hub','title_generation',
             'triage_specifier','web_extract']:
    cfg['auxiliary'][slot] = {
        'api_key': 'ollama', 'base_url': 'http://127.0.0.1:11434/v1',
        'extra_body': {}, 'model': 'pdurugyan/qwen3.5-9b-...:hermes',
        'provider': 'ollama', 'timeout': 30,
    }
# vision: disabled (kein llama3.2-vision lokal)
cfg['auxiliary']['vision'] = {
    'api_key': '', 'base_url': '', 'extra_body': {}, 'model': '',
    'provider': 'none', 'timeout': 120, 'download_timeout': 30,
}
with open('/home/bratan/.hermes/config.yaml', 'w') as f:
    yaml.safe_dump(cfg, f, default_flow_style=False, sort_keys=False,
                   allow_unicode=True, width=1000)
```

## Siehe auch

- `scripts/hermes-local-guard.sh` (im selben Skill) — Watchdog-Template
- `scripts/mnemosyne-sleep.sh` + `scripts/mnemosyne-backup.sh` — Mnemosyne-Production-Crons (mit flock-Locking)
- `references/mnemosyne-setup-2026-06-08.md` — Multilingual-Embedding, remember()-API, Sleep-Edge-Case
- `references/ollama-provider-security.md` — Auxiliary-401 (Cloud-Default, lokal aus)
- `~/docs/system/hermes-offline-migration.md` — Vollständige Case Study (06-08)
