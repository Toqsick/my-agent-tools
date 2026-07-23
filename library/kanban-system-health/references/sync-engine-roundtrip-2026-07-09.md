# Sync Engine Roundtrip Test — 2026-07-09

## Ziel

Vollständigen Roundtrip der `sync_engine.py` testen:
`db_to_md` → manueller MD-Edit (Status ändern) → `md_to_db` → `auto` (Drift-Erkennung)

**Quelle:** `~/.hermes/scripts/sync_engine.py`
**DB:** `~/.hermes/kanban/boards/hermes/kanban.db`
**MD:** `~/Documents/Obsidian/Hermes-Agent/kanban.md`

## Test-Methodik (Wiederverwendbar)

```
1. Ist-Zustand erfassen (DB-Inhalt + kanban.md + sync_state)
2. 2 Test-Tasks in DB anlegen (create_task)
3. db_to_md → verifizieren dass Tasks in kanban.md erscheinen
4. MD manuell editieren (check-box + Section-Change simulieren)
5. md_to_db → ausführen
6. Verifikation: DB-Status = erwarteter Status
7. auto → verifizieren Drift-Erkennung (sollte no_change sagen)
8. Cleanup: Tasks löschen, sync_state zurücksetzen, db_to_md
```

## Resultate

| Run | Direction | Output |
|-----|-----------|--------|
| 1 | `db_to_md` | `rendered=23` (21 alt + 2 neu) |
| 2 | `md_to_db` | `status=1 title=0 skip=0` |
| 3 | `auto` | `direction=no_change — nothing to do` |

**Roundtrip erfolgreich:** ALPHA `ready→done`, BRAVO unverändert `ready`.

## 5 Edge-Cases

### 1. `create_task` defaultet auf `ready`, nicht `todo`
Der `kanban_db.create_task`-Wrapper setzt bei `priority >= 1` den Status auf `ready` statt `todo`. Konsequenz: neue Tasks landen in `## Ready`, nicht `## Todo`.

**Workaround:** Für Test-Zwecke `priority=0` setzen, ODER `## Ready` im Test erwarten.

### 2. Sync-Engine-Log hat keine Task-IDs bei md_to_db
`status=1 title=0 skip=0` zählt nur Summary-Werte. Bei vielen gleichzeitigen Edits ist Debugging, welche Task genau geändert wurde, nur via SQL möglich.

**Nice-to-have:** Logging um Task-IDs erweitern: `status=N task_ids=t_xxx,t_yyy`.

### 3. Section-Header-Erkennung case-sensitive
Erwartet exakt `## Done`, `## Ready`, `## Blocked`, `## Todo`, `## Running`. Abweichende Schreibweisen (`## done`) landen im Lost-&-Found-Bereich.

**Status:** Expected behavior — kanban.md nutzt kanonische Header.

### 4. `_nothing here_` Placeholder wird sauber verdrängt
Leere Sections haben `_nothing here_`. Beim manuellen Move einer Task in eine leere Section wird der Placeholder durch md_to_db korrekt entfernt.

**Status:** Funktionierend — kein Fix nötig.

### 5. Roundtrip-Idempotenz bestätigt
Nach md_to_db waren DB und MD konsistent. Der unmittelbar folgende `auto`-Run erkannte `no_change`. Die Hash-basierte Drift-Detektion arbeitet zuverlässig.

**Status:** ✅ Production-Ready.

## Empfehlung für Cron-Betrieb

```yaml
# Cron-Job sollte `auto` nutzen (Hash-Drift-Erkennung)
# Fallback: md_to_db bei Bidirectional-Drift
# Tick: 60s (dispatch_interval_seconds)
```

## CLI-Befehle (für schnelle Wiederholung)

```bash
# db_to_md
/home/bratan/.hermes/hermes-agent/venv/bin/python3 \
  /home/bratan/.hermes/scripts/sync_engine.py --direction db_to_md

# md_to_db
/home/bratan/.hermes/hermes-agent/venv/bin/python3 \
  /home/bratan/.hermes/scripts/sync_engine.py --direction md_to_db

# auto (Drift-Erkennung)
/home/bratan/.hermes/hermes-agent/venv/bin/python3 \
  /home/bratan/.hermes/scripts/sync_engine.py --direction auto

# SQL-Verifikation
sqlite3 /home/bratan/.hermes/kanban/boards/hermes/kanban.db \
  "SELECT id, status, title FROM tasks WHERE title LIKE 'SYNC-ROUNDTRIP-%'"
```

## Verwandte Doku

- `kanban-system-health` — Kanban Operations-Playbook
- `~/docs/system/kanban-sync-engine-*.md` — Sync-Engine-Architektur (falls vorhanden)