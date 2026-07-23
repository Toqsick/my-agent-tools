# Mnemosyne Memory-Provider — Detailed Setup Notes

**Datum:** 2026-06-08
**Status:** Production-ready (Phase 1-3 verifiziert, Phase 4 Doku)
**Source:** Drei Phase-Reports unter `~/docs/system/mnemosyne-phase{1,2,3}-report.md`

## Quick Reference: Warum Mnemosyne statt eingebautem nous-Provider

- **100% lokal** — keine Cloud-Calls, keine API-Keys, keine Subscription
- **Sub-ms Latenz** für DB-Operationen (mit Embedding ~10ms)
- **Multilingual-Embedding** — kritisch für deutsche Texte (5/5 vs 2/5 Recall)
- **17 Tools** im Hermes-Plugin (remember/recall/stats/sleep/import/export/TripleStore/Scratchpad)
- **Cross-Session-Memory** via Hermes-Hooks (pre_llm_call, post_tool_call)
- **Triple-Store** für zeitbewusstes KG (subject, predicate, object mit valid_from/to)

## Pitfalls (alle aus der 2026-06-08 Session)

### Pitfall 1: Plugin-Folder-Name

**Mnemosyne Installer legt `hermes-mnemosyne/` an, Hermes scannt aber nach `<provider-name>/`.**

```bash
# BAD — Hermes findet es nicht
~/.hermes/plugins/hermes-mnemosyne/

# GOOD — manuell umbenennen
mv ~/.hermes/plugins/hermes-mnemosyne ~/.hermes/plugins/mnemosyne
```

Verifiziert: 2026-06-08, nach dem Rename zeigte `hermes memory status` → "Plugin: installed ✓".

### Pitfall 2: Hermes-venv hat kein pip

**Auf Ubuntu 24.04+ ist `~/.hermes/hermes-agent/venv/` ohne pip (via `uv` erstellt). `python -m ensurepip` fehlt auch.**

```bash
# BAD
~/.hermes/hermes-agent/venv/bin/pip install mnemosyne
# → "No module named pip"

# GOOD — uv pip direkt
cd ~/.hermes/hermes-agent
uv pip install --python venv/bin/python3 "mnemosyne-memory[embeddings]" "mnemosyne-hermes"
```

### Pitfall 3: Default-Embedding ist englisch

**Mnemosyne nutzt Default `bge-small-en-v1.5` — funktioniert NICHT für deutsche Texte.**

| Sprache | Default-Embedding | Multilingual-Embedding |
|---|---|---|
| Englisch | 5/5 ✓ | 5/5 ✓ |
| Deutsch | 2/5 ✗ | **5/5 ✓** |

```bash
# Multilingual aktivieren
hermes config set memory.mnemosyne.embedding_model "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
```

Modell-Größe: 241 MB Disk, ~240 MB extra RAM bei Load, ~20s First-Download.

### Pitfall 4: Provider-Wechsel ohne Restart

**Memory-Provider-Wechsel wird erst nach `hermes gateway restart` wirksam.**

```bash
hermes config set memory.provider mnemosyne
hermes memory status    # zeigt möglicherweise noch alten Provider bis Restart!
hermes gateway restart  # PFLICHT
hermes memory status    # jetzt korrekt: "mnemosyne ← active"
```

### Pitfall 5: Sleep-Cycle "no_op" bei frischen Memories

**Sleep konsolidiert nur "old" Memories. Bei frisch erstellten Einträgen (< 24h) sagt Sleep: "No old working memories to consolidate".**

- Kein Bug — erwartetes Verhalten
- Täglicher Cron um 4 Uhr löst das automatisch
- Erste erfolgreiche Konsolidierung meist nach 24h
- Bei dauerhaftem no_op nach 48h → Bug-Report an AxDSan

### Pitfall 6: Hook-Overhead ≠ Ollama-Kaltstart

**Erster Hermes-Call nach >10 Min Idle dauert 80-90s — das ist NICHT Mnemosyne-Overhead, sondern Ollama's 9B-Model-Reload (4-5 GB in VRAM).**

Echter Mnemosyne-Overhead: **~2.5s Median** (im 9B-Rauschen verschwindend). Nach 5+ Hermes-Calls mit warmem Cache: 9-11s pro Call, **unabhängig vom Provider**.

## Configuration Reference

### Root Config (`~/.hermes/config.yaml`)

```yaml
memory:
  provider: mnemosyne                              # Built-in nous ersetzen
  memory_char_limit: 2000
  user_char_limit: 1500
  mnemosyne:                                       # provider-spezifisch
    embedding_model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    auto_sleep: true                               # Sleep triggert automatisch
    sleep_threshold: 30                            # nach 30 Working-Memories
    vector_type: int8                              # kompakte Vector-Storage
```

### Crons (Production-Hardening)

```bash
# Sleep-Cron — täglich 4 Uhr
hermes cron create "0 4 * * *" --name mnemosyne-sleep \
  --script mnemosyne-sleep.sh --no-agent --deliver local
# Job-ID: f31e9bc21117

# Backup-Cron — täglich 5 Uhr, 7-Tage-Retention
hermes cron create "0 5 * * *" --name mnemosyne-backup \
  --script mnemosyne-backup.sh --no-agent --deliver local
# Job-ID: d64840a80f53
```

### Backup-Script Template

```bash
#!/bin/bash
# mnemosyne-backup.sh
set -euo pipefail
BACKUP_DIR="/home/bratan/backups/mnemosyne"
DB_PATH="/home/bratan/.hermes/mnemosyne/data/mnemosyne.db"
LOG="/home/bratan/.hermes/logs/mnemosyne-backup.log"
RETENTION_DAYS=7

mkdir -p "$BACKUP_DIR" "$(dirname "$LOG")"

# Konsistenter Snapshot via sqlite3 .backup
TIMESTAMP=$(date +%Y-%m-%d)
BACKUP_FILE="$BACKUP_DIR/mnemosyne-$TIMESTAMP.db"
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

# Retention cleanup
find "$BACKUP_DIR" -name "mnemosyne-*.db" -mtime +$RETENTION_DAYS -delete

# Log
SIZE=$(stat -c%s "$BACKUP_FILE")
echo "[$(date -Iseconds)] Backup OK: $BACKUP_FILE ($SIZE bytes)" >> "$LOG"
```

## Performance Benchmarks (von 2026-06-08)

| Metrik | Wert |
|---|---|
| Hook-Overhead (Median, gleiche Query, warmer Cache) | ~2.5s |
| Hook-Overhead (Mean) | ~0.5s (im 9B-Rauschen) |
| Write-Latenz (EN-Embedding, ohne Cold-Start) | 10ms Median |
| Read-Latenz (Multilingual, ohne Cold-Start) | 6ms Median |
| First-Write (Cold, Multilingual-Model-Download) | 23s |
| Warm Hermes-Call (9B + Mnemosyne, alles gecached) | 9-11s |
| Cold Hermes-Call (9B-Model-Reload) | 80-90s (NICHT Mnemosyne-Overhead) |
| Recall-Quality (DE, Multilingual) | 5/5 |
| Recall-Quality (DE, EN-Embedding) | 2/5 |
| RAM (warm, mit Multilingual-Embedding) | +241 MB |
| Disk (Multilingual-Embedding-Cache) | +241 MB |

## Rollback

**Minimaler Rollback** (1 Zeile, behält DB):
```bash
hermes config set memory.provider nous
hermes gateway restart
```

**Voller Uninstall** (löscht alle Memories):
```bash
# VORHER: Export!
hermes mnemosyne export --output ~/backups/mnemosyne-final.json

# 1. Config zurücksetzen
hermes config set memory.provider nous

# 2. Plugin-Datei löschen
rm -rf ~/.hermes/plugins/mnemosyne

# 3. Python-Package entfernen
cd ~/.hermes/hermes-agent
uv pip uninstall mnemosyne-memory mnemosyne-hermes

# 4. DB + Cache löschen (alle Memories weg!)
rm -rf ~/.hermes/mnemosyne
rm -rf ~/.hermes/cache/fastembed

# 5. Crons entfernen
hermes cron remove f31e9bc21117
hermes cron remove d64840a80f53
```

## Quick-Check: Läuft mein Mnemosyne-Setup?

```bash
# 1. Plugin aktiv?
hermes memory status | grep -E "Provider|Plugin|Status"

# 2. Stats lesbar?
hermes mnemosyne stats

# 3. Recall funktioniert (deutsch)?
hermes chat -q "Welches Linux nutze ich?" --quiet
# Erwartete Antwort: Zorin OS (oder ähnlich — basiert auf deinen Memories)

# 4. Backups laufen?
ls -la ~/backups/mnemosyne/

# 5. Sleep funktioniert?
hermes mnemosyne sleep --dry-run
```

## Siehe auch

- `references/ollama-provider-security.md` — Ollama-Setup, Auxiliary 401 Fix
- `references/local-llm-ollama-primary.md` — Ollama als Hauptmodell (9B Qwen)
- `~/docs/system/mnemosyne-phase1-report.md` — Read-only-Test mit Latenz-Tabellen
- `~/docs/system/mnemosyne-phase2-report.md` — Plugin-Integration + End-to-End
- `~/docs/system/mnemosyne-phase3-report.md` — Production-Hardening
- `~/docs/system/mnemosyne-setup.md` — Master-Doku
- GitHub: https://github.com/AxDSan/mnemosyne
- PyPI: `mnemosyne-memory` 3.3.0, `mnemosyne-hermes` 0.1.1
