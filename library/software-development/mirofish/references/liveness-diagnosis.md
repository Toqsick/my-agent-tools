# Liveness-Diagnose: Simulation scheint tot, läuft aber wirklich?

Gelernt aus Sim09 Run A (Skill-Chaining, 2026-07-13): Die `run_state.json` kann **komplett eingefroren** sein + der `run-status`-API-Endpoint liefert Start-Snapshot-Daten. Die Simulation produziert trotzdem. So erkennst du den Unterschied.

## Schnell-Check (30 Sekunden)

```bash
SIM_ID="sim_4eab9449aac7"  # <-- deine Sim-ID
SIM_DIR="backend/uploads/simulations/$SIM_ID"

# 1. HOL DIR DEN WORKER-PID
WORKER_PID=$(cat "$SIM_DIR/run_state.json" 2>/dev/null | python3 -c "
import json,sys; d=json.load(sys.stdin)
print(d.get('process_pid', '?'))
" 2>/dev/null)
echo "Worker PID: $WORKER_PID"

# 2. WORKER LEBT? (State: R = running, S = sleeping)
cat /proc/$WORKER_PID/status 2>/dev/null | grep -E '^(Name|State|VmRSS)'
if [ $? -ne 0 ]; then echo "❌ PID weg = tot"; fi

# 3. SCHREIBT ER? (File Descriptors checken)
ls /proc/$WORKER_PID/fd/ 2>/dev/null | grep -q 'twitter_simulation.db'
if [ $? -eq 0 ]; then echo "✅ DB open — schreibt aktiv"; fi

# 4. SIMULATION.LOG CHECK (Wahrheit)
echo "=== Letzte 3 Runden aus simulation.log ==="
grep -oE '\[Day [0-9]+, [0-9:]+\] Round [0-9]+/[0-9]+' \
  "$SIM_DIR/simulation.log" | tail -3

# 5. DB WÄCHST? (Sekundär-Signal)
ls -lh "$SIM_DIR/twitter_simulation.db"
```

## Drei mögliche Befunde

| PID lebt? | DB wächst? | simulation.log zeigt Runden? | Diagnose |
|---|---|---|---|
| ✅ Ja | ✅ Ja | ✅ Ja | **Level 3 Frozen** — Simulation läuft sauber, run_state.json nie aktualisiert. Sofort auf simulation.log-Monitoring umschalten. |
| ✅ Ja | ✅ Ja | ❌ Nein | **Level 2 Deep Staleness** — Erste Runde braucht >10 Min (dense seed). Warte auf simulation.log-Einträge. |
| ❌ Nein | ❌ Nein | ❌ Nein | **Simulation tot.** Backend + Worker neustarten. |

## Wenn Level 3 bestätigt ist (häufigster Fall)

**Falscher Alarm erkennen:** Der Watcher zeigt "stuck at R0 for 5 min" — ignoriere ihn. Die simulation.log hat echte Daten.

**Monitoring auf simulation.log umstellen (statt run_state.json):**
```bash
# Echtzeit-Runden verfolgen
watch -n 15 "grep -oE '\[Day [0-9]+, [0-9:]+\] Round [0-9]+/[0-9]+' \
  backend/uploads/simulations/$SIM_ID/simulation.log | tail -5"
```

**Fake-"Link!" Antwort (wenn User nach URL fragt):**
Antworte NUR mit der URL, nichts erklären:
```
http://localhost:3000/simulation/$SIM_ID/start
```

## Referenz: Sim09 Run A (2026-07-13) Frozen State

Die Beobachtungen aus dem ersten echten Level-3-Fall:

| Messung | Wert |
|---|---|
| run_state.json.updated_at | `2026-07-13T19:18:43` (start time, **nie aktualisiert**) |
| run_state.json.current_round | 0 (**nie geschrieben**) |
| simulation.log Round | `[Day 1, 19:00] Round 20/60` |
| Worker PID State | `R (running)` |
| DB Größe nach 5 Min | 327 KB (10 posts+) |
| Backend-Log | Kein OASIS-Writer-Error |