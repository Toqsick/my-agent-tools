# Hermes Fallback Chain — Verifizierte Mechanik (Code-Level)

> **Quelle:** Live-Code-Dive in `hermes_cli/fallback_config.py`, `agent/chat_completion_helpers.py`, `agent/agent_init.py`, `gateway/run.py` (2026-07-17)
> **Kern-Erkenntnis:** Die Fallback-Chain ist eine **statische Liste, kein State-Machine-Cursor**. Jeder neue Agent startet bei Position 0.

## Config: `fallback_providers` (statisch)

```yaml
fallback_providers:
  - provider: minimax
    model: MiniMax-M3
  - provider: zai
    model: glm-5.2
```

Die Config definiert eine **statische Liste** in der angegebenen Reihenfolge. Position 1 ist IMMER `minimax/M3`, Position 2 IMMER `zai/glm-5.2`. Es gibt **kein Gedächtnis** darüber, wo der Cursor zuletzt stand — nach jedem Session-Reset/Agent-Create startet der Index neu.

## Code-Mechanik: `try_activate_fallback()`

In `agent/chat_completion_helpers.py:1372`:

```python
def try_activate_fallback(agent, reason: "FailoverReason | None" = None) -> bool:
    # 1. Prüfe ob Index über Chain-Länge hinaus ist
    if agent._fallback_index >= len(agent._fallback_chain):
        # Chain exhausted → arm cooldown
        return False

    # 2. Nächsten Eintrag aus der Chain holen
    fb = agent._fallback_chain[agent._fallback_index]
    agent._fallback_index += 1  # ← ZÄHLT NUR HIER HOCH

    # 3. Versuche den Provider zu aktivieren
    #    Wenn fehlschlägt → rekursiv try_activate_fallback() (nächster Index)
```

**WICHTIG:** Der Index wird **nur** in `try_activate_fallback()` inkrementiert — und das nur wenn ein PROVIDER FAILURE eintritt. Ein expliziter Modell-Wechsel (via `System: The active model has changed to...`) geht einen **komplett anderen Code-Pfad** und tangiert `_fallback_index` NICHT.

## Index-Reset: Jeder neue Agent startet bei 0

In `agent/agent_init.py:1175`:

```python
agent._fallback_index = 0
agent._fallback_activated = getattr(agent, "_fallback_activated", False)
```

**Bedeutung:** Jede neue Session, jeder `/new`, jeder neue Cron-Job-Run startet mit `_fallback_index=0`. Wenn der letzte Turn auf Position 2 (GLM 5.2) war und du startest eine neue Session, geht es wieder bei Position 1 (MiniMax-M3) los.

## Cooldown-Mechaniken

| Trigger | Dauer | Code | Effekt |
|---------|-------|------|--------|
| **Rate-Limit / Billing (429, 402)** | **60 Sekunden** | `agent._rate_limited_until = time.monotonic() + 60` | Verhindert dass der Fault sofort wieder in die Chain fährt. Setzt nur wenn der Fehler an **Position 1 (Primary)** auftritt. |
| **Chain exhausted (nicht rate-limit)** | **5 Sekunden** | `_FALLBACK_EXHAUSTED_COOLDOWN_S = 5.0` | Verhindert Replay-Storm (#24996). Kurz genug für sinnvollen Turn-Wechsel, lang genug gegen 10 Back-to-Back-Versuche. |
| **HTTP 400 / Client Error** | **Kein Cooldown** | Fall-through | Nächster Turn probiert direkt Position 1 wieder. |

## Gateway: Live-Config-Refresh

In `gateway/run.py:5164`:

```python
def _refresh_fallback_model(self) -> list | None:
    """Re-read fallback_providers from disk for the next agent create/reuse."""
```

Die Gateway-Instanz refreshed die Chain **vor jedem Agent-Create/Reuse**. Eine Änderung an `fallback_providers` wirkt asynchron — kein Gateway-Restart nötig. Bei Parse-Fehler (mid-edit, #60955): behält alte Chain.

## Expliziter Model-Switch vs. Fallback-Activation

| Aspekt | Expliziter Switch | Fallback-Activation |
|--------|------------------|-------------------|
| **Auslöser** | User-Chat-Befehl (`/model`) oder System-Event | API-Fehler (Timeout, 429, 500, Auth) |
| **Flag** | Keines | `agent._fallback_activated = True` |
| **Index-Effekt** | Keiner | `_fallback_index += 1` |
| **Dauerhaftigkeit** | Bleibt bis zum nächsten expliziten Switch | Bis zum nächsten erfolgreichen Turn (dann `restore_primary_runtime`) |
| **Cooldown** | Keiner | 60s/5s je nach Fehler-Typ |

**Praxis-Beispiel:** User war auf GLM 5.2, Modell-Switch (System-Message) zu MiniMax-M3. Der Fallback-Index ist **immer noch 0** — kein Cursor-Wandering passiert.

### Fallback-Activation Lebenszyklus

1. API-Call schlägt fehl (Timeout/429/500/401)
2. Retry-Loop ruft `try_activate_fallback(reason)` auf
3. `_fallback_index` wird inkrementiert, `_fallback_activated = True`
4. Der nächste API-Call geht zum Fallback-Provider
5. **Erfolgreicher Turn:** `restore_primary_runtime()` prüft `_fallback_activated` + `_rate_limited_until`
   - Cooldown abgelaufen → Primary wird restored, `_fallback_activated = False`
   - Cooldown aktiv → Fallback bleibt für diesen Turn
6. **Fehlschlagender Turn:** `try_activate_fallback()` rekursiv → nächster Chain-Eintrag
7. **Chain exhausted:** Cooldown, keine weiteren Versuche

## Cron: Kein Fallback für LLM-Jobs

LLM-Cron-Jobs haben **gepinnte** provider+model im Job-Record. `fallback_providers` wird für Crons NICHT angewandt. Provider-Drift (#44585) tritt auf wenn:
- Der Cron unpinned ist (kein provider/model im Record)
- Die globale Config geändert wurde
- Der Cron schlägt mit `RuntimeError: Skipped to prevent unintended spend` fehl

**Fix:** `cronjob(action='update', job_id='<id>', model={'provider':'<p>', 'model':'<m>'})`

## Pitfalls

| Pitfall | Beschreibung |
|---------|-------------|
| **"Chain merkt sich Position"** | Häufigste Fehlannahme: "Ich war auf GLM, also springt Fallback zu Position 3". FALSCH — jeder neue Agent startet bei Index 0. |
| **Expliziter Switch = Fallback** | Ein System-Message-Switch ist KEIN Fallback. Der Index wird nicht erhöht. Nach einem expliziten Switch zu GLM ist bei Provider-Failure die volle Chain (1=minimax, 2=glm, 3=...) verfügbar. |
| **Cooldown-Blindheit** | Nach Rate-Limit auf Primary wird `_rate_limited_until` für 60s gesetzt. Nächster Turn kann NICHT zurück — der Fallback "klebt". Das ist Design. |
| **Model-Switch aus Fallback** | Wenn `_fallback_activated=True` und User macht `/model glm-5.2`: der Switch überschreibt den Fallback-Status. User sieht Wunschmodell — aber `_fallback_index` wurde nicht resettet. |
| **Cron: glaubt Fallback greift** | Der Cron läuft IMMER auf dem gepinnten Modell. `fallback_providers` wird nicht angewandt. Provider-Drift killt den Job hart. |
| **providers vs fallback_providers** | `providers:` definiert verfügbare Provider (können separat genutzt werden). Nur `fallback_providers:` definiert die Automatik-Chain. Ein Provider in `providers:` ohne Eintrag in `fallback_providers:` wird NIE automatisch aktiviert. |

## Verifikation

```bash
python3 -c "
from hermes_cli.fallback_config import get_fallback_chain
import yaml
cfg = yaml.safe_load(open('/home/bratan/.hermes/config.yaml'))
print(get_fallback_chain(cfg))
"

# Agent-State einer Session prüfen (wenn verfügbar)
python3 -c "
import sqlite3, json
db = sqlite3.connect('/home/bratan/.hermes/state.db')
row = db.execute('SELECT session_id, agent_state FROM sessions ORDER BY updated_at DESC LIMIT 1').fetchone()
if row:
    state = json.loads(row[1] or '{}')
    print(f'Session: {row[0]}')
    print(f'  provider: {state.get(\"provider\",\"?\")}')
    print(f'  _fallback_activated: {state.get(\"_fallback_activated\",\"?\")}')
    print(f'  _fallback_index: {state.get(\"_fallback_index\",\"?\")}')
    print(f'  _fallback_chain: {state.get(\"_fallback_chain\",\"?\")}')
"
```

## Cross-References

- `model-provider-switch.md` — Explizite Modell-Wechsel (separater Mechanismus)
- `hermes-maintenance.md` — Provider-Config und Auth
- `cron-debug-deepdive.md` — Provider-Drift bei Crons
- `cron-pinning-recovery.md` — Bulk-Recovery für gepinnte Jobs
