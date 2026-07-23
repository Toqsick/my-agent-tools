# Crontab Safety Patterns

> Erkenntnisse aus der Session 2026-07-05: Fast vollständiger Crontab-Verlust durch
> fehlerhaftes `awk`-Dedup-Muster, Recovery aus Backup.

## Grundregeln für Crontab-Edits

1. **Immer zuerst Backup.** Vor jeder Crontab-Änderung:
   ```bash
   crontab -l > ~/50-System/backups/crontab-pre-$(date +%Y-%m-%d).bak
   ```

2. **Here-Doc statt `-e`.** `crontab -` aus einer Here-Doc ist deterministischer
   als `crontab -e` (kein Editor, kein versehentliches Doppel-Einfügen):
   ```bash
   (crontab -l 2>/dev/null; echo "0 9 * * * /path/to/script.sh") | crontab -
   ```

3. **Keine Inline-Secrets.** Token, API-Keys, Chat-IDs gehören in `~/.hermes/.env`,
   nicht in die Crontab-Zeile. Immer Wrapper-Skript nutzen:
   - Crontab: `0 3 * * 0 /home/bratan/50-System/bin/wrapper.sh`
   - Wrapper: `set -a; . "$HOME/.hermes/.env"; set +a # dann exec`

4. **Nach jeder Änderung verifizieren:**
   ```bash
   crontab -l | grep -E "(bot|Token|BOT_TOKEN|CHAT_ID|\"[0-9]{6,}\")" || echo "clean"
   ```

## Recovery-Workflow bei Crontab-Verlust

Wenn die Crontab versehentlich geleert oder korrumpiert wurde:

1. **Nichts manuell neu schreiben.** Erst Backups prüfen:
   ```bash
   ls -lat ~/50-System/backups/crontab-pre-*.bak
   ls -lat ~/.hermes/backups/crontab-pre-*.bak  # falls vorhanden
   ```

2. **Backup-Content inspizieren:**
   ```bash
   cat ~/50-System/backups/crontab-pre-2026-07-05.bak
   ```

3. **Sauber neu aufbauen** (Duplikate vermeiden, Secrets entfernen):
   ```bash
   cat <<'EOF' | crontab -
   # Kommentar: Zweck des Jobs
   <schedule> <command>
   EOF
   ```

4. **Verifikation:**
   ```bash
   crontab -l           # Vollständig?
   sudo systemctl is-active cron  # Service läuft?
   ```

## Was NICHT tun

- ❌ `awk '!seen[$0]++'` zur Deduplizierung von Crontab-Zeilen — zerstört bei
     Pipe-Fehlern die gesamte Crontab (geschehen 2026-07-05)
- ❌ `crontab -r` ohne vorheriges Backup
- ❌ Tokens direkt in Crontab setzen (Working-Agreement §7)
- ❌ Crontab-Edits ohne `crontab -l > backup.bak` vorher

## Crontab-Audit-Checkliste

| Prüfung | Befehl | Soll |
|---------|--------|------|
| Secrets im Klartext? | `crontab -l \| grep -E "(bot\|Token\|CHAT_ID\|\"\[0-9\]{6,}\")"` | leer |
| Duplikate? | `crontab -l \| sort \| uniq -d` | leer |
| Alle Pfade existieren? | `crontab -l \| grep -oP '/[/a-zA-Z0-9_.-]+' \| xargs -I{} bash -c 'test -e "{}" || echo "MISSING: {}"'` | keine MISSING |
| Cron läuft? | `systemctl is-active cron` | active |

## Verbindet zu

- `yuno-cleaner` skill: `references/cron-wrapper-pattern.md` — Spezifisches Wrapper-Example
- Working-Agreement §7 — Secrets-Pfade statt Inhalte
