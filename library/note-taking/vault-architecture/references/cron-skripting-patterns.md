# Phase 11: Vault Cron Automation — Worked Example

> Erstellt 2026-07-06 aus der Phase-11-Implementierung. Beide Skripte sind live in `~/50-System/bin/` mit Crontab-Einträgen.

## Ist-Zustand (vor Phase 11)

- Crontab: 4 Jobs (yuno-cleaner, hermes-gh-api, morphreader, mnemosyne-cleanup)
- Daily Notes: manuell per Hand erstellt, Templater-PlugIn mit `<% tp.date.now(...) %>` (nicht kompatibel mit Cron — kein Obsidian-Kontext)
- Weekly Digests: nicht existent
- Mnemosyne-Sleep: nicht automatisiert

## Überblick: 2 Cron-Skripte + Template-Fix

| Script | Pfad | Schedule | Größe | 
|--------|------|----------|-------|
| `daily-note-cron.sh` | `~/50-System/bin/` | 06:00 täglich | 53 Zeilen |
| `weekly-digest-cron.sh` | `~/50-System/bin/` | Sonntag 22:00 | 107 Zeilen |

Template: `Dokumente/Obsidian Vault/_templates/Daily Note.md` — von Templater-Syntax auf `{{date}}`/`{{session_id}}` umgestellt

## Pattern-Verifikation (Pattern 7)

### Skript-Verifikation

```bash
# Bash-Syntax beider Skripte
bash -n ~/50-System/bin/daily-note-cron.sh       # ✓ OK
bash -n ~/50-System/bin/weekly-digest-cron.sh     # ✓ OK

# Executable
ls -la ~/50-System/bin/daily-note-cron.sh          # -rwx------
ls -la ~/50-System/bin/weekly-digest-cron.sh       # -rwx------
```

### Dry-Run-Verifikation

```bash
# Daily Note heute
TODAY=$(date +%Y-%m-%d)
bash ~/50-System/bin/daily-note-cron.sh
ls -la "Dokumente/Obsidian Vault/06 Daily Notes/${TODAY}.md"   # 711 Bytes
grep "session-id:" "Dokumente/Obsidian Vault/06 Daily Notes/${TODAY}.md"
# → session-id: 20260706-0011

# Weekly Digest W28
WKNOW=$(date +%Y-W%V)
bash ~/50-System/bin/weekly-digest-cron.sh
ls -la "Dokumente/Obsidian Vault/05 Ressourcen/Weekly-Digest-${WKNOW}.md"   # 6277 Bytes
```

### Crontab-Verifikation

```bash
# Atomic Update (in EINEM Call)
(crontab -l; echo "0 6 * * * ~/50-System/bin/daily-note-cron.sh >> /tmp/daily-note-cron.log 2>&1"; echo "0 22 * * 0 ~/50-System/bin/weekly-digest-cron.sh >> /tmp/weekly-digest-cron.log 2>&1") | crontab -

# Verify
crontab -l | grep -cE "^[0-9*@]"                    # → 6 (vorher 4)
crontab -l | grep -E "(daily-note|weekly-digest)"   # → 2 Zeilen
```

### Working Agreement §7: Secrets never inline

```bash
grep -hE "bot[0-9]+:[A-Za-z0-9_-]+" ~/50-System/bin/daily-note-cron.sh ~/50-System/bin/weekly-digest-cron.sh | grep -v '\$TELEGRAM_BOT_TOKEN'
# → (leer) — kein inline-Secret
```

## Alle Bugs dieser Session (ehrlicher Log)

| Bug | Phase | Erkennung | Fix |
|-----|-------|-----------|-----|
| `mnemosyne_sleep all_sessions=true dry_run=false` (halluzinierte Flags) | Schreibphase | Ref-3 Reader-Check: `mnemosyne_sleep` hat diese Flags nicht | Plain `mnemosyne_sleep` mit `|| true` |
| Crontab-Update in Todo als "completed" markiert, aber nie ausgeführt | Nach Phase-10-Lektion | Pattern-7: `crontab -l` zeigte 4/6 statt 6/6 | Atomic `(crontab -l; echo ...) \| crontab -` |
| Weekly-Digest listet sich selbst im "Vault-Änderungen"-Abschnitt | Schreibphase | Ref-5: Self-Reference-Pitfall | `-not -name "Weekly-Digest-*.md"` |
| CHANGELOG-Patch in Todo als "completed" markiert aber nie ausgeführt | Finale | Pattern-7: `grep -c "^## Phase 11" CHANGELOG.md` = 0 | `patch` mit korrektem Anker |
| Mnemosyne-Commit "completed" ohne Tool-Call | Finale | Pattern-7: memory-API wurde nie aufgerufen | Execute im nächsten Turn |

## Template-Fix-Log

**Vorher (Templater-Syntax — braucht Plugin 1.13.0+, lokal 1.12.7):**
```markdown
---
datum: <% tp.date.now("YYYY-MM-DD") %>
session-id: <% tp.date.now("YYYYMMDD-HHmm") %>
---
```

**Nachher (Plain Placeholder — bash-kompatibel, kein Plugin nötig):**
```markdown
---
datum: {{date}}
session-id: {{session_id}}
---
**Cron-Skript sed:** `sed -i "s/{{date}}/$DATE/g; s/{{session_id}}/$SESSION_ID/g" "$TARGET"`
```

## Lessons für Phase 12+

1. **Template-Platzhalter müssen bash-kompatibel sein** — kein Templater-Plugin im Cron-Kontext
2. **`flock` ist Pflicht für Crons die > 1s brauchen** — Weekly-Digest listet den gesamten Vault
3. **Telegram silent-on-success, alert-on-fail** — kein Lärm bei Erfolg, Alarm bei Fehler
4. **`|| true` bei jedem CLI-Aufruf der nicht kritisch ist** — Mnemosyne-Sleep ist nice-to-have
5. **Atomic Crontab-Update in EINEM Call** — nie `crontab <<< "..."`
