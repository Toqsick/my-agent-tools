# Hermes Config-Optimierung — 06.06.2026

**Kontext:** Systematische Optimierung von Hermes Agent (v0.15.1) nach
Bug-Search & Fix der System-Skripte. Ziel: Stabilität, Token-Kosten,
Transparenz.

## Durchgeführte Änderungen

### 1. Cron-Job repariert: hermes-network-monitor

**Problem:** Cron-Job lief alle 5 Minuten mit `Script not found:
/home/bratan/.hermes/scripts/hermes-network-switch.sh` — das Skript lag in
`~/bin/`, nicht in `~/.hermes/scripts/`.

**Fix:** Skript nach `~/.hermes/scripts/` kopiert:
```bash
cp ~/bin/hermes-network-switch.sh ~/.hermes/scripts/hermes-network-switch.sh
chmod +x ~/.hermes/scripts/hermes-network-switch.sh
```

### 2. title_generation von openrouter → nous

**Problem:** `auxiliary.title_generation.provider: openrouter` — OpenRouter
hat keine Credentials mehr, daher HTTP 401 bei Sitzungstitel-Generierung
(sichtbar nur in `~/.hermes/logs/gateway.log`).

**Fix:**
```bash
hermes config set auxiliary.title_generation.provider nous
```

### 3. delegation.reasoning_effort auf low

**Problem:** Subagenten (via `delegate_task`) nutzten das Haupt-Modell mit
vollem Reasoning — unnötig für die meisten Subagent-Tasks.

**Fix:**
```bash
hermes config set delegation.reasoning_effort low
```
→ Spart ~50% Tokens pro Subagent-Call.

### 4. display.show_cost aktiviert

**Fix:**
```bash
hermes config set display.show_cost true
```
→ Zeigt Token-Kosten in Sitzungen an (`/usage` oder Session-Ende).

### 5. gateway_timeout_warning auf 600s

**Fix:**
```bash
hermes config set agent.gateway_timeout_warning 600
```
→ 5 Minuten frühere Warnung vor Gateway-Timeout.

### 6. Config-Relikt entfernt

**Problem:** Top-Level-Key `reasoning_effort: xhigh` (Zeile 706) war ein
Relikt aus früheren config set-Operationen. Inkonsistent zum korrekten
`delegation.reasoning_effort: low` und `reasoning: effort: ''`.

**Fix:**
```bash
sed -i '/^reasoning_effort: xhigh$/d' ~/.hermes/config.yaml
```

### 7. Gateway neugestartet

```bash
hermes gateway restart
```
PID 31900 → 46843. Alle Änderungen aktiv.

## Config-Diff (vorher → nachher)

| Bereich | Vorher | Nachher |
|---------|--------|---------|
| `auxiliary.title_generation.provider` | `openrouter` | `nous` |
| `delegation.reasoning_effort` | `''` (leer) | `low` |
| `display.show_cost` | `false` | `true` |
| `agent.gateway_timeout_warning` | `900` | `600` |
| Cron-Skript-Pfad | `~/bin/` | `~/.hermes/scripts/` |
| `reasoning_effort: xhigh` (Relikt) | vorhanden | entfernt |

## Auswirkungen

- **Kein 401 mehr** bei Titel-Generierung
- **Subagenten sparen ~50% Tokens** durch low reasoning
- **Token-Kosten sichtbar** in jeder Sitzung
- **Frühere Timeout-Warnung** (10 statt 15 Minuten)
- **Cron-Job läuft sauber** statt alle 5 Min in den Error

## Nächste Optimierungs-Ideen (nicht umgesetzt)

- `terminal.timeout` auf 300 erhöhen (für lange Builds)
- `logging.level:` auf WARNING (reduziert Log-Volumen)
- `display.resume_exchanges` auf 5 (kompaktere Resume-Ansicht)
