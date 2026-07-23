# Local Config Secret Exfiltration — Live Evidence 2026-07-11

## Scenario

Ein GitHub-PAT (`gho_2X...Lz1g`) wurde in `~/.hermes/config.yaml` Zeile 728 (mcp_servers.github-mcp-server-github.env) hardcoded gefunden — 40 Zeichen `gho_`-Präfix-PAT.

## Fundort-Scan

### Primäre Quelle
- `~/.hermes/config.yaml` Zeile 728 (600 Perms)

### Working-Tree-Kopien (3 Library-Repos)
| Pfad | Typ | Status |
|------|-----|--------|
| `~/30-Library/hermes-v7/.hermes/config.yaml` | Library-Clone (Main-Repo) | Token unverändert kopiert |
| `~/10-Projekte/20-experimental/hermes-v7-wt/.hermes/config.yaml` | Worktree-Copy | Token unverändert kopiert |
| `~/10-Projekte/40-archive/hermes-zorin/.hermes/config.yaml` | Archive-Copy | Token unverändert kopiert |

### Lokale Backups (3 Files)
| Pfad | Entstehung | Mtime |
|------|-----------|-------|
| `~/.hermes/config.yaml.bak.20260708_003022` | Vermutlich Auto-Backup vor einem `hermes config set` (08.07.) | Jul 08 |
| `~/.hermes/config.yaml.pre-audit-2026-07-11` | Auto-Backup vor System-Audit (11.07.) | Jul 11 |
| `~/.hermes/config.yaml.corrupt.20260709-122816.bak` | Crash-Recovery-Backup (09.07.) | Jul 09 |

**Total: 6 Dateien mit Token auf Disk** — alle 600 Perms, nur `bratan` lesbar.

## Git-History-Check

### Methode
```bash
for REPO in ~/30-Library/hermes-v7 ~/10-Projekte/20-experimental/hermes-v7-wt ~/10-Projekte/40-archive/hermes-zorin ~/10-Projekte/10-active/greyhack-tools ~/10-Projekte/10-active/github-mcp-server ~/.hermes/hermes-agent; do
  git -C "$REPO" log --all --source --oneline -S"gho_2XZO" 2>/dev/null
done
```

### Ergebnis
- **Kein einziger Treffer in `git log -S`** über alle 6+ geprüften Repos
- Token wurde NIE committed — nur in Working-Tree-Kopien und Backups
- **Entwarnung:** Git-History-Purge (force-push, filter-branch) nicht nötig

## API-Status-Check

### Methode
```bash
curl -sI -H "Authorization: token gho_2XZO..." https://api.github.com/user
```

### Ergebnis
- **HTTP 401** — Token ist revoked/expired/unbekannt
- Keine `X-OAuth-Scopes` im Response-Header
- **Bedeutung:** Der Token funktioniert nicht mehr. Selbst wenn Datei gelesen wird, kann niemand damit was authentifizieren.
- Risk-Bewertung: Minimal → revoked Token ist (fast) so wertlos wie kein Token

## Grep-Precision Fallstrick

Der initiale breite Scan `grep -rE "gho_"` zeigte 25 Repos mit Treffern. Grund: Test-Fixtures in `/home/bratan/.hermes/hermes-agent/tests/hermes_cli/test_copilot_auth.py` enthalten `"gho_ab...1234"` — das Pattern `gho_` matched teilweise auch 8-Zeichen-Test-Tokens.

**Lösung:** Präzises Pattern `gho_[A-Za-z0-9_-]{30,40}` (echte GitHub-PATs sind exakt 40 Zeichen, `gho_` + 36 alphanumerische Zeichen, kein `...`).

Ergebnis nach Präzisierung: **5 echte Files statt 25 falscher Positives.**

## Comparison: Git-Remote-Token-Leak vs Local-Config-Exfiltration

| Feature | Git-Remote-Token-Leak (bisher in Skill) | Local-Config-Exfiltration (diese Session) |
|---------|---------------------------------------|------------------------------------------|
| Fundort | `git remote get-url origin` | `~/.hermes/config.yaml` + Library-Copies |
| Expositionsweg | Git push / Hub-Sync | Backup-Sync, Cloud-Mount, Repo-Library |
| Token-Restwert | Token ist LIVE (HTTP 200 → Auth) | Token ist revoked (HTTP 401) |
| Fix | git remote set-url + revoken | Env-Reference-Migration + Backup-Cleanup |
| Emergency-Level | P0 (Live-Token, öffentlich syncbar) | P2 (Hygiene, totes Token) |
| Git-History | Token in log commits (wenn gepusht) | Token NIE in log (nur Working-Tree) |

## Lessons Learned

1. **Revoked ≠ Gelöscht:** Auch wenn Token revoked ist, bleibt der String in 6 Files. Bei Backup-Sync oder Cloud-Mount theoretisch exponierbar. Saubere Lösung: Env-Reference-Pattern `${TOKEN}` — Token lebt nur in `~/.env` (chmod 600), nicht in `config.yaml`.

2. **Grep-Präzision ist Safety:** Breiter `grep -rE "gho_"` löst False-Positives aus. Präzises Pattern + API-Verifikation = zuverlässiges Bild. Jede Secret-Suche: (a) präzises Pattern definieren, (b) False-Positives manuell rausfiltern, (c) API-Status als Ground Truth.

3. **Surface-Area ist größer als man denkt:** Primär-File + 3 Library-Copies + 3 Backups = 6 Kopien. Das ist typisch für Hermes-Setups: `git clone` von hermes-v7 in verschiedene Library/Worktree/Archive-Ordner kopiert den `.hermes/`-Ordner inkl. config.yaml mit. Jeder Klon produziert eine Token-Kopie.

4. **Permissions alle 600, aber:** Config-Files in Library-Clones haben keine Git-Protection (sind in `.gitignore` oder gar nicht tracked). Ein `git push ` vom falschen Pfad könnte theoretisch die config.yaml mitsamt Token pushen — auch wenn sie nicht im Git steht, wenn jemand `git add` + `git push` im falschen Verzeichnis macht. Permissions-only ist kein ausreichender Schutz für 6-File-Spread.

## Recommendations

### P2-Hygiene (wenn Zeit)
1. Token-String in allen 6 Files durch `${GITHUB_PERSONAL_ACCESS_TOKEN}` (Env-Reference) ersetzen
2. Backups rotieren (`config.yaml.bak*` löschen, neues Backup ohne Token erstellen)
3. Library-Copies (`hermes-v7/.hermes/config.yaml`, `hermes-v7-wt/.hermes/config.yaml`, `hermes-zorin/.hermes/config.yaml`) auf Env-Reference umstellen

### Read-Only Default für Config-Files
- `~/30-Library/hermes-v7/.hermes/config.yaml` → Perms auf 600 setzen (falls anders)
- Selbiges für Worktree + Archive

## Verifikations-Kommando (für Follow-Up)
```bash
# Nach Migration prüfen:
grep -rln "gho_2XZOEMH2" ~/.hermes ~/30-Library ~/10-Projekte 2>/dev/null
# Sollte leer sein (Token existiert nirgendwo mehr als Plaintext)
```