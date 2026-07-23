# state.db Maintenance & VACUUM Pattern (2026-06-08)

## state.db Größe: Was ist normal?

`~/.hermes/state.db` wächst mit jeder Session. Faustregeln (gemessen 2026-06-08 mit 143 Sessions):

| Sessions | DB-Größe | Bewertung |
|----------|----------|-----------|
| <50 | 30-60 MB | normal |
| 50-200 | 60-150 MB | normal |
| 200-500 | 150-400 MB | evtl. prune sinnvoll |
| >500 | >400 MB | prune empfohlen |

**state.db Schema (28 columns per session):**
`id, source, user_id, model, model_config, system_prompt, parent_session_id,
started_at, ended_at, end_reason, message_count, tool_call_count, input_tokens,
output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens, cwd,
billing_provider, billing_base_url, billing_mode, estimated_cost_usd, actual_cost_usd,
cost_status, cost_source, pricing_version, title, api_call_count, handoff_state,
handoff_platform, handoff_error, rewind_count, archived`

Die Token-Tracking-Spalten (`input_tokens`, `output_tokens`, `cache_read_tokens`,
`cache_write_tokens`, `reasoning_tokens`, `estimated_cost_usd`, `actual_cost_usd`)
sind die Haupt-Speicherfresser. Bei intensiver Nutzung mit großen Modellen
schnell 100+ MB.

## Wann prune, wann VACUUM?

| Situation | Aktion | Effekt |
|-----------|--------|--------|
| Sessions >30 Tage alt vorhanden | `hermes sessions prune --older-than 30 --yes` | löscht Daten |
| Alle Sessions neu, DB trotzdem groß | `VACUUM` | reclaimt Space, löscht nichts |
| Beides | Erst prune, dann VACUUM | maximaler Effekt |

## VACUUM-Pattern (Pitfall: prunet nichts bei jungen DBs)

`hermes sessions prune --older-than 30` löscht NUR Sessions älter als 30 Tage.
**Wenn alle Sessions <7 Tage alt sind** (frischer Hermes-Setup, kurze
Installationsphase, neu hochgezogenes System), löscht prune NICHTS. Das
kann frustrierend sein wenn man eine 116MB DB loswerden will.

**Alternative — `VACUUM` (nicht-destruktiv):**

```bash
# 1. Backup (IMMER — VACUUM ist sicher, aber Backup ist günstige Versicherung)
cp ~/.hermes/state.db ~/.hermes/state.db.pre-vacuum-$(date +%s).bak

# 2. Integrity-Check VOR vacuum (sollte "ok" returnen)
sqlite3 ~/.hermes/state.db "PRAGMA integrity_check"

# 3. Vacuum (1-5s bei 150MB)
sqlite3 ~/.hermes/state.db "VACUUM"

# 4. Vorher/Nachher-Vergleich
ls -la ~/.hermes/state.db ~/.hermes/state.db.pre-vacuum-*.bak
```

**Realer Erfahrungswert 2026-06-08:**
- 122.6 MB DB mit 143 Sessions, alle <7 Tage
- VACUUM: 122.6 MB → 121.5 MB (1.1 MB freigegeben)
- Bei fragmentierten DBs (viele gelöschte/archivierte Sessions) deutlich mehr

**Wann VACUUM deutlich mehr bringt:**
- Viele Sessions wurden gelöscht/archiviert (z.B. nach mehreren prune-Runs)
- Hermes wurde mehrmals geupdatet (Schema-Änderungen können Fragmente hinterlassen)
- DB wurde nicht regelmäßig komprimiert

## Warum VACUUM nicht im Hermes CLI?

`VACUUM` ist eine SQLite-spezifische Operation. Hermes abstrahiert die DB-Zugriffe
und bietet nur `prune` als user-facing cleanup. VACUUM muss manuell via
`sqlite3`-Binary gemacht werden.

**Voraussetzung:** `sqlite3` muss installiert sein:
```bash
which sqlite3 || sudo apt install sqlite3
```

## state.db Schema-Inspizieren (für eigene Analysen)

```bash
# Columns pro Tabelle
sqlite3 ~/.hermes/state.db ".schema sessions" | head -50

# Sessions by source + age
sqlite3 ~/.hermes/state.db "
  SELECT source, COUNT(*),
         ROUND(SUM(estimated_cost_usd), 2) as cost
  FROM sessions
  GROUP BY source
  ORDER BY count DESC"

# Top 10 teuerste Sessions
sqlite3 ~/.hermes/state.db "
  SELECT id, source, model,
         ROUND(estimated_cost_usd, 2) as cost,
         input_tokens + output_tokens as total_tokens
  FROM sessions
  ORDER BY estimated_cost_usd DESC
  LIMIT 10"
```

## Cleanup-Strategie: Empfohlene Reihenfolge

```bash
# 1. Alte Sessions löschen (>30 Tage)
hermes sessions prune --older-than 30 --yes

# 2. VACUUM für Fragmentierung
sqlite3 ~/.hermes/state.db "VACUUM"

# 3. Optional: WAL/SHM-Files aufräumen
ls -la ~/.hermes/state.db*
# state.db-wal und state.db-shm werden automatisch gemerged beim nächsten close

# 4. Cache-Cleanup (npm, pip, uv, huggingface)
npm cache clean --force
pip cache purge
uv cache clean
# Huggingface-Cache: rm -rf ~/.cache/huggingface (regeneriert sich)

# 5. Alte state-snapshots löschen (NUR wenn Pre-Update-Snapshot nicht gebraucht)
ls -la ~/.hermes/state-snapshots/
# Behalte das neueste, lösche ältere (VORHER testen dass aktueller Hermes-Stand stabil läuft!)
```

## Pitfall: state.db Backup NICHT übersehen

`VACUUM` ist sicher, aber:
- DB-Inkonsistenzen können bei Hardware-Fail auftreten
- `cp` während aktiver Sessions ist nicht atomar
- Beste Practice: `hermes gateway stop && cp state.db .../ && hermes gateway start`
- Oder: SQLite `.backup` command (atomar):
  ```bash
  sqlite3 ~/.hermes/state.db ".backup /tmp/state.db.snapshot"
  ```
